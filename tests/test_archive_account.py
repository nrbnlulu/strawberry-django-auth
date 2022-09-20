from gqlauth.core.types_ import GQLAuthErrors

from .testCases import (
    AbstractTestCase,
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
    UserStatusType,
)


class ArchiveAccountTestCaseMixin(AbstractTestCase):
    def _arg_query(self, user_status_type: UserStatusType):
        return """
        mutation MyMutation {
          authEntry {
            ... on GQLAuthError {
              code
              message
            }
            ... on AuthMutation {
              archiveAccount(password: \"%s\") {
                ... on MutationNormalOutput {
                  success
                  errors
                }
                ... on GQLAuthError {
                  code
                  message
                }
              }
            }
          }
        }
        """ % (
            user_status_type.user.password
        )

    def _relay_query(self, user_status_type: UserStatusType):
        return """
        mutation MyMutation {
          authEntry {
            ... on GQLAuthError {
              code
              message
            }
            ... on AuthMutation {
              archiveAccount(input: {password: \"%s\"}) {
                ... on MutationNormalOutput {
                  success
                  errors
                }
                ... on GQLAuthError {
                  code
                  message
                }
              }
            }
          }
        }
        """ % (
            user_status_type.user.password
        )

    def test_not_authenticated(self, db_verified_user_status):
        """
        try to archive not authenticated user
        """
        # pass a user verified user with good password.
        query = self.make_query(db_verified_user_status)
        db_verified_user_status.user.password = self.WRONG_PASSWORD
        # execute query with bad user password.
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert executed["message"] == GQLAuthErrors.INVALID_TOKEN.value

    def test_invalid_password(self, db_verified_user_status, wrong_pass_ver_user_status_type):
        """
        try to archive account with invalid password
        """

        query = self.make_query(wrong_pass_ver_user_status_type)
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert executed["archiveAccount"] == {
            "success": False,
            "errors": {"password": [{"message": "Invalid password.", "code": "invalid_password"}]},
        }

    def test_valid_password(self, db_verified_user_status):
        """
        try to archive account
        """
        query = self.make_query(db_verified_user_status)
        assert not db_verified_user_status.user.obj.status.archived
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert executed["archiveAccount"] == {"errors": None, "success": True}
        db_verified_user_status.user.obj.refresh_from_db()
        assert db_verified_user_status.user.obj.status.archived

    def test_revoke_refresh_tokens_on_archive_account(self, db_verified_user_status):
        """
        when archive account, all refresh tokens should be revoked
        """
        self.get_tokens(db_verified_user_status)
        user = db_verified_user_status.user.obj
        user.refresh_from_db()
        refresh_tokens = user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert not token.revoked

        query = self.make_query(db_verified_user_status)
        assert not user.status.archived
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert executed["archiveAccount"] == {"errors": None, "success": True}
        user.refresh_from_db()
        assert user.status.archived
        refresh_tokens = user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert token.revoked

    def test_not_verified_user(
        self,
        allow_login_not_verified,
        db_unverified_user_status,
        wrong_pass_unverified_user_status_type,
    ):
        """
        try to archive account
        """
        user = db_unverified_user_status.user.obj
        query = self.make_query(wrong_pass_unverified_user_status_type)
        assert not user.status.archived
        executed = self.make_request(query=query, user_status=db_unverified_user_status)
        assert executed["archiveAccount"]["message"] == GQLAuthErrors.NOT_VERIFIED.value
        assert not user.status.archived


class TestArgArchiveAccount(ArchiveAccountTestCaseMixin, ArgTestCase):
    ...


class TestRelayArchiveAccount(ArchiveAccountTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgArchiveAccount(ArchiveAccountTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayArchiveAccount(ArchiveAccountTestCaseMixin, AsyncRelayTestCase):
    ...
