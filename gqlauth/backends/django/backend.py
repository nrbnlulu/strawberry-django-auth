from __future__ import annotations

import time
from functools import cached_property
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.utils.translation import gettext_lazy as _

from gqlauth.backends.basebackend import GqlAuthBackendABC, UserProto
from gqlauth.core.constants import TokenAction
from gqlauth.core.exceptions import UserAlreadyVerified
from gqlauth.user.signals import user_verified

if TYPE_CHECKING:
    from gqlauth.backends.django.models import AbstractGqlAuthUser

    class DjangoUserProto(UserProto, AbstractGqlAuthUser):
        ...


class StatusChoices(models.TextChoices):
    UNVERIFIED = "UVE", _("Unverified")
    VERIFIED = "VE", _("Verified")


class DjangoGqlAuthBackend(GqlAuthBackendABC):
    @cached_property
    def utils(self):
        from gqlauth.core import utils

        return utils

    @cached_property
    def app_settings(self):
        return self.utils.app_settings

    @cached_property
    def user_model(self) -> DjangoUserProto:
        return get_user_model()

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
            user.status = StatusChoices.VERIFIED
            user.save(update_fields=["status"])
            user_verified.send(sender=self, user=user)
        else:
            raise UserAlreadyVerified

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
