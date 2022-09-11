from typing import Any, Awaitable, Dict, List, Union

from django.contrib.auth import get_user_model
from strawberry.field import StrawberryField
from strawberry.types import Info
from strawberry_django.fields.field import StrawberryDjangoField

from gqlauth.core.constants import Error
from gqlauth.core.directives import BaseAuthDirective
from gqlauth.core.exceptions import TokenExpired
from gqlauth.core.types_ import AuthError, AuthWrapper, ErrorMessage, FieldError
from gqlauth.jwt.types_ import TokenType

__all__ = ["GqlAuthRootField", "GqlAuthField"]

USER_MODEL = get_user_model()


class GqlAuthRootField(StrawberryField):
    def get_result(
        self, source: Any, info: Info, args: List[Any], kwargs: Dict[str, Any]
    ) -> Union[Awaitable[Any], Any]:
        token = info.context.request.headers["Authorization"]
        try:
            token_type = TokenType.from_token(token)
            user = token_type.get_user_instance()
            info.context.user = user
            res = super().get_result(source, info, args, kwargs)
            assert isinstance(res, AuthWrapper)
            info.context.auth_output = res
            return res
        except TokenExpired:
            return AuthWrapper(
                success=False,
                data=None,
                errors=AuthError(non_field_errors=ErrorMessage(code=Error.EXPIRED_TOKEN)),
            )


class GqlAuthField(StrawberryDjangoField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_result(self, source, info, args, kwargs):
        user = info.context.user
        for directive in self.directives:
            if isinstance(directive, BaseAuthDirective) and (
                error := directive.resolve_permission(user, source, info, *args, **kwargs)
            ):
                auth_output: AuthWrapper = info.context.auth_output
                auth_output.errors.field_errors.append(
                    FieldError(field=self.python_name, code=error)
                )
                return None
        return super().get_result(source, info, args, kwargs)
