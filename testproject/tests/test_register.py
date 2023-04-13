from smtplib import SMTPException
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from gqlauth.backends.strawberry_django_auth.models import Captcha
from gqlauth.backends.strawberry_django_auth.signals import user_registered
from gqlauth.core.types_ import Messages
from gqlauth.settings_type import GqlAuthSettings
from strawberry.utils.str_converters import to_camel_case

from .conftest import CC_USERNAME_FIELD, UserType


def _generate_register_args(user: UserType, captcha: Captcha) -> str:
    initial = ""
    app_settings: GqlAuthSettings = settings.GQL_AUTH
    if not app_settings.ALLOW_PASSWORDLESS_REGISTRATION:
        initial = f'password1: "{user.password}",  password2: "{user.password}", '
    if settings.GQL_AUTH.REGISTER_REQUIRE_CAPTCHA:
        initial += f'identifier: "{captcha.uuid}", userEntry:"{captcha.text}"'
    for field in [field.name for field in settings.GQL_AUTH.REGISTER_MUTATION_FIELDS]:
        if "password" not in field:
            initial += f', {to_camel_case(field)}: "{getattr(user, field)}"'
    return initial


def _arg_query(user: UserType, captcha: Captcha):
    return """
    mutation {
        register(
            %s
        )
        { success, errors  }
    }
    """ % (
        _generate_register_args(user, captcha)
    )


@pytest.mark.default_user  # settings_b has passwordless registration
def test_register_invalid_password_validation(verified_user_type, anonymous_schema, captcha):
    """Fail to register same user with bad password."""
    # register
    us = verified_user_type
    us.user.password = "123"  # invalid password
    executed = anonymous_schema.execute(query=_arg_query(us.user, captcha)).data["register"]
    assert not executed["success"]
    assert executed["errors"]


def test_register_twice_fails(default_testcase, db):
    """Register user, fail to register same user again."""
    signal_received = False

    def receive_signal(sender, user, signal):
        assert user.id is not None
        nonlocal signal_received
        signal_received = True

    user_registered.connect(receive_signal)
    ut = UserType(verified=True)

    def get_query() -> str:
        return _arg_query(ut, Captcha.create_captcha())

    # register
    executed = default_testcase.anonymous_schema.execute(query=get_query())
    assert not executed.errors
    executed = executed.data["register"]
    assert executed["success"]
    assert not executed["errors"]
    assert signal_received
    # try to register again
    executed = default_testcase.anonymous_schema.execute(query=get_query()).data["register"]
    assert not executed["success"]
    assert executed["errors"][CC_USERNAME_FIELD]


@mock.patch(
    "gqlauth.backends.strawberry_django_auth.backend.DjangoGqlAuthBackend.send_activation_email",
    mock.MagicMock(side_effect=SMTPException),
)
@pytest.mark.default_user
def test_register_email_send_fail(default_testcase, captcha, app_settings, verified_user_type):
    app_settings.SEND_ACTIVATION_EMAIL = True
    executed = default_testcase.anonymous_schema.execute(
        query=_arg_query(verified_user_type, captcha)
    )
    executed = executed.data["register"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"] == Messages.EMAIL_FAIL
    assert not get_user_model().objects.all()
