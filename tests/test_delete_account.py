from django.core.exceptions import ObjectDoesNotExist
import pytest
from pytest import mark

from gqlauth.core.constants import Messages
from gqlauth.core.types_ import GqlAuthError

from .testCases import AbstractTestCase, ArgTestCase, RelayTestCase, UserStatusType


class DeleteAccountTestCaseMixin(AbstractTestCase):
    @staticmethod
    def _arg_query(user_status: UserStatusType):
        return """
        mutation MyMutation {
          authEntry {
            node {
              deleteAccount(password: "%s") {
                error {
                  code
                  message
                }
                success
                node {
                  errors
                  success
                }
              }
            }
            error {
              code
              message
            }
            success
          }
        }
        """ % (
            user_status.user.password
        )

    @staticmethod
    def _relay_query(user_status: UserStatusType):
        return """
        mutation MyMutation {
          authEntry {
            node {
              deleteAccount(input: {password: "%s"}) {
                error {
                  code
                  message
                }
                success
                node {
                  errors
                  success
                }
              }
            }
            error {
              code
              message
            }
            success
          }
        }
        """ % (
            user_status.user.password
        )

    def test_invalid_password(self, db_verified_user_status, wrong_pass_ver_user_status_type):
        query = self.make_query(wrong_pass_ver_user_status_type)
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert executed["node"]["deleteAccount"]["node"] == {
            "errors": {"password": Messages.INVALID_PASSWORD},
            "success": False,
        }

    def test_not_verified_user(
        self,
        allow_login_not_verified,
        db_unverified_user_status,
        wrong_pass_unverified_user_status_type,
    ):
        query = self.make_query(wrong_pass_unverified_user_status_type)
        user = db_unverified_user_status.user.obj
        assert user.is_active
        executed = self.make_request(query=query, user_status=db_unverified_user_status)
        assert executed["node"]["deleteAccount"] == {
            "error": {
                "code": GqlAuthError.NOT_VERIFIED.name,
                "message": GqlAuthError.NOT_VERIFIED.value,
            },
            "success": False,
            "node": None,
        }
        assert user.is_active

    @mark.settings_b
    def test_valid_password_permanently_delete(self, db_verified_user_status):
        query = self.make_query(db_verified_user_status)
        user = db_verified_user_status.user.obj
        assert user.is_active
        executed = self.make_request(query=query, user_status=db_verified_user_status)["node"][
            "deleteAccount"
        ]["node"]
        assert executed["success"]
        assert not executed["errors"]
        with pytest.raises(ObjectDoesNotExist):
            user.refresh_from_db()


class TestArgDeleteAccount(DeleteAccountTestCaseMixin, ArgTestCase):
    ...


class TestRelayDeleteAccountRelay(DeleteAccountTestCaseMixin, RelayTestCase):
    ...
