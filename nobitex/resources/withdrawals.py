"""
Withdrawal endpoints – crypto and rial.

Includes:
- Create crypto withdrawal request
- Confirm crypto withdrawal (with OTP)
- View crypto withdrawal status
- Create rial withdrawal request
- Cancel rial withdrawal
- View rial withdrawal details
- List all withdrawals (crypto + rial)
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Withdrawals:
    """Crypto and rial withdrawal operations."""

    def __init__(self, client) -> None:
        """
        Args:
            client: An authenticated ``nobitex.Client`` instance.
        """
        self._client = client

    # ---------------------------------------------------------------
    # Crypto withdrawal
    # ---------------------------------------------------------------
    def crypto_withdraw(
        self,
        wallet: int,
        amount: Optional[str] = None,
        address: Optional[str] = None,
        network: Optional[str] = None,
        invoice: Optional[str] = None,
        explanations: Optional[str] = None,
        no_tag: bool = False,
        tag: Optional[str] = None,
        otp_header: Optional[str] = None,   # X-TOTP value
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Request a cryptocurrency withdrawal.

        Args:
            wallet: Wallet ID (int).
            amount: Amount to withdraw (string for precision). Required if
                ``invoice`` is not provided.
            address: Destination wallet address (string). Ignored if ``invoice``
                is used.
            network: Blockchain network (e.g. ``"BTCLN"``, ``"BSC"``). Optional.
            invoice: Lightning Network invoice (for BTCLN). If given, ``amount``
                and ``address`` are extracted from it.
            explanations: Optional description.
            no_tag: Set ``True`` to skip the destination tag for networks that
                require it (BNB, EOS, PMN, XLM, XRP).
            tag: Destination tag/memo for networks that require it.
            otp_header: TOTP code for the ``X-TOTP`` header. Required if the
                destination address is not in your address book.
            extra_headers: Any additional HTTP headers.

        Returns:
            ``{"status": "ok", "withdraw": {...}}``
        """
        payload: Dict[str, Any] = {"wallet": wallet}
        if amount is not None:
            payload["amount"] = amount
        if address is not None:
            payload["address"] = address
        if network is not None:
            payload["network"] = network
        if invoice is not None:
            payload["invoice"] = invoice
        if explanations is not None:
            payload["explanations"] = explanations
        if no_tag:
            payload["noTag"] = True
        if tag is not None:
            payload["tag"] = tag

        headers: Dict[str, str] = {}
        if otp_header is not None:
            headers["X-TOTP"] = otp_header
        if extra_headers:
            headers.update(extra_headers)

        return self._client.post(
            "/users/wallets/withdraw",
            json=payload,
            headers=headers or None,
        )

    def confirm_crypto_withdraw(
        self,
        withdraw_id: int,
        otp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Confirm a crypto withdrawal (submit OTP).

        Args:
            withdraw_id: Withdrawal request ID (from ``crypto_withdraw``).
            otp: One‑time password sent via SMS/email. Required unless the
                destination address is in your trusted address book.

        Returns:
            ``{"status": "ok", "withdraw": {...}}``
        """
        payload: Dict[str, Any] = {"withdraw": withdraw_id}
        if otp is not None:
            payload["otp"] = otp
        return self._client.post(
            "/users/wallets/withdraw-confirm",
            json=payload,
        )

    def get_crypto_withdraw(self, withdraw_id: int) -> Dict[str, Any]:
        """
        Get details of a crypto withdrawal.

        Args:
            withdraw_id: Withdrawal request ID.

        Returns:
            ``{"status": "ok", "withdraw": {...}}``
        """
        return self._client.get(f"/withdraws/{withdraw_id}")

    # ---------------------------------------------------------------
    # Rial withdrawal
    # ---------------------------------------------------------------
    def rial_withdraw(
        self,
        destination_bank_account_id: int,
        amount: str,
    ) -> Dict[str, Any]:
        """
        Request a rial withdrawal to a bank account.

        Args:
            destination_bank_account_id: ID of the verified bank account.
            amount: Amount in Rials (string for precision, e.g. ``"2500000000"``).

        Returns:
            ``{"status": "ok", "result": {...}}``
        """
        payload = {
            "destinationBankAccountId": destination_bank_account_id,
            "amount": amount,
        }
        return self._client.post("/cobank/withdraw", json=payload)

    def cancel_rial_withdraw(self, withdraw_id: str) -> Dict[str, Any]:
        """
        Cancel a rial withdrawal. Only possible within 3 minutes of creation
        and if status is still ``"New"``.

        Args:
            withdraw_id: Withdrawal request ID (string, e.g. ``"CW430542"``).

        Returns:
            ``{"status": "ok", "result": {...}}``
        """
        return self._client.post(f"/cobank/withdraw/{withdraw_id}/cancel")

    def get_rial_withdraw(self, withdraw_id: str) -> Dict[str, Any]:
        """
        Get details of a rial withdrawal.

        Args:
            withdraw_id: Withdrawal request ID (string).

        Returns:
            ``{"status": "ok", "result": {...}}``
        """
        return self._client.get(f"/cobank/withdraw/{withdraw_id}")

    # ---------------------------------------------------------------
    # List all withdrawals (crypto + rial)
    # ---------------------------------------------------------------
    def get_list(self) -> Dict[str, Any]:
        """
        Retrieve a list of all withdrawal requests (crypto and rial).

        Returns:
            ``{"status": "ok", "withdraws": [...], "hasNext": bool}``
        """
        return self._client.get("/users/wallets/withdraws/list")
