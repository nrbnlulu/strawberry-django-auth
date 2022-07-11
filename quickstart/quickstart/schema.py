# quickstart.schema.py
import strawberry
from strawberry_django_jwt.middleware import JSONWebTokenMiddleware

from gqlauth.user import arg_mutations as mutations
from gqlauth.user.queries import UserQueries


@strawberry.type
class AuthMutation:
    register = mutations.Register.field
    verify_account = mutations.VerifyAccount.field
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
    captcha = mutations.Cap.field

    # django-graphql-jwt authentication
    # with some extra features
    token_auth = mutations.ObtainJSONWebToken.field
    verify_token = mutations.VerifyToken.field
    refresh_token = mutations.RefreshToken.field
    revoke_token = mutations.RevokeToken.field


schema = strawberry.Schema(
    query=UserQueries,
    mutation=AuthMutation,
    extensions=[
        JSONWebTokenMiddleware,
    ],
)
