In order to have a user in your context from headers
our django middleware would not suffice.
you would need to user our `channels` middleware.

Here is an example of an asgi.py file that uses our middleware to support JWT from headers:
_**asgi.py**_

```python
from gqlauth.core.middlewares import channels_jwt_middleware

...

websocket_urlpatterns = [
    re_path("^graphql", channels_jwt_middleware(GraphQLWSConsumer.as_asgi(schema=arg_schema))),
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
```

Now in order to have the user inside `info.context.request` we need to use a custom schema
_**schema.py**_
```python
from gqlauth.core.middlewares import JwtSchema


arg_schema = JwtSchema(
    query=Query, mutation=Mutation, subscription=Subscription
)
```
