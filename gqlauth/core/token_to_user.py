from typing import Any, Union

from django.contrib.auth.models import AnonymousUser
from jwt import PyJWTError

from gqlauth.core.exceptions import TokenExpired
from gqlauth.core.types_ import GQLAuthError, GQLAuthErrors
from gqlauth.core.utils import USER_UNION, app_settings
from gqlauth.jwt.types_ import TokenType

anon_user = AnonymousUser()


class UserOrError:
    __slots__ = ("user", "error")

    def __init__(self, user: USER_UNION = anon_user, error: Exception = None):
        self.user = user
        self.error = error


USER_OR_ERROR_KEY = UserOrError.__name__


def get_user_or_error(scope_or_request: Union[dict, Any]) -> UserOrError:
    user_or_error = UserOrError()
    if token := app_settings.JWT_TOKEN_FINDER(scope_or_request):
        try:
            token = TokenType.from_token(token)
            user = token.get_user_instance()
            user_or_error.user = user
        except PyJWTError:  # raised by python-jwt
            user_or_error.error = GQLAuthError(code=GQLAuthErrors.INVALID_TOKEN)

        except TokenExpired:
            user_or_error.error = GQLAuthError(code=GQLAuthErrors.EXPIRED_TOKEN)
        except Exception as exc:  # pragma: no cover
            import traceback

            traceback.print_tb(exc.__traceback__)
            print(exc)
            raise exc
    else:
        user_or_error.error = GQLAuthError(code=GQLAuthErrors.MISSING_TOKEN)

    return user_or_error


from channels.db import database_sync_to_async


class GqlAuthMiddleWare:
    def __init__(self, inner: type):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if not scope.get(USER_OR_ERROR_KEY, None):
            scope[USER_OR_ERROR_KEY] = await self._get_user_or_error(scope)
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def _get_user_or_error(self, scope) -> UserOrError:
        return get_user_or_error(scope)


from graphql import GraphQLError
from strawberry import Schema


class TokenSchema(Schema):
    """
    injects token to context.
    """

    def execute_sync(self, *args, **kwargs):
        self._inject_user_and_errors(kwargs)
        return super().execute_sync(*args, **kwargs)

    async def execute(self, *args, **kwargs):
        self._inject_user_and_errors(kwargs)
        return await super().execute(*args, **kwargs)

    def subscribe(self, *args, **kwargs):
        user_or_error = self._inject_user_and_errors(kwargs)
        if not user_or_error.user.is_authenticated:
            raise GraphQLError(message=GQLAuthErrors.UNAUTHENTICATED.value)
        res = super().subscribe(*args, **kwargs)
        return res

    @staticmethod
    def _inject_user_and_errors(kwargs: dict) -> UserOrError:
        context = kwargs["context_value"]
        # channels compat
        if ws := getattr(context, "ws", None):
            user_or_error: UserOrError = ws.scope[USER_OR_ERROR_KEY]
        else:
            user_or_error = getattr(context.request, USER_OR_ERROR_KEY)
        context.request.user = user_or_error.user
        return user_or_error


class GqlAuthJwtMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, USER_OR_ERROR_KEY):
            setattr(request, USER_OR_ERROR_KEY, get_user_or_error(request))

        return self.get_response(request)
