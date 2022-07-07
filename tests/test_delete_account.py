from django.core.exceptions import ObjectDoesNotExist
from pytest import mark

from gqlauth.constants import Messages
from gqlauth.settings import gqlauth_settings as app_settings

from .testCases import DefaultTestCase, RelayTestCase


class DeleteAccountTestCaseMixin:
    def setUp(self):
        self.user1 = self.register_user(email="foo@email.com", username="foo")
        self.user2 = self.register_user(email="bar@email.com", username="bar", verified=True)
        app_settings.ALLOW_DELETE_ACCOUNT = True

    def test_not_authenticated(self):
        """
        try to archive not authenticated
        """
        query = self.make_query()
        executed = self.make_request(query)
        self.assertEqual(executed["success"], False)
        self.assertEqual(executed["errors"]["nonFieldErrors"], Messages.UNAUTHENTICATED)

    def test_invalid_password(self):
        query = self.make_query(password="123")
        variables = {"user": self.user2}
        executed = self.make_request(query, variables)
        self.assertEqual(executed["success"], False)
        self.assertEqual(executed["errors"]["password"], Messages.INVALID_PASSWORD)

    def test_not_verified_user(self):
        query = self.make_query()
        variables = {"user": self.user1}
        self.assertEqual(self.user1.is_active, True)
        executed = self.make_request(query, variables)
        self.assertEqual(executed["success"], False)
        self.assertEqual(executed["errors"]["nonFieldErrors"], Messages.NOT_VERIFIED)
        self.assertEqual(self.user1.is_active, True)

    @mark.settings_b
    def test_valid_password_permanently_delete(self):
        query = self.make_query()
        variables = {"user": self.user2}
        self.assertEqual(self.user2.is_active, True)
        executed = self.make_request(query, variables)
        self.assertEqual(executed["success"], True)
        self.assertEqual(executed["errors"], None)
        with self.assertRaises(ObjectDoesNotExist):
            self.user2.refresh_from_db()

    def make_query(self, password=None):
        return """
            mutation {{
              deleteAccount(password: "{}") {{
                success, errors
              }}
            }}
        """.format(
            password or self.default_password,
        )


class DeleteAccountTestCase(DeleteAccountTestCaseMixin, DefaultTestCase):
    def make_query(self, password=None):
        return """
            mutation {{
              deleteAccount(password: "{}") {{
                success, errors
              }}
            }}
        """.format(
            password or self.default_password,
        )


class DeleteAccountRelayTestCase(DeleteAccountTestCaseMixin, RelayTestCase):
    def make_query(self, password=None):
        return """
            mutation {{
              deleteAccount(input: {{ password: "{}"}}) {{
                success, errors
              }}
            }}
        """.format(
            password or self.default_password,
        )
