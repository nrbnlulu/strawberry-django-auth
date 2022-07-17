import pytest
from django.core.exceptions import ObjectDoesNotExist
from pytest import mark

from gqlauth.constants import Messages
from gqlauth.settings import gqlauth_settings as app_settings

from .testCases import DefaultTestCase, RelayTestCase, UserStatusType


class DeleteAccountTestCaseMixin:

    def _arg_query(self, user_status: UserStatusType):
        return """
            mutation {{
              deleteAccount(password: "{}") {{
                success, errors
              }}
            }}
        """.format(
           user_status.user.password
        )

    def _relay_query(self, user_status: UserStatusType):
        return """
            mutation {{
              deleteAccount(input: {{ password: "{}"}}) {{
                success, errors
              }}
            }}
        """.format(
           user_status.user.password
        )

    def test_not_authenticated(self, db_verified_user_status):
        """
        try to archive not authenticated
        """
        query = self.make_query(db_verified_user_status)
        db_verified_user_status.user.password = self.WRONG_PASSWORD
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.UNAUTHENTICATED

    def test_invalid_password(self, db_verified_user_status, wrong_pass_ver_user_status_type):
        query = self.make_query(wrong_pass_ver_user_status_type)
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert not executed["success"]
        assert executed["errors"]["password"] == Messages.INVALID_PASSWORD

    def test_not_verified_user(
            self,
            allow_login_not_verified,
            db_unverified_user_status,
            wrong_pass_unverified_user_status_type
    ):
        query = self.make_query(wrong_pass_unverified_user_status_type)
        user = db_unverified_user_status.user.obj
        assert user.is_active
        executed = self.make_request(query=query, user_status=db_unverified_user_status)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.NOT_VERIFIED
        assert user.is_active

    @mark.settings_b
    def test_valid_password_permanently_delete(self, db_verified_user_status):
        query = self.make_query(db_verified_user_status)
        user = db_verified_user_status.user.obj
        assert user.is_active
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert executed["success"]
        assert not executed["errors"]
        with pytest.raises(ObjectDoesNotExist):
            user.refresh_from_db()



class TestArgDeleteAccount(DeleteAccountTestCaseMixin, DefaultTestCase):
    ...


class TestRelayDeleteAccountRelay(DeleteAccountTestCaseMixin, RelayTestCase):
    ...