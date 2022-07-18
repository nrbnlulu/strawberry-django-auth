from .testCases import ArgTestCase, RelayTestCase, UserType, AsyncArgTestCase, \
    AsyncRelayTestCase


class RemoveSecondaryEmailCaseMixin:
    def _arg_query(self, user: UserType):
        return """
        mutation {
            removeSecondaryEmail(password: "%s")
                { success, errors }
            }
        """ % (
                user.password
        )
    def _relay_query(self, user: UserType):
        return """
        mutation {
        removeSecondaryEmail(input:{ password: "%s"})
            { success, errors  }
        }
        """ % (
                user.password
        )

    def test_remove_email(self, db_verified_user_status):
        user = db_verified_user_status.user.obj
        user.status.secondary_email = "secondary@email.com"
        user.status.save()
        executed = self.make_request(query=self.make_query(db_verified_user_status.user), user_status=db_verified_user_status)
        assert executed["success"]
        assert not executed["errors"]
        user.refresh_from_db()
        assert not user.status.secondary_email


class TestArgRemoveSecondaryEmail(RemoveSecondaryEmailCaseMixin, ArgTestCase):
    ...

class TestRelayRemoveSecondaryEmail(RemoveSecondaryEmailCaseMixin, RelayTestCase):
    ...

class TestArgRemoveSecondaryEmail(RemoveSecondaryEmailCaseMixin, AsyncArgTestCase):
    ...

class TestRelayRemoveSecondaryEmail(RemoveSecondaryEmailCaseMixin, AsyncRelayTestCase):
    ...
