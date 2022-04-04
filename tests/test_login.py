from .__init__ import *
from gqlauth.models import Captcha
from .testCases import RelayTestCase, DefaultTestCase
from gqlauth.constants import Messages
from gqlauth.settings import gqlauth_settings

class LoginTestCaseMixin:
    def setUp(self):
        gqlauth_settings.ALLOW_DELETE_ACCOUNT = True
        self.archived_user = self.register_user(
            email="gaa@email.com", username="gaa", verified=True, archived=True
        )
        self.not_verified_user = self.register_user(
            email="boo@email.com", username="boo", verified=False
        )
        self.verified_user = self.register_user(
            email="foo@email.com",
            username="foo",
            verified=True,
            secondary_email="secondary@email.com",
        )
    @staticmethod
    def gen_captcha():
        return Captcha.create_captcha()

    def test_archived_user_becomes_active_on_login(self):
        self.assertEqual(self.archived_user.status.archived, True)
        query = self.get_query(self.archived_user.username)
        executed = self.make_request(query)
        self.archived_user.refresh_from_db()
        self.assertEqual(self.archived_user.status.archived, False)
        self.assertTrue(executed["success"])
        self.assertFalse(executed["errors"])
        self.assertTrue(executed['obtainPayload']["token"])
        self.assertTrue(executed['obtainPayload']["refreshToken"])

    def test_login_username(self):
        query = self.get_query(self.verified_user.username)
        executed = self.make_request(query)
        self.assertTrue(executed["success"])
        self.assertFalse(executed["errors"])
        self.assertTrue(executed['obtainPayload']["token"])
        self.assertTrue(executed['obtainPayload']["refreshToken"])
        gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED = True
        query = self.get_query(self.not_verified_user.username)
        executed = self.make_request(query)
        self.assertTrue(executed["success"])
        self.assertFalse(executed["errors"])
        self.assertTrue(executed['obtainPayload']["token"])
        self.assertTrue(executed['obtainPayload']["refreshToken"])

    def test_login_wrong_credentials(self):
        query = self.get_query("username", "wrong")
        executed = self.make_request(query)
        self.assertFalse(executed["success"])
        self.assertTrue(executed["errors"])
        self.assertFalse(executed['obtainPayload'])

    def test_login_wrong_credentials_2(self):
        query = self.get_query(self.verified_user.username, "wrongpass")
        executed = self.make_request(query)
        self.assertFalse(executed["success"])
        self.assertTrue(executed["errors"])
        self.assertFalse(executed['obtainPayload'])

    @override_settings(GQL_AUTH=SETTING_B)
    def test_not_verified_login_not_verified(self):
        gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED = False
        query = self.get_query(self.not_verified_user.username)
        executed = self.make_request(query)
        self.assertFalse(executed["success"])
        self.assertEqual(executed["errors"]["nonFieldErrors"], Messages.NOT_VERIFIED)
        self.assertFalse(executed['obtainPayload'])

    @override_settings(GQL_AUTH=SETTING_B)
    def test_setting_not_verified_allowed_but_with_wrong_pass(self):
        gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED = True
        query = self.get_query(self.not_verified_user.username, "wrongpass")
        executed = self.make_request(query)
        self.assertFalse(executed["success"])
        self.assertEqual(
            executed["errors"]["nonFieldErrors"], Messages.INVALID_CREDENTIALS
        )
        self.assertFalse(executed['obtainPayload'])



class LoginTestCase(LoginTestCaseMixin, DefaultTestCase):
    def get_query(self, username, password=None):
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


class LoginRelayTestCase(LoginTestCaseMixin, RelayTestCase):
    def get_query(self, username, password=None):
        cap = self.gen_captcha()
        return """
        mutation {
        tokenAuth(input_:{username: "%s", password: "%s",identifier: "%s", userEntry: "%s"})  {
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
