"""
Settings for gqlauth are all namespaced in the GQL_AUTH setting.
For example your project's `settings.py` file might look like this:
GQL_AUTH = {
    "LOGIN_OPTIONAL_FIELDS": ["email", "username"],
    "SEND_ACTIVATION_EMAIL": True,
}
This module provides the `gqlauth_settings` object, that is used to access
strawberry settings, checking for user settings first, then falling
back to the defaults.
"""

from django.conf import settings as django_settings
from django.test.signals import setting_changed

from datetime import timedelta

# Copied shamelessly from Graphene / Django REST Framework

DEFAULTS = {
    # if allow logging in without verification,
    # the register mutation will return a token
    "ALLOW_LOGIN_NOT_VERIFIED": False,
    # mutation fields options
    "LOGIN_OPTIONAL_FIELDS": [],
    "LOGIN_REQUIRE_CAPTCHA": True,
    "LOGIN_REQUIRED_FIELDS": ['username', 'password'],
    # required fields on register, plus password1 and password2,
    # can be a dict like UPDATE_MUTATION_FIELDS setting
    "REGISTER_MUTATION_FIELDS": ["email", "username"],
    "REGISTER_MUTATION_FIELDS_OPTIONAL": [],
    "REGISTER_REQUIRE_CAPTCHA": True,
    "CAPTCHA_TEXT_FACTORY": None,
    # captcha stuff
    "CAPTCHA_EXPIRATION_DELTA": timedelta(seconds=120),
    "CAPTCHA_MAX_RETRIES": 5,
    # optional fields on update account, can be list of fields
    "UPDATE_MUTATION_FIELDS": {"first_name": str, "last_name": str},
    # tokens
    "EXPIRATION_ACTIVATION_TOKEN": timedelta(days=7),
    "EXPIRATION_PASSWORD_RESET_TOKEN": timedelta(hours=1),
    "EXPIRATION_SECONDARY_EMAIL_ACTIVATION_TOKEN": timedelta(hours=1),
    "EXPIRATION_PASSWORD_SET_TOKEN": timedelta(hours=1),
    # email stuff
    "EMAIL_FROM": getattr(django_settings, "DEFAULT_FROM_EMAIL", "test@email.com"),
    "SEND_ACTIVATION_EMAIL": False,
    # client: example.com/activate/token
    "ACTIVATION_PATH_ON_EMAIL": "activate",
    "ACTIVATION_SECONDARY_EMAIL_PATH_ON_EMAIL": "activate",
    # client: example.com/password-set/token
    "PASSWORD_SET_PATH_ON_EMAIL": "password-set",
    # client: example.com/password-reset/token
    "PASSWORD_RESET_PATH_ON_EMAIL": "password-reset",
    # email subjects templates
    "EMAIL_SUBJECT_ACTIVATION": "email/activation_subject.txt",
    "EMAIL_SUBJECT_ACTIVATION_RESEND": "email/activation_subject.txt",
    "EMAIL_SUBJECT_SECONDARY_EMAIL_ACTIVATION": "email/activation_subject.txt",
    "EMAIL_SUBJECT_PASSWORD_SET": "email/password_set_subject.txt",
    "EMAIL_SUBJECT_PASSWORD_RESET": "email/password_reset_subject.txt",
    # email templates
    "EMAIL_TEMPLATE_ACTIVATION": "email/activation_email.html",
    "EMAIL_TEMPLATE_ACTIVATION_RESEND": "email/activation_email.html",
    "EMAIL_TEMPLATE_SECONDARY_EMAIL_ACTIVATION": "email/activation_email.html",
    "EMAIL_TEMPLATE_PASSWORD_SET": "email/password_set_email.html",
    "EMAIL_TEMPLATE_PASSWORD_RESET": "email/password_reset_email.html",
    "EMAIL_TEMPLATE_VARIABLES": {},
    # query stuff
    "USER_NODE_EXCLUDE_FIELDS": ["password", "is_superuser"],
    "USER_NODE_FILTER_FIELDS": {
        "email": ["exact"],
        "username": ["exact", "icontains", "istartswith"],
        "is_active": ["exact"],
        "status__archived": ["exact"],
        "status__verified": ["exact"],
        "status__secondary_email": ["exact"],
    },
    # turn is_active to False instead
    "ALLOW_DELETE_ACCOUNT": False,
    # string path for email function wrapper, see the testproject example
    "EMAIL_ASYNC_TASK": False,
    # mutation error type
    "CUSTOM_ERROR_TYPE": None,
    # registration with no password
    "ALLOW_PASSWORDLESS_REGISTRATION": False,
    "SEND_PASSWORD_SET_EMAIL": False,
}


class GraphQLAuthSettings(object):
    """
    A settings object, that allows API settings to be accessed as properties.
    For example:
        from gqlauth.settings import settings
        print(settings)
    """

    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(django_settings, "GQL_AUTH", {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid gqlauth setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Cache the result
        setattr(self, attr, val)
        return val


gqlauth_settings = GraphQLAuthSettings(None, DEFAULTS)


def reload_gqlauth_settings(*args, **kwargs):
    global gqlauth_settings
    setting, value = kwargs["setting"], kwargs["value"]
    if setting == "GQL_AUTH":
        gqlauth_settings = GraphQLAuthSettings(value, DEFAULTS)


setting_changed.connect(reload_gqlauth_settings)
