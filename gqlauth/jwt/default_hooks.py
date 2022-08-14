from dataclasses import asdict
from datetime import datetime
import json

from django.conf import settings as django_settings
from django.core.serializers.json import DjangoJSONEncoder
import jwt
from strawberry.types import Info

from gqlauth.jwt.models import AbstractRefreshToken
from gqlauth.jwt.types_ import TokenType

app_settings = django_settings.GQL_AUTH


def create_token_type(info: Info) -> TokenType:
    ret = TokenType(
        exp=datetime.utcnow() + app_settings.JWT_EXPIRATION_DELTA, origIat=datetime.utcnow()
    )
    serialized = json.dumps(asdict(ret), sort_keys=True, indent=1, cls=DjangoJSONEncoder)
    ret.token = jwt.encode(
        payload={"token_type": serialized},
        key=app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM,
    )
    return ret


def decode_jwt(token: str, _: Info) -> TokenType:
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


def refresh_has_expired_handler(refresh_token: AbstractRefreshToken, _: Info) -> bool:
    return refresh_token.created > (datetime.now() - app_settings.JWT_REFRESH_EXPIRATION_DELTA)
