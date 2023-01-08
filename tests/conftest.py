import dataclasses
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Iterable, NamedTuple, Union

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
import faker
from faker.providers import BaseProvider
import pytest
from strawberry import Schema
from strawberry.utils.str_converters import to_camel_case

from gqlauth.core.token_to_user import USER_OR_ERROR_KEY, UserOrError
from gqlauth.settings_type import GqlAuthSettings
from testproject.sample.models import Apple
from testproject.schema import arg_schema
from tests.channelsliveserver import ChannelsLiveServer

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
        """
        This will create a new user with user status
        from the user_status_type class and will return the same object
        with the django user inside it.
        """
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


@pytest.fixture(scope="session")
def verified_user_status_type():
    return UserStatusType(
        verified=True,
        user=UserType.generate(),
    )


@pytest.fixture(scope="session")
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
def db_verified_user_status(transactional_db, verified_user_status_type) -> UserStatusType:
    us = verified_user_status_type
    us.create()
    return us


@pytest.fixture()
def db_archived_user_status(db, verified_user_status_type) -> UserStatusType:
    us = verified_user_status_type()
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
    us = unverified_user_status_type()
    us.user.password = WRONG_PASSWORD
    return us


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

    def execute(self, query: str):
        return self.schema.execute_sync(query=query, context_value=self.context)


@pytest.fixture()
def verified_schema(db_verified_user_status, rf) -> SchemaHelper:
    return SchemaHelper.create(rf=rf, us_type=db_verified_user_status)


@pytest.fixture()
def unverified_schema(rf, db_unverified_user_status) -> SchemaHelper:
    return SchemaHelper.create(rf=rf, us_type=db_unverified_user_status)


@pytest.fixture(scope="session")
def channels_live_server(request):
    server = ChannelsLiveServer()
    request.addfinalizer(server.stop)
    return server
