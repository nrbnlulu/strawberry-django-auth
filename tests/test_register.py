from smtplib import SMTPException
from unittest import mock
from pytest import mark

from django.contrib.auth import get_user_model

from .testCases import RelayTestCase, DefaultTestCase

from gqlauth.constants import Messages
from gqlauth.signals import user_registered
from gqlauth.utils import get_token, get_payload_from_token


class RegisterTestCaseMixin:
    def test_register_invalid_password_validation(self):
        """
        fail to register same user with bad password
        """

        # register
        executed = self.make_request(self.register_query("123"))
        self.assertEqual(executed["success"], False)
        self.assertTrue(executed["errors"])

    def test_register(self):
        """
        Register user, fail to register same user again
        """
        signal_received = False

        def receive_signal(sender, user, signal):
            self.assertTrue(user.id is not None)
            nonlocal signal_received
            signal_received = True

        user_registered.connect(receive_signal)

        # register
        executed = self.make_request(self.register_query())
        self.assertEqual(executed["success"], True)
        self.assertEqual(executed["errors"], None)
        self.assertTrue(signal_received)

        # try to register again
        executed = self.make_request(self.register_query())
        self.assertEqual(executed["success"], False)
        self.assertTrue(executed["errors"]["username"])

        # try to register again
        executed = self.make_request(self.register_query(username="other_username"))
        self.assertEqual(executed["success"], False)
        self.assertTrue(executed["errors"]["email"])

    def test_register_duplicate_unique_email(self):
        user = self.register_user(
            email="foo@email.com",
            username="foo",
            verified=True,
            secondary_email="test@email.com",
        )

        executed = self.make_request(self.register_query())
        self.assertEqual(executed["success"], False)
        self.assertTrue(executed["errors"]["email"])

    def test_register_duplicate_unique_email_2(self):
        user = self.register_user(email="foo@email.com", username="foo")
        executed = self.make_request(self.register_query())
        self.assertEqual(executed["success"], False)
        self.assertTrue(executed["errors"]["email"])

    @mock.patch(
        "gqlauth.models.UserStatus.send_activation_email",
        mock.MagicMock(side_effect=SMTPException),
    )
    @mark.settings_b
    def test_register_email_send_fail(self):
        from gqlauth.settings import gqlauth_settings as app_settings
        app_settings.SEND_ACTIVATION_EMAIL = True
        executed = self.make_request(self.register_query())
        self.assertEqual(executed["success"], False)
        self.assertEqual(executed["errors"]["nonFieldErrors"], Messages.EMAIL_FAIL)
        self.assertEqual(len(get_user_model().objects.all()), 0)

class RegisterTestCase(RegisterTestCaseMixin, DefaultTestCase):
    def register_query(self, password="akssdgfbwkc", username="username"):
        cap = self.gen_captcha()
        return """
        mutation {
            register(
                email: "foo@email.com",
                username: "%s",
                password1: "%s",
                password2: "%s",
                identifier: "%s",
                userEntry:"%s"
            )
            { success, errors  }
        }
        """ % (
            username,
            password,
            password,
            cap.uuid,
            cap.text,
        )

    def verify_query(self, token):
        return """
        mutation {
            verifyAccount(token: "%s")
                { success, errors }
            }
        """ % (
            token
        )


class RegisterRelayTestCase(RegisterTestCaseMixin, RelayTestCase):
    def register_query(self, password="akssdgfbwkc", username="username"):
        cap = self.gen_captcha()
        return """
            mutation {
            register(
            input_:{
             email: "foo@email.com",
              username: "%s", password1: "%s", password2: "%s" , identifier: "%s", userEntry:"%s"
            }
            )
            { success, errors }
        }
        """ % (
            username,
            password,
            password,
            cap.uuid,
            cap.text,
        )

    def verify_query(self, token):
        return """
        mutation {
        verifyAccount(input_:{ token: "%s"})
            { success, errors  }
        }
        """ % (
            token
        )
