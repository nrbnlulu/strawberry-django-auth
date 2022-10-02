from datetime import timedelta

from channels.testing import ChannelsLiveServerTestCase
from django.conf import settings
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport

from gqlauth.core.types_ import GQLAuthErrors
from gqlauth.jwt.types_ import TokenType
from tests.testCases import AbstractTestCase, ArgTestCase, AsyncArgTestCase


class GqlAuthFieldInSchemaMixin(AbstractTestCase):
    def test_expired_token(self, app_settings, db_verified_user_status):
        with self.override_gqlauth(app_settings.JWT_EXPIRATION_DELTA, timedelta(seconds=0)):
            res = self.make_request(
                user_status=db_verified_user_status, query=self.AUTH_REQUIRED_QUERY
            )
            assert res == {
                "code": GQLAuthErrors.EXPIRED_TOKEN.name,
                "message": GQLAuthErrors.EXPIRED_TOKEN.value,
            }

    batched_field_query = """
    query MyQuery {
      batchedField {
        ... on AppleType {
          __typename
          name
          isEaten
          color
        }
        ... on GQLAuthError {
          __typename
          code
          message
        }
      }
    }
    """

    def test_batched_field_fails(
        self, db_unverified_user_status, db_apple, allow_login_not_verified
    ):
        res = self.make_request(
            query=self.batched_field_query, user_status=db_unverified_user_status
        )
        assert res["code"] == GQLAuthErrors.NOT_VERIFIED.name

    def test_batched_field_success(self, db_verified_user_status, db_apple):
        res = self.make_request(query=self.batched_field_query, user_status=db_verified_user_status)
        assert res["name"] == db_apple.name


class TestGqlAuthRootFieldInSchema(GqlAuthFieldInSchemaMixin, ArgTestCase):
    ...


class TestGqlAuthRootFieldInSchemaAsync(GqlAuthFieldInSchemaMixin, AsyncArgTestCase):
    ...


class TestSubscriptions(ChannelsLiveServerTestCase, AbstractTestCase):
    def setUp(self) -> None:
        self.unverified_ws_transport = WebsocketsTransport(
            url=self.live_server_ws_url + "/graphql",
            # keep_alive_timeout=5
        )
        self.unverified_ws_client = Client(
            transport=self.unverified_ws_transport, fetch_schema_from_transport=False
        )

        user = self.verified_user_status_type()
        user.create()
        token = TokenType.from_user(user.user.obj).token
        self.verified_ws_transport = WebsocketsTransport(
            url=self.live_server_ws_url + "/graphql",
            headers={"AUTHORIZATION": f"JWT {token}"}
            # keep_alive_timeout=5
        )
        self.verified_ws_client = Client(
            transport=self.verified_ws_transport, fetch_schema_from_transport=False
        )

    query = """
    subscription MySubscription {
      count(target: 2) {
        ... on GQLAuthError {
          code
          message
        }
        ... on Integer {
          node
        }
      }
    }
    """

    def test_no_token(self):
        for res in self.unverified_ws_client.subscribe(document=gql(self.query)):
            assert res["count"]["code"] == GQLAuthErrors.INVALID_TOKEN.name

    @staticmethod
    def find_token(headers: dict):
        headers

    def test_with_token(self):

        with self.override_gqlauth(settings.GQL_AUTH.JWT_TOKEN_FINDER, self.find_token):
            for index, res in enumerate(
                self.verified_ws_client.subscribe(document=gql(self.query))
            ):
                assert res["count"]["node"] == index
