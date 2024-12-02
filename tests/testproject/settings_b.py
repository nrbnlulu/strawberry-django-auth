from typing import Optional

from strawberry.annotation import StrawberryAnnotation
from strawberry.types.field import StrawberryField

from gqlauth.settings_type import DjangoSetting
from tests.testproject.settings import *  # noqa F403

sys.path.append(str(Path(__file__).parent))  # noqa F403
phone_number_field = StrawberryField(
    python_name="phone_number", default=None, type_annotation=StrawberryAnnotation(str)
)
password_field = StrawberryField(
    python_name="password", default=None, type_annotation=StrawberryAnnotation(str)
)

GQL_AUTH = GqlAuthSettings(  # noqa F405
    LOGIN_REQUIRE_CAPTCHA=False,
    REGISTER_REQUIRE_CAPTCHA=False,
    SEND_ACTIVATION_EMAIL=False,
    ALLOW_DELETE_ACCOUNT=True,
    ALLOW_LOGIN_NOT_VERIFIED=False,
    ALLOW_PASSWORDLESS_REGISTRATION=True,
    LOGIN_FIELDS={
        phone_number_field,
        password_field,
        StrawberryField(
            python_name="first_name",
            default=None,
            type_annotation=StrawberryAnnotation(Optional[str]),
        ),
        StrawberryField(
            python_name="last_name",
            default=None,
            type_annotation=StrawberryAnnotation(Optional[str]),
        ),
    },
    REGISTER_MUTATION_FIELDS={
        phone_number_field,
    },
    EMAIL_FROM=DjangoSetting.override("SomeDiffrentEmail@thanInDjango.settings"),
    JWT_PAYLOAD_PK=phone_number_field,
)

INSTALLED_APPS += ["customuser"]  # noqa F405

AUTH_USER_MODEL = "customuser.CustomPhoneNumberUser"
