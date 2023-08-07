from uuid import UUID

import strawberry
import strawberry_django

from gqlauth.captcha import models
from gqlauth.captcha.models import PILLOW_INSTALLED
from gqlauth.core.scalars import image as Image

if PILLOW_INSTALLED:

    @strawberry_django.type(model=models.Captcha)
    class CaptchaType:
        uuid: UUID
        image: strawberry.auto

        @strawberry_django.field(description="returns the b64 encoded image.")
        def pil_image(self: models.Captcha) -> Image:  # type: ignore
            return self.as_bytes()  # type: ignore
