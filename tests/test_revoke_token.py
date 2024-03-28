def _arg_query(token: str):
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
    """ % (token)


def test_revoke_token(db_verified_user_status, anonymous_schema):
    query = _arg_query(db_verified_user_status.generate_refresh_token().token)
    res = anonymous_schema.execute(query=query)
    assert not res.errors
    res = res.data["revokeToken"]
    assert res["success"]
    assert res["refreshToken"]["revoked"]
    assert res["refreshToken"]["isExpired"]
    assert not res["errors"]


def test_invalid_token(db_verified_user_status, anonymous_schema):
    query = _arg_query("invalid_token")
    res = anonymous_schema.execute(query=query)
    assert not res.errors
    res = res.data["revokeToken"]

    assert not res["success"]
    assert res["errors"]
    assert not res["refreshToken"]
