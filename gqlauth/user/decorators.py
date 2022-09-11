from functools import wraps

from strawberry.types import Info

from gqlauth.core.constants import Messages
from gqlauth.core.types_ import MutationNormalOutput
from gqlauth.core.utils import get_user


def _password_confirmation_required(fn):
    @wraps(fn)
    def wrapper(src, info: Info, input_):
        if password := getattr(input_, "password", False):
            password_arg = "password"
        else:
            password = input_.old_password
            password_arg = "oldPassword"

        user = get_user(info)
        if user.check_password(password):
            return fn(src, info, input_)
        errors = {password_arg: Messages.INVALID_PASSWORD}
        return MutationNormalOutput(success=False, errors=errors)

    return wrapper
