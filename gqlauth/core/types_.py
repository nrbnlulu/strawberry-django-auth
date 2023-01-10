from enum import Enum
from typing import Optional, TypeVar

import strawberry
from graphql import GraphQLError

from gqlauth.core.scalars import ExpectedErrorType

T = TypeVar("T")


@strawberry.type
class MutationNormalOutput:
    success: bool
    errors: Optional[ExpectedErrorType] = None


class GQLAuthError(GraphQLError):
    def __init__(self, code: "GQLAuthErrors", *args, **kwargs):
        kwargs["message"] = ""
        super().__init__(*args, **kwargs)
        if not self.message:
            self.message = code.value


class GQLAuthErrors(Enum):
    UNAUTHENTICATED = "Unauthenticated."
    INVALID_TOKEN = "Invalid token."
    EXPIRED_TOKEN = "Expired token."
    NO_SUFFICIENT_PERMISSIONS = "Permissions found could not satisfy the required permissions."
    NOT_VERIFIED = "Please verify your account."
    MISSING_TOKEN = "No JWT found"
