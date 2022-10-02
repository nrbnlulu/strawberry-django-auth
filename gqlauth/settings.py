import dataclasses
from typing import get_args
import warnings

from django.conf import settings as django_settings

from gqlauth.settings_type import DjangoSetting, GqlAuthSettings, ImportString

gqlauth_settings: GqlAuthSettings

if user_settings := getattr(django_settings, "GQL_AUTH", False):
    if isinstance(user_settings, GqlAuthSettings):
        gqlauth_settings = user_settings

    else:
        raise Exception(
            f"GQL_AUTH settings should be of type "
            f"{GqlAuthSettings}, but you provided {type(user_settings)}"
        )

else:
    warnings.warn("You have not provided any custom gql auth settings falling back to defaults")
    gqlauth_settings = GqlAuthSettings()

defaults = GqlAuthSettings()
# retain django_settings
for field in dataclasses.fields(gqlauth_settings):
    name = field.name
    value = getattr(gqlauth_settings, name)
    if DjangoSetting in get_args(field.type) and value is getattr(defaults, name):
        setattr(gqlauth_settings, name, value())
    elif (f_type := getattr(field.type, "__origin__", None)) and f_type is ImportString:
        assert isinstance(value, ImportString)
        setattr(gqlauth_settings, name, value.preform_import())

del defaults
