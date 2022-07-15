from gqlauth.utils import get_token

from .testCases import DefaultTestCase, RelayTestCase


class PasswordResetTestCaseMixin:
    def setUp(self, unverified_user):
        unverified_user = self.register_user(
            email="gaa@email.com", username="gaa", verified=True, archived=False
        )
        unverified_user_old_pass = unverified_user.password

    def test_reset_password(self, unverified_user):
        token = get_token(unverified_user, "password_reset")
        query = self.get_query(token)
        executed = self.make_request(query=query)
        assert executed["success"]
        assert not executed["errors"]
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user_old_pass == unverified_user.password)

    def test_reset_password_invalid_form(self, unverified_user):
        token = get_token(unverified_user, "password_reset")
        query = self.get_query(token, "wrong_pass")
        executed = self.make_request(query=query)
        assert not executed["success"]
        self.assertTrue(executed["errors"])
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user_old_pass != unverified_user.password)

    def test_reset_password_invalid_token(self, unverified_user):
        query = self.get_query("fake_token")
        executed = self.make_request(query=query)
        assert not executed["success"]
        self.assertTrue(executed["errors"]["nonFieldErrors"])
        unverified_user.refresh_from_db()
        self.assertTrue(unverified_user_old_pass == unverified_user.password)

    def test_revoke_refresh_tokens_on_password_reset(self, unverified_user):
        executed = self.make_request(query=self.login_query())
        unverified_user.refresh_from_db()
        refresh_tokens = unverified_user.refresh_tokens.all()
        for token in refresh_tokens:
            self.assertFalse(token.revoked)
        token = get_token(unverified_user, "password_reset")
        query = self.get_query(token)
        executed = self.make_request(query=query)
        assert executed["success"]
        assert not executed["errors"]
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user_old_pass == unverified_user.password)
        refresh_tokens = unverified_user.refresh_tokens.all()
        for token in refresh_tokens:
            assert token.revoked

    def test_reset_password_verify_user(self, unverified_user):
        unverified_user.verified = False
        unverified_user.save()

        token = get_token(unverified_user, "password_reset")
        query = self.get_query(token)
        executed = self.make_request(query=query)

        assert executed["success"]
        assert not executed["errors"]
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user_old_pass == unverified_user.password)
        self.assertTrue(unverified_user.status.verified)


class PasswordResetTestCase(PasswordResetTestCaseMixin, DefaultTestCase):
    def get_query(self, token, new_password1="new_password", new_password2="new_password"):
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


class PasswordResetRelayTestCase(PasswordResetTestCaseMixin, RelayTestCase):
    def get_query(self, token, new_password1="new_password", new_password2="new_password"):
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
