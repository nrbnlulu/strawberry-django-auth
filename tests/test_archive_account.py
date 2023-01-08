from gqlauth.core.types_ import GQLAuthErrors
from gqlauth.models import RefreshToken

from .testCases import AbstractTestCase, UserStatusType


class TestArchiveAccountTestCaseMixin(AbstractTestCase):
    def make_query(self, user_status_type: UserStatusType) -> str:
        return """
                mutation {
                  archiveAccount(password: "%s"){
                      success
                      errors

                  }
              }
                """ % (
            user_status_type.user.password
        )

    def test_not_verified(self, unverified_schema):
        """
        try to archive not verified user
        """
        res = unverified_schema.execute(self.make_query(unverified_schema.us_type))
        assert res.errors[0].message == GQLAuthErrors.NOT_VERIFIED.value

    def test_invalid_password(self, verified_schema, wrong_pass_ver_user_status_type):
        """
        try to archive account with invalid password
        """

        res = verified_schema.execute(self.make_query(wrong_pass_ver_user_status_type))
        assert res.data["archiveAccount"] == {
            "success": False,
            "errors": {"password": [{"message": "Invalid password.", "code": "invalid_password"}]},
        }

    def test_valid_password(self, verified_schema):
        """
        try to archive account
        """
        user = verified_schema.us_type.user.obj
        assert not user.status.archived
        res = verified_schema.execute(self.make_query(verified_schema.us_type))
        assert res.data["archiveAccount"] == {"errors": None, "success": True}
        user.refresh_from_db()
        assert user.status.archived

    def test_revoke_refresh_tokens_on_archive_account(self, verified_schema):
        """
        when archive account, all refresh tokens should be revoked
        """
        user = verified_schema.us_type.user.obj
        user.refresh_from_db()
        RefreshToken.from_user(user)
        refresh_tokens = user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert not token.revoked

        res = verified_schema.execute(self.make_query(verified_schema.us_type))

        assert res.data["archiveAccount"] == {"errors": None, "success": True}
        user.refresh_from_db()
        assert user.status.archived
        refresh_tokens = user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert token.revoked
