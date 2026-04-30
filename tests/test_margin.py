"""Tests for the Margin trading resource."""

import json
import pytest
import responses

from nobitex.resources.margin import Margin


# ---------------------------------------------------------------
# get_markets
# ---------------------------------------------------------------
def test_get_markets(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "markets": {
            "BTCIRT": {
                "srcCurrency": "btc",
                "dstCurrency": "rls",
                "positionFeeRate": "0.001",
                "maxLeverage": "5",
                "sellEnabled": True,
                "buyEnabled": False,
            },
        },
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/margin/markets/list",
        json=expected,
    )
    result = Margin(client_token).get_markets()
    assert result == expected


# ---------------------------------------------------------------
# get_liquidity_pools
# ---------------------------------------------------------------
def test_get_liquidity_pools(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "pools": {
            "btc": {"capacity": "30", "filledCapacity": "28.082343"},
            "ltc": {"capacity": "160", "filledCapacity": "149.234"},
        },
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/liquidity-pools/list",
        json=expected,
    )
    result = Margin(client_token).get_liquidity_pools()
    assert result == expected


# ---------------------------------------------------------------
# transfer
# ---------------------------------------------------------------
def test_transfer(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "srcWallet": {"id": 1, "currency": "rls", "balance": "1000"},
        "dstWallet": {"id": 2, "currency": "rls", "balance": "2000"},
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/wallets/transfer",
        json=expected,
    )
    result = Margin(client_token).transfer(
        currency="rls",
        amount="2500000000",
        src="spot",
        dst="margin",
    )
    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["currency"] == "rls"
    assert body["amount"] == "2500000000"
    assert body["src"] == "spot"
    assert body["dst"] == "margin"


# ---------------------------------------------------------------
# get_delegation_limits
# ---------------------------------------------------------------
def test_get_delegation_limits(mocked_responses, client_token, base_url):
    market = "BTCUSDT"
    expected = {
        "status": "ok",
        "limits": {
            "buy": [{"leverage": "1", "limit": "1250"}],
            "sell": [{"leverage": "1", "limit": "0.021"}],
        },
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/margin/v2/delegation-limit?market={market}",
        json=expected,
    )
    result = Margin(client_token).get_delegation_limits(market=market)
    assert result == expected


# ---------------------------------------------------------------
# add_order
# ---------------------------------------------------------------
def test_add_margin_order_limit(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "order": {
            "id": 25,
            "type": "sell",
            "execution": "Limit",
            "tradeType": "Margin",
            "srcCurrency": "btc",
            "dstCurrency": "rls",
            "price": "6400000000",
            "amount": "0.01",
            "status": "Active",
        },
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/margin/orders/add",
        json=expected,
    )
    result = Margin(client_token).add_order(
        src_currency="btc",
        dst_currency="rls",
        amount="0.01",
        price="6400000000",
        type_="sell",
        leverage="2",
    )
    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["srcCurrency"] == "btc"
    assert body["dstCurrency"] == "rls"
    assert body["amount"] == "0.01"
    assert body["price"] == "6400000000"
    assert body["type"] == "sell"
    assert body["leverage"] == "2"
    # default execution "limit" not sent
    assert "execution" not in body


def test_add_margin_order_market(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "order": {"id": 26, "execution": "Market"}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/margin/orders/add",
        json=expected,
    )
    result = Margin(client_token).add_order(
        src_currency="btc",
        dst_currency="usdt",
        amount="0.01",
        price="21300",
        type_="sell",
        execution="market",
    )
    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["execution"] == "market"


def test_add_margin_order_stop_market(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "order": {"id": 27, "execution": "StopMarket"}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/margin/orders/add",
        json=expected,
    )
    result = Margin(client_token).add_order(
        src_currency="doge",
        dst_currency="rls",
        amount="64",
        price="47500",
        type_="sell",
        execution="stop_market",
        stop_price="46500",
    )
    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["stopPrice"] == "46500"


def test_add_margin_order_oco(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "orders": [
            {"id": 27, "execution": "Limit"},
            {"id": 28, "execution": "StopLimit"},
        ],
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/margin/orders/add",
        json=expected,
    )
    result = Margin(client_token).add_order(
        src_currency="btc",
        dst_currency="usdt",
        amount="0.01",
        price="42390",
        type_="buy",
        leverage="1.5",
        mode="oco",
        stop_price="42700",
        stop_limit_price="42715",
    )
    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["mode"] == "oco"
    assert body["stopPrice"] == "42700"
    assert body["stopLimitPrice"] == "42715"


# ---------------------------------------------------------------
# get_positions
# ---------------------------------------------------------------
def test_get_positions_default_active(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "positions": [],
        "hasNext": False,
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/positions/list?status=active",
        json=expected,
    )
    result = Margin(client_token).get_positions()
    assert result == expected


def test_get_positions_with_filters(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "positions": [{"id": 128, "srcCurrency": "btc"}],
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/positions/list?status=active&srcCurrency=btc&dstCurrency=rls",
        json=expected,
    )
    result = Margin(client_token).get_positions(
        src_currency="btc", dst_currency="rls"
    )
    assert result == expected


def test_get_positions_past(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "positions": [{"id": 32, "status": "Closed"}],
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/positions/list?status=past",
        json=expected,
    )
    result = Margin(client_token).get_positions(status="past")
    assert result == expected


# ---------------------------------------------------------------
# get_position
# ---------------------------------------------------------------
def test_get_position(mocked_responses, client_token, base_url):
    position_id = 128
    expected = {
        "status": "ok",
        "position": {
            "id": position_id,
            "srcCurrency": "btc",
            "status": "Open",
        },
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/positions/{position_id}/status",
        json=expected,
    )
    result = Margin(client_token).get_position(position_id)
    assert result == expected


# ---------------------------------------------------------------
# close_position
# ---------------------------------------------------------------
def test_close_position_limit(mocked_responses, client_token, base_url):
    position_id = 128
    expected = {
        "status": "ok",
        "order": {
            "id": 28,
            "type": "buy",
            "execution": "Limit",
            "side": "close",
        },
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/positions/{position_id}/close",
        json=expected,
    )
    result = Margin(client_token).close_position(
        position_id=position_id,
        amount="0.0100150225",
        price="6200000000",
    )
    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["amount"] == "0.0100150225"
    assert body["price"] == "6200000000"
    assert "execution" not in body  # default


def test_close_position_oco(mocked_responses, client_token, base_url):
    position_id = 128
    expected = {
        "status": "ok",
        "orders": [
            {"id": 29, "execution": "Limit"},
            {"id": 30, "execution": "StopLimit"},
        ],
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/positions/{position_id}/close",
        json=expected,
    )
    result = Margin(client_token).close_position(
        position_id=position_id,
        amount="0.01",
        price="6200000000",
        mode="oco",
        stop_price="6300000000",
        stop_limit_price="6310000000",
    )
    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["mode"] == "oco"
    assert body["stopPrice"] == "6300000000"
    assert body["stopLimitPrice"] == "6310000000"


# ---------------------------------------------------------------
# edit_collateral
# ---------------------------------------------------------------
def test_edit_collateral(mocked_responses, client_token, base_url):
    position_id = 128
    expected = {
        "status": "ok",
        "position": {
            "id": position_id,
            "collateral": "230000000",
        },
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/positions/{position_id}/edit-collateral",
        json=expected,
    )
    result = Margin(client_token).edit_collateral(
        position_id=position_id,
        collateral="230000000",
    )
    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["collateral"] == "230000000"
