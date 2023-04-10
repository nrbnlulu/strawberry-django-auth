import dataclasses
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, NamedTuple, Union

import faker
import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test.client import RequestFactory
from faker.providers import BaseProvider
from gqlauth.backends.basebackend import UserProto
from gqlauth.backends.strawberry_django_auth.backend import DjangoUserProto
from gqlauth.backends.strawberry_django_auth.models import Captcha, RefreshToken
from gqlauth.core.constants import JWT_PREFIX
from gqlauth.core.middlewares import USER_OR_ERROR_KEY, UserOrError, get_user_or_error
from gqlauth.jwt.types_ import TokenType
from gqlauth.settings_type import GqlAuthSettings
from strawberry import Schema
from strawberry.channels.testing import GraphQLWebsocketCommunicator
from strawberry.types import ExecutionResult
from strawberry.utils.str_converters import to_camel_case

from gql.relay_schema import relay_schema
from gql.schema import arg_schema
from sample.models import Apple
from testproject.asgi import application as testproject_application

sys.path.append(str(Path(__file__).parent.parent))


if TYPE_CHECKING:  # pragma: no cover
    pass
UserModel = get_user_model()
WRONG_PASSWORD = "wrong password"
CC_USERNAME_FIELD = to_camel_case(UserModel.USERNAME_FIELD)
USERNAME_FIELD = UserModel.USERNAME_FIELD
EMAIL_FIELD = UserModel.EMAIL_FIELD

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
class UserType:
    verified: bool
    archived: bool = False
    password: str = dataclasses.field(default_factory=lambda: fake.password())
    email_field: str = dataclasses.field(default_factory=lambda: fake.email())
    username_field: str = dataclasses.field(default_factory=lambda: fake.user_name())

    def create(self) -> UserProto:
        flex_fields = {
            EMAIL_FIELD: self.email_field,
            USERNAME_FIELD: self.username_field,
        }
        user: UserProto = UserModel(**flex_fields)

        # password must be set via this method.
        self.user.set_password(self.password)

        user.set_verified(self.verified)
        user.set_archived(self.archived)
        user.save()
        return user

    def generate_refresh_token(self, user: DjangoUserProto) -> RefreshToken:
        return RefreshToken.from_user(user)


@pytest.fixture()
def verified_user_type():
    return UserType(
        verified=True,
    ).create()


@pytest.fixture()
def unverified_user_type():
    return UserType(
        verified=False,
    )


@pytest.fixture()
def wrong_pass_ver_user_status_type():
    return UserType(password=WRONG_PASSWORD, verified=True)


@pytest.fixture()
def wrong_pass_unverified_user_status_type(unverified_user_type):
    return UserType(verified=False, password=WRONG_PASSWORD)


@pytest.fixture()
def captcha(db) -> Captcha:
    return Captcha.create_captcha()


@pytest.fixture()
def db_apple(db) -> Apple:
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
    user: UserProto

    @classmethod
    def create(cls, req, user: UserProto, schema=arg_schema):
        context = FakeContext(request=req)
        setattr(context.request, USER_OR_ERROR_KEY, UserOrError(user=user))
        return SchemaHelper(context=context, schema=schema, user=user)

    def execute(self, query: str, relay: bool = False) -> ExecutionResult:
        if relay:
            return relay_schema.execute_sync(query=query, context_value=self.context)
        return self.schema.execute_sync(query=query, context_value=self.context)


class GqlAuthTestCase:
    user: UserType

    @contextmanager
    def ws_client_no_headers(self, user: UserProto):
        with GraphQLWebsocketCommunicator(
            application=testproject_application,
            path="graphql",
        ) as communicator:
            yield communicator

    @pytest.fixture()
    def ws_verified_client(self, user: UserProto) -> GraphQLWebsocketCommunicator:
        with GraphQLWebsocketCommunicator(
            application=testproject_application,
            path="graphql",
            headers=[(b"authorization", self.generate_fresh_token(user).encode())],
        ) as communicator:
            yield communicator

    def generate_fresh_token(self, user: UserProto) -> str:
        return JWT_PREFIX + " " + TokenType.from_user(user).token

    def anonymous_schema(self) -> SchemaHelper:
        req = self.request()
        setattr(req, USER_OR_ERROR_KEY, get_user_or_error(req))
        context = FakeContext(request=req)
        return SchemaHelper(schema=arg_schema, context=context, user=None)

    def request(self):
        return RequestFactory().post("/fake")

    @pytest.fixture()
    def verified_schema(self) -> SchemaHelper:
        user = UserType(verified=True).create()
        return SchemaHelper.create(req=self.request(), user=user)

    def unverified_schema(self) -> SchemaHelper:
        user = UserType(verified=False).create()
        return SchemaHelper.create(req=self.request(), user=user)
