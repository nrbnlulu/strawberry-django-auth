from smtplib import SMTPException
from unittest import mock

import pytest

from gqlauth.core.constants import Messages

from .conftest import UserType

pytestmark = pytest.mark.default_user


def _arg_query(user: UserType):
    return """
    mutation {
    sendPasswordResetEmail(email: "%s")
        { success, errors }
    }
    """ % (user.email)


def test_send_email_invalid_email(db_verified_user_status, anonymous_schema):
    """Invalid email should be successful request.

    (due to security measures)
    """
    user = db_verified_user_status.user
    user.email = "invalid@email.com"
    query = _arg_query(user)
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["sendPasswordResetEmail"]
    assert executed["success"]
    assert not executed["errors"]


def test_invalid_form(db_verified_user_status, anonymous_schema):
    user = db_verified_user_status.user
    user.email = "invalid * form@email.com"
    query = _arg_query(user)
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["sendPasswordResetEmail"]
    assert not executed["success"]
    assert executed["errors"]["email"]


def test_send_email_valid_email_verified_user(
    db_verified_user_status, anonymous_schema
):
    query = _arg_query(db_verified_user_status.user)
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["sendPasswordResetEmail"]
    assert executed["success"]
    assert not executed["errors"]


@mock.patch(
    "gqlauth.models.UserStatus.send_password_reset_email",
    mock.MagicMock(side_effect=SMTPException),
)
def test_send_email_fail_to_send_email(db_verified_user_status, anonymous_schema):
    query = _arg_query(db_verified_user_status.user)
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["sendPasswordResetEmail"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"] == Messages.EMAIL_FAIL
