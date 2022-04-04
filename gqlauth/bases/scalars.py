from gqlauth.utils import camelize
import strawberry
from gqlauth.bases.exceptions import WrongUsage




def serialize_excpected_error(errors):
    if isinstance(errors, dict):
        if errors.get("__all__", False):
            errors["non_field_errors"] = errors.pop("__all__")
        return camelize(errors)
    elif isinstance(errors, list):
        return {"nonFieldErrors": errors}
    raise WrongUsage("`errors` must be list or dict!")


@strawberry.scalar(name='ExpectedError',
                   serialize=lambda value: serialize_excpected_error(value),
                   parse_value=lambda value: ExpectedErrorType(value)
                   )
class ExpectedErrorType:
    """
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
    """
    pass

