from gqlauth.core.types_ import GQLAuthErrors
from gqlauth.models import RefreshToken
from tests.conftest import UserStatusType


def make_query(user_status_type: UserStatusType) -> str:
    return """
            mutation {
              archiveAccount(password: "%s"){
                  success
                  errors

              }
          }
            """ % (user_status_type.user.password)


def test_not_verified(unverified_schema):
    """Try to archive not verified user."""
    res = unverified_schema.execute(make_query(unverified_schema.us_type))
    assert res.errors[0].message == GQLAuthErrors.NOT_VERIFIED.value


def test_invalid_password(verified_schema, wrong_pass_ver_user_status_type):
    """Try to archive account with invalid password."""

    res = verified_schema.execute(make_query(wrong_pass_ver_user_status_type))
    assert res.data["archiveAccount"] == {
        "success": False,
        "errors": {
            "password": [{"message": "Invalid password.", "code": "invalid_password"}]
        },
    }


def test_valid_password(verified_schema):
    """Try to archive account."""
    user = verified_schema.us_type.user.obj
    assert not user.status.archived
    res = verified_schema.execute(make_query(verified_schema.us_type))
    assert res.data["archiveAccount"] == {"errors": None, "success": True}
    user.refresh_from_db()
    assert user.status.archived


def test_revoke_refresh_tokens_on_archive_account(verified_schema):
    """When archive account, all refresh tokens should be revoked."""
    user = verified_schema.us_type.user.obj
    user.refresh_from_db()
    RefreshToken.from_user(user)
    refresh_tokens = user.refresh_tokens.all()
    assert refresh_tokens
    for token in refresh_tokens:
        assert not token.revoked

    res = verified_schema.execute(make_query(verified_schema.us_type))

    assert res.data["archiveAccount"] == {"errors": None, "success": True}
    user.refresh_from_db()
    assert user.status.archived
    refresh_tokens = user.refresh_tokens.all()
    assert refresh_tokens
    for token in refresh_tokens:
        assert token.revoked
