from typing import List, Optional

from django.contrib.auth import get_user_model
import strawberry
from strawberry.schema_directive import Location
from strawberry.types import Info

from gqlauth.core.utils import get_user

from ..core.directives import IsAuthenticated
from ..core.field import GqlAuthField

# project
from .types_ import UserFilter, UserType

USER_MODEL = get_user_model()


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Sample:
    message: str = "fdsafdsafdsfa"


@strawberry.django.type(model=USER_MODEL, filters=UserFilter)
class UserQueries:
    users: Optional[List[UserType]] = GqlAuthField(
        filters=UserFilter,
        default_factory=lambda: USER_MODEL.objects.all(),
        directives=[
            IsAuthenticated(),
        ],
    )

    @strawberry.django.field
    def public_user(self, info: Info) -> Optional[UserType]:
        user = get_user(info)
        if user.is_authenticated:
            return user
        return None

    @strawberry.django.field
    def me(self, info: Info) -> Optional[UserType]:
        user = get_user(info)
        if not user.is_anonymous:
            return user
        return None
