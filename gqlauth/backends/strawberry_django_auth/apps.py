from django.apps import AppConfig


class GqlAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gqlauth.backends.strawberry_django_auth"
    verbose_name = "GraphQL Authentication"
