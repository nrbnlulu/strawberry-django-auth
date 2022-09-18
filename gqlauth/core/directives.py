from abc import ABC, abstractmethod
from typing import Any, List, Optional

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
import strawberry
from strawberry.schema_directive import Location
from strawberry.types import Info

from gqlauth.core.types_ import ErrorMessage, GqlAuthError
from gqlauth.core.utils import get_status

USER_MODEL = get_user_model()

__all__ = ["BaseAuthDirective", "IsAuthenticated", "HasPermission", "IsVerified"]


class BaseAuthDirective(ABC):
    @abstractmethod
    def resolve_permission(
        self, user: USER_MODEL, source: Any, info: Info, args: list, kwargs: dict
    ) -> Optional[ErrorMessage]:
        ...


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires authentication",
)
class IsAuthenticated(BaseAuthDirective):
    def resolve_permission(self, user: USER_MODEL, source: Any, info: Info, *args, **kwargs):
        if not user.is_authenticated:
            return ErrorMessage(code=GqlAuthError.UNAUTHENTICATED)
        return None


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires the user to be verified",
)
class IsVerified(BaseAuthDirective):
    def resolve_permission(self, user: USER_MODEL, source: Any, info: Info, *args, **kwargs):
        if (status := get_status(user)) and status.verified:
            return None
        return ErrorMessage(code=GqlAuthError.NOT_VERIFIED)


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires a certain permissions to be resolved.",
)
class HasPermission(BaseAuthDirective):
    permissions: strawberry.Private[List[str]]

    def resolve_permission(self, user: USER_MODEL, source: Any, info: Info, *args, **kwargs):
        for permission in self.permissions:
            if not user.has_perm(permission):
                return ErrorMessage(
                    code=GqlAuthError.NO_SUFFICIENT_PERMISSIONS,
                    message=_(
                        f"User {user.first_name or getattr(user, user.USERNAME_FIELD, None)}, has not sufficient permissions for {info.path.key}"
                    ),
                )
        return None
