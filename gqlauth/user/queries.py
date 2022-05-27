from typing import Optional
import strawberry
import strawberry_django
from strawberry.django import auth
from gqlauth.utils import g_user
from django.contrib.auth import get_user_model

# project
from .types import UserType, UserFilter


@strawberry.django.type(model=get_user_model(), filters=UserFilter)
class UserQueries:
    user: Optional[UserType] = strawberry.django.field()
    users: list[UserType] = strawberry.django.field(filters=UserFilter)

    @strawberry.django.field
    def public_user(self, info) -> Optional[UserType]:
        user = g_user(info)
        if user.is_authenticated:
            return user

    @strawberry.django.field
    def me(self, info) -> Optional[UserType]:
        user = g_user(info)
        if not user.is_anonymous:
            return user
