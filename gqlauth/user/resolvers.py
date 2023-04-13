import functools
from dataclasses import asdict
from smtplib import SMTPException
from typing import Callable, Optional, Type, cast
from uuid import UUID

import strawberry
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction
from strawberry.field import StrawberryField
from strawberry.types import Info
from strawberry_django_plus import gql

from gqlauth.backends.basebackend import UserProto
from gqlauth.backends.strawberry_django_auth.forms import (
    EmailForm,
    PasswordLessRegisterForm,
    RegisterForm,
    UpdateAccountForm,
)
from gqlauth.backends.strawberry_django_auth.models import Captcha as CaptchaModel
from gqlauth.backends.strawberry_django_auth.models import RefreshToken
from gqlauth.backends.strawberry_django_auth.signals import user_registered, user_verified
from gqlauth.captcha.types_ import CaptchaType
from gqlauth.core.constants import TokenAction
from gqlauth.core.exceptions import (
    PasswordAlreadySetError,
    TokenScopeError,
    UserAlreadyVerified,
    UserNotVerified,
)
from gqlauth.core.types_ import (
    CaptchaErrorCodes,
    EmailErrorCodes,
    EmailErrorsInterface,
    ErrorCodes,
    ErrorMessage,
    GQLAuthError,
    MutationNormalOutput,
    OperationErrorCodes,
    OperationErrorsInterface,
    RawErrorsInterface,
    TokenErrorCodes,
    TokenErrorsInterface,
)
from gqlauth.core.utils import (
    get_payload_from_token,
    get_user,
    inject_fields,
)
from gqlauth.jwt.types_ import (
    ObtainJSONWebTokenOutput,
    RefreshTokenType,
    RevokeRefreshTokenType,
    TokenType,
    VerifyTokenInput,
    VerifyTokenType,
)
from gqlauth.settings import gqlauth_settings as app_settings
from gqlauth.user.helpers import confirm_password

UserModel = get_user_model()


def wrap_token_errors(ret_type: Type):
    """Catch token errors and return expected error."""

    def wrapper(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except SignatureExpired:
                return MutationNormalOutput(
                    success=False,
                    errors=ret_type(token=ErrorMessage.from_code(TokenErrorCodes.TOKEN_EXPIRED)),
                )
            except (BadSignature, TokenScopeError):
                return MutationNormalOutput(
                    success=False,
                    errors=ret_type(token=ErrorMessage.from_code(TokenErrorCodes.INVALID_TOKEN)),
                )

        return inner

    return wrapper


class BaseMixin:
    field: StrawberryField
    REQUIRE_VERIFICATION: bool = False
    resolve_mutation: Callable

    @classmethod
    def verification_check(cls, info: Info) -> None:
        if cls.REQUIRE_VERIFICATION:
            user = get_user(info)
            if user.is_anonymous:
                raise GQLAuthError(code=ErrorCodes.UNAUTHENTICATED)
            elif not user.is_verified:
                raise GQLAuthError(code=ErrorCodes.NOT_VERIFIED)


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

    @strawberry.type()
    class RegisterMutationErrors(EmailErrorsInterface, RawErrorsInterface):
        if app_settings.REGISTER_REQUIRE_CAPTCHA:
            captcha: Optional[ErrorMessage[CaptchaErrorCodes]] = None

    form = (
        PasswordLessRegisterForm if app_settings.ALLOW_PASSWORDLESS_REGISTRATION else RegisterForm
    )

    @classmethod
    def resolve_mutation(
        cls, info, input_: RegisterInput
    ) -> MutationNormalOutput[RegisterMutationErrors]:
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            if captcha_error := app_settings.BACKEND.validate_captcha(
                input_.identifier, user_input=input_.userEntry
            ):
                return MutationNormalOutput(
                    success=False,
                    errors=cls.RegisterMutationErrors(
                        captcha=ErrorMessage.from_code(captcha_error)
                    ),
                )

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
                            app_settings.BACKEND.send_activation_email(user, info)

                        if send_password_set:
                            app_settings.BACKEND.send_password_set_email(user, info)

                    user_registered.send(sender=cls, user=user)
                    return MutationNormalOutput(success=True)
                else:
                    return MutationNormalOutput(
                        success=False,
                        errors=cls.RegisterMutationErrors(raw_errors=f.errors.get_json_data()),
                    )
        except SMTPException:
            return MutationNormalOutput(
                success=False,
                errors=cls.RegisterMutationErrors(
                    email=ErrorMessage.from_code(EmailErrorCodes.EMAIL_FAILED)
                ),
            )


class VerifyAccountMixin(BaseMixin):
    """Verify user account.

    Receive the token that was sent by email. If the token is valid,
    make the user verified.
    """

    @strawberry.input
    class VerifyAccountInput:
        token: str

    @strawberry.type()
    class VerifyAccountErrors(TokenErrorsInterface, OperationErrorsInterface):
        ...

    @wrap_token_errors(VerifyAccountErrors)
    @classmethod
    def resolve_mutation(
        cls, info: Info, input_: VerifyAccountInput
    ) -> MutationNormalOutput[VerifyAccountErrors]:
        try:
            app_settings.BACKEND.verify(input_.token)
            return MutationNormalOutput(success=True)
        except UserAlreadyVerified:
            return MutationNormalOutput(
                success=False,
                errors=cls.VerifyAccountErrors(
                    operation_error=ErrorMessage.from_code(OperationErrorCodes.ALREADY_VERIFIED)
                ),
            )


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

    @strawberry.type()
    class ResendActivationEmailErrors(
        EmailErrorsInterface, RawErrorsInterface, OperationErrorsInterface
    ):
        ...

    @classmethod
    def resolve_mutation(
        cls, info: Info, input_: ResendActivationEmailInput
    ) -> MutationNormalOutput:
        try:
            email = input_.email
            f = EmailForm({"email": email})
            if f.is_valid():
                user = app_settings.BACKEND.get_user_by_email(email)
                app_settings.BACKEND.resend_activation_email(info, user)
                return MutationNormalOutput(success=True)
            return MutationNormalOutput(
                success=False,
                errors=cls.ResendActivationEmailErrors(
                    raw_errors=f.errors.get_json_data(),
                ),
            )
        except ObjectDoesNotExist:
            return MutationNormalOutput(success=True)  # even if user is not registered
        except SMTPException:
            return MutationNormalOutput(
                success=False,
                errors=cls.ResendActivationEmailErrors(
                    email=ErrorMessage.from_code(EmailErrorCodes.EMAIL_FAILED)
                ),
            )
        except UserAlreadyVerified:
            return MutationNormalOutput(
                success=False,
                errors=cls.ResendActivationEmailErrors(
                    operation_errror=ErrorMessage.from_code(OperationErrorCodes.ALREADY_VERIFIED)
                ),
            )


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

    @strawberry.type()
    class SendPasswordResetEmailErrors(RawErrorsInterface, EmailErrorsInterface):
        ...

    @classmethod
    def resolve_mutation(
        cls, info, input_: SendPasswordResetEmailInput
    ) -> MutationNormalOutput[SendPasswordResetEmailErrors]:
        try:
            email = input_.email
            f = EmailForm({"email": email})
            if f.is_valid():
                app_settings.BACKEND.send_password_reset_email(get_user(info), info, [email])
                return MutationNormalOutput(success=True)
            return MutationNormalOutput(
                success=False,
                errors=cls.SendPasswordResetEmailErrors(
                    raw_error=f.errors.get_json_data(),
                ),
            )
        except ObjectDoesNotExist:
            return MutationNormalOutput(success=True)  # even if user is not registered
        except SMTPException:
            return MutationNormalOutput(
                success=False,
                errors=cls.SendPasswordResetEmailErrors(
                    email=ErrorMessage.from_code(EmailErrorCodes.EMAIL_FAILED)
                ),
            )
        except UserNotVerified:  # FIXME: This is not raised anywhere?
            user = app_settings.BACKEND.get_user_by_email(input_.email)
            try:
                app_settings.BACKEND.resend_activation_email(info, user)
                return MutationNormalOutput(
                    success=False,
                    errors=cls.SendPasswordResetEmailErrors(
                        operation_errror=ErrorMessage.from_code(OperationErrorCodes.UNVERIFIED)
                    ),
                )
            except SMTPException:
                return MutationNormalOutput(
                    success=False,
                    errors=cls.SendPasswordResetEmailErrors(
                        email=ErrorMessage.from_code(EmailErrorCodes.EMAIL_FAILED)
                    ),
                )


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

    @strawberry.type()
    class PasswordResetErrors(TokenErrorsInterface, RawErrorsInterface):
        ...

    @wrap_token_errors(PasswordResetErrors)
    @classmethod
    def resolve_mutation(
        cls, _, input_: PasswordResetInput
    ) -> MutationNormalOutput[PasswordResetErrors]:
        payload = get_payload_from_token(
            input_.token,
            TokenAction.PASSWORD_RESET,
            app_settings.EXPIRATION_PASSWORD_RESET_TOKEN,
        )
        user = app_settings.BACKEND.get_user_from_payload(payload)
        f = cls.form(user, asdict(input_))
        if f.is_valid():
            app_settings.BACKEND.revoke_user_refresh_token(user)
            f.save()  # type: ignore
            if not user.is_verified:
                user.set_verified(True)
                user_verified.send(sender=cls, user=user)

            return MutationNormalOutput(success=True)
        return MutationNormalOutput(
            success=False, errors=cls.PasswordResetErrors(raw_error=f.errors.get_json_data())
        )


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

    @strawberry.type()
    class PasswordSetErrors(RawErrorsInterface, TokenErrorsInterface, OperationErrorsInterface):
        ...

    @wrap_token_errors(PasswordSetErrors)
    @classmethod
    def resolve_mutation(
        cls, _, input_: PasswordSetInput
    ) -> MutationNormalOutput[PasswordSetErrors]:
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
                app_settings.BACKEND.revoke_user_refresh_token(user)
                user: UserProto = f.save()  # type: ignore
                if not user.is_verified:
                    user.set_verified(True)
                return MutationNormalOutput(success=True)
            return MutationNormalOutput(
                success=False, errors=cls.PasswordSetErrors(raw_error=f.errors.get_json_data())
            )
        except PasswordAlreadySetError:
            return MutationNormalOutput(
                success=False,
                errors=cls.PasswordSetErrors(
                    operation_error=ErrorMessage.from_code(OperationErrorCodes.PASSWORD_ALREADY_SET)
                ),
            )


class ObtainJSONWebTokenMixin(BaseMixin):
    """Obtain JSON web token for given user.

    Allow to perform login with different fields,
    The fields are defined on settings.

    Not verified users can log in by default. This
    can be changes on settings.

    If user is archived, make it unarchived and
    return `unarchiving=True` on OutputBase.
    """

    @strawberry.type()
    class ObtainJSONWebTokenErrors(TokenErrorsInterface, OperationErrorsInterface):
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            captcha: Optional[ErrorMessage[CaptchaErrorCodes]] = None

    if not app_settings.BACKEND.LOGIN_INPUT_TYPE:

        @strawberry.input
        @inject_fields(app_settings.LOGIN_FIELDS)
        class ObtainJSONWebTokenInput:
            password: str
            if app_settings.LOGIN_REQUIRE_CAPTCHA:
                identifier: UUID
                userEntry: str

        app_settings.BACKEND.LOGIN_INPUT_TYPE = ObtainJSONWebTokenInput

        if app_settings.REGISTER_REQUIRE_CAPTCHA:
            captcha: Optional[ErrorMessage[CaptchaErrorCodes]] = None

    @wrap_token_errors(ObtainJSONWebTokenErrors)
    @classmethod
    def resolve_mutation(
        cls, info, input_: app_settings.BACKEND.LOGIN_INPUT_TYPE
    ) -> ObtainJSONWebTokenOutput[ObtainJSONWebTokenErrors]:
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            if captcha_error := app_settings.BACKEND.validate_captcha(
                input_.identifier, input_.userEntry
            ):
                return ObtainJSONWebTokenOutput(
                    success=False,
                    errors=cls.ObtainJSONWebTokenErrors(
                        captcha=ErrorMessage.from_code(captcha_error)
                    ),
                )
        try:
            # authenticate against django authentication backends.
            user = app_settings.BACKEND.login(info, input_)
            if not user:
                return ObtainJSONWebTokenOutput(
                    success=False,
                    errors=cls.ObtainJSONWebTokenErrors(
                        operation_error=ErrorMessage.from_code(
                            OperationErrorCodes.INVALID_CREDENTIALS
                        )
                    ),
                )

            # gqlauth logic
            if user.is_archived:  # un-archive on login
                app_settings.BACKEND.unarchived(user)
            if user.is_verified or app_settings.ALLOW_LOGIN_NOT_VERIFIED:
                # successful login.
                return ObtainJSONWebTokenOutput.from_user(user)
            else:
                return ObtainJSONWebTokenOutput(
                    success=False,
                    errors=cls.ObtainJSONWebTokenErrors(
                        operation_error=ErrorMessage.from_code(OperationErrorCodes.UNVERIFIED)
                    ),
                )
        except PermissionDenied:
            # one of the authentication backends rejected the user.
            return ObtainJSONWebTokenOutput(
                success=False,
                errors=cls.ObtainJSONWebTokenErrors(
                    operation_error=ErrorMessage.from_code(OperationErrorCodes.UNAUTHENTICATED)
                ),
            )


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
    def resolve_action(cls, user: UserProto):
        user.set_archived(True)
        app_settings.BACKEND.revoke_user_refresh_token(user)


class DeleteAccountMixin(ArchiveOrDeleteMixin):
    """Delete account permanently or make `user.is_active=False`.

    The behavior is defined on settings.
    Anyway user refresh tokens are revoked.

    User must be verified and confirm password.
    """

    @classmethod
    def resolve_action(cls, user: UserProto):
        if app_settings.ALLOW_DELETE_ACCOUNT:
            app_settings.BACKEND.revoke_user_refresh_token(user)
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

    class PasswordChangeErrors(RawErrorsInterface):
        ...

    @classmethod
    def resolve_mutation(
        cls, info: Info, input_: PasswordChangeInput
    ) -> ObtainJSONWebTokenOutput[PasswordChangeErrors]:
        user = get_user(info)
        if error := confirm_password(user, input_):
            return ObtainJSONWebTokenOutput(**asdict(error))

        args = asdict(input_)
        f = cls.form(user, args)  # type: ignore
        if f.is_valid():
            app_settings.BACKEND.revoke_user_refresh_token(user)
            user: UserProto = f.save()  # type: ignore
            return ObtainJSONWebTokenOutput.from_user(user)
        else:
            return ObtainJSONWebTokenOutput(
                success=False, errors=cls.PasswordChangeErrors(raw_error=f.errors.get_json_data())
            )


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

    @strawberry.type()
    class UpdateAccountErrors(RawErrorsInterface):
        ...

    @classmethod
    def resolve_mutation(
        cls, info, input_: UpdateAccountInput
    ) -> MutationNormalOutput[UpdateAccountErrors]:
        f = cls.form(
            asdict(input_),
            instance=get_user(info),
        )
        if f.is_valid():
            f.save()
            return MutationNormalOutput(success=True)
        else:
            return MutationNormalOutput(
                success=False, errors=cls.UpdateAccountErrors(raw_error=f.errors.get_json_data())
            )


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
    obtain a brand-new re/fresh-token
    This is an alternative to log in when your token expired.
    """

    @strawberry.type()
    class RefreshTokenErrors(TokenErrorsInterface):
        ...

    @strawberry.input()
    class RefreshTokenInput:
        refresh_token: str

    @classmethod
    def resolve_mutation(
        cls, info, input_: RefreshTokenInput
    ) -> ObtainJSONWebTokenOutput[RefreshTokenErrors]:
        try:
            res = RefreshToken.objects.get(token=input_.refresh_token)
        except RefreshToken.DoesNotExist:
            return ObtainJSONWebTokenOutput(
                success=False,
                errors=cls.RefreshTokenErrors(
                    token=ErrorMessage.from_code(TokenErrorCodes.INVALID_TOKEN)
                ),
            )
        user = res.user
        if res.is_expired_():
            return ObtainJSONWebTokenOutput(
                success=False,
                errors=cls.RefreshTokenErrors(
                    token=ErrorMessage.from_code(TokenErrorCodes.TOKEN_EXPIRED)
                ),
            )
        res.revoke()
        # fields that are determined by if statements are not recognized by mypy.
        ret = ObtainJSONWebTokenOutput(
            success=True, token=TokenType.from_user(user), refresh_token=res  # type: ignore
        )
        ret.refresh_token = cast(RefreshTokenType, RefreshToken.from_user(user))
        return ret


class RevokeTokenMixin(BaseMixin):
    """### Suspends a refresh token.

    *token must exist to be revoked.*
    """

    @strawberry.input
    class RevokeTokenInput:
        refresh_token: str

    class RevokeTokenErrors(TokenErrorsInterface):
        ...

    @classmethod
    def resolve_mutation(
        cls, _: Info, input_: RevokeTokenInput
    ) -> RevokeRefreshTokenType[RevokeTokenErrors]:
        try:
            refresh_token = RefreshToken.objects.get(
                token=input_.refresh_token, revoked__isnull=True
            )
            refresh_token.revoke()
            return RevokeRefreshTokenType(
                success=True, refresh_token=cast(RefreshTokenType, refresh_token)
            )
        except RefreshToken.DoesNotExist:
            return RevokeRefreshTokenType(
                success=False,
                errors=cls.RevokeTokenErrors(
                    token=ErrorMessage.from_code(TokenErrorCodes.INVALID_TOKEN)
                ),
            )
