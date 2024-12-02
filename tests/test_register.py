from smtplib import SMTPException
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from strawberry.utils.str_converters import to_camel_case

from gqlauth.captcha.models import Captcha
from gqlauth.core.constants import Messages
from gqlauth.settings_type import GqlAuthSettings
from gqlauth.user.signals import user_registered

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
    """ % (_generate_register_args(user, captcha))


@pytest.mark.default_user  # settings_b has passwordless registration
def test_register_invalid_password_validation(
    verified_user_status_type, anonymous_schema, captcha
):
    """Fail to register same user with bad password."""
    # register
    us = verified_user_status_type
    us.user.password = "123"  # invalid password
    executed = anonymous_schema.execute(query=_arg_query(us.user, captcha)).data[
        "register"
    ]
    assert not executed["success"]
    assert executed["errors"]


@pytest.mark.skip(
    "This test will is waiting"
    "for the channel consumer to mimic the *real* behavior of channel requests."
)
async def test_channels_register(
    verified_user_status_type, captcha, unverified_channels_app_communicator
):
    us = verified_user_status_type
    query = _arg_query(us.user, captcha)
    async for res in unverified_channels_app_communicator.subscribe(query):
        assert res.data["register"]["success"] is True


def test_register_twice_fails(verified_user_status_type, anonymous_schema, db):
    """Register user, fail to register same user again."""
    signal_received = False

    def receive_signal(sender, user, signal):
        assert user.id is not None
        nonlocal signal_received
        signal_received = True

    user_registered.connect(receive_signal)

    def get_query() -> str:
        return _arg_query(verified_user_status_type.user, Captcha.create_captcha())

    # register
    executed = anonymous_schema.execute(query=get_query())
    assert not executed.errors
    executed = executed.data["register"]
    assert not executed["errors"]
    assert executed["success"]
    assert signal_received
    # try to register again
    executed = anonymous_schema.execute(query=get_query()).data["register"]
    assert not executed["success"]
    assert executed["errors"][CC_USERNAME_FIELD]


@mock.patch(
    "gqlauth.models.UserStatus.send_activation_email",
    mock.MagicMock(side_effect=SMTPException),
)
@pytest.mark.default_user
def test_register_email_send_fail(verified_user_status_type, captcha, anonymous_schema):
    from gqlauth.settings import gqlauth_settings as app_settings

    us = verified_user_status_type.user
    app_settings.SEND_ACTIVATION_EMAIL = True
    executed = anonymous_schema.execute(query=_arg_query(us, captcha)).data["register"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"] == Messages.EMAIL_FAIL
    assert not get_user_model().objects.all()
