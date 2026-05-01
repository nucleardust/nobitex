"""Tests for the WebSocket client (requires ``centrifuge-python``).

If the library is not installed, all tests are skipped.
"""

import json
import pytest

try:
    import centrifuge
except ImportError:
    pytest.skip("centrifuge-python not installed – skipping WebSocket tests", allow_module_level=True)

from unittest.mock import AsyncMock, MagicMock, patch

from nobitex.resources import websocket as ws_module
from nobitex.resources.websocket import WebSocketClient


# -----------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------
@pytest.fixture
def rest_client_mock():
    """A mocked REST client that returns a pre‑set token."""
    client = MagicMock()
    client.get.return_value = {"token": "fake-ws-token"}
    return client


@pytest.fixture
def cent_client_mock():
    """Mock centrifuge.Client and its subscription mechanism."""
    with patch.object(ws_module.centrifuge, "Client") as MockCentClient:
        mock_cent = MagicMock()
        MockCentClient.return_value = mock_cent

        # Simulate event registration
        event_handlers = {}
        mock_cent.on.side_effect = lambda event, handler: event_handlers.setdefault(event, []).append(handler)

        # Subscribe mock
        mock_sub = MagicMock()
        mock_sub.channel = None
        mock_cent.new_subscription.return_value = mock_sub

        yield mock_cent, mock_sub, event_handlers


# -----------------------------------------------------------------
# Tests
# -----------------------------------------------------------------
class TestConnect:
    @pytest.mark.asyncio
    async def test_connect_without_token_fetches_token(self, rest_client_mock, cent_client_mock):
        mock_cent, mock_sub, event_handlers = cent_client_mock
        ws = WebSocketClient(rest_client_mock)  # token=None

        assert ws._token is None
        await ws.connect()

        # Token was fetched
        rest_client_mock.get.assert_called_once_with("/auth/ws/token")
        # Centrifuge client created with fetched token
        ws_module.centrifuge.Client.assert_called_with(
            ws._base_ws_url,
            token="fake-ws-token",
            get_token=ws._token_callback,
        )
        # Centrifuge connect called
        mock_cent.connect.assert_called_once()
        # Connected event should be set (we simulate by calling handler)
        assert not ws._connected.is_set()
        # Simulate connected event
        for handler in event_handlers.get("connected", []):
            handler({})
        assert ws._connected.is_set()

    @pytest.mark.asyncio
    async def test_connect_with_token_does_not_fetch(self, rest_client_mock, cent_client_mock):
        mock_cent, mock_sub, event_handlers = cent_client_mock
        ws = WebSocketClient(rest_client_mock, token="provided-token")

        await ws.connect()
        rest_client_mock.get.assert_not_called()
        ws_module.centrifuge.Client.assert_called_with(
            ws._base_ws_url,
            token="provided-token",
            get_token=ws._token_callback,
        )

    @pytest.mark.asyncio
    async def test_disconnect(self, rest_client_mock, cent_client_mock):
        mock_cent, mock_sub, event_handlers = cent_client_mock
        ws = WebSocketClient(rest_client_mock, token="t")
        await ws.connect()
        # Simulate connected
        for handler in event_handlers.get("connected", []):
            handler({})
        assert ws._connected.is_set()

        await ws.disconnect()
        mock_cent.disconnect.assert_called_once()
        assert not ws._connected.is_set()


class TestSubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_basic(self, rest_client_mock, cent_client_mock):
        mock_cent, mock_sub, event_handlers = cent_client_mock
        ws = WebSocketClient(rest_client_mock, token="t")
        await ws.connect()
        for handler in event_handlers.get("connected", []):
            handler({})

        callback = AsyncMock()
        await ws.subscribe("public:orderbook-BTCIRT", callback)

        # new_subscription called with correct channel and delta
        mock_cent.new_subscription.assert_called_with("public:orderbook-BTCIRT", delta="fossil")
        mock_sub.subscribe.assert_called_once()

        # When a publication arrives, callback should be called with parsed data
        # Simulate a publication event
        pub_data = {
            "data": {
                "data": json.dumps({"asks": [["100", "0.1"]], "bids": [["99", "0.2"]]})
            }
        }
        # Find the registered publication handler
        # Our code: sub.on('publication', _handler). So we need to get that handler from the mock_sub.on calls
        # mock_sub.on was called with ('publication', <function>)
        pub_handlers = [args[1] for args in mock_sub.on.call_args_list if args[0] == "publication"]
        assert len(pub_handlers) == 1
        await pub_handlers[0](pub_data)

        callback.assert_called_once_with({"asks": [["100", "0.1"]], "bids": [["99", "0.2"]]})

    @pytest.mark.asyncio
    async def test_subscribe_without_delta(self, rest_client_mock, cent_client_mock):
        mock_cent, mock_sub, event_handlers = cent_client_mock
        ws = WebSocketClient(rest_client_mock, token="t")
        await ws.connect()
        for handler in event_handlers.get("connected", []):
            handler({})

        await ws.subscribe("public:channel", AsyncMock(), delta=None)
        mock_cent.new_subscription.assert_called_with("public:channel")  # no delta kwarg

    @pytest.mark.asyncio
    async def test_subscribe_not_connected_raises(self, rest_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t")
        with pytest.raises(RuntimeError, match="not connected"):
            await ws.subscribe("ch", AsyncMock())

    @pytest.mark.asyncio
    async def test_unsubscribe(self, rest_client_mock, cent_client_mock):
        mock_cent, mock_sub, event_handlers = cent_client_mock
        ws = WebSocketClient(rest_client_mock, token="t")
        await ws.connect()
        for handler in event_handlers.get("connected", []):
            handler({})

        await ws.subscribe("public:channel", AsyncMock())
        # Change channel name to match
        mock_sub.channel = "public:channel"
        await ws.unsubscribe("public:channel")
        mock_sub.unsubscribe.assert_called_once()
        # Second unsubscribe does nothing
        await ws.unsubscribe("public:channel")  # should log warning but not crash


class TestShortcutMethods:
    @pytest.mark.asyncio
    async def test_subscribe_orderbook(self, rest_client_mock, cent_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t")
        # Mock subscribe to avoid actual subscription
        with patch.object(ws, "subscribe", AsyncMock()) as mock_sub:
            callback = AsyncMock()
            await ws.subscribe_orderbook("btcirt", callback)
            mock_sub.assert_called_once_with("public:orderbook-BTCIRT", callback)

    @pytest.mark.asyncio
    async def test_subscribe_candle(self, rest_client_mock, cent_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t")
        with patch.object(ws, "subscribe", AsyncMock()) as mock_sub:
            callback = AsyncMock()
            await ws.subscribe_candle("btcusdt", "15", callback)
            mock_sub.assert_called_once_with("public:candle-BTCUSDT-15", callback)

    @pytest.mark.asyncio
    async def test_subscribe_trades(self, rest_client_mock, cent_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t")
        with patch.object(ws, "subscribe", AsyncMock()) as mock_sub:
            callback = AsyncMock()
            await ws.subscribe_trades("ethirt", callback)
            mock_sub.assert_called_once_with("public:trades-ETHIRT", callback)

    @pytest.mark.asyncio
    async def test_subscribe_market_stats_specific(self, rest_client_mock, cent_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t")
        with patch.object(ws, "subscribe", AsyncMock()) as mock_sub:
            callback = AsyncMock()
            await ws.subscribe_market_stats("btcirt", callback)
            mock_sub.assert_called_once_with("public:market-stats-BTCIRT", callback)

    @pytest.mark.asyncio
    async def test_subscribe_market_stats_all(self, rest_client_mock, cent_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t")
        with patch.object(ws, "subscribe", AsyncMock()) as mock_sub:
            callback = AsyncMock()
            await ws.subscribe_market_stats(None, callback)
            mock_sub.assert_called_once_with("public:market-stats-all", callback)

    @pytest.mark.asyncio
    async def test_subscribe_private_orders_requires_auth_param(self, rest_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t")
        with pytest.raises(ValueError, match="websocket_auth_param"):
            await ws.subscribe_private_orders(AsyncMock())

    @pytest.mark.asyncio
    async def test_subscribe_private_orders_with_auth_param(self, rest_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t", websocket_auth_param="abc123")
        with patch.object(ws, "subscribe", AsyncMock()) as mock_sub:
            callback = AsyncMock()
            await ws.subscribe_private_orders(callback)
            mock_sub.assert_called_once_with("private:orders#abc123", callback)

    @pytest.mark.asyncio
    async def test_subscribe_private_trades_requires_auth_param(self, rest_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t")
        with pytest.raises(ValueError, match="websocket_auth_param"):
            await ws.subscribe_private_trades(AsyncMock())

    @pytest.mark.asyncio
    async def test_subscribe_private_trades_with_auth_param(self, rest_client_mock):
        ws = WebSocketClient(rest_client_mock, token="t", websocket_auth_param="xyz")
        with patch.object(ws, "subscribe", AsyncMock()) as mock_sub:
            callback = AsyncMock()
            await ws.subscribe_private_trades(callback)
            mock_sub.assert_called_once_with("private:trades#xyz", callback)
