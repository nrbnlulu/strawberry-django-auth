from smtplib import SMTPException
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
import pytest
from strawberry.utils.str_converters import to_camel_case

from gqlauth.core.constants import Messages
from gqlauth.user.signals import user_registered

from .testCases import (
    ArgTestCase,
    AsyncArgTestCase,
    AsyncRelayTestCase,
    RelayTestCase,
    UserType,
)


class RegisterTestCaseMixin:
    def _generate_register_args(self, user: UserType) -> str:
        initial = f'password1: "{user.password}",  password2: "{user.password}"'
        if settings.GQL_AUTH.REGISTER_REQUIRE_CAPTCHA:
            cap = self.gen_captcha()
            initial += f',  identifier: "{cap.uuid}", userEntry:"{cap.text}"'
        for field in [field.name for field in settings.GQL_AUTH.REGISTER_MUTATION_FIELDS]:
            if "password" not in field:
                initial += f', {to_camel_case(field)}: "{getattr(user, field)}"'
        return initial

    def _arg_query(self, user: UserType):
        return """
        mutation {{
            register(
                {}
            )
            {{ success, errors  }}
        }}
        """.format(
            self._generate_register_args(user)
        )

    def _relay_query(self, user: UserType):
        return """
            mutation {{
            register(
            input:{{
             {}
            }}
            )
            {{ success, errors }}
        }}
        """.format(
            self._generate_register_args(user)
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

    def test_register_twice_fails(self, current_markers):
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
        assert executed["errors"][self.CC_USERNAME_FIELD]
        # try to register again other fields but same email
        # in setting_b we don't have email field os there is only one unique field.
        if "not settings_b" in current_markers:
            us1 = self.verified_user_status_type().user
            us1.email = us.email
            executed = self.make_request(query=self.make_query(us1))
            assert not executed["success"]
            assert executed["errors"]["email"]

    @pytest.mark.default_user
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
    @pytest.mark.default_user
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


class TestAsyncArgRegister(RegisterTestCaseMixin, AsyncArgTestCase):
    ...


class TestAsyncRelayRegister(RegisterTestCaseMixin, AsyncRelayTestCase):
    ...
