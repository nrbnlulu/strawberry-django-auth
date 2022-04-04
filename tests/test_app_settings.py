from gqlauth import settings

from django.test import TestCase


class AppSettingsTestCase(TestCase):
    def test_reload_settings(self):
        self.assertFalse(settings.gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED)
        user_settings = {"ALLOW_LOGIN_NOT_VERIFIED": True}
        settings.reload_gqlauth_settings(
            setting="GQL_AUTH", value=user_settings
        )
        self.assertTrue(settings.gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED)
