from smtplib import SMTPException
from uuid import UUID

from django.core.signing import BadSignature, SignatureExpired
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.db import transaction
from django.utils.module_loading import import_string

from strawberry_django_jwt.exceptions import JSONWebTokenError, JSONWebTokenExpired

from gqlauth.forms import RegisterForm, EmailForm, UpdateAccountForm, PasswordLessRegisterForm
from gqlauth.utils import normalize_fields, g_user
from gqlauth.models import Captcha, UserStatus
from gqlauth.settings import gqlauth_settings as app_settings
from gqlauth.exceptions import (
    UserAlreadyVerified,
    UserNotVerified,
    TokenScopeError,
    EmailAlreadyInUse,
    InvalidCredentials,
    PasswordAlreadySetError,
)
from gqlauth.constants import Messages, TokenAction
from gqlauth.utils import revoke_user_refresh_token, get_payload_from_token, using_refresh_tokens
from gqlauth.shortcuts import get_user_by_email, get_user_to_login
from gqlauth.signals import user_registered, user_verified
from gqlauth.decorators import (
    password_confirmation_required,
    verification_required,
    secondary_email_required,
    login_required
)

UserModel = get_user_model()
if app_settings.EMAIL_ASYNC_TASK and isinstance(app_settings.EMAIL_ASYNC_TASK, str):
    async_email_func = import_string(app_settings.EMAIL_ASYNC_TASK)
else:
    async_email_func = None


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

    class _meta:

        password_fields = (
            []
            if app_settings.ALLOW_PASSWORDLESS_REGISTRATION
            else ["password1", "password2"]
        )
        extra_fields = password_fields
        if app_settings.REGISTER_REQUIRE_CAPTCHA:
            captcha_fields = {'identifier': UUID, "userEntry": str}
            extra_fields = normalize_fields(captcha_fields, password_fields)

        _required_inputs = normalize_fields(
            app_settings.REGISTER_MUTATION_FIELDS, extra_fields
        )
        _inputs = app_settings.REGISTER_MUTATION_FIELDS_OPTIONAL

    form = (
        PasswordLessRegisterForm
        if app_settings.ALLOW_PASSWORDLESS_REGISTRATION
        else RegisterForm
    )

    @classmethod
    def check_captcha(cls, input_):
        uuid = input_.get('identifier')
        try:
            obj = Captcha.objects.get(uuid=uuid)
        except Captcha.DoesNotExist:
            return Messages.CAPTCHA_EXPIRED
        return obj.validate(input_.get('userEntry'))

    @classmethod
    def resolve_mutation(cls, info, **input_):
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            check_res = cls.check_captcha(input_)
            if not check_res == Messages.CAPTCHA_VALID:
                return cls.output(success=False, errors={'captcha': check_res})

        try:
            with transaction.atomic():
                f = cls.form(input_)
                if f.is_valid():
                    email = input_.get('email')
                    UserStatus.clean_email(email)
                    user = f.save()
                    send_activation = (
                            app_settings.SEND_ACTIVATION_EMAIL is True and email
                    )
                    send_password_set = (
                            app_settings.ALLOW_PASSWORDLESS_REGISTRATION is True
                            and app_settings.SEND_PASSWORD_SET_EMAIL is True
                            and email
                    )
                    if send_activation:
                        # TODO CHECK FOR EMAIL ASYNC SETTING
                        if async_email_func:
                            async_email_func(user.status.send_activation_email, (info,))
                        else:
                            user.status.send_activation_email(info)

                    if send_password_set:
                        # TODO CHECK FOR EMAIL ASYNC SETTING
                        if async_email_func:
                            async_email_func(
                                user.status.send_password_set_email, (info,)
                            )
                        else:
                            user.status.send_password_set_email(info)

                    user_registered.send(sender=cls, user=user)
                    return cls.output(success=True)
                else:
                    return cls.output(success=False, errors=f.errors.get_json_data())
        except EmailAlreadyInUse:
            return cls.output(
                success=False,
                # if the email was set as a secondary email,
                # the RegisterForm will not catch it,
                # so we need to run UserStatus.clean_email(email)
                errors={UserModel.EMAIL_FIELD: Messages.EMAIL_IN_USE},
            )
        except SMTPException:
            return cls.output(success=False, errors=Messages.EMAIL_FAIL)


class VerifyAccountMixin:
    """
    Verify user account.

    Receive the token that was sent by email.
    If the token is valid, make the user verified
    by making the `user.status.verified` field true.
    """

    class _meta:
        _required_inputs = ["token"]

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            token = input_.get("token")
            UserStatus.verify(token)
            return cls.output(success=True)
        except UserAlreadyVerified:
            return cls.output(success=False, errors=Messages.ALREADY_VERIFIED)
        except SignatureExpired:
            return cls.output(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return cls.output(success=False, errors=Messages.INVALID_TOKEN)


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

    class _meta:
        _required_inputs = ["token"]

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            token = input_.get("token")
            UserStatus.verify_secondary_email(token)
            return cls.output(success=True)
        except EmailAlreadyInUse:
            # while the token was sent and the user haven't
            # verified, the email was free. If other account
            # was created with it, it is already in use.
            return cls.output(success=False, errors=Messages.EMAIL_IN_USE)
        except SignatureExpired:
            return cls.output(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return cls.output(success=False, errors=Messages.INVALID_TOKEN)


class ResendActivationEmailMixin:
    """
    Sends activation email.

    It is called resend because theoretically
    the first activation email was sent when
    the user registered.

    If there is no user with the requested email,
    a successful response is returned.
    """

    class _meta:
        _required_inputs = ["email"]

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            email = input_.get("email")
            f = EmailForm({"email": email})
            if f.is_valid():
                user = get_user_by_email(email)
                if async_email_func:
                    async_email_func(user.status.resend_activation_email, (info,))
                else:
                    user.status.resend_activation_email(info)
                return cls.output(success=True)
            return cls.output(success=False, errors=f.errors.get_json_data())
        except ObjectDoesNotExist:
            return cls.output(success=True)  # even if user is not registred
        except SMTPException:
            return cls.output(success=False, errors=Messages.EMAIL_FAIL)
        except UserAlreadyVerified:
            return cls.output(success=False, errors={"email": Messages.ALREADY_VERIFIED})


class SendPasswordResetEmailMixin:
    """
    Send password reset email.

    For non verified users, send an activation
    email instead.

    Accepts both primary and secondary email.

    If there is no user with the requested email,
    a successful response is returned.
    """

    class _meta:
        _required_inputs = ["email"]

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            email = input_.get("email")
            f = EmailForm({"email": email})
            if f.is_valid():
                user = get_user_by_email(email)
                if async_email_func:
                    async_email_func(
                        user.status.send_password_reset_email, (info, [email])
                    )
                else:
                    user.status.send_password_reset_email(info, [email])
                return cls.output(success=True)
            return cls.output(success=False, errors=f.errors.get_json_data())
        except ObjectDoesNotExist:
            return cls.output(success=True)  # even if user is not registred
        except SMTPException:
            return cls.output(success=False, errors=Messages.EMAIL_FAIL)
        except UserNotVerified:
            user = get_user_by_email(email)
            try:
                if async_email_func:
                    async_email_func(user.status.resend_activation_email, (info,))
                else:
                    user.status.resend_activation_email(info)
                return cls(
                    success=False,
                    errors={"email": Messages.NOT_VERIFIED_PASSWORD_RESET},
                )
            except SMTPException:
                return cls.output(success=False, errors=Messages.EMAIL_FAIL)


class PasswordResetMixin:
    """
    Change user password without old password.

    Receive the token that was sent by email.

    If token and new passwords are valid, update
    user password and in case of using refresh
    tokens, revoke all of them.

    Also, if user has not been verified yet, verify it.
    """

    class _meta:
        _required_inputs = ["token", "new_password1", "new_password2"]

    form = SetPasswordForm

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            token = input_.get("token")
            payload = get_payload_from_token(
                token,
                TokenAction.PASSWORD_RESET,
                app_settings.EXPIRATION_PASSWORD_RESET_TOKEN,
            )
            user = UserModel._default_manager.get(**payload)
            form_dict = {
                'new_password1': input_['newPassword1'],
                'new_password2': input_['newPassword2']
            }
            f = cls.form(user, form_dict)
            if f.is_valid():
                revoke_user_refresh_token(user)
                user = f.save()
                if user.status.verified is False:
                    user.status.verified = True
                    user.status.save(update_fields=["verified"])
                    user_verified.send(sender=cls, user=user)

                return cls.output(success=True)
            return cls.output(success=False, errors=f.errors.get_json_data())
        except SignatureExpired:
            return cls.output(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return cls.output(success=False, errors=Messages.INVALID_TOKEN)


class PasswordSetMixin:
    """
    Set user password - for passwordless registration

    Receive the token that was sent by email.

    If token and new passwords are valid, set
    user password and in case of using refresh
    tokens, revoke all of them.

    Also, if user has not been verified yet, verify it.
    """

    class _meta:
        _required_inputs = ["token", "new_password1", "new_password2"]

    form = SetPasswordForm

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            token = input_.get("token")
            payload = get_payload_from_token(
                token,
                TokenAction.PASSWORD_SET,
                app_settings.EXPIRATION_PASSWORD_SET_TOKEN,
            )
            user = UserModel._default_manager.get(**payload)
            form_dict = {
                'new_password1': input_['newPassword1'],
                'new_password2': input_['newPassword2']
            }
            f = cls.form(user, form_dict)
            if f.is_valid():
                # Check if user has already set a password
                if user.has_usable_password():
                    raise PasswordAlreadySetError
                revoke_user_refresh_token(user)
                user = f.save()

                if user.status.verified is False:
                    user.status.verified = True
                    user.status.save(update_fields=["verified"])

                return cls.output(success=True)
            return cls.output(success=False, errors=f.errors.get_json_data())
        except SignatureExpired:
            return cls.output(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError):
            return cls.output(success=False, errors=Messages.INVALID_TOKEN)
        except (PasswordAlreadySetError):
            return cls.output(success=False, errors=Messages.PASSWORD_ALREADY_SET)


class ObtainJSONWebTokenMixin:
    """
    Obtain JSON web token for given user.

    Allow to perform login with different fields,
    and secondary email if set. The fields are
    defined on settings.

    Not verified users can login by default. This
    can be changes on settings.

    If user is archived, make it unarchive and
    return `unarchiving=True` on OutputBase.
    """

    class _meta:
        additional_req = {}
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            additional_req.update({'identifier': UUID, 'userEntry': str})
        _required_inputs = normalize_fields(app_settings.LOGIN_REQUIRED_FIELDS, additional_req)

        _inputs = app_settings.LOGIN_OPTIONAL_FIELDS
        _parent_resolver_name = 'obtain'

    @classmethod
    def check_captcha(cls, **input_):
        uuid = input_.get("identifier")
        try:
            obj = Captcha.objects.get(id=uuid)
        except Captcha.DoesNotExist:
            return Messages.CAPTCHA_EXPIRED

        return obj.validate(input_.get('userEntry'))

    @classmethod
    def resolve_mutation(cls, info, **input_):
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            check_res = cls.check_captcha(**input_)
            if not check_res == Messages.CAPTCHA_VALID:
                return cls.output(success=False, errors={'captcha': check_res})

        try:
            USERNAME_FIELD = UserModel.USERNAME_FIELD
            unarchiving = False

            # extract USERNAME_FIELD to use in query
            username = input_.get("username")
            password = input_.get("password")
            query_input_ = {USERNAME_FIELD: username}
            user = get_user_to_login(**query_input_)
            query_input_['password'] = password

            if user.status.archived is True:  # unarchive on login
                UserStatus.unarchive(user)
                unarchiving = True

            if user.status.verified or app_settings.ALLOW_LOGIN_NOT_VERIFIED:
                # this will raise if not successful
                res = cls.obtain.get_result(None, None, [cls, info], query_input_)

                return cls.output(success=True, obtainPayload=res)
            else:
                raise UserNotVerified

        except (JSONWebTokenError, ObjectDoesNotExist, InvalidCredentials):
            return cls.output(success=False, errors=Messages.INVALID_CREDENTIALS)
        except UserNotVerified:
            return cls.output(success=False, errors=Messages.NOT_VERIFIED)


class ArchiveOrDeleteMixin:
    @classmethod
    @verification_required
    @password_confirmation_required
    def resolve_mutation(cls, info, **input_):
        user = g_user(info)
        cls.resolve_action(user, info=info)
        return cls.output(success=True)


class ArchiveAccountMixin(ArchiveOrDeleteMixin):
    """
    Archive account and revoke refresh tokens.

    User must be verified and confirm password.
    """

    class _meta:
        _required_inputs = ["password"]

    @classmethod
    def resolve_action(cls, user, **input_):
        UserStatus.archive(user)
        revoke_user_refresh_token(user=user)


class DeleteAccountMixin(ArchiveOrDeleteMixin):
    """
    Delete account permanently or make `user.is_active=False`.

    The behavior is defined on settings.
    Anyway user refresh tokens are revoked.

    User must be verified and confirm password.
    """

    class _meta:
        _required_inputs = ["password"]

    @classmethod
    def resolve_action(cls, user, *args, **input_):
        if app_settings.ALLOW_DELETE_ACCOUNT:
            revoke_user_refresh_token(user=user)
            user.delete()


class PasswordChangeMixin:
    """
    Change account password when user knows the old password.

    A new token and refresh token are sent. User must be verified.
    """

    class _meta:
        _required_inputs = ["old_password", "new_password1", "new_password2"]
        _outputs = []
        if using_refresh_tokens():
            _outputs = ["refresh_token", 'token']
        _parent_resolver_name = 'obtain'

    form = PasswordChangeForm

    @classmethod
    @verification_required
    @password_confirmation_required
    def resolve_mutation(cls, info, **input_):
        user = g_user(info)
        form_dict = {
            'old_password': input_['oldPassword'],
            'new_password1': input_['newPassword1'],
            'new_password2': input_['newPassword2']
        }
        f = cls.form(user, form_dict)
        if f.is_valid():
            revoke_user_refresh_token(user)
            user = f.save()
            parent_input = {
                user.USERNAME_FIELD: getattr(user, user.USERNAME_FIELD),
                'password': input_.get("newPassword1")
            }
            parent_res = cls.obtain.get_result(
                None, None, [cls, info], parent_input
            )
            return cls.output(success=True, obtainPayload=parent_res)
        else:
            return cls.output(success=False, errors=f.errors.get_json_data())


class UpdateAccountMixin:
    """
    Update user model fields, defined on settings.

    User must be verified.
    """

    class _meta:
        _inputs = app_settings.UPDATE_MUTATION_FIELDS

    form = UpdateAccountForm

    @classmethod
    @verification_required
    def resolve_mutation(cls, info, **input_):
        user = g_user(info)
        f = cls.form(
        {
            'first_name': input_.get('firstName'),
            'last_name': input_.get('lastName')
        },
        instance=user)
        if f.is_valid():
            f.save()
            return cls.output(success=True)
        else:
            return cls.output(success=False, errors=f.errors.get_json_data())


class VerifyTokenMixin:
    """
    Checks if a token is not expired and correct
    """

    class _meta:
        _parent_resolver_name = 'verify'

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            payload = cls.verify.get_result(None, None, [cls, info], input_)
            return cls.output(success=True, verifyPayload=(payload))
        except JSONWebTokenExpired:
            return cls.output(success=False, errors=Messages.EXPIRED_TOKEN)
        except JSONWebTokenError:
            return cls.output(success=False, errors=Messages.INVALID_TOKEN)


class RefreshTokenMixin:
    """
    ### refreshToken to refresh your token:

    using the refresh token you already got during authorization.
    this will obtain a brand-new token (and possibly a refresh token)
    with renewed expiration time for non-expired tokens
    """

    class _meta:
        _parent_resolver_name = 'refresh'

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            parent_input = {
                'refresh_token': input_.get('refreshToken')
            }

            res = cls.refresh.get_result(None, None, [cls, info], parent_input)
            return cls.output(success=True, refreshPayload=res)

        except JSONWebTokenExpired:
            return cls.output(success=False, errors=Messages.EXPIRED_TOKEN)
        except JSONWebTokenError:
            return cls.output(success=False, errors=Messages.INVALID_TOKEN)


class RevokeTokenMixin:
    """
    Suspends a refresh token
    """

    class _meta:
        _parent_resolver_name = 'revoke'

    @classmethod
    def resolve_mutation(cls, info, **input_):
        try:
            parent_input = {
                'refresh_token': input_.get('refreshToken')
            }

            res = cls.revoke.get_result(None, None, [cls, info], parent_input)
            return cls.output(success=True, revokePayload=res)

        except JSONWebTokenExpired:
            return cls.output(success=False, errors=Messages.EXPIRED_TOKEN)
        except JSONWebTokenError:
            return cls.output(success=False, errors=Messages.INVALID_TOKEN)


class SendSecondaryEmailActivationMixin:
    """
    Send activation to secondary email.

    User must be verified and confirm password.
    """

    class _meta:
        _required_inputs = ["password"]

    @classmethod
    @verification_required
    @password_confirmation_required
    def resolve_mutation(cls, info, **input_):
        try:
            email = input_.get("email")
            f = EmailForm({"email": email})
            if f.is_valid():
                user = g_user(info)
                if async_email_func:
                    async_email_func(
                        user.status.send_secondary_email_activation, (info, email)
                    )
                else:
                    user.status.send_secondary_email_activation(info, email)
                return cls.output(success=True)
            return cls.output(success=False, errors=f.errors.get_json_data())
        except EmailAlreadyInUse:
            # while the token was sent and the user haven't verified,
            # the email was free. If other account was created with it
            # it is already in use
            return cls.output(success=False, errors={"email": Messages.EMAIL_IN_USE})
        except SMTPException:
            return cls.output(success=False, errors=Messages.EMAIL_FAIL)


class SwapEmailsMixin:
    """
    Swap between primary and secondary emails.

    Require password confirmation.
    """

    class _meta:
        _required_inputs = ["password"]

    @classmethod
    @secondary_email_required
    @password_confirmation_required
    def resolve_mutation(cls, info, **input_):
        info.context.user.status.swap_emails()
        return cls.output(success=True)


class RemoveSecondaryEmailMixin:
    """
    Remove user secondary email.

    Require password confirmation.
    """

    class _meta:
        _required_inputs = ["password"]

    @classmethod
    @secondary_email_required
    @password_confirmation_required
    def resolve_mutation(cls, info, **input_):
        info.context.user.status.remove_secondary_email()
        return cls.output(success=True)
