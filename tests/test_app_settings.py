import pytest

from gqlauth.core.types_ import GQLAuthErrors
from gqlauth.settings_type import GqlAuthSettings
from tests.testCases import ArgTestCase

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


class TestOverrideHooks(ArgTestCase):
    def test_override_find_jwt_hook(self, db_verified_user_status, app_settings):
        def hook(info):
            return "invalid value"

        with self.override_gqlauth(app_settings.JWT_TOKEN_FINDER, hook):
            res = self.make_request(
                query=self.AUTH_REQUIRED_QUERY, user_status=db_verified_user_status
            )
            assert res["message"] == GQLAuthErrors.INVALID_TOKEN.value
