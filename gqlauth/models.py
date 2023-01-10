import binascii
import os
import time
from datetime import datetime

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import models
from django.db.models import Case, When
from django.db.models import Value as Val
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from strawberry.types import Info

from gqlauth.core.constants import TokenAction
from gqlauth.core.exceptions import UserAlreadyVerified
from gqlauth.core.utils import get_payload_from_token, get_token

# gqlauth imports
from gqlauth.settings import gqlauth_settings as app_settings
from gqlauth.user.signals import user_verified

USER_MODEL = get_user_model()


class UserStatus(models.Model):
    """A helper model that handles user account stuff."""

    user = models.OneToOneField(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="status"
    )
    verified = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return "%s - status" % (self.user)

    def send(self, subject, template, context, recipient_list=None):
        _subject = render_to_string(subject, context).replace("\n", " ").strip()
        html_message = render_to_string(template, context)
        message = strip_tags(html_message)

        return send_mail(
            subject=_subject,
            from_email=app_settings.EMAIL_FROM,
            message=message,
            html_message=html_message,
            recipient_list=(recipient_list or [getattr(self.user, USER_MODEL.EMAIL_FIELD)]),
            fail_silently=False,
        )

    def get_email_context(self, info: Info, path, action, **kwargs):
        token = get_token(self.user, action, **kwargs)
        request = info.context.request
        site = get_current_site(request)
        return {
            "user": self.user,
            "request": request,
            "token": token,
            "port": request.get_port(),
            "site_name": site.name,
            "domain": site.domain,
            "protocol": "https" if request.is_secure() else "http",
            "path": path,
            "timestamp": time.time(),
            **app_settings.EMAIL_TEMPLATE_VARIABLES,
        }

    def send_activation_email(self, info, *args, **kwargs):
        email_context = self.get_email_context(
            info, app_settings.ACTIVATION_PATH_ON_EMAIL, TokenAction.ACTIVATION
        )
        template = app_settings.EMAIL_TEMPLATE_ACTIVATION
        subject = app_settings.EMAIL_SUBJECT_ACTIVATION
        return self.send(subject, template, email_context, *args, **kwargs)

    def resend_activation_email(self, info, *args, **kwargs):
        if self.verified is True:
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

    @classmethod
    def verify(cls, token):
        payload = get_payload_from_token(
            token, TokenAction.ACTIVATION, app_settings.EXPIRATION_ACTIVATION_TOKEN
        )
        user = USER_MODEL._default_manager.get(**payload)
        user_status = cls.objects.get(user=user)
        if user_status.verified is False:
            user_status.verified = True
            user_status.save(update_fields=["verified"])
            user_verified.send(sender=cls, user=user)
        else:
            raise UserAlreadyVerified

    @classmethod
    def unarchive(cls, user):
        user_status = cls.objects.get(user=user)
        if user_status.archived is True:
            user_status.archived = False
            user_status.save(update_fields=["archived"])

    @classmethod
    def archive(cls, user):
        user_status = cls.objects.get(user=user)
        if user_status.archived is False:
            user_status.archived = True
            user_status.save(update_fields=["archived"])


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
