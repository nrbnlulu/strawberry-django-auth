import binascii
from datetime import datetime
import os

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
import pytz

from gqlauth.jwt.managers import RefreshTokenQuerySet

app_settings = django_settings.GQL_AUTH
USER_MODEL = get_user_model()


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

    def expires_at_(self) -> datetime:
        return self.created + app_settings.JWT_REFRESH_EXPIRATION_DELTA

    def is_expired_(self) -> bool:
        """
        Whether the token is expired or not.
        it is up to the database query to filter out tokens without revoked date.
        """
        return pytz.UTC.localize(datetime.now().utcnow()) > self.expires_at_()

    def revoke(self):
        self.revoked = datetime.now()
        self.save(update_fields=["revoked"])

    objects = RefreshTokenQuerySet.as_manager()

    class Meta:
        abstract = True
        verbose_name = _("refresh token")
        verbose_name_plural = _("refresh tokens")
        unique_together = ("token", "revoked")

    def __str__(self):
        return self.token

    @classmethod
    def from_user(cls, user: USER_MODEL) -> "AbstractRefreshToken":
        token = binascii.hexlify(
            os.urandom(app_settings.JWT_REFRESH_TOKEN_N_BYTES),
        ).decode()

        obj = cls.objects.create(user=user, token=token)
        obj.save()
        return obj


class RefreshToken(AbstractRefreshToken):
    """RefreshToken default model"""
