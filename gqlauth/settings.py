import warnings

from django.conf import settings as django_settings

from gqlauth.settings_type import GqlAuthSettings

gqlauth_settings: GqlAuthSettings

if user_settings := getattr(django_settings, "GQL_AUTH", False):
    if isinstance(user_settings, GqlAuthSettings):
        gqlauth_settings = user_settings

    else:
        raise Exception(
            f"GQL_AUTH settings should be of type "
            f"{GqlAuthSettings}, but you provided {type(user_settings)}"
        )

else:  # pragma: no cover
    warnings.warn("You have not provided any custom gql auth settings falling back to defaults")
    gqlauth_settings = GqlAuthSettings()
