from typing import Any, Awaitable, Callable, Dict, List, Union

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from jwt import PyJWTError
from strawberry import UNSET
from strawberry.field import StrawberryField
from strawberry.types import Info
from strawberry_django import django_resolver
from strawberry_django.fields.field import StrawberryDjangoField
from strawberry_django.utils import is_async

from gqlauth.core.directives import BaseAuthDirective
from gqlauth.core.exceptions import TokenExpired
from gqlauth.core.types_ import AuthOutput, ErrorMessage, GqlAuthError
from gqlauth.core.utils import get_token_from_headers, get_user
from gqlauth.jwt.types_ import TokenType

__all__ = ["GqlAuthRootField", "field"]

USER_MODEL = get_user_model()


class GqlAuthRootField(StrawberryDjangoField):
    def _resolve(
        self, token: TokenType, source: Any, info: Info, args: List[Any], kwargs: Dict[str, Any]
    ):
        user = token.get_user_instance()
        info.context.user = user
        return super().get_result(source, info, args, kwargs)

    def get_result(
        self, source: Any, info: Info, args: List[Any], kwargs: Dict[str, Any]
    ) -> Union[Awaitable[Any], Any]:
        token = get_token_from_headers(info.context.request.headers)
        try:
            token_type = TokenType.from_token(token)
        except PyJWTError:  # raised by python-jwt
            return AuthOutput(error=ErrorMessage(code=GqlAuthError.INVALID_TOKEN))

        except TokenExpired:
            return AuthOutput(error=ErrorMessage(code=GqlAuthError.EXPIRED_TOKEN))

        if is_async():
            return sync_to_async(self._resolve)(token_type, source, info, args, kwargs)
        else:
            return self._resolve(token_type, source, info, args, kwargs)


class GqlAuthField(StrawberryDjangoField):
    def _resolve(self, source, info, args, kwargs):
        user = get_user(info)
        for directive in self.directives:

            if isinstance(directive, BaseAuthDirective) and (
                error := directive.resolve_permission(user, source, info, args, kwargs)
            ):
                return AuthOutput(error=error)
        return super().get_result(source, info, args, kwargs)

    def get_result(self, source, info, args, kwargs):
        if is_async():
            return sync_to_async(self._resolve)(source, info, args, kwargs)
        return self._resolve(source, info, args, kwargs)


def field(
    resolver=None,
    *,
    name=None,
    field_name=None,
    filters=UNSET,
    default=UNSET,
    directives: List[BaseAuthDirective] = None,
    **kwargs,
) -> Union[StrawberryField, Callable[..., StrawberryField]]:
    field_ = GqlAuthField(
        python_name=None,
        graphql_name=name,
        filters=filters,
        django_name=field_name,
        default=default,
        directives=directives,
        **kwargs,
    )
    if resolver:
        resolver = django_resolver(resolver)
        field_ = field_(resolver)
    return field_
