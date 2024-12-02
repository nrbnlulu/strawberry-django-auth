from gqlauth.core.constants import Messages


def _arg_query(token: str, revoke="false"):
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
    """.format(token, revoke)


def test_refresh_token(db_verified_user_status, anonymous_schema):
    query = _arg_query(db_verified_user_status.generate_refresh_token().token)
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["refreshToken"]
    assert executed["success"]
    assert executed["token"]["token"]
    assert executed["refreshToken"]["token"]
    assert not executed["errors"]


def test_invalid_token(anonymous_schema, db):
    query = _arg_query("invalid_token")
    res = anonymous_schema.execute(query=query)
    assert not res.errors
    res = res.data["refreshToken"]
    assert not res["success"]
    assert not res["refreshToken"]
    assert res["errors"]


def test_revoke_refresh_token(anonymous_schema, db_verified_user_status):
    refresh = db_verified_user_status.generate_refresh_token()
    assert not refresh.is_expired_()
    query = _arg_query(refresh.token, "true")
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["refreshToken"]
    assert executed["success"]
    assert executed["token"]["token"]
    assert executed["refreshToken"]["token"]
    assert not executed["errors"]

    refresh.refresh_from_db()
    assert refresh.revoked
    assert refresh.is_expired_()
    # try to get a new token with the revoked token
    executed = anonymous_schema.execute(query=query)
    assert (
        executed.data["refreshToken"]["errors"]["nonFieldErrors"]
        == Messages.EXPIRED_TOKEN
    )
