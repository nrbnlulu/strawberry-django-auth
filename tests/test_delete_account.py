import pytest
from django.core.exceptions import ObjectDoesNotExist
from pytest import mark

from gqlauth.core.constants import Messages
from gqlauth.core.types_ import GQLAuthErrors
from tests.conftest import UserStatusType


def _arg_query(user_status: UserStatusType):
    return """
    mutation MyMutation {
      deleteAccount(password: "%s") {
        errors
        success
      }
    }
    """ % (user_status.user.password)


def test_invalid_password(
    db_verified_user_status, wrong_pass_ver_user_status_type, verified_schema
):
    res = verified_schema.execute(query=_arg_query(wrong_pass_ver_user_status_type))
    assert res.data["deleteAccount"]["errors"]["password"] == Messages.INVALID_PASSWORD


def test_not_verified_user(
    unverified_schema,
    wrong_pass_unverified_user_status_type,
):
    res = unverified_schema.execute(
        query=_arg_query(wrong_pass_unverified_user_status_type)
    )
    assert res.errors[0].message == GQLAuthErrors.NOT_VERIFIED.value


@mark.settings_b
def test_valid_password_permanently_delete(db_verified_user_status, verified_schema):
    res = verified_schema.execute(query=_arg_query(db_verified_user_status))
    assert not res.errors
    assert res.data["deleteAccount"]["success"]
    user = db_verified_user_status.user.obj
    with pytest.raises(ObjectDoesNotExist):
        user.refresh_from_db()
