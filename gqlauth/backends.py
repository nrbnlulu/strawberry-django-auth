from strawberry_django_jwt.backends import JSONWebTokenBackend
from strawberry_django_jwt.shortcuts import get_user_by_token
from strawberry_django_jwt.utils import get_credentials
from strawberry_django_jwt.exceptions import JSONWebTokenError, JSONWebTokenExpired


class GraphQLAuthBackend(JSONWebTokenBackend):
    """
    Only difference from the original backend
    is it does not raise when fail on get_user_by_token
    preventing of raise when client send token to a
    mutation that does not requery login but is not on
    allow any settings.

    Main advantage is to let the mutation handle the
    unauthentication error. Intead of an actual error,
    we can return e.g. success=False errors=Unauthenticated
    """

    def authenticate(self, request=None, **kwargs):
        # if it isnt a request or settings dosnt require a _jwt_token
        if request is None or getattr(request, "_jwt_token_auth", False):
            return None



        try:  # +++
            token = get_credentials(request, **kwargs)
            if token is not None:
                return get_user_by_token(token, request)
        except JSONWebTokenError:  # +++
            pass  # +++

        except JSONWebTokenExpired:
            ...
        return None
