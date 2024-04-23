import pytest
from django.apps import apps
from django.test import TestCase
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from django.test import override_settings
from gqlauth.captcha.models import Captcha
from gqlauth.core.constants import Messages
from gqlauth.settings_type import GqlAuthSettings
from strawberry.types import ExecutionResult
from strawberry.utils.str_converters import to_camel_case

from .conftest import SchemaHelper, UserModel, UserStatusType


@pytest.fixture
def login_query(request):
    app_settings: GqlAuthSettings = request.getfixturevalue("app_settings")
    captcha: Captcha = request.getfixturevalue("captcha")

    def inner(user_status: UserStatusType) -> str:
        user = user_status.user
        arguments = (
            f'{to_camel_case(UserModel.USERNAME_FIELD)}: "{user.username_field}",'
            f' password: "{user.password}"'
        )

        if app_settings.LOGIN_REQUIRE_CAPTCHA:
            arguments += f', identifier: "{captcha.uuid}" ,userEntry: "{captcha.text}"'

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
           """ % (
            arguments
        )

    return inner


@pytest.fixture()
def archived_schema(db_archived_user_status, rf) -> SchemaHelper:
    return SchemaHelper.create(rf=rf, us_type=db_archived_user_status)


class TestMigrations(TestCase):

    @property
    def app(self):
        return apps.get_containing_app_config("gqlauth").name

    migrate_from = None
    migrate_to = None

    def setUp(self):
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to     properties".format(type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass


class TagsTestCase(TestMigrations):

    migrate_from = '0001_initial'
    migrate_to = '0002_alter_userstatus_options'

    def setUpBeforeMigration(self, apps):
        UserModel.objects.create(username='testusername')

    def test_tags_migrated(self):
        user = UserModel.objects.get(username='testusername')
        self.assertTrue(user.status is not None)


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


def test_login_success(verified_schema, unverified_schema, allow_login_not_verified, login_query):
    res = verified_schema.execute(login_query(verified_schema.us_type))
    default_test(res)


@override_settings(USE_TZ=False)
def test_login_success(verified_schema, unverified_schema, allow_login_not_verified, login_query):
    res = verified_schema.execute(login_query(verified_schema.us_type))
    default_test(res)


def test_not_verified_fails(unverified_schema, login_query):
    res = unverified_schema.execute(login_query(unverified_schema.us_type))
    res = res.data["tokenAuth"]
    assert not res["success"]
    assert res["errors"]["nonFieldErrors"] == Messages.NOT_VERIFIED
    assert not res["refreshToken"]
    assert not res["refreshToken"]


def test_login_unverified_success(allow_login_not_verified, unverified_schema, login_query):
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
