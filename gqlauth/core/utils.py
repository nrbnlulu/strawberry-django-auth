import contextlib
import inspect
import typing
from typing import Dict, Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.core import signing
from strawberry.field import StrawberryField
from strawberry.types import Info
from strawberry.utils.str_converters import to_camel_case

from gqlauth.core.exceptions import TokenScopeError

if typing.TYPE_CHECKING:  # pragma: no cover
    from gqlauth.models import UserStatus
    from gqlauth.settings_type import GqlAuthSettings

    class UserProto(AbstractBaseUser):
        status: UserStatus


UserProto: "UserProto" = "UserProto"  # type: ignore  # noqa: F811

USER_MODEL = get_user_model()
USER_UNION = typing.Union["UserProto", AnonymousUser, AbstractBaseUser]
app_settings: "GqlAuthSettings" = settings.GQL_AUTH


def hide_args_kwargs(field):
    sig = inspect.signature(field)
    cleared = tuple(p for p in sig.parameters.values() if p.name not in ("kwargs", "args"))
    field.__signature__ = inspect.signature(field).replace(parameters=(cleared))
    return field


def isiterable(value):
    try:
        iter(value)
    except TypeError:  # pragma: no cover
        return False
    return True


def camelize(data):
    if isinstance(data, dict):
        return {to_camel_case(k): camelize(v) for k, v in data.items()}
    if isiterable(data) and not isinstance(data, str):
        return [camelize(d) for d in data]
    return data


def get_user(info: Info) -> USER_UNION:
    return info.context.request.user  # type: ignore


def cast_to_status_user(user: USER_UNION) -> UserProto:
    user.status  # type: ignore  # raise attribute error
    return user  # type: ignore


def get_user_by_email(email: str) -> "UserProto":
    user = USER_MODEL.objects.get(**{USER_MODEL.EMAIL_FIELD: email})
    assert hasattr(user, "status")
    return user  # type: ignore


def get_token(user, action, **kwargs):
    username = user.get_username()
    if hasattr(username, "pk"):
        username = username.pk
    payload = {user.USERNAME_FIELD: username, "action": action}
    if kwargs:
        payload.update(**kwargs)
    token = signing.dumps(payload)
    return token


def get_payload_from_token(token, action, exp=None):
    payload = signing.loads(token, max_age=exp)
    _action = payload.pop("action")
    if _action != action:
        raise TokenScopeError
    return payload


def revoke_user_refresh_token(user):
    refresh_tokens = user.refresh_tokens.all()
    for refresh_token in refresh_tokens:
        with contextlib.suppress(Exception):
            refresh_token.revoke()


def fields_names(strawberry_fields: Iterable[StrawberryField]):
    return [field.python_name for field in strawberry_fields]


def inject_fields(fields: typing.Iterable[StrawberryField], annotations_only=False):
    def wrapped(cls: type):
        # python 3.8 compat:
        if not hasattr(cls, "__annotations__"):  # pragma: no cover
            cls.__annotations__ = {}

        for field in fields:
            if not field.name:
                continue
            if not annotations_only:
                setattr(cls, field.name, field)
            assert field.type_annotation
            cls.__annotations__[field.name] = field.type_annotation.annotation
        return cls

    return wrapped


def inject_arguments(args: Dict[str, type]):
    """injects arguments to the decorated resolver.

    :param args: `dict[name, type]` of arguments to be injected.,
    """

    def wrapped(fn):
        sig = inspect.signature(fn)
        params = {
            inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=type_)
            for name, type_ in args.items()
        }
        params.update(sig.parameters.values())
        fn.__signature__ = inspect.signature(fn).replace(parameters=params)
        return fn

    return wrapped
