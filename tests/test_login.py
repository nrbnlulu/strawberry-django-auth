import pytest
from strawberry.types import ExecutionResult
from strawberry.utils.str_converters import to_camel_case

from gqlauth.captcha.models import Captcha
from gqlauth.core.constants import Messages
from gqlauth.settings_type import GqlAuthSettings

from .conftest import SchemaHelper, UserModel, UserStatusType


@pytest.fixture
def login_query(request):
    app_settings: GqlAuthSettings = request.getfixturevalue("app_settings")
    captcha: Captcha = request.getfixturevalue("captcha")

    def inner(user_status: UserStatusType, user_entry: str = "") -> str:
        user = user_status.user
        arguments = (
            f'{to_camel_case(UserModel.USERNAME_FIELD)}: "{user.username_field}",'
            f' password: "{user.password}"'
        )
        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            arguments += f', identifier: "{captcha.uuid}" ,userEntry: "{user_entry or captcha.text}"'

        return """
           mutation {
           tokenAuth(%s)
                  {
            errors
            success
            refreshToken {
              created
              isExpired
              expiresAt
              token
              revoked
            }
            token {
              token
              payload {
                exp
                origIat
              }
            }
            user {
              archived
              dateJoined
              firstName
              isActive
              id
              isStaff
              isSuperuser
              lastLogin
              lastName
              logentrySet {
                pk
              }
              status {
                archived
                verified
              }
              verified
            }
          }
        }
           """ % (arguments)

    return inner


@pytest.fixture()
def archived_schema(db_archived_user_status, rf) -> SchemaHelper:
    return SchemaHelper.create(rf=rf, us_type=db_archived_user_status)


def default_test(res: ExecutionResult):
    assert not res.errors
    res = res.data["tokenAuth"]
    assert res["success"]
    assert not res["errors"]
    assert res["refreshToken"]["token"]
    assert res["token"]["token"]
    assert res["user"]["lastLogin"]


def test_archived_user_becomes_active_on_login(
    db_archived_user_status, login_query, archived_schema
):
    user = db_archived_user_status.user.obj
    assert user.status.archived
    res = archived_schema.execute(login_query(db_archived_user_status))
    user.refresh_from_db()
    assert not user.status.archived
    default_test(res)


def test_login_success(
    verified_schema, unverified_schema, allow_login_not_verified, login_query
):
    res = verified_schema.execute(login_query(verified_schema.us_type))
    default_test(res)


def test_login_with_ci_mode_with_invalid_captcha_success(
    verified_schema,
    allow_login_not_verified,
    login_query,
    override_gqlauth,
    app_settings: GqlAuthSettings,
) -> None:
    if not app_settings.LOGIN_REQUIRE_CAPTCHA:
        pytest.skip("This tests requires captcha to be enabled")
    with override_gqlauth(app_settings.CI_MODE, True):
        query = login_query(verified_schema.us_type, user_entry="invalid")
        res = verified_schema.execute(query)
        default_test(res)


def test_not_verified_fails(unverified_schema, login_query):
    res = unverified_schema.execute(login_query(unverified_schema.us_type))
    res = res.data["tokenAuth"]
    assert not res["success"]
    assert res["errors"]["nonFieldErrors"] == Messages.NOT_VERIFIED
    assert not res["refreshToken"]
    assert not res["refreshToken"]


def test_login_unverified_success(
    allow_login_not_verified, unverified_schema, login_query
):
    res = unverified_schema.execute(login_query(unverified_schema.us_type))
    default_test(res)


def test_login_wrong_username(verified_schema, login_query):
    us_type = verified_schema.us_type
    us_type.user.username_field = "wrong_username"
    res = verified_schema.execute(login_query(us_type))
    res = res.data["tokenAuth"]
    assert not res["success"]
    assert res["errors"]
    assert not res["refreshToken"]


def test_login_wrong_password(verified_schema, login_query):
    us_type = verified_schema.us_type
    us_type.user.password = "wrong_passwordZ"
    res = verified_schema.execute(login_query(us_type))
    res = res.data["tokenAuth"]
    assert not res["success"]
    assert res["errors"]
    assert not res["refreshToken"]


def test_setting_not_verified_allowed_but_with_wrong_pass(
    unverified_schema,
    allow_login_not_verified,
    login_query,
):
    us_type = unverified_schema.us_type
    us_type.user.password = "wrong_pass"
    query = login_query(us_type)
    res = unverified_schema.execute(query=query)
    res = res.data["tokenAuth"]
    assert not res["success"]
    assert res["errors"]["nonFieldErrors"] == Messages.INVALID_CREDENTIALS
    assert not res["refreshToken"]
    assert not res["refreshToken"]
