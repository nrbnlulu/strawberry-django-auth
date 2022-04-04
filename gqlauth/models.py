from datetime import timedelta
from django.utils import timezone
import io
import logging
import uuid
import time
from gqlauth.factory.captcha_factorty import generate_city_captcha

from django.db import models
from django.conf import settings as django_settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.db import transaction

# gqlauth imports
from gqlauth.settings import gqlauth_settings as app_settings
from .constants import Messages, TokenAction
from .utils import get_token, get_payload_from_token
from .exceptions import (
    UserAlreadyVerified,
    UserNotVerified,
    EmailAlreadyInUse,
    WrongUsage,
)
from .signals import user_verified

logger = logging.getLogger(__name__)

USER_MODEL = get_user_model()

class Captcha(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=50, editable=False)
    insert_time = models.DateTimeField(auto_now_add=True, editable=False)
    tries = models.IntegerField(default=0)

    @staticmethod
    def _format(text: str):
        return text.lower().replace(' ', '')

    @classmethod
    def create_captcha(cls):
        cap = generate_city_captcha()
        obj = cls(text=cap.text)
        setattr(obj, 'image', cap.image)
        obj.save()
        if django_settings.DEBUG:
            obj.show()
        return obj

    def save(self, *args, **kwargs):
        self.text = self._format(self.text)
        super().save(*args, **kwargs)

    def validate(self, input_: str):
        """
        validates input_.
        - if tried to validate more than 3 times obj will be deleted in the database 
        - else increments by one
        - if reaches expiery date deletes the obj
        - returns bool for success state
        """
        if self.tries > app_settings.CAPTCHA_MAX_RETRIES:
            try:
                self.delete()
            except ValueError:
                logger.info("object already deleted")
            return Messages.CAPTCHA_MAX_RETRIES

        else:
            self.tries += 1

        # check expiery
        if timezone.now() > self.insert_time + app_settings.CAPTCHA_EXPIRATION_DELTA:
            try:
                self.delete()
            except ValueError:
                logger.info("object aleardy deleted")
            return Messages.CAPTCHA_EXPIRED

        # validate
        if input_.replace(" ", "") == self.text.replace(" ", ""):
            # delete captcha if valid
            self.delete()
            return Messages.CAPTCHA_VALID

        return Messages.CAPTCHA_INVALID

    def show(self):
        self.image.show()

    def as_bytes(self):
        bytes_array = io.BytesIO()
        self.image.save(bytes_array, format='PNG')
        return bytes_array.getvalue()

    def __str__(self):
        interval = (self.insert_time + app_settings.CAPTCHA_EXPIRATION_DELTA) - timezone.now()
        interval = interval.total_seconds()
        expiery_str = (f" expires in {interval} seconds"
                       if interval > 0
                       else "already expierd")
        return "captcha " + expiery_str


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
            recipient_list=(
                    recipient_list or [getattr(self.user, USER_MODEL.EMAIL_FIELD)]
            ),
            fail_silently=False,
        )

    def get_email_context(self, info, path, action, **kwargs):
        token = get_token(self.user, action, **kwargs)
        site = get_current_site(info.context)
        return {
            "user": self.user,
            "request": info.context,
            "token": token,
            "port": info.context.get_port(),
            "site_name": site.name,
            "domain": site.domain,
            "protocol": "https" if info.context.is_secure() else "http",
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
        if email:
            if cls.email_is_free(email) is False:
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

