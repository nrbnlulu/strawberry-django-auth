from typing import Tuple

import pytest

from gqlauth.core.constants import Messages
from gqlauth.core.utils import get_token

from .conftest import UserStatusType, fake


def _arg_query(token, password=None):
    password = password or fake.password()
    return """
    mutation {{
        passwordSet(
            token: "{}",
            newPassword1: "{}",
            newPassword2: "{}"
        )
        {{ success, errors }}
    }}
    """.format(
        token,
        password,
        password,
    )


@pytest.fixture()
def set_token_with_unverified_user(
    db_unverified_user_status,
) -> Tuple[UserStatusType, str]:
    db_unverified_user_status.user.old_password = (
        db_unverified_user_status.user.obj.password
    )
    return (
        db_unverified_user_status,
        get_token(db_unverified_user_status.user.obj, "password_set"),
    )


def test_already_set_password(set_token_with_unverified_user, anonymous_schema):
    user_status, token = set_token_with_unverified_user
    user = user_status.user.obj
    query = _arg_query(token)
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["passwordSet"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"] == Messages.PASSWORD_ALREADY_SET

    user.refresh_from_db()
    assert user_status.user.old_password == user.password


def test_set_password_invalid_form(set_token_with_unverified_user, anonymous_schema):
    user_status, token = set_token_with_unverified_user
    user = user_status.user.obj
    # too weak password.
    query = _arg_query(token, "wrong_pass")
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["passwordSet"]
    assert not executed["success"]
    assert executed["errors"]
    user.refresh_from_db()
    assert user_status.user.old_password == user.password


def test_set_password_invalid_token(set_token_with_unverified_user, anonymous_schema):
    user_status, _ = set_token_with_unverified_user
    user = user_status.user.obj
    query = _arg_query("fake_token")
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["passwordSet"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"]
    user.refresh_from_db()
    assert user_status.user.old_password == user.password
