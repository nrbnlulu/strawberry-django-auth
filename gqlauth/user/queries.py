from typing import Optional
from django.contrib.auth import get_user_model
# strawberry
import strawberry
from strawberry.django import auth
from gqlauth.utils import g_user
# project
from .types import UserType, UserFilter
from typing import List



@strawberry.type
class UserQueries:
    user: Optional[UserType] = strawberry.django.field()
    users: UserType = strawberry.django.field(filters=UserFilter)
    # me: UserType = strawberry.django.field(resolver=lambda info: g_user(info))
    #
    # @strawberry.field
    # def public_user(self, info) -> Optional[UserType]:
    #     user = g_user(info)
    #     if user.is_authenticated:
    #         return user
    #     return None
