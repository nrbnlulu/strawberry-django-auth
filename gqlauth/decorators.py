from functools import wraps

from gqlauth.utils import g_user

from .constants import Messages
from .exceptions import PermissionDenied, WrongUsage


def login_required(fn):
    """
    If the user is registered
    """

    @wraps(fn)
    def wrapper(src, info, **kwargs):
        if g_user(info).is_authenticated:
            return fn(src, info, **kwargs)
        else:
            return src.output(success=False, errors=Messages.UNAUTHENTICATED)

    return wrapper


def verification_required(fn):
    """
    if the user was approved
    """

    @wraps(fn)
    @login_required
    def wrapper(src, info, **kwargs):
        if not g_user(info).status.verified:
            return src.output(success=False, errors=Messages.NOT_VERIFIED)
        return fn(src, info, **kwargs)

    return wrapper


def secondary_email_required(fn):
    @wraps(fn)
    @verification_required
    def wrapper(src, info, **kwargs):
        if not g_user(info).status.secondary_email:
            return src.output(success=False, errors=Messages.SECONDARY_EMAIL_REQUIRED)
        return fn(src, info, **kwargs)

    return wrapper


def password_confirmation_required(fn):
    @wraps(fn)
    def wrapper(src, info, **kwargs):
        try:
            password_arg = next(i for i in kwargs.keys() if i in ["password", "oldPassword"])
            password = kwargs[password_arg]
        except Exception:
            raise WrongUsage(
                """
                @password_confirmation is supposed to be used on
                user with 'password' or 'old_password' field required.
                """
            )
        user = g_user(info)
        if user.check_password(password):
            return fn(src, info, **kwargs)
        errors = {password_arg: Messages.INVALID_PASSWORD}
        return src.output(success=False, errors=errors)

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
