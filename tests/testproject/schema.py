import strawberry
from strawberry.tools import merge_types

from typing import List

from gqlauth.user import arg_mutations, relay
from gqlauth.user.types import UserType, UserFilter


@strawberry.type
class UserQueries:
    user: UserType = strawberry.django.field()
    users: List[UserType] = strawberry.django.field(filters=UserFilter)


@strawberry.type
class AuthMutation:

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
    captcha = relay.Cap.Field


Query = merge_types("RootQuery", (UserQueries,))

Mutation = merge_types("RootMutation", (AuthMutation,))

schema = strawberry.Schema(query=Query, mutation=Mutation)
