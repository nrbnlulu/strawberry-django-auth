from pytest import mark
from django.test import TestCase
from django.conf import settings as django_settings
from gqlauth import settings as app_settings


class AppSettingsTestCase(TestCase):
    def test_reload_settings(self):
        self.assertFalse(app_settings.gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED)
        user_settings = {"ALLOW_LOGIN_NOT_VERIFIED": True}
        app_settings.reload_gqlauth_settings(setting="GQL_AUTH", value=user_settings)
        self.assertTrue(app_settings.gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED)

    def test_load_user_settings_from_django_settings(self):
        assert (
            django_settings.DEFAULT_FROM_EMAIL
            == app_settings.gqlauth_settings.EMAIL_FROM
        )

    @mark.settings_b
    def test_user_can_override_DjangoSetting_TypeVar(self):
        assert (
            django_settings.DEFAULT_FROM_EMAIL
            != app_settings.gqlauth_settings.EMAIL_FROM
        )
