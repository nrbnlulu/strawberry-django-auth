from gqlauth.constants import Messages

from .testCases import (
    AsyncDefaultTestCase,
    AsyncRelayTestCase,
    DefaultTestCase,
    RelayTestCase,
)


class ArchiveAccountTestCaseMixin:
    def test_not_authenticated(self):
        """
        try to archive not authenticated
        """
        query = self.make_query()
        executed = self.make_request(query)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.UNAUTHENTICATED

    def test_invalid_password(self, verified_user):
        """
        try to archive account with invalid password
        """
        variables = {"user": verified_user}
        query = self.make_query(password="123")
        executed = self.make_request(query, variables)
        assert not executed["success"]
        assert executed["errors"]["password"] == Messages.INVALID_PASSWORD

    def test_valid_password(self, verified_user):
        """
        try to archive account
        """
        query = self.make_query()
        variables = {"user": verified_user}
        assert not verified_user.status.archived
        executed = self.make_request(query, variables=variables)
        assert executed["success"]
        assert not executed["errors"]
        verified_user.refresh_from_db()
        assert verified_user.status.archived

    def test_revoke_refresh_tokens_on_archive_account(self, verified_user, verified_tokens):
        """
        when archive account, all refresh tokens should be revoked
        """
        verified_user.refresh_from_db()
        refresh_tokens = verified_user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert not token.revoked

        query = self.make_query()
        variables = {"user": verified_user}
        assert not verified_user.status.archived
        executed = self.make_request(query, variables)
        assert executed["success"]
        assert not executed["errors"]
        verified_user.refresh_from_db()
        assert verified_user.status.archived

        verified_user.refresh_from_db()
        refresh_tokens = verified_user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert token.revoked

    def test_not_verified_user(self, unverified_user):
        """
        try to archive account
        """
        query = self.make_query(self.wrong_password)
        variables = {"user": unverified_user}
        assert not unverified_user.status.archived
        executed = self.make_request(query, variables)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.NOT_VERIFIED
        assert not unverified_user.status.archived


class TestArchiveAccountTestCase(ArchiveAccountTestCaseMixin, DefaultTestCase):
    def make_query(self, password=None):
        return """
            mutation {{
              archiveAccount(password: "{}") {{
                success, errors
              }}
            }}
        """.format(
            password or self.default_password,
        )


class TestArchiveAccountRelayTestCase(ArchiveAccountTestCaseMixin, RelayTestCase):
    def make_query(self, password=None):
        return """
            mutation {{
              archiveAccount(input: {{ password: "{}"}}) {{
                success, errors
              }}
            }}
        """.format(
            password or self.default_password,
        )


class TestAsyncArchiveAccountTestCase(ArchiveAccountTestCaseMixin, AsyncDefaultTestCase):
    def make_query(self, password=None):
        return """
            mutation {{
              archiveAccount(password: "{}") {{
                success, errors
              }}
            }}
        """.format(
            password or self.default_password,
        )


class TestAsyncArchiveAccountRelayTestCase(ArchiveAccountTestCaseMixin, AsyncRelayTestCase):
    def make_query(self, password=None):
        return """
            mutation {{
              archiveAccount(input: {{ password: "{}"}}) {{
                success, errors
              }}
            }}
        """.format(
            password or self.default_password,
        )
