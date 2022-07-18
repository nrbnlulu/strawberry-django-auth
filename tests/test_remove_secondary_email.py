from .testCases import ArgTestCase, RelayTestCase


class RemoveSecondaryEmailCaseMixin:
    def setUp(self):
        self.user = self.register_user(
            email="bar@email.com",
            username="bar",
            verified=True,
            secondary_email="secondary@email.com",
        )

    def test_remove_email(self):
        executed = make_request(query=self.query(), user={"user": self.user})
        assert executed["success"]
        assert not executed["errors"]
        self.user.refresh_from_db()
        self.assertEqual(self.user.status.secondary_email, None)


class RemoveSecondaryEmailCase(RemoveSecondaryEmailCaseMixin, ArgTestCase):
    def query(self, password=None):
        return """
        mutation {
            removeSecondaryEmail(password: "%s")
                { success, errors }
            }
        """ % (
            password or self.DEFAULT_PASSWORD
        )


class RemoveSecondaryEmailRelayTestCase(RemoveSecondaryEmailCaseMixin, RelayTestCase):
    def query(self, password=None):
        return """
        mutation {
        removeSecondaryEmail(input:{ password: "%s"})
            { success, errors  }
        }
        """ % (
            password or self.DEFAULT_PASSWORD
        )
