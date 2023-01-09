from typing import Optional

from django.contrib.auth import get_user_model
import strawberry
from strawberry.schema_directive import Location
from strawberry.types import Info
from strawberry_django_plus import gql
from strawberry_django_plus.permissions import IsAuthenticated

from gqlauth.core.utils import get_user

# project
from .types_ import UserFilter, UserType

USER_MODEL = get_user_model()


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Sample:
    message: str = "fdsafdsafdsfa"


@gql.django.type(model=USER_MODEL, filters=UserFilter)
class UserQueries:
    @gql.django.field(description="Returns the current user if he is not anonymous.")
    def public_user(self, info: Info) -> Optional[UserType]:
        user = get_user(info)
        if not user.is_anonymous:
            return user  # type: ignore
        return None

    @gql.django.field(directives=[IsAuthenticated()])
    def me(self, info: Info) -> UserType:
        return get_user(info)
