from typing import TYPE_CHECKING, Optional, Union

from django.contrib.auth import get_user_model

from gqlauth.captcha.models import Captcha as CaptchaModel
from gqlauth.core.constants import Messages
from gqlauth.core.types_ import MutationNormalOutput
from gqlauth.core.utils import get_status

if TYPE_CHECKING:
    from gqlauth.user.resolvers import ObtainJSONWebTokenInput, RegisterMixin

USER_MODEL = get_user_model()


def confirm_password(user: USER_MODEL, input_) -> Optional[MutationNormalOutput]:
    if password := getattr(input_, "password", False):
        password_arg = "password"
    else:
        password = input_.old_password
        password_arg = "oldPassword"

    if user.check_password(password):
        return None
    errors = {password_arg: Messages.INVALID_PASSWORD}
    return MutationNormalOutput(success=False, errors=errors)


def check_secondary_email(user: USER_MODEL) -> Optional[MutationNormalOutput]:
    if (status := get_status(user)) and status.secondary_email:
        return None
    return MutationNormalOutput(success=False, errors=Messages.SECONDARY_EMAIL_REQUIRED)


def check_captcha(input_: Union["RegisterMixin.RegisterInput", "ObtainJSONWebTokenInput"]):
    uuid = input_.identifier
    try:
        obj = CaptchaModel.objects.get(uuid=uuid)
    except CaptchaModel.DoesNotExist:
        return Messages.CAPTCHA_EXPIRED
    return obj.validate(input_.userEntry)
