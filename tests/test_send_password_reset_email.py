from smtplib import SMTPException
from unittest import mock

from gqlauth.constants import Messages

from .testCases import ArgTestCase, RelayTestCase, UserType, AsyncArgTestCase, AsyncRelayTestCase


class SendPasswordResetEmailTestCaseMixin:
    def _arg_query(self, user: UserType):
        return """
        mutation {
        sendPasswordResetEmail(email: "%s")
            { success, errors }
        }
        """ % (
            user.email
        )

    def _relay_query(self, user: UserType):
        return """
        mutation {
        sendPasswordResetEmail(input:{ email: "%s"})
            { success, errors  }
        }
        """ % (
            user.email
        )

    def test_send_email_invalid_email(self, db_verified_user_status):
        """
        invalid email should be successful request.
        (due to security measures)
        """
        user = db_verified_user_status.user
        user.email = "invalid@email.com"
        query = self.make_query(user)
        executed = self.make_request(query=query)
        assert executed["success"]
        assert not executed["errors"]

    def test_invalid_form(self, db_verified_user_status):
        user = db_verified_user_status.user
        user.email = "invalid * form@email.com"
        query = self.make_query(user)
        executed = self.make_request(query=query)
        assert not executed["success"]
        assert executed["errors"]["email"]

    def test_send_email_valid_email_verified_user(self, db_verified_user_status):
        query = self.make_query(db_verified_user_status.user)
        executed = self.make_request(query=query)
        assert executed["success"]
        assert not executed["errors"]

    def test_send_to_secondary_email(self, db_verified_user_status):
        user = db_verified_user_status.user
        user.email = "foo@bar.com"
        user.obj.status.secondary_email = user.email
        user.obj.status.save()

        query = self.make_query(user)
        executed = self.make_request(query=query)
        assert executed["success"]
        assert not executed["errors"]

    @mock.patch(
        "gqlauth.models.UserStatus.send_password_reset_email",
        mock.MagicMock(side_effect=SMTPException),
    )
    def test_send_email_fail_to_send_email(self, db_verified_user_status):
        query = self.make_query(db_verified_user_status.user)
        executed = self.make_request(query=query)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.EMAIL_FAIL


class TestArgSendPasswordResetEmail(SendPasswordResetEmailTestCaseMixin, ArgTestCase):
    ...


class TestRelaySendPasswordResetEmail(SendPasswordResetEmailTestCaseMixin, RelayTestCase):
    ...

class TestAsyncArgSendPasswordResetEmail(SendPasswordResetEmailTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelaySendPasswordResetEmail(SendPasswordResetEmailTestCaseMixin, AsyncRelayTestCase):
    ...
