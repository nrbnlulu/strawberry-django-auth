from __future__ import annotations

import dataclasses
from typing import Any, Callable, cast, final

import strawberry
from graphql.pyutils import AwaitableOrValue
from strawberry.schema_directive import Location
from strawberry.types import Info
from strawberry_django.permissions import DjangoNoPermission, DjangoPermissionExtension
from strawberry_django.utils.typing import UserType
from typing_extensions import override

from gqlauth.core.utils import UserProto


@strawberry.schema_directive(
    locations=[Location.FIELD_DEFINITION],
    description="Checks whether a user is verified",
)
@final
class IsVerified(DjangoPermissionExtension):
    """Mark a field as only resolvable by authenticated users."""

    message: strawberry.Private[str] = dataclasses.field(
        default="User is not authenticated."
    )

    @override
    def resolve_for_user(
        self,
        resolver: Callable[..., Any],
        user: UserType | None,
        *,
        info: Info,
        source: Any,
    ) -> AwaitableOrValue:
        user = cast(UserProto, user)
        if user.is_authenticated and user.status.verified:
            return resolver()
        raise DjangoNoPermission
