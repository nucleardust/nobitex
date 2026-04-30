"""
Integration smoke test – requires a real token and live API access.

Set these environment variables before running:
    NOBITEX_TOKEN=your_token_here
    # or
    NOBITEX_API_KEY=your_public_key
    NOBITEX_PRIVATE_KEY=your_private_key_hex

Then run:
    pytest tests/test_integration.py -v
"""

import os
import pytest

from nobitex.client import Client
from nobitex.resources.market import Market
from nobitex.resources.account import Account
from nobitex.exceptions import APIError, AuthenticationError


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def get_client():
    """Create an authenticated client from environment variables."""
    token = os.getenv("NOBITEX_TOKEN")
    api_key = os.getenv("NOBITEX_API_KEY")
    private_key = os.getenv("NOBITEX_PRIVATE_KEY")

    if token:
        return Client(token=token)
    if api_key and private_key:
        return Client(api_key=api_key, private_key=private_key)
    raise ValueError(
        "Set NOBITEX_TOKEN or NOBITEX_API_KEY + NOBITEX_PRIVATE_KEY"
    )


# ---------------------------------------------------------------
# Tests
# ---------------------------------------------------------------
@pytest.mark.integration
def test_public_orderbook():
    """Smoke test: fetch public orderbook without authentication."""
    # Market data can be fetched without any auth
    client = Client(token="none")  # token ignored for public endpoints
    market = Market(client)
    data = market.get_orderbook("BTCIRT")
    assert data["status"] == "ok"
    assert "asks" in data
    assert "bids" in data


@pytest.mark.integration
def test_public_stats():
    """Smoke test: fetch market stats."""
    client = Client(token="none")
    market = Market(client)
    data = market.get_stats(src_currency="btc", dst_currency="rls")
    assert data["status"] == "ok"
    assert "stats" in data


@pytest.mark.integration
def test_authenticated_profile():
    """Smoke test: fetch user profile with real token."""
    try:
        client = get_client()
    except ValueError:
        pytest.skip("No credentials provided for authenticated test")

    account = Account(client)
    try:
        profile = account.get_profile()
        assert profile["status"] == "ok"
        assert "profile" in profile
        assert "email" in profile["profile"]
        print(f"Logged in as: {profile['profile']['email']}")
    except AuthenticationError:
        pytest.fail("Authentication failed – check your token/API keys")
    except APIError as e:
        pytest.fail(f"API error: {e}")


@pytest.mark.integration
def test_authenticated_wallets():
    """Smoke test: list wallets with real token."""
    try:
        client = get_client()
    except ValueError:
        pytest.skip("No credentials provided for authenticated test")

    account = Account(client)
    wallets = account.get_wallets_list()
    assert wallets["status"] == "ok"
    assert "wallets" in wallets
    print(f"Found {len(wallets['wallets'])} wallets")


@pytest.mark.integration
def test_authenticated_balance():
    """Smoke test: get single wallet balance."""
    try:
        client = get_client()
    except ValueError:
        pytest.skip("No credentials provided for authenticated test")

    account = Account(client)
    balance = account.get_balance("rls")
    assert balance["status"] == "ok"
    assert "balance" in balance
    print(f"RLS balance: {balance['balance']}")


# Optional: uncomment to test placing a very tiny limit order on a sandbox market
# @pytest.mark.integration
# def test_place_tiny_order():
#     """Place a minimum order on BTCIRT (careful: real trade!)."""
#     try:
#         client = get_client()
#     except ValueError:
#         pytest.skip("No credentials")
#
#     spot = Spot(client)
#     resp = spot.add_order(
#         type_="buy",
#         src_currency="btc",
#         dst_currency="rls",
#         amount="0.0001",
#         price=1000000,   # extremely low, unlikely to fill
#     )
#     if resp["status"] == "failed":
#         print(f"Order failed: {resp['message']}")
#     else:
#         print(f"Order placed: {resp['order']['id']}")
