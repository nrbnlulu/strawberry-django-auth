from gqlauth.constants import Messages

from .testCases import (
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
    UserType,
)


class SwapEmailsCaseMixin:
    def _arg_query(self, user: UserType):
        return """
        mutation {
            swapEmails(password: "%s")
                { success, errors }
            }
        """ % (
            user.password
        )

    def _relay_query(self, user: UserType):
        return """
        mutation {
        swapEmails(input:{ password: "%s"})
            { success, errors  }
        }
        """ % (
            user.password
        )

    def test_swap_emails(self, db_verified_with_secondary_email):
        user = db_verified_with_secondary_email.user
        user_obj = user.obj
        prev_secondary_email = user_obj.status.secondary_email
        executed = self.make_request(
            query=self.make_query(user), user_status=db_verified_with_secondary_email
        )
        assert executed["success"]
        assert not executed["errors"]
        user_obj.refresh_from_db()
        assert user_obj.email == prev_secondary_email
        assert user_obj.status.secondary_email == user.email

    def test_swap_emails_without_secondary_email(self, db_verified_user_status):
        executed = self.make_request(
            query=self.make_query(db_verified_user_status.user), user_status=db_verified_user_status
        )
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.SECONDARY_EMAIL_REQUIRED


class TestArgSwapEmails(SwapEmailsCaseMixin, ArgTestCase):
    ...


class TestRelaySwapEmail(SwapEmailsCaseMixin, RelayTestCase):
    ...


class TestAsyncArgSwapEmails(SwapEmailsCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelaySwapEmail(SwapEmailsCaseMixin, AsyncRelayTestCase):
    ...
