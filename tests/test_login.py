from gqlauth.constants import Messages
from gqlauth.settings import gqlauth_settings

from .testCases import (
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
    UserStatusType,
)


class LoginTestCaseMixin:
    def setUp(self):
        gqlauth_settings.ALLOW_DELETE_ACCOUNT = True

    def _arg_query(self, user_status: UserStatusType):
        user = user_status.user
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
            user.username,
            user.password,
            cap.uuid,
            cap.text,
        )

    def _relay_query(self, user_status: UserStatusType):
        cap = self.gen_captcha()
        user = user_status.user
        return """
        mutation {{
        tokenAuth(input:{{username: "{}", password: "{}",identifier: "{}", userEntry: "{}"}})  {{
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

    def test_archived_user_becomes_active_on_login(self, db_archived_user_status):
        user = db_archived_user_status.user.obj
        assert user.status.archived
        query = self.make_query(db_archived_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        user.refresh_from_db()
        assert not user.status.archived
        assert executed["success"]
        assert not executed["errors"]
        assert executed["obtainPayload"]["token"]
        assert executed["obtainPayload"]["refreshToken"]

    def test_login_username(
        self,
        db_verified_user_status,
        db_unverified_user_status,
        allow_login_not_verified,
    ):
        query = self.make_query(db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["success"]
        assert not executed["errors"]
        assert executed["obtainPayload"]["token"]
        assert executed["obtainPayload"]["refreshToken"]
        query = self.make_query(db_unverified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["success"]
        assert not executed["errors"]
        assert executed["obtainPayload"]["token"]
        assert executed["obtainPayload"]["refreshToken"]

    def test_login_wrong_username(self, db_verified_user_status):
        db_verified_user_status.user.username = "wrong_username"
        query = self.make_query(db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]
        assert not executed["obtainPayload"]

    def test_login_wrong_password(self, db_verified_user_status):
        db_verified_user_status.user.password = self.WRONG_PASSWORD
        query = self.make_query(db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]
        assert not executed["obtainPayload"]

    def test_not_verified_login_not_verified(self, db_unverified_user_status):
        query = self.make_query(db_unverified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.NOT_VERIFIED
        assert not executed["obtainPayload"]

    def test_setting_not_verified_allowed_but_with_wrong_pass(
        self,
        db_unverified_user_status,
        allow_login_not_verified,
    ):
        db_unverified_user_status.user.password = self.WRONG_PASSWORD
        query = self.make_query(db_unverified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.INVALID_CREDENTIALS
        assert not executed["obtainPayload"]


class TestArgLogin(LoginTestCaseMixin, ArgTestCase):
    ...


class TestRelayLogin(LoginTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgArchiveAccount(LoginTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayArchiveAccount(LoginTestCaseMixin, AsyncRelayTestCase):
    ...
