"""
Spot trading endpoints (require authentication).

Includes:
- Place new orders (limit, market, stop-loss, OCO)
- Query order status
- List user orders with filtering & pagination
- Cancel / update order status
- Batch cancel old orders
- List user trades
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union


class Spot:
    """Spot trading methods – place, monitor, cancel orders, and fetch trades."""

    def __init__(self, client) -> None:
        """
        Args:
            client: An authenticated ``nobitex.Client`` instance.
        """
        self._client = client

    # ---------------------------------------------------------------
    # Place a new order
    # ---------------------------------------------------------------
    def add_order(
        self,
        type_: str,
        src_currency: str,
        dst_currency: str,
        amount: str,
        price: Optional[str] = None,
        execution: str = "limit",
        stop_price: Optional[str] = None,
        stop_limit_price: Optional[str] = None,
        mode: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a new order on the spot market.

        Args:
            type_: Order side – ``"buy"`` or ``"sell"``.
            src_currency: Source currency code (e.g. ``"btc"``).
            dst_currency: Destination currency code (e.g. ``"rls"``, ``"usdt"``).
            amount: Order amount in source currency (e.g. ``"0.6"``).
            price: Limit price per unit. Required for limit orders; for market
                orders it's a safety ceiling/floor (recommended).
            execution: Order execution type:
                - ``"limit"`` (default)
                - ``"market"``
                - ``"stop_market"`` (for stop‑loss)
                - ``"stop_limit"`` (for stop‑limit)
            stop_price: Stop price (required for stop‑loss/OCO).
            stop_limit_price: Stop limit price (required for OCO or stop_limit).
            mode: ``"oco"`` to create an OCO order pair.
            client_order_id: User‑defined client unique ID (max 32 chars,
                unique among open/active/inactive orders).

        Returns:
            JSON response. For a regular order: ``{"status": "ok", "order": {...}}``.
            For an OCO order: ``{"status": "ok", "orders": [...]}``.
            On failure: ``{"status": "failed", "code": "...", "message": "..."}``.
        """
        payload: Dict[str, Any] = {
            "type": type_,
            "srcCurrency": src_currency,
            "dstCurrency": dst_currency,
            "amount": amount,
        }
        if price is not None:
            payload["price"] = price
        if execution != "limit":
            payload["execution"] = execution
        if stop_price is not None:
            payload["stopPrice"] = stop_price
        if stop_limit_price is not None:
            payload["stopLimitPrice"] = stop_limit_price
        if mode is not None:
            payload["mode"] = mode
        if client_order_id is not None:
            payload["clientOrderId"] = client_order_id

        return self._client.post("/market/orders/add", json=payload)

    # ---------------------------------------------------------------
    # Query order status
    # ---------------------------------------------------------------
    def get_order_status(
        self,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the current status of an order.

        You must supply at least one of ``order_id`` or ``client_order_id``.
        If both are given, ``order_id`` takes precedence.

        Args:
            order_id: Nobitex order ID.
            client_order_id: User‑defined client order ID (experimental).

        Returns:
            ``{"status": "ok", "order": {...}}`` on success.
        """
        payload: Dict[str, Any] = {}
        if order_id is not None:
            payload["id"] = order_id
        if client_order_id is not None:
            payload["clientOrderId"] = client_order_id
        return self._client.post("/market/orders/status", json=payload)

    # ---------------------------------------------------------------
    # List user orders
    # ---------------------------------------------------------------
    def get_orders_list(
        self,
        status: Optional[str] = None,
        type_: Optional[str] = None,
        execution: Optional[str] = None,
        trade_type: Optional[str] = None,
        src_currency: Optional[str] = None,
        dst_currency: Optional[str] = None,
        details: int = 1,
        from_id: Optional[int] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a list of your orders with extensive filtering and pagination.

        Args:
            status: Filter by order status:
                ``"all"``, ``"open"``, ``"done"``, ``"close"``.
                Default – ``"open"``.
            type_: Filter by side: ``"buy"`` or ``"sell"``.
            execution: Filter by execution type:
                ``"limit"``, ``"market"``, ``"stop_limit"``, ``"stop_market"``.
            trade_type: Filter by order type: ``"spot"`` or ``"margin"``.
            src_currency: Source currency code (e.g. ``"btc"``).
            dst_currency: Destination currency code (e.g. ``"rls"``).
            details: Detail level (1 or 2). 2 returns extra fields like
                ``averagePrice``, ``fee``, etc.
            from_id: Return orders with ID greater than this value (cursor).
            order: Sorting criteria (e.g. ``"id"``, ``"-id"``, ``"created_at"``,
                ``"price"``). Default depends on other params.
            page: Page number (alternative to ``from_id``; mutually exclusive).
            page_size: Number of orders per page (max 1000). Default 100.

        Returns:
            ``{"status": "ok", "orders": [...]}``
        """
        params: Dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if type_ is not None:
            params["type"] = type_
        if execution is not None:
            params["execution"] = execution
        if trade_type is not None:
            params["tradeType"] = trade_type
        if src_currency is not None:
            params["srcCurrency"] = src_currency
        if dst_currency is not None:
            params["dstCurrency"] = dst_currency
        if details != 1:
            params["details"] = details
        if from_id is not None:
            params["fromId"] = from_id
        if order is not None:
            params["order"] = order
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size

        return self._client.get("/market/orders/list", params=params or None)

    # ---------------------------------------------------------------
    # Update order status (cancel / activate)
    # ---------------------------------------------------------------
    def update_order_status(
        self,
        status: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Change an order's status (cancel or activate a stop order).

        Args:
            status: New status – typically ``"canceled"``. You can also
                change from ``"new"`` to ``"active"``.
            order_id: Nobitex order ID.
            client_order_id: User‑defined client order ID.

        Returns:
            ``{"status": "ok", "updatedStatus": "Canceled", "order": {...}}``
        """
        payload: Dict[str, Union[str, int]] = {"status": status}
        if order_id is not None:
            payload["order"] = order_id
        if client_order_id is not None:
            payload["clientOrderId"] = client_order_id
        return self._client.post("/market/orders/update-status", json=payload)

    # ---------------------------------------------------------------
    # Batch cancel old orders
    # ---------------------------------------------------------------
    def cancel_old_orders(
        self,
        hours: Optional[float] = None,
        execution: Optional[str] = None,
        trade_type: Optional[str] = None,
        src_currency: Optional[str] = None,
        dst_currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel all (or filtered) active orders older than a given time.

        Args:
            hours: Cancel orders older than this many hours. If ``None``,
                **all** active matching orders are cancelled.
            execution: Filter by execution type (e.g. ``"limit"``).
            trade_type: Filter by ``"spot"`` or ``"margin"``.
            src_currency: Source currency code.
            dst_currency: Destination currency code.

        Returns:
            ``{"status": "ok"}`` on success, or
            ``{"status": "failed", "code": "...", "message": "..."}``.
        """
        payload: Dict[str, Any] = {}
        if hours is not None:
            payload["hours"] = hours
        if execution is not None:
            payload["execution"] = execution
        if trade_type is not None:
            payload["tradeType"] = trade_type
        if src_currency is not None:
            payload["srcCurrency"] = src_currency
        if dst_currency is not None:
            payload["dstCurrency"] = dst_currency

        return self._client.post("/market/orders/cancel-old", json=payload)

    # ---------------------------------------------------------------
    # List user trades
    # ---------------------------------------------------------------
    def get_trades_list(
        self,
        src_currency: Optional[str] = None,
        dst_currency: Optional[str] = None,
        from_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve your recent trades (last 3 days).

        Args:
            src_currency: Source currency code.
            dst_currency: Destination currency code.
                Both must be provided or both omitted.
            from_id: Minimum trade ID (cursor for pagination).

        Returns:
            ``{"status": "ok", "trades": [...], "hasNext": false}``
        """
        params: Dict[str, Any] = {}
        if src_currency is not None:
            params["srcCurrency"] = src_currency
        if dst_currency is not None:
            params["dstCurrency"] = dst_currency
        if from_id is not None:
            params["fromId"] = from_id

        return self._client.get("/market/trades/list", params=params or None)
