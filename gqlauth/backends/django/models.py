from __future__ import annotations

import binascii
import os
from datetime import datetime
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Case, When
from django.db.models import Value as Val
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from gqlauth.settings import gqlauth_settings as app_settings

if TYPE_CHECKING:
    from gqlauth.backends.django.backend import DjangoUserProto

USER_MODEL = get_user_model()


class RefreshTokenQuerySet(models.QuerySet):
    def expired(self):
        expires = timezone.now() - app_settings.JWT_REFRESH_EXPIRATION_DELTA
        return self.annotate(
            expired=Case(
                When(created__lt=expires, then=Val(True)),
                output_field=models.BooleanField(),
                default=Val(False),
            ),
        )


class RefreshToken(models.Model):
    """Refresh token is a random set of bytes decoded to a string that is
    referring a user.

    It can be used to retrieve a new token without the need to login
    again.
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
        """Whether the token is expired or not.

        it is up to the database query to filter out tokens without
        revoked date.
        """
        return datetime.now(tz=self.created.tzinfo) > self.expires_at_() or bool(self.revoked)

    def revoke(self):
        self.revoked = datetime.now()
        self.save(update_fields=["revoked"])

    objects = RefreshTokenQuerySet.as_manager()  # type: ignore

    class Meta:
        verbose_name = _("refresh token")
        verbose_name_plural = _("refresh tokens")
        unique_together = ("token", "revoked")

    def __str__(self):
        return self.token

    @classmethod
    def from_user(cls, user: DjangoUserProto) -> RefreshToken:
        token = binascii.hexlify(
            os.urandom(app_settings.JWT_REFRESH_TOKEN_N_BYTES),
        ).decode()

        obj = RefreshToken.objects.create(user=user, token=token)
        obj.save()
        return obj
