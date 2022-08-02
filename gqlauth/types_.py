from uuid import UUID

import strawberry
import strawberry_django

from gqlauth import models
from gqlauth.scalars import image as Image


@strawberry_django.type(model=models.Captcha)
class CaptchaType:
    uuid: UUID
    image: strawberry.auto

    @strawberry.django.field(description="returns the b64 encoded image.")
    def pil_image(self) -> Image:
        return self.as_bytes()
