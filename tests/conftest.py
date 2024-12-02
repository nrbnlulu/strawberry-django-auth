import dataclasses
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Iterable, NamedTuple, Union

import faker
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from faker.providers import BaseProvider
from strawberry import Schema
from strawberry.channels.testing import GraphQLWebsocketCommunicator
from strawberry.types import ExecutionResult
from strawberry.utils.str_converters import to_camel_case

from gqlauth.captcha.models import Captcha
from gqlauth.core.constants import JWT_PREFIX
from gqlauth.core.middlewares import USER_OR_ERROR_KEY, UserOrError, get_user_or_error
from gqlauth.jwt.types_ import TokenType
from gqlauth.models import RefreshToken
from gqlauth.settings_type import GqlAuthSettings
from tests.testproject.asgi import application
from tests.testproject.relay_schema import relay_schema
from tests.testproject.sample.models import Apple
from tests.testproject.schema import arg_schema

if TYPE_CHECKING:  # pragma: no cover
    from gqlauth.core.utils import UserProto

UserModel = get_user_model()
WRONG_PASSWORD = "wrong password"
CC_USERNAME_FIELD = to_camel_case(UserModel.USERNAME_FIELD)
USERNAME_FIELD = UserModel.USERNAME_FIELD
EMAIL_FIELD = UserModel.EMAIL_FIELD
additional_fields = USERNAME_FIELD, EMAIL_FIELD

fake = faker.Faker()


class MARKERS:
    settings_b = "settings_b"


@pytest.fixture
def current_markers(request, pytestconfig):
    return pytestconfig.getoption("-m")


@pytest.fixture
def username_field() -> str:
    return UserModel.USERNAME_FIELD


def inject_fields(fields: Iterable[str]):
    def wrapped(cls):
        annotations = list(cls.__annotations__.items())
        res = {field: str for field in fields if field}
        # this solves non default fields after default fields
        annotations.extend(list(res.items()))
        annotations.reverse()
        annotations = {name: annotation for name, annotation in annotations}
        cls.__annotations__ = annotations
        return cls

    return wrapped


class UserFieldFakeProvider(BaseProvider):
    def username(self) -> str:
        return fake.user_name()


fake.add_provider(UserFieldFakeProvider)


@dataclass
@inject_fields(additional_fields)
class UserType:
    password: str = fake.password()
    obj: Union["UserProto", AbstractBaseUser] = None
    username_field: str = None

    @classmethod
    def generate(cls):
        p = fake.password()
        u = getattr(fake, USERNAME_FIELD)()
        kwargs = {USERNAME_FIELD: u}
        if EMAIL_FIELD:
            kwargs[EMAIL_FIELD] = getattr(fake, EMAIL_FIELD)()

        return cls(password=p, **kwargs)

    def __post_init__(self):
        us_field = getattr(self, USERNAME_FIELD)
        self.username_field = us_field


@dataclass
class UserStatusType:
    verified: bool
    archived: bool = False
    user: Union[UserModel, UserType] = None

    def create(self):
        """This will create a new user with user status from the
        user_status_type class and will return the same object with the django
        user inside it."""
        user = self.user  # caching the user type object
        kwargs = asdict(user)
        kwargs.pop("username_field")
        kwargs.pop("obj")
        self.user = UserModel(**kwargs)
        # password must be set via this method.
        self.user.set_password(user.password)
        # must save for status to be created
        self.user.save()
        for field, value in asdict(self).items():
            setattr(self.user.status, field, value)
        self.user.status.save()
        self.user.refresh_from_db()
        user.obj = self.user
        self.user = user
        db_status = self.user.obj.status
        if self.verified:
            assert db_status.verified
        else:
            assert not db_status.verified

    def generate_refresh_token(self) -> RefreshToken:
        user = self.user.obj
        assert user, "must have a created user instance"
        return RefreshToken.from_user(user)

    def generate_fresh_token(self) -> str:
        return JWT_PREFIX + " " + TokenType.from_user(self.user.obj).token


@pytest.fixture()
def verified_user_status_type():
    return UserStatusType(
        verified=True,
        user=UserType.generate(),
    )


@pytest.fixture()
def unverified_user_status_type():
    return UserStatusType(
        verified=False,
        user=UserType.generate(),
    )


@pytest.fixture()
def db_unverified_user_status(db, unverified_user_status_type) -> UserStatusType:
    us = unverified_user_status_type
    us.create()
    return us


@pytest.fixture()
def db_verified_user_status(
    transactional_db, verified_user_status_type
) -> UserStatusType:
    us = verified_user_status_type
    us.create()
    return us


@pytest.fixture()
def db_archived_user_status(
    transactional_db, verified_user_status_type
) -> UserStatusType:
    us = verified_user_status_type
    us.archived = True
    us.create()
    return us


@pytest.fixture()
def wrong_pass_ver_user_status_type():
    user_type = UserType.generate()
    user_type.password = WRONG_PASSWORD
    return UserStatusType(verified=True, user=user_type)


@pytest.fixture()
def wrong_pass_unverified_user_status_type(unverified_user_status_type):
    us = unverified_user_status_type
    us.user.password = WRONG_PASSWORD
    return us


@pytest.fixture()
def captcha(transactional_db) -> Captcha:
    return Captcha.create_captcha()


@pytest.fixture()
def db_apple(transactional_db) -> Apple:
    a = Apple(color="red", name="smith")
    a.save()
    return a


@pytest.fixture()
def allow_login_not_verified(settings) -> None:
    settings.GQL_AUTH.ALLOW_LOGIN_NOT_VERIFIED = True


@pytest.fixture()
def app_settings(settings) -> GqlAuthSettings:
    return settings.GQL_AUTH


@pytest.fixture
def override_gqlauth(app_settings):
    @contextmanager
    def inner(default: Any = None, replace: Any = None, name: str = None) -> None:
        if not name:
            for field in dataclasses.fields(app_settings):
                if getattr(app_settings, field.name) == default:
                    name = field.name
                    break
            if not name:
                raise ValueError(f"setting not found for value {default}")
        else:
            default = getattr(app_settings, name)
        setattr(app_settings, name, replace)
        yield
        setattr(app_settings, name, default)

    return inner


@dataclasses.dataclass
class FakeContext:
    request: Union[HttpRequest, dict]


class SchemaHelper(NamedTuple):
    schema: Schema
    context: FakeContext
    us_type: UserStatusType

    @classmethod
    def create(cls, rf, us_type: UserStatusType, schema=arg_schema):
        user = us_type.user.obj
        req = rf.post(path="/fake")
        context = FakeContext(request=req)
        setattr(context.request, USER_OR_ERROR_KEY, UserOrError(user=user))
        return SchemaHelper(context=context, schema=schema, us_type=us_type)

    def execute(self, query: str, relay: bool = False) -> ExecutionResult:
        if relay:
            return relay_schema.execute_sync(query=query, context_value=self.context)
        return self.schema.execute_sync(query=query, context_value=self.context)


@pytest.fixture()
def anonymous_schema(rf) -> SchemaHelper:
    req = rf.post(path="/fake")
    setattr(req, USER_OR_ERROR_KEY, get_user_or_error(req))
    context = FakeContext(request=req)
    return SchemaHelper(schema=arg_schema, context=context, us_type=None)


@pytest.fixture()
def verified_schema(db_verified_user_status, rf) -> SchemaHelper:
    return SchemaHelper.create(rf=rf, us_type=db_verified_user_status)


@pytest.fixture()
def unverified_schema(rf, db_unverified_user_status) -> SchemaHelper:
    return SchemaHelper.create(rf=rf, us_type=db_unverified_user_status)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.fixture()
async def verified_channels_app_communicator(
    db_verified_user_status,
) -> GraphQLWebsocketCommunicator:
    async with GraphQLWebsocketCommunicator(
        application,
        path="graphql",
        headers=[
            (b"authorization", db_verified_user_status.generate_fresh_token().encode())
        ],
    ) as comm:
        yield comm


@pytest.fixture()
async def unverified_channels_app_communicator(
    db_verified_user_status,
) -> GraphQLWebsocketCommunicator:
    async with GraphQLWebsocketCommunicator(application, path="graphql") as comm:
        # We need this in the register test
        comm.scope["headers"].append(("host", "localhost:8000"))
        yield comm
