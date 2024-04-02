import pytest

from .conftest import CC_USERNAME_FIELD


@pytest.fixture
def query():
    return """
query MyQuery {
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
        """ % (CC_USERNAME_FIELD)


def test_me_authenticated_success(query, db_verified_user_status, verified_schema):
    executed = verified_schema.execute(query=query)
    assert not executed.errors
    executed = executed.data["me"]
    assert executed[CC_USERNAME_FIELD] == db_verified_user_status.user.username_field


def test_me_anonymous_fail(query, anonymous_schema):
    executed = anonymous_schema.execute(query=query)
    assert "Unauthenticated" in executed.errors[0].message


def test_public_user_query_return_none(query, anonymous_schema):
    query = query.replace("me {", "publicUser {")
    executed = anonymous_schema.execute(query=query)
    assert not executed.errors


def test_public_user_query_return_success(query, unverified_schema):
    query = query.replace("me {", "publicUser {")
    res = unverified_schema.execute(query=query)
    assert not res.errors
    res = res.data["publicUser"]
    assert res[CC_USERNAME_FIELD] == unverified_schema.us_type.user.username_field
    assert not res["verified"]
