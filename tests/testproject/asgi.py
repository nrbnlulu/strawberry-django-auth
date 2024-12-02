from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from strawberry.channels import GraphQLHTTPConsumer, GraphQLWSConsumer

from gqlauth.core.middlewares import channels_jwt_middleware
from tests.testproject.schema import arg_schema

websocket_urlpatterns = [
    re_path(
        "^graphql",
        channels_jwt_middleware(GraphQLWSConsumer.as_asgi(schema=arg_schema)),
    ),
]
gql_http_consumer = AuthMiddlewareStack(
    channels_jwt_middleware(GraphQLHTTPConsumer.as_asgi(schema=arg_schema))
)
application = ProtocolTypeRouter(
    {
        "http": URLRouter(
            [
                re_path("^graphql", gql_http_consumer),
            ]
        ),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
