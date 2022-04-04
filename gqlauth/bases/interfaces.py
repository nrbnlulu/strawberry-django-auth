import typing

import strawberry
from gqlauth.bases.scalars import ExpectedErrorType


@strawberry.interface
class OutputInterface:
    """
    A class to all public classes extend to
    padronize the output
    """
    success: bool
    errors: typing.Optional[ExpectedErrorType] = None

class MutationMixin:
    """
    All user should extend this class
    """

    @classmethod
    def mutate(cls, root, info, **input):
        return cls.resolve_mutation(root, info, **input)

    @classmethod
    def parent_resolve(cls, root, info, **kwargs):
        return super().mutate(root, info, **kwargs)


class DynamicArgsMixin:
    """
    A class that knows how to initialize graphene arguments

    get args from
        cls._args
        cls._required_args
    args is dict { arg_name: arg_type }
    or list [arg_name,] -> defaults to String
    """

    _args = {}
    _required_args = {}

    def __init_subclass__(cls, **kwargs):
        if isinstance(cls._args, dict):
            for key in cls._args:
                setattr(cls, key)
        elif isinstance(cls._args, list):
            for key in cls._args:
                cls._meta.arguments.update({key: graphene.String()})

        if isinstance(cls._required_args, dict):
            for key in cls._required_args:
                cls._meta.arguments.update(
                    {
                        key: graphene.Argument(
                            getattr(graphene, cls._required_args[key]), required=True
                        )
                    }
                )
        elif isinstance(cls._required_args, list):
            for key in cls._required_args:
                cls._meta.arguments.update({key: graphene.String(required=True)})
        return super().Field(*args, **kwargs)


