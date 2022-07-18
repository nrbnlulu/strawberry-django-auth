from gqlauth.constants import Messages
from gqlauth.signals import user_verified
from gqlauth.utils import get_token

from .testCases import ArgTestCase, RelayTestCase, AsyncArgTestCase, AsyncRelayTestCase


class VerifyAccountCaseMixin:
    def _arg_query(self, token):
        return """
        mutation {
            verifyAccount(token: "%s")
                { success, errors }
            }
        """ % (
            token
        )

    def _relay_query(self, token):
        return """
        mutation {
        verifyAccount(input:{ token: "%s"})
            { success, errors  }
        }
        """ % (
            token
        )

    def test_verify_user(self, db_unverified_user_status):
        user_status = db_unverified_user_status
        user_obj = user_status.user.obj
        assert not user_obj.status.verified
        signal_received = False

        def receive_signal(sender, user, signal):
            assert user.id == user_obj.id
            nonlocal signal_received
            signal_received = True

        user_verified.connect(receive_signal)
        token = get_token(user_obj, "activation")
        executed = self.make_request(self.make_query(token))
        assert executed["success"]
        assert not executed["errors"]
        assert signal_received
        user_obj.refresh_from_db()
        assert user_obj.status.verified

    def test_verified_user(self, db_verified_user_status):
        user_status = db_verified_user_status
        user_obj = user_status.user.obj
        token = get_token(user_obj, "activation")
        executed = self.make_request(self.make_query(token))
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.ALREADY_VERIFIED

    def test_invalid_token(self):
        executed = self.make_request(self.make_query("faketoken"))
        assert not executed["success"]
        executed["errors"]["nonFieldErrors"] == Messages.INVALID_TOKEN

    def test_other_token(self, db_unverified_user_status):
        user_status = db_unverified_user_status
        user_obj = user_status.user.obj
        token = get_token(user_obj, "password_reset")
        executed = self.make_request(self.make_query(token))
        assert not executed["success"]
        executed["errors"]["nonFieldErrors"] == Messages.INVALID_TOKEN


class TestArgVerifyAccount(VerifyAccountCaseMixin, ArgTestCase):
    ...


class TestRelayVerifyAccountRelay(VerifyAccountCaseMixin, RelayTestCase):
    ...

class TestAsyncArgVerifyAccount(VerifyAccountCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayVerifyAccountRelay(VerifyAccountCaseMixin, AsyncRelayTestCase):
    ...
