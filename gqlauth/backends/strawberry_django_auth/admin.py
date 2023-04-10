from django.apps import apps
from django.contrib import admin

app = apps.get_app_config("strawberry_django_auth")

for _, model in app.models.items():
    admin.site.register(model)
