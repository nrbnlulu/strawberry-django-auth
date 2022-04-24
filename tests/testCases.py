import pprint
import re
from importlib import reload
import sys
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, override_settings

from gqlauth.models import UserStatus, Captcha
from gqlauth.signals import user_registered
from gqlauth.settings import gqlauth_settings

from .__init__ import *


class TestBase(TestCase):
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

    default_password = "23kegbsi7g2k"

    @staticmethod
    def gen_captcha():
        return Captcha.create_captcha()

    def register_user(
        self,
        password=None,
        verified=False,
        archived=False,
        secondary_email="",
        *args,
        **kwargs
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

    def make_request(
        self, query, variables={"user": AnonymousUser()}, raw=False, schema: str = None
    ):
        from .schema import default_schema, relay_schema

        request_factory = RequestFactory()
        context = request_factory.post("/api/")
        if schema == "relay":
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
        except:
            print("\nInvalid query!")
            raise Exception(*[error.message for error in executed.errors])
        finally:
            pprint.pprint(executed.errors)


class RelayTestCase(TestBase):
    def make_request(self, *args, **kwargs):
        return super().make_request(schema="relay", *args, **kwargs)

    def login_query(self, username="foo", password=None):
        cap = self.gen_captcha()
        return """
          mutation {
        tokenAuth(input:{username: "%s", password: "%s",identifier: "%s", userEntry: "%s"})
                      {
    success
    errors
    obtainPayload{
      token
      refreshToken
    }
  }
}

        """ % (
            username,
            password or self.default_password,
            cap.id,
            cap.text,
        )


class DefaultTestCase(TestBase):
    def make_request(self, *args, **kwargs):
        return super().make_request(schema="default", *args, **kwargs)

    def login_query(self, username="foo", password=None):
        cap = self.gen_captcha()
        return """
           mutation {
           tokenAuth(username: "%s", password: "%s" ,identifier: "%s" ,userEntry: "%s")
                  {
    success
    errors
    obtainPayload{
      token
      refreshToken
    }
  }
}

           """ % (
            username,
            password or self.default_password,
            cap.id,
            cap.text,
        )
