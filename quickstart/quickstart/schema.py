# quickstart.schema.py

import strawberry
from strawberry_django_plus import gql
from strawberry_django_plus.directives import SchemaDirectiveExtension
from strawberry_django_plus.permissions import IsAuthenticated

from gqlauth.core.directives import IsVerified
from gqlauth.user import arg_mutations as mutations
from gqlauth.user.queries import UserQueries
from gqlauth.user.resolvers import Captcha


@strawberry.type
class MyAuthorizedQueries(UserQueries):
    @strawberry.field
    def secured_string(self) -> str:
        return "secure"


@strawberry.type
class Query:
    @gql.django.field(directives=[IsVerified()])
    def auth_entry(self) -> MyAuthorizedQueries:
        return MyAuthorizedQueries()


@strawberry.type
class AuthMutation:
    verify_token = mutations.VerifyToken.field
    update_account = mutations.UpdateAccount.field
    archive_account = mutations.ArchiveAccount.field
    delete_account = mutations.DeleteAccount.field
    password_change = mutations.PasswordChange.field


@strawberry.type
class Mutation:
    @gql.django.field(directives=[IsAuthenticated()])
    def auth_entry(self) -> AuthMutation:
        return AuthMutation()

    captcha = Captcha.field
    token_auth = mutations.ObtainJSONWebToken.field
    register = mutations.Register.field
    verify_account = mutations.VerifyAccount.field
    resend_activation_email = mutations.ResendActivationEmail.field
    send_password_reset_email = mutations.SendPasswordResetEmail.field
    password_reset = mutations.PasswordReset.field
    password_set = mutations.PasswordSet.field
    refresh_token = mutations.RefreshToken.field
    revoke_token = mutations.RevokeToken.field


schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[SchemaDirectiveExtension])
