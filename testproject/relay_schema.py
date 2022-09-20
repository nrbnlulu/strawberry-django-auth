from typing import Union

import strawberry

from gqlauth.core.directives import TokenRequired
from gqlauth.core.field_ import field
from gqlauth.core.types_ import GQLAuthError
from gqlauth.user import relay
from gqlauth.user.resolvers import Captcha
from testproject.schema import Query


@strawberry.type
class AuthMutation:
    update_account = relay.UpdateAccount.field
    archive_account = relay.ArchiveAccount.field
    delete_account = relay.DeleteAccount.field
    password_change = relay.PasswordChange.field
    swap_emails = relay.SwapEmails.field
    remove_secondary_email = relay.RemoveSecondaryEmail.field
    send_secondary_email_activation = relay.SendSecondaryEmailActivation.field


@strawberry.type
class Mutation:
    @field(directives=[TokenRequired()])
    def auth_entry(self) -> Union[AuthMutation, GQLAuthError]:
        return AuthMutation()

    captcha = Captcha.field
    token_auth = relay.ObtainJSONWebToken.field
    register = relay.Register.field
    verify_token = relay.VerifyToken.field
    resend_activation_email = relay.ResendActivationEmail.field
    send_password_reset_email = relay.SendPasswordResetEmail.field
    password_reset = relay.PasswordReset.field
    password_set = relay.PasswordSet.field
    refresh_token = relay.RefreshToken.field
    revoke_token = relay.RevokeToken.field
    verify_account = relay.VerifyAccount.field
    verify_secondary_email = relay.VerifySecondaryEmail.field


relay_schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
