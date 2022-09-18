from django.contrib.auth import get_user_model
from strawberry.utils.str_converters import to_camel_case

from gqlauth.core.types_ import GqlAuthError

from .testCases import ArgTestCase

UserModel = get_user_model()
USERNAME_FIELD = to_camel_case(UserModel.USERNAME_FIELD)


class TestQueries(ArgTestCase):
    query = """
        query MyQuery {
          authEntry {
            node {
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
                secondaryEmail
                status {
                  archived
                  secondaryEmail
                  verified
                }
                verified
              }
            }
            success
            error {
              code
              message
            }
          }
        }
            """ % (
        USERNAME_FIELD
    )

    def test_me_authenticated(self, db_verified_user_status):

        executed = self.make_request(query=self.query, user_status=db_verified_user_status)
        assert executed["node"]["me"][USERNAME_FIELD] == db_verified_user_status.user.username_field

    def test_me_anonymous(self):
        executed = self.make_request(query=self.query, no_login_query=True)
        assert executed != {
            "node": None,
            "success": False,
            "error": {
                "code": GqlAuthError.INVALID_TOKEN,
                "message": GqlAuthError.INVALID_TOKEN.value,
            },
        }

    def test_public_user_query(self, db_unverified_user_status, allow_login_not_verified):
        query = (
            """
        query MyQuery {
          authEntry {
            success
            node {
              publicUser {
                %s
                verified
              }
            }
            error {
              code
              message
            }
          }
        }
        """
            % USERNAME_FIELD
        )
        executed = self.make_request(query=query, user_status=db_unverified_user_status)
        assert executed == {
            "success": True,
            "node": {
                "publicUser": {
                    USERNAME_FIELD: db_unverified_user_status.user.username_field,
                    "verified": False,
                }
            },
            "error": None,
        }
