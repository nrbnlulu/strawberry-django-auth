from typing import TypeVar

import strawberry

from gqlauth.core.scalars import ExpectedErrorType

T = TypeVar("T")


@strawberry.interface
class OutputInterface:
    success: bool
    errors: ExpectedErrorType | None
