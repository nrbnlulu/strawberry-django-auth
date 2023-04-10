from __future__ import annotations

import contextlib
import time
from functools import cached_property
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from gqlauth.backends.basebackend import GqlAuthBackendABC, UserProto
from gqlauth.core.constants import TokenAction
from gqlauth.user.signals import user_verified


# avoid import errors
class DjangoUserProto:
    ...


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from gqlauth.backends.django.mixins import StatusMixin
    from gqlauth.backends.django.models import RefreshToken

    class DjangoUserProto(UserProto, AbstractUser, StatusMixin):  # noqa: F811
        ...


class DjangoGqlAuthBackend(GqlAuthBackendABC):
    @cached_property
    def exceptions(self):
        from gqlauth.core import exceptions

        return exceptions

    @cached_property
    def utils(self):
        from gqlauth.core import utils

        return utils

    @cached_property
    def app_settings(self):
        return self.utils.app_settings

    @cached_property
    def user_model(self) -> DjangoUserProto:
        return get_user_model()  # type: ignore

    @cached_property
    def refresh_token_model(self) -> type[RefreshToken]:
        from gqlauth.backends.django.models import RefreshToken

        return RefreshToken

    def get_user_from_payload(self, payload: dict) -> DjangoUserProto:
        return self.user_model.objects.get(**payload)

    def unarchived(self, user: DjangoUserProto) -> None:
        if user.archived:
            user.archived = False
            user.save(update_fields=["archived"])

    def verify(self, token: str) -> None:
        payload = self.utils.get_payload_from_token(
            token, TokenAction.ACTIVATION, self.app_settings.EXPIRATION_ACTIVATION_TOKEN
        )
        user: DjangoUserProto = self.user_model.objects.get(**payload)  # type: ignore
        if not user.is_verified():
            user.set_verified(True)
            user_verified.send(sender=self, user=user)
        else:
            raise self.exceptions.UserAlreadyVerified

    @classmethod
    def archive(cls, user: DjangoUserProto):
        if not user.archived:
            user.archived = True
            user.save(update_fields=["archived"])

    def get_email_context(self, info, path, action, **kwargs) -> dict:
        token = self.utils.get_token(self, action, **kwargs)
        request = info.context.request
        site = get_current_site(request)
        return {
            "user": self,
            "request": request,
            "token": token,
            "port": request.get_port(),
            "site_name": site.name,
            "domain": site.domain,
            "protocol": "https" if request.is_secure() else "http",
            "path": path,
            "timestamp": time.time(),
            **self.app_settings.EMAIL_TEMPLATE_VARIABLES,
        }

    def send_email(
        self, subject, template, context, recipient_list: list[str] | None = None
    ) -> None:
        _subject = render_to_string(subject, context).replace("\n", " ").strip()
        html_message = render_to_string(template, context)
        message = strip_tags(html_message)
        return send_mail(
            subject=_subject,
            from_email=self.app_settings.EMAIL_FROM,
            message=message,
            html_message=html_message,
            recipient_list=recipient_list or [getattr(self, self.user_model.EMAIL_FIELD)],
            fail_silently=False,
        )

    def send_activation_email(self, info, *args, **kwargs) -> None:
        email_context = self.get_email_context(
            info, self.app_settings.ACTIVATION_PATH_ON_EMAIL, TokenAction.ACTIVATION
        )
        template = self.app_settings.EMAIL_TEMPLATE_ACTIVATION
        subject = self.app_settings.EMAIL_SUBJECT_ACTIVATION
        return self.send_email(subject, template, email_context, *args, **kwargs)

    def resend_activation_email(self, info, user, *args, **kwargs) -> None:
        if user.is_verified():
            raise self.exceptions.UserAlreadyVerified
        email_context = self.get_email_context(
            info, self.app_settings.ACTIVATION_PATH_ON_EMAIL, TokenAction.ACTIVATION
        )
        template = self.app_settings.EMAIL_TEMPLATE_ACTIVATION_RESEND
        subject = self.app_settings.EMAIL_SUBJECT_ACTIVATION_RESEND
        return self.send_email(subject, template, email_context, *args, **kwargs)

    def send_password_set_email(self, info, *args, **kwargs) -> None:
        email_context = self.get_email_context(
            info, self.app_settings.PASSWORD_SET_PATH_ON_EMAIL, TokenAction.PASSWORD_SET
        )
        template = self.app_settings.EMAIL_TEMPLATE_PASSWORD_SET
        subject = self.app_settings.EMAIL_SUBJECT_PASSWORD_SET
        return self.send_email(subject, template, email_context, *args, **kwargs)

    def send_password_reset_email(self, info, *args, **kwargs) -> None:
        email_context = self.get_email_context(
            info, self.app_settings.PASSWORD_RESET_PATH_ON_EMAIL, TokenAction.PASSWORD_RESET
        )
        template = self.app_settings.EMAIL_TEMPLATE_PASSWORD_RESET
        subject = self.app_settings.EMAIL_SUBJECT_PASSWORD_RESET
        return self.send_email(subject, template, email_context, *args, **kwargs)

    def revoke_user_refresh_token(self, user: DjangoUserProto) -> None:
        for refresh_token in self.refresh_token_model.objects.filter(user=user):
            with contextlib.suppress(BaseException):
                refresh_token.revoke()
