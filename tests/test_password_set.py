from gqlauth.utils import get_token

from .testCases import DefaultTestCase, RelayTestCase


class PasswordSetTestCaseMixin:
    def setUp(self):
        unverified_user = self.register_user(
            email="gaa@email.com", username="gaa", verified=True, archived=False
        )
        unverified_user_old_pass = unverified_user.password

    def test_already_set_password(self):
        token = get_token(unverified_user, "password_set")
        query = self.get_query(token)
        executed = self.make_request(query=query)
        assert not executed["success"]
        self.assertEqual(
            executed["errors"],
            {
                "nonFieldErrors": [
                    {
                        "code": "password_already_set",
                        "message": "Password already set for account.",
                    }
                ]
            },
        )
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user_old_pass != unverified_user.password)

    def test_set_password_invalid_form(self):
        token = get_token(unverified_user, "password_set")
        query = self.get_query(token, "wrong_pass")
        executed = self.make_request(query=query)
        assert not executed["success"]
        self.assertTrue(executed["errors"])
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user_old_pass != unverified_user.password)

    def test_set_password_invalid_token(self):
        query = self.get_query("fake_token")
        executed = self.make_request(query=query)
        assert not executed["success"]
        self.assertTrue(executed["errors"]["nonFieldErrors"])
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user_old_pass != unverified_user.password)


class PasswordSetTestCase(PasswordSetTestCaseMixin, DefaultTestCase):
    def get_query(self, token, new_password1="new_password", new_password2="new_password"):
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
            new_password1,
            new_password2,
        )


class PasswordSetRelayTestCase(PasswordSetTestCaseMixin, RelayTestCase):
    def get_query(self, token, new_password1="new_password", new_password2="new_password"):
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
            new_password1,
            new_password2,
        )
