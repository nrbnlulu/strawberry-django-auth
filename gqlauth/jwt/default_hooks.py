import json
from typing import TYPE_CHECKING, Optional, Union, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http.request import HttpRequest
import jwt

from gqlauth.core.constants import JWT_PREFIX
from gqlauth.core.utils import app_settings

if TYPE_CHECKING:  # pragma: no cover
    from gqlauth.jwt.types_ import TokenType
USER_MODEL = get_user_model()


def token_finder(request_or_scope: Union[dict, "HttpRequest"]) -> Optional[str]:
    token: Optional[str] = None
    if isinstance(request_or_scope, HttpRequest):
        headers = request_or_scope.headers
        token = headers.get("authorization", None) or headers.get("Authorization", None)
    else:
        headers = request_or_scope["headers"]
        for k, v in headers:
            if k == b"authorization":
                token = v.decode()
                break
    if token:
        return token.strip(JWT_PREFIX)
    return None


def create_token_type(user: AbstractBaseUser) -> "TokenType":
    from gqlauth.jwt.types_ import TokenPayloadType, TokenType

    user_pk = app_settings.JWT_PAYLOAD_PK.python_name
    pk_field = {user_pk: getattr(user, user_pk)}
    payload = TokenPayloadType(
        **pk_field,
    )
    serialized = json.dumps(payload.as_dict(), sort_keys=True, indent=1)
    return TokenType(
        token=str(
            jwt.encode(
                payload={"payload": serialized},
                key=cast(str, app_settings.JWT_SECRET_KEY),
                algorithm=app_settings.JWT_ALGORITHM,
            )
        ),
        payload=payload,
    )


def decode_jwt(token: str) -> "TokenType":
    from gqlauth.jwt.types_ import TokenPayloadType, TokenType

    decoded = json.loads(
        jwt.decode(
            token,
            key=cast(str, app_settings.JWT_SECRET_KEY),
            algorithms=[
                app_settings.JWT_ALGORITHM,
            ],
        )["payload"]
    )
    return TokenType(token=token, payload=TokenPayloadType.from_dict(decoded))
