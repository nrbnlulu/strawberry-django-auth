from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
import strawberry
from strawberry import auto
from strawberry.types import Info

import gqlauth.jwt.models

app_settings = settings.GQL_AUTH

USER_MODEL = get_user_model()


@strawberry.django.type(model=gqlauth.jwt.models.RefreshToken)
class RefreshTokenType:
    user: auto
    token: auto
    created: auto
    revoked: auto

    @strawberry.django.field
    def expires_at(self: gqlauth.jwt.models.RefreshToken) -> datetime:
        return self._expires_at()

    @strawberry.django.field
    def is_expired(self: gqlauth.jwt.models.RefreshToken) -> bool:
        return self._is_expired()


@strawberry.type
class TokenType:
    exp: datetime
    origIat: datetime
    # token will be created later.
    token: str = None

    @classmethod
    def from_user(cls, info: Info, user: USER_MODEL) -> "TokenType":
        return app_settings.JWT_PAYLOAD_HANDLER(info, user)

    @classmethod
    def from_token(cls, token: str) -> "TokenType":
        return app_settings.JWT_


@strawberry.type
class JWTType:
    token: TokenType
    if app_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
        refresh_token: RefreshTokenType
