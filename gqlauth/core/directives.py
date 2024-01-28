from typing import Any, Callable

from strawberry.types import Info
from strawberry_django.permissions import DjangoNoPermission, DjangoPermissionExtension

from gqlauth.core.utils import UserProto


class IsVerified(DjangoPermissionExtension):
    """Mark a field as only resolvable by authenticated users."""

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
        raise DjangoNoPermission("User is not verified.")
