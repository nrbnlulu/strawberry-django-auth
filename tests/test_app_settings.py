import pytest

from gqlauth.settings_type import GqlAuthSettings


@pytest.fixture()
def default_app_settings() -> GqlAuthSettings:
    return GqlAuthSettings()


def test_load_user_settings_from_django_settings(settings, default_app_settings):
    fake = "foo@bar.com"
    assert settings.DEFAULT_FROM_EMAIL != fake
    settings.DEFAULT_FROM_EMAIL = fake
    assert default_app_settings.EMAIL_FROM.value == fake


@pytest.mark.settings_b
def test_user_can_override_django_settings(settings, app_settings):
    assert settings.DEFAULT_FROM_EMAIL != "SomeDiffrentEmail@thanInDjango.settings"
    assert app_settings.EMAIL_FROM.value == "SomeDiffrentEmail@thanInDjango.settings"


@pytest.mark.settings_b
def test_if_no_email_in_REGISTER_MUTATION_FIELDS_send_email_is_false(
    app_settings, default_app_settings
):
    assert default_app_settings.SEND_ACTIVATION_EMAIL
    assert not app_settings.SEND_ACTIVATION_EMAIL


def test_override_find_jwt_hook(
    db_verified_user_status, app_settings, override_gqlauth
):
    def hook(info):
        return "invalid value"

    with override_gqlauth(app_settings.JWT_TOKEN_FINDER, hook):
        assert app_settings.JWT_TOKEN_FINDER(None) == "invalid value"
