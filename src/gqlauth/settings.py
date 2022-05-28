from django.conf import settings as django_settings
from gqlauth.settings_type import GqlAuthSettings
from django.test.signals import setting_changed

import logging

logger = logging.getLogger(__name__)

gqlauth_settings: GqlAuthSettings = None

if user_settings := getattr(django_settings, "GQL_AUTH", False):
    if isinstance(user_settings, GqlAuthSettings):
        gqlauth_settings = user_settings
    else:
        raise Exception(
            f"GQL_AUTH settings should be of type "
            f"{GqlAuthSettings}, but you provided {type(user_settings)}"
        )

else:
    logger.warning(
        "GQL AUTH: You have not provided "
        "any custom gql auth settings falling back to defaults"
    )
    gqlauth_settings = GqlAuthSettings()


def reload_gqlauth_settings(*args, **kwargs):
    global gqlauth_settings
    setting, value = kwargs["setting"], kwargs["value"]
    if setting == "GQL_AUTH":
        gqlauth_settings = GqlAuthSettings(**value)


setting_changed.connect(reload_gqlauth_settings)
