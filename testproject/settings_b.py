from .settings import *  # noqa F403

sys.path.append(str(Path(__file__).parent))  # noqa F403

GQL_AUTH = GqlAuthSettings(  # noqa F405
    LOGIN_REQUIRE_CAPTCHA=False,
    REGISTER_REQUIRE_CAPTCHA=False,
    SEND_ACTIVATION_EMAIL=False,
    ALLOW_DELETE_ACCOUNT=True,
    ALLOW_LOGIN_NOT_VERIFIED=False,
    LOGIN_REQUIRED_FIELDS=["phone_number", "password"],
    REGISTER_MUTATION_FIELDS={"phone_number": str},
    UPDATE_MUTATION_FIELDS=["first_name", "last_name"],
    EMAIL_FROM="SomeDiffrentEmail@thanInDjango.settings",
)

INSTALLED_APPS += ["customuser"]  # noqa F405

AUTH_USER_MODEL = "customuser.CustomPhoneNumberUser"
