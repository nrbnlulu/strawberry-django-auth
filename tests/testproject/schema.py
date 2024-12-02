from typing import AsyncGenerator

import strawberry
import strawberry_django
from strawberry.types import Info
from strawberry_django.permissions import IsAuthenticated

from gqlauth.core.middlewares import JwtSchema
from gqlauth.core.utils import get_user
from gqlauth.user import arg_mutations
from gqlauth.user.arg_mutations import Captcha
from gqlauth.user.queries import UserQueries
from tests.testproject.sample.models import Apple


@strawberry_django.type(model=Apple)
class AppleType:
    color: strawberry.auto
    name: strawberry.auto
    is_eaten: strawberry.auto


@strawberry.type
class Mutation:
    @strawberry_django.field(directives=[IsAuthenticated])
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
    @strawberry_django.field(
        directives=[
            IsAuthenticated(),
        ]
    )
    def whatsMyUserName(self, info: Info) -> str:
        return get_user(info).username

    @strawberry.field()
    def amIAnonymous(self, info: Info) -> bool:
        user = get_user(info)
        return not user.is_authenticated


@strawberry.type
class Subscription:
    @strawberry.subscription()
    async def whatsMyName(
        self, info: Info, target: int = 10
    ) -> AsyncGenerator[str, None]:
        user = get_user(info)
        assert user.is_authenticated
        for _ in range(target):
            yield get_user(info).username


arg_schema = JwtSchema(query=Query, mutation=Mutation, subscription=Subscription)
