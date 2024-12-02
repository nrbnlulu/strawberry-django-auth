from typing import Tuple

import pytest

from gqlauth.core.utils import get_token

from .conftest import UserStatusType


def _arg_query(token, new_password1="new_password", new_password2="new_password"):
    return """
    mutation {{
        passwordReset(
            token: "{}",
            newPassword1: "{}",
            newPassword2: "{}"
        )
        {{ success, errors }}
    }}
    """.format(
        token,
        new_password1,
        new_password2,
    )


@pytest.fixture()
def reset_token_with_unverified_user(
    db_unverified_user_status,
) -> Tuple[UserStatusType, str]:
    db_unverified_user_status.user.old_password = (
        db_unverified_user_status.user.obj.password
    )
    return (
        db_unverified_user_status,
        get_token(db_unverified_user_status.user.obj, "password_reset"),
    )


def test_reset_password(reset_token_with_unverified_user, unverified_schema):
    user_status, token = reset_token_with_unverified_user
    user = user_status.user.obj
    query = _arg_query(token=token)
    #  user can not be verified.
    executed = unverified_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["passwordReset"]
    assert executed["success"]
    assert not executed["errors"]
    user.refresh_from_db()
    assert user_status.user.old_password != user.password


def test_reset_password_invalid_form(
    reset_token_with_unverified_user, unverified_schema
):
    user_status, token = reset_token_with_unverified_user
    user = user_status.user.obj
    query = _arg_query(token, "wrong_pass")
    executed = unverified_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["passwordReset"]
    assert not executed["success"]
    assert executed["errors"]
    user.refresh_from_db()
    assert user_status.user.old_password == user.password


def test_reset_password_invalid_token(
    reset_token_with_unverified_user, unverified_schema
):
    user_status, _ = reset_token_with_unverified_user
    user = user_status.user.obj
    query = _arg_query("fake_token")
    executed = unverified_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["passwordReset"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"]
    user.refresh_from_db()
    assert user_status.user.old_password == user.password


def test_revoke_refresh_tokens_on_password_reset(
    allow_login_not_verified, reset_token_with_unverified_user, unverified_schema
):
    user_status, reset_token = reset_token_with_unverified_user
    user = user_status.user.obj
    user_status.generate_refresh_token()
    user.refresh_from_db()
    refresh_tokens = user.refresh_tokens.all()
    assert refresh_tokens
    for token in refresh_tokens:
        assert not token.revoked
    query = _arg_query(reset_token)
    res = unverified_schema.execute(query=query)
    assert not res.errors
    res = res.data["passwordReset"]
    assert res["success"]
    assert not res["errors"]
    user.refresh_from_db()
    assert user_status.user.old_password != user.password
    refresh_tokens = user.refresh_tokens.all()
    assert refresh_tokens
    for token in refresh_tokens:
        assert token.revoked


def test_reset_password_verify_user(db_verified_user_status, verified_schema):
    user = db_verified_user_status.user.obj
    old_password = user.password
    token = get_token(user, "password_reset")
    query = _arg_query(token)
    res = verified_schema.execute(query=query)
    assert not res.errors
    res = res.data["passwordReset"]
    assert res["success"]
    assert not res["errors"]
    user.refresh_from_db()
    assert old_password != user.password
    assert user.status.verified
