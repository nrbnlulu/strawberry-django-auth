import typing
from typing import Union
import inspect
import dataclasses
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string

import strawberry
from strawberry.utils.str_converters import to_camel_case
from gqlauth.settings import gqlauth_settings as app_settings
from gqlauth.utils import create_strawberry_argument
from gqlauth.utils import list_to_dict, hide_args_kwargs
from gqlauth.bases.exceptions import (
    WrongUsage
)
from gqlauth.bases.interfaces import OutputInterface
from gqlauth.bases.scalars import ExpectedErrorType

UserModel = get_user_model()
if app_settings.EMAIL_ASYNC_TASK and isinstance(app_settings.EMAIL_ASYNC_TASK, str):
    async_email_func = import_string(app_settings.EMAIL_ASYNC_TASK)
else:
    async_email_func = None


def make_dataclass_helper(required: dict | list, non_required: dict | list, camelize=True):
    res_req = []
    res_non_req = []

    if isinstance(required, dict):
        if camelize:
            for key in required:
                res_req.append((to_camel_case(key), required[key]))
        else:
            for key in required:
                res_req.append((key, required[key]))

    elif isinstance(required, list):
        if camelize:
            for key in required:
                res_req.append((to_camel_case(key), str))

        else:
            for key in required:
                res_req.append((key, str))

    if isinstance(non_required, dict):
        if camelize:
            for key in non_required:
                res_non_req.append(
                    (to_camel_case(key), typing.Optional[non_required[key]], dataclasses.field(default=None)))
        else:
            for key in non_required:
                res_non_req.append((key, typing.Optional[non_required[key]], dataclasses.field(default=None)))

    elif isinstance(non_required, list):
        if camelize:
            for key in non_required:
                res_non_req.append((to_camel_case(key), typing.Optional[str], dataclasses.field(default=None)))
        else:
            for key in non_required:
                res_non_req.append((key, typing.Optional[str], dataclasses.field(default=None)))

    return res_req + res_non_req


def is_optional(field):
    return typing.get_origin(field) is Union and \
           type(None) in typing.get_args(field)


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

                def resolve_mutation(self, input_):
                    logic...

    """

    def __init_subclass__(cls, **kwargs):
        _inputs = getattr(cls._meta, '_inputs', [])
        _required_inputs = getattr(cls._meta, '_required_inputs', [])

        if _inputs or _required_inputs:
            if not isinstance(_inputs, dict | list) and _inputs:
                raise WrongUsage(f'dynamic inputs can be list or dict not{type(_inputs)}')
            if not isinstance(_required_inputs, dict | list) and _required_inputs:
                raise WrongUsage(f'dynamic required inputs can be list or dict not{type(_required_inputs)}')

        parent_resolver_name = getattr(cls._meta, '_parent_resolver_name', None)
        if parent_resolver_name:
            _inputs = list_to_dict(_inputs)
            _required_inputs = list_to_dict(_required_inputs)

            parent_resolver = getattr(cls, parent_resolver_name, None)
            for name, ret_type in parent_resolver.base_resolver.annotations.items():
                if name != 'return':
                    if is_optional(ret_type):
                        _inputs[name] = typing.get_args(ret_type)[0]
                    else:
                        _required_inputs[name] = ret_type

        if _inputs or _required_inputs:
            dc = dataclasses.make_dataclass(f'{cls.__name__}Input',
                                            [
                                                *make_dataclass_helper(
                                                    _required_inputs, _inputs),
                                            ]
                                            )

            inputs = strawberry.input(dc)
            setattr(cls._meta, 'inputs', inputs)
        else:
            setattr(cls._meta, 'inputs', None)
        super().__init_subclass__()

    def Field(self):
        raise NotImplemented


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

                def resolve_mutation(self, input_):
                    logic...

    """

    def __init_subclass__(cls, **kwargs):
        _inputs = getattr(cls._meta, '_inputs', [])
        _required_inputs = getattr(cls._meta, '_required_inputs', [])

        if _inputs or _required_inputs:
            if not isinstance(_inputs, dict | list) and _inputs:
                raise WrongUsage(f'dynamic inputs can be list or dict not{type(_inputs)}')
            if not isinstance(_required_inputs, dict | list) and _required_inputs:
                raise WrongUsage(f'dynamic required inputs can be list or dict not{type(_required_inputs)}')

        parent_resolver_name = getattr(cls._meta, '_parent_resolver_name', None)
        if parent_resolver_name:
            _inputs = list_to_dict(_inputs)
            _required_inputs = list_to_dict(_required_inputs)

            parent_resolver = getattr(cls, parent_resolver_name, None)
            for name, ret_type in parent_resolver.base_resolver.annotations.items():
                if name != 'return':
                    if is_optional(ret_type):
                        _inputs[name] = typing.get_args(ret_type)[0]
                    else:
                        _required_inputs[name] = ret_type

        if _inputs or _required_inputs:

            args = make_dataclass_helper(
                _required_inputs, _inputs)

            setattr(cls._meta, 'args', args)
        else:
            setattr(cls._meta, 'args', [])
        super().__init_subclass__()

    @property
    def Field(self):
        raise NotImplemented(
            'This mimxin has to be mixed with either `DynamicRelayMutationMixin`,'
            ' or `DynamicDefaultMutationMixin`')


class DynamicPayloadMixin:
    """
        A class that knows how to initialize strawberry
        payload from a list or dict
        and to merge parent payload to the given payload

        as dict { payload_name: payload_type }
        as list [input_name,] -> defaults to String

        #usage:
            class SomeMutation(DynamicInputMixin, OutputMixin, MutationMixin):
                    _outputs = [some, non, required, fields]
                    _required_outputs = {some:str, required:int, fields:list}

                    def resolve_mutation(self, input_):
                        logic...
        """

    def __init_subclass__(cls, **kwargs):
        _outputs = getattr(cls._meta, '_outputs', [])
        _required_outputs = getattr(cls._meta, '_required_outputs', [])
        if _outputs or _required_outputs:
            if not isinstance(_outputs, dict | list | None) and _outputs:
                raise WrongUsage(f'dynamic outputs can be list or dict not{type(_outputs)}')
            if not isinstance(_required_outputs, dict | list | None) and _required_outputs:
                raise WrongUsage(f'dynamic required outputs can be list or dict not{type(_required_outputs)}')

        parent_resolver_name = getattr(cls._meta, '_parent_resolver_name', None)
        if parent_resolver_name:
            parent_resolver = getattr(cls, parent_resolver_name, None)
            new_dict = {}
            if isinstance(_outputs, list):
                # must create a dict for non str types
                for output in _outputs:
                    new_dict[output] = str
                _outputs = new_dict

            _outputs[parent_resolver_name + 'Payload'] = parent_resolver.type

        if _outputs or _required_outputs:
            dc = dataclasses.make_dataclass(f'{cls.__name__}Outputs',
                                            [
                                                ('success', bool),
                                                *make_dataclass_helper(
                                                    _required_outputs, _outputs),
                                                ('errors', typing.Optional[ExpectedErrorType],
                                                 dataclasses.field(default=None)),
                                            ],
                                            namespace={
                                                'get': lambda self, attr: self.__getattribute__(attr)
                                            }
                                            )
            outputs = strawberry.type(dc)
        else:
            outputs = strawberry.type(OutputInterface)

        setattr(cls, 'output', outputs)
        super().__init_subclass__()

    @property
    def Field(self):
        raise NotImplemented('This mimxin has to be mixed with either `DynamicRelayMutationMixin`,'
                             ' or `DynamicDefaultMutationMixin`')


class DynamicRelayMutationMixin:
    def __init_subclass__(cls, **kwargs):
        @strawberry.mutation(description=cls.__doc__)
        def Field(info, input_: cls._meta.inputs) -> cls.output:
            arguments = {f.name: getattr(input_, f.name) for f in dataclasses.fields(input_)}
            return cls.resolve_mutation(info, **arguments)

        if Field.arguments[0].type is None: Field.arguments.pop(0)  # if no input
        setattr(cls, 'Field', Field)

    def resolve_mutation(self, info, **kwargs):
        raise NotImplemented('This has method has to be implemented by the logic delegated mixin')


class DynamicArgsMutationMixin:
    def __init_subclass__(cls, **kwargs):
        def Field(info, **kwargs) -> cls.output:
            return cls.resolve_mutation(info, **kwargs)

        Field = hide_args_kwargs(Field)
        Field = strawberry.mutation(Field, description=cls.__doc__)

        for arg_tuple in cls._meta.args:
            arg = create_strawberry_argument(arg_tuple[0], arg_tuple[0], arg_tuple[1])
            Field.arguments.append(arg)
        setattr(cls, 'Field', Field)

    def resolve_mutation(self, info, *args, **kwargs):
        raise NotImplemented('This has method has to be implemented by the logic delegated mixin')



