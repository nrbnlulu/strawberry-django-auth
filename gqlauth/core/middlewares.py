from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils.decorators import sync_and_async_middleware
from jwt import PyJWTError
from strawberry import Schema

from gqlauth.core.exceptions import TokenExpired
from gqlauth.core.types_ import GQLAuthError, GQLAuthErrors
from gqlauth.core.utils import USER_UNION, app_settings
from gqlauth.jwt.types_ import TokenType

anon_user = AnonymousUser()
if TYPE_CHECKING:
    pass


class UserOrError:
    __slots__ = ("user", "error")

    def __init__(self, user: USER_UNION = anon_user, error: Exception | None = None):
        self.user = user
        self.error = error


USER_OR_ERROR_KEY = UserOrError.__name__


def get_user_or_error(scope_or_request: dict | HttpRequest) -> UserOrError:
    user_or_error = UserOrError()
    if token_str := app_settings.JWT_TOKEN_FINDER(scope_or_request):
        try:
            token = TokenType.from_token(token=token_str)
            user = token.get_user_instance()
            user_or_error.user = user

        except PyJWTError:  # raised by python-jwt
            user_or_error.error = GQLAuthError(code=GQLAuthErrors.INVALID_TOKEN)

        except TokenExpired:
            user_or_error.error = GQLAuthError(code=GQLAuthErrors.EXPIRED_TOKEN)

    else:
        user_or_error.error = GQLAuthError(code=GQLAuthErrors.MISSING_TOKEN)

    return user_or_error


def channels_jwt_middleware(inner: Callable):
    from channels.db import database_sync_to_async

    if asyncio.iscoroutinefunction(inner):
        get_user_or_error_async = database_sync_to_async(get_user_or_error)

        async def middleware(scope, receive, send):
            if not scope.get(USER_OR_ERROR_KEY, None):
                user_or_error: UserOrError = await get_user_or_error_async(scope)
                scope[USER_OR_ERROR_KEY] = user_or_error
            return await inner(scope, receive, send)

    else:  # pragma: no cover
        raise NotImplementedError("sync channels middleware is not supported yet.")
    return middleware


@sync_and_async_middleware
def django_jwt_middleware(get_response):
    def logic(request: HttpRequest) -> None:
        if not hasattr(request, USER_OR_ERROR_KEY):
            user_or_error: UserOrError = get_user_or_error(request)
            setattr(request, USER_OR_ERROR_KEY, user_or_error)

    if asyncio.iscoroutinefunction(get_response):
        async_logic = sync_to_async(logic)

        async def middleware(request: HttpRequest):
            await async_logic(request)
            return await get_response(request)

    else:

        def middleware(request: HttpRequest):  # type: ignore
            logic(request)
            return get_response(request)

    return middleware


class JwtSchema(Schema):
    """Injects token to context."""

    def execute_sync(self, *args, **kwargs):
        self._inject_user_and_errors(kwargs)
        return super().execute_sync(*args, **kwargs)

    async def execute(self, *args, **kwargs):
        self._inject_user_and_errors(kwargs)
        return await super().execute(*args, **kwargs)

    async def subscribe(self, *args, **kwargs):
        self._inject_user_and_errors(kwargs)
        return await super().subscribe(*args, **kwargs)

    @staticmethod
    def _inject_user_and_errors(kwargs: dict) -> UserOrError:
        context = kwargs.get("context_value")
        # channels compat
        if isinstance(context, dict):
            request = context["request"]
            try:
                user_or_error: UserOrError = request.consumer.scope[USER_OR_ERROR_KEY]
            except AttributeError:
                # FIXME: This is here because the test consumer is not 1:1 as a real client ATM
                user_or_error = request.scope[USER_OR_ERROR_KEY]
            request.user = user_or_error.user  # type: ignore
        else:
            user_or_error: UserOrError = getattr(context.request, USER_OR_ERROR_KEY)  # type: ignore
            context.request.user = user_or_error.user  # type: ignore
        return user_or_error
