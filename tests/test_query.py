from .testCases import ArgTestCase


class TestQueries(ArgTestCase):
    def test_me_authenticated(self, db_verified_user_status):
        query = """
        query {
            me {
                username
            }
        }
        """
        executed = self.make_request(query=query, user_status=db_verified_user_status)
        assert executed["username"]

    def test_me_anonymous(self):
        query = """
        query {
            me {
                username
            }
        }
        """
        executed = self.make_request(query=query, no_login_query=True)
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
