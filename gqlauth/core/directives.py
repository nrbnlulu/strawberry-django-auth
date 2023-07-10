import dataclasses
from typing import Any, Callable, final

import strawberry
from strawberry.schema_directive import Location
from strawberry.types import Info
from strawberry_django.permissions import DjangoNoPermission, DjangoPermissionExtension

from gqlauth.core.utils import UserProto


@strawberry.schema_directive(
    locations=[Location.FIELD_DEFINITION],
    description="Checks whether a user is verified",
)
@final
class IsVerified(DjangoPermissionExtension):
    """Mark a field as only resolvable by authenticated users."""

    message: strawberry.Private[str] = dataclasses.field(default="User is not authenticated.")

    def resolve_for_user(
        self,
        resolver: Callable,
        user: UserProto,
        *,
        info: Info,
        source: Any,
    ):
        if user.is_authenticated and user.status.verified:
            return resolver()
        raise DjangoNoPermission
