from functools import wraps

from strawberry.types import Info

from gqlauth.utils import g_info, g_user

from .bases.types_ import MutationNormalOutput
from .constants import Messages
from .exceptions import PermissionDenied


def login_required(fn):
    """
    If the user is registered
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        info = g_info(args)
        if g_user(info).is_authenticated:
            return fn(*args, **kwargs)
        else:
            return MutationNormalOutput(success=False, errors=Messages.UNAUTHENTICATED)

    return wrapper


def verification_required(fn):
    """
    if the user was approved
    """

    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        info = g_info(args)
        if not g_user(info).status.verified:
            return MutationNormalOutput(success=False, errors=Messages.NOT_VERIFIED)
        return fn(*args, **kwargs)

    return wrapper


def secondary_email_required(fn):
    @wraps(fn)
    @verification_required
    def wrapper(*args, **kwargs):
        info = g_info(args)
        if not g_user(info).status.secondary_email:
            return MutationNormalOutput(success=False, errors=Messages.SECONDARY_EMAIL_REQUIRED)
        return fn(*args, **kwargs)

    return wrapper


def _password_confirmation_required(fn):
    """
    not to be used publicly.
    """

    @wraps(fn)
    def wrapper(src, info: Info, input_):
        if password := getattr(input_, "password", False):
            password_arg = "password"
        else:
            password = input_.old_password
            password_arg = "oldPassword"

        user = g_user(info)
        if user.check_password(password):
            return fn(src, info, input_)
        errors = {password_arg: Messages.INVALID_PASSWORD}
        return MutationNormalOutput(success=False, errors=errors)

    return wrapper


def allowed_permissions(roles: list):
    """
    checks a list of roles if it applies to a user
    verification required by default.
    """

    def decorator(fn):
        @wraps(fn)
        @verification_required
        def wrapper(src, info, **kwargs):
            user = g_user(info)
            if roles in user.user_permissions.all():
                return user
            raise PermissionDenied(
                f"required permissions are {roles} user {user} is missing "
                f"{[role for role in roles if role not in user.user_permissions.all()]}"
            )

        return wrapper

    return decorator
