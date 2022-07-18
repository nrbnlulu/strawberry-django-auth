from smtplib import SMTPException
from unittest import mock

from django.contrib.auth import get_user_model
from pytest import mark

from gqlauth.constants import Messages
from gqlauth.signals import user_registered

from .testCases import ArgTestCase, RelayTestCase, UserType, AsyncDefaultTestCase, \
    AsyncRelayTestCase


class RegisterTestCaseMixin:
    class RegisterUserType(UserType):
        password_2: str = None
        def __post_init__(self):
            if not self.password_2:
                self.password_2 = self.password

    def _arg_query(self,user: UserType):
        cap = self.gen_captcha()
        return """
        mutation {{
            register(
                email: "{}",
                username: "{}",
                password1: "{}",
                password2: "{}",
                identifier: "{}",
                userEntry:"{}"
            )
            {{ success, errors  }}
        }}
        """.format(
            user.email,
            user.username,
            user.password,
            user.password,
            cap.uuid,
            cap.text,
        )

    def _relay_query(self,user: UserType):
        cap = self.gen_captcha()
        return """
            mutation {{
            register(
            input:{{
             email: "{}",
              username: "{}", password1: "{}", password2: "{}" , identifier: "{}", userEntry:"{}"
            }}
            )
            {{ success, errors }}
        }}
        """.format(
            user.email,
            user.username,
            user.password,
            user.password,
            cap.uuid,
            cap.text,
        )


    def test_register_invalid_password_validation(self):
        """
        fail to register same user with bad password
        """

        # register
        us = self.verified_user_status_type()
        us.user.password = "123"  # invalid password
        executed = self.make_request(query=self.make_query(us.user), no_login_query=True)
        assert not executed["success"]
        assert executed["errors"]

    def test_register_twice_fails(self):
        """
        Register user, fail to register same user again
        """
        signal_received = False

        def receive_signal(sender, user, signal):
            assert user.id is not None
            nonlocal signal_received
            signal_received = True
        user_registered.connect(receive_signal)

        us = self.verified_user_status_type().user
        # register
        executed = self.make_request(query=self.make_query(us))
        assert executed["success"]
        assert not executed["errors"]
        assert signal_received
        # try to register again
        executed = self.make_request(query=self.make_query(us))
        assert not executed["success"]
        assert executed["errors"]["username"]

        us1 = self.verified_user_status_type().user
        us1.username = "foo_username"
        # try to register again
        executed = self.make_request(query=self.make_query(us1))
        assert not executed["success"]
        assert executed["errors"]["email"]

    def test_register_duplicate_unique_email(self, db_verified_user_status):
        us = db_verified_user_status.user
        us.username = "foo_username"  # dropping duplication for username
        executed = self.make_request(query=self.make_query(us))
        assert not executed["success"]
        assert executed["errors"]["email"]

    @mock.patch(
        "gqlauth.models.UserStatus.send_activation_email",
        mock.MagicMock(side_effect=SMTPException),
    )
    def test_register_email_send_fail(self):
        from gqlauth.settings import gqlauth_settings as app_settings
        us = self.verified_user_status_type().user
        app_settings.SEND_ACTIVATION_EMAIL = True
        executed = self.make_request(query=self.make_query(us))
        assert not executed["success"]
        assert executed["errors"]["nonFieldErrors"] == Messages.EMAIL_FAIL
        assert not get_user_model().objects.all()


class TestArgRegister(RegisterTestCaseMixin, ArgTestCase):
    ...


class TestRelayRegister(RegisterTestCaseMixin, RelayTestCase):
    ...


class TestAsyncArgRegister(RegisterTestCaseMixin, AsyncDefaultTestCase):
    ...


class TestAsyncRelayRegister(RegisterTestCaseMixin, AsyncRelayTestCase):
    ...

