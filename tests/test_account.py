"""Tests for the Account resource (authenticated endpoints)."""

import pytest
import responses

from nobitex.resources.account import Account


# ---------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------
def test_get_profile(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "profile": {"email": "user@example.com"},
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/profile",
        json=expected,
    )
    result = Account(client_token).get_profile()
    assert result == expected


# ---------------------------------------------------------------
# get_wallets_list
# ---------------------------------------------------------------
def test_get_wallets_list_default_spot(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "wallets": [{"id": 1, "currency": "rls"}]}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/wallets/list",    # no query param for "spot"
        json=expected,
    )
    result = Account(client_token).get_wallets_list()
    assert result == expected


def test_get_wallets_list_margin(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "wallets": [{"id": 999, "currency": "btc"}]}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/wallets/list?type=margin",
        json=expected,
    )
    result = Account(client_token).get_wallets_list(wallet_type="margin")
    assert result == expected


# ---------------------------------------------------------------
# get_wallets_v2
# ---------------------------------------------------------------
def test_get_wallets_v2_no_params(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "wallets": {}}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/v2/wallets",
        json=expected,
    )
    result = Account(client_token).get_wallets_v2()
    assert result == expected


def test_get_wallets_v2_with_currencies(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "wallets": {"BTC": {"balance": "1.0"}}}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/v2/wallets?currencies=rls,btc",
        json=expected,
    )
    result = Account(client_token).get_wallets_v2(currencies="rls,btc")
    assert result == expected


def test_get_wallets_v2_margin(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "wallets": {}}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/v2/wallets?type=margin",
        json=expected,
    )
    result = Account(client_token).get_wallets_v2(wallet_type="margin")
    assert result == expected


def test_get_wallets_v2_both_params(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "wallets": {"BTC": {"balance": "0.5"}}}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/v2/wallets?currencies=btc&type=margin",
        json=expected,
    )
    result = Account(client_token).get_wallets_v2(currencies="btc", wallet_type="margin")
    assert result == expected


# ---------------------------------------------------------------
# get_balance
# ---------------------------------------------------------------
def test_get_balance(mocked_responses, client_token, base_url):
    currency = "ltc"
    expected = {"status": "ok", "balance": "10.2649975"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/balance",
        json=expected,
    )
    result = Account(client_token).get_balance(currency)
    assert result == expected
    # Check that the correct JSON body was sent
    request_body = mocked_responses.calls[0].request.body
    assert f'"currency":"{currency}"' in (request_body or "")


# ---------------------------------------------------------------
# generate_address
# ---------------------------------------------------------------
def test_generate_address_without_network(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "address": "LRf3vuTMy4UwD5b72G84hmkfGBQYJeTwUs"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/generate-address",
        json=expected,
    )
    result = Account(client_token).generate_address(currency="btc")
    assert result == expected
    body = mocked_responses.calls[0].request.body
    assert '"currency":"btc"' in (body or "")
    assert "network" not in (body or "")   # network not sent


def test_generate_address_with_network(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/generate-address",
        json=expected,
    )
    result = Account(client_token).generate_address(currency="btc", network="BSC")
    assert result == expected
    body = mocked_responses.calls[0].request.body
    assert '"currency":"btc"' in (body or "")
    assert '"network":"BSC"' in (body or "")


# ---------------------------------------------------------------
# add_card
# ---------------------------------------------------------------
def test_add_card(mocked_responses, client_token, base_url):
    expected = {"status": "ok"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/cards-add",
        json=expected,
    )
    result = Account(client_token).add_card(number="5041721011111111", bank="رسالت")
    assert result == expected
    body = mocked_responses.calls[0].request.body
    assert '"number":"5041721011111111"' in (body or "")
    assert '"bank":"رسالت"' in (body or "")


# ---------------------------------------------------------------
# add_bank_account
# ---------------------------------------------------------------
def test_add_bank_account(mocked_responses, client_token, base_url):
    expected = {"status": "ok"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/accounts-add",
        json=expected,
    )
    result = Account(client_token).add_bank_account(
        number="0346666666666",
        shaba="IR460170000000346666666666",
        bank="ملی",
    )
    assert result == expected
    body = mocked_responses.calls[0].request.body
    assert '"number":"0346666666666"' in (body or "")
    assert '"shaba":"IR460170000000346666666666"' in (body or "")


# ---------------------------------------------------------------
# get_limitations
# ---------------------------------------------------------------
def test_get_limitations(mocked_responses, client_token, base_url):
    expected = {
        "status": "ok",
        "limitations": {"userLevel": "level2", "features": {}, "limits": {}},
    }
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/limitations",
        json=expected,
    )
    result = Account(client_token).get_limitations()
    assert result == expected


# ---------------------------------------------------------------
# get_wallet_transactions
# ---------------------------------------------------------------
def test_get_wallet_transactions(mocked_responses, client_token, base_url):
    wallet_id = 4159
    expected = {"status": "ok", "transactions": [], "hasNext": False}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/wallets/transactions/list?wallet={wallet_id}",
        json=expected,
    )
    result = Account(client_token).get_wallet_transactions(wallet_id)
    assert result == expected


# ---------------------------------------------------------------
# get_transactions_history
# ---------------------------------------------------------------
def test_get_transactions_history_no_filters(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "transactions": [], "hasNext": False}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/transactions-history",
        json=expected,
    )
    result = Account(client_token).get_transactions_history()
    assert result == expected


def test_get_transactions_history_all_filters(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "transactions": [{"id": 10}], "hasNext": False}
    params = {
        "currency": "ltc",
        "tp": "withdraw",
        "from": "2018-10-01T00:00:00+00:00",
        "to": "2018-10-20T00:00:00+00:00",
        "from_id": 96124,
    }
    query = (
        "currency=ltc&tp=withdraw"
        "&from=2018-10-01T00%3A00%3A00%2B00%3A00"
        "&to=2018-10-20T00%3A00%3A00%2B00%3A00"
        "&from_id=96124"
    )
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/transactions-history?{query}",
        json=expected,
    )
    result = Account(client_token).get_transactions_history(**params)
    assert result == expected


# ---------------------------------------------------------------
# get_deposits
# ---------------------------------------------------------------
def test_get_deposits_all(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "deposits": [], "hasNext": False}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/wallets/deposits/list",
        json=expected,
    )
    result = Account(client_token).get_deposits()   # default wallet_id=None
    assert result == expected


def test_get_deposits_specific_wallet(mocked_responses, client_token, base_url):
    wallet_id = 4159
    expected = {"status": "ok", "deposits": [{"amount": "3.0"}]}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/wallets/deposits/list?wallet={wallet_id}",
        json=expected,
    )
    result = Account(client_token).get_deposits(wallet_id)
    assert result == expected


# ---------------------------------------------------------------
# Favorite markets
# ---------------------------------------------------------------
def test_get_favorite_markets(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "favoriteMarkets": ["BTCIRT"]}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/markets/favorite",
        json=expected,
    )
    result = Account(client_token).get_favorite_markets()
    assert result == expected


def test_set_favorite_markets(mocked_responses, client_token, base_url):
    markets = "BTCIRT,DOGEUSDT"
    expected = {"status": "ok", "favoriteMarkets": ["BTCIRT", "DOGEUSDT"]}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/markets/favorite",
        json=expected,
    )
    result = Account(client_token).set_favorite_markets(markets)
    assert result == expected
    body = mocked_responses.calls[0].request.body
    assert f'"market":"{markets}"' in (body or "")


def test_delete_favorite_markets_single(mocked_responses, client_token, base_url):
    market = "DOGEUSDT"
    expected = {"status": "ok", "favoriteMarkets": ["BTCIRT"]}
    mocked_responses.add(
        responses.DELETE,
        f"{base_url}/users/markets/favorite",
        json=expected,
    )
    result = Account(client_token).delete_favorite_markets(market)
    assert result == expected
    body = mocked_responses.calls[0].request.body
    assert f'"market":"{market}"' in (body or "")


def test_delete_favorite_markets_all(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "favoriteMarkets": []}
    mocked_responses.add(
        responses.DELETE,
        f"{base_url}/users/markets/favorite",
        json=expected,
    )
    result = Account(client_token).delete_favorite_markets("All")
    assert result == expected
    body = mocked_responses.calls[0].request.body
    assert '"market":"All"' in (body or "")
