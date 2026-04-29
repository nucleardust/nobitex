"""
Market data endpoints (public, no authentication required).

Covers:
- /v3/orderbook/{symbol}
- /v2/depth/{symbol}
- /v2/trades/{symbol}
- /market/stats
- /market/udf/history
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Market:
    """Public market data methods."""

    def __init__(self, client) -> None:
        """
        Args:
            client: An instance of ``nobitex.Client``.
        """
        self._client = client

    # ---------------------------------------------------------------
    # Orderbook
    # ---------------------------------------------------------------
    def get_orderbook(self, symbol: str = "all") -> Dict[str, Any]:
        """
        Fetch orderbook for a single market or all markets.

        Args:
            symbol: Market symbol (e.g. ``"BTCIRT"``). Use ``"all"`` for all
                markets at once.

        Returns:
            JSON response. For a single symbol:
                ``{"status": "ok", "lastUpdate": ..., "asks": [...], "bids": [...]}``
            For ``"all"``:
                ``{"status": "ok", "BTCIRT": {...}, "USDTIRT": {...}, ...}``
        """
        return self._client.get(f"/v3/orderbook/{symbol}")

    # ---------------------------------------------------------------
    # Depth (chart) – experimental
    # ---------------------------------------------------------------
    def get_depth(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch aggregated orderbook depth for charting.

        Args:
            symbol: Market symbol (e.g. ``"BTCIRT"``).

        Returns:
            JSON response with aggregated ``bids``, ``asks``, ``lastTradePrice``,
            ``lastUpdate``.
        """
        return self._client.get(f"/v2/depth/{symbol}")

    # ---------------------------------------------------------------
    # Recent trades
    # ---------------------------------------------------------------
    def get_trades(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch recent trades for a market.

        Args:
            symbol: Market symbol (e.g. ``"BCHIRT"``).

        Returns:
            ``{"status": "ok", "trades": [{"time": ..., "price": ..., "volume": ..., "type": ...}]}``
        """
        return self._client.get(f"/v2/trades/{symbol}")

    # ---------------------------------------------------------------
    # Market statistics
    # ---------------------------------------------------------------
    def get_stats(
        self,
        src_currency: Optional[str] = None,
        dst_currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch 24-hour statistics for one or all markets.

        Args:
            src_currency: Source currency filter (e.g. ``"btc"``). Optional.
            dst_currency: Destination currency filter (e.g. ``"rls"``). Optional.

        Returns:
            ``{"status": "ok", "stats": {"btc-rls": {...}, ...}}``

        Note:
            The legacy ``global`` key is returned for backward compatibility
            but is deprecated and may be removed in future.
        """
        params = {}
        if src_currency is not None:
            params["srcCurrency"] = src_currency
        if dst_currency is not None:
            params["dstCurrency"] = dst_currency
        return self._client.get("/market/stats", params=params)

    # ---------------------------------------------------------------
    # OHLC / candlestick history
    # ---------------------------------------------------------------
    def get_ohlc(
        self,
        symbol: str,
        resolution: str,
        to: int,
        from_: Optional[int] = None,
        countback: Optional[int] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Fetch candlestick (OHLC) data.

        Args:
            symbol: Market symbol (e.g. ``"BTCIRT"``).
            resolution: Candle interval. One of:
                ``"1"``, ``"5"``, ``"15"``, ``"30"`` (minutes),
                ``"60"``, ``"180"``, ``"240"``, ``"360"``, ``"720"`` (hours),
                ``"D"``, ``"2D"``, ``"3D"`` (days).
            to: End timestamp in Unix seconds.
            from_: Start timestamp in Unix seconds. Optional; if omitted
                ``countback`` must be provided.
            countback: Number of candles before ``to``. Takes precedence
                over ``from_``.
            page: Page number for paginating results (when >500 candles
                are requested). Default 1.

        Returns:
            ``{"s": "ok", "t": [...], "o": [...], "h": [...], "l": [...], "c": [...], "v": [...]}``
            On errors: ``{"s": "error", "errmsg": "..."}`` or ``{"s": "no_data"}``.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "resolution": resolution,
            "to": to,
        }
        if from_ is not None:
            params["from"] = from_
        if countback is not None:
            params["countback"] = countback
        if page != 1:
            params["page"] = page
        return self._client.get("/market/udf/history", params=params)
