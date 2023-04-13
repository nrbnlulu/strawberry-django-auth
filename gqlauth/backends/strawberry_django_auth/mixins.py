from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusMixin(models.Model):
    """To Be extended by types implementing."""

    class Meta:
        abstract = True

    is_verified = models.BooleanField(default=False, verbose_name=_("Is the user verified?"))
    is_archived = models.BooleanField(default=False, verbose_name=_("Is the user archived?"))

    def __str__(self):
        return f"Status[vreified={self.is_verified}, archived={self.is_archived}]"

    def set_verified(self, v: bool) -> None:
        self.is_verified = v
        self.save(update_fields=["verified"])

    def set_archived(self, v: bool) -> None:
        self.is_archived = v
        self.save(update_fields=["archived"])


__all__ = ["StatusMixin"]
