import pprint
import re
from dataclasses import dataclass, asdict
from typing import Union, NewType
from django.conf import settings as django_settings

from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth import get_user_model
from django.test import AsyncClient, Client
import pytest

from gqlauth.models import Captcha

Query = NewType("Query", str)
UserModel = get_user_model()


@dataclass
class UserType:
    username: str
    email: str
    first_name: str = None
    password: str = "FAKE@gfagfdfa132"

    def __post_init__(self):
        if not self.first_name:
            self.first_name = self.username


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
    RELAY = r'/relay_schema'
    ARG = r'/arg_schema'
    ASYNC_RELAY = r'/async_relay_schema'
    ASYNC_ARG = r'/async_arg_schema'


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

    def verified_user_status_type(self):
        return UserStatusType(
            verified=True,
            user=UserType(email="verified@email.com",
                          username='verified_user'),
        )

    def unverified_user_status_type(self):
        return UserStatusType(
            verified=False,
            user=UserType(email="unverified@email.com",
                          username='unverified_user'),
        )

    def get_tokens(self, user_status: UserStatusType):
        # call make_request with no user_status to ignore the default login_query
        return self.make_request(
            self.login_query(user_status),
            user_status=None,
            no_login_query=True
        )

    @staticmethod
    def gen_captcha():
        return Captcha.create_captcha()

    @pytest.fixture()
    def wrong_pass_ver_user_status_type(self):
        return UserStatusType(
            verified=True,
            user=UserType(email="verified@email.com",
                          username='verified_user',
                          password=self.WRONG_PASSWORD,
                          ),
        )

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
            self, query: Query,
            user_status: UserStatusType = None,
            raw: bool = False,
            no_login_query: bool = False,
            path: Union[
                "PATHS.ARG", "PATHS.ASYNC_ARG", "PATHS.RELAY", "PATHS.ASYNC_RELAY"] = PATHS.ARG
    ) -> dict:
        if self.RELAY:
            path = PATHS.RELAY

        client = Client(raise_request_exception=True)
        headers = {}
        # if user_status_type was not provided then we should
        # ignore login query since there is no user
        if user_status and not no_login_query:
            token = client.post(path=path,
                                content_type='application/json',
                                data={'query': self.login_query(user_status)}).json()['data'][
                'tokenAuth']
            if token['success']:
                token = token['obtainPayload']['token']
                headers = {'HTTP_AUTHORIZATION': f'JWT {token}'}
        res = client.post(path=path, content_type='application/json',
                          data={'query': query}, **headers)

        res = res.json()
        if raw:
            return res['data']
        pattern = r"{\s*(?P<target>\w*)"
        m = re.search(pattern, query)
        m = m.groupdict()
        try:
            return res['data'][m["target"]]
        except Exception:
            raise Exception(*[error['message'] for error in res['errors']])
        finally:
            pprint.pprint(res)

    async def amake_request(
            self, query: Query = None,
            user_status: UserStatusType = None,
            no_login_query: bool = False,
            raw: bool = False,
            path: Union[
                "PATHS.ARG", "PATHS.ASYNC_ARG", "PATHS.RELAY", "PATHS.ASYNC_RELAY"] = PATHS.ASYNC_ARG,
            test_fail_sync_req: bool = False,
    ) -> dict:
        if self.RELAY:
            path = PATHS.ASYNC_RELAY

        client = AsyncClient(raise_request_exception=True)

        if test_fail_sync_req:
            client = Client(raise_request_exception=True)

        headers = dict()
        # if user_status_type was not provided then we should
        # ignore login query since there is no user
        if user_status and not no_login_query:
            login_query = await sync_to_async(self.login_query)(user_status)
            token = await client.post(path=path,
                                content_type='application/json',
                                data={'query': login_query})
            token = token.json()['data']['tokenAuth']
            if token['success']:
                token = token['obtainPayload']['token']
                headers = {'AUTHORIZATION': f'JWT {token}'}
        res = await client.post(path=path, content_type='application/json',
                                data={'query': query}, **headers)

        res = res.json()
        if raw:
            return res['data']
        pattern = r"{\s*(?P<target>\w*)"
        m = re.search(pattern, query)
        m = m.groupdict()
        try:
            return res['data'][m["target"]]
        except Exception:
            raise Exception(*[error['message'] for error in res['errors']])
        finally:
            pprint.pprint(res)


class RelayTestCase(TestBase):
    RELAY = True

    def make_query(self, *args, **kwargs):
        return self._relay_query(*args, **kwargs)

    def login_query(self, user_status: UserStatusType):
        cap = self.gen_captcha()
        user = user_status.user
        return """
          mutation {{
        tokenAuth(input:{{username: "{}", password: "{}",identifier: "{}", userEntry: "{}"}})
                      {{
            success
            errors
            obtainPayload{{
              token
              refreshToken
            }}
          }}
        }}
        """.format(
            user.username,
            user.password,
            cap.uuid,
            cap.text,
        )


class ArgTestCase(TestBase):
    RELAY = False

    def make_query(self, *args, **kwargs):
        return self._arg_query(*args, **kwargs)

    def login_query(self, user_status: UserStatusType):
        cap = self.gen_captcha()
        user = user_status.user
        return """
           mutation {{
           tokenAuth(username: "{}", password: "{}" ,identifier: "{}" ,userEntry: "{}")
                  {{
                success
                errors
                obtainPayload{{
                  token
                  refreshToken
                }}
              }}
            }}

           """.format(
            user.username,
            user.password,
            cap.uuid,
            cap.text,
        )


class AsyncTestCaseMixin:

    def make_request(self, *args, **kwargs):
        return async_to_sync(self.amake_request)(*args, **kwargs)



class AsyncDefaultTestCase(AsyncTestCaseMixin, ArgTestCase):
    ...


class AsyncRelayTestCase(AsyncTestCaseMixin, RelayTestCase):
    ...


