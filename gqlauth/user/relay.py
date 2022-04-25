from gqlauth.bases.mixins import (
    DynamicRelayMutationMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
)
from strawberry_django_jwt.mutations import ObtainJSONWebToken as JwtObtainParent
from strawberry_django_jwt.mutations import Verify as VerifyParent
from strawberry_django_jwt.mutations import Refresh as RefreshParent
from strawberry_django_jwt.mutations import Revoke as RevokeParent


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
    Cap,
)


class Register(
    RegisterMixin, DynamicInputMixin, DynamicPayloadMixin, DynamicRelayMutationMixin
):
    __doc__ = RegisterMixin.__doc__


class VerifyAccount(
    VerifyAccountMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = VerifyAccountMixin.__doc__


class ResendActivationEmail(
    ResendActivationEmailMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = ResendActivationEmailMixin.__doc__


class SendPasswordResetEmail(
    SendPasswordResetEmailMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = SendPasswordResetEmailMixin.__doc__


class SendSecondaryEmailActivation(
    SendSecondaryEmailActivationMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = SendSecondaryEmailActivationMixin.__doc__


class VerifySecondaryEmail(
    VerifySecondaryEmailMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = VerifySecondaryEmailMixin.__doc__


class SwapEmails(
    SwapEmailsMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = SwapEmailsMixin.__doc__


class RemoveSecondaryEmail(
    RemoveSecondaryEmailMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = RemoveSecondaryEmailMixin.__doc__


class PasswordSet(
    PasswordSetMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = PasswordSetMixin.__doc__


class PasswordReset(
    PasswordResetMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = PasswordResetMixin.__doc__


class ObtainJSONWebToken(
    ObtainJSONWebTokenMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
    JwtObtainParent,
):
    __doc__ = ObtainJSONWebTokenMixin.__doc__


class ArchiveAccount(
    ArchiveAccountMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = ArchiveAccountMixin.__doc__


class DeleteAccount(
    DeleteAccountMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = DeleteAccountMixin.__doc__


class PasswordChange(
    PasswordChangeMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
    JwtObtainParent,
):
    __doc__ = PasswordChangeMixin.__doc__


class UpdateAccount(
    UpdateAccountMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
):
    __doc__ = UpdateAccountMixin.__doc__


class VerifyToken(
    VerifyTokenMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
    VerifyParent,
):
    __doc__ = VerifyTokenMixin.__doc__


class RefreshToken(
    RefreshTokenMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
    RefreshParent,
):
    __doc__ = RefreshTokenMixin.__doc__


class RevokeToken(
    RevokeTokenMixin,
    DynamicInputMixin,
    DynamicPayloadMixin,
    DynamicRelayMutationMixin,
    RevokeParent,
):
    __doc__ = RevokeTokenMixin.__doc__
