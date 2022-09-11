from typing import Generic, List, Optional, TypeVar

from django.utils.translation import gettext as _
import strawberry

from gqlauth.core.constants import Error
from gqlauth.core.scalars import ExpectedErrorType

T = TypeVar("T")


@strawberry.type
class MutationNormalOutput:
    success: bool
    errors: Optional[ExpectedErrorType] = None


@strawberry.type
class ErrorMessage:
    code: Error
    message: str = None

    def __post_init__(self):
        if not self.message:
            assert isinstance(self.code.value, str)
            self.message = _(self.code.value)
        self.message = _(self.message)


@strawberry.type
class FieldError(ErrorMessage):
    field: str


@strawberry.type
class AuthError:
    non_field_errors: List[ErrorMessage] = strawberry.field(default_factory=list)
    field_errors: List[FieldError] = strawberry.field(default_factory=list)


@strawberry.type
class AuthWrapper(Generic[T]):
    success: bool = True
    errors: Optional[AuthError] = strawberry.field(default_factory=AuthError)

    data: Optional[T] = None
