"""
Nobitex API wrapper – public interface.
"""

from .client import Client
from .exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ClientError,
    ConflictError,
    GatewayTimeoutError,
    InternalServerError,
    MethodNotAllowedError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
    UnprocessableEntityError,
    ValidationError,
)
