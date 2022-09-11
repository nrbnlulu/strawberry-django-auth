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
from tests.testCases import ArgTestCase, Query, TestBase

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

    def test_has_permission_fails(self, db_verified_user_status):
        user = db_verified_user_status.user.obj
        perm = HasPermission(
            permissions=[
                "sample.can_eat",
            ]
        )

        class FakePath:
            key = "test"

        class FakeInfo:
            path = FakePath

        assert perm.resolve_permission(user, None, FakeInfo).code is Error.NO_SUFFICIENT_PERMISSIONS

    def test_has_permission_success(self, db_verified_user_status_can_eat):
        user = db_verified_user_status_can_eat.user.obj
        perm = HasPermission(
            permissions=[
                "sample.can_eat",
            ]
        )
        assert perm.resolve_permission(user, None, None) is None


class TestAuthDirectivesInSchema(ArgTestCase):
    def make_query(self) -> Query:
        return Query(
            """
        query MyQuery {
          authEntry {
            data {
              apples {
                color
                isEaten
                name
              }
            }
            errors {
              fieldErrors {
                code
                field
                message
              }
              nonFieldErrors {
                code
                message
              }
            }
          }
        }
        """
        )

    def test_not_verified_fails(self, db_unverified_user_status, app_settings):
        app_settings.ALLOW_LOGIN_NOT_VERIFIED = True
        res = self.make_request(query=self.make_query(), user_status=db_unverified_user_status)
        assert res == {
            "data": {"apples": None},
            "errors": {
                "fieldErrors": [
                    {
                        "code": "NOT_VERIFIED",
                        "field": "apples",
                        "message": "Please verify your account.",
                    }
                ],
                "nonFieldErrors": [],
            },
        }

    def test_verified_success(self, db_verified_user_status):
        res = self.make_request(query=self.make_query(), user_status=db_verified_user_status)
        assert res == {"data": {"apples": []}, "errors": {"fieldErrors": [], "nonFieldErrors": []}}
