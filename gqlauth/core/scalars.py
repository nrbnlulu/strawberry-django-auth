import typing
from base64 import b64decode, b64encode

import strawberry
from PIL.Image import Image

from gqlauth.core.exceptions import WrongUsage
from gqlauth.core.utils import camelize


def serialize_excpected_error(errors):
    if isinstance(errors, dict):
        if errors.get("__all__", False):
            errors["non_field_errors"] = errors.pop("__all__")
        return camelize(errors)
    elif isinstance(errors, list):
        return {"nonFieldErrors": errors}
    raise WrongUsage("`errors` must be list or dict!")


ExpectedErrorType = strawberry.scalar(
    typing.NewType("ExpectedError", dict),
    description="""
     Errors messages and codes mapped to
    fields or non fields errors.
    Example:
    {
        field_name: [
            {
                "message": "error message",
                "code": "error_code"
            }
        ],
        other_field: [
            {
                "message": "error message",
                "code": "error_code"
            }
        ],
        nonFieldErrors: [
            {
                "message": "error message",
                "code": "error_code"
            }
        ]
    }
    """,
    serialize=lambda value: serialize_excpected_error(value),
    parse_value=lambda value: value,
)

image = strawberry.scalar(
    typing.NewType("image", Image),
    serialize=lambda v: b64encode(v).decode("ascii"),
    parse_value=lambda v: b64decode(v),
)
