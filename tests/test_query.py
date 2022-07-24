from django.contrib.auth import get_user_model
from strawberry.utils.str_converters import to_camel_case

from .testCases import ArgTestCase

UserModel = get_user_model()
USERNAME_FIELD = to_camel_case(UserModel.USERNAME_FIELD)


class TestQueries(ArgTestCase):
    query = """
    query {{
        me {{
            {}
        }}
    }}
    """.format(
        USERNAME_FIELD
    )

    def test_me_authenticated(self, db_verified_user_status):

        executed = self.make_request(query=self.query, user_status=db_verified_user_status)
        assert executed[USERNAME_FIELD]

    def test_me_anonymous(self):
        executed = self.make_request(query=self.query, no_login_query=True)
        assert not executed

    def test_public_user_query(self, db_unverified_user_status, allow_login_not_verified):
        query = """
        query {
            publicUser {
                verified
            }
        }
        """
        executed = self.make_request(query=query, user_status=db_unverified_user_status)
        assert executed == {"verified": False}
