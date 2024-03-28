from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import AsyncGraphQLView, GraphQLView

import testproject.relay_schema

from . import schema, views

urlpatterns = [
    path('', views.index, name='index'),
    path("admin/", admin.site.urls),
    path("arg_schema", csrf_exempt(GraphQLView.as_view(schema=schema.arg_schema))),
    path(
        "relay_schema",
        csrf_exempt(GraphQLView.as_view(schema=testproject.relay_schema.relay_schema)),
    ),
    path("arg_schema_async", csrf_exempt(AsyncGraphQLView.as_view(schema=schema.arg_schema))),
    path(
        "relay_schema_async",
        csrf_exempt(AsyncGraphQLView.as_view(schema=testproject.relay_schema.relay_schema)),
    ),
] + static(settings.MEDIA_URL, document_root=str(settings.MEDIA_ROOT))
