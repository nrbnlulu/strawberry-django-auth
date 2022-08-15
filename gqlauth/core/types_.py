from typing import Optional

import strawberry

from gqlauth.core.scalars import ExpectedErrorType


@strawberry.type
class MutationNormalOutput:
    success: bool
    errors: Optional[ExpectedErrorType] = None
