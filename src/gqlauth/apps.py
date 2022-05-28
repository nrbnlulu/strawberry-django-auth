from django.apps import AppConfig
from gqlauth.settings import gqlauth_settings


class GqlAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gqlauth"
    verbose_name = "GraphQL Auth"

    def ready(self):
        from . import signals
