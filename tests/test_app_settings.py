import pytest

from gqlauth import settings as app_settings


def test_load_user_settings_from_django_settings(settings):
    assert app_settings.gqlauth_settings.EMAIL_FROM == settings.DEFAULT_FROM_EMAIL


@pytest.mark.settings_b
def test_user_can_override_django_settings(settings):
    assert settings.GQL_AUTH.EMAIL_FROM == app_settings.gqlauth_settings.EMAIL_FROM
    assert app_settings.gqlauth_settings.EMAIL_FROM != settings.DEFAULT_FROM_EMAIL
