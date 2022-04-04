from gqlauth.bases.mixins import (
    DynamicArgsMutationMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
)
from gqlauth.user.resolvers import (
    RegisterMixin,
    VerifyAccountMixin,
    ResendActivationEmailMixin,
    SendPasswordResetEmailMixin,
    PasswordSetMixin,
    PasswordResetMixin,
    ObtainJSONWebTokenMixin,
    ArchiveAccountMixin,
    DeleteAccountMixin,
    PasswordChangeMixin,
    UpdateAccountMixin,
    RefreshTokenMixin,
    VerifyTokenMixin,
    RevokeTokenMixin,
    SendSecondaryEmailActivationMixin,
    VerifySecondaryEmailMixin,
    SwapEmailsMixin,
    RemoveSecondaryEmailMixin,
)
class Register(
    RegisterMixin, DynamicArgsMixin, DynamicPayloadMixin, DynamicArgsMutationMixin
):
    __doc__ = RegisterMixin.__doc__

from strawberry_django_jwt.mutations import  Verify as VerifyParent
class VerifyAccount(
    VerifyAccountMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
    VerifyParent
):
    __doc__ = VerifyAccountMixin.__doc__



class ResendActivationEmail(
    ResendActivationEmailMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin
):
    __doc__ = ResendActivationEmailMixin.__doc__



class SendPasswordResetEmail(
    SendPasswordResetEmailMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin
):
    __doc__ = SendPasswordResetEmailMixin.__doc__



class SendSecondaryEmailActivation(
    SendSecondaryEmailActivationMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = SendSecondaryEmailActivationMixin.__doc__



class VerifySecondaryEmail(
    VerifySecondaryEmailMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = VerifySecondaryEmailMixin.__doc__



class SwapEmails(
    SwapEmailsMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = SwapEmailsMixin.__doc__



class RemoveSecondaryEmail(
    RemoveSecondaryEmailMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = RemoveSecondaryEmailMixin.__doc__



class PasswordSet(
    PasswordSetMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = PasswordSetMixin.__doc__



class PasswordReset(
    PasswordResetMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = PasswordResetMixin.__doc__

from strawberry_django_jwt.mutations import ObtainJSONWebToken as JwtObtainParent
class ObtainJSONWebToken(
    ObtainJSONWebTokenMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
    JwtObtainParent,
):
    __doc__ = ObtainJSONWebTokenMixin.__doc__




class ArchiveAccount(
    ArchiveAccountMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = ArchiveAccountMixin.__doc__



class DeleteAccount(
    DeleteAccountMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = DeleteAccountMixin.__doc__



class PasswordChange(
    PasswordChangeMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
    JwtObtainParent
):
    __doc__ = PasswordChangeMixin.__doc__



class UpdateAccount(
    UpdateAccountMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
):
    __doc__ = UpdateAccountMixin.__doc__


from strawberry_django_jwt.mutations import Verify as VerifyParent
class VerifyToken(
    VerifyTokenMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
    VerifyParent
):
    __doc__ = VerifyTokenMixin.__doc__



from strawberry_django_jwt.mutations import Refresh
class RefreshToken(
    RefreshTokenMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
    Refresh
):
    __doc__ = RefreshTokenMixin.__doc__


from strawberry_django_jwt.mutations import Revoke as RevokeParent

class RevokeToken(
    RevokeTokenMixin,
    DynamicArgsMixin,
    DynamicPayloadMixin,
    DynamicArgsMutationMixin,
    RevokeParent
):
    __doc__ = RevokeTokenMixin.__doc__

