# quickstart.schema.py
import strawberry
from strawberry.types import Info

from gqlauth.core.field_ import GqlAuthRootField
from gqlauth.core.types_ import AuthOutput
from gqlauth.user import arg_mutations as mutations
from gqlauth.user.queries import UserQueries


@strawberry.type
class AuthMutation:
    resend_activation_email = mutations.ResendActivationEmail.field
    send_password_reset_email = mutations.SendPasswordResetEmail.field
    password_reset = mutations.PasswordReset.field
    password_set = mutations.PasswordSet.field
    password_change = mutations.PasswordChange.field
    archive_account = mutations.ArchiveAccount.field
    delete_account = mutations.DeleteAccount.field
    update_account = mutations.UpdateAccount.field
    send_secondary_email_activation = mutations.SendSecondaryEmailActivation.field
    verify_secondary_email = mutations.VerifySecondaryEmail.field
    swap_emails = mutations.SwapEmails.field
    captcha = mutations.Captcha.field

    verify_token = mutations.VerifyToken.field
    refresh_token = mutations.RefreshToken.field
    revoke_token = mutations.RevokeToken.field


@strawberry.type
class Query:
    @GqlAuthRootField()
    def auth_entry(self, info: Info) -> AuthOutput[UserQueries]:
        return AuthOutput(success=True, data=UserQueries())


@strawberry.type
class Mutation:
    @GqlAuthRootField()
    def auth_entry(self) -> AuthOutput[AuthMutation]:
        return AuthOutput(data=AuthMutation())

    token_auth = mutations.ObtainJSONWebToken.field
    register = mutations.Register.field
    verify_account = mutations.VerifyAccount.field


schema = strawberry.Schema(query=Query, mutation=Mutation)
