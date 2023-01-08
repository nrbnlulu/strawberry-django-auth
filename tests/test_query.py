from gqlauth.core.types_ import GQLAuthErrors

from .conftest import USERNAME_FIELD
from .testCases import ArgTestCase


class TestQueries(ArgTestCase):
    query = """
        query MyQuery {
          authEntry {
            ... on GQLAuthError {
              code
              message
            }
            ... on AuthQueries {
              me {
                archived
                firstName
                dateJoined
                id
                isActive
                isStaff
                lastLogin
                isSuperuser
                lastName
                %s
                status {
                  archived
                  verified
                }
                verified
              }
            }
          }
        }
            """ % (
        USERNAME_FIELD
    )

    def test_me_authenticated(self, db_verified_user_status):

        executed = self.make_request(query=self.query, user_status=db_verified_user_status)
        assert executed["me"][USERNAME_FIELD] == db_verified_user_status.user.username_field

    def test_me_anonymous(self):
        executed = self.make_request(query=self.query, no_login_query=True)
        assert executed == {
            "code": GQLAuthErrors.INVALID_TOKEN.name,
            "message": GQLAuthErrors.INVALID_TOKEN.value,
        }

    def test_public_user_query(self, db_unverified_user_status, allow_login_not_verified):
        query = self.query.replace("me {", "publicUser {")
        executed = self.make_request(query=query, user_status=db_unverified_user_status)
        assert (
            executed["publicUser"][USERNAME_FIELD] == db_unverified_user_status.user.username_field
        )
        assert not executed["publicUser"]["verified"]
