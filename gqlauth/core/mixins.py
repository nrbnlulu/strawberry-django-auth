from django.contrib.auth import get_user_model
from strawberry.field import StrawberryField
from strawberry.types import Info

import gqlauth
from gqlauth.core.utils import hide_args_kwargs, inject_arguments
from gqlauth.user.resolvers import BaseMixin

UserModel = get_user_model()


class ArgMixin:
    field: StrawberryField

    def __init_subclass__(cls: BaseMixin, **kwargs):
        input_type = cls.resolve_mutation.__annotations__["input_"]
        return_type = cls.resolve_mutation.__annotations__["return"]

        @gqlauth.core.field_.field(description=cls.__doc__, directives=cls.directives)
        @inject_arguments(input_type.__annotations__)
        @hide_args_kwargs
        def field(info: Info, **kwargs) -> return_type:
            return cls.resolve_mutation(info, input_type(**kwargs))

        cls.field = field


class RelayMixin:
    field: StrawberryField
    afield: StrawberryField

    def __init_subclass__(cls: BaseMixin, **kwargs):
        input_type = cls.resolve_mutation.__annotations__["input_"]
        return_type = cls.resolve_mutation.__annotations__["return"]

        @gqlauth.core.field_.field(description=cls.__doc__, directives=cls.directives)
        @hide_args_kwargs
        def field(info: Info, input: input_type) -> return_type:
            return cls.resolve_mutation(info, input)

        cls.field = field
