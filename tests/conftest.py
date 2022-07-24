from django.contrib.auth import get_user_model
import pytest

UserModel = get_user_model()


class MARKERS:
    settings_b = "settings_b"


@pytest.fixture
def current_markers(request, pytestconfig):
    return pytestconfig.getoption("-m")


@pytest.fixture
def username_field():
    return UserModel.USERNAME_FIELD
