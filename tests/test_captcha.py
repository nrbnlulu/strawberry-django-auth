from unittest.mock import MagicMock
from uuid import uuid4

from django.contrib.auth import get_user_model

from gqlauth.constants import Messages
from gqlauth.models import Captcha
from gqlauth.settings import gqlauth_settings
from gqlauth.signals import user_registered

from .testCases import RelayTestCase


class CaptchaTestCaseMixin:
    @staticmethod
    def gen_captcha():
        return Captcha.create_captcha()

    def test_get_captcha_saves_and_returns_cap_obj(self):
        cap = self.gen_captcha()
        Captcha.objects.get(pk=cap.uuid)

    def test_captcha_text_validation(self):
        cap = self.gen_captcha()
        text = cap.text
        obj = Captcha.objects.get(pk=cap.uuid)
        self.assertTrue(obj.validate(user_entry=text))

    def test_register_user_require_captcha_validation(self):
        try:
            self.make_request(self.register_query_without_cap_fields(username="fdsafsdfgv"))
        except Exception as e:
            assert "identifier' of required type 'UUID!' was not provided." in e.args[0]
            assert "userEntry' of required type 'String!' was not provided" in e.args[1]

    def test_login_require_captcha_validation(self):
        try:
            self.make_request(self.login_query_without_cap_fields(username="fake"))
        except Exception as e:
            assert "identifier' of required type 'String!' was not provided" in e.args[0]
            assert "userEntry' of required type 'String!' was not provided" in e.args[1]

    def test_register_wrong_captcha_validation(self):
        cap = self.gen_captcha()
        res = self.make_request(self.register_query(uuid=cap.uuid))
        self.assertEqual(res["errors"]["captcha"], Messages.CAPTCHA_INVALID)

    def test_register_wrong_uuid(self):
        cap = self.gen_captcha()
        res = self.make_request(self.register_query(uuid=uuid4(), input_=cap.text))
        self.assertEqual(res["errors"]["captcha"], Messages.CAPTCHA_EXPIRED)

    def test_register_correct_captcha_create_user(self, username="test_captcha"):
        handler = MagicMock()
        user_registered.connect(handler)

        cap = self.gen_captcha()
        self.make_request(
            self.register_query(
                username=username,
                password="SuperSecureP@ssw0rd",
                uuid=cap.uuid,
                input_=cap.text,
            )
        )
        user = get_user_model().objects.get(username=username)
        handler.assert_called_once()
        assert handler.call_args.kwargs.get("user") == user

    def test_login_user_require_captcha_validation(self):
        try:
            self.make_request(self.register_query_without_cap_fields(username="fdsafsdfgv"))
        except Exception as e:
            self.assertIn("identifier' of required type 'UUID!' was not provided", e.args[0])
            self.assertIn("userEntry' of required type 'String!' was not provided", e.args[1])

    def test_max_tries_deletes_captcha(self):
        cap = self.gen_captcha()
        for _ in range(gqlauth_settings.CAPTCHA_MAX_RETRIES + 2):
            cap.validate("wrong")

        self.assertRaises(Captcha.DoesNotExist, lambda: Captcha.objects.get(pk=cap.uuid))


req_captcha = {
    "LOGIN_REQUIRE_CAPTCHA": True,
    "REGISTER_REQUIRE_CAPTCHA": True,
}


class CaptchaRelayTestCase(CaptchaTestCaseMixin, RelayTestCase):
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
