from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from gqlauth.core.constants import Error
from gqlauth.core.directives import (
    HasPermission,
    IsAuthenticated,
    IsVerified,
    SecondaryEmailRequired,
)
from gqlauth.core.utils import get_status
from tests.testCases import AsyncArgTestCase, TestBase

USER_MODEL = get_user_model()


class TestAuthDirectives(TestBase):
    def test_is_authenticated_fails(self):
        res = IsAuthenticated().resolve_permission(AnonymousUser(), None, None)
        assert res.code == Error.UNAUTHENTICATED
        assert res.message == Error.UNAUTHENTICATED.value

    def test_is_authenticated_success(self, db_verified_user_status):
        assert (
            IsAuthenticated().resolve_permission(db_verified_user_status.user.obj, None, None)
            is None
        )

    def test_is_verified_fails(self, db_unverified_user_status):
        res = IsVerified().resolve_permission(db_unverified_user_status.user.obj, None, None)
        assert res.code == Error.NOT_VERIFIED
        assert res.message == Error.NOT_VERIFIED.value

    def test_is_verified_success(self, db_verified_user_status):
        assert IsVerified().resolve_permission(db_verified_user_status.user.obj, None, None) is None

    def test_secondary_email_fails(self, db_verified_user_status):
        res = SecondaryEmailRequired().resolve_permission(
            db_verified_user_status.user.obj, None, None
        )
        assert res.code == Error.SECONDARY_EMAIL_REQUIRED
        assert res.message == Error.SECONDARY_EMAIL_REQUIRED.value

    def test_secondary_email_success(self, db_verified_user_status):
        user = db_verified_user_status.user.obj
        status = get_status(user)
        status.secondary_email = "someemafmsdkalfdmil@fdsa.com"
        status.save()
        status.refresh_from_db()
        assert SecondaryEmailRequired().resolve_permission(user, None, None) is None


class TestAppleQuery(AsyncArgTestCase):
    def test_has_permission_fails(self, db_verified_user_status):
        user = db_verified_user_status.user.obj
        perm = HasPermission(
            permissions=[
                "sample.can_eat",
            ]
        )
        assert perm.resolve_permission(user, None, None).code is Error.NO_SUFFICIENT_PERMISSIONS

    def test_has_permission_success(self, db_verified_user_status_can_eat):
        user = db_verified_user_status_can_eat.user.obj
        perm = HasPermission(
            permissions=[
                "sample.can_eat",
            ]
        )
        assert perm.resolve_permission(user, None, None) is None
