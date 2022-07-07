from gqlauth.utils import get_token

from .testCases import DefaultTestCase, RelayTestCase


class PasswordSetTestCaseMixin:
    def setUp(self):
        self.user1 = self.register_user(
            email="gaa@email.com", username="gaa", verified=True, archived=False
        )
        self.user1_old_pass = self.user1.password

    def test_already_set_password(self):
        token = get_token(self.user1, "password_set")
        query = self.get_query(token)
        executed = self.make_request(query)
        self.assertEqual(executed["success"], False)
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
        self.user1.refresh_from_db()
        self.assertFalse(self.user1_old_pass != self.user1.password)

    def test_set_password_invalid_form(self):
        token = get_token(self.user1, "password_set")
        query = self.get_query(token, "wrong_pass")
        executed = self.make_request(query)
        self.assertEqual(executed["success"], False)
        self.assertTrue(executed["errors"])
        self.user1.refresh_from_db()
        self.assertFalse(self.user1_old_pass != self.user1.password)

    def test_set_password_invalid_token(self):
        query = self.get_query("fake_token")
        executed = self.make_request(query)
        self.assertEqual(executed["success"], False)
        self.assertTrue(executed["errors"]["nonFieldErrors"])
        self.user1.refresh_from_db()
        self.assertFalse(self.user1_old_pass != self.user1.password)


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
