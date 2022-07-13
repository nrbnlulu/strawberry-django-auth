from gqlauth.constants import Messages
from gqlauth.signals import user_verified
from gqlauth.utils import get_token

from .testCases import DefaultTestCase, RelayTestCase


class VerifyAccountCaseMixin:
    def setUp(self):
        unverified_user = self.register_user(email="foo@email.com", username="foo", verified=False)
        self.user2 = self.register_user(email="bar@email.com", username="bar", verified=True)

    def test_verify_user(self):
        signal_received = False

        def receive_signal(sender, user, signal):
            self.assertEqual(user.id, unverified_user.id)
            nonlocal signal_received
            signal_received = True

        user_verified.connect(receive_signal)
        token = get_token(unverified_user, "activation")
        executed = self.make_request(self.verify_query(token))
        assert executed["success"]
        self.assertFalse(executed["errors"])
        self.assertTrue(signal_received)

    def test_verified_user(self):
        token = get_token(self.user2, "activation")
        executed = self.make_request(self.verify_query(token))
        assert not executed["success"]
        self.assertEqual(executed["errors"]["nonFieldErrors"], Messages.ALREADY_VERIFIED)

    def test_invalid_token(self):
        executed = self.make_request(self.verify_query("faketoken"))
        assert not executed["success"]
        self.assertEqual(executed["errors"]["nonFieldErrors"], Messages.INVALID_TOKEN)

    def test_other_token(self):
        token = get_token(self.user2, "password_reset")
        executed = self.make_request(self.verify_query(token))
        assert not executed["success"]
        self.assertEqual(executed["errors"]["nonFieldErrors"], Messages.INVALID_TOKEN)


class VerifyAccountCase(VerifyAccountCaseMixin, DefaultTestCase):
    def verify_query(self, token):
        return """
        mutation {
            verifyAccount(token: "%s")
                { success, errors }
            }
        """ % (
            token
        )


class VerifyAccountRelayTestCase(VerifyAccountCaseMixin, RelayTestCase):
    def verify_query(self, token):
        return """
        mutation {
        verifyAccount(input:{ token: "%s"})
            { success, errors  }
        }
        """ % (
            token
        )
