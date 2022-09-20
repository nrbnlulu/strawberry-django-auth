from datetime import timedelta

from gqlauth.core.types_ import GQLAuthErrors
from tests.testCases import AbstractTestCase, ArgTestCase, AsyncArgTestCase


class GqlAuthRootFieldInSchemaMixin(AbstractTestCase):
    def test_expired_token(self, app_settings, db_verified_user_status):
        with self.override_gqlauth(app_settings.JWT_EXPIRATION_DELTA, timedelta(seconds=0)):
            res = self.make_request(
                user_status=db_verified_user_status, query=self.AUTH_REQUIRED_QUERY
            )
            assert res == {
                "code": GQLAuthErrors.EXPIRED_TOKEN.name,
                "message": GQLAuthErrors.EXPIRED_TOKEN.value,
            }


class TestGqlAuthRootFieldInSchema(GqlAuthRootFieldInSchemaMixin, ArgTestCase):
    ...


class TestGqlAuthRootFieldInSchemaAsync(GqlAuthRootFieldInSchemaMixin, AsyncArgTestCase):
    ...
