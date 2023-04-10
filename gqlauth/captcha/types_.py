from uuid import UUID

import strawberry
import strawberry_django

import gqlauth.backends.strawberry_django_auth.models
from gqlauth.core.scalars import image as Image


@strawberry_django.type(model=gqlauth.backends.strawberry_django_auth.models.Captcha)
class CaptchaType:
    uuid: UUID
    image: strawberry.auto

    @strawberry_django.field(description="returns the b64 encoded image.")
    def pil_image(self: gqlauth.backends.strawberry_django_auth.models.Captcha) -> Image:  # type: ignore
        return self.as_bytes()  # type: ignore
