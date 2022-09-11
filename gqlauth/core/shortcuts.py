from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from gqlauth.models import UserStatus

UserModel = get_user_model()


def get_user_by_email(email: str):
    """
    get user by email or by secondary email
    raise ObjectDoesNotExist
    """
    try:
        user = UserModel._default_manager.get(**{UserModel.EMAIL_FIELD: email})
        return user
    except ObjectDoesNotExist:
        status = UserStatus._default_manager.get(secondary_email=email)
        return status.user
