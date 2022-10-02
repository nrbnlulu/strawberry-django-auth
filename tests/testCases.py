from abc import ABC
from contextlib import contextmanager
import dataclasses
from dataclasses import asdict, dataclass
import pprint
import re
from typing import TYPE_CHECKING, Any, Iterable, Union

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.test import AsyncClient, Client
from faker import Faker
from faker.providers import BaseProvider
import pytest
from strawberry.utils.str_converters import to_camel_case

from gqlauth.captcha.models import Captcha
from gqlauth.settings import gqlauth_settings
from gqlauth.settings_type import GqlAuthSettings
from testproject.sample.models import Apple

if TYPE_CHECKING:
    from gqlauth.core.utils import UserProto


class FitProvider(BaseProvider):
    _fake = Faker()

    def username(self) -> str:
        return self._fake.user_name()


UserModel = get_user_model()
fake = Faker()
fake.add_provider(FitProvider)
EMAIL_FIELD = UserModel.EMAIL_FIELD
USERNAME_FIELD = UserModel.USERNAME_FIELD
additional_fields = USERNAME_FIELD, EMAIL_FIELD


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
        if not self.username_field:
            self.username_field = getattr(self, USERNAME_FIELD)


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


class PATHS:
    RELAY = r"/relay_schema"
    ARG = r"/arg_schema"
    ASYNC_ARG = r"/arg_schema_async"
    ASYNC_RELAY = r"/relay_schema_async"


class AbstractTestCase(ABC):
    WRONG_PASSWORD = "wrong password"
    CC_USERNAME_FIELD = to_camel_case(UserModel.USERNAME_FIELD)
    USERNAME_FIELD = UserModel.USERNAME_FIELD
    AUTH_REQUIRED_QUERY = """
        query MyQuery {
          authEntry {
            ... on GQLAuthError {

              code
              message
            }
            ... on AuthQueries {

              me {
                verified
              }
            }
          }
        }
    """

    IS_RELAY = False
    IS_ASYNC = False

    def make_query(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def login_query(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def make_request(
        self,
        query: str,
        user_status: UserStatusType = None,
        raw: bool = False,
        no_login_query: bool = False,
        path: Union[
            "PATHS.ARG",
            "PATHS.RELAY",
        ] = PATHS.ARG,
    ) -> dict:
        ...

    def verified_user_status_type(self):
        return UserStatusType(
            verified=True,
            user=UserType.generate(),
        )

    def unverified_user_status_type(self):
        return UserStatusType(
            verified=False,
            user=UserType.generate(),
        )

    def get_tokens(self, user_status: UserStatusType):
        # call make_request with no user_status to ignore the default login_query
        return self.make_request(
            self.login_query(user_status), user_status=None, no_login_query=True
        )

    @staticmethod
    def gen_captcha():
        return Captcha.create_captcha()

    @pytest.fixture()
    def wrong_pass_ver_user_status_type(self):
        user_type = UserType.generate()
        user_type.password = self.WRONG_PASSWORD
        return UserStatusType(verified=True, user=user_type)

    @pytest.fixture()
    def wrong_pass_unverified_user_status_type(self):
        us = self.unverified_user_status_type()
        us.user.password = self.WRONG_PASSWORD
        return us

    @pytest.fixture()
    def db_unverified_user_status(self, db) -> UserStatusType:
        us = self.unverified_user_status_type()
        us.create()
        return us

    @pytest.fixture()
    def db_verified_user_status(self, db) -> UserStatusType:
        us = self.verified_user_status_type()
        us.create()
        return us

    @pytest.fixture()
    def db_verified_user_status_can_eat(self, db_verified_user_status) -> UserStatusType:
        from django.contrib.contenttypes.models import ContentType

        from testproject.sample.models import Apple

        ct = ContentType.objects.get_for_model(Apple)
        us = db_verified_user_status.user.obj
        perm = ct.permission_set.get(codename="can_eat")
        us.user_permissions.set((perm,))
        return db_verified_user_status

    @pytest.fixture()
    def db_archived_user_status(self, db) -> UserStatusType:
        us = self.verified_user_status_type()
        us.archived = True
        us.create()
        return us

    @pytest.fixture()
    def db_apple(self, db) -> Apple:
        a = Apple(color="red", name="smith")
        a.save()
        return a

    @pytest.fixture()
    def allow_login_not_verified(self) -> None:
        django_settings.GQL_AUTH.ALLOW_LOGIN_NOT_VERIFIED = True
        yield
        django_settings.GQL_AUTH.ALLOW_LOGIN_NOT_VERIFIED = False

    @pytest.fixture()
    def app_settings(self, settings) -> GqlAuthSettings:
        return settings.GQL_AUTH

    @contextmanager
    def override_gqlauth(self, default: Any = None, replace: Any = None, name: str = None) -> None:
        if not name:
            for field in dataclasses.fields(gqlauth_settings):
                if getattr(gqlauth_settings, field.name) == default:
                    name = field.name
                    break
            if not name:
                raise ValueError(f"setting not found for value {default}")
        else:
            default = getattr(gqlauth_settings, name)
        setattr(gqlauth_settings, name, replace)
        yield
        setattr(gqlauth_settings, name, default)


@pytest.mark.django_db(transaction=True)
class TestBase(AbstractTestCase):
    """
    provide make_request helper to easily make
    requests with context variables.
    Return a shortcut of the client.execute["data"]["<query name>"].
    example:
        query = `
            mutation {
             register ...
            }
        `
        return client.execute["data"]["register"]
    """

    def _generate_login_args(self, user_status: UserStatusType):
        cap = self.gen_captcha()
        user = user_status.user
        initial = (
            f'{to_camel_case(UserModel.USERNAME_FIELD)}: "{user.username_field}",'
            f' password: "{user.password}"'
        )

        if django_settings.GQL_AUTH.LOGIN_REQUIRE_CAPTCHA:
            initial += f', identifier: "{cap.uuid}" ,userEntry: "{cap.text}"'
        return initial

    def _get_path(self):
        if self.IS_RELAY:
            path = PATHS.RELAY
            if self.IS_ASYNC:
                path = PATHS.ASYNC_RELAY
        elif self.IS_ASYNC:
            path = PATHS.ASYNC_ARG
        else:
            path = PATHS.ARG
        return path

    def make_request(
        self,
        query: str,
        user_status: UserStatusType = None,
        raw: bool = False,
        no_login_query: bool = False,
        path: Union["PATHS.ARG", "PATHS.RELAY", "PATHS.ASYNC_ARG", "PATHS.ASYNC_RELAY"] = None,
    ) -> dict:
        if not path:
            path = self._get_path()

        client = Client(raise_request_exception=True)
        headers = {}
        # if user_status_type was not provided then we should
        # ignore login query since there is no user
        if user_status and not no_login_query:
            token = client.post(
                path=path,
                content_type="application/json",
                data={"query": self.login_query(user_status)},
            ).json()
            token = token["data"]["tokenAuth"]
            if token["success"]:
                token = token["token"]["token"]
                headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = client.post(
            path=path, content_type="application/json", data={"query": query}, **headers
        )
        res = res.json()
        if raw:
            return res["data"]
        pattern = r"{\s*(?P<target>\w*)"
        m = re.search(pattern, query)
        m = m.groupdict()
        try:
            return res["data"][m["target"]]
        except Exception:
            raise Exception(*[error["message"] for error in res["errors"]])
        finally:
            pprint.pprint(res)

    async def amake_request(
        self,
        query: str = None,
        user_status: UserStatusType = None,
        no_login_query: bool = False,
        raw: bool = False,
        path: Union[
            "PATHS.ARG",
            "PATHS.RELAY",
        ] = None,
    ) -> dict:
        if not path:
            path = self._get_path()

        client = AsyncClient(raise_request_exception=True)

        headers = {}
        # if user_status_type was not provided then we should
        # ignore login query since there is no user
        if user_status and not no_login_query:
            login_query = await sync_to_async(self.login_query)(user_status)
            token = await client.post(
                path=path, content_type="application/json", data={"query": login_query}
            )
            token = token.json()["data"]["tokenAuth"]
            if token["success"]:
                token = token["token"]["token"]
                headers = {"AUTHORIZATION": f"JWT {token}"}
        res = await client.post(
            path=path, content_type="application/json", data={"query": query}, **headers
        )

        res = res.json()
        if raw:
            return res["data"]
        pattern = r"{\s*(?P<target>\w*)"
        m = re.search(pattern, query)
        m = m.groupdict()
        try:
            return res["data"][m["target"]]
        except Exception:
            raise Exception(*[error["message"] for error in res["errors"]])
        finally:
            pprint.pprint(res)


class RelayTestCase(TestBase):
    IS_RELAY = True

    # TODO: is that used anywhere?
    def make_query(self, *args, **kwargs):
        return self._relay_query(*args, **kwargs)

    def login_query(self, user_status: UserStatusType) -> str:
        return """
          mutation {{
        tokenAuth(input:{{{}}})
                      {{
            errors
            success
            refreshToken {{
              created
              isExpired
              expiresAt
              token
              revoked
            }}
            token {{
              token
              payload {{
                exp
                origIat
              }}
            }}
            user {{
              archived
              dateJoined
              firstName
              isActive
              id
              isStaff
              isSuperuser
              lastLogin
              lastName
              logentrySet {{
                pk
              }}
              status {{
                archived
                verified
              }}
              verified
            }}
          }}
        }}
        """.format(
            self._generate_login_args(user_status)
        )


class ArgTestCase(TestBase):
    RELAY = False

    def make_query(self, *args, **kwargs):
        return self._arg_query(*args, **kwargs)

    def login_query(self, user_status: UserStatusType) -> str:
        return """
           mutation {{
           tokenAuth({})
                  {{
            errors
            success
            refreshToken {{
              created
              isExpired
              expiresAt
              token
              revoked
            }}
            token {{
              token
              payload {{
                exp
                origIat
              }}
            }}
            user {{
              archived
              dateJoined
              firstName
              isActive
              id
              isStaff
              isSuperuser
              lastLogin
              lastName
              logentrySet {{
                pk
              }}
              status {{
                archived
                verified
              }}
              verified
            }}
          }}
        }}
           """.format(
            self._generate_login_args(user_status)
        )


class AsyncTestCaseMixin(AbstractTestCase):
    def make_request(self, *args, **kwargs):
        return async_to_sync(self.amake_request)(*args, **kwargs)

    IS_ASYNC = True


class AsyncArgTestCase(AsyncTestCaseMixin, ArgTestCase):
    ...


class AsyncRelayTestCase(AsyncTestCaseMixin, RelayTestCase):
    ...
