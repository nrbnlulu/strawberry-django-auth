from uuid import UUID
import strawberry_django
import strawberry
from strawberry_django import auto

from gqlauth import models
from gqlauth.scalars import image


@strawberry_django.type(model=models.Captcha)
class CaptchaType:
    uuid: UUID
    @strawberry.field
    def image(self) -> image:
        return self.as_bytes()
