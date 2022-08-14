from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
import strawberry
from strawberry.field import StrawberryField
from strawberry.types import Info

from gqlauth.core.utils import hide_args_kwargs, inject_arguments

UserModel = get_user_model()


class ArgMixin:
    field: StrawberryField
    afield: StrawberryField

    def __init_subclass__(cls, **kwargs):
        input_type = cls.resolve_mutation.__annotations__["input_"]
        return_type = cls.resolve_mutation.__annotations__["return"]

        @strawberry.mutation(description=cls.__doc__)
        @inject_arguments(input_type.__annotations__)
        @hide_args_kwargs
        def field(info: Info, **kwargs) -> return_type:
            return cls.resolve_mutation(info, input_type(**kwargs))

        cls.field = field

        @strawberry.mutation(description=cls.__doc__)
        @inject_arguments(input_type.__annotations__)
        @hide_args_kwargs
        async def afield(info: Info, **kwargs) -> return_type:
            return await sync_to_async(cls.resolve_mutation)(info, input_type(**kwargs))

        cls.afield = afield


class RelayMixin:
    field: StrawberryField
    afield: StrawberryField

    def __init_subclass__(cls, **kwargs):
        input_type = cls.resolve_mutation.__annotations__["input_"]
        return_type = cls.resolve_mutation.__annotations__["return"]

        @strawberry.mutation(description=cls.__doc__)
        @hide_args_kwargs
        def field(info: Info, input: input_type) -> return_type:
            return cls.resolve_mutation(info, input)

        cls.field = field

        @strawberry.mutation(description=cls.__doc__)
        @hide_args_kwargs
        async def afield(info: Info, input: input_type) -> return_type:
            return await sync_to_async(cls.resolve_mutation)(info, input)

        cls.afield = afield
