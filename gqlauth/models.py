import binascii
from datetime import datetime
import os
import time

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Case
from django.db.models import Value as Val
from django.db.models import When
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from strawberry.types import Info

from gqlauth.core.constants import TokenAction
from gqlauth.core.exceptions import EmailAlreadyInUse, UserAlreadyVerified, WrongUsage
from gqlauth.core.utils import get_payload_from_token, get_request, get_token

# gqlauth imports
from gqlauth.settings import gqlauth_settings as app_settings
from gqlauth.user.signals import user_verified

USER_MODEL = get_user_model()


class UserStatus(models.Model):
    """
    A helper model that handles user account stuff.
    """

    user = models.OneToOneField(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="status"
    )
    verified = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    secondary_email = models.EmailField(blank=True, null=True)

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
        request = get_request(info)
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

    def send_secondary_email_activation(self, info, email):
        if not self.email_is_free(email):
            raise EmailAlreadyInUse
        email_context = self.get_email_context(
            info,
            app_settings.ACTIVATION_SECONDARY_EMAIL_PATH_ON_EMAIL,
            TokenAction.ACTIVATION_SECONDARY_EMAIL,
            secondary_email=email,
        )
        template = app_settings.EMAIL_TEMPLATE_SECONDARY_EMAIL_ACTIVATION
        subject = app_settings.EMAIL_SUBJECT_SECONDARY_EMAIL_ACTIVATION
        return self.send(subject, template, email_context, recipient_list=[email])

    @classmethod
    def email_is_free(cls, email):
        try:
            USER_MODEL._default_manager.get(**{USER_MODEL.EMAIL_FIELD: email})
            return False
        except Exception:
            pass
        try:
            UserStatus._default_manager.get(secondary_email=email)
            return False
        except Exception:
            pass
        return True

    @classmethod
    def clean_email(cls, email=False):
        if email and cls.email_is_free(email) is False:
            raise EmailAlreadyInUse

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
    def verify_secondary_email(cls, token):
        payload = get_payload_from_token(
            token,
            TokenAction.ACTIVATION_SECONDARY_EMAIL,
            app_settings.EXPIRATION_SECONDARY_EMAIL_ACTIVATION_TOKEN,
        )
        secondary_email = payload.pop("secondary_email")
        if not cls.email_is_free(secondary_email):
            raise EmailAlreadyInUse
        user = USER_MODEL._default_manager.get(**payload)
        user_status = cls.objects.get(user=user)
        user_status.secondary_email = secondary_email
        user_status.save(update_fields=["secondary_email"])

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

    def swap_emails(self):
        if not self.secondary_email:
            raise WrongUsage
        with transaction.atomic():
            EMAIL_FIELD = USER_MODEL.EMAIL_FIELD
            primary = getattr(self.user, EMAIL_FIELD)
            setattr(self.user, EMAIL_FIELD, self.secondary_email)
            self.secondary_email = primary
            self.user.save(update_fields=[EMAIL_FIELD])
            self.save(update_fields=["secondary_email"])

    def remove_secondary_email(self):
        if not self.secondary_email:
            raise WrongUsage
        with transaction.atomic():
            self.secondary_email = None
            self.save(update_fields=["secondary_email"])


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
        return datetime.now(tz=self.created.tzinfo) > self.expires_at_() or bool(self.revoked)

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
