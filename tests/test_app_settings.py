import pytest

from gqlauth.settings_type import GqlAuthSettings

defaults = GqlAuthSettings()


def test_load_user_settings_from_django_settings(settings):
    assert defaults.EMAIL_FROM != "diffrent_than_gqlauth_default@cccc.com"
    assert settings.DEFAULT_FROM_EMAIL == "diffrent_than_gqlauth_default@cccc.com"


@pytest.mark.settings_b
def test_user_can_override_django_settings(settings):
    assert settings.DEFAULT_FROM_EMAIL != "SomeDiffrentEmail@thanInDjango.settings"
    assert settings.GQL_AUTH.EMAIL_FROM == "SomeDiffrentEmail@thanInDjango.settings"


@pytest.mark.settings_b
def test_if_no_email_in_REGISTER_MUTATION_FIELDS_send_email_is_false(settings):
    assert defaults.SEND_ACTIVATION_EMAIL
    assert not settings.GQL_AUTH.SEND_ACTIVATION_EMAIL


def test_override_find_jwt_hook(db_verified_user_status, app_settings, override_gqlauth):
    def hook(info):
        return "invalid value"

    with override_gqlauth(app_settings.JWT_TOKEN_FINDER, hook):
        assert app_settings.JWT_TOKEN_FINDER(None) == "invalid value"
