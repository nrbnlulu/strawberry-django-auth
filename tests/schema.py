import strawberry
from strawberry.tools import merge_types
from gqlauth.user.queries import UserQueries
from gqlauth.user import relay, arg_mutations


@strawberry.type
class AuthMutation:
    token_auth = arg_mutations.ObtainJSONWebToken.Field
    verify_token = arg_mutations.VerifyToken.Field
    refresh_token = arg_mutations.RefreshToken.Field
    revoke_token = arg_mutations.RevokeToken.Field
    register = arg_mutations.Register.Field
    verify_account = arg_mutations.VerifyAccount.Field
    update_account = arg_mutations.UpdateAccount.Field
    resend_activation_email = arg_mutations.ResendActivationEmail.Field
    archive_account = arg_mutations.ArchiveAccount.Field
    delete_account = arg_mutations.DeleteAccount.Field
    password_change = arg_mutations.PasswordChange.Field
    send_password_reset_email = arg_mutations.SendPasswordResetEmail.Field
    password_reset = arg_mutations.PasswordReset.Field
    password_set = arg_mutations.PasswordSet.Field
    verify_secondary_email = arg_mutations.VerifySecondaryEmail.Field
    swap_emails = arg_mutations.SwapEmails.Field
    remove_secondary_email = arg_mutations.RemoveSecondaryEmail.Field
    send_secondary_email_activation = arg_mutations.SendSecondaryEmailActivation.Field


@strawberry.type
class AuthRelayMutation:
    token_auth = relay.ObtainJSONWebToken.Field
    verify_token = relay.VerifyToken.Field
    refresh_token = relay.RefreshToken.Field
    revoke_token = relay.RevokeToken.Field
    register = relay.Register.Field
    verify_account = relay.VerifyAccount.Field
    update_account = relay.UpdateAccount.Field
    resend_activation_email = relay.ResendActivationEmail.Field
    archive_account = relay.ArchiveAccount.Field
    delete_account = relay.DeleteAccount.Field
    password_change = relay.PasswordChange.Field
    send_password_reset_email = relay.SendPasswordResetEmail.Field
    password_reset = relay.PasswordReset.Field
    password_set = relay.PasswordSet.Field
    verify_secondary_email = relay.VerifySecondaryEmail.Field
    swap_emails = relay.SwapEmails.Field
    remove_secondary_email = relay.RemoveSecondaryEmail.Field
    send_secondary_email_activation = relay.SendSecondaryEmailActivation.Field


Query = merge_types("RootQuery", (UserQueries,))

Mutation = merge_types("RootMutation", (AuthMutation,))

RelayMutation = merge_types("RootRelay", (AuthRelayMutation,))

relay_schema = strawberry.Schema(query=Query, mutation=RelayMutation)

default_schema = strawberry.Schema(query=Query, mutation=Mutation)
