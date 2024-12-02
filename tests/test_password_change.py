import dataclasses

from .conftest import UserStatusType, fake


@dataclasses.dataclass
class PasswordChangeForm:
    password_1: str
    password_2: str


def _arg_query(user_status: UserStatusType, password_form: PasswordChangeForm):
    return """
mutation {{
  passwordChange(oldPassword: "{}", newPassword1: "{}", newPassword2: "{}") {{
    errors
    success
    token {{
      token
      payload {{
        origIat
        exp
      }}
    }}
    refreshToken {{
      token
      created
      revoked
      expiresAt
      isExpired
    }}
  }}
}}
    """.format(
        user_status.user.password,
        password_form.password_1,
        password_form.password_2,
    )


SECURE_PASSWORD = fake.password()


def test_password_change(db_verified_user_status, verified_schema):
    """Change password."""
    form = PasswordChangeForm(SECURE_PASSWORD, SECURE_PASSWORD)
    query = _arg_query(user_status=db_verified_user_status, password_form=form)
    res = verified_schema.execute(query=query)
    user = db_verified_user_status.user.obj
    data = res.data["passwordChange"]
    assert data["success"]
    assert not data["errors"]
    assert data["token"]["token"]
    assert data["refreshToken"]["token"]
    user.refresh_from_db()
    assert db_verified_user_status.user.password != user.password


def test_mismatch_passwords(db_verified_user_status, verified_schema):
    """Wrong inputs."""
    user = db_verified_user_status.user.obj
    old_password = user.password
    form = PasswordChangeForm(SECURE_PASSWORD, SECURE_PASSWORD + "mismatch")
    query = _arg_query(user_status=db_verified_user_status, password_form=form)
    res = verified_schema.execute(query=query)
    data = res.data["passwordChange"]
    assert not data["success"]
    assert data["errors"]["newPassword2"]
    assert not data["refreshToken"] or data["token"]
    user.refresh_from_db()
    assert user.password == old_password


def test_passwords_validation(db_verified_user_status, verified_schema):
    """Easy password."""
    simple_password = PasswordChangeForm("123", "123")
    query = _arg_query(
        user_status=db_verified_user_status, password_form=simple_password
    )
    res = verified_schema.execute(query=query)
    assert not res.errors
    data = res.data["passwordChange"]
    assert not data["success"]
    assert data["errors"]
    assert not data["refreshToken"] or data["token"]


def test_revoke_refresh_tokens_on_password_change(
    db_verified_user_status, verified_schema
):
    user = db_verified_user_status.user.obj
    old_password = user.password
    form = PasswordChangeForm(SECURE_PASSWORD, SECURE_PASSWORD)
    query = _arg_query(user_status=db_verified_user_status, password_form=form)
    # creating token and verify that it is valid.
    db_verified_user_status.generate_refresh_token()
    user.refresh_from_db()
    refresh_tokens = user.refresh_tokens.all()
    assert refresh_tokens
    for token in refresh_tokens:
        assert not token.revoked
    executed = verified_schema.execute(query=query).data["passwordChange"]
    assert executed["success"]
    assert not executed["errors"]
    assert executed["token"]["token"]
    assert executed["refreshToken"]["token"]
    user.refresh_from_db()
    assert old_password != user.password
    refresh_tokens = user.refresh_tokens.all()
    assert refresh_tokens
    # the last token is not revoked
    # since it is returned by the password change mutation.
    for token in list(refresh_tokens)[:-1]:
        assert token.revoked
