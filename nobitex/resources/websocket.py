"""
WebSocket real‑time client using Centrifugo.

Requires ``centrifuge‑python`` (install with ``pip install centrifuge‑python``).

Public channels (no auth):
    public:orderbook-{SYMBOL}
    public:candle-{SYMBOL}-{RESOLUTION}
    public:trades-{SYMBOL}
    public:market-stats-{SYMBOL}
    public:market-stats-all

Private channels (need auth):
    private:orders#{websocketAuthParam}
    private:trades#{websocketAuthParam}
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional

import centrifuge
from centrifuge import Client as CentClient, Subscription

from nobitex.client import Client as RestClient

logger = logging.getLogger(__name__)

Callback = Callable[[Any], Coroutine[Any, Any, None]]


class WebSocketClient:
    """
    Nobitex real‑time WebSocket client powered by Centrifugo.

    Args:
        rest_client: Authenticated REST ``Client`` (needed to fetch the WS token).
        token: Optional connection token. If omitted, it will be fetched
            automatically from ``/auth/ws/token/``.
        base_ws_url: WebSocket endpoint (defaults to
            ``wss://ws.nobitex.ir/connection/websocket``).
        websocket_auth_param: User‑specific private channel suffix.
            Can be obtained from ``/users/profile`` → ``websocketAuthParam``.
            Required for private channel subscriptions.
    """

    def __init__(
        self,
        rest_client: RestClient,
        token: Optional[str] = None,
        base_ws_url: str = "wss://ws.nobitex.ir/connection/websocket",
        websocket_auth_param: Optional[str] = None,
    ) -> None:
        self._rest = rest_client
        self._token = token
        self._base_ws_url = base_ws_url
        self._websocket_auth_param = websocket_auth_param
        self._cent: Optional[CentClient] = None
        self._subscriptions: List[Subscription] = []
        self._connected = asyncio.Event()

    # ---------------------------------------------------------------
    # Token management
    # ---------------------------------------------------------------
    async def _get_token(self) -> str:
        """Fetch a fresh WS token from the REST API."""
        resp = self._rest.get("/auth/ws/token")
        return resp["token"]

    async def _token_callback(self, _event: Any) -> str:
        """Centrifuge callback for token refresh."""
        return await self._get_token()

    # ---------------------------------------------------------------
    # Connection
    # ---------------------------------------------------------------
    async def connect(self) -> None:
        """Connect to the WebSocket server."""
        token = self._token or await self._get_token()

        self._cent = CentClient(
            self._base_ws_url,
            token=token,
            get_token=self._token_callback,
        )

        self._cent.on("connected", self._on_connected)
        self._cent.on("disconnected", self._on_disconnected)
        self._cent.on("error", self._on_error)

        self._cent.connect()
        await self._connected.wait()

    async def disconnect(self) -> None:
        """Gracefully close the WebSocket connection."""
        if self._cent:
            self._cent.disconnect()
        self._connected.clear()

    async def _on_connected(self, _ctx: Any) -> None:
        logger.info("WebSocket connected")
        self._connected.set()

    async def _on_disconnected(self, ctx: dict) -> None:
        logger.warning("WebSocket disconnected: %s", ctx.get("reason", "unknown"))
        self._connected.clear()

    async def _on_error(self, ctx: dict) -> None:
        logger.error("WebSocket error: %s", ctx.get("error", "unknown"))

    # ---------------------------------------------------------------
    # Subscription helpers
    # ---------------------------------------------------------------
    async def subscribe(
        self,
        channel: str,
        callback: Callback,
        delta: str = "fossil",
    ) -> None:
        """
        Subscribe to a channel and process messages asynchronously.

        Args:
            channel: Full channel name (e.g. ``"public:orderbook-BTCIRT"``).
            callback: Async coroutine called with the parsed message data.
            delta: Centrifuge delta mode. Use ``"fossil"`` for compressed
                orderbook updates (default). Pass ``None`` for full data.
        """
        if not self._cent:
            raise RuntimeError("Client not connected. Call connect() first.")

        opts = {}
        if delta:
            opts["delta"] = delta

        sub = self._cent.new_subscription(channel, **opts)

        async def _handler(ctx: dict) -> None:
            data = json.loads(ctx["data"]["data"]) if "data" in ctx else ctx
            await callback(data)

        sub.on("publication", _handler)
        sub.subscribe()
        self._subscriptions.append(sub)
        logger.info("Subscribed to %s", channel)

    async def unsubscribe(self, channel: str) -> None:
        """Remove a subscription."""
        for sub in self._subscriptions:
            if sub.channel == channel:
                sub.unsubscribe()
                self._subscriptions.remove(sub)
                logger.info("Unsubscribed from %s", channel)
                return
        logger.warning("Channel %s not found", channel)

    # ---------------------------------------------------------------
    # Pre‑defined channel shortcuts
    # ---------------------------------------------------------------
    async def subscribe_orderbook(
        self, symbol: str, callback: Callback
    ) -> None:
        """Subscribe to public orderbook updates for a market."""
        channel = f"public:orderbook-{symbol.upper()}"
        await self.subscribe(channel, callback)

    async def subscribe_candle(
        self, symbol: str, resolution: str, callback: Callback
    ) -> None:
        """
        Subscribe to candlestick (OHLC) updates.

        Args:
            symbol: Market symbol (e.g. ``"BTCIRT"``).
            resolution: Candle interval (``"1"``, ``"5"``, ..., ``"D"``, ``"2D"``, ``"3D"``).
        """
        channel = f"public:candle-{symbol.upper()}-{resolution}"
        await self.subscribe(channel, callback)

    async def subscribe_trades(
        self, symbol: str, callback: Callback
    ) -> None:
        """Subscribe to public trade feed for a market."""
        channel = f"public:trades-{symbol.upper()}"
        await self.subscribe(channel, callback)

    async def subscribe_market_stats(
        self, symbol: Optional[str] = None, callback: Callback = None
    ) -> None:
        """
        Subscribe to 24h market stats.

        Args:
            symbol: Market symbol (e.g. ``"BTCIRT"``). If ``None``,
                subscribes to the aggregate channel ``public:market-stats-all``.
        """
        channel = (
            "public:market-stats-all"
            if symbol is None
            else f"public:market-stats-{symbol.upper()}"
        )
        await self.subscribe(channel, callback)

    # Private channels require websocketAuthParam
    async def subscribe_private_orders(self, callback: Callback) -> None:
        """Subscribe to private order updates (requires auth)."""
        if not self._websocket_auth_param:
            raise ValueError("websocket_auth_param is required for private channels")
        channel = f"private:orders#{self._websocket_auth_param}"
        await self.subscribe(channel, callback)

    async def subscribe_private_trades(self, callback: Callback) -> None:
        """Subscribe to private trade updates (requires auth)."""
        if not self._websocket_auth_param:
            raise ValueError("websocket_auth_param is required for private channels")
        channel = f"private:trades#{self._websocket_auth_param}"
        await self.subscribe(channel, callback)
