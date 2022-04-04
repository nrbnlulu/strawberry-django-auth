import warnings
import inspect
from django.core import signing
from django.conf import settings as django_settings
from strawberry.annotation import StrawberryAnnotation
from strawberry.utils.str_converters import to_camel_case
from strawberry.arguments import StrawberryArgument, UNSET
from .exceptions import TokenScopeError


def hide_args_kwargs(field):
    sig = inspect.signature(field)
    cleared = tuple(
        p for p in sig.parameters.values() if p.name not in ('kwargs', 'args')
    )
    field.__signature__ = inspect.signature(field).replace(parameters=(cleared))
    return field

def isiterable(value):
    try:
        iter(value)
    except TypeError:
        return False
    return True

def camelize(data):
    if isinstance(data, dict):
        return {to_camel_case(k): camelize(v) for k, v in data.items()}
    if isiterable(data) and not isinstance(data, str):
        return [camelize(d) for d in data]
    return data

def list_to_dict(lst: [str]):
    """takes list of string and creates a dict with str as their values"""
    new_dict = {}
    for item in lst:
        new_dict[item] = str
    return new_dict

warnings.simplefilter("once")


def g_user(info):
    # returns a user from info obj
    user = getattr(info.context, 'user', False)
    if user: return user
    return info.context.request.user


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



def using_refresh_tokens():
    if (
            hasattr(django_settings, "GRAPHQL_JWT")
            and django_settings.GRAPHQL_JWT.get("JWT_LONG_RUNNING_REFRESH_TOKEN", False)
            and "strawberry_django_jwt.refresh_token"
            in django_settings.INSTALLED_APPS
    ):
        return True
    return False


def revoke_user_refresh_token(user):
    if using_refresh_tokens():
        refresh_tokens = user.refresh_tokens.all()
        for refresh_token in refresh_tokens:
            try:
                refresh_token.revoke()
            except Exception:  # JSONWebTokenError
                pass


def flat_dict(dict_or_list):
    """
    if is dict, return list of dict keys,
    if is list, return the list
    """
    return list(dict_or_list.keys()) if isinstance(dict_or_list, dict) else dict_or_list


def normalize_fields(dict_or_list, extra_list_or_dict):
    """
    helper merge settings defined fileds
    with default str type
    """
    if not isinstance(extra_list_or_dict, dict):
        extra_list_or_dict = list_to_dict(extra_list_or_dict)
    if not isinstance(dict_or_list, dict):
        dict_or_list = list_to_dict(dict_or_list)
    dict_or_list.update(extra_list_or_dict)

    return dict_or_list






def create_strawberry_argument(
        python_name: str, graphql_name: str, type_, default=None
):
    return StrawberryArgument(
        python_name=python_name,
        graphql_name=graphql_name,
        type_annotation=StrawberryAnnotation(type_),
        default=default or UNSET
    )
