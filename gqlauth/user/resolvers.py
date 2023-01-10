from dataclasses import asdict
from smtplib import SMTPException
from typing import Callable, cast
from uuid import UUID

import strawberry
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction
from strawberry.field import StrawberryField
from strawberry.types import Info
from strawberry_django_plus import gql

from gqlauth.captcha.models import Captcha as CaptchaModel
from gqlauth.captcha.types_ import CaptchaType
from gqlauth.core.constants import Messages, TokenAction
from gqlauth.core.exceptions import (
    PasswordAlreadySetError,
    TokenScopeError,
    UserAlreadyVerified,
    UserNotVerified,
)
from gqlauth.core.types_ import GQLAuthError, GQLAuthErrors, MutationNormalOutput
from gqlauth.core.utils import (
    cast_to_status_user,
    get_payload_from_token,
    get_user,
    get_user_by_email,
    inject_fields,
    revoke_user_refresh_token,
)
from gqlauth.jwt.types_ import (
    ObtainJSONWebTokenInput,
    ObtainJSONWebTokenType,
    RefreshTokenType,
    RevokeRefreshTokenType,
    TokenType,
    VerifyTokenInput,
    VerifyTokenType,
)
from gqlauth.models import RefreshToken, UserStatus
from gqlauth.settings import gqlauth_settings as app_settings
from gqlauth.user.forms import EmailForm, PasswordLessRegisterForm, RegisterForm, UpdateAccountForm
from gqlauth.user.helpers import check_captcha, confirm_password
from gqlauth.user.signals import user_registered, user_verified

UserModel = get_user_model()


class BaseMixin:
    field: StrawberryField
    REQUIRE_VERIFICATION: bool = False
    resolve_mutation: Callable

    @classmethod
    def verification_check(cls, info: Info) -> None:
        if cls.REQUIRE_VERIFICATION:
            user = get_user(info)
            try:
                if not user.status.verified:  # type: ignore
                    raise GQLAuthError(code=GQLAuthErrors.NOT_VERIFIED)
            except AttributeError:  # anonymous user has no status.
                if user.is_anonymous:
                    raise GQLAuthError(code=GQLAuthErrors.UNAUTHENTICATED)


class Captcha:
    """Creates a brand-new captcha. Returns a base64 encoded string of the
    captcha. And uuid representing the captcha id in the database. When you
    will try to log in or register You will need submit that uuid With the user
    input.

    **The captcha will be invoked when the timeout expires**.
    """

    @gql.django.field(description=__doc__)
    def field(self) -> CaptchaType:
        return CaptchaModel.create_captcha()


class RegisterMixin(BaseMixin):
    """Register user with fields defined in the settings. If the email field of
    the user model is part of the registration fields (default), check if there
    is no user with that email.

    If it exists, it does not register the user,
    even if the email field is not defined as unique
    (default of the default django user model).

    When creating the user, it also creates a `UserStatus`
    related to that user, making it possible to track
    if the user is archived / verified.

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
        email = getattr(input_, "email", False)
        try:
            with transaction.atomic():
                f = cls.form(asdict(input_))
                if f.is_valid():
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
        except SMTPException:
            return MutationNormalOutput(success=False, errors=Messages.EMAIL_FAIL)


class VerifyAccountMixin(BaseMixin):
    """Verify user account.

    Receive the token that was sent by email. If the token is valid,
    make the user verified by making the `user.status.verified` field
    true.
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


class ResendActivationEmailMixin(BaseMixin):
    """Sends activation email.

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


class SendPasswordResetEmailMixin(BaseMixin):
    """Send password reset email.

    For non verified users, send an activation
    email instead.

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


class PasswordResetMixin(BaseMixin):
    """Change user password without old password.

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
            status: "UserStatus" = getattr(user, "status")  # noqa: B009
            f = cls.form(user, asdict(input_))
            if f.is_valid():
                revoke_user_refresh_token(user)
                user = f.save()  # type: ignore
                if status.verified is False:
                    status.verified = True
                    status.save(update_fields=["verified"])
                    user_verified.send(sender=cls, user=user)

                return MutationNormalOutput(success=True)
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())
        except SignatureExpired:
            return MutationNormalOutput(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return MutationNormalOutput(success=False, errors=Messages.INVALID_TOKEN)


class PasswordSetMixin(BaseMixin):
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
                user = f.save()  # type: ignore
                status: "UserStatus" = getattr(user, "status")  # noqa: B009

                if status.verified is False:
                    status.verified = True
                    status.save(update_fields=["verified"])

                return MutationNormalOutput(success=True)
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())
        except SignatureExpired:
            return MutationNormalOutput(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return MutationNormalOutput(success=False, errors=Messages.INVALID_TOKEN)
        except PasswordAlreadySetError:
            return MutationNormalOutput(success=False, errors=Messages.PASSWORD_ALREADY_SET)


class ObtainJSONWebTokenMixin(BaseMixin):
    """Obtain JSON web token for given user.

    Allow to perform login with different fields,
    The fields are defined on settings.

    Not verified users can log in by default. This
    can be changes on settings.

    If user is archived, make it unarchived and
    return `unarchiving=True` on OutputBase.
    """

    @classmethod
    def resolve_mutation(cls, info, input_: ObtainJSONWebTokenInput) -> ObtainJSONWebTokenType:
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            check_res = check_captcha(input_)
            if check_res != Messages.CAPTCHA_VALID:
                return ObtainJSONWebTokenType(success=False, errors={"captcha": check_res})

        return ObtainJSONWebTokenType.authenticate(info, input_)


class ArchiveOrDeleteMixin(BaseMixin):
    @strawberry.input
    class ArchiveOrDeleteMixinInput:
        password: str

    REQUIRE_VERIFICATION = True

    @classmethod
    def resolve_mutation(cls, info, input_: ArchiveOrDeleteMixinInput) -> MutationNormalOutput:
        user = get_user(info)
        if error := confirm_password(user, input_):
            return error
        cls.resolve_action(user)  # type: ignore
        return MutationNormalOutput(success=True)


class ArchiveAccountMixin(ArchiveOrDeleteMixin):
    """Archive account and revoke refresh tokens.

    User must be verified and confirm password.
    """

    @classmethod
    def resolve_action(cls, user):
        UserStatus.archive(user)
        revoke_user_refresh_token(user=user)


class DeleteAccountMixin(ArchiveOrDeleteMixin):
    """Delete account permanently or make `user.is_active=False`.

    The behavior is defined on settings.
    Anyway user refresh tokens are revoked.

    User must be verified and confirm password.
    """

    @classmethod
    def resolve_action(cls, user):
        if app_settings.ALLOW_DELETE_ACCOUNT:
            revoke_user_refresh_token(user=user)
            user.delete()


class PasswordChangeMixin(BaseMixin):
    """Change account password when user knows the old password.

    A new token and refresh token are sent. User must be verified.
    """

    @strawberry.input
    class PasswordChangeInput:
        old_password: str
        new_password1: str
        new_password2: str

    form = PasswordChangeForm
    REQUIRE_VERIFICATION = True

    @classmethod
    def resolve_mutation(cls, info: Info, input_: PasswordChangeInput) -> ObtainJSONWebTokenType:
        user = get_user(info)
        if error := confirm_password(user, input_):
            return ObtainJSONWebTokenType(**asdict(error))

        args = asdict(input_)
        f = cls.form(user, args)  # type: ignore
        if f.is_valid():
            revoke_user_refresh_token(user)
            user = f.save()
            user_with_status = cast_to_status_user(user)
            return ObtainJSONWebTokenType.from_user(user_with_status)
        else:
            return ObtainJSONWebTokenType(success=False, errors=f.errors.get_json_data())


class UpdateAccountMixin(BaseMixin):
    """Update user model fields, defined on settings.

    User must be verified.
    """

    @strawberry.input
    @inject_fields(app_settings.UPDATE_MUTATION_FIELDS)
    class UpdateAccountInput:
        ...

    form = UpdateAccountForm
    REQUIRE_VERIFICATION = True

    @classmethod
    def resolve_mutation(cls, info, input_: UpdateAccountInput) -> MutationNormalOutput:
        user = get_user(info)
        f = cls.form(
            asdict(input_),
            instance=user,
        )
        if f.is_valid():
            f.save()
            return MutationNormalOutput(success=True)
        else:
            return MutationNormalOutput(success=False, errors=f.errors.get_json_data())


class VerifyTokenMixin(BaseMixin):
    """### Checks if a token is not expired and correct.

    *Note that this is not for refresh tokens.*
    """

    @classmethod
    def resolve_mutation(cls, _: Info, input_: VerifyTokenInput) -> VerifyTokenType:
        return VerifyTokenType.from_token(input_)


class RefreshTokenMixin(BaseMixin):
    """### refreshToken to generate a new login token:

    *Use this only if `JWT_LONG_RUNNING_REFRESH_TOKEN` is True*

    using the refresh-token you already got during authorization, and
    obtain a brand-new token (and possibly a new refresh token if you revoked the previous).
    This is an alternative to log in when your token expired.
    """

    @strawberry.input(
        description="If `revoke_refresh_token` is true,"
        " revokes to refresh token an creates a new one."
    )
    class RefreshTokenInput:
        refresh_token: str
        revoke_refresh_token: bool = strawberry.field(
            description="revokes the previous refresh token, and will generate new one.",
            default=False,
        )

    @classmethod
    def resolve_mutation(cls, info, input_: RefreshTokenInput) -> ObtainJSONWebTokenType:
        try:
            res = RefreshToken.objects.get(token=input_.refresh_token)
        except RefreshToken.DoesNotExist:
            return ObtainJSONWebTokenType(success=False, errors=Messages.INVALID_TOKEN)
        user = res.user
        if res.is_expired_():
            return ObtainJSONWebTokenType(success=False, errors=Messages.EXPIRED_TOKEN)
        # fields that are determined by if statements are not recognized by mypy.
        ret = ObtainJSONWebTokenType(
            success=True, token=TokenType.from_user(user), refresh_token=res  # type: ignore
        )
        if input_.revoke_refresh_token:
            res.revoke()
            ret.refresh_token = cast(RefreshTokenType, RefreshToken.from_user(user))
        return ret


class RevokeTokenMixin(BaseMixin):
    """### Suspends a refresh token.

    *token must exist to be revoked.*
    """

    @strawberry.input
    class RevokeTokenInput:
        refresh_token: str

    @classmethod
    def resolve_mutation(cls, _: Info, input_: RevokeTokenInput) -> RevokeRefreshTokenType:
        try:
            refresh_token = RefreshToken.objects.get(
                token=input_.refresh_token, revoked__isnull=True
            )
            refresh_token.revoke()
            return RevokeRefreshTokenType(
                success=True, refresh_token=cast(RefreshTokenType, refresh_token)
            )
        except RefreshToken.DoesNotExist:
            return RevokeRefreshTokenType(success=False, errors=Messages.INVALID_TOKEN)
