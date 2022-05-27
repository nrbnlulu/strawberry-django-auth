from django.contrib.auth import get_user_model
from typing import Optional

# strawberry
import strawberry
from strawberry import auto

# project
from gqlauth import models

USER_MODEL = get_user_model()
user_pk_field = USER_MODEL._meta.pk.name


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


def inject_field(field: dict[str, type]):
    def wrapped(cls):
        cls.__annotations__.update(field)
        return cls

    return wrapped


@strawberry.django.filters.filter(USER_MODEL)
@inject_field({user_pk_field: auto})
class UserFilter:
    username: auto
    email: auto
    first_name: auto
    last_name: auto
    logentry_set: auto
    is_superuser: auto
    last_login: auto
    is_staff: auto
    is_active: auto
    date_joined: auto
    # connablealert_set: auto
    # groups: auto
    # user_permissions: auto
    status: UserStatusFilter


@strawberry.django.type(model=USER_MODEL, filters=UserFilter)
@inject_field({user_pk_field: auto})
class UserType:
    username: auto
    email: auto
    first_name: auto
    last_name: auto
    logentry_set: auto
    is_superuser: auto
    last_login: auto
    is_staff: auto
    is_active: auto
    date_joined: auto

    # status: UserStatusType

    @strawberry.django.field
    def pk(self, info) -> int:
        return self.pk

    @strawberry.django.field
    def archived(self, info) -> bool:
        return self.status.archived

    @strawberry.django.field
    def verified(self, info) -> bool:
        return self.status.verified

    @strawberry.django.field
    def secondary_email(self, info) -> Optional[str]:
        return self.status.secondary_email

    def get_queryset(self, queryset, info, **kwargs):
        return queryset.select_related("status")
