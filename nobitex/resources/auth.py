"""
Authentication endpoints – login (automatic token retrieval) and logout.

These endpoints are standalone; they do not require an authenticated
``Client`` instance. Use them to obtain or revoke API tokens.
"""

from __future__ import annotations

import requests
from typing import Any, Dict, Optional


class Auth:
    """Automatic token management (login / logout)."""

    @staticmethod
    def login(
        username: str,
        password: str,
        remember: str = "no",
        totp_code: Optional[str] = None,
        user_agent: str = "TraderBot/MyNobitexWrapper/1.0",
    ) -> Dict[str, Any]:
        """
        Obtain an API token by logging in with credentials.

        .. note:: This endpoint requires an Iranian IP and a valid TOTP
           (if 2FA is enabled). It is recommended to use tokens obtained
           from the Nobitex panel for most use‑cases.

        Args:
            username: Email address used for login.
            password: Account password.
            remember: ``"yes"`` to get a 30‑day token, ``"no"`` (default) for 4‑hour.
            totp_code: Two‑factor authentication code (if 2FA enabled).
                This value is sent in the ``X-TOTP`` header.
            user_agent: Value of the ``User-Agent`` header. Must follow the
                pattern ``TraderBot/XXXXX``.

        Returns:
            ``{"status": "success", "key": "...", "device": "..."}``
            on success. May raise ``APIError`` subclasses on failure.
        """
        url = "https://apiv2.nobitex.ir/auth/login/"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        }
        if totp_code:
            headers["X-TOTP"] = totp_code

        payload = {
            "username": username,
            "password": password,
            "remember": remember,
            "captcha": "api",
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        # We use the same exception system (imported later to avoid circularity)
        from nobitex.exceptions import raise_for_error
        if not resp.ok:
            raise_for_error(
                status_code=resp.status_code,
                message=resp.json().get("message", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                response_body=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                headers=dict(resp.headers),
            )
        return resp.json()

    @staticmethod
    def logout(token: str) -> Dict[str, Any]:
        """
        Invalidate a token (logout).

        Args:
            token: The API token to be revoked.

        Returns:
            ``{"detail": "خروج با موفقیت انجام شد.", "message": "خروج با موفقیت انجام شد."}``
        """
        url = "https://apiv2.nobitex.ir/auth/logout/"
        headers = {"Authorization": f"Token {token}"}
        resp = requests.post(url, headers=headers, timeout=30)
        from nobitex.exceptions import raise_for_error
        if not resp.ok:
            raise_for_error(
                status_code=resp.status_code,
                message=resp.json().get("message", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                response_body=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                headers=dict(resp.headers),
            )
        return resp.json()
