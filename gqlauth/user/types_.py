from typing import Optional

from django.contrib.auth import get_user_model
import strawberry
from strawberry import auto
from strawberry.types import Info

from gqlauth import models
from gqlauth.settings import gqlauth_settings
from gqlauth.utils import inject_many

USER_MODEL = get_user_model()
user_pk_field = USER_MODEL._meta.pk.name

USER_FIELDS = [
    [
        user_pk_field,
        USER_MODEL.USERNAME_FIELD,
        USER_MODEL.EMAIL_FIELD,
    ],
    gqlauth_settings.UPDATE_MUTATION_FIELDS,
]


@strawberry.django.filters.filter(models.UserStatus)
class UserStatusFilter:
    verified: auto
    archived: auto
    secondary_email: auto


@strawberry.django.type(model=models.UserStatus, filters=UserStatusFilter)
class UserStatusType:
    verified: auto
    archived: auto
    secondary_email: auto


@strawberry.django.filters.filter(USER_MODEL)
@inject_many(USER_FIELDS)
class UserFilter:
    logentry_set: auto
    is_superuser: auto
    last_login: auto
    is_staff: auto
    is_active: auto
    date_joined: auto
    status: UserStatusFilter


@strawberry.django.type(model=USER_MODEL, filters=UserFilter)
@inject_many(USER_FIELDS)
class UserType:
    logentry_set: auto
    is_superuser: auto
    last_login: auto
    is_staff: auto
    is_active: auto
    date_joined: auto
    status: UserStatusType

    @strawberry.django.field
    def archived(self, info: Info) -> bool:
        return self.status.archived

    @strawberry.django.field
    def verified(self, info: Info) -> bool:
        return self.status.verified

    @strawberry.django.field
    def secondary_email(self, info: Info) -> Optional[str]:
        return self.status.secondary_email
