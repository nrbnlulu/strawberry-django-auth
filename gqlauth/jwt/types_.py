import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Optional, TypeVar, cast

import strawberry
import strawberry_django
from strawberry import auto

from gqlauth.backends.strawberry_django_auth.models import RefreshToken
from gqlauth.core.exceptions import TokenExpired
from gqlauth.core.types_ import (
    ErrorCodes,
    MutationNormalOutput,
)
from gqlauth.core.utils import USER_MODEL, app_settings, inject_fields
from gqlauth.user.types_ import UserType

if TYPE_CHECKING:
    from gqlauth.backends.basebackend import UserProto


@strawberry_django.type(
    model=RefreshToken,
    description="""
Refresh token can be used to obtain a new token instead of log in again
when the token expires.

*This is only used if `JWT_LONG_RUNNING_REFRESH_TOKEN` is set to True.*
""",
)
class RefreshTokenType:
    token: auto = strawberry_django.field(
        description="randomly generated token that is attached to a FK user."
    )
    created: auto
    revoked: auto

    @strawberry_django.field
    def expires_at(self) -> datetime:
        self: RefreshToken  # type: ignore
        return self.expires_at_()  # type: ignore

    @strawberry_django.field
    def is_expired(self) -> bool:
        self: RefreshToken  # type: ignore
        return self.is_expired_()  # type: ignore


@strawberry.type(
    description="""
the data that was used to create the token.
"""
)
@inject_fields(
    {
        app_settings.JWT_PAYLOAD_PK,
    }
)
class TokenPayloadType:
    origIat: datetime = strawberry.field(
        description="when the token was created", default_factory=datetime.utcnow
    )
    exp: datetime = strawberry.field(description="when the token will be expired", default=None)

    def __post_init__(self):
        if not self.exp:
            self.exp = self.origIat + app_settings.JWT_EXPIRATION_DELTA

    def as_dict(self):
        ret = dataclasses.asdict(self)
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if isinstance(value, datetime):
                ret[field.name] = value.strftime(app_settings.JWT_TIME_FORMAT)
        return ret

    @classmethod
    def from_dict(cls, data: dict) -> "TokenPayloadType":
        for field in dataclasses.fields(cls):
            value = data[field.name]
            if isinstance(value, str) and field.type is datetime:
                data[field.name] = datetime.strptime(value, app_settings.JWT_TIME_FORMAT)
        return cls(**data)


@strawberry.type(
    description="""
encapsulates the token with the payload that was used to create the token.
"""
)
class TokenType:
    payload: TokenPayloadType
    token: str = strawberry.field(description="The encoded payload, namely a token.")

    def is_expired(self):
        return self.payload.exp < (datetime.utcnow())

    @classmethod
    def from_user(cls, user: "UserProto") -> "TokenType":
        return app_settings.JWT_PAYLOAD_HANDLER(user)

    @classmethod
    def from_token(cls, token: str) -> "TokenType":
        """Might raise TokenExpired."""
        token_type: TokenType = app_settings.JWT_DECODE_HANDLER(token)
        if token_type.is_expired():
            raise TokenExpired
        return token_type

    def get_user_instance(self) -> "UserProto":
        """might raise not existed exception."""
        pk_name = app_settings.JWT_PAYLOAD_PK.python_name
        query = {pk_name: getattr(self.payload, pk_name)}
        return USER_MODEL.objects.get(**query)  # type: ignore


T = TypeVar("T")


@strawberry.type(
    description="""
    encapsulates token data, and refresh token data if `JWT_LONG_RUNNING_REFRESH_TOKEN` is on.
    with an output interface.
    """
)
class ObtainJSONWebTokenOutput(MutationNormalOutput[T]):
    user: Optional[UserType] = None
    token: Optional[TokenType] = None
    if app_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
        refresh_token: Optional[RefreshTokenType] = None

    @classmethod
    def from_user(cls, user: "UserProto") -> "ObtainJSONWebTokenOutput":
        """creates a new token and possibly a new refresh token based on the
        user.

        *call this method only for trusted users.*
        """
        ret = cls(success=True, user=user, token=TokenType.from_user(user))
        if app_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
            ret.refresh_token = cast(RefreshTokenType, RefreshToken.from_user(user))
        return ret


@strawberry.input
class VerifyTokenInput:
    token: str


@strawberry.type
class VerifyTokenType(MutationNormalOutput[T]):
    token: Optional[TokenType] = None
    user: Optional[UserType] = None

    @classmethod
    def from_token(cls, token_input: VerifyTokenInput) -> "VerifyTokenType":
        try:
            token_type = TokenType.from_token(token_input.token)
            user = token_type.get_user_instance()
        except USER_MODEL.DoesNotExist:
            return VerifyTokenType(success=False, errors=ErrorCodes.INVALID_CREDENTIALS)
        except TokenExpired:
            return VerifyTokenType(success=False, errors=ErrorCodes.TOKEN_EXPIRED)

        else:
            return VerifyTokenType(token=token_type, user=cast(UserType, user), success=True)


@strawberry.type
class RevokeRefreshTokenType(MutationNormalOutput[T]):
    refresh_token: Optional[RefreshTokenType] = None
