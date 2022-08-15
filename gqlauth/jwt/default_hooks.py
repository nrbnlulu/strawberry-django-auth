from dataclasses import asdict
from datetime import datetime
import json

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
import jwt
from strawberry.types import Info

from gqlauth.jwt.types_ import TokenPayloadType, TokenType

USER_MODEL = get_user_model()
app_settings = django_settings.GQL_AUTH


def create_token_type(_: Info, user: USER_MODEL) -> TokenType:
    user_pk = app_settings.JWT_PAYLOAD_PK.python_name
    pk_field = {user_pk: getattr(user, user_pk)}
    payload = TokenPayloadType(
        exp=datetime.utcnow() + app_settings.JWT_EXPIRATION_DELTA,
        origIat=datetime.utcnow(),
        **pk_field,
    )
    serialized = json.dumps(asdict(payload), sort_keys=True, indent=1, cls=DjangoJSONEncoder)
    return TokenType(
        token=jwt.encode(
            payload={"payload": serialized},
            key=app_settings.JWT_SECRET_KEY,
            algorithm=app_settings.JWT_ALGORITHM,
        ),
        payload=payload,
    )


def decode_jwt(token: str) -> TokenType:
    return TokenType(
        json.loads(
            **jwt.decode(
                token,
                app_settings.JWT_SECRET_KEY,
                algorithms=[
                    app_settings.JWT_ALGORITHM,
                ],
            )
        ),
        cls=DjangoJSONEncoder,
    )
