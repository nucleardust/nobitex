"""Tests for the Market resource (public endpoints)."""

import pytest
import responses

from nobitex.resources.market import Market


# ---------------------------------------------------------------
# get_orderbook
# ---------------------------------------------------------------
def test_get_orderbook_single(mocked_responses, client_token, base_url):
    symbol = "BTCIRT"
    expected = {
        "status": "ok",
        "lastUpdate": 1644991756704,
        "asks": [["1476091000", "1.016"]],
        "bids": [["1470001120", "0.126571"]],
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/v3/orderbook/{symbol}/",
        json=expected,
    )
    result = Market(client_token).get_orderbook(symbol)
    assert result == expected


def test_get_orderbook_all(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "BTCIRT": {},
        "USDTIRT": {},
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/v3/orderbook/all/",
        json=expected,
    )
    result = Market(client_token).get_orderbook("all")
    assert result == expected


# ---------------------------------------------------------------
# get_depth
# ---------------------------------------------------------------
def test_get_depth(mocked_responses, client_token, base_url):
    symbol = "BTCIRT"
    expected = {
        "status": "ok",
        "bids": [["7309999000", "2.200274"]],
        "asks": [["7409894000", "0.054789"]],
        "lastTradePrice": "7417000000",
        "lastUpdate": "1658565992195",
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/v2/depth/{symbol}/",
        json=expected,
    )
    result = Market(client_token).get_depth(symbol)
    assert result == expected


# ---------------------------------------------------------------
# get_trades
# ---------------------------------------------------------------
def test_get_trades(mocked_responses, client_token, base_url):
    symbol = "BCHIRT"
    expected = {
        "status": "ok",
        "trades": [
            {"time": 1588689375067, "price": "1470000110", "volume": "0", "type": "sell"},
            {"time": 1588689360464, "price": "1470000110", "volume": "0.002", "type": "buy"},
        ],
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/v2/trades/{symbol}/",
        json=expected,
    )
    result = Market(client_token).get_trades(symbol)
    assert result == expected


# ---------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------
def test_get_stats_no_filters(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "stats": {"btc-rls": {}}}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/stats/",
        json=expected,
    )
    result = Market(client_token).get_stats()
    assert result == expected
    # Ensure no query params were sent
    assert "srcCurrency" not in mocked_responses.calls[0].request.url
    assert "dstCurrency" not in mocked_responses.calls[0].request.url


def test_get_stats_with_filters(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "stats": {"btc-rls": {}}}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/stats/?srcCurrency=btc&dstCurrency=rls",
        json=expected,
    )
    result = Market(client_token).get_stats(src_currency="btc", dst_currency="rls")
    assert result == expected


# ---------------------------------------------------------------
# get_ohlc
# ---------------------------------------------------------------
def test_get_ohlc_basic(mocked_responses, client_token, base_url):
    expected = {
        "s": "ok",
        "t": [1562095800],
        "o": [146272500],
        "h": [155869600],
        "l": [140062400],
        "c": [151440200],
        "v": [18.22],
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/udf/history/?symbol=BTCIRT&resolution=D&to=1562230967",
        json=expected,
    )
    result = Market(client_token).get_ohlc(
        symbol="BTCIRT", resolution="D", to=1562230967
    )
    assert result == expected


def test_get_ohlc_with_countback(mocked_responses, client_token, base_url):
    expected = {"s": "ok", "t": [1562182200]}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/udf/history/?symbol=BTCIRT&resolution=60&to=1562230967&countback=4",
        json=expected,
    )
    result = Market(client_token).get_ohlc(
        symbol="BTCIRT",
        resolution="60",
        to=1562230967,
        countback=4,
    )
    assert result == expected


def test_get_ohlc_with_page(mocked_responses, client_token, base_url):
    expected = {"s": "ok", "t": [1562182200]}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/udf/history/?symbol=BTCIRT&resolution=D&to=1562230967&page=2",
        json=expected,
    )
    result = Market(client_token).get_ohlc(
        symbol="BTCIRT",
        resolution="D",
        to=1562230967,
        page=2,
    )
    assert result == expected
