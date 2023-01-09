from django.contrib.auth import get_user_model

from gqlauth.core.directives import IsVerified

USER_MODEL = get_user_model()


def test_is_verified_fails(db_unverified_user_status):
    assert not IsVerified().check_condition(None, None, db_unverified_user_status.user.obj)


def test_is_verified_success(db_verified_user_status):
    assert IsVerified().check_condition(None, None, db_verified_user_status.user.obj)
