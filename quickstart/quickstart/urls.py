from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import AsyncGraphQLView, GraphQLView

from .aschema import aschema
from .schema import schema

urlpatterns = [
    path("", csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    path("async", csrf_exempt(AsyncGraphQLView.as_view(graphiql=True, schema=aschema))),
]
