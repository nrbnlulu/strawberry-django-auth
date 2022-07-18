import pytest

from gqlauth.utils import get_token

from .testCases import ArgTestCase, AsyncArgTestCase, AsyncRelayTestCase, RelayTestCase


class PasswordResetTestCaseMixin:
    def _arg_query(self, token, new_password1="new_password", new_password2="new_password"):
        return """
        mutation {{
            passwordReset(
                token: "{}",
                newPassword1: "{}",
                newPassword2: "{}"
            )
            {{ success, errors }}
        }}
        """.format(
            token,
            new_password1,
            new_password2,
        )

    def _relay_query(self, token, new_password1="new_password", new_password2="new_password"):
        return """
        mutation {{
            passwordReset(
                input: {{
                    token: "{}",
                    newPassword1: "{}",
                    newPassword2: "{}"
                }})
            {{ success, errors }}
        }}
        """.format(
            token,
            new_password1,
            new_password2,
        )

    @pytest.fixture()
    def reset_token_with_unverified_user(self, db_unverified_user_status) -> tuple:
        db_unverified_user_status.user.old_password = db_unverified_user_status.user.obj.password
        return (
            db_unverified_user_status,
            get_token(db_unverified_user_status.user.obj, "password_reset"),
        )

    def test_reset_password(self, reset_token_with_unverified_user):
        user_status, token = reset_token_with_unverified_user
        user = user_status.user.obj
        query = self.make_query(token=token)
        #  user can not be verified.
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["success"]
        assert not executed["errors"]
        user.refresh_from_db()
        assert user_status.user.old_password != user.password

    def test_reset_password_invalid_form(self, reset_token_with_unverified_user):
        user_status, token = reset_token_with_unverified_user
        user = user_status.user.obj
        query = self.make_query(token, "wrong_pass")
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]
        user.refresh_from_db()
        assert user_status.user.old_password == user.password

    def test_reset_password_invalid_token(self, reset_token_with_unverified_user):
        user_status, _ = reset_token_with_unverified_user
        user = user_status.user.obj
        query = self.make_query("fake_token")
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"]
        user.refresh_from_db()
        assert user_status.user.old_password == user.password

    def test_revoke_refresh_tokens_on_password_reset(
        self, allow_login_not_verified, reset_token_with_unverified_user
    ):
        user_status, reset_token = reset_token_with_unverified_user
        user = user_status.user.obj
        self.get_tokens(user_status)
        user.refresh_from_db()
        refresh_tokens = user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert not token.revoked
        query = self.make_query(reset_token)
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["success"]
        assert not executed["errors"]
        user.refresh_from_db()
        assert user_status.user.old_password != user.password
        refresh_tokens = user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert token.revoked

    def test_reset_password_verify_user(self, db_verified_user_status):
        user = db_verified_user_status.user.obj
        old_password = user.password
        token = get_token(user, "password_reset")
        query = self.make_query(token)
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["success"]
        assert not executed["errors"]
        user.refresh_from_db()
        assert old_password != user.password
        assert user.status.verified


class TestArgPasswordReset(PasswordResetTestCaseMixin, ArgTestCase):
    ...


class TestRelyPasswordReset(PasswordResetTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgPasswordReset(PasswordResetTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayPasswordReset(PasswordResetTestCaseMixin, AsyncRelayTestCase):
    ...
