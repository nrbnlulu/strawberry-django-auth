from typing import TYPE_CHECKING, Optional, Union

from django.contrib.auth import get_user_model

from gqlauth.captcha.models import Captcha as CaptchaModel
from gqlauth.core.constants import Messages
from gqlauth.core.types_ import MutationNormalOutput
from gqlauth.core.utils import USER_UNION

if TYPE_CHECKING:  # pragma: no cover
    from gqlauth.user.resolvers import ObtainJSONWebTokenInput, RegisterMixin

USER_MODEL = get_user_model()


def confirm_password(user: USER_UNION, input_) -> Optional[MutationNormalOutput]:
    if password := getattr(input_, "password", False):
        password_arg = "password"
    else:
        password = input_.old_password
        password_arg = "oldPassword"
    assert isinstance(password, str)
    if user.check_password(password):
        return None
    errors = {password_arg: Messages.INVALID_PASSWORD}
    return MutationNormalOutput(success=False, errors=errors)


def check_captcha(input_: Union["RegisterMixin.RegisterInput", "ObtainJSONWebTokenInput"]):
    uuid = input_.identifier
    try:
        obj = CaptchaModel.objects.get(uuid=uuid)
    except CaptchaModel.DoesNotExist:
        return Messages.CAPTCHA_EXPIRED
    return obj.validate(input_.userEntry)
