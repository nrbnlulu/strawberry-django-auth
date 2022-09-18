import dataclasses

from .testCases import (
    AbstractTestCase,
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
    UserStatusType,
    fake,
)


class PasswordChangeTestCaseMixin(AbstractTestCase):
    SECURE_PASSWORD = fake.password()

    @dataclasses.dataclass
    class PasswordChangeForm:
        password_1: str
        password_2: str

    @classmethod
    def _arg_query(cls, user_status: UserStatusType, password_form: PasswordChangeForm):
        return """
        mutation MyMutation {{
          authEntry {{
            node {{
              passwordChange(oldPassword: "{}", newPassword1:"{}", newPassword2:"{}"){{
                success
                errors
                token{{
                  token
                  payload{{
                    exp
                    origIat
                  }}
                }}
                refreshToken{{
                  token
                  created
                  revoked
                  expiresAt
                  isExpired
                }}
              }}
            }}
          }}
        }}
        """.format(
            user_status.user.password,
            password_form.password_1,
            password_form.password_2,
        )

    @classmethod
    def _relay_query(cls, user_status: UserStatusType, password_form: PasswordChangeForm):
        return """
        mutation MyMutation {{
          authEntry {{
            node {{
              passwordChange(input:{{oldPassword: "{}", newPassword1:"{}", newPassword2:"{}"}}){{
                success
                errors
                token{{
                  token
                  payload{{
                    exp
                    origIat
                  }}
                }}
                refreshToken{{
                  token
                  created
                  revoked
                  expiresAt
                  isExpired
                }}
              }}
            }}
          }}
        }}
        """.format(
            user_status.user.password,
            password_form.password_1,
            password_form.password_2,
        )

    def test_password_change(self, db_verified_user_status):
        """
        change password
        """
        form = self.PasswordChangeForm(self.SECURE_PASSWORD, self.SECURE_PASSWORD)
        query = self.make_query(user_status=db_verified_user_status, password_form=form)
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        user = db_verified_user_status.user.obj
        data = executed["node"]["passwordChange"]
        assert data["success"]
        assert not data["errors"]
        assert data["token"]["token"]
        assert data["refreshToken"]["token"]
        user.refresh_from_db()
        assert db_verified_user_status.user.password != user.password

    def test_mismatch_passwords(self, db_verified_user_status):
        """
        wrong inputs
        """
        user = db_verified_user_status.user.obj
        old_password = user.password
        form = self.PasswordChangeForm(self.SECURE_PASSWORD, self.SECURE_PASSWORD + "mismatch")
        query = self.make_query(user_status=db_verified_user_status, password_form=form)
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        data = executed["node"]["passwordChange"]
        assert not data["success"]
        assert data["errors"]["newPassword2"]
        assert not data["refreshToken"] or data["token"]
        user.refresh_from_db()
        assert user.password == old_password

    def test_passwords_validation(self, db_verified_user_status):
        """
        easy password
        """
        simple_password = self.PasswordChangeForm("123", "123")
        query = self.make_query(user_status=db_verified_user_status, password_form=simple_password)
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        data = executed["node"]["passwordChange"]
        assert not data["success"]
        assert data["errors"]
        assert not data["refreshToken"] or data["token"]

    def test_revoke_refresh_tokens_on_password_change(self, db_verified_user_status):
        user = db_verified_user_status.user.obj
        old_password = user.password
        form = self.PasswordChangeForm(self.SECURE_PASSWORD, self.SECURE_PASSWORD)
        query = self.make_query(user_status=db_verified_user_status, password_form=form)
        # creating token and verify that it is valid.
        self.get_tokens(db_verified_user_status)
        user.refresh_from_db()
        refresh_tokens = user.refresh_tokens.all()
        assert refresh_tokens
        for token in refresh_tokens:
            assert not token.revoked
        executed = self.make_request(query=query, user_status=db_verified_user_status)["node"][
            "passwordChange"
        ]
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


class TestArgPasswordChange(PasswordChangeTestCaseMixin, ArgTestCase):
    ...


class TestRelayPasswordChange(PasswordChangeTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgPasswordChange(PasswordChangeTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayPasswordChange(PasswordChangeTestCaseMixin, AsyncRelayTestCase):
    ...
