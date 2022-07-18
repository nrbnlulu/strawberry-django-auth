from gqlauth.utils import get_token

from .testCases import ArgTestCase, AsyncArgTestCase, AsyncRelayTestCase, RelayTestCase


class VerifySecondaryEmailCaseMixin:
    def _arg_query(self, token):
        return """
        mutation {
            verifySecondaryEmail(token: "%s")
                { success, errors }
            }
        """ % (
            token
        )

    def _relay_query(self, token):
        return """
        mutation {
        verifySecondaryEmail(input:{ token: "%s"})
            { success, errors  }
        }
         """ % (
            token
        )

    def test_verify_secondary_email(self, db_verified_user_status):

        token = get_token(
            db_verified_user_status.user.obj,
            "activation_secondary_email",
            secondary_email="new_email@email.com",
        )
        executed = self.make_request(query=self.make_query(token))
        assert executed["success"]
        assert not executed["errors"]

    def test_invalid_token(self):
        executed = self.make_request(query=self.make_query("fake-token"))
        assert not executed["success"]
        assert executed["errors"]

    def test_email_in_use(self, db_verified_user_status, db_unverified_user_status):
        # just for having an "in use email"
        user_obj2 = db_unverified_user_status.user.obj
        user_obj2.status.verified = True
        user_obj2.save()
        user_obj = db_verified_user_status.user.obj
        token = get_token(user_obj, "activation_secondary_email", secondary_email=user_obj2.email)
        executed = self.make_request(query=self.make_query(token))
        assert not executed["success"]
        assert executed["errors"]


class TestArgVerifySecondaryEmail(VerifySecondaryEmailCaseMixin, ArgTestCase):
    ...


class TestRelayVerifySecondaryEmail(VerifySecondaryEmailCaseMixin, RelayTestCase):
    ...


class TestAsyncArgVerifySecondaryEmail(VerifySecondaryEmailCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayVerifySecondaryEmail(VerifySecondaryEmailCaseMixin, AsyncRelayTestCase):
    ...
