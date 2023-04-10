from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Protocol

from strawberry.types import Info


class GqlAuthBackendABC(ABC):
    """Abstract class for GraphQL backend logic implementor."""

    @abstractmethod
    def get_user_from_payload(self, payload: dict) -> UserProto:
        raise NotImplementedError

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

    @abstractmethod
    def send_email(
        self,
        subject: str,
        template: str,
        context: dict[str, Any],
        recipient_list: list[str] | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_activation_email(self, info: Info, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def resend_activation_email(self, info: Info, user: UserProto, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_password_set_email(self, info: Info, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_password_reset_email(self, info: Info, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def revoke_user_refresh_token(self, user: UserProto) -> None:
        raise NotImplementedError


class UserProto(Protocol):
    is_verified: Callable[[], bool]
    set_verified: Callable[[bool], None]
    is_archived: Callable[[], bool]
    set_archived: Callable[[bool], None]
    delete: Callable[[], None]
    USERNAME_FIELD: str
    EMAIL_FIELD: str | None


UserProto: UserProto = "UserProto"  # type: ignore  # noqa: F811
