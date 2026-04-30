"""Tests for the Spot trading resource."""

import json
import pytest
import responses

from nobitex.resources.spot import Spot


# ---------------------------------------------------------------
# add_order
# ---------------------------------------------------------------
def test_add_order_limit(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "order": {
            "id": 25,
            "type": "buy",
            "execution": "Limit",
            "price": "520000000",
            "amount": "0.6",
            "status": "Active",
        },
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/add",
        json=expected,
    )

    result = Spot(client_token).add_order(
        type_="buy",
        src_currency="btc",
        dst_currency="rls",
        amount="0.6",
        price="520000000",
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["type"] == "buy"
    assert body["srcCurrency"] == "btc"
    assert body["dstCurrency"] == "rls"
    assert body["amount"] == "0.6"
    assert body["price"] == "520000000"
    assert "execution" not in body           # default 'limit' not sent


def test_add_order_market_with_price(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "order": {"id": 26}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/add",
        json=expected,
    )

    result = Spot(client_token).add_order(
        type_="sell",
        src_currency="doge",
        dst_currency="rls",
        amount="64",
        execution="market",
        price="47500",
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["execution"] == "market"
    assert body["price"] == "47500"
    assert body["type"] == "sell"


def test_add_order_stop_market(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "order": {
            "id": 26,
            "execution": "StopMarket",
            "status": "Inactive",
        },
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/add",
        json=expected,
    )

    result = Spot(client_token).add_order(
        type_="sell",
        src_currency="doge",
        dst_currency="rls",
        amount="64",
        execution="stop_market",
        stop_price="47500",
        client_order_id="order1",
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["execution"] == "stop_market"
    assert body["stopPrice"] == "47500"
    assert body["clientOrderId"] == "order1"
    assert "price" not in body


def test_add_order_oco(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "orders": [
            {"id": 27, "execution": "Limit"},
            {"id": 28, "execution": "StopLimit"},
        ],
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/add",
        json=expected,
    )

    result = Spot(client_token).add_order(
        type_="buy",
        src_currency="btc",
        dst_currency="usdt",
        amount="0.01",
        mode="oco",
        price="42390",
        stop_price="42700",
        stop_limit_price="42715",
        client_order_id="order1",
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["mode"] == "oco"
    assert body["price"] == "42390"
    assert body["stopPrice"] == "42700"
    assert body["stopLimitPrice"] == "42715"


# ---------------------------------------------------------------
# get_order_status
# ---------------------------------------------------------------
def test_get_order_status_by_id(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "order": {"id": 5684, "status": "Active"},
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/status",
        json=expected,
    )

    result = Spot(client_token).get_order_status(order_id=5684)

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["id"] == 5684
    assert "clientOrderId" not in body


def test_get_order_status_by_client_id(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "order": {"clientOrderId": "order1"}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/status",
        json=expected,
    )

    result = Spot(client_token).get_order_status(client_order_id="order1")

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["clientOrderId"] == "order1"
    assert "id" not in body


def test_get_order_status_both_id_precedence(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "order": {"id": 100}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/status",
        json=expected,
    )

    result = Spot(client_token).get_order_status(order_id=100, client_order_id="ignored")

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["id"] == 100
    assert body["clientOrderId"] == "ignored"


# ---------------------------------------------------------------
# get_orders_list
# ---------------------------------------------------------------
def test_get_orders_list_default(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "orders": []}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/orders/list",
        json=expected,
    )

    result = Spot(client_token).get_orders_list()

    assert result == expected
    # No query params in URL
    assert "?" not in mocked_responses.calls[0].request.url


def test_get_orders_list_with_filters(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "orders": []}
    params_str = "status=open&type=buy&execution=limit&srcCurrency=btc&dstCurrency=rls&details=2"
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/orders/list?{params_str}",
        json=expected,
    )

    result = Spot(client_token).get_orders_list(
        status="open",
        type_="buy",
        execution="limit",
        src_currency="btc",
        dst_currency="rls",
        details=2,
    )

    assert result == expected


def test_get_orders_list_pagination_from_id(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "orders": [{"id": 200}]}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/orders/list?fromId=100",
        json=expected,
    )

    result = Spot(client_token).get_orders_list(from_id=100)

    assert result == expected


def test_get_orders_list_page(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "orders": []}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/orders/list?page=3&pageSize=50",
        json=expected,
    )

    result = Spot(client_token).get_orders_list(page=3, page_size=50)

    assert result == expected


# ---------------------------------------------------------------
# update_order_status
# ---------------------------------------------------------------
def test_update_order_status_cancel_by_id(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "updatedStatus": "Canceled",
        "order": {"id": 5684},
    }
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/update-status",
        json=expected,
    )

    result = Spot(client_token).update_order_status(
        status="canceled", order_id=5684
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["order"] == 5684
    assert body["status"] == "canceled"


def test_update_order_status_cancel_by_client_id(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "updatedStatus": "Canceled"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/update-status",
        json=expected,
    )

    result = Spot(client_token).update_order_status(
        status="canceled", client_order_id="order1"
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["clientOrderId"] == "order1"
    assert body["status"] == "canceled"
    assert "order" not in body


# ---------------------------------------------------------------
# cancel_old_orders
# ---------------------------------------------------------------
def test_cancel_old_orders_with_hours(mocked_responses, client_token, base_url):
    expected = {"status": "ok"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/cancel-old",
        json=expected,
    )

    result = Spot(client_token).cancel_old_orders(
        hours=2.4,
        execution="limit",
        src_currency="btc",
        dst_currency="rls",
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["hours"] == 2.4
    assert body["execution"] == "limit"
    assert body["srcCurrency"] == "btc"
    assert body["dstCurrency"] == "rls"


def test_cancel_old_orders_all(mocked_responses, client_token, base_url):
    expected = {"status": "ok"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/market/orders/cancel-old",
        json=expected,
    )

    result = Spot(client_token).cancel_old_orders()

    assert result == expected
    body = mocked_responses.calls[0].request.body
    # body should be empty JSON object "{}"
    assert body is None or body == b"" or json.loads(body) == {}


# ---------------------------------------------------------------
# get_trades_list
# ---------------------------------------------------------------
def test_get_trades_list_no_filters(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "trades": [], "hasNext": False}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/trades/list",
        json=expected,
    )

    result = Spot(client_token).get_trades_list()

    assert result == expected


def test_get_trades_list_filtered(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "trades": [{"id": 1}]}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/trades/list?srcCurrency=usdt&dstCurrency=rls",
        json=expected,
    )

    result = Spot(client_token).get_trades_list(
        src_currency="usdt", dst_currency="rls"
    )

    assert result == expected


def test_get_trades_list_with_from_id(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "trades": [], "hasNext": False}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/market/trades/list?fromId=10023",
        json=expected,
    )

    result = Spot(client_token).get_trades_list(from_id=10023)

    assert result == expected
