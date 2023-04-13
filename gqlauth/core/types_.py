from __future__ import annotations

import enum
from typing import Generic, Type, TypeVar

import strawberry
from graphql import GraphQLError


class GQLAuthError(GraphQLError):
    def __init__(self, code: ErrorCodes, *args, **kwargs):
        kwargs["message"] = ""
        super().__init__(*args, **kwargs)
        if not self.message:
            self.message = code.value


class ErrorCodes(enum.Enum):
    INVALID_TOKEN = "Invalid token."
    TOKEN_EXPIRED = "Token Expired."
    MISSING_TOKEN = "No token provided"

    INVALID_PASSWORD = "Invalid password."

    CAPTCHA_INVALID = "Captcha wrong, try again."
    CAPTCHA_MAX_RETRIES = "Maximum tries exceeded, please refresh the captcha."
    CAPTCHA_EXPIRED = "Expired or not Existed captcha please refresh."

    EMAIL_FAILED = "Failed to send email."

    # operation errors
    ALREADY_VERIFIED = "Account already verified."
    PASSWORD_ALREADY_SET = "Password already set for account."
    UNAUTHENTICATED = "Unauthenticated."
    UNVERIFIED = "Please verify your account."
    INVALID_CREDENTIALS = "Please, enter valid credentials."


def create_sb_enum_from_errors(klass_name: str, *errors: ErrorCodes) -> type[ErrorCodes]:
    ret = enum.Enum("GqlAuth" + klass_name, {error.name: error.value for error in errors})
    return strawberry.enum(ret)


TokenErrorCodes = create_sb_enum_from_errors(
    "TokenErrorCodes", ErrorCodes.INVALID_TOKEN, ErrorCodes.TOKEN_EXPIRED
)

CaptchaErrorCodes = create_sb_enum_from_errors(
    "CaptchaErrorCodes",
    ErrorCodes.CAPTCHA_INVALID,
    ErrorCodes.CAPTCHA_MAX_RETRIES,
    ErrorCodes.CAPTCHA_EXPIRED,
)

EmailErrorCodes = create_sb_enum_from_errors("EmailErrorCodes", ErrorCodes.EMAIL_FAILED)

OperationErrorCodes = create_sb_enum_from_errors(
    "OperationErrorCodes",
    ErrorCodes.ALREADY_VERIFIED,
    ErrorCodes.PASSWORD_ALREADY_SET,
    ErrorCodes.UNAUTHENTICATED,
    ErrorCodes.INVALID_CREDENTIALS,
)

T_ErrorCode = TypeVar("T_ErrorCode", bound=ErrorCodes)
T = TypeVar("T", bound=Type)


@strawberry.type
class MutationNormalOutput(Generic[T]):
    success: bool
    errors: T


@strawberry.type
class ErrorMessage(Generic[T_ErrorCode]):
    message: str
    code: T_ErrorCode

    @classmethod
    def from_code(cls, code: ErrorCodes) -> ErrorMessage:
        return cls(message=code.value, code=code)


@strawberry.interface
class RawErrorsInterface:
    raw_errors: strawberry.scalars.JSON | None = None


@strawberry.interface
class EmailErrorsInterface:
    email: ErrorMessage[EmailErrorCodes] | None = None


@strawberry.interface
class TokenErrorsInterface:
    token: ErrorMessage[TokenErrorCodes] | None = None


@strawberry.interface
class OperationErrorsInterface:
    operation_error: ErrorMessage[OperationErrorCodes] | None = None
