import strawberry_django
from django.contrib.auth import get_user_model
from strawberry import auto
from strawberry.annotation import StrawberryAnnotation
from strawberry.field import StrawberryField
from strawberry.types import Info

from gqlauth.core.utils import inject_fields
from gqlauth.models import UserStatus
from gqlauth.settings import gqlauth_settings

USER_MODEL = get_user_model()
# UPDATE_MUTATION_FIELDS are here because they are most likely to be in the model.
USER_FIELDS = {
    StrawberryField(
        python_name=USER_MODEL._meta.pk.name,  # type: ignore
        default=None,
        type_annotation=StrawberryAnnotation(auto),
    ),
    StrawberryField(
        python_name=USER_MODEL.USERNAME_FIELD,
        default=None,
        type_annotation=StrawberryAnnotation(auto),
    ),
    StrawberryField(
        python_name=USER_MODEL.EMAIL_FIELD, default=None, type_annotation=StrawberryAnnotation(auto)
    ),
}.union(gqlauth_settings.UPDATE_MUTATION_FIELDS)


@strawberry_django.filters.filter(UserStatus)
class UserStatusFilter:
    verified: auto
    archived: auto


@strawberry_django.type(model=UserStatus, filters=UserStatusFilter)
class UserStatusType:
    verified: auto
    archived: auto


@strawberry_django.filters.filter(USER_MODEL)
@inject_fields(USER_FIELDS, annotations_only=True)
class UserFilter:
    logentry_set: auto
    is_superuser: auto
    last_login: auto
    is_staff: auto
    is_active: auto
    date_joined: auto
    status: UserStatusFilter


@strawberry_django.type(model=USER_MODEL, filters=UserFilter)
@inject_fields(USER_FIELDS, annotations_only=True)
class UserType:
    logentry_set: auto
    is_superuser: auto
    last_login: auto
    is_staff: auto
    is_active: auto
    date_joined: auto
    status: UserStatusType

    @strawberry_django.field
    def archived(self, info: Info) -> bool:
        return self.status.archived

    @strawberry_django.field
    def verified(self, info: Info) -> bool:
        return self.status.verified
