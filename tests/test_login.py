from gqlauth.core.constants import Messages

from .testCases import (
    AbstractTestCase,
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
)


class LoginTestCaseMixin(AbstractTestCase):
    def test_archived_user_becomes_active_on_login(self, db_archived_user_status):
        user = db_archived_user_status.user.obj
        assert user.status.archived
        query = self.login_query(db_archived_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        user.refresh_from_db()
        assert not user.status.archived
        assert executed["success"]
        assert not executed["errors"]
        assert executed["refreshToken"]["token"]
        assert executed["token"]["token"]

    def test_login_username(
        self,
        db_verified_user_status,
        db_unverified_user_status,
        allow_login_not_verified,
    ):
        query = self.login_query(db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["success"]
        assert not executed["errors"]
        assert executed["refreshToken"]["token"]
        assert executed["token"]["token"]
        query = self.login_query(db_unverified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["success"]
        assert not executed["errors"]
        assert executed["refreshToken"]["token"]
        assert executed["token"]["token"]

    def test_login_wrong_username(self, db_verified_user_status):
        db_verified_user_status.user.username_field = "wrong_username"
        query = self.login_query(db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]
        assert not executed["refreshToken"]

    def test_login_wrong_password(self, db_verified_user_status):
        db_verified_user_status.user.password = self.WRONG_PASSWORD
        query = self.login_query(db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]
        assert not executed["refreshToken"]

    def test_not_verified_login_not_verified(self, db_unverified_user_status):
        query = self.login_query(db_unverified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.NOT_VERIFIED
        assert not executed["refreshToken"]

    def test_setting_not_verified_allowed_but_with_wrong_pass(
        self,
        db_unverified_user_status,
        allow_login_not_verified,
    ):
        db_unverified_user_status.user.password = self.WRONG_PASSWORD
        query = self.login_query(db_unverified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.INVALID_CREDENTIALS
        assert not executed["refreshToken"]


class TestArgLogin(LoginTestCaseMixin, ArgTestCase):
    ...


class TestRelayLogin(LoginTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgArchiveAccount(LoginTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayArchiveAccount(LoginTestCaseMixin, AsyncRelayTestCase):
    ...
