from datetime import timedelta

from gqlauth.core.types_ import GqlAuthError
from tests.testCases import AbstractTestCase, ArgTestCase, AsyncArgTestCase


class GqlAuthRootFieldInSchemaMixin(AbstractTestCase):
    def make_query(self) -> str:
        return """
        query {
          authEntry {
            node {
              me {
                verified
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

    def test_expired_token(self, app_settings, db_verified_user_status):
        with self.override_gqlauth(app_settings.JWT_EXPIRATION_DELTA, timedelta(seconds=0)):
            res = self.make_request(user_status=db_verified_user_status, query=self.make_query())
            assert res == {
                "node": None,
                "error": {
                    "code": GqlAuthError.EXPIRED_TOKEN.name,
                    "message": GqlAuthError.EXPIRED_TOKEN.value,
                },
                "success": False,
            }


class TestGqlAuthRootFieldInSchema(GqlAuthRootFieldInSchemaMixin, ArgTestCase):
    ...


class TestGqlAuthRootFieldInSchemaAsync(GqlAuthRootFieldInSchemaMixin, AsyncArgTestCase):
    ...
