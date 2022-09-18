from .testCases import (
    AbstractTestCase,
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
)


class RevokeTokenTestCaseMixin(AbstractTestCase):
    @staticmethod
    def _arg_query(token):
        return """
        mutation MyMutation {
          revokeToken(refreshToken: "%s") {
            errors
            success
            refreshToken {
              created
              expiresAt
              isExpired
              revoked
              token
            }
          }
        }
        """ % (
            token
        )

    @staticmethod
    def _relay_query(token):
        return """
        mutation MyMutation {
          revokeToken(input: {refreshToken: "%s"}) {
            errors
            success
            refreshToken {
              created
              expiresAt
              isExpired
              revoked
              token
            }
          }
        }
        """ % (
            token
        )

    def test_revoke_token(self, db_verified_user_status):
        query = self.login_query(user_status=db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert executed["refreshToken"]["token"]

        query = self.make_query(executed["refreshToken"]["token"])
        executed = self.make_request(query=query)
        assert executed["success"]
        assert executed["refreshToken"]["revoked"]
        assert executed["refreshToken"]["isExpired"]
        assert not executed["errors"]

    def test_invalid_token(self):
        query = self.make_query("invalid_token")
        executed = self.make_request(query=query)
        assert not executed["success"]
        assert executed["errors"]
        assert not executed["refreshToken"]


class TestArgRevokeToken(RevokeTokenTestCaseMixin, ArgTestCase):
    ...


class TestRelayVerifyToken(RevokeTokenTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgRevokeToken(RevokeTokenTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayVerifyToken(RevokeTokenTestCaseMixin, AsyncRelayTestCase):
    ...
