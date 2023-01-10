import io
import uuid

from django.db import models
from django.utils import timezone

from gqlauth.captcha.captcha_factorty import CaptchaInstanceType, generate_captcha_text
from gqlauth.core.constants import Messages
from gqlauth.settings import gqlauth_settings as app_settings


class Captcha(models.Model):
    instance: CaptchaInstanceType
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=50, editable=False)
    insert_time = models.DateTimeField(auto_now_add=True, editable=False)
    tries = models.IntegerField(default=0)
    image = models.ImageField(
        blank=False,
        null=False,
        upload_to="captcha/%Y/%m/%d/",
        editable=False,
        help_text="url for the captcha image",
    )

    @staticmethod
    def _format(text: str):
        return text.lower().replace(" ", "")

    @classmethod
    def create_captcha(cls):
        cap = generate_captcha_text()
        obj = cls(text=cap.text)
        # saving the image for future use when resolving to base64 or saving to .png
        obj.instance = cap
        obj.save()
        if app_settings.FORCE_SHOW_CAPTCHA:
            cap.pil_image.show()
        if app_settings.CAPTCHA_SAVE_IMAGE:
            django_content_file = obj.instance.to_django(name=str(obj.uuid))
            obj.image.save(django_content_file.name, django_content_file)

        return obj

    def save(self, *args, **kwargs):
        self.text = self._format(self.text)
        super().save(*args, **kwargs)

    def validate(self, user_entry: str):
        """validates input_.

        - if tried to validate more than 3 times obj will be deleted in the database
        - else increments by one
        - if reaches expiery date deletes the obj
        - returns bool for success state
        """
        if self.tries > app_settings.CAPTCHA_MAX_RETRIES:
            try:
                self.delete()
            except ValueError:
                ...  # object is deleted
            return Messages.CAPTCHA_MAX_RETRIES

        self.tries += 1

        # check expiery
        if timezone.now() > self.insert_time + app_settings.CAPTCHA_EXPIRATION_DELTA:
            try:
                self.delete()
            except ValueError:
                ...  # object is deleted
            return Messages.CAPTCHA_EXPIRED

        # validate
        if app_settings.CAPTCHA_TEXT_VALIDATOR(
            self.text.replace(" ", ""), user_entry.replace(" ", "")
        ):
            # delete captcha if valid
            self.delete()
            return Messages.CAPTCHA_VALID

        return Messages.CAPTCHA_INVALID

    def as_bytes(self):
        """Stores the image on a bytes_array.

        The scalar will further convert it to b64 string representation.
        """
        bytes_array = io.BytesIO()
        self.instance.pil_image.save(bytes_array, format="PNG")
        return bytes_array.getvalue()

    def __str__(self):
        interval = (self.insert_time + app_settings.CAPTCHA_EXPIRATION_DELTA) - timezone.now()
        interval = interval.total_seconds()
        expiery_str = f" expires in {interval} seconds" if interval > 0 else "already expierd"
        return "captcha " + expiery_str
