import binascii
from datetime import datetime
import os

from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from strawberry.types import Info

from gqlauth.jwt.managers import RefreshTokenQuerySet
from gqlauth.user.models import USER_MODEL

app_settings = django_settings.GQL_AUTH


class AbstractRefreshToken(models.Model):
    """
    Refresh token is a random set of bytes decoded to a string that is referring a user.
    It can be used to retrieve a new token without the need to login again.
    """

    id = models.BigAutoField(primary_key=True)  # noqa A003
    user = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
        verbose_name=_("user"),
    )
    token = models.CharField(_("token"), max_length=255, editable=False)
    created = models.DateTimeField(_("created"), auto_now_add=True)
    revoked = models.DateTimeField(_("revoked"), null=True, blank=True)

    def _expires_at(self) -> datetime:
        return self.created + app_settings.JWT_REFRESH_EXPIRATION_DELTA

    def _is_expired(self, info: Info = None) -> bool:
        return app_settings.JWT_REFRESH_EXPIRED_HANDLER(self.created, info)

    objects = RefreshTokenQuerySet.as_manager()

    class Meta:
        abstract = True
        verbose_name = _("refresh token")
        verbose_name_plural = _("refresh tokens")
        unique_together = ("token", "revoked")

    def __str__(self):
        return self.token

    @classmethod
    def from_user(cls, user: User) -> "AbstractRefreshToken":
        token = binascii.hexlify(
            os.urandom(app_settings.JWT_REFRESH_TOKEN_N_BYTES),
        ).decode()

        obj = cls.objects.create(user=user, token=token)
        obj.save()
        return obj


class RefreshToken(AbstractRefreshToken):
    """RefreshToken default model"""
