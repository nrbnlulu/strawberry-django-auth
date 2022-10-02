from abc import ABC, abstractmethod
from typing import Any, List, Optional

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from jwt import PyJWTError
import strawberry
from strawberry.schema_directive import Location
from strawberry.types import Info

from gqlauth.core.exceptions import TokenExpired
from gqlauth.core.types_ import GQLAuthError, GQLAuthErrors
from gqlauth.core.utils import get_user, get_user_with_status
from gqlauth.jwt.types_ import TokenType
from gqlauth.settings import gqlauth_settings as app_settings

USER_MODEL = get_user_model()

__all__ = ["BaseAuthDirective", "IsAuthenticated", "HasPermission", "IsVerified", "TokenRequired"]


class BaseAuthDirective(ABC):
    @abstractmethod
    def resolve_permission(
        self,
        source: Any,
        info: Info,
        args: list,
        kwargs: dict,
    ) -> Optional[GQLAuthError]:
        ...


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires a JWT token, this token will be used to find the user object.",
)
class TokenRequired(BaseAuthDirective):
    def resolve_permission(
        self, source: Any, info: Info, args: list, kwargs: dict
    ) -> Optional[GQLAuthError]:
        token = app_settings.JWT_TOKEN_FINDER(info)
        try:
            token_type = TokenType.from_token(token)
        except PyJWTError:  # raised by python-jwt
            return GQLAuthError(code=GQLAuthErrors.INVALID_TOKEN)

        except TokenExpired:
            return GQLAuthError(code=GQLAuthErrors.EXPIRED_TOKEN)
        user = token_type.get_user_instance()
        info.context.user = user
        return None


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires authentication",
)
class IsAuthenticated(BaseAuthDirective):
    def resolve_permission(self, source: Any, info: Info, args, kwargs):
        user = get_user(info)
        if not user.is_authenticated:
            return GQLAuthError(code=GQLAuthErrors.UNAUTHENTICATED)
        return None


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires the user to be verified",
)
class IsVerified(BaseAuthDirective):
    def resolve_permission(self, source: Any, info: Info, args, kwargs):
        if (user := get_user_with_status(info)) and user.status.verified:
            return None
        return GQLAuthError(code=GQLAuthErrors.NOT_VERIFIED)


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires a certain permissions to be resolved.",
)
class HasPermission(BaseAuthDirective):
    permissions: strawberry.Private[List[str]]

    def resolve_permission(self, source: Any, info: Info, args, kwargs):
        user = get_user(info)
        for permission in self.permissions:
            if not user.has_perm(permission):  # type: ignore
                return GQLAuthError(
                    code=GQLAuthErrors.NO_SUFFICIENT_PERMISSIONS,
                    message=_(
                        f"User {getattr(user, user.USERNAME_FIELD, user.first_name)}, has not sufficient permissions for {info.path.key}"  # type: ignore
                    ),
                )
        return None
