# quickstart.schema.py
import strawberry
from gqlauth.user import relay as mutations
from gqlauth.user.queries import UserQueries


@strawberry.type
class AuthMutation:
    register = mutations.Register.Field
    verify_account = mutations.VerifyAccount.Field
    resend_activation_email = mutations.ResendActivationEmail.Field
    send_password_reset_email = mutations.SendPasswordResetEmail.Field
    password_reset = mutations.PasswordReset.Field
    password_set = mutations.PasswordSet.Field
    password_change = mutations.PasswordChange.Field
    archive_account = mutations.ArchiveAccount.Field
    delete_account = mutations.DeleteAccount.Field
    update_account = mutations.UpdateAccount.Field
    send_secondary_email_activation = mutations.SendSecondaryEmailActivation.Field
    verify_secondary_email = mutations.VerifySecondaryEmail.Field
    swap_emails = mutations.SwapEmails.Field
    captcha = mutations.Cap.Field

    # django-graphql-jwt authentication
    # with some extra features
    token_auth = mutations.ObtainJSONWebToken.Field
    verify_token = mutations.VerifyToken.Field
    refresh_token = mutations.RefreshToken.Field
    revoke_token = mutations.RevokeToken.Field


schema = strawberry.Schema(query=UserQueries, mutation=AuthMutation)
