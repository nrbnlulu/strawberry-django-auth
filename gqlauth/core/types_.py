from enum import Enum
from typing import Generic, Optional, TypeVar

from django.utils.translation import gettext as _
import strawberry

from gqlauth.core.scalars import ExpectedErrorType

T = TypeVar("T")


@strawberry.type
class MutationNormalOutput:
    success: bool
    errors: Optional[ExpectedErrorType] = None


@strawberry.type
class ErrorMessage:
    code: "GqlAuthError" = None
    message: str = None

    def __post_init__(self):
        if not self.message:
            assert isinstance(self.code.value, str)
            self.message = _(self.code.value)
        self.message = _(self.message)


@strawberry.type
class AuthOutput(Generic[T]):
    node: Optional[T] = None
    error: Optional[ErrorMessage] = None
    success: bool = False

    def __post_init__(self):
        if self.node:
            assert not self.error
            self.success = True


@strawberry.enum
class GqlAuthError(Enum):
    UNAUTHENTICATED = "Unauthenticated."
    INVALID_TOKEN = "Invalid token."
    EXPIRED_TOKEN = "Expired token."
    NO_SUFFICIENT_PERMISSIONS = "Permissions found could not satisfy the required permissions."
    NOT_VERIFIED = "Please verify your account."
