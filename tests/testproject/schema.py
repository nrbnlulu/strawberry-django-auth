from typing import List

import strawberry
from strawberry.tools import merge_types

from gqlauth.user import relay
from gqlauth.user.types_ import UserFilter, UserType


@strawberry.type
class UserQueries:
    user: UserType = strawberry.django.field()
    users: List[UserType] = strawberry.django.field(filters=UserFilter)


@strawberry.type
class AuthMutation:
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
    captcha = relay.Cap


Query = merge_types("RootQuery", (UserQueries,))

Mutation = merge_types("RootMutation", (AuthMutation,))

schema = strawberry.Schema(query=Query, mutation=Mutation)
