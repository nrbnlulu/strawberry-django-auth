from django.contrib.auth import get_user_model
import strawberry
from strawberry.django import auto

from gqlauth import models


@strawberry.django.type(model=models.UserStatus)
class UserStatusType:
    verified: auto
    archived: auto
    secondary_email: auto


@strawberry.django.filters.filter(get_user_model(), lookups=True)
class UserFilter:
    id: auto  # noqa: A003
    username: auto
    email: auto
    name: auto
    last_name: auto
    status: UserStatusType


@strawberry.django.type(model=get_user_model(), filters=UserFilter)
class UserType:
    ...
