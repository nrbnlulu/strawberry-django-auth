from django.apps import apps
from django.contrib import admin

app = apps.get_app_config("gqlauth")

for _, model in app.models.items():
    admin.site.register(model)
