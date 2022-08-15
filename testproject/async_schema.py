import strawberry
from strawberry.tools import merge_types

from gqlauth.user import arg_mutations, relay
from gqlauth.user.queries import UserQueries


@strawberry.type
class AuthMutation:
    token_auth = arg_mutations.ObtainJSONWebToken.afield
    verify_token = arg_mutations.VerifyToken.afield
    refresh_token = arg_mutations.RefreshToken.afield
    revoke_token = arg_mutations.RevokeToken.afield
    register = arg_mutations.Register.afield
    verify_account = arg_mutations.VerifyAccount.afield
    update_account = arg_mutations.UpdateAccount.afield
    resend_activation_email = arg_mutations.ResendActivationEmail.afield
    archive_account = arg_mutations.ArchiveAccount.afield
    delete_account = arg_mutations.DeleteAccount.afield
    password_change = arg_mutations.PasswordChange.afield
    send_password_reset_email = arg_mutations.SendPasswordResetEmail.afield
    password_reset = arg_mutations.PasswordReset.afield
    password_set = arg_mutations.PasswordSet.afield
    verify_secondary_email = arg_mutations.VerifySecondaryEmail.afield
    swap_emails = arg_mutations.SwapEmails.afield
    remove_secondary_email = arg_mutations.RemoveSecondaryEmail.afield
    send_secondary_email_activation = arg_mutations.SendSecondaryEmailActivation.afield


@strawberry.type
class AuthRelayMutation:
    token_auth = relay.ObtainJSONWebToken.afield
    verify_token = relay.VerifyToken.afield
    refresh_token = relay.RefreshToken.afield
    revoke_token = relay.RevokeToken.afield
    register = relay.Register.afield
    verify_account = relay.VerifyAccount.afield
    update_account = relay.UpdateAccount.afield
    resend_activation_email = relay.ResendActivationEmail.afield
    archive_account = relay.ArchiveAccount.afield
    delete_account = relay.DeleteAccount.afield
    password_change = relay.PasswordChange.afield
    send_password_reset_email = relay.SendPasswordResetEmail.afield
    password_reset = relay.PasswordReset.afield
    password_set = relay.PasswordSet.afield
    verify_secondary_email = relay.VerifySecondaryEmail.afield
    swap_emails = relay.SwapEmails.afield
    remove_secondary_email = relay.RemoveSecondaryEmail.afield
    send_secondary_email_activation = relay.SendSecondaryEmailActivation.afield


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
