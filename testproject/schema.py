from typing import AsyncGenerator

import strawberry
from strawberry_django_plus import gql
from strawberry_django_plus.directives import SchemaDirectiveExtension
from strawberry_django_plus.permissions import IsAuthenticated

from gqlauth.core.token_to_user import TokenSchema
from gqlauth.user import arg_mutations
from gqlauth.user.arg_mutations import Captcha
from gqlauth.user.queries import UserQueries
from testproject.sample.models import Apple


@gql.django.type(model=Apple)
class AppleType:
    color: strawberry.auto
    name: strawberry.auto
    is_eaten: strawberry.auto


@strawberry.type
class Mutation:
    @gql.django.field(directives=[IsAuthenticated])
    def eat_apple(self, apple_id: int) -> "AppleType":
        apple = Apple.objects.get(id=apple_id)
        apple.is_eaten = True
        apple.save()
        return apple

    verify_token = arg_mutations.VerifyToken.field
    update_account = arg_mutations.UpdateAccount.field
    archive_account = arg_mutations.ArchiveAccount.field
    delete_account = arg_mutations.DeleteAccount.field
    password_change = arg_mutations.PasswordChange.field

    captcha = Captcha.field
    token_auth = arg_mutations.ObtainJSONWebToken.field
    register = arg_mutations.Register.field
    verify_account = arg_mutations.VerifyAccount.field
    resend_activation_email = arg_mutations.ResendActivationEmail.field
    send_password_reset_email = arg_mutations.SendPasswordResetEmail.field
    password_reset = arg_mutations.PasswordReset.field
    password_set = arg_mutations.PasswordSet.field
    refresh_token = arg_mutations.RefreshToken.field
    revoke_token = arg_mutations.RevokeToken.field


@strawberry.type
class Query(UserQueries):
    @gql.django.field(
        directives=[
            IsAuthenticated(),
        ]
    )
    def apple(self) -> AppleType:
        return Apple.objects.latest("pk")


@strawberry.type
class Subscription:
    @strawberry.subscription()
    async def count(self, target: int = 10) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i


arg_schema = TokenSchema(
    query=Query, mutation=Mutation, subscription=Subscription, extensions=[SchemaDirectiveExtension]
)
