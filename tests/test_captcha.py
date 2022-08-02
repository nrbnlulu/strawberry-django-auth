from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from PIL import Image
from django.contrib.auth import get_user_model
import pytest

from gqlauth.constants import Messages
from gqlauth.models import Captcha
from gqlauth.settings import gqlauth_settings
from gqlauth.signals import user_registered

from .testCases import AsyncRelayTestCase, RelayTestCase


@pytest.mark.skipif(
    not gqlauth_settings.LOGIN_REQUIRE_CAPTCHA or not gqlauth_settings.REGISTER_REQUIRE_CAPTCHA,
    reason="This test requires captcha mutation fields to be initialized",
)
class CaptchaTestCaseMixin:
    @classmethod
    @pytest.fixture()
    def cap(cls, db):
        return Captcha.create_captcha()

    def test_get_captcha_saves_and_returns_cap_obj(self, cap):
        Captcha.objects.get(pk=cap.uuid)

    def test_captcha_text_validation(self, cap):
        text = cap.text
        obj = Captcha.objects.get(pk=cap.uuid)
        assert obj.validate(user_entry=text)

    def test_register_user_require_captcha_validation(self):
        try:
            self.make_request(
                query=self.register_query_without_cap_fields(username="fdsafsdfgv"),
                user_status=None,
            )
        except Exception as e:
            assert "identifier' of required type 'UUID!' was not provided." in e.args[0]
            assert "userEntry' of required type 'String!' was not provided" in e.args[1]

    def test_login_require_captcha_validation(self):
        try:
            self.make_request(
                query=self.login_query_without_cap_fields(username="fake"), user_status=None
            )
        except Exception as e:
            assert "identifier' of required type 'String!' was not provided" in e.args[0]
            assert "userEntry' of required type 'String!' was not provided" in e.args[1]

    def test_register_wrong_captcha_validation(self, cap):
        res = self.make_request(query=self.register_query(uuid=cap.uuid), user_status=None)
        assert res["errors"]["captcha"] == Messages.CAPTCHA_INVALID

    def test_register_wrong_uuid(self, cap):
        res = self.make_request(
            query=self.register_query(uuid=uuid4(), input_=cap.text), user_status=None
        )
        assert res["errors"]["captcha"] == Messages.CAPTCHA_EXPIRED

    def test_register_correct_captcha_create_user(self, cap, username="test_captcha"):
        handler = MagicMock()
        user_registered.connect(handler)
        self.make_request(
            query=self.register_query(
                username=username,
                password="SuperSecureP@ssw0rd",
                uuid=cap.uuid,
                input_=cap.text,
            ),
            user_status=None,
        )
        user = get_user_model().objects.get(username=username)
        handler.assert_called_once()
        assert handler.call_args.kwargs.get("user") == user

    def test_login_user_require_captcha_validation(self):
        try:
            self.make_request(
                query=self.register_query_without_cap_fields(username="fdsafsdfgv"),
                user_status=None,
            )
        except Exception as e:
            assert "identifier' of required type 'UUID!' was not provided" in e.args[0]
            assert "userEntry' of required type 'String!' was not provided" in e.args[1]

    def test_max_tries_deletes_captcha(self, cap):
        for _ in range(gqlauth_settings.CAPTCHA_MAX_RETRIES + 2):
            cap.validate("wrong")
        with pytest.raises(Captcha.DoesNotExist):
            Captcha.objects.get(pk=cap.uuid)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def test_captcha_saved_if_settings_is_on(cap):
        assert Path(cap.image.path).exists()
        # if this didn't raise we are good.
        Image.open(cap.image.path)


class TestCaptchaRelay(CaptchaTestCaseMixin, RelayTestCase):
    ...


class TestCaptchaAsync(CaptchaTestCaseMixin, AsyncRelayTestCase):
    ...
