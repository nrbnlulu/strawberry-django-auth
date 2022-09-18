from gqlauth.core.types_ import GqlAuthError

from .testCases import (
    AbstractTestCase,
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
)


class UpdateAccountTestCaseMixin(AbstractTestCase):
    def _arg_query(self, first_name="firstname"):
        return """
        mutation MyMutation {
          authEntry {
            success
            error {
              message
              code
            }
            node {
              updateAccount(firstName: "%s") {
                error {
                  code
                  message
                }
                node {
                  errors
                  success
                }
                success
              }
            }
          }
        }
        """ % (
            first_name
        )

    def _relay_query(self, first_name="firstname"):
        return """
        mutation MyMutation {
          authEntry {
            success
            error {
              message
              code
            }
            node {
              updateAccount(input: {firstName: "%s"}) {
                error {
                  code
                  message
                }
                node {
                  errors
                  success
                }
                success
              }
            }
          }
        }
        """ % (
            first_name
        )

    def test_update_account_unauthenticated(self, db_verified_user_status):
        executed = self.make_request(self.make_query())
        assert executed == {
            "success": False,
            "error": {
                "message": GqlAuthError.INVALID_TOKEN.value,
                "code": GqlAuthError.INVALID_TOKEN.name,
            },
            "node": None,
        }

    def test_update_account_not_verified(self, db_unverified_user_status, allow_login_not_verified):
        executed = self.make_request(self.make_query(), user_status=db_unverified_user_status)
        assert executed["node"]["updateAccount"] == {
            "error": {
                "code": GqlAuthError.NOT_VERIFIED.name,
                "message": GqlAuthError.NOT_VERIFIED.value,
            },
            "node": None,
            "success": False,
        }

    def test_update_account(self, db_verified_user_status):
        user_status = db_verified_user_status
        user = user_status.user.obj
        executed = self.make_request(self.make_query(), user_status=db_verified_user_status)
        assert executed["node"]["updateAccount"] == {
            "error": None,
            "node": {"errors": None, "success": True},
            "success": True,
        }
        user.refresh_from_db()
        assert user.first_name == "firstname"

    def test_invalid_form(self, db_verified_user_status):
        user_status = db_verified_user_status
        user_obj = user_status.user.obj
        user_obj.first_name = user_status.user.username_field
        user_obj.save()
        super_long_string = "10" * 150  # django.auth first_name field is 150 characters or fewer.
        executed = self.make_request(
            self.make_query(first_name=super_long_string), user_status=db_verified_user_status
        )["node"]["updateAccount"]["node"]
        assert not executed["success"]
        assert executed["errors"]["firstName"]
        user_obj.refresh_from_db()
        assert user_obj.first_name == user_status.user.username_field

    # @mark.settings_b
    def test_update_account_list_on_settings(self, db_verified_user_status):
        user_status = db_verified_user_status
        user_obj = user_status.user.obj
        executed = self.make_request(self.make_query(), user_status=db_verified_user_status)[
            "node"
        ]["updateAccount"]["node"]
        assert executed["success"]
        assert not executed["errors"]
        user_obj.refresh_from_db()
        assert user_obj.first_name == "firstname"


class TestArgUpdateAccount(UpdateAccountTestCaseMixin, ArgTestCase):
    ...


class TestRelayUpdateAccount(UpdateAccountTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgUpdateAccount(UpdateAccountTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayUpdateAccount(UpdateAccountTestCaseMixin, AsyncRelayTestCase):
    ...
