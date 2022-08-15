from dataclasses import asdict, dataclass
import pprint
import re
from typing import Iterable, NewType, Union

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.test import AsyncClient, Client
from faker import Faker
from faker.providers import BaseProvider
import pytest
from strawberry.utils.str_converters import to_camel_case

from gqlauth.captcha.models import Captcha


class FitProvider(BaseProvider):
    _fake = Faker()

    def username(self) -> str:
        return self._fake.user_name()


Query = NewType("Query", str)
UserModel = get_user_model()
fake = Faker()
fake.add_provider(FitProvider)

additional_fields = UserModel.USERNAME_FIELD, UserModel.EMAIL_FIELD


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

    @classmethod
    def generate(cls):
        kwargs = {field: getattr(fake, field)() for field, _ in cls.__annotations__.items()}
        return cls(**kwargs)

    @property
    def USERNAME_FIELD(self):
        return getattr(self, UserModel.USERNAME_FIELD)

    @USERNAME_FIELD.setter
    def USERNAME_FIELD(self, value):
        setattr(self, UserModel.USERNAME_FIELD, value)


@dataclass
class UserStatusType:
    verified: bool
    archived: bool = False
    secondary_email: str = ""
    user: Union[UserModel, UserType] = None

    def create(self):
        """
        This will create a new user with user status
        from the user_status_type class and will return the same object
        with the django user inside it.
        """
        user = self.user  # caching the user type object
        self.user = UserModel(**asdict(user))
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
    ASYNC_RELAY = r"/async_relay_schema"
    ASYNC_ARG = r"/async_arg_schema"


@pytest.mark.django_db(transaction=True)
class TestBase:
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

    WRONG_PASSWORD = "wrong password"
    CC_USERNAME_FIELD = to_camel_case(UserModel.USERNAME_FIELD)
    USERNAME_FIELD = UserModel.USERNAME_FIELD

    def _generate_login_args(self, user_status: UserStatusType):
        cap = self.gen_captcha()
        user = user_status.user
        initial = (
            f'{to_camel_case(UserModel.USERNAME_FIELD)}: "{user.USERNAME_FIELD}",'
            f' password: "{user.password}"'
        )

        if django_settings.GQL_AUTH.LOGIN_REQUIRE_CAPTCHA:
            initial += f', identifier: "{cap.uuid}" ,userEntry: "{cap.text}"'
        return initial

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
    def db_verified_with_secondary_email(self, db_verified_user_status) -> UserStatusType:
        user = db_verified_user_status.user.obj
        user.status.secondary_email = "secondary@email.com"
        user.status.save()
        user.refresh_from_db()
        return db_verified_user_status

    @pytest.fixture()
    def db_archived_user_status(self, db) -> UserStatusType:
        us = self.verified_user_status_type()
        us.archived = True
        us.create()
        return us

    @pytest.fixture()
    def allow_login_not_verified(self):
        django_settings.GQL_AUTH.ALLOW_LOGIN_NOT_VERIFIED = True
        yield
        django_settings.GQL_AUTH.ALLOW_LOGIN_NOT_VERIFIED = False

    def make_request(
        self,
        query: Query,
        user_status: UserStatusType = None,
        raw: bool = False,
        no_login_query: bool = False,
        path: Union["PATHS.ARG", "PATHS.ASYNC_ARG", "PATHS.RELAY", "PATHS.ASYNC_RELAY"] = PATHS.ARG,
    ) -> dict:
        if self.RELAY:
            path = PATHS.RELAY

        client = Client(raise_request_exception=True)
        headers = {}
        # if user_status_type was not provided then we should
        # ignore login query since there is no user
        if user_status and not no_login_query:
            token = client.post(
                path=path,
                content_type="application/json",
                data={"query": self.login_query(user_status)},
            ).json()["data"]["tokenAuth"]
            if token["success"]:
                token = token["obtainPayload"]["token"]
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
        query: Query = None,
        user_status: UserStatusType = None,
        no_login_query: bool = False,
        raw: bool = False,
        path: Union[
            "PATHS.ARG", "PATHS.ASYNC_ARG", "PATHS.RELAY", "PATHS.ASYNC_RELAY"
        ] = PATHS.ASYNC_ARG,
    ) -> dict:
        if self.RELAY:
            path = PATHS.ASYNC_RELAY

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
                token = token["obtainPayload"]["token"]
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
    RELAY = True

    def make_query(self, *args, **kwargs):
        return self._relay_query(*args, **kwargs)

    def login_query(self, user_status: UserStatusType):
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
                username
              }}
            }}
            user {{
              archived
              dateJoined
              firstName
              email
              isActive
              id
              isStaff
              isSuperuser
              lastLogin
              lastName
              logentrySet {{
                pk
              }}
              secondaryEmail
              status {{
                archived
                verified
                secondaryEmail
              }}
              username
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

    def login_query(self, user_status: UserStatusType):

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
                username
              }}
            }}
            user {{
              archived
              dateJoined
              firstName
              email
              isActive
              id
              isStaff
              isSuperuser
              lastLogin
              lastName
              logentrySet {{
                pk
              }}
              secondaryEmail
              status {{
                archived
                verified
                secondaryEmail
              }}
              username
              verified
            }}
          }}
        }}
           """.format(
            self._generate_login_args(user_status)
        )


class AsyncTestCaseMixin:
    def make_request(self, *args, **kwargs):
        return async_to_sync(self.amake_request)(*args, **kwargs)


class AsyncArgTestCase(AsyncTestCaseMixin, ArgTestCase):
    ...


class AsyncRelayTestCase(AsyncTestCaseMixin, RelayTestCase):
    ...
