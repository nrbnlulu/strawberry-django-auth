from typing import Optional, TypeVar

import strawberry

from gqlauth.bases.scalars import ExpectedErrorType

T = TypeVar("T")


@strawberry.interface
class OutputInterface:
    success: bool
    errors: Optional[ExpectedErrorType]
