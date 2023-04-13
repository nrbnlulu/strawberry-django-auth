from __future__ import annotations

import binascii
import io
import os
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Case, When
from django.db.models import Value as Val
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from gqlauth.backends.basebackend import UserProto
from gqlauth.captcha.captcha_factorty import CaptchaInstanceType, generate_captcha_text
from gqlauth.core.types_ import CaptchaErrorCodes
from gqlauth.settings import gqlauth_settings as app_settings

if TYPE_CHECKING:
    pass

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
    def from_user(cls, user: UserProto) -> RefreshToken:
        token = binascii.hexlify(
            os.urandom(app_settings.JWT_REFRESH_TOKEN_N_BYTES),
        ).decode()

        obj = RefreshToken.objects.create(user=user, token=token)
        obj.save()
        return obj


class Captcha(models.Model):
    instance: CaptchaInstanceType
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=50, editable=False)
    insert_time = models.DateTimeField(auto_now_add=True, editable=False)
    tries = models.IntegerField(default=0)
    image = models.ImageField(
        blank=False,
        null=False,
        upload_to="captcha/%Y/%m/%d/",
        editable=False,
        help_text="url for the captcha image",
    )

    @staticmethod
    def _format(text: str):
        return text.lower().replace(" ", "")

    @classmethod
    def create_captcha(cls):
        cap = generate_captcha_text()
        obj = cls(text=cap.text)
        # saving the image for future use when resolving to base64 or saving to .png
        obj.instance = cap
        obj.save()
        if app_settings.FORCE_SHOW_CAPTCHA:
            cap.pil_image.show()
        if app_settings.CAPTCHA_SAVE_IMAGE:
            django_content_file = obj.instance.to_django(name=str(obj.uuid))
            obj.image.save(django_content_file.name, django_content_file)

        return obj

    def save(self, *args, **kwargs):
        self.text = self._format(self.text)
        super().save(*args, **kwargs)

    def validate(self, user_entry: str) -> CaptchaErrorCodes | None:
        """validates input_.

        - if tried to validate more than 3 times obj will be deleted in the database
        - else increments by one
        - if reaches expiery date deletes the obj
        - returns bool for success state
        """
        if self.tries > app_settings.CAPTCHA_MAX_RETRIES:
            try:
                self.delete()
            except ValueError:
                ...  # object is deleted
            return CaptchaErrorCodes.CAPTCHA_MAX_RETRIES

        self.tries += 1

        # check expiery
        if timezone.now() > self.insert_time + app_settings.CAPTCHA_EXPIRATION_DELTA:
            try:
                self.delete()
            except ValueError:
                ...  # object is deleted
            return CaptchaErrorCodes.CAPTCHA_EXPIRED

        # validate
        if app_settings.CAPTCHA_TEXT_VALIDATOR(
            self.text.replace(" ", ""), user_entry.replace(" ", "")
        ):
            # delete captcha if valid
            self.delete()
            return

        return CaptchaErrorCodes.CAPTCHA_INVALID

    def as_bytes(self):
        """Stores the image on a bytes_array.

        The scalar will further convert it to b64 string representation.
        """
        bytes_array = io.BytesIO()
        self.instance.pil_image.save(bytes_array, format="PNG")
        return bytes_array.getvalue()

    def __str__(self):
        interval = (self.insert_time + app_settings.CAPTCHA_EXPIRATION_DELTA) - timezone.now()
        interval = interval.total_seconds()
        expiery_str = f" expires in {interval} seconds" if interval > 0 else "already expierd"
        return "captcha " + expiery_str
