from gqlauth.utils import get_token

from .testCases import DefaultTestCase, RelayTestCase


class VerifySecondaryEmailCaseMixin:
    def setUp(self):
        self.user = self.register_user(email="bar@email.com", username="bar", verified=True)
        self.user2 = self.register_user(email="foo@email.com", username="foo", verified=True)

    def test_verify_secondary_email(self):
        token = get_token(
            self.user,
            "activation_secondary_email",
            secondary_email="new_email@email.com",
        )
        executed = self.make_request(self.verify_query(token))
        assert executed["success"]
        self.assertFalse(executed["errors"])

    def test_invalid_token(self):
        executed = self.make_request(self.verify_query("faketoken"))
        assert not executed["success"]
        self.assertTrue(executed["errors"])

    def test_email_in_use(self):
        token = get_token(self.user, "activation_secondary_email", secondary_email="foo@email.com")
        executed = self.make_request(self.verify_query(token))
        assert not executed["success"]
        self.assertTrue(executed["errors"])


class VerifySecondaryEmailCase(VerifySecondaryEmailCaseMixin, DefaultTestCase):
    def verify_query(self, token):
        return """
        mutation {
            verifySecondaryEmail(token: "%s")
                { success, errors }
            }
        """ % (
            token
        )


class VerifySecondaryEmailRelayTestCase(VerifySecondaryEmailCaseMixin, RelayTestCase):
    def verify_query(self, token):
        return """
        mutation {
        verifySecondaryEmail(input:{ token: "%s"})
            { success, errors  }
        }
        """ % (
            token
        )
