from typing import Optional

import strawberry
from strawberry_django_jwt.mutations import Refresh as RefreshParent
from strawberry_django_jwt.object_types import TokenDataType
from strawberry_django_jwt.refresh_token.object_types import RevokeType

from gqlauth.core.interfaces import OutputInterface
from gqlauth.core.scalars import ExpectedErrorType

refresh_payload_dt = RefreshParent.refresh.base_resolver.annotations["return"]


@strawberry.type
class ObtainJSONWebTokenPayload(OutputInterface):
    success: bool
    obtainPayload: Optional[TokenDataType] = None
    errors: Optional[ExpectedErrorType] = None


@strawberry.type
class RefreshTokenPayload(OutputInterface):
    success: bool
    refreshPayload: Optional[refresh_payload_dt] = None
    errors: Optional[ExpectedErrorType] = None


@strawberry.type
class MutationNormalOutput:
    success: bool
    errors: Optional[ExpectedErrorType] = None


@strawberry.type
class VerifyTokenPayload(OutputInterface):
    success: bool
    verifyPayload: Optional[TokenDataType] = None
    errors: Optional[ExpectedErrorType] = None


@strawberry.type
class RevokeTokenPayload:
    success: bool
    revokePayload: Optional[RevokeType] = None
    errors: Optional[ExpectedErrorType] = None
