import pytest

from gqlauth.constants import Messages
from gqlauth.utils import get_token

from .testCases import (
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
    fake,
)


class PasswordSetTestCaseMixin:
    def _arg_query(self, token, password=None):
        password = password or fake.password()
        return """
        mutation {{
            passwordSet(
                token: "{}",
                newPassword1: "{}",
                newPassword2: "{}"
            )
            {{ success, errors }}
        }}
        """.format(
            token,
            password,
            password,
        )

    def _relay_query(self, token, password=None):
        password = password or fake.password()
        return """
        mutation {{
            passwordSet(
                input: {{
                    token: "{}",
                    newPassword1: "{}",
                    newPassword2: "{}"
                }})
            {{ success, errors }}
        }}
        """.format(
            token,
            password,
            password,
        )

    @pytest.fixture()
    def set_token_with_unverified_user(self, db_unverified_user_status) -> tuple:
        db_unverified_user_status.user.old_password = db_unverified_user_status.user.obj.password
        return (
            db_unverified_user_status,
            get_token(db_unverified_user_status.user.obj, "password_set"),
        )

    def test_already_set_password(self, set_token_with_unverified_user):
        user_status, token = set_token_with_unverified_user
        user = user_status.user.obj
        query = self.make_query(token)
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.PASSWORD_ALREADY_SET

        user.refresh_from_db()
        assert user_status.user.old_password == user.password

    def test_set_password_invalid_form(self, set_token_with_unverified_user):
        user_status, token = set_token_with_unverified_user
        user = user_status.user.obj
        # too weak password.
        query = self.make_query(token, "wrong_pass")
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]
        user.refresh_from_db()
        assert user_status.user.old_password == user.password

    def test_set_password_invalid_token(self, set_token_with_unverified_user):
        user_status, _ = set_token_with_unverified_user
        user = user_status.user.obj
        query = self.make_query("fake_token")
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"]
        user.refresh_from_db()
        assert user_status.user.old_password == user.password


class TestArgPasswordSet(PasswordSetTestCaseMixin, ArgTestCase):
    ...


class TestRelayPasswordSet(PasswordSetTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgPasswordSet(PasswordSetTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayPasswordSet(PasswordSetTestCaseMixin, AsyncRelayTestCase):
    ...
