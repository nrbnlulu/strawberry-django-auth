import pytest

from gqlauth import settings as app_settings

pytestmark = pytest.mark.django_db


def test_load_user_settings_from_django_settings(settings):
    assert app_settings.gqlauth_settings.EMAIL_FROM == settings.DEFAULT_FROM_EMAIL


@pytest.mark.settings_b
def test_user_can_override_django_settings(settings):
    assert app_settings.gqlauth_settings.EMAIL_FROM != settings.DEFAULT_FROM_EMAIL


def test_reload_settings(settings):
    assert not app_settings.gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED
    user_settings = {"ALLOW_LOGIN_NOT_VERIFIED": True}
    app_settings.reload_gqlauth_settings(setting="GQL_AUTH", value=user_settings)
    assert app_settings.gqlauth_settings.ALLOW_LOGIN_NOT_VERIFIED
