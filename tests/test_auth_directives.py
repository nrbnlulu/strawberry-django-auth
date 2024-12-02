import pytest
from django.contrib.auth import get_user_model
from strawberry_django.permissions import DjangoNoPermission

from gqlauth.core.directives import IsVerified

USER_MODEL = get_user_model()


def test_is_verified_fails(db_unverified_user_status):
    with pytest.raises(DjangoNoPermission):
        IsVerified().resolve_for_user(
            lambda: True, db_unverified_user_status.user.obj, info=None, source=None
        )


def test_is_verified_success(db_verified_user_status):
    assert IsVerified().resolve_for_user(
        lambda: True, db_verified_user_status.user.obj, info=None, source=None
    )
