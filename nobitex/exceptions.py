"""
API wrapper exceptions.

All exceptions inherit from :class:`APIError`, which stores the HTTP status code, response body, and optional headers for debugging. Specific subclasses allow granular error handling.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.headers = headers or {}
        super().__init__(message)

    def __str__(self) -> str:
        base = f"{self.status_code} " if self.status_code else ""
        return f"{base}{self.message}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r})"
        )


# ---- 4xx Client Errors --------------------------------------------------
class ClientError(APIError):
    """Base for 4xx client errors."""
    pass


class BadRequestError(ClientError):
    """400 Bad Request."""
    pass


class AuthenticationError(ClientError):
    """401 Unauthorized – missing or invalid credentials."""
    pass


class AuthorizationError(ClientError):
    """403 Forbidden – valid credentials but insufficient permissions."""
    pass


class NotFoundError(ClientError):
    """404 Not Found."""
    pass


class MethodNotAllowedError(ClientError):
    """405 Method Not Allowed."""
    pass


class ConflictError(ClientError):
    """409 Conflict."""
    pass


class UnprocessableEntityError(ClientError):
    """422 Unprocessable Entity – validation error."""
    pass


class RateLimitError(ClientError):
    """429 Too Many Requests."""

    def __init__(
        self,
        message: str,
        retry_after_seconds: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message, **kwargs)


# ---- 5xx Server Errors ---------------------------------------------------
class ServerError(APIError):
    """Base for 5xx server errors."""
    pass


class InternalServerError(ServerError):
    """500 Internal Server Error."""
    pass


class BadGatewayError(ServerError):
    """502 Bad Gateway."""
    pass


class ServiceUnavailableError(ServerError):
    """503 Service Unavailable."""
    pass


class GatewayTimeoutError(ServerError):
    """504 Gateway Timeout."""
    pass


# ---- Status-code mapping helper -----------------------------------------
_ERROR_CLASS_MAP: Dict[int, type] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    405: MethodNotAllowedError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    500: InternalServerError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError,
}


def raise_for_error(
    status_code: int,
    message: str = "",
    response_body: Any = None,
    headers: Optional[Dict[str, str]] = None,
    retry_after_seconds: Optional[float] = None,
) -> None:
    """
    Instantiate and raise the appropriate exception for an HTTP error.

    Args:
        status_code: HTTP status code.
        message: Human-readable error message.
        response_body: Parsed or raw response body.
        headers: Response headers (used for rate-limit handling).
        retry_after_seconds: Optional ``Retry-After`` value (seconds).
    """
    error_cls = _ERROR_CLASS_MAP.get(status_code)
    if error_cls is None:
        if 400 <= status_code < 500:
            error_cls = ClientError
        elif 500 <= status_code < 600:
            error_cls = ServerError
        else:
            error_cls = APIError

    if error_cls is RateLimitError:
        raise error_cls(
            message,
            status_code=status_code,
            response_body=response_body,
            headers=headers,
            retry_after_seconds=retry_after_seconds,
        )
    else:
        raise error_cls(
            message,
            status_code=status_code,
            response_body=response_body,
            headers=headers,
        )
