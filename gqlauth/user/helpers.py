from typing import TYPE_CHECKING, Optional

from django.contrib.auth import get_user_model

from gqlauth.core.types_ import ErrorCodes, MutationNormalOutput
from gqlauth.core.utils import UserProto

if TYPE_CHECKING:  # pragma: no cover
    pass

USER_MODEL = get_user_model()


def confirm_password(user: UserProto, input_) -> Optional[MutationNormalOutput]:
    if password := getattr(input_, "password", False):
        password_arg = "password"
    else:
        password = input_.old_password
        password_arg = "oldPassword"
    assert isinstance(password, str)
    if user.check_password(password):
        return None
    errors = {password_arg: ErrorCodes.INVALID_PASSWORD}
    return MutationNormalOutput(success=False, errors=errors)
