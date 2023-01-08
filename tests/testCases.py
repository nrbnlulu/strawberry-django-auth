from abc import ABC
from contextlib import contextmanager
import dataclasses
import pprint
import re
from typing import Any, Union

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings as django_settings
import pytest
from strawberry.utils.str_converters import to_camel_case

from gqlauth.captcha.models import Captcha
from gqlauth.settings import gqlauth_settings
from tests.conftest import UserModel, UserStatusType

from .conftest import WRONG_PASSWORD


class PATHS:
    RELAY = r"/relay_schema"
    ARG = r"/arg_schema"
    ASYNC_ARG = r"/arg_schema_async"
    ASYNC_RELAY = r"/relay_schema_async"


class AbstractTestCase(ABC):
    WRONG_PASSWORD = WRONG_PASSWORD
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

    @staticmethod
    def gen_captcha():
        return Captcha.create_captcha()

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
        from django.test import Client

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
        from django.test.client import AsyncClient

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
