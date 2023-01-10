from django.utils.translation import gettext as _


class GraphQLAuthError(Exception):
    def __init__(self, message=None):
        if message is None:
            message = " ".join([_("Authorization error:"), self.default_message])

        super().__init__(message)


class WrongUsage(GraphQLAuthError):
    """Internal exception."""

    default_message = _("Wrong usage, check your code!.")


class UserAlreadyVerified(GraphQLAuthError):
    default_message = _("User already verified.")


class InvalidCredentials(GraphQLAuthError):
    default_message = _("Invalid credentials.")


class UserNotVerified(GraphQLAuthError):
    default_message = _("User is not verified.")


class TokenScopeError(GraphQLAuthError):
    default_message = _("This token is for something else.")


class TokenExpired(GraphQLAuthError):
    default_message = _("This token is expired")


class PasswordAlreadySetError(GraphQLAuthError):
    default_message = _("Password already set for account.")


class PermissionDenied(GraphQLAuthError):
    default_message = _("User is not allowed for this content")
