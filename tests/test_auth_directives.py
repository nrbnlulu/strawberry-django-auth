from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from gqlauth.core.directives import HasPermission, IsAuthenticated, IsVerified
from gqlauth.core.types_ import GqlAuthError
from tests.testCases import AbstractTestCase, ArgTestCase, AsyncArgTestCase

USER_MODEL = get_user_model()


class TestAuthDirectives(ArgTestCase):
    def test_is_authenticated_fails(self):
        res = IsAuthenticated().resolve_permission(AnonymousUser(), None, None)
        assert res.code == GqlAuthError.UNAUTHENTICATED
        assert res.message == GqlAuthError.UNAUTHENTICATED.value

    def test_is_authenticated_success(self, db_verified_user_status):
        assert (
            IsAuthenticated().resolve_permission(db_verified_user_status.user.obj, None, None)
            is None
        )

    def test_is_verified_fails(self, db_unverified_user_status):
        res = IsVerified().resolve_permission(db_unverified_user_status.user.obj, None, None)
        assert res.code == GqlAuthError.NOT_VERIFIED
        assert res.message == GqlAuthError.NOT_VERIFIED.value

    def test_is_verified_success(self, db_verified_user_status):
        assert (
            IsVerified().resolve_permission(
                db_verified_user_status.user.obj, None, None, None, None
            )
            is None
        )

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

        assert (
            perm.resolve_permission(user, None, FakeInfo).code
            is GqlAuthError.NO_SUFFICIENT_PERMISSIONS
        )

    def test_has_permission_success(self, db_verified_user_status_can_eat):
        user = db_verified_user_status_can_eat.user.obj
        perm = HasPermission(
            permissions=[
                "sample.can_eat",
            ]
        )
        assert perm.resolve_permission(user, None, None) is None


class IsVerifiedDirectivesInSchemaMixin(AbstractTestCase):
    def make_query(self) -> str:
        return """
      query MyQuery {
          authEntry {
            node {
              apples {
                node {
                  color
                  name
                  isEaten
                }
                error{
                  message
                  code
                }
                success
              }
            }
            error{
              code
              message
            }
            success
          }
        }
        """

    def test_not_verified_fails(
        self, db_apple, db_unverified_user_status, allow_login_not_verified
    ):
        res = self.make_request(query=self.make_query(), user_status=db_unverified_user_status)
        assert res == {
            "error": None,
            "node": {
                "apples": {
                    "error": {"code": "NOT_VERIFIED", "message": "Please verify your account."},
                    "node": None,
                    "success": False,
                }
            },
            "success": True,
        }

    def test_verified_success(self, db_apple, db_verified_user_status):
        res = self.make_request(query=self.make_query(), user_status=db_verified_user_status)
        assert res == {
            "error": None,
            "node": {
                "apples": {
                    "error": None,
                    "node": [
                        {
                            "color": db_apple.color,
                            "isEaten": db_apple.is_eaten,
                            "name": db_apple.name,
                        }
                    ],
                    "success": True,
                }
            },
            "success": True,
        }


class TestIsVerifiedDirectivesInSchema(IsVerifiedDirectivesInSchemaMixin, ArgTestCase):
    ...


class TestIsVerifiedDirectivesInSchemaAsync(IsVerifiedDirectivesInSchemaMixin, AsyncArgTestCase):
    ...


class HasPermissionDirectiveInSchemaMixin(AbstractTestCase):
    def make_query(self, apple_id):
        return (
            """
             mutation MyMutation {
              authEntry {
                node {
                  eatApple(appleId: %s) {
                    node {
                      color
                      name
                      isEaten
                    }
                    error {
                      code
                      message
                    }
                    success
                  }
                }
                error {
                  code
                  message
                }
                success
              }
            }
                """
            % apple_id
        )

    def test_has_permission_fails(self, db_apple, db_verified_user_status):
        username = db_verified_user_status.user.username_field
        res = self.make_request(self.make_query(db_apple.id), db_verified_user_status)
        assert res == {
            "error": None,
            "node": {
                "eatApple": {
                    "error": {
                        "code": "NO_SUFFICIENT_PERMISSIONS",
                        "message": f"User {username}, has not "
                        "sufficient permissions for "
                        "eatApple",
                    },
                    "node": None,
                    "success": False,
                }
            },
            "success": True,
        }

    def test_has_permission_success(self, db_apple, db_verified_user_status_can_eat):
        res = self.make_request(self.make_query(db_apple.id), db_verified_user_status_can_eat)
        assert res == {
            "error": None,
            "node": {
                "eatApple": {
                    "error": None,
                    "node": {"color": db_apple.color, "isEaten": True, "name": db_apple.name},
                    "success": True,
                }
            },
            "success": True,
        }
        db_apple.refresh_from_db()
        assert db_apple.is_eaten


class TestPermissionArgSchema(HasPermissionDirectiveInSchemaMixin, ArgTestCase):
    ...


class TestPermissionAsync(HasPermissionDirectiveInSchemaMixin, AsyncArgTestCase):
    ...
