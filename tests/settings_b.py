from .settings import *  # noqa F403

GQL_AUTH = GqlAuthSettings(  # noqa F405
    LOGIN_REQUIRE_CAPTCHA=True,
    REGISTER_REQUIRE_CAPTCHA=True,
    ALLOW_DELETE_ACCOUNT=True,
    ALLOW_LOGIN_NOT_VERIFIED=False,
    REGISTER_MUTATION_FIELDS={"email": str, "username": str},
    UPDATE_MUTATION_FIELDS=["first_name", "last_name"],
    EMAIL_FROM="SomeDiffrentEmail@thanInDjango.settings",
)

INSTALLED_APPS += ["tests"]  # noqa F405

AUTH_USER_MODEL = "tests.CustomUser"
