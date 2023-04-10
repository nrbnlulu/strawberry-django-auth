from typing import TypedDict

from django.utils.translation import gettext as _


class ErrorMessageDict(TypedDict):
    message: str
    code: str


class MessagesDict(TypedDict):
    messages: list[ErrorMessageDict]


class Messages:
    INVALID_PASSWORD = MessagesDict(
        messages=[{"message": _("Invalid password."), "code": "invalid_password"}]
    )
    UNAUTHENTICATED = MessagesDict(
        messages=[{"message": _("Unauthenticated."), "code": "unauthenticated"}]
    )
    INVALID_TOKEN = MessagesDict(
        messages=[{"message": _("Invalid token."), "code": "invalid_token"}]
    )
    EXPIRED_TOKEN = MessagesDict(
        messages=[{"message": _("Expired token."), "code": "expired_token"}]
    )
    NO_SUFFICIENT_PERMISSIONS = MessagesDict(
        messages=[{"message": _("Expired token."), "code": "expired_token"}]
    )

    # captcha messages
    CAPTCHA_VALID = MessagesDict(
        messages=[{"message": _("Captcha successfully validated!"), "code": "valid_captcha"}]
    )
    CAPTCHA_INVALID = MessagesDict(
        messages=[{"message": _("Captcha wrong, try again."), "code": "invalid_captcha"}]
    )
    CAPTCHA_MAX_RETRIES = MessagesDict(
        messages=[
            {
                "message": _("Maximum tries exceeded, please refresh the captcha."),
                "code": "max_retries_exceeded",
            }
        ]
    )
    CAPTCHA_EXPIRED = MessagesDict(
        messages=[
            {
                "message": _("Expired or not Existed captcha please refresh."),
                "code": "expired_captcha",
            }
        ]
    )

    ALREADY_VERIFIED = MessagesDict(
        messages=[{"message": _("Account already verified."), "code": "already_verified"}]
    )
    EMAIL_FAIL = MessagesDict(
        messages=[{"message": _("Failed to send email."), "code": "email_fail"}]
    )
    INVALID_CREDENTIALS = MessagesDict(
        messages=[
            {
                "message": _("Please, enter valid credentials."),
                "code": "invalid_credentials",
            }
        ]
    )
    NOT_VERIFIED = MessagesDict(
        messages=[{"message": _("Please verify your account."), "code": "not_verified"}]
    )
    NOT_VERIFIED_PASSWORD_RESET = MessagesDict(
        messages=[
            {
                "message": _("Verify your account. A new verification email was sent."),
                "code": "not_verified",
            }
        ]
    )
    PASSWORD_ALREADY_SET = MessagesDict(
        messages=[
            {
                "message": _("Password already set for account."),
                "code": "password_already_set",
            }
        ]
    )
