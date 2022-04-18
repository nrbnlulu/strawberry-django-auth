from .settings import *

GRAPHQL_AUTH = {
    "ALLOW_DELETE_ACCOUNT": True,
    "ALLOW_LOGIN_NOT_VERIFIED": False,
    "REGISTER_MUTATION_FIELDS": {"email": str, "username": str},
    "UPDATE_MUTATION_FIELDS": ["first_name", "last_name"],
}

INSTALLED_APPS += ["tests"]

AUTH_USER_MODEL = "tests.CustomUser"
