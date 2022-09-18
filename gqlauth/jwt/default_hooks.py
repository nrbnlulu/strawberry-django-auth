import json
from typing import TYPE_CHECKING

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
import jwt
from strawberry.types import Info

if TYPE_CHECKING:
    from gqlauth.jwt.types_ import TokenType

USER_MODEL = get_user_model()
app_settings = django_settings.GQL_AUTH


def create_token_type(_: Info, user: USER_MODEL) -> "TokenType":
    from gqlauth.jwt.types_ import TokenPayloadType, TokenType

    user_pk = app_settings.JWT_PAYLOAD_PK.python_name
    pk_field = {user_pk: getattr(user, user_pk)}
    payload = TokenPayloadType(
        **pk_field,
    )
    serialized = json.dumps(payload.as_dict(), sort_keys=True, indent=1)
    return TokenType(
        token=jwt.encode(
            payload={"payload": serialized},
            key=app_settings.JWT_SECRET_KEY,
            algorithm=app_settings.JWT_ALGORITHM,
        ),
        payload=payload,
    )


def decode_jwt(token: str) -> "TokenType":
    from gqlauth.jwt.types_ import TokenPayloadType, TokenType

    decoded = json.loads(
        jwt.decode(
            token,
            app_settings.JWT_SECRET_KEY,
            algorithms=[
                app_settings.JWT_ALGORITHM,
            ],
        )["payload"]
    )
    return TokenType(token=token, payload=TokenPayloadType.from_dict(decoded))
