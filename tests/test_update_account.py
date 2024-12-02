import pytest

from gqlauth.core.types_ import GQLAuthErrors


def _arg_query(first_name="firstname"):
    return """
mutation MyMutation {
  updateAccount(firstName: "%s") {
    success
    errors
  }
}
    """ % (first_name)


def test_update_account_unauthenticated(db_verified_user_status, anonymous_schema):
    executed = anonymous_schema.execute(_arg_query())
    assert executed.errors[0].message == GQLAuthErrors.UNAUTHENTICATED.value


def test_update_account_not_verified(unverified_schema, allow_login_not_verified):
    executed = unverified_schema.execute(_arg_query())
    assert executed.errors[0].message == GQLAuthErrors.NOT_VERIFIED.value


def test_update_account_success(db_verified_user_status, verified_schema):
    user_status = db_verified_user_status
    user = user_status.user.obj
    executed = verified_schema.execute(_arg_query())
    assert not executed.errors
    assert executed.data["updateAccount"] == {"errors": None, "success": True}
    user.refresh_from_db()
    assert user.first_name == "firstname"


def test_invalid_form(db_verified_user_status, verified_schema):
    user_status = db_verified_user_status
    user_obj = user_status.user.obj
    user_obj.first_name = user_status.user.username_field
    user_obj.save()
    super_long_string = (
        "10" * 150
    )  # django.auth first_name field is 150 characters or fewer.
    executed = verified_schema.execute(_arg_query(first_name=super_long_string)).data[
        "updateAccount"
    ]
    assert not executed["success"]
    assert executed["errors"]["firstName"]
    user_obj.refresh_from_db()
    assert user_obj.first_name == user_status.user.username_field


@pytest.mark.settings_b
def test_update_account_on_settings_b(db_verified_user_status, verified_schema):
    user_status = db_verified_user_status
    user_obj = user_status.user.obj
    executed = verified_schema.execute(_arg_query()).data["updateAccount"]
    assert executed["success"]
    assert not executed["errors"]
    user_obj.refresh_from_db()
    assert user_obj.first_name == "firstname"
