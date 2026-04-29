"""
Synchronous HTTP client for the Nobitex API v2.

Supports:
- Token authentication (obtained from panel or via /auth/login/)
- API‑Key authentication (Ed25519 signature) – requires the ``cryptography`` package
- Configurable User‑Agent header
- Centralised error handling via ``exceptions.raise_for_error``
"""

from __future__ import annotations

import json as json_lib
import time
from base64 import b64encode
from typing import Any, Dict, Optional, Union

import requests
from requests import Response, Session

# -------- Optional Ed25519 support ----------------------------------------
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    _ED25519_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ED25519_AVAILABLE = False

# -------- Local imports ----------------------------------------------------
from .exceptions import raise_for_error


class Client:
    """
    Nobitex API v2 client.

    Args:
        token: Authentication token (from panel or /auth/login/).
        api_key: Public key for API‑Key authentication.
        private_key: Private key (Ed25519) matching the ``api_key``.
            Expected as a hex string or base64 string, or a
            ``cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey``
            object.
        base_url: Base URL of the API (default: ``https://apiv2.nobitex.ir``).
        user_agent: User‑Agent header (must follow ``TraderBot/...`` pattern).
        timeout: Request timeout in seconds (default 30).
    """

    def __init__(
        self,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        private_key: Optional[Union[str, "Ed25519PrivateKey"]] = None,
        base_url: str = "https://apiv2.nobitex.ir",
        user_agent: str = "TraderBot/MyNobitexWrapper/1.0",
        timeout: int = 30,
    ) -> None:
        if not token and not (api_key and private_key):
            raise ValueError(
                "Either a token or both api_key and private_key must be provided."
            )

        self._token = token
        self._api_key = api_key
        self._private_key = self._prepare_private_key(private_key)
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent
        self._timeout = timeout
        self._session = Session()

        # Headers that are always the same
        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": self._user_agent,
            }
        )

    # ------------------------------------------------------------------
    # Private key handling
    # ------------------------------------------------------------------
    @staticmethod
    def _prepare_private_key(
        key: Optional[Union[str, "Ed25519PrivateKey"]],
    ) -> Optional["Ed25519PrivateKey"]:
        """Convert a string private key into an Ed25519PrivateKey object."""
        if key is None:
            return None
        if not _ED25519_AVAILABLE:
            raise ImportError(
                "To use API‑Key authentication, install the 'cryptography' package: "
                "pip install cryptography"
            )
        if isinstance(key, Ed25519PrivateKey):
            return key
        # Assume it's a hex or base64 string
        try:
            private_bytes = bytes.fromhex(key)
            return Ed25519PrivateKey.from_private_bytes(private_bytes)
        except (ValueError, TypeError):
            # Try base64
            import base64

            private_bytes = base64.b64decode(key)
            return Ed25519PrivateKey.from_private_bytes(private_bytes)

    # ------------------------------------------------------------------
    # Authentication header builders
    # ------------------------------------------------------------------
    def _auth_headers(
        self,
        method: str,
        path: str,
        body: Optional[Union[str, bytes]] = None,
    ) -> Dict[str, str]:
        """Generate the authentication headers for a request."""
        headers: Dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Token {self._token}"
            return headers

        # API‑Key authentication
        if self._api_key and self._private_key:
            timestamp = str(int(time.time()))
            # Ensure path starts with / and body is a string
            full_path = path if path.startswith("/") else f"/{path}"
            body_str = body if isinstance(body, str) else (body.decode() if body else "")
            message = f"{timestamp}{method}{full_path}{body_str}"
            signature = b64encode(self._private_key.sign(message.encode())).decode()

            headers.update(
                {
                    "Nobitex-Key": self._api_key,
                    "Nobitex-Signature": signature,
                    "Nobitex-Timestamp": timestamp,
                }
            )
            return headers
        raise RuntimeError("No valid authentication method configured.")

    # ------------------------------------------------------------------
    # Core request method
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Send an HTTP request and return the parsed JSON body.

        Raises:
            APIError: on non‑2xx responses.
        """

        url = f"{self._base_url}{path}"

        # Build headers: auth + any extra
        extra_headers = dict(headers) if headers else {}
        # If a JSON body is given, serialise it early for signing
        body_raw = None
        if json is not None:
            body_raw = json_lib.dumps(json, separators=(",", ":"))
            extra_headers["Content-Type"] = "application/json"

        auth_headers = self._auth_headers(
            method=method,
            path=path,
            body=body_raw,
        )
        all_headers = {**self._session.headers, **auth_headers, **extra_headers}

        # Prepare request arguments
        kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "params": params,
            "headers": all_headers,
            "timeout": self._timeout,
        }

        # For requests with a JSON body, pass the pre‑serialised string if the
        # auth method needs it, but `requests` can also serialise from a dict.
        if json is not None:
            # Use data=body_raw and Content-Type already set to avoid double‑serialisation
            kwargs["data"] = body_raw

        try:
            response = self._session.request(**kwargs)
        except requests.RequestException as e:
            # Wrap low‑level network errors (optional, you can just re‑raise)
            raise ConnectionError(f"Request failed: {e}") from e

        # Parse response
        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        # Check HTTP status and raise appropriate exception
        if not response.ok:
            raise_for_error(
                status_code=response.status_code,
                message=response_data.get("message", "") if isinstance(response_data, dict) else str(response_data),
                response_body=response_data,
                headers=dict(response.headers),
                retry_after_seconds=self._parse_retry_after(response.headers),
            )

        return response_data

    @staticmethod
    def _parse_retry_after(headers: Dict[str, str]) -> Optional[float]:
        """Extract Retry-After header value in seconds, if present."""
        retry = headers.get("Retry-After")
        if retry is None:
            return None
        try:
            return float(retry)
        except ValueError:
            # Could be a date; for simplicity ignore
            return None

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
    ) -> Any:
        return self._request("POST", path, json=json, data=data)

    def put(self, path: str, json: Optional[Any] = None) -> Any:
        return self._request("PUT", path, json=json)

    def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("DELETE", path, params=params)

    def patch(self, path: str, json: Optional[Any] = None) -> Any:
        return self._request("PATCH", path, json=json)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------
    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
