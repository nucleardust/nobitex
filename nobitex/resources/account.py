"""
Account & wallet endpoints (all require authentication).

Includes:
- Profile
- Wallets (list, balance, v2 selective list)
- Blockchain address generation
- Bank cards & accounts management
- User limitations
- Wallet transactions, deposits, history
- Favorite markets
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union


class Account:
    """User profile, wallets, cards, accounts, transactions, and favorites."""

    def __init__(self, client) -> None:
        """
        Args:
            client: An authenticated ``nobitex.Client`` instance.
        """
        self._client = client

    # ---------------------------------------------------------------
    # Profile
    # ---------------------------------------------------------------
    def get_profile(self) -> Dict[str, Any]:
        """
        Fetch user profile, trade statistics, and verification status.

        Returns:
            ``{"status": "ok", "profile": {...}, "tradeStats": {...}, "websocketAuthParam": "..."}``
        """
        return self._client.get("/users/profile")

    # ---------------------------------------------------------------
    # Wallets
    # ---------------------------------------------------------------
    def get_wallets_list(self, wallet_type: str = "spot") -> Dict[str, Any]:
        """
        List all user wallets (spot or margin).

        Args:
            wallet_type: ``"spot"`` (default) or ``"margin"``.

        Returns:
            ``{"status": "ok", "wallets": [...]}``
        """
        params = {"type": wallet_type} if wallet_type != "spot" else None
        return self._client.get("/users/wallets/list", params=params)

    def get_wallets_v2(
        self,
        currencies: Optional[str] = None,
        wallet_type: str = "spot",
    ) -> Dict[str, Any]:
        """
        Selective wallet list (v2). Returns balances for specified currencies.

        Args:
            currencies: Comma‑separated currency codes (e.g. ``"rls,btc"``).
                If omitted, all wallets are returned.
            wallet_type: ``"spot"`` (default) or ``"margin"``.

        Returns:
            ``{"status": "ok", "wallets": {"RLS": {...}, "BTC": {...}}}``
        """
        params: Dict[str, str] = {}
        if currencies:
            params["currencies"] = currencies
        if wallet_type != "spot":
            params["type"] = wallet_type
        return self._client.get("/v2/wallets", params=params or None)

    def get_balance(self, currency: str) -> Dict[str, Any]:
        """
        Get the balance of a single currency wallet.

        Args:
            currency: Currency code (e.g. ``"ltc"``, ``"rls"``).

        Returns:
            ``{"status": "ok", "balance": "10.2649975000"}``
        """
        return self._client.post("/users/wallets/balance", json={"currency": currency})

    # ---------------------------------------------------------------
    # Blockchain address generation
    # ---------------------------------------------------------------
    def generate_address(
        self,
        currency: str,
        network: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a new blockchain deposit address.

        Args:
            currency: Currency code (e.g. ``"btc"``).
            network: Optional network (e.g. ``"BSC"``).

        Returns:
            ``{"status": "ok", "address": "LRf3vuTMy4UwD5b72G84hmkfGBQYJeTwUs"}``
        """
        payload: Dict[str, str] = {"currency": currency}
        if network:
            payload["network"] = network
        return self._client.post("/users/wallets/generate-address", json=payload)

    # ---------------------------------------------------------------
    # Bank cards & accounts
    # ---------------------------------------------------------------
    def add_card(self, number: str, bank: str) -> Dict[str, Any]:
        """
        Register a new bank card.

        Args:
            number: 16‑digit card number (optional dash separated).
            bank: Bank name (e.g. ``"رسالت"``).

        Returns:
            ``{"status": "ok"}``
        """
        return self._client.post(
            "/users/cards-add",
            json={"number": number, "bank": bank},
        )

    def add_bank_account(self, number: str, shaba: str, bank: str) -> Dict[str, Any]:
        """
        Register a new bank account.

        Args:
            number: Account number.
            shaba: IBAN (IR...).
            bank: Bank name.

        Returns:
            ``{"status": "ok"}``
        """
        return self._client.post(
            "/users/accounts-add",
            json={"number": number, "shaba": shaba, "bank": bank},
        )

    # ---------------------------------------------------------------
    # Limitations
    # ---------------------------------------------------------------
    def get_limitations(self) -> Dict[str, Any]:
        """
        Retrieve user level and withdrawal/trade limits.

        Returns:
            ``{"status": "ok", "limitations": {...}}``
        """
        return self._client.get("/users/limitations")

    # ---------------------------------------------------------------
    # Transactions & deposits
    # ---------------------------------------------------------------
    def get_wallet_transactions(self, wallet_id: int) -> Dict[str, Any]:
        """
        List recent transactions for a specific wallet.

        Args:
            wallet_id: Wallet ID (integer).

        Returns:
            ``{"status": "ok", "transactions": [...], "hasNext": bool}``
        """
        return self._client.get(
            "/users/wallets/transactions/list",
            params={"wallet": wallet_id},
        )

    def get_transactions_history(
        self,
        currency: Optional[str] = None,
        tp: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        from_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Advanced transaction history with optional filters.

        Args:
            currency: Currency code (e.g. ``"ltc"``, ``"rls"``).
            tp: Transaction type (``deposit``, ``withdraw``, ``buy``, ...).
            from_date: Start datetime (ISO format).
            to_date: End datetime (ISO format).
            from_id: Transaction ID to start from (pagination).

        Returns:
            ``{"status": "ok", "transactions": [...], "hasNext": bool}``
        """
        params: Dict[str, Union[str, int]] = {}
        if currency:
            params["currency"] = currency
        if tp:
            params["tp"] = tp
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if from_id is not None:
            params["from_id"] = from_id
        return self._client.get(
            "/users/transactions-history",
            params=params or None,
        )

    def get_deposits(self, wallet_id: Optional[int] = None) -> Dict[str, Any]:
        """
        List recent deposits (up to 3 months old).

        Args:
            wallet_id: Wallet ID. If ``None`` (default), all wallets are shown
                but without pagination or time filters.

        Returns:
            ``{"status": "ok", "deposits": [...], "hasNext": bool}``
        """
        params = None if wallet_id is None else {"wallet": wallet_id}
        return self._client.get("/users/wallets/deposits/list", params=params)

    # ---------------------------------------------------------------
    # Favorite markets
    # ---------------------------------------------------------------
    def get_favorite_markets(self) -> Dict[str, Any]:
        """Get the list of favorite market symbols."""
        return self._client.get("/users/markets/favorite")

    def set_favorite_markets(self, markets: str) -> Dict[str, Any]:
        """
        Replace the favorite markets list.

        Args:
            markets: Comma‑separated market symbols (e.g. ``"BTCIRT,DOGEUSDT"``).

        Returns:
            ``{"status": "ok", "favoriteMarkets": [...]}``
        """
        return self._client.post(
            "/users/markets/favorite",
            json={"market": markets},
        )

    def delete_favorite_markets(self, market: str = "All") -> Dict[str, Any]:
        """
        Remove a market from favorites.

        Args:
            market: Market symbol to remove, or ``"All"`` to clear all.

        Returns:
            ``{"status": "ok", "favoriteMarkets": [...]}``
        """
        return self._client.delete(
            f"/users/markets/favorite",
            json={"market": market},
        )
