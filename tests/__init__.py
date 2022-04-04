from django.test import override_settings
from django.conf import settings as django_settings
from datetime import timedelta

GQL_AUTH_DEF = {
    # if allow to login without verification,
    # the register mutation will return a token
    "ALLOW_LOGIN_NOT_VERIFIED": True,
    # mutations fields options
    "LOGIN_ALLOWED_FIELDS": ["email", "username"],
    "ALLOW_LOGIN_WITH_SECONDARY_EMAIL": True,
    # required fields on register, plus password1 and password2,
    # can be a dict like UPDATE_MUTATION_FIELDS setting
    "REGISTER_MUTATION_FIELDS": ["email", "username"],
    "REGISTER_MUTATION_FIELDS_OPTIONAL": [],
    # optional fields on update account, can be list of fields
    "UPDATE_MUTATION_FIELDS": {"first_name": "String", "last_name": "String"},
    # tokens
    "EXPIRATION_ACTIVATION_TOKEN": timedelta(days=7),
    "EXPIRATION_PASSWORD_RESET_TOKEN": timedelta(hours=1),
    "EXPIRATION_SECONDARY_EMAIL_ACTIVATION_TOKEN": timedelta(hours=1),
    "EXPIRATION_PASSWORD_SET_TOKEN": timedelta(hours=1),
    # email stuff
    "EMAIL_FROM": getattr(django_settings, "DEFAULT_FROM_EMAIL", "test@email.com"),
    "SEND_ACTIVATION_EMAIL": True,
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

GRAPHQL_JWT_DEF = {
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
    "JWT_ALLOW_ANY_CLASSES": [
        # mutations
        "gqlauth.mutations.Register",
        "gqlauth.mutations.VerifyAccount",
        "gqlauth.mutations.ResendActivationEmail",
        "gqlauth.mutations.SendPasswordResetEmail",
        "gqlauth.mutations.PasswordReset",
        "gqlauth.mutations.ObtainJSONWebToken",
        "gqlauth.mutations.VerifyToken",
        "gqlauth.mutations.RefreshToken",
        "gqlauth.mutations.RevokeToken",
        "gqlauth.mutations.VerifySecondaryEmail"
        # relay
        "gqlauth.relay.Register",
        "gqlauth.relay.VerifyAccount",
        "gqlauth.relay.ResendActivationEmail",
        "gqlauth.relay.SendPasswordResetEmail",
        "gqlauth.relay.PasswordReset",
        "gqlauth.relay.ObtainJSONWebToken",
        "gqlauth.relay.VerifyToken",
        "gqlauth.relay.RefreshToken",
        "gqlauth.relay.RevokeToken",
        "gqlauth.relay.VerifySecondaryEmail",
    ],
}

SETTING_B = {
        "ALLOW_DELETE_ACCOUNT": True,
        "REGISTER_MUTATION_FIELDS": {"email": str, "username": str},
        "UPDATE_MUTATION_FIELDS": ["first_name", "last_name"],
        "ALLOW_LOGIN_NOT_VERIFIED": False,
    }

