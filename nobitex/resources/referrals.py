"""
Referral program endpoints – referral codes, status, and setting referrer.

All methods require authentication.
"""

from __future__ import annotations

from typing import Any, Dict


class Referrals:
    """Manage referral codes and track referral status."""

    def __init__(self, client) -> None:
        """
        Args:
            client: An authenticated ``nobitex.Client`` instance.
        """
        self._client = client

    def get_links(self) -> Dict[str, Any]:
        """
        List all your referral codes with performance statistics.

        Returns:
            ``{"status": "ok", "links": [{"id": ..., "referralCode": ..., ...}, ...]}``
        """
        return self._client.get("/users/referral/links-list")

    def create_link(self, friend_share: int = 0) -> Dict[str, Any]:
        """
        Generate a new referral code.

        Args:
            friend_share: Percentage of trading fees shared with the invited
                user (default 0). Must be a valid value per platform rules.

        Returns:
            ``{"status": "ok", ...}`` on success. May return errors:

            - ``InvalidGivebackShare`` – `friend_share` out of allowed range
            - ``TooManyReferralLinks`` – maximum 30 codes per account reached
            - ``ReferralCodeUnavailable`` – temporarily unavailable
        """
        return self._client.post(
            "/users/referral/links-add",
            json={"friendShare": friend_share},
        )

    def get_referral_status(self) -> Dict[str, Any]:
        """
        Check whether the current user was invited by another user.

        Returns:
            ``{"status": "ok", "hasReferrer": true/false}``
        """
        return self._client.post("/users/referral/referral-status")

    def set_referrer(self, referrer_code: str) -> Dict[str, Any]:
        """
        Set the referrer for this account (within 24 hours of sign‑up).

        Args:
            referrer_code: Referral code of the inviting user.

        Returns:
            ``{"status": "ok"}`` on success. May fail if:

            - ``ReferrerChangeUnavailable`` – more than 24 hours since sign‑up
        """
        return self._client.post(
            "/users/referral/set-referrer",
            json={"referrerCode": referrer_code},
        )
