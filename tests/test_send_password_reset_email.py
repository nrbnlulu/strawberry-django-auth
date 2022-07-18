from smtplib import SMTPException
from unittest import mock

from gqlauth.constants import Messages

from .testCases import DefaultTestCase, RelayTestCase


class SendPasswordResetEmailTestCaseMixin:
    def setUp(self):
        unverified_user = self.register_user(email="foo@email.com", username="foo", verified=False)
        self.user2 = self.register_user(
            email="bar@email.com",
            username="bar",
            verified=True,
            secondary_email="secondary@email.com",
        )

    def test_send_email_invalid_email(self):
        """
        invalid email should be successful request
        """
        query = self.make_query("invalid@email.com")
        executed = self.make_request(query=query)
        assert executed["success"]
        assert not executed["errors"]

    def test_invalid_form(self):
        query = self.make_query("baremail.com")
        executed = self.make_request(query=query)
        assert not executed["success"]
        self.assertTrue(executed["errors"]["email"])

    def test_send_email_valid_email_verified_user(self):
        query = self.make_query("bar@email.com")
        executed = self.make_request(query=query)
        assert executed["success"]
        assert not executed["errors"]

    def test_send_to_secondary_email(self):
        query = self.make_query("secondary@email.com")
        executed = self.make_request(query=query)
        assert executed["success"]
        assert not executed["errors"]

    @mock.patch(
        "gqlauth.models.UserStatus.send_password_reset_email",
        mock.MagicMock(side_effect=SMTPException),
    )
    def test_send_email_fail_to_send_email(self):
        mock
        query = self.make_query("bar@email.com")
        executed = self.make_request(query=query)
        assert not executed["success"]
        self.assertEqual(executed["errors"]["nonFieldErrors"], Messages.EMAIL_FAIL)


class SendPasswordResetEmailTestCase(SendPasswordResetEmailTestCaseMixin, DefaultTestCase):
    def make_query(self, email):
        return """
        mutation {
        sendPasswordResetEmail(email: "%s")
            { success, errors }
        }
        """ % (
            email
        )


class SendPasswordResetEmailRelayTestCase(SendPasswordResetEmailTestCaseMixin, RelayTestCase):
    def make_query(self, email):
        return """
        mutation {
        sendPasswordResetEmail(input:{ email: "%s"})
            { success, errors  }
        }
        """ % (
            email
        )
