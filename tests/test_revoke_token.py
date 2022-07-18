from .testCases import ArgTestCase, AsyncArgTestCase, AsyncRelayTestCase, RelayTestCase


class RevokeTokenTestCaseMixin:
    def _arg_query(self, token):
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

    def _relay_query(self, token):
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

    def test_revoke_token(self, db_verified_user_status):
        query = self.login_query(user_status=db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["obtainPayload"]["refreshToken"]

        query = self.make_query(executed["obtainPayload"]["refreshToken"])
        executed = self.make_request(query=query)
        assert executed["success"]
        assert executed["revokePayload"]["revoked"]
        assert not executed["errors"]

    def test_invalid_token(self):
        query = self.make_query("invalid_token")
        executed = self.make_request(query=query)
        assert not executed["success"]
        assert executed["errors"]
        assert not executed["revokePayload"]


class TestArgRevokeToken(RevokeTokenTestCaseMixin, ArgTestCase):
    ...


class TestRelayVerifyToken(RevokeTokenTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgRevokeToken(RevokeTokenTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayVerifyToken(RevokeTokenTestCaseMixin, AsyncRelayTestCase):
    ...
