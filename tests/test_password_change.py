from gqlauth.utils import revoke_user_refresh_token

from .testCases import DefaultTestCase, RelayTestCase


class PasswordChangeTestCaseMixin:
    def setUp(self):
        super().setUp()
        self.user = self.register_user(email="gaa@email.com", username="gaa", verified=True)
        self.old_pass = self.user.password

    def test_password_change(self):
        """
        change password
        """
        variables = {"user": self.user}
        executed = self.make_request(self.get_query(), variables)
        assert executed["success"]
        assert not executed["errors"]
        assert executed["obtainPayload"]["token"]
        assert executed["obtainPayload"]["refreshToken"]
        self.user.refresh_from_db()
        self.assertFalse(self.old_pass == self.user.password)

    def test_mismatch_passwords(self):
        """
        wrong inputs
        """
        variables = {"user": self.user}
        executed = self.make_request(query=self.get_query("wrong"), user=variables)
        assert not executed["success"]
        self.assertTrue(executed["errors"]["newPassword2"])
        assert not executed["obtainPayload"]
        self.user.refresh_from_db()
        self.assertTrue(self.old_pass == self.user.password)

    def test_passwords_validation(self):
        """
        easy password
        """
        variables = {"user": self.user}
        executed = self.make_request(query=self.get_query("123", "123"), user=variables)
        assert not executed["success"]
        self.assertTrue(executed["errors"]["newPassword2"])
        assert not executed["obtainPayload"]

    def test_revoke_refresh_tokens_on_password_change(self):
        executed = self.make_request(query=self.login_query())
        self.user.refresh_from_db()
        refresh_tokens = self.user.refresh_tokens.all()
        for token in refresh_tokens:
            self.assertFalse(token.revoked)
        variables = {"user": self.user}
        executed = self.make_request(query=self.get_query(), user=variables)
        assert executed["success"]
        assert not executed["errors"]
        assert executed["obtainPayload"]["token"]
        assert executed["obtainPayload"]["refreshToken"]
        self.user.refresh_from_db()
        self.assertFalse(self.old_pass == self.user.password)
        refresh_tokens = self.user.refresh_tokens.all()
        revoke_user_refresh_token(self.user)
        self.user.refresh_from_db()
        refresh_tokens = self.user.refresh_tokens.all()
        for token in refresh_tokens:
            assert token.revoked


class PasswordChangeTestCase(PasswordChangeTestCaseMixin, DefaultTestCase):
    def get_query(self, new_password1="new_password", new_password2="new_password"):
        return """
        mutation {{
            passwordChange(
                oldPassword: "{}",
                newPassword1: "{}",
                newPassword2: "{}"
            )
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
            self.DEFAULT_PASSWORD,
            new_password1,
            new_password2,
        )


class PasswordChangeRelayTestCase(PasswordChangeTestCaseMixin, RelayTestCase):
    def get_query(self, new_password1="new_password", new_password2="new_password"):
        return """
        mutation {{
            passwordChange(
                input: {{
                    oldPassword: "{}",
                    newPassword1: "{}",
                    newPassword2: "{}"
                }})
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
            self.DEFAULT_PASSWORD,
            new_password1,
            new_password2,
        )
