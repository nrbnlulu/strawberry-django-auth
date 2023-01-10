import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Optional, cast
from uuid import UUID

import strawberry
import strawberry_django
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from strawberry import auto
from strawberry.types import Info

from gqlauth.core.constants import Messages
from gqlauth.core.exceptions import TokenExpired
from gqlauth.core.interfaces import OutputInterface
from gqlauth.core.scalars import ExpectedErrorType
from gqlauth.core.utils import USER_MODEL, app_settings, inject_fields
from gqlauth.models import RefreshToken
from gqlauth.user.types_ import UserType

if TYPE_CHECKING:
    from gqlauth.core.utils import UserProto


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


@strawberry.input
@inject_fields(app_settings.LOGIN_FIELDS)
class ObtainJSONWebTokenInput:
    password: str
    if app_settings.LOGIN_REQUIRE_CAPTCHA:
        identifier: UUID
        userEntry: str


@strawberry.type(
    description="""
    encapsulates token data, and refresh token data if `JWT_LONG_RUNNING_REFRESH_TOKEN` is on.
    with an output interface.
    """
)
class ObtainJSONWebTokenType(OutputInterface):
    success: bool
    user: Optional[UserType] = None
    token: Optional[TokenType] = None
    if app_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
        refresh_token: Optional[RefreshTokenType] = None
    errors: Optional[ExpectedErrorType] = None

    @classmethod
    def from_user(cls, user: "UserProto") -> "ObtainJSONWebTokenType":
        """creates a new token and possibly a new refresh token based on the
        user.

        *call this method only for trusted users.*
        """
        ret = ObtainJSONWebTokenType(
            success=True, user=cast(UserType, user), token=TokenType.from_user(user)
        )
        if app_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
            ret.refresh_token = cast(RefreshTokenType, RefreshToken.from_user(user))
        return ret

    @classmethod
    def authenticate(cls, info: Info, input_: ObtainJSONWebTokenInput) -> "ObtainJSONWebTokenType":
        """return `ObtainJSONWebTokenType`. authenticates against django
        authentication backends.

        *creates a new token and possibly a refresh token.*
        """
        args = {
            USER_MODEL.USERNAME_FIELD: getattr(input_, USER_MODEL.USERNAME_FIELD),
            "password": input_.password,
        }
        try:
            # authenticate against django authentication backends.
            user: Optional["UserProto"]
            if not (user := authenticate(info.context.request, **args)):  # type: ignore
                return ObtainJSONWebTokenType(success=False, errors=Messages.INVALID_CREDENTIALS)
            from gqlauth.models import UserStatus

            status: UserStatus = getattr(user, "status")  # noqa: B009
            # gqlauth logic
            if status.archived is True:  # un-archive on login
                UserStatus.unarchive(user)
            if status.verified or app_settings.ALLOW_LOGIN_NOT_VERIFIED:
                # successful login.
                return ObtainJSONWebTokenType.from_user(user)
            else:
                return ObtainJSONWebTokenType(success=False, errors=Messages.NOT_VERIFIED)

        except PermissionDenied:
            # one of the authentication backends rejected the user.
            return ObtainJSONWebTokenType(success=False, errors=Messages.UNAUTHENTICATED)

        except TokenExpired:
            return ObtainJSONWebTokenType(success=False, errors=Messages.EXPIRED_TOKEN)


@strawberry.input
class VerifyTokenInput:
    token: str


@strawberry.type
class VerifyTokenType(OutputInterface):
    success: bool
    token: Optional[TokenType] = None
    user: Optional[UserType] = None
    errors: Optional[ExpectedErrorType] = None

    @classmethod
    def from_token(cls, token_input: VerifyTokenInput) -> "VerifyTokenType":
        try:
            token_type = TokenType.from_token(token_input.token)
            user = token_type.get_user_instance()
        except USER_MODEL.DoesNotExist:
            return VerifyTokenType(success=False, errors=Messages.INVALID_CREDENTIALS)
        except TokenExpired:
            return VerifyTokenType(success=False, errors=Messages.EXPIRED_TOKEN)

        else:
            return VerifyTokenType(token=token_type, user=cast(UserType, user), success=True)


@strawberry.type
class RevokeRefreshTokenType:
    success: bool
    refresh_token: Optional[RefreshTokenType] = None
    errors: Optional[ExpectedErrorType] = None
