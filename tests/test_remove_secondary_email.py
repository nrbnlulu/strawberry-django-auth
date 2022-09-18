from gqlauth.core.constants import Messages

from .testCases import (
    AbstractTestCase,
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
    UserType,
)


class RemoveSecondaryEmailCaseMixin(AbstractTestCase):
    def _arg_query(self, user: UserType):
        return """
        mutation {
          authEntry {
            node {
              removeSecondaryEmail(password: "%s") {
                errors
                success
              }
            }
            error{
              code
              message
            }
            success
          }
        }
        """ % (
            user.password
        )

    def _relay_query(self, user: UserType):
        return """
        mutation {
          authEntry {
            node {
              removeSecondaryEmail(input: {password: "%s"}) {
                errors
                success
              }
            }
            error{
              code
              message
            }
            success
          }
        }
                """ % (
            user.password
        )

    def test_remove_email(self, db_verified_with_secondary_email):
        user = db_verified_with_secondary_email.user.obj
        user.status.save()
        executed = self.make_request(
            query=self.make_query(db_verified_with_secondary_email.user),
            user_status=db_verified_with_secondary_email,
        )
        assert executed["node"]["removeSecondaryEmail"] == {"errors": None, "success": True}
        user.refresh_from_db()
        assert not user.status.secondary_email

    def test_remove_email_fails(self, db_verified_with_secondary_email):
        user = db_verified_with_secondary_email.user.obj
        user.status.remove_secondary_email()
        executed = self.make_request(
            query=self.make_query(db_verified_with_secondary_email.user),
            user_status=db_verified_with_secondary_email,
        )
        assert executed["node"]["removeSecondaryEmail"] == {
            "errors": {"nonFieldErrors": Messages.SECONDARY_EMAIL_REQUIRED},
            "success": False,
        }


class TestArgRemoveSecondaryEmail(RemoveSecondaryEmailCaseMixin, ArgTestCase):
    ...


class TestRelayRemoveSecondaryEmail(RemoveSecondaryEmailCaseMixin, RelayTestCase):
    ...


class TestAsyncArgRemoveSecondaryEmail(RemoveSecondaryEmailCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayRemoveSecondaryEmail(RemoveSecondaryEmailCaseMixin, AsyncRelayTestCase):
    ...
