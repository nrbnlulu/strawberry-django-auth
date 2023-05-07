import pytest
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

pytestmark = pytest.mark.default_user


@pytest.fixture()
def auth_headers(db_verified_user_status) -> dict:
    token = db_verified_user_status.generate_fresh_token()
    return {"authorization": token, "HTTP_AUTHORIZATION": token}


def test_channels_middleware_authorized_user(db_verified_user_status, ws_verified_client):
    query = """
    subscription {
      whatsMyName
    }
    """
    for res in ws_verified_client.subscribe(document=gql(query)):
        assert res["whatsMyName"] == db_verified_user_status.user.username_field


def test_channel_middleware_authorized_on_query(
    auth_headers, db_verified_user_status, channels_live_server
):
    transport = AIOHTTPTransport(
        url=channels_live_server.http_url,
        headers=auth_headers,
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)
    res = client.execute(document=gql("query { whatsMyUserName }"))
    assert res["whatsMyUserName"] == db_verified_user_status.user.username_field


def test_channels_middleware_no_user_has_anonymous_user(channels_live_server):
    transport = AIOHTTPTransport(url=channels_live_server.http_url)
    client = Client(transport=transport)
    res = client.execute(document=gql("query { amIAnonymous }"))
    assert res["amIAnonymous"]


def test_django_middleware_authorized_user(client, db_verified_user_status, auth_headers):
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
