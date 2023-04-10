from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusMixin(models.Model):
    """To Be extended by types implementing."""

    class Meta:
        abstract = True

    verified = models.BooleanField(default=False, verbose_name=_("Is the user verified?"))
    archived = models.BooleanField(default=False, verbose_name=_("Is the user archived?"))

    def __str__(self):
        return f"Status[vreified={self.verified}, archived={self.archived}]"

    def is_verified(self) -> bool:
        return self.verified

    def set_verified(self, v: bool) -> None:
        self.verified = v
        self.save(update_fields=["verified"])

    def is_archived(self) -> bool:
        return self.archived

    def set_archived(self, v: bool) -> None:
        self.verified = v
        self.save(update_fields=["archived"])


__all__ = ["StatusMixin"]
