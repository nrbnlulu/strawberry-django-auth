from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid


class CustomUser(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    email = models.EmailField(blank=False, unique=True, max_length=254, verbose_name=_("email address"))

    USERNAME_FIELD = "username"  # e.g: "username", "email"
    EMAIL_FIELD = "email"  # e.g: "email", "primary_email"

