import binascii
import os
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.mail import send_mail
from django.db import models
from django.db.models import Case, When
from django.db.models import Value as Val
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from gqlauth.backends.django.backend import StatusChoices
from gqlauth.core.constants import TokenAction
from gqlauth.core.exceptions import UserAlreadyVerified

# gqlauth imports
from gqlauth.settings import gqlauth_settings as app_settings

USER_MODEL = get_user_model()


class AbstractGqlAuthUser(AbstractBaseUser):
    """To Be extended by types implementing."""

    class Meta:
        abstract = True

    status = models.CharField(
        max_length=2,
        choices=StatusChoices.choices,
        default=StatusChoices.UNVERIFIED,
    )
    archived = models.BooleanField(default=False, verbose_name=_("Is the user archived?"))

    def __str__(self):
        return f"Status - {self.status}"

    def is_verified(self) -> bool:
        return self.status is StatusChoices.VERIFIED

    def is_unverified(self) -> bool:
        return self.status is StatusChoices.UNVERIFIED

    def is_archived(self) -> bool:
        return self.archived

    def send(self, subject, template, context, recipient_list=None):
        _subject = render_to_string(subject, context).replace("\n", " ").strip()
        html_message = render_to_string(template, context)
        message = strip_tags(html_message)

        return send_mail(
            subject=_subject,
            from_email=app_settings.EMAIL_FROM,
            message=message,
            html_message=html_message,
            recipient_list=(recipient_list or [getattr(self, USER_MODEL.EMAIL_FIELD)]),
            fail_silently=False,
        )

    def send_activation_email(self, info, *args, **kwargs):
        email_context = self.get_email_context(
            info, app_settings.ACTIVATION_PATH_ON_EMAIL, TokenAction.ACTIVATION
        )
        template = app_settings.EMAIL_TEMPLATE_ACTIVATION
        subject = app_settings.EMAIL_SUBJECT_ACTIVATION
        return self.send(subject, template, email_context, *args, **kwargs)

    def resend_activation_email(self, info, *args, **kwargs):
        if self.is_verified():
            raise UserAlreadyVerified
        email_context = self.get_email_context(
            info, app_settings.ACTIVATION_PATH_ON_EMAIL, TokenAction.ACTIVATION
        )
        template = app_settings.EMAIL_TEMPLATE_ACTIVATION_RESEND
        subject = app_settings.EMAIL_SUBJECT_ACTIVATION_RESEND
        return self.send(subject, template, email_context, *args, **kwargs)

    def send_password_set_email(self, info, *args, **kwargs):
        email_context = self.get_email_context(
            info, app_settings.PASSWORD_SET_PATH_ON_EMAIL, TokenAction.PASSWORD_SET
        )
        template = app_settings.EMAIL_TEMPLATE_PASSWORD_SET
        subject = app_settings.EMAIL_SUBJECT_PASSWORD_SET
        return self.send(subject, template, email_context, *args, **kwargs)

    def send_password_reset_email(self, info, *args, **kwargs):
        email_context = self.get_email_context(
            info, app_settings.PASSWORD_RESET_PATH_ON_EMAIL, TokenAction.PASSWORD_RESET
        )
        template = app_settings.EMAIL_TEMPLATE_PASSWORD_RESET
        subject = app_settings.EMAIL_SUBJECT_PASSWORD_RESET
        return self.send(subject, template, email_context, *args, **kwargs)


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
    def from_user(cls, user) -> "RefreshToken":
        token = binascii.hexlify(
            os.urandom(app_settings.JWT_REFRESH_TOKEN_N_BYTES),
        ).decode()

        obj = RefreshToken.objects.create(user=user, token=token)
        obj.save()
        return obj


__all__ = ["AbstractGqlAuthUser", "RefreshToken", "RefreshTokenQuerySet", "UserAlreadyVerified"]
