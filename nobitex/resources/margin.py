"""
Margin trading endpoints (require authentication).

Includes:
- List margin markets
- List liquidity pools
- Transfer funds between spot and margin wallets
- Get delegation limits per market
- Place margin orders (limit, market, stop-loss, OCO)
- List positions (open/past)
- Get single position status
- Close a position (with optional OCO)
- Edit position collateral
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union


class Margin:
    """Margin trading methods – markets, orders, positions, and collateral."""

    def __init__(self, client) -> None:
        """
        Args:
            client: An authenticated ``nobitex.Client`` instance.
        """
        self._client = client

    # ---------------------------------------------------------------
    # Margin markets
    # ---------------------------------------------------------------
    def get_markets(self) -> Dict[str, Any]:
        """
        List available margin markets and their settings.

        Returns:
            ``{"status": "ok", "markets": {"BTCIRT": {...}, ...}}``
        """
        return self._client.get("/margin/markets/list")

    # ---------------------------------------------------------------
    # Liquidity pools
    # ---------------------------------------------------------------
    def get_liquidity_pools(self) -> Dict[str, Any]:
        """
        List active liquidity pools and their capacity/filled amounts.

        Returns:
            ``{"status": "ok", "pools": {"btc": {"capacity": "30", "filledCapacity": "28.08"}, ...}}``
        """
        return self._client.get("/liquidity-pools/list")

    # ---------------------------------------------------------------
    # Wallet transfer (spot <-> margin)
    # ---------------------------------------------------------------
    def transfer(
        self,
        currency: str,
        amount: str,
        src: str,
        dst: str,
    ) -> Dict[str, Any]:
        """
        Transfer funds between spot and margin wallets.

        Args:
            currency: Currency code (``"rls"`` or ``"usdt"``).
            amount: Amount to transfer (as string for precision).
            src: Source wallet type (``"spot"`` or ``"margin"``).
            dst: Destination wallet type (``"spot"`` or ``"margin"``).
                Must be different from ``src``.

        Returns:
            ``{"status": "ok", "srcWallet": {...}, "dstWallet": {...}}``
            On failure: ``{"status": "failed", "code": "...", "message": "..."}``
        """
        payload = {
            "currency": currency,
            "amount": amount,
            "src": src,
            "dst": dst,
        }
        return self._client.post("/wallets/transfer", json=payload)

    # ---------------------------------------------------------------
    # Delegation limits
    # ---------------------------------------------------------------
    def get_delegation_limits(self, market: str) -> Dict[str, Any]:
        """
        Get remaining delegation limits for a margin market.

        Args:
            market: Market symbol (e.g. ``"BTCUSDT"``).

        Returns:
            ``{"status": "ok", "limits": {"buy": [...], "sell": [...]}}``
        """
        return self._client.get(
            "/margin/v2/delegation-limit",
            params={"market": market},
        )

    # ---------------------------------------------------------------
    # Place margin order
    # ---------------------------------------------------------------
    def add_order(
        self,
        src_currency: str,
        dst_currency: str,
        amount: str,
        price: str,
        type_: str = "sell",
        leverage: str = "1",
        execution: str = "limit",
        stop_price: Optional[str] = None,
        stop_limit_price: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a margin order (open or close, regular or OCO).

        Args:
            src_currency: Source currency (e.g. ``"btc"``).
            dst_currency: Destination currency (e.g. ``"rls"``, ``"usdt"``).
            amount: Order amount in source currency.
            price: Limit price per unit. Required for limit orders; for market
                orders it's a safety bound (recommended).
            type_: ``"sell"`` (default) or ``"buy"``.
            leverage: Leverage multiplier (e.g. ``"2"``). Must be a multiple of
                0.5 within the market's allowed range.
            execution: ``"limit"`` (default), ``"market"``, ``"stop_limit"``,
                or ``"stop_market"``.
            stop_price: Stop price (required for stop‑loss/OCO).
            stop_limit_price: Stop limit price (required for OCO/stop_limit).
            mode: ``"oco"`` to create an OCO order pair.

        Returns:
            For a regular order: ``{"status": "ok", "order": {...}}``
            For an OCO: ``{"status": "ok", "orders": [...]}``
            On failure: ``{"status": "failed", "code": "...", "message": "..."}``
        """
        payload: Dict[str, Any] = {
            "srcCurrency": src_currency,
            "dstCurrency": dst_currency,
            "amount": amount,
            "price": price,
            "type": type_,
            "leverage": leverage,
        }
        if execution != "limit":
            payload["execution"] = execution
        if stop_price is not None:
            payload["stopPrice"] = stop_price
        if stop_limit_price is not None:
            payload["stopLimitPrice"] = stop_limit_price
        if mode is not None:
            payload["mode"] = mode

        return self._client.post("/margin/orders/add", json=payload)

    # ---------------------------------------------------------------
    # Positions
    # ---------------------------------------------------------------
    def get_positions(
        self,
        src_currency: Optional[str] = None,
        dst_currency: Optional[str] = None,
        status: str = "active",
    ) -> Dict[str, Any]:
        """
        List margin positions (open or past).

        Args:
            src_currency: Filter by source currency (e.g. ``"btc"``).
            dst_currency: Filter by destination currency (e.g. ``"rls"``).
            status: ``"active"`` (default) for open positions,
                ``"past"`` for closed/liquidated/expired positions.

        Returns:
            ``{"status": "ok", "positions": [...], "hasNext": bool}``
        """
        params: Dict[str, Any] = {"status": status}
        if src_currency is not None:
            params["srcCurrency"] = src_currency
        if dst_currency is not None:
            params["dstCurrency"] = dst_currency
        return self._client.get("/positions/list", params=params)

    def get_position(self, position_id: int) -> Dict[str, Any]:
        """
        Get detailed status of a single position.

        Args:
            position_id: Position ID.

        Returns:
            ``{"status": "ok", "position": {...}}``
        """
        return self._client.get(f"/positions/{position_id}/status")

    # ---------------------------------------------------------------
    # Close position
    # ---------------------------------------------------------------
    def close_position(
        self,
        position_id: int,
        amount: str,
        price: str,
        execution: str = "limit",
        stop_price: Optional[str] = None,
        stop_limit_price: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Close (or partially close) an open position.

        Args:
            position_id: Position ID.
            amount: Amount to close (in source currency). Must not exceed
                remaining liability.
            price: Limit price per unit.
            execution: ``"limit"`` (default), ``"market"``, ``"stop_limit"``,
                or ``"stop_market"``.
            stop_price: Stop price (required for stop‑loss/OCO).
            stop_limit_price: Stop limit price (required for OCO/stop_limit).
            mode: ``"oco"`` to create an OCO close pair.

        Returns:
            ``{"status": "ok", "order": {...}}`` (or ``"orders": [...]`` for OCO)
        """
        payload: Dict[str, Any] = {
            "amount": amount,
            "price": price,
        }
        if execution != "limit":
            payload["execution"] = execution
        if stop_price is not None:
            payload["stopPrice"] = stop_price
        if stop_limit_price is not None:
            payload["stopLimitPrice"] = stop_limit_price
        if mode is not None:
            payload["mode"] = mode

        return self._client.post(
            f"/positions/{position_id}/close",
            json=payload,
        )

    # ---------------------------------------------------------------
    # Edit collateral
    # ---------------------------------------------------------------
    def edit_collateral(
        self,
        position_id: int,
        collateral: str,
    ) -> Dict[str, Any]:
        """
        Increase or decrease the collateral of an open position.

        Args:
            position_id: Position ID.
            collateral: New collateral amount (as string for precision).
                Must respect the minimum margin ratio and available balance.

        Returns:
            ``{"status": "ok", "position": {...}}`` (updated position)
        """
        return self._client.post(
            f"/positions/{position_id}/edit-collateral",
            json={"collateral": collateral},
        )
