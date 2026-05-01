"""
Address book and withdrawal whitelist management.

Endpoints:
- GET /address_book – list saved addresses
- POST /address_book – add a new address
- DELETE /address_book/<id>/delete – remove an address
- POST /address_book/whitelist/activate – enable whitelist
- POST /address_book/whitelist/deactivate – disable whitelist
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class AddressBook:
    """Manage saved withdrawal addresses and whitelist mode."""

    def __init__(self, client) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------
    def list_addresses(self, network: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve saved addresses, optionally filtered by network.

        Args:
            network: Blockchain network (e.g. ``"BSC"``). If ``None``, all
                addresses are returned.

        Returns:
            ``{"status": "ok", "data": [{"id": ..., "title": ..., "network": ..., "address": ..., "tag": ..., "createdAt": ...}]}``
        """
        params = {"network": network} if network else None
        return self._client.get("/address_book", params=params)

    # ------------------------------------------------------------------
    # Add address
    # ------------------------------------------------------------------
    def add_address(
        self,
        title: str,
        network: str,
        address: str,
        otp_code: str,
        tfa_code: str,
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save a new withdrawal address.

        Args:
            title: Human‑readable label for the address.
            network: Blockchain network (e.g. ``"BSC"``, ``"BNB"``).
            address: Destination wallet address.
            otp_code: One‑time password sent to email/phone.
            tfa_code: Two‑factor authentication code (TOTP).
            tag: Destination tag/memo (mandatory for BNB, EOS, PMN, XLM, XRP).

        Returns:
            ``{"status": "ok", "data": {"id": ..., ...}}``
        """
        payload: Dict[str, str] = {
            "title": title,
            "network": network,
            "address": address,
            "otpCode": otp_code,
            "tfaCode": tfa_code,
        }
        if tag is not None:
            payload["tag"] = tag
        return self._client.post("/address_book", json=payload)

    # ------------------------------------------------------------------
    # Delete address
    # ------------------------------------------------------------------
    def delete_address(self, address_id: int) -> Dict[str, Any]:
        """
        Remove an address from the address book.

        Args:
            address_id: ID of the address entry to delete.

        Returns:
            ``{"status": "ok"}``
        """
        return self._client.delete(f"/address_book/{address_id}/delete")

    # ------------------------------------------------------------------
    # Whitelist (safe withdrawal) control
    # ------------------------------------------------------------------
    def activate_whitelist(self) -> Dict[str, Any]:
        """
        Enable withdrawal whitelist mode.

        When active, withdrawals are restricted to addresses saved in the
        address book (except Lightning network).

        Returns:
            ``{"status": "ok"}``
        """
        return self._client.post("/address_book/whitelist/activate")

    def deactivate_whitelist(
        self, otp_code: str, tfa_code: str
    ) -> Dict[str, Any]:
        """
        Disable withdrawal whitelist mode.

        .. warning:: After deactivation, withdrawals will be blocked for
            24 hours to protect the account.

        Args:
            otp_code: One‑time password sent to email/phone.
            tfa_code: Two‑factor authentication code (TOTP).

        Returns:
            ``{"status": "ok"}``
        """
        payload = {"otpCode": otp_code, "tfaCode": tfa_code}
        return self._client.post(
            "/address_book/whitelist/deactivate", json=payload
        )
