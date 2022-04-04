import strawberry
from strawberry.tools import merge_types

from typing import List

from gqlauth.user import arg_mutations
from gqlauth.user.types import UserType, UserFilter



@strawberry.type
class UserQueries:
    user: UserType = strawberry.django.field()
    users: List[UserType] = strawberry.django.field(filters=UserFilter)

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


Query = merge_types('RootQuery', (UserQueries,))

Mutation = merge_types('RootMutation', (AuthMutation,))

schema = strawberry.Schema(query=Query, mutation=Mutation)
