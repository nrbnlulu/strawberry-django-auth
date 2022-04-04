from . import relay
from . import arg_mutations
import strawberry


@strawberry.type
class UserMutations:
    register = relay.Register.Field
    login = relay.ObtainJSONWebToken.Field
    update_password = relay.PasswordChange.Field
    update_account_relay = relay.UpdateAccount.Field
    verify_token = relay.VerifyToken.Field
    refresh_token = relay.RefreshToken.Field
    revoke_token = relay.RevokeToken.Field
    update_account = arg_mutations.UpdateAccount.Field

