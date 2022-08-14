from gqlauth.core.constants import Messages

from .testCases import ArgTestCase, AsyncArgTestCase, AsyncRelayTestCase, RelayTestCase


class UpdateAccountTestCaseMixin:
    def _arg_query(self, first_name="firstname"):
        return """
        mutation {
            updateAccount(firstName: "%s")
                { success, errors  }
        }
        """ % (
            first_name
        )

    def _relay_query(self, first_name="firstname"):
        return """
        mutation {
            updateAccount(input:{ firstName: "%s" })
                { success, errors }
        }
        """ % (
            first_name
        )

    def test_update_account_unauthenticated(self, db_verified_user_status):
        executed = self.make_request(self.make_query())
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.UNAUTHENTICATED

    def test_update_account_not_verified(self, db_unverified_user_status, allow_login_not_verified):
        executed = self.make_request(self.make_query(), user_status=db_unverified_user_status)
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.NOT_VERIFIED

    def test_update_account(self, db_verified_user_status):
        user_status = db_verified_user_status
        user = user_status.user.obj
        executed = self.make_request(self.make_query(), user_status=db_verified_user_status)
        assert executed["success"]
        assert not executed["errors"]
        user.refresh_from_db()
        assert user.first_name == "firstname"

    def test_invalid_form(self, db_verified_user_status):
        user_status = db_verified_user_status
        user_obj = user_status.user.obj
        user_obj.first_name = user_status.user.USERNAME_FIELD
        user_obj.save()
        super_long_string = "10" * 150  # django.auth first_name field is 150 characters or fewer.
        executed = self.make_request(
            self.make_query(first_name=super_long_string), user_status=db_verified_user_status
        )
        assert not executed["success"]
        assert executed["errors"]["firstName"]
        user_obj.refresh_from_db()
        assert user_obj.first_name == user_status.user.USERNAME_FIELD

    # @mark.settings_b
    def test_update_account_list_on_settings(self, db_verified_user_status):
        user_status = db_verified_user_status
        user_obj = user_status.user.obj
        executed = self.make_request(self.make_query(), user_status=db_verified_user_status)
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
