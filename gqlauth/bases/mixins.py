import dataclasses
import typing

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
import strawberry
from strawberry.types import Info

from gqlauth.bases.exceptions import WrongUsage
from gqlauth.bases.interfaces import OutputInterface
from gqlauth.bases.scalars import ExpectedErrorType
from gqlauth.utils import (
    create_strawberry_argument,
    hide_args_kwargs,
    is_optional,
    list_to_dict,
    make_dataclass_helper,
)

UserModel = get_user_model()


class DynamicInputMixin:
    """
    A class that knows how to initialize strawberry input

    as dict { arg name: arg type }
    as list [arg_name,] -> defaults to String

    ### usage:
        class SomeMutation(DynamicInputMixin, MutationMixin):
                class _meta:
                    _inputs = [some, non, required, fields]
                    _required_inputs = {some:str, required:int, fields:list}

                def resolve_mutation(self, input):
                    logic...

    """

    def __init_subclass__(cls, **kwargs):
        _inputs = getattr(cls._meta, "_inputs", [])
        _required_inputs = getattr(cls._meta, "_required_inputs", [])

        if _inputs or _required_inputs:
            if not isinstance(_inputs, (dict, list)) and _inputs:
                raise WrongUsage(f"dynamic inputs can be list or dict not{type(_inputs)}")
            if not isinstance(_required_inputs, (dict, list)) and _required_inputs:
                raise WrongUsage(
                    f"dynamic required inputs can be list or dict" f" not{type(_required_inputs)}"
                )

        parent_resolver_name = getattr(cls._meta, "_parent_resolver_name", None)
        if parent_resolver_name:
            _inputs = list_to_dict(_inputs)
            _required_inputs = list_to_dict(_required_inputs)

            parent_resolver = getattr(cls, parent_resolver_name, None)
            for name, ret_type in parent_resolver.base_resolver.annotations.items():
                if name != "return":
                    if is_optional(ret_type):
                        _inputs[name] = typing.get_args(ret_type)[0]
                    else:
                        _required_inputs[name] = ret_type

        if _inputs or _required_inputs:
            dc = dataclasses.make_dataclass(
                f"{cls.__name__}Input",
                [
                    *make_dataclass_helper(_required_inputs, _inputs),
                ],
            )

            inputs = strawberry.input(dc)
            cls._meta.inputs = inputs
        else:
            cls._meta.inputs = None
        super().__init_subclass__()

    def field(self):
        raise NotImplementedError()

    async def afield(self):
        raise NotImplementedError()


class DynamicArgsMixin:
    """
    A class that knows how to initialize strawberry arguments

    as dict { arg name: arg type }
    as list [arg_name,]  defaults to String

    ### usage:
        class SomeMutation(DynamicInputMixin, MutationMixin):
                class _meta:
                    _inputs = [some, non, required, fields]
                    _required_inputs = {some:str, required:int, fields:list}

                def resolve_mutation(self, input):
                    logic...

    """

    def __init_subclass__(cls, **kwargs):
        _inputs = getattr(cls._meta, "_inputs", [])
        _required_inputs = getattr(cls._meta, "_required_inputs", [])

        if _inputs or _required_inputs:
            if not isinstance(_inputs, (dict, list)) and _inputs:
                raise WrongUsage(f"dynamic inputs can be list or dict not{type(_inputs)}")
            if not isinstance(_required_inputs, (dict, list)) and _required_inputs:
                raise WrongUsage(
                    f"dynamic required inputs" f" can be list or dict not{type(_required_inputs)}"
                )

        parent_resolver_name = getattr(cls._meta, "_parent_resolver_name", None)
        if parent_resolver_name:
            _inputs = list_to_dict(_inputs)
            _required_inputs = list_to_dict(_required_inputs)

            parent_resolver = getattr(cls, parent_resolver_name, None)
            for name, ret_type in parent_resolver.base_resolver.annotations.items():
                if name != "return":
                    if is_optional(ret_type):
                        _inputs[name] = typing.get_args(ret_type)[0]
                    else:
                        _required_inputs[name] = ret_type

        if _inputs or _required_inputs:

            args = make_dataclass_helper(_required_inputs, _inputs)

            cls._meta.args = args
        else:
            cls._meta.args = []
        super().__init_subclass__()

    def field(self):
        raise NotImplementedError(
            "This mixin has to be mixed with either `DynamicRelayMutationMixin`,"
            " or `DynamicDefaultMutationMixin`"
        )

    async def afield(self):
        raise NotImplementedError()


class DynamicPayloadMixin:
    """
    A class that knows how to initialize strawberry
    payload from a list or dict
    and to merge parent payload to the given payload

    as dict { payload_name: payload_type }.
    as list [output_name,] -> defaults to String.
    or from the resolve_mutation return annotation.

    #usage:
        class SomeMutation(DynamicInputMixin, OutputMixin, MutationMixin):
                _outputs = [some, non, required, fields]
                _required_outputs = {some:str, required:int, fields:list}

                def resolve_mutation(self, input) -> SomeType:
                    logic...
    """

    def __init_subclass__(cls, **kwargs):
        _outputs = getattr(cls._meta, "_outputs", [])
        _required_outputs = getattr(cls._meta, "_required_outputs", [])

        if _outputs or _required_outputs:
            if not isinstance(_outputs, (dict, list, None)) and _outputs:
                raise WrongUsage(f"dynamic outputs can be list or dict not{type(_outputs)}")
            if not isinstance(_required_outputs, (dict, list, None)) and _required_outputs:
                raise WrongUsage(
                    f"dynamic required" f" outputs can be list or dict not{type(_required_outputs)}"
                )

        parent_resolver_name = getattr(cls._meta, "_parent_resolver_name", None)
        if parent_resolver_name:
            parent_resolver = getattr(cls, parent_resolver_name, None)
            new_dict = {}
            if isinstance(_outputs, list):
                # must create a dict for non str types
                for output in _outputs:
                    new_dict[output] = str
                _outputs = new_dict

            _outputs[parent_resolver_name + "Payload"] = parent_resolver.type

        if _outputs or _required_outputs:
            dc = dataclasses.make_dataclass(
                f"{cls.__name__}Outputs",
                [
                    ("success", bool),
                    *make_dataclass_helper(_required_outputs, _outputs),
                    (
                        "errors",
                        typing.Optional[ExpectedErrorType],
                        dataclasses.field(default=None),
                    ),
                ],
                namespace={"get": lambda self, attr: self.__getattribute__(attr)},
            )
            outputs = strawberry.type(dc)
        else:
            outputs = strawberry.type(OutputInterface)

        cls.output = outputs
        super().__init_subclass__()

    @property
    def field(self):
        raise NotImplementedError()(
            "This mimxin has to be mixed with either `DynamicRelayMutationMixin`,"
            " or `DynamicDefaultMutationMixin`"
        )


class DynamicRelayMutationMixin:
    def __init_subclass__(cls, **kwargs):
        @strawberry.mutation(description=cls.__doc__)
        def field(info: Info, input: cls._meta.inputs) -> cls.output:  # noqa: A002
            arguments = {f.name: getattr(input, f.name) for f in dataclasses.fields(input)}
            return cls.resolve_mutation(info, **arguments)

        if field.arguments[0].type is None:
            field.arguments.pop(0)  # if no input
        cls.field = field

        @strawberry.mutation(description=cls.__doc__)
        async def afield(info: Info, input: cls._meta.inputs) -> cls.output:  # noqa: A002
            arguments = {f.name: getattr(input, f.name) for f in dataclasses.fields(input)}
            return await sync_to_async(cls.resolve_mutation)(info, **arguments)

        if afield.arguments[0].type is None:
            afield.arguments.pop(0)  # if no input
        cls.afield = afield

    def resolve_mutation(self, info, **kwargs):
        raise NotImplementedError()(
            "This has method has to be implemented by the logic delegated mixin"
        )


class DynamicArgsMutationMixin:
    def __init_subclass__(cls, **kwargs):
        def field(info: Info, **kwargs) -> cls.output:
            return cls.resolve_mutation(info, **kwargs)

        field = hide_args_kwargs(field)
        field = strawberry.mutation(field, description=cls.__doc__)

        for arg_tuple in cls._meta.args:
            arg = create_strawberry_argument(arg_tuple[0], arg_tuple[0], arg_tuple[1])
            field.arguments.append(arg)
        cls.field = field

        async def afield(info: Info, **kwargs) -> cls.output:
            return await sync_to_async(cls.resolve_mutation)(info, **kwargs)

        afield = hide_args_kwargs(afield)
        afield = strawberry.mutation(afield, description=cls.__doc__)

        for arg_tuple in cls._meta.args:
            arg = create_strawberry_argument(arg_tuple[0], arg_tuple[0], arg_tuple[1])
            afield.arguments.append(arg)
        cls.afield = afield

    def resolve_mutation(self, info, *args, **kwargs):
        raise NotImplementedError()(
            "This has method has to be implemented by the logic delegated mixin"
        )
