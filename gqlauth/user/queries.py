from typing import List, Optional

from django.contrib.auth import get_user_model
import strawberry
from strawberry.types import Info

from gqlauth.utils import g_user

# project
from .types_ import UserFilter, UserType


@strawberry.django.type(model=get_user_model(), filters=UserFilter)
class UserQueries:
    user: Optional[UserType] = strawberry.django.field()
    users: List[UserType] = strawberry.django.field(filters=UserFilter)

    @strawberry.django.field
    def public_user(self, info: Info) -> Optional[UserType]:
        user = g_user(info)
        if user.is_authenticated:
            return user
        return None

    @strawberry.django.field
    def me(self, info: Info) -> Optional[UserType]:
        user = g_user(info)
        if not user.is_anonymous:
            return user
        return None
