import strawberry_django
from django.contrib.auth import get_user_model
from strawberry import auto
from strawberry.annotation import StrawberryAnnotation
from strawberry.field import StrawberryField

from gqlauth.core.utils import inject_fields
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
}.union(gqlauth_settings.UPDATE_MUTATION_FIELDS)

ef_name = getattr(USER_MODEL, "EMAIL_FIELD", None)
if ef_name:
    USER_FIELDS.add(
        StrawberryField(
            python_name=ef_name, default=None, type_annotation=StrawberryAnnotation(auto)
        )
    )


@strawberry_django.filters.filter(USER_MODEL)
@inject_fields(USER_FIELDS, annotations_only=True)
class UserFilter:
    last_login: auto
    date_joined: auto
    is_verified: auto
    is_archived: auto


@strawberry_django.type(model=USER_MODEL, filters=UserFilter)
@inject_fields(USER_FIELDS, annotations_only=True)
class UserType:
    last_login: auto
    date_joined: auto
    is_verified: auto
    is_archived: auto
