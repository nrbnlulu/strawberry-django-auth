import pytest

pytestmark = pytest.mark.default_user


@pytest.fixture()
def auth_headers(db_verified_user_status) -> dict:
    token = db_verified_user_status.generate_fresh_token()
    return {"authorization": token, "HTTP_AUTHORIZATION": token}


async def test_channels_middleware_authorized_user(
    db_verified_user_status, verified_channels_app_communicator
):
    query = """
    subscription {
      whatsMyName
    }
    """
    async for res in verified_channels_app_communicator.subscribe(query):
        assert res.data["whatsMyName"] == db_verified_user_status.user.username_field


async def test_channel_middleware_authorized_on_query(
    db_verified_user_status, verified_channels_app_communicator
):
    query = "query { whatsMyUserName }"
    async for res in verified_channels_app_communicator.subscribe(query):
        assert (
            res.data["whatsMyUserName"] == db_verified_user_status.user.username_field
        )


async def test_channels_middleware_no_user_has_anonymous_user(
    unverified_channels_app_communicator,
):
    query = "query { amIAnonymous }"
    async for res in unverified_channels_app_communicator.subscribe(query):
        assert res.data["amIAnonymous"]


def test_django_middleware_authorized_user(
    client, db_verified_user_status, auth_headers
):
    res = client.post(
        path="/arg_schema",
        data={"query": "query { whatsMyUserName }"},
        content_type="application/json",
        **auth_headers,
    )

    res = res.json()["data"]
    assert res["whatsMyUserName"] == db_verified_user_status.user.username_field


def test_django_middleware_no_user_has_anonymous_user(client):
    res = client.post(
        path="/arg_schema",
        data={"query": "query { amIAnonymous }"},
        content_type="application/json",
    )
    assert res.json()["data"]["amIAnonymous"] is True


async def test_async_middleware(async_client):
    res = await async_client.post(
        path="/arg_schema",
        data={"query": "query { amIAnonymous }"},
        content_type="application/json",
    )
    assert res.json()["data"]["amIAnonymous"] is True
