import dataclasses
from typing import Any, final

import strawberry
from strawberry.schema_directive import Location
from strawberry_django_plus.permissions import ConditionDirective

from gqlauth.core.utils import UserProto


@strawberry.schema_directive(
    locations=[Location.FIELD_DEFINITION],
    description="Checks whether a user is verified",
)
@final
class IsVerified(ConditionDirective):
    """Mark a field as only resolvable by authenticated users."""

    message: strawberry.Private[str] = dataclasses.field(default="User is not authenticated.")

    def check_condition(self, root: Any, info, user: UserProto, **kwargs) -> bool:  # type: ignore
        return user.is_authenticated and user.status.verified
