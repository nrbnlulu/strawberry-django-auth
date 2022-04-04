from django.utils.translation import gettext as _


class ErrorBase(Exception):
    default_message = None

    def __init__(self, message=None):
        if message is None:
            message = self.default_message

        super().__init__(message)


class WrongUsage(ErrorBase):
    """
    internal exception
    """
    default_message = _("Wrong usage, check your code!.")

class WrongInput(ErrorBase):
    default_message = _("Wrong Input received")

