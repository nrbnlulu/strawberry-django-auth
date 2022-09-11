from enum import Enum

from django.utils.translation import gettext as _
import strawberry


# TODO: delete this.
class Messages:
    INVALID_PASSWORD = [{"message": _("Invalid password."), "code": "invalid_password"}]
    UNAUTHENTICATED = [{"message": _("Unauthenticated."), "code": "unauthenticated"}]
    INVALID_TOKEN = [{"message": _("Invalid token."), "code": "invalid_token"}]
    EXPIRED_TOKEN = [{"message": _("Expired token."), "code": "expired_token"}]
    NO_SUFFICIENT_PERMISSIONS = [{"message": _("Expired token."), "code": "expired_token"}]

    # captcha messages
    CAPTCHA_VALID = [{"message": _("Captcha successfully validated!"), "code": "valid_captcha"}]
    CAPTCHA_INVALID = [{"message": _("Captcha wrong, try again."), "code": "invalid_captcha"}]
    CAPTCHA_MAX_RETRIES = [
        {
            "message": _("Maximum tries exceeded, please refresh the captcha."),
            "code": "max_retries_exceeded",
        }
    ]
    CAPTCHA_EXPIRED = [
        {
            "message": _("Expired or not Existed captcha please refresh."),
            "code": "expired_captcha",
        }
    ]

    ALREADY_VERIFIED = [{"message": _("Account already verified."), "code": "already_verified"}]
    EMAIL_FAIL = [{"message": _("Failed to send email."), "code": "email_fail"}]
    INVALID_CREDENTIALS = [
        {
            "message": _("Please, enter valid credentials."),
            "code": "invalid_credentials",
        }
    ]
    NOT_VERIFIED = [{"message": _("Please verify your account."), "code": "not_verified"}]
    NOT_VERIFIED_PASSWORD_RESET = [
        {
            "message": _("Verify your account. A new verification email was sent."),
            "code": "not_verified",
        }
    ]
    EMAIL_IN_USE = [{"message": _("A user with that email already exists."), "code": "unique"}]
    SECONDARY_EMAIL_REQUIRED = [
        {
            "message": _("You need to setup a secondary email to proceed."),
            "code": "secondary_email_required",
        }
    ]
    PASSWORD_ALREADY_SET = [
        {
            "message": _("Password already set for account."),
            "code": "password_already_set",
        }
    ]


class TokenAction:
    ACTIVATION = "activation"
    PASSWORD_RESET = "password_reset"
    ACTIVATION_SECONDARY_EMAIL = "activation_secondary_email"
    PASSWORD_SET = "password_set"


@strawberry.enum
class Error(Enum):
    INVALID_PASSWORD = "Invalid password."
    UNAUTHENTICATED = "Unauthenticated."
    INVALID_TOKEN = "Invalid token."
    EXPIRED_TOKEN = "Expired token."
    NO_SUFFICIENT_PERMISSIONS = "Expired token."

    CAPTCHA_INVALID = "Captcha wrong, try again."
    CAPTCHA_MAX_RETRIES = "Maximum tries exceeded, please refresh the captcha"
    CAPTCHA_EXPIRED = "Expired or not Existed captcha please refresh."

    ALREADY_VERIFIED = "Account already verified."
    INVALID_CREDENTIALS = "Please, enter valid credentials."
    NOT_VERIFIED = "Please verify your account."
    NOT_VERIFIED_PASSWORD_RESET = "Verify your account. A new verification email was sent."

    EMAIL_IN_USE = "A user with that email already exists."
    EMAIL_FAIL = "Failed to send email."
    SECONDARY_EMAIL_REQUIRED = "You need to setup a secondary email to proceed."
    PASSWORD_ALREADY_SET = "Password already set for account."

    DJANGO_ERROR = ""
