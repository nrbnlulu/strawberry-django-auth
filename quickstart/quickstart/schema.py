# quickstart.schema.py
import strawberry

from gqlauth.core.field_ import GqlAuthRootField
from gqlauth.core.types_ import AuthOutput
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
    @GqlAuthRootField()
    def auth_entry(self) -> AuthOutput[MyAuthorizedQueries]:
        return AuthOutput(success=True, node=MyAuthorizedQueries())


@strawberry.type
class AuthMutation:
    verify_token = mutations.VerifyToken.field
    update_account = mutations.UpdateAccount.field
    archive_account = mutations.ArchiveAccount.field
    delete_account = mutations.DeleteAccount.field
    password_change = mutations.PasswordChange.field
    swap_emails = mutations.SwapEmails.field
    remove_secondary_email = mutations.RemoveSecondaryEmail.field
    send_secondary_email_activation = mutations.SendSecondaryEmailActivation.field


@strawberry.type
class Mutation:
    @GqlAuthRootField()
    def auth_entry(self) -> AuthOutput[AuthMutation]:
        return AuthOutput(node=AuthMutation())

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
    verify_secondary_email = mutations.VerifySecondaryEmail.field


schema = strawberry.Schema(query=Query, mutation=Mutation)
