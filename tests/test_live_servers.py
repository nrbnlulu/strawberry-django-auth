import pytest
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

pytestmark = pytest.mark.default_user


def test_channels_middleware_authorized_user(ws_verified_client, db_verified_user_status):
    query = """
    subscription {
      whatsMyName
    }
    """
    for res in ws_verified_client.subscribe(document=gql(query)):
        assert res["whatsMyName"] == db_verified_user_status.user.username_field


def test_channel_middleware_authorized_on_query(channels_live_server, db_verified_user_status):
    transport = AIOHTTPTransport(
        url=channels_live_server.http_url,
        headers={"authorization": db_verified_user_status.generate_fresh_token()},
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)
    res = client.execute(document=gql("query { whatsMyUserName }"))
    assert res["whatsMyUserName"] == db_verified_user_status.user.username_field


def test_channels_middleware_no_user_has_anonymous_user(channels_live_server):
    transport = AIOHTTPTransport(url=channels_live_server.http_url)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    res = client.execute(document=gql("query { amIAnonymous }"))
    assert res["amIAnonymous"]


def test_django_middleware_authorized_user(live_server, db_verified_user_status):
    transport = AIOHTTPTransport(
        url=live_server.url + "/arg_schema",
        headers={"authorization": db_verified_user_status.generate_fresh_token()},
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)
    res = client.execute(document=gql("query { whatsMyUserName }"))
    assert res["whatsMyUserName"] == db_verified_user_status.user.username_field


def test_django_middleware_no_user_has_anonymous_user(live_server):
    transport = AIOHTTPTransport(url=live_server.url + "/arg_schema")
    client = Client(transport=transport, fetch_schema_from_transport=False)
    res = client.execute(document=gql("query { amIAnonymous }"))
    assert res["amIAnonymous"]
