import io
import sys
from dataclasses import dataclass
from pathlib import Path

from django.core.files.base import ContentFile
from PIL.Image import Image

from gqlauth.settings import gqlauth_settings as app_settings

from .create import ImageCaptcha

sys.path.append(str(Path(__file__).parent.parent.parent))
FONTS_PATH = str(Path(__file__).parent.joinpath("fonts"))


@dataclass
class CaptchaInstanceType:
    pil_image: Image
    text: str

    def to_django(self, name: str) -> ContentFile:
        # inspired by https://stackoverflow.com/questions/34140900
        bytes_array = io.BytesIO()
        self.pil_image.save(bytes_array, format="PNG")
        return ContentFile(bytes_array.getvalue(), name + ".png")

    def show(self):
        self.pil_image.show()


def get_image(text):
    image = ImageCaptcha(
        width=300,
        height=150,
        heb_fonts=[FONTS_PATH + "/stam.ttf"],
        fonts=[FONTS_PATH + "/OpenSans-Semibold.ttf"],
    )
    image = image.generate_image(text)
    return image


def generate_text() -> str:
    return app_settings.CAPTCHA_TEXT_FACTORY()


def generate_captcha_text() -> CaptchaInstanceType:
    text = generate_text()
    image = get_image(text)
    return CaptchaInstanceType(pil_image=image, text=text)
