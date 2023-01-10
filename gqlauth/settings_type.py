import json
from dataclasses import dataclass, field
from datetime import timedelta
from random import SystemRandom
from typing import (
    TYPE_CHECKING,
    Callable,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from django.http.request import HttpRequest
from strawberry.annotation import StrawberryAnnotation
from strawberry.field import StrawberryField

import jwt

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.auth.base_user import AbstractBaseUser

    from gqlauth.core.utils import UserProto
    from gqlauth.jwt.types_ import TokenType


def token_finder(request_or_scope: Union[dict, "HttpRequest"]) -> Optional[str]:
    from gqlauth.core.constants import JWT_PREFIX

    token: Optional[str] = None
    if isinstance(request_or_scope, HttpRequest):  # django
        headers = request_or_scope.headers
        token = headers.get("authorization", None) or headers.get("Authorization", None)
    else:  # channels
        request_or_scope = cast(dict, request_or_scope)
        raw_headers: List[Tuple[bytes, bytes]] = request_or_scope["headers"]
        for k, v in raw_headers:
            if k == b"authorization":
                token = v.decode()
                break
    if token:
        return token.strip(JWT_PREFIX)
    return None


def create_token_type(user: "AbstractBaseUser") -> "TokenType":
    from gqlauth.core.utils import app_settings
    from gqlauth.jwt.types_ import TokenPayloadType, TokenType

    user_pk = app_settings.JWT_PAYLOAD_PK.python_name
    pk_field = {user_pk: getattr(user, user_pk)}
    payload = TokenPayloadType(
        **pk_field,
    )
    serialized = json.dumps(payload.as_dict(), sort_keys=True, indent=1)
    return TokenType(
        token=str(
            jwt.encode(
                payload={"payload": serialized},
                key=cast(str, app_settings.JWT_SECRET_KEY.value),
                algorithm=app_settings.JWT_ALGORITHM,
            )
        ),
        payload=payload,
    )


def decode_jwt(token: str) -> "TokenType":
    from gqlauth.core.utils import app_settings
    from gqlauth.jwt.types_ import TokenPayloadType, TokenType

    decoded = json.loads(
        jwt.decode(
            token,
            key=cast(str, app_settings.JWT_SECRET_KEY.value),
            algorithms=[
                app_settings.JWT_ALGORITHM,
            ],
        )["payload"]
    )
    return TokenType(token=token, payload=TokenPayloadType.from_dict(decoded))


def default_text_factory():
    return "".join(
        [
            str(node)
            for node in [
                SystemRandom().randint(0, 10) for _ in range(5, SystemRandom().randint(10, 20))
            ]
        ]
    )


T = TypeVar("T")


class DjangoSetting(Generic[T]):
    __slots__ = ("setting", "cached")

    def __init__(self, setting: str, value: Optional[T] = None):
        self.setting = setting
        self.cached: Optional[T] = value

    @property
    def value(self) -> T:
        if self.cached:  # slotted classes can't use cached property (without __dict__)
            return self.cached
        from django.conf import settings

        final = settings
        for attr in self.setting.split("."):
            final = getattr(final, attr)

        return final  # type: ignore

    @classmethod
    def override(cls, value: T) -> "DjangoSetting":
        return DjangoSetting(setting="", value=value)


username_field = StrawberryField(
    python_name="username", default=None, type_annotation=StrawberryAnnotation(str)
)
password_field = StrawberryField(
    python_name="password", default=None, type_annotation=StrawberryAnnotation(str)
)
first_name_field = StrawberryField(
    python_name="first_name",
    default=None,
    type_annotation=StrawberryAnnotation(Optional[str]),
)
last_name_field = StrawberryField(
    python_name="last_name",
    default=None,
    type_annotation=StrawberryAnnotation(Optional[str]),
)
email_field = StrawberryField(
    python_name="email", default=None, type_annotation=StrawberryAnnotation(str)
)


def default_captcha_text_validator(original: str, received: str) -> bool:
    return original == received


@dataclass
class GqlAuthSettings:
    ALLOW_LOGIN_NOT_VERIFIED: bool = False
    """"""
    LOGIN_FIELDS: Set[StrawberryField] = field(
        default_factory=lambda: {
            username_field,
        }
    )
    """These fields would be used to authenticate with SD-jwt `authenticate`
    function. This function will call each of our `AUTHENTICATION_BACKENDS`,
    And will return the user from one of them unless `PermissionDenied` was
    raised. You can pass any fields that would be accepted by your backends.

    **Note that `password field` is mandatory and cannot be removed.**
    """
    LOGIN_REQUIRE_CAPTCHA: bool = True
    """whether login will require captcha verification."""
    REGISTER_MUTATION_FIELDS: Set[StrawberryField] = field(
        default_factory=lambda: {email_field, username_field}
    )
    """Fields on register, plus password1 and password2, can be a dict like
    UPDATE_MUTATION_fieldS setting."""
    REGISTER_REQUIRE_CAPTCHA: bool = True
    """whether register will require captcha verification."""
    # captcha stuff
    #: captcha expiration delta.
    CAPTCHA_EXPIRATION_DELTA: timedelta = timedelta(seconds=120)
    #: max number of attempts for one captcha.
    CAPTCHA_MAX_RETRIES: int = 5
    CAPTCHA_TEXT_FACTORY: Callable = default_text_factory
    """A callable with no arguments that returns a string.

    This will be used to generate the captcha image.
    """
    CAPTCHA_TEXT_VALIDATOR: Callable[[str, str], bool] = default_captcha_text_validator
    """A callable that will receive the original string vs user input and
    returns a boolean."""
    FORCE_SHOW_CAPTCHA: bool = False
    """Whether to show the captcha image after it has been created for
    debugging purposes."""
    CAPTCHA_SAVE_IMAGE: bool = False
    """If True, an png representation of the captcha will be saved under
    MEDIA_ROOT/captcha/<datetime>/<uuid>.png."""
    # optional fields on update account, can be list of fields
    UPDATE_MUTATION_FIELDS: Set[StrawberryField] = field(
        default_factory=lambda: {first_name_field, last_name_field}
    )
    """fields on update account mutation."""

    # email tokens
    EXPIRATION_ACTIVATION_TOKEN: timedelta = timedelta(days=7)
    EXPIRATION_PASSWORD_RESET_TOKEN: timedelta = timedelta(hours=1)
    EXPIRATION_PASSWORD_SET_TOKEN: timedelta = timedelta(hours=1)
    # email stuff

    EMAIL_FROM: DjangoSetting[str] = DjangoSetting("DEFAULT_FROM_EMAIL")
    SEND_ACTIVATION_EMAIL: bool = True
    ACTIVATION_PATH_ON_EMAIL: str = "activate"
    PASSWORD_SET_PATH_ON_EMAIL: str = "password-set"
    PASSWORD_RESET_PATH_ON_EMAIL: str = "password-reset"
    # email subjects templates
    EMAIL_SUBJECT_ACTIVATION: str = "email/activation_subject.txt"
    EMAIL_SUBJECT_ACTIVATION_RESEND: str = "email/activation_subject.txt"
    EMAIL_SUBJECT_PASSWORD_SET: str = "email/password_set_subject.txt"
    EMAIL_SUBJECT_PASSWORD_RESET: str = "email/password_reset_subject.txt"
    # email templates
    EMAIL_TEMPLATE_ACTIVATION: str = "email/activation_email.html"
    EMAIL_TEMPLATE_ACTIVATION_RESEND: str = "email/activation_email.html"
    EMAIL_TEMPLATE_PASSWORD_SET: str = "email/password_set_email.html"
    EMAIL_TEMPLATE_PASSWORD_RESET: str = "email/password_reset_email.html"
    EMAIL_TEMPLATE_VARIABLES: dict = field(default_factory=lambda: {})
    # others
    ALLOW_DELETE_ACCOUNT: bool = False
    """If True, DeleteAcount mutation will permanently delete the user."""
    ALLOW_PASSWORDLESS_REGISTRATION: bool = False
    """Whether to allow registration with no password."""
    SEND_PASSWORD_SET_EMAIL: bool = False
    # JWT stuff
    JWT_SECRET_KEY: DjangoSetting[str] = DjangoSetting("SECRET_KEY")
    """key used to sign the JWT token."""

    JWT_ALGORITHM: str = "HS256"
    """Algorithm used for signing the token."""
    JWT_TIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%f"
    """A valid 'strftime' string that will be used to encode the token
    payload."""
    JWT_PAYLOAD_HANDLER: Callable[["UserProto"], "TokenType"] = create_token_type
    """A custom function to generate the token datatype, its up to you to
    encode the token."""
    JWT_PAYLOAD_PK: StrawberryField = field(default_factory=lambda: username_field)
    """field that will be used to generate the token from a user instance and
    retrieve user based on the decoded token.

    *This filed must be unique in the database*
    """
    JWT_DECODE_HANDLER: Callable[[str], "TokenType"] = decode_jwt

    JWT_TOKEN_FINDER: Callable[[Union["HttpRequest", dict]], Optional[str]] = token_finder
    """A hook called by `GqlAuthRootField` to find the token. Accepts the
    request object (might be channels scope dict or django request object)

     **remember to strip the "JWT " prefix
    if you override this.**
    """
    JWT_EXPIRATION_DELTA: timedelta = timedelta(minutes=5)
    """Timedelta added to `utcnow()` to set the expiration time.

    When this ends you will have to create a new token by logging in or
    using the refresh token.
    """
    # refresh token stuff
    JWT_LONG_RUNNING_REFRESH_TOKEN: bool = True
    """Whether to enable refresh tokens to be used as an alternative to login
    every time the token is expired."""
    JWT_REFRESH_TOKEN_N_BYTES: int = 20
    """Number of bytes for long running refresh token."""
    JWT_REFRESH_EXPIRATION_DELTA: timedelta = timedelta(days=7)
    """Refresh token expiration time delta."""

    def __post_init__(self):
        # if there override the defaults
        if "email" not in {field_.name for field_ in self.REGISTER_MUTATION_FIELDS}:
            self.SEND_ACTIVATION_EMAIL = False
