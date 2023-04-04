from django.db import models
from gqlauth.backends.django.models import AbstractGqlAuthUser


class CustomUser(AbstractGqlAuthUser):
    email = models.EmailField(blank=False, max_length=254, verbose_name="email address")

    USERNAME_FIELD = "username"  # e.g: "username", "email"
    EMAIL_FIELD = "email"  # e.g: "email", "primary_email"
