from dataclasses import dataclass
from base64 import b64decode, b64encode
import io
from gqlauth.settings import gqlauth_settings as app_settings
from pathlib import Path
import sys
from PIL.Image import Image
from faker import Faker
from .create import ImageCaptcha
sys.path.append(str(Path(__file__).parent.parent.parent))
FONTS_PATH = str(Path(__file__).parent.joinpath('fonts'))
fake = Faker()


@dataclass
class CaptchaType:
    image: Image
    text: str

    def as_base64(self):
        bytes_array = io.BytesIO()
        self.image.save(bytes_array,format='PNG')
        return b64encode(bytes_array.getvalue())

    def show(self):
        self.image.show()


def get_image(text):
    image = ImageCaptcha(width=300,
    height=150,
    heb_fonts=[FONTS_PATH+'/stam.ttf'],
    fonts=[FONTS_PATH+'/OpenSans-Semibold.ttf'],
    )
    image = image.generate_image(text)
    return image


def generate_text() -> str:
    factory = app_settings.CAPTCHA_TEXT_FACTORY
    if factory:
        return factory()
    return " ".join([fake.city(), str(fake.pyint())])


def generate_city_captcha():
    text = generate_text()
    image = get_image(text)
    return CaptchaType(image=image, text=text)

