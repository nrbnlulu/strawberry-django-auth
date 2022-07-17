# quickstart.schema.py
import strawberry
from strawberry_django_jwt.middleware import AsyncJSONWebTokenMiddleware

from gqlauth.user import arg_mutations as mutations
from gqlauth.user.queries import UserQueries


@strawberry.type
class AuthMutation:
    register = mutations.Register.afield
    verify_account = mutations.VerifyAccount.afield
    resend_activation_email = mutations.ResendActivationEmail.afield
    send_password_reset_email = mutations.SendPasswordResetEmail.afield
    password_reset = mutations.PasswordReset.afield
    password_set = mutations.PasswordSet.afield
    password_change = mutations.PasswordChange.afield
    archive_account = mutations.ArchiveAccount.afield
    delete_account = mutations.DeleteAccount.afield
    update_account = mutations.UpdateAccount.afield
    send_secondary_email_activation = mutations.SendSecondaryEmailActivation.afield
    verify_secondary_email = mutations.VerifySecondaryEmail.afield
    swap_emails = mutations.SwapEmails.afield
    captcha = mutations.Captcha.afield

    # django-graphql-jwt authentication
    # with some extra features
    token_auth = mutations.ObtainJSONWebToken.afield
    verify_token = mutations.VerifyToken.afield
    refresh_token = mutations.RefreshToken.afield
    revoke_token = mutations.RevokeToken.afield


aschema = strawberry.Schema(
    query=UserQueries,
    mutation=AuthMutation,
    extensions=[
        AsyncJSONWebTokenMiddleware,
    ],
)
