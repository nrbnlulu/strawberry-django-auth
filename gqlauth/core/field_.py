from functools import partial
from typing import Any, AsyncGenerator, Callable, List, Union

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from strawberry import UNSET
from strawberry.field import StrawberryField
from strawberry_django import django_resolver
from strawberry_django.fields.field import StrawberryDjangoField
from strawberry_django.utils import is_async

from gqlauth.core.directives import BaseAuthDirective
from gqlauth.core.types_ import GQLAuthError

__all__ = ["field"]

USER_MODEL = get_user_model()


class GqlAuthField(StrawberryDjangoField):
    def _resolve(self, source, info, args, kwargs) -> Union[GQLAuthError, Any]:
        for directive in self.directives:
            if isinstance(directive, BaseAuthDirective) and (
                error := directive.resolve_permission(source, info, args, kwargs)
            ):
                return error
        return super().get_result(source, info, args, kwargs)

    async def _resolve_subscriptions(
        self, source, info, args, kwargs
    ) -> Union[AsyncGenerator, GQLAuthError]:
        for directive in self.directives:
            if isinstance(directive, BaseAuthDirective) and (
                error := await sync_to_async(directive.resolve_permission)(
                    source, info, args, kwargs
                )
            ):
                yield error
                return
        async for res in super().get_result(source, info, args, kwargs):
            yield res

    def get_result(self, source, info, args, kwargs):
        if self.is_subscription:
            return self._resolve_subscriptions(source, info, args, kwargs)
        elif is_async():
            return sync_to_async(self._resolve)(source, info, args, kwargs)
        return self._resolve(source, info, args, kwargs)


def field(
    resolver=None,
    *,
    name=None,
    field_name=None,
    filters=UNSET,
    default=UNSET,
    directives: List[BaseAuthDirective] = None,
    **kwargs,
) -> Union[StrawberryField, Callable[..., StrawberryField]]:
    field_ = GqlAuthField(
        python_name=None,
        graphql_name=name,
        filters=filters,
        django_name=field_name,
        default=default,
        directives=directives,
        **kwargs,
    )
    if resolver:
        resolver = django_resolver(resolver)
        field_ = field_(resolver)
    return field_


subscription = partial(field, is_subscription=True)
