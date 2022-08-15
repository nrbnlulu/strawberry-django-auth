import strawberry
from strawberry.tools import merge_types

from gqlauth.user import arg_mutations, relay
from gqlauth.user.arg_mutations import Captcha
from gqlauth.user.queries import UserQueries


@strawberry.type
class AuthMutation:
    captcha = Captcha.field
    token_auth = arg_mutations.ObtainJSONWebToken.field
    verify_token = arg_mutations.VerifyToken.field
    refresh_token = arg_mutations.RefreshToken.field
    revoke_token = arg_mutations.RevokeToken.field
    register = arg_mutations.Register.field
    verify_account = arg_mutations.VerifyAccount.field
    update_account = arg_mutations.UpdateAccount.field
    resend_activation_email = arg_mutations.ResendActivationEmail.field
    archive_account = arg_mutations.ArchiveAccount.field
    delete_account = arg_mutations.DeleteAccount.field
    password_change = arg_mutations.PasswordChange.field
    send_password_reset_email = arg_mutations.SendPasswordResetEmail.field
    password_reset = arg_mutations.PasswordReset.field
    password_set = arg_mutations.PasswordSet.field
    verify_secondary_email = arg_mutations.VerifySecondaryEmail.field
    swap_emails = arg_mutations.SwapEmails.field
    remove_secondary_email = arg_mutations.RemoveSecondaryEmail.field
    send_secondary_email_activation = arg_mutations.SendSecondaryEmailActivation.field


@strawberry.type
class AuthRelayMutation:
    token_auth = relay.ObtainJSONWebToken.field
    verify_token = relay.VerifyToken.field
    refresh_token = relay.RefreshToken.field
    revoke_token = relay.RevokeToken.field
    register = relay.Register.field
    verify_account = relay.VerifyAccount.field
    update_account = relay.UpdateAccount.field
    resend_activation_email = relay.ResendActivationEmail.field
    archive_account = relay.ArchiveAccount.field
    delete_account = relay.DeleteAccount.field
    password_change = relay.PasswordChange.field
    send_password_reset_email = relay.SendPasswordResetEmail.field
    password_reset = relay.PasswordReset.field
    password_set = relay.PasswordSet.field
    verify_secondary_email = relay.VerifySecondaryEmail.field
    swap_emails = relay.SwapEmails.field
    remove_secondary_email = relay.RemoveSecondaryEmail.field
    send_secondary_email_activation = relay.SendSecondaryEmailActivation.field


Query = merge_types("RootQuery", (UserQueries,))

Mutation = merge_types("RootMutation", (AuthMutation,))

RelayMutation = merge_types("RootRelay", (AuthRelayMutation,))

relay_schema = strawberry.Schema(
    query=Query,
    mutation=RelayMutation,
)

arg_schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
