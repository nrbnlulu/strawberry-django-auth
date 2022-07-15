import pprint
import re
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Union, NewType

import password
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.core.exceptions import SynchronousOnlyOperation
from django.test import AsyncClient, Client
from django.forms.models import model_to_dict
import pytest

from gqlauth.models import Captcha, UserStatus

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
    user: UserType
    verified: bool = False
    archived: bool = False
    secondary_email: str = ""

    @classmethod
    def create(cls, user_status: "UserStatusType") -> UserModel:
        user_status.user = UserModel(**asdict(user_status.user))
        user_status = UserStatus(**asdict(user_status))
        return user_status.user


class PATHS:
    RELAY = r'/relay_schema'
    ARG = r'/arg_schema'
    ASYNC_RELAY = r'/async_relay_schema'
    ASYNC_ARG = r'/async_arg_schema'


@pytest.mark.django_db
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

    verified_user_status_type = UserStatusType(
        verified=True,
        user=UserType(email="verified@email.com",
                      username='verified_user'),
    )
    unverified_user_status_type = UserStatusType(
        verified=False,
        user=UserType(email="unverified@email.com",
                      username='unverified_user'),
    )

    verified_user_type = verified_user_status_type.user
    unverified_user_type = unverified_user_status_type.user

    def register_user(
            self, user_status_type: UserType
    ):
        user = user_status_type.create(user_status_type)
        user.save()
        user.refresh_from_db()
        return user

    @pytest.fixture()
    def unverified_user(self, db):
        return self.register_user(
            self.verified_user_status_type
        )

    @pytest.fixture()
    def verified_user(self, db):
        return self.register_user(
            self.verified_user_status_type
        )

    @pytest.fixture()
    def verified_tokens(self):
        return self.make_request(query=self.login_query(username="verified"))

    @staticmethod
    def gen_captcha():
        return Captcha.create_captcha()

    def make_request(
            self, query: Query = None,
            user_status: UserStatusType = verified_user_status_type,
            raw: bool = False,
            path: Union[
                "PATHS.ARG", "PATHS.ASYNC_ARG", "PATHS.RELAY", "PATHS.ASYNC_RELAY"] = PATHS.ARG
    ) -> dict:
        if self.RELAY:
            path = PATHS.RELAY

        client = Client(raise_request_exception=True)
        headers = {}
        # if user_status_type was not provided then we should
        # ignore login query since there is no user
        if user_status:
            token = client.post(path=path,
                                content_type='application/json',
                                data={'query': self.login_query(user_status)})
            token = token.json()['data']
            headers = {'Authorization': f'JWT {token}'}
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

    @async_to_sync
    async def amake_request(
            self, query: Query = None,
            user_status: UserStatusType = verified_user_status_type,
            raw: bool = False,
            path: Union[
                "PATHS.ARG", "PATHS.ASYNC_ARG", "PATHS.RELAY", "PATHS.ASYNC_RELAY"] = PATHS.ARG,
            test_fail_sync_req: bool = False,
    ) -> dict:
        if self.RELAY:
            path = PATHS.ASYNC_RELAY

        client = AsyncClient(raise_request_exception=True)

        if test_fail_sync_req:
            client = Client(raise_request_exception=True)

        headers = {}
        # if user_status_type was not provided then we should
        # ignore login query since there is no user
        if user_status:
            token = await client.post(path=path,
                                content_type='application/json',
                                data={'query': self.login_query(user_status)})
            token = token.json()['data']
            headers = {'Authorization': f'JWT {token}'}
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


class DefaultTestCase(TestBase):
    RELAY = False

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
        return self.amake_request(*args, **kwargs)

    @pytest.fixture()
    def verified_tokens(self):
        # calling the sync version of make request.
        return super().make_request(query=self.login_query(username="verified"))


class AsyncDefaultTestCase(AsyncTestCaseMixin, DefaultTestCase):
    ...


class AsyncRelayTestCase(AsyncTestCaseMixin, RelayTestCase):
    ...


class AsyncFailTestMixin(AsyncTestCaseMixin):
    """
    This TestMixin checks whether a request sent with wsgi context is
    failing. Although async code can call sync code, It should raise
    """
    def make_request(self, *args, **kwargs):
        with pytest.raises(SynchronousOnlyOperation):
            return self.amake_request(*args, test_fail_sync_req=True, **kwargs)


class AsyncDefaultFailsTestCase(AsyncFailTestMixin, DefaultTestCase):
    ...


class AsyncRelayFailsTestCase(AsyncFailTestMixin, RelayTestCase):
    ...
