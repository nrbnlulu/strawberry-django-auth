from enum import Enum
from typing import Optional, TypeVar

from django.utils.translation import gettext as _
import strawberry

from gqlauth.core.scalars import ExpectedErrorType

T = TypeVar("T")


@strawberry.type
class MutationNormalOutput:
    success: bool
    errors: Optional[ExpectedErrorType] = None


@strawberry.type
class GQLAuthError:
    code: "GQLAuthErrors"
    message: Optional[str] = None

    def __post_init__(self):
        if not self.message:
            assert isinstance(self.code.value, str)
            self.message = _(self.code.value)
        self.message = _(self.message)


@strawberry.enum
class GQLAuthErrors(Enum):
    UNAUTHENTICATED = "Unauthenticated."
    INVALID_TOKEN = "Invalid token."
    EXPIRED_TOKEN = "Expired token."
    NO_SUFFICIENT_PERMISSIONS = "Permissions found could not satisfy the required permissions."
    NOT_VERIFIED = "Please verify your account."
