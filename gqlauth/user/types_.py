from typing import Dict, List, Optional, Union

from django.contrib.auth import get_user_model
import strawberry
from strawberry import auto
from strawberry.types import Info

from gqlauth import models
from gqlauth.exceptions import WrongUsage
from gqlauth.settings import gqlauth_settings

USER_MODEL = get_user_model()
user_pk_field = USER_MODEL._meta.pk.name

USER_FIELDS = [
    [
        user_pk_field,
    ],
    gqlauth_settings.UPDATE_MUTATION_FIELDS,
    gqlauth_settings.REGISTER_MUTATION_FIELDS,
    gqlauth_settings.REGISTER_MUTATION_FIELDS_OPTIONAL,
]


def inject_fields(fields: Union[Dict[str, type], List[str]]):
    def wrapped(cls):
        if isinstance(fields, dict):
            cls.__annotations__.update(fields)
        elif isinstance(fields, list):
            cls.__annotations__.update({field: auto for field in fields})
        else:
            raise WrongUsage(
                "Can handle only list of strings or dict of name and types."
                f"You provided {type(fields)}"
            )
        return cls

    return wrapped


def inject_many(fields: List[Union[Dict[str, type], List[str]]]):
    def wrapped(cls):
        for node in fields:
            inject_fields(node)(cls)
        return cls

    return wrapped


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

    def make_queryset(self, queryset, info: Info, **kwargs):
        raise Exception("This is not redundant")
        return queryset.select_related("status")
