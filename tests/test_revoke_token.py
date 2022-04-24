from unittest import skip

from django.contrib.auth import get_user_model
from django.utils import timezone

from .testCases import RelayTestCase, DefaultTestCase
from gqlauth.constants import Messages


# GRAPHQL_JWT = {
#     "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
# }


class RevokeTokenTestCaseMixin:
    def setUp(self):
        self.user1 = self.register_user(email="foo@email.com", username="foo_username")
        self.user1.status.verified = True
        self.user1.status.save()
        self.user1.refresh_from_db()
        super().setUp()

    def test_revoke_token(self):
        query = self.login_query(username='foo_username')
        executed = self.make_request(query)
        self.assertTrue(executed['obtainPayload']["refreshToken"])

        query = self.get_revoke_query(executed['obtainPayload']["refreshToken"])
        executed = self.make_request(query)
        self.assertTrue(executed["success"])
        self.assertTrue(executed['revokePayload']["revoked"])
        self.assertFalse(executed["errors"])

    def test_invalid_token(self):
        query = self.get_revoke_query("invalid_token")
        executed = self.make_request(query)
        self.assertFalse(executed["success"])
        self.assertTrue(executed["errors"])
        self.assertFalse(executed['revokePayload'])


class RevokeTokenTestCase(RevokeTokenTestCaseMixin, DefaultTestCase):
    def get_revoke_query(self, token):
        return """
        mutation {
        revokeToken(refreshToken: "%s" )
            {
        success
        errors
        revokePayload{
          revoked
        }
      }
    }
        """ % (
            token
        )


class VerifyTokenRelayTestCase(RevokeTokenTestCaseMixin, RelayTestCase):
    def get_revoke_query(self, token):
        return """
        mutation {
        revokeToken(input: {refreshToken: "%s"} )
           {
        success
        errors
        revokePayload{
          revoked
        }
      }
    }
        """ % (
            token
        )
