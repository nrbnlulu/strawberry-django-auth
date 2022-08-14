from dataclasses import asdict
from smtplib import SMTPException
from typing import Union
from uuid import UUID

from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction
import strawberry
from strawberry.types import Info
from strawberry_django_jwt.exceptions import JSONWebTokenError, JSONWebTokenExpired
from strawberry_django_jwt.mutations import ObtainJSONWebToken as JwtObtainParent
from strawberry_django_jwt.mutations import Refresh as RefreshParent
from strawberry_django_jwt.mutations import Revoke as RevokeParent
from strawberry_django_jwt.mutations import Verify as VerifyParent
from strawberry_django_jwt.utils import create_user_token

from gqlauth.captcha.models import Captcha as CaptchaModel
from gqlauth.captcha.types_ import CaptchaType
from gqlauth.core.constants import Messages, TokenAction
from gqlauth.core.exceptions import (
    EmailAlreadyInUse,
    InvalidCredentials,
    PasswordAlreadySetError,
    TokenScopeError,
    UserAlreadyVerified,
    UserNotVerified,
)
from gqlauth.core.shortcuts import get_user_by_email, get_user_to_login
from gqlauth.core.types_ import (
    MutationNormalOutput,
    ObtainJSONWebTokenPayload,
    RefreshTokenPayload,
    RevokeTokenPayload,
    VerifyTokenPayload,
)
from gqlauth.core.utils import (
    g_user,
    get_payload_from_token,
    inject_fields,
    revoke_user_refresh_token,
)
from gqlauth.settings import gqlauth_settings as app_settings
from gqlauth.user.decorators import (
    _password_confirmation_required,
    secondary_email_required,
    verification_required,
)
from gqlauth.user.forms import (
    EmailForm,
    PasswordLessRegisterForm,
    RegisterForm,
    UpdateAccountForm,
)
from gqlauth.user.models import UserStatus
from gqlauth.user.signals import user_registered, user_verified

UserModel = get_user_model()


class Captcha:
    """
    Creates a brand-new captcha.
    Returns a base64 encoded string of the captcha.
    And uuid representing the captcha id in the database.
    When you will try to log in or register You will
    need submit that uuid With the user input.
    **The captcha will be invoked when the timeout expires**.
    """

    @strawberry.mutation(description=__doc__)
    def field(self) -> CaptchaType:
        return CaptchaModel.create_captcha()

    @strawberry.mutation(description=__doc__)
    @sync_to_async
    def afield(self) -> CaptchaType:
        return CaptchaModel.create_captcha()


def check_captcha(
    input_: Union["RegisterMixin.RegisterInput", "ObtainJSONWebTokenMixin.ObtainJSONWebTokenInput"]
):
    uuid = input_.identifier
    try:
        obj = CaptchaModel.objects.get(uuid=uuid)
    except CaptchaModel.DoesNotExist:
        return Messages.CAPTCHA_EXPIRED
    return obj.validate(input_.userEntry)


class RegisterMixin:
    """
    Register user with fields defined in the settings.
    If the email field of the user model is part of the
    registration fields (default), check if there is
    no user with that email or as a secondary email.

    If it exists, it does not register the user,
    even if the email field is not defined as unique
    (default of the default django user model).

    When creating the user, it also creates a `UserStatus`
    related to that user, making it possible to track
    if the user is archived, verified and has a secondary
    email.

    Send account verification email.

    If allowed to not verified users login, return token.
    """

    @strawberry.input
    @inject_fields(app_settings.REGISTER_MUTATION_FIELDS)
    class RegisterInput:
        if not app_settings.ALLOW_PASSWORDLESS_REGISTRATION:
            password1: str
            password2: str

        if app_settings.REGISTER_REQUIRE_CAPTCHA:
            identifier: UUID
            userEntry: str

    form = (
        PasswordLessRegisterForm if app_settings.ALLOW_PASSWORDLESS_REGISTRATION else RegisterForm
    )

    @classmethod
    def resolve_mutation(cls, info, input_: RegisterInput) -> MutationNormalOutput:
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            check_res = check_captcha(input_)
            if check_res != Messages.CAPTCHA_VALID:
                return MutationNormalOutput(success=False, errors={"captcha": check_res})

        try:
            with transaction.atomic():
                f = cls.form(asdict(input_))
                if f.is_valid():
                    email = getattr(input_, "email", False)
                    UserStatus.clean_email(email)
                    user = f.save()
                    if email:
                        send_activation = app_settings.SEND_ACTIVATION_EMAIL is True
                        send_password_set = (
                            app_settings.ALLOW_PASSWORDLESS_REGISTRATION is True
                            and app_settings.SEND_PASSWORD_SET_EMAIL is True
                        )
                        if send_activation:
                            user.status.send_activation_email(info)

                        if send_password_set:
                            user.status.send_password_set_email(info)

                    user_registered.send(sender=cls, user=user)
                    return MutationNormalOutput(success=True)
                else:
                    return MutationNormalOutput(success=False, errors=f.errors.get_json_data())
        except EmailAlreadyInUse:
            return MutationNormalOutput(
                success=False,
                # if the email was set as a secondary email,
                # the RegisterForm will not catch it,
                # so we need to run UserStatus.clean_email(email)
                errors={UserModel.EMAIL_FIELD: Messages.EMAIL_IN_USE},
            )
        except SMTPException:
            return MutationNormalOutput(success=False, errors=Messages.EMAIL_FAIL)


class VerifyAccountMixin:
    """
    Verify user account.

    Receive the token that was sent by email.
    If the token is valid, make the user verified
    by making the `user.status.verified` field true.
    """

    @strawberry.input
    class VerifyAccountInput:
        token: str

    @classmethod
    def resolve_mutation(cls, info: Info, input_: VerifyAccountInput) -> MutationNormalOutput:
        try:
            UserStatus.verify(input_.token)
            return MutationNormalOutput(success=True)
        except UserAlreadyVerified:
            return MutationNormalOutput(success=False, errors=Messages.ALREADY_VERIFIED)
        except SignatureExpired:
            return MutationNormalOutput(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return MutationNormalOutput(success=False, errors=Messages.INVALID_TOKEN)


class VerifySecondaryEmailMixin:
    """
    Verify user secondary email.

    Receive the token that was sent by email.
    User is already verified when using this mutation.

    If the token is valid, add the secondary email
    to `user.status.secondary_email` field.

    Note that until the secondary email is verified,
    it has not been saved anywhere beyond the token,
    so it can still be used to create a new account.
    After being verified, it will no longer be available.
    """

    @strawberry.input
    class VerifySecondaryEmailInput:
        token: str

    @classmethod
    def resolve_mutation(cls, _, input_: VerifySecondaryEmailInput) -> MutationNormalOutput:
        try:
            token = input_.token
            UserStatus.verify_secondary_email(token)
            return MutationNormalOutput(success=True)
        except EmailAlreadyInUse:
            # while the token was sent and the user haven't
            # verified, the email was free. If other account
            # was created with it, it is already in use.
            return MutationNormalOutput(success=False, errors=Messages.EMAIL_IN_USE)
        except SignatureExpired:
            return MutationNormalOutput(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return MutationNormalOutput(success=False, errors=Messages.INVALID_TOKEN)


class ResendActivationEmailMixin:
    """
    Sends activation email.

    It is called resend because theoretically
    the first activation email was sent when
    the user registered.

    If there is no user with the requested email,
    a successful response is returned.
    """

    @strawberry.input
    class ResendActivationEmailInput:
        email: str

    @classmethod
    def resolve_mutation(cls, info, input_: ResendActivationEmailInput) -> MutationNormalOutput:
        try:
            email = input_.email
            f = EmailForm({"email": email})
            if f.is_valid():
                user = get_user_by_email(email)
                user.status.resend_activation_email(info)
                return MutationNormalOutput(success=True)
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())
        except ObjectDoesNotExist:
            return MutationNormalOutput(success=True)  # even if user is not registered
        except SMTPException:
            return MutationNormalOutput(success=False, errors=Messages.EMAIL_FAIL)
        except UserAlreadyVerified:
            return MutationNormalOutput(success=False, errors={"email": Messages.ALREADY_VERIFIED})


class SendPasswordResetEmailMixin:
    """
    Send password reset email.

    For non verified users, send an activation
    email instead.

    Accepts both primary and secondary email.

    If there is no user with the requested email,
    a successful response is returned.
    """

    @strawberry.input
    class SendPasswordResetEmailInput:
        email: str

    @classmethod
    def resolve_mutation(cls, info, input_: SendPasswordResetEmailInput) -> MutationNormalOutput:
        try:
            email = input_.email
            f = EmailForm({"email": email})
            if f.is_valid():
                user = get_user_by_email(email)
                user.status.send_password_reset_email(info, [email])
                return MutationNormalOutput(success=True)
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())
        except ObjectDoesNotExist:
            return MutationNormalOutput(success=True)  # even if user is not registered
        except SMTPException:
            return MutationNormalOutput(success=False, errors=Messages.EMAIL_FAIL)
        except UserNotVerified:
            user = get_user_by_email(input_.email)
            try:
                user.status.resend_activation_email(info)
                return MutationNormalOutput(
                    success=False,
                    errors={"email": Messages.NOT_VERIFIED_PASSWORD_RESET},
                )
            except SMTPException:
                return MutationNormalOutput(success=False, errors=Messages.EMAIL_FAIL)


class PasswordResetMixin:
    """
    Change user password without old password.

    Receive the token that was sent by email.

    If token and new passwords are valid, update
    user password and in case of using refresh
    tokens, revoke all of them.

    Also, if user has not been verified yet, verify it.
    """

    @strawberry.input
    class PasswordResetInput:
        token: str
        new_password1: str
        new_password2: str

    form = SetPasswordForm

    @classmethod
    def resolve_mutation(cls, _, input_: PasswordResetInput) -> MutationNormalOutput:
        try:
            payload = get_payload_from_token(
                input_.token,
                TokenAction.PASSWORD_RESET,
                app_settings.EXPIRATION_PASSWORD_RESET_TOKEN,
            )
            user = UserModel._default_manager.get(**payload)

            f = cls.form(user, asdict(input_))
            if f.is_valid():
                revoke_user_refresh_token(user)
                user = f.save()
                if user.status.verified is False:
                    user.status.verified = True
                    user.status.save(update_fields=["verified"])
                    user_verified.send(sender=cls, user=user)

                return MutationNormalOutput(success=True)
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())
        except SignatureExpired:
            return MutationNormalOutput(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return MutationNormalOutput(success=False, errors=Messages.INVALID_TOKEN)


class PasswordSetMixin:
    """
    Set user password - for password-less registration

    Receive the token that was sent by email.

    If token and new passwords are valid, set
    user password and in case of using refresh
    tokens, revoke all of them.

    Also, if user has not been verified yet, verify it.
    """

    @strawberry.input
    class PasswordSetInput:
        token: str
        new_password1: str
        new_password2: str

    form = SetPasswordForm

    @classmethod
    def resolve_mutation(cls, _, input_: PasswordSetInput) -> MutationNormalOutput:
        try:
            token = input_.token
            payload = get_payload_from_token(
                token,
                TokenAction.PASSWORD_SET,
                app_settings.EXPIRATION_PASSWORD_SET_TOKEN,
            )
            user = UserModel._default_manager.get(**payload)
            f = cls.form(user, asdict(input_))
            if f.is_valid():
                # Check if user has already set a password
                if user.has_usable_password():
                    raise PasswordAlreadySetError
                revoke_user_refresh_token(user)
                user = f.save()

                if user.status.verified is False:
                    user.status.verified = True
                    user.status.save(update_fields=["verified"])

                return MutationNormalOutput(success=True)
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())
        except SignatureExpired:
            return MutationNormalOutput(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return MutationNormalOutput(success=False, errors=Messages.INVALID_TOKEN)
        except PasswordAlreadySetError:
            return MutationNormalOutput(success=False, errors=Messages.PASSWORD_ALREADY_SET)


class ObtainJSONWebTokenMixin:
    """
    Obtain JSON web token for given user.

    Allow to perform login with different fields,
    and secondary email if set. The fields are
    defined on settings.

    Not verified users can log in by default. This
    can be changes on settings.

    If user is archived, make it unarchived and
    return `unarchiving=True` on OutputBase.
    """

    @strawberry.input
    @inject_fields(app_settings.LOGIN_FIELDS)
    class ObtainJSONWebTokenInput:
        password: str
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            identifier: UUID
            userEntry: str

    @classmethod
    def resolve_mutation(cls, info, input_: ObtainJSONWebTokenInput) -> ObtainJSONWebTokenPayload:
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            check_res = check_captcha(input_)
            if check_res != Messages.CAPTCHA_VALID:
                return ObtainJSONWebTokenPayload(success=False, errors={"captcha": check_res})

        try:
            args = {
                UserModel.USERNAME_FIELD: getattr(input_, UserModel.USERNAME_FIELD),
            }

            user = get_user_to_login(**args)
            if user.status.archived is True:  # un-archive on login
                UserStatus.unarchive(user)

            if user.status.verified or app_settings.ALLOW_LOGIN_NOT_VERIFIED:
                # this will raise if not successful
                res = JwtObtainParent.obtain.get_result(None, None, [cls, info], asdict(input_))
                return ObtainJSONWebTokenPayload(success=True, obtainPayload=res)
            else:
                raise UserNotVerified

        except (JSONWebTokenError, ObjectDoesNotExist, InvalidCredentials):
            return ObtainJSONWebTokenPayload(success=False, errors=Messages.INVALID_CREDENTIALS)
        except UserNotVerified:
            return ObtainJSONWebTokenPayload(success=False, errors=Messages.NOT_VERIFIED)


class ArchiveOrDeleteMixin:
    @strawberry.input
    class ArchiveOrDeleteMixinInput:
        password: str

    @classmethod
    @verification_required
    @_password_confirmation_required
    def resolve_mutation(cls, info, input_: ArchiveOrDeleteMixinInput) -> MutationNormalOutput:
        user = g_user(info)
        cls.resolve_action(user)
        return MutationNormalOutput(success=True)


class ArchiveAccountMixin(ArchiveOrDeleteMixin):
    """
    Archive account and revoke refresh tokens.
    User must be verified and confirm password.
    """

    @classmethod
    def resolve_action(cls, user):
        UserStatus.archive(user)
        revoke_user_refresh_token(user=user)


class DeleteAccountMixin(ArchiveOrDeleteMixin):
    """
    Delete account permanently or make `user.is_active=False`.

    The behavior is defined on settings.
    Anyway user refresh tokens are revoked.

    User must be verified and confirm password.
    """

    @classmethod
    def resolve_action(cls, user):
        if app_settings.ALLOW_DELETE_ACCOUNT:
            revoke_user_refresh_token(user=user)
            user.delete()


class PasswordChangeMixin:
    """
    Change account password when user knows the old password.

    A new token and refresh token are sent. User must be verified.
    """

    @strawberry.input
    class PasswordChangeInput:
        old_password: str
        new_password1: str
        new_password2: str

    form = PasswordChangeForm

    @classmethod
    @verification_required
    @_password_confirmation_required
    def resolve_mutation(cls, info: Info, input_: PasswordChangeInput) -> ObtainJSONWebTokenPayload:
        args = asdict(input_)
        user = g_user(info)
        f = cls.form(user, args)
        if f.is_valid():
            revoke_user_refresh_token(user)
            user = f.save()
            parent_res = async_to_sync(create_user_token)(user)
            return ObtainJSONWebTokenPayload(success=True, obtainPayload=parent_res)
        else:
            return ObtainJSONWebTokenPayload(success=False, errors=f.errors.get_json_data())


class UpdateAccountMixin:
    """
    Update user model fields, defined on settings.

    User must be verified.
    """

    @strawberry.input
    @inject_fields(app_settings.UPDATE_MUTATION_FIELDS)
    class UpdateAccountInput:
        ...

    form = UpdateAccountForm

    @classmethod
    @verification_required
    def resolve_mutation(cls, info, input_: UpdateAccountInput) -> MutationNormalOutput:
        user = g_user(info)
        f = cls.form(
            asdict(input_),
            instance=user,
        )
        if f.is_valid():
            f.save()
            return MutationNormalOutput(success=True)
        else:
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())


class VerifyTokenMixin:
    """
    Checks if a token is not expired and correct
    """

    @strawberry.input
    class VerifyTokenInput:
        token: str

    @classmethod
    def resolve_mutation(cls, info, input_: VerifyTokenInput) -> VerifyTokenPayload:
        try:
            payload = VerifyParent.verify.get_result(None, None, [cls, info], asdict(input_))
            return VerifyTokenPayload(success=True, verifyPayload=payload)
        except JSONWebTokenExpired:
            return VerifyTokenPayload(success=False, errors=Messages.EXPIRED_TOKEN)
        except JSONWebTokenError:
            return VerifyTokenPayload(success=False, errors=Messages.INVALID_TOKEN)


class RefreshTokenMixin:
    """
    ### refreshToken to refresh your token:

    using the refresh token you already got during authorization.
    this will obtain a brand-new token (and possibly a refresh token)
    with renewed expiration time for non-expired tokens
    """

    @strawberry.input
    class RefreshTokenInput:
        refresh_token: str

    @classmethod
    def resolve_mutation(cls, info, input_: RefreshTokenInput) -> RefreshTokenPayload:
        try:
            res = RefreshParent.refresh.get_result(None, None, [cls, info], asdict(input_))
            return RefreshTokenPayload(success=True, refreshPayload=res)

        except JSONWebTokenExpired:
            return RefreshTokenPayload(success=False, errors=Messages.EXPIRED_TOKEN)
        except JSONWebTokenError:
            return RefreshTokenPayload(success=False, errors=Messages.INVALID_TOKEN)


class RevokeTokenMixin:
    """
    Suspends a refresh token
    """

    @strawberry.input
    class RevokeTokenInput:
        refresh_token: str

    @classmethod
    def resolve_mutation(cls, info, input_: RevokeTokenInput) -> RevokeTokenPayload:
        try:
            res = RevokeParent.revoke.get_result(None, None, [cls, info], asdict(input_))
            return RevokeTokenPayload(success=True, revokePayload=res)

        except JSONWebTokenExpired:
            return RevokeTokenPayload(success=False, errors=Messages.EXPIRED_TOKEN)
        except JSONWebTokenError:
            return RevokeTokenPayload(success=False, errors=Messages.INVALID_TOKEN)


class SendSecondaryEmailActivationMixin:
    """
    Send activation to secondary email.

    User must be verified and confirm password.
    """

    @strawberry.input
    class SendSecondaryEmailActivationInput:
        password: str

    @classmethod
    @verification_required
    @_password_confirmation_required
    def resolve_mutation(
        cls, info, input_: SendSecondaryEmailActivationInput
    ) -> MutationNormalOutput:
        try:
            email = input_.get("email")
            f = EmailForm({"email": email})
            if f.is_valid():
                user = g_user(info)
                user.status.send_secondary_email_activation(info, email)
                return MutationNormalOutput(success=True)
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())
        except EmailAlreadyInUse:
            # while the token was sent and the user haven't verified,
            # the email was free. If other account was created with if
            # it is already in use
            return MutationNormalOutput(success=False, errors={"email": Messages.EMAIL_IN_USE})
        except SMTPException:
            return MutationNormalOutput(success=False, errors=Messages.EMAIL_FAIL)


class SwapEmailsMixin:
    """
    Swap between primary and secondary emails.

    Require password confirmation.
    """

    @strawberry.input
    class SwapEmailsInput:
        password: str

    @classmethod
    @secondary_email_required
    def resolve_mutation(cls, info: Info, input_: SwapEmailsInput) -> MutationNormalOutput:
        if not g_user(info).check_password(input_.password):
            return MutationNormalOutput(success=False, errors=Messages.INVALID_PASSWORD)
        g_user(info).status.swap_emails()
        return MutationNormalOutput(success=True)


class RemoveSecondaryEmailMixin:
    """
    Remove user secondary email.

    Require password confirmation.
    """

    @strawberry.input
    class RemoveSecondaryEmailInput:
        password: str

    @classmethod
    @secondary_email_required
    @_password_confirmation_required
    def resolve_mutation(
        cls, info: Info, input_: RemoveSecondaryEmailInput
    ) -> MutationNormalOutput:
        g_user(info).status.remove_secondary_email()
        return MutationNormalOutput(success=True)
