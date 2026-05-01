"""
Security endpoints – login history, emergency cancel, and anti‑phishing code.

All methods require authentication.
"""

from __future__ import annotations

from typing import Any, Dict


class Security:
    """Account security settings and logs."""

    def __init__(self, client) -> None:
        """
        Args:
            client: An authenticated ``nobitex.Client`` instance.
        """
        self._client = client

    # ------------------------------------------------------------------
    # Login history
    # ------------------------------------------------------------------
    def get_login_attempts(self) -> Dict[str, Any]:
        """
        Retrieve recent login attempts (successful & failed).

        Returns:
            ``{"status": "ok", "attempts": [{"ip": ..., "username": ..., "status": ..., "createdAt": ...}, ...]}``
        """
        return self._client.get("/users/login-attempts")

    # ------------------------------------------------------------------
    # Emergency cancel activation
    # ------------------------------------------------------------------
    def activate_emergency_cancel(self) -> Dict[str, Any]:
        """
        Enable emergency withdrawal cancellation.

        Once activated, a unique cancel code is generated. Subsequently, every
        withdrawal confirmation email/SMS will contain a link that allows
        instant cancellation (without logging in).

        .. attention:: If a withdrawal is cancelled via this method, the
           account will be blocked from placing new withdrawals for 72 hours.

        Returns:
            ``{"status": "ok", "cancelCode": {"code": "seJlef35L3"}}``
        """
        return self._client.get("/security/emergency-cancel/activate")

    # ------------------------------------------------------------------
    # Anti‑phishing code
    # ------------------------------------------------------------------
    def create_anti_phishing_code(self, code: str, otp_code: str) -> Dict[str, Any]:
        """
        Set or update the anti‑phishing code.

        The code (4‑15 characters) will be included in all automated emails
        from Nobitex, allowing you to verify their authenticity.

        Args:
            code: Anti‑phishing code (4‑15 printable characters).
            otp_code: One‑time password sent to your mobile (use
                ``/v2/otp/request`` with ``usage="anti_phishing_code"`` to obtain).

        Returns:
            ``{"status": "ok"}`` on success. Errors may include:
            - ``ParseError`` – missing fields
            - ``InvalidOTPCode`` – incorrect OTP
            - ``InvalidCodeLength`` – code length out of range
        """
        # The live API expects multipart/form-data; sending as URL‑encoded form
        # works in practice. If not, we can adjust to use files=... later.
        return self._client.post(
            "/security/anti-phishing",
            data={"code": code, "otpCode": otp_code},
        )

    def get_anti_phishing_code(self) -> Dict[str, Any]:
        """
        Retrieve the current anti‑phishing code (masked).

        Returns:
            ``{"status": "ok", "antiPhishingCode": "s*********g"}``
            If no code is set: ``{"status": "failed", "code": "NotFound", ...}``
        """
        return self._client.get("/security/anti-phishing")
