from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import Callable, Protocol

from strawberry.types import Info


class GqlAuthBackendABC(ABC):
    """Abstract class for all mutations logic."""

    @abstractmethod
    def unarchived(self, user: UserProto) -> None:
        raise NotImplementedError

    @abstractmethod
    def verify(self, token: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def archive(cls, user: UserProto) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_email_context(self, info: Info, path, action, **kwargs) -> dict:
        raise NotImplementedError


class StatusEnum(enum.Enum):
    VERIFIED, UNVERIFIED, ARCHIVED = range(3)


class UserProto(Protocol):
    status: StatusEnum
    is_verified: Callable[[], bool]
    is_unverified: Callable[[], bool]
    is_archived: Callable[[], bool]


UserProto: UserProto = "UserProto"  # type: ignore  # noqa: F811
