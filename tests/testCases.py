import pprint
import re

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import AsyncRequestFactory, RequestFactory
import pytest

from gqlauth.models import Captcha, UserStatus


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

    wrong_password = "wrong password"
    default_password = "FAKE@gfagfdfa132"

    def register_user(
        self, password=None, verified=False, archived=False, secondary_email="", *args, **kwargs
    ):
        if kwargs.get("username"):
            kwargs.update({"first_name": kwargs.get("username")})
        user = get_user_model().objects.create(*args, **kwargs)
        user.set_password(password or self.default_password)
        user.save()
        user_status = UserStatus._default_manager.get(user=user)
        user_status.verified = verified
        user_status.archived = archived
        user_status.secondary_email = secondary_email
        user_status.save()
        user_status.refresh_from_db()
        user.refresh_from_db()
        return user

    @pytest.fixture()
    def unverified_user(self, db):
        return self.register_user(
            email="unverified@email.com", username="unverified", verified=False
        )

    @pytest.fixture()
    def verified_user(self, db):
        return self.register_user(email="verified@email.com", username="verified", verified=True)

    @pytest.fixture()
    def verified_tokens(self):
        return self.make_request(self.login_query(username="verified"))

    @staticmethod
    def gen_captcha():
        return Captcha.create_captcha()

    def make_request(self, query, variables=None, raw=False):
        if variables is None:
            variables = {"user": AnonymousUser()}
        from .schema import default_schema, relay_schema

        request_factory = RequestFactory()
        context = request_factory.post("/api/")
        if self.RELAY:
            schema = relay_schema
        else:
            schema = default_schema
        for key in variables:
            setattr(context, key, variables[key])
        executed = schema.execute_sync(query, context_value=context)
        if raw:
            return executed.data
        pattern = r"{\s*(?P<target>\w*)"
        m = re.search(pattern, query)
        m = m.groupdict()
        try:
            return executed.data[m["target"]]
        except Exception:
            print("\nInvalid query!")
            raise Exception(*[error.message for error in executed.errors])
        finally:
            pprint.pprint(executed.errors)

    @async_to_sync
    async def amake_request(self, query, variables=None, raw=False):
        if variables is None:
            variables = {"user": AnonymousUser()}
        from .async_schema import default_schema, relay_schema

        context = AsyncRequestFactory().post("/api/")
        if self.RELAY:
            schema = relay_schema
        else:
            schema = default_schema
        for key in variables:
            setattr(context, key, variables[key])
        executed = await schema.execute(query, context_value=context)
        if raw:
            return executed.data
        pattern = r"{\s*(?P<target>\w*)"
        m = re.search(pattern, query)
        m = m.groupdict()
        try:
            return executed.data[m["target"]]
        except Exception:
            print("\nInvalid query!")
            raise Exception(*[error.message for error in executed.errors])
        finally:
            pprint.pprint(executed.errors)


class RelayTestCase(TestBase):
    RELAY = True

    def login_query(self, username, password=None):
        cap = self.gen_captcha()
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
            username,
            password or self.default_password,
            cap.uuid,
            cap.text,
        )


class DefaultTestCase(TestBase):
    RELAY = False

    def login_query(self, username="unverified", password=None):
        cap = self.gen_captcha()
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
            username,
            password or self.default_password,
            cap.uuid,
            cap.text,
        )


class AsyncTestCaseMixin:
    def make_request(self, *args, **kwargs):
        res = self.amake_request(*args, **kwargs)
        return res

    @pytest.fixture()
    def verified_tokens(self):
        # calling the sync version of make request.
        return super().make_request(self.login_query(username="verified"))


class AsyncDefaultTestCase(AsyncTestCaseMixin, DefaultTestCase):
    ...


class AsyncRelayTestCase(AsyncTestCaseMixin, RelayTestCase):
    ...
