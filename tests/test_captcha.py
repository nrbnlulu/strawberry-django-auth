from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from PIL import Image

from gqlauth.captcha.models import Captcha
from gqlauth.core.constants import Messages
from gqlauth.settings import gqlauth_settings
from gqlauth.user.signals import user_registered

pytestmark = pytest.mark.skipif(
    not gqlauth_settings.LOGIN_REQUIRE_CAPTCHA
    or not gqlauth_settings.REGISTER_REQUIRE_CAPTCHA,
    reason="This test requires captcha mutation fields to be initialized",
)


def test_get_captcha_saves_and_returns_cap_obj(captcha):
    Captcha.objects.get(pk=captcha.uuid)


def test_captcha_text_validation(captcha):
    text = captcha.text
    obj = Captcha.objects.get(pk=captcha.uuid)
    assert obj.validate(user_entry=text)


def test_str(captcha):
    assert str(captcha)


def test_bytes(captcha):
    captcha.as_bytes()


def test_register_user_require_captcha_validation(unverified_schema):
    res = unverified_schema.execute(
        query=register_query_without_cap_fields(username="fdsafsdfgv"), relay=True
    )
    assert (
        "identifier' of required type 'UUID!' was not provided."
        in res.errors[0].message
    )
    assert (
        "userEntry' of required type 'String!' was not provided"
        in res.errors[1].message
    )


def test_login_require_captcha_validation(unverified_schema):
    res = unverified_schema.execute(
        query=login_query_without_cap_fields(username="fake"), relay=True
    )
    assert (
        "identifier' of required type 'UUID!' was not provided."
        in res.errors[0].message
    )
    assert (
        "userEntry' of required type 'String!' was not provided"
        in res.errors[1].message
    )


def test_register_wrong_captcha_validation(captcha, unverified_schema):
    res = unverified_schema.execute(query=register_query(uuid=captcha.uuid), relay=True)
    assert res.data["register"]["errors"]["captcha"] == Messages.CAPTCHA_INVALID


def test_register_wrong_uuid(captcha, unverified_schema):
    res = unverified_schema.execute(query=register_query(uuid=uuid4()), relay=True)
    assert res.data["register"]["errors"]["captcha"] == Messages.CAPTCHA_EXPIRED


def test_register_correct_captcha_create_user(
    captcha, unverified_schema, username="test_captcha"
):
    handler = MagicMock()
    user_registered.connect(handler)
    unverified_schema.execute(
        query=register_query(
            username=username,
            password="SuperSecureP@ssw0rd",
            uuid=captcha.uuid,
            input_=captcha.text,
        ),
        relay=True,
    )
    user = get_user_model().objects.get(username=username)
    handler.assert_called_once()
    assert handler.call_args.kwargs.get("user") == user


def test_max_tries_deletes_captcha(captcha):
    for _ in range(gqlauth_settings.CAPTCHA_MAX_RETRIES + 2):
        captcha.validate("wrong")
    with pytest.raises(Captcha.DoesNotExist):
        Captcha.objects.get(pk=captcha.uuid)


def login_query_without_cap_fields(password="fake", username="username"):
    return """
        mutation {{
            tokenAuth(
            input:{{
             username: "{}", password: "{}"
            }}
            )
            {{ success, errors }}
        }}
        """.format(
        username,
        password,
    )


def login_query(password="fake", username="username", uuid="fake", input_="wrong"):
    return """
        mutation {{
            tokenAuth(
            input:{{
            username: "{}", password: "{}",identifier: "{}", userEntry:"{}"
            }}
            )
            {{ success, errors }}
        }}
        """.format(
        username,
        password,
        uuid,
        input_,
    )


def test_captcha_saved_if_settings_is_on(captcha):
    assert Path(captcha.image.path).exists()
    # if this didn't raise we are good.
    Image.open(captcha.image.path)


def register_query_without_cap_fields(password="akssdgfbwkc", username="username"):
    return """
      mutation{{
        register(
            input: {{
                email: "tesfdfdt@email.com", username: "{}", password1: "{}", password2: "{}"
                   }}
           )
          {{
            success
            errors
          }}
        }}
      """.format(
        username,
        password,
        password,
    )


def register_query(password="fake", username="username", uuid="fake", input_="wrong"):
    return """
      mutation {{
          register(
          input: {{
           email: "tesfdfdt@email.com", username: "{}", password1: "{}", password2: "{}" , identifier: "{}", userEntry:"{}"
          }}
          )
          {{ success, errors }}
      }}
      """.format(
        username,
        password,
        password,
        uuid,
        input_,
    )


def test_captcha_mutation(anonymous_schema, db):
    query = """
        mutation MyMutation {
            captcha{
            uuid
            image{
              name
              path
              size
              url
              width
              height
            }
            pilImage
          }
        }
    """
    res = anonymous_schema.execute(query=query)
    assert not res.errors
    uuid = res.data["captcha"]["uuid"]
    assert Captcha.objects.get(uuid=uuid)
