from gqlauth.core.constants import Messages
from gqlauth.models import RefreshToken

from .testCases import (
    AbstractTestCase,
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
)


class RefreshTokenTestCaseMixin(AbstractTestCase):
    def _arg_query(self, token: str, revoke="false"):
        return """
        mutation MyMutation {{
          refreshToken(refreshToken: "{}", revokeRefreshToken: {}) {{
            errors
            token {{
              token
            }}
            success
            refreshToken {{
              token
              revoked
              isExpired
              expiresAt
              created
            }}
          }}
        }}
        """.format(
            token, revoke
        )

    def _relay_query(self, token: str, revoke="false"):
        return """
        mutation MyMutation {{
          refreshToken(input: {{refreshToken: "{}", revokeRefreshToken: {}}}) {{
            errors
            token {{
              token
            }}
            success
            refreshToken {{
              token
              revoked
              isExpired
              expiresAt
              created
            }}
          }}
        }}
        """.format(
            token, revoke
        )

    def test_refresh_token(self, db_verified_user_status):
        query = self.login_query(user_status=db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert (token := executed["refreshToken"]["token"])
        query = self.make_query(token)
        executed = self.make_request(query=query)
        assert executed["success"]
        assert executed["token"]["token"]
        assert executed["refreshToken"]["token"]
        assert not executed["errors"]

    def test_invalid_token(self):
        query = self.make_query("invalid_token")
        executed = self.make_request(query=query, no_login_query=True)
        assert not executed["success"]
        assert not executed["refreshToken"]
        assert executed["errors"]

    def test_revoke_refresh_token(self, db_verified_user_status):
        query = self.login_query(user_status=db_verified_user_status)
        executed = self.make_request(query=query, no_login_query=True)
        assert (token := executed["refreshToken"]["token"])
        prev = RefreshToken.objects.get(token=token)
        assert not prev.is_expired_()
        query = self.make_query(token, "true")
        self.make_request(query=query)
        prev.refresh_from_db()
        assert prev.revoked
        assert prev.is_expired_()
        # try to get a new token with the revoked token
        executed = self.make_request(query=query)
        assert executed["errors"]["nonFieldErrors"] == Messages.EXPIRED_TOKEN


class TestArgRefreshToken(RefreshTokenTestCaseMixin, ArgTestCase):
    ...


class TestRelayRefreshToken(RefreshTokenTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgRefreshToken(RefreshTokenTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayRefreshToken(RefreshTokenTestCaseMixin, AsyncRelayTestCase):
    ...
