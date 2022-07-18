from .testCases import DefaultTestCase, RelayTestCase, AsyncDefaultTestCase, AsyncRelayTestCase


class RefreshTokenTestCaseMixin:
    def _arg_query(self, token: str):
        return """
        mutation {
        refreshToken(refreshToken: "%s" )
            {
            refreshPayload{
              payload{
                exp
                origIat
                username
              }
              token
              refreshToken
              refreshExpiresIn
            }
            errors
                success
          }
        }
        """ % (
            token
        )

    def _relay_query(self, token: str):
        return """
        mutation {
        refreshToken(input: {refreshToken: "%s"} )
            {
            refreshPayload{
              payload{
                exp
                origIat
                username
              }
              token
              refreshToken
              refreshExpiresIn
            }
            errors
            success
          }
        }
        """ % (
            token
        )

    def test_refresh_token(self, db_verified_user_status):
        query = self.login_query(user_status=db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert (token := executed["obtainPayload"]["refreshToken"])
        query = self.make_query(token)
        executed = self.make_request(query=query)
        assert executed["success"]
        assert executed["refreshPayload"]["refreshToken"]
        assert executed["refreshPayload"]["payload"]
        assert not executed["errors"]

    def test_invalid_token(self):
        query = self.make_query("invalid_token")
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert not executed["refreshPayload"]
        assert executed["errors"]


class TestArgRefreshToken(RefreshTokenTestCaseMixin, DefaultTestCase):
    ...


class TestRelayRefreshToken(RefreshTokenTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgRefreshToken(RefreshTokenTestCaseMixin, AsyncDefaultTestCase):
    ...


class TestAsyncRelayRefreshToken(RefreshTokenTestCaseMixin, AsyncRelayTestCase):
    ...
