from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Protocol,
)

from strawberry.types import Info

if TYPE_CHECKING:
    from gqlauth.core.types_ import CaptchaErrorCodes


class GqlAuthBackendABC(ABC):
    """Abstract class for GraphQL backend logic implementor."""

    LOGIN_INPUT_TYPE: type | None = None

    @abstractmethod
    def login(self, info: Info, input: LOGIN_INPUT_TYPE | Any) -> UserProto | None:
        raise NotImplementedError

    @abstractmethod
    def get_user_from_payload(self, payload: dict) -> UserProto:
        raise NotImplementedError

    @abstractmethod
    def unarchived(self, user: UserProto) -> None:
        raise NotImplementedError

    @abstractmethod
    def verify(self, token: str) -> None:
        """
        :raises UserAlreadyVerified, TokenScopeError:
        """
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
        user: UserProto,
        subject: str,
        template: str,
        context: dict[str, Any],
        recipient_list: list[str] | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_activation_email(self, user: UserProto, info: Info, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def resend_activation_email(self, user: UserProto, info: Info, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_password_set_email(self, user: UserProto, info: Info, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_password_reset_email(self, user: UserProto, info: Info, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def revoke_user_refresh_token(self, user: UserProto) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_email(self, email: str) -> UserProto:
        raise NotImplementedError

    @abstractmethod
    def validate_captcha(self, uuid: uuid.UUID, user_input: str) -> CaptchaErrorCodes | None:
        raise NotImplementedError


class UserProto(Protocol):
    is_verified: bool
    set_verified: Callable[[bool], None]
    is_archived: bool
    set_archived: Callable[[bool], None]
    delete: Callable[[], None]
    USERNAME_FIELD: str
    EMAIL_FIELD: str | None

    is_anonymous: bool
    """If this is not a user from the database this would be true."""


UserProto: UserProto = "UserProto"  # type: ignore  # noqa: F811
