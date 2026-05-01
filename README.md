# nobitex

Python client for the [Nobitex](https://nobitex.ir/) API v2.

![Demo](assets/demo.gif)

- **Authentication** – token or Ed25519 API‑Key (automatic signature)
- **Public data** – orderbook, trades, OHLC, market stats
- **Account** – profile, wallets, balances, transactions
- **Spot trading** – limit, market, stop‑loss, OCO orders
- **Margin trading** – positions, leverage, collateral management
- **Withdrawals** – crypto (multiple networks, Lightning) and Rial (bank transfer, cancel)
- **Address book & whitelist** – safe withdrawal management
- **Security** – login history, emergency cancel, anti‑phishing
- **Referrals** – create codes, track performance, set referrer
- **Profits** – daily / monthly portfolio reports
- **WebSocket** – real‑time orderbook, trades, candles, user orders (async, Centrifugo)
- **System options** – coin settings, precision, limits

## Installation

```bash
pip install git+https://github.com/nucleardust/nobitex.git
#coming soon:
#pip install nobitex-peach
```

*For local development:*

```bash
git clone https://github.com/nucleardust/nobitex.git
cd nobitex
pip install -e .
```

### Optional dependencies

- **WebSocket** `pip install nobitex-peach[websocket]`
- `pip install "nobitex-peach[websocket] @ git+https://github.com/nucleardust/nobitex.git"`
- **Dev tools** `pip install nobitex-peach[dev]`
- `pip install "nobitex-peach[dev] @ git+https://github.com/nucleardust/nobitex.git"`

## Quick start

```python
from nobitex import Client
from nobitex.resources.market import Market

# token authentication (from panel → settings)
client = Client(token="your-token")

market = Market(client)
orderbook = market.get_orderbook("BTCIRT")
print(orderbook["asks"][0])
```

**API‑Key authentication** (Ed25519 – recommended for bots):

```python
client = Client(
    api_key="your-public-key",
    private_key="your-private-key",   # hex or base64 string
)
```

## Usage by resource

### Market (public data)

```python
from nobitex import Client
from nobitex.resources.market import Market

client = Client(token="dummy")   # token ignored for public endpoints
market = Market(client)

# orderbook
orderbook = market.get_orderbook("BTCIRT")
all_orderbooks = market.get_orderbook("all")

# trades
trades = market.get_trades("BTCIRT")

# 24h stats
stats = market.get_stats(src_currency="btc", dst_currency="rls")

# OHLC candles
candles = market.get_ohlc(
    symbol="BTCIRT", resolution="D", to=1609459200, from_=1609372800
)
```

### Account & wallets

```python
from nobitex.resources.account import Account

account = Account(client)

# profile
profile = account.get_profile()

# wallet list
wallets = account.get_wallets_list()
balance = account.get_balance("btc")

# transactions
txs = account.get_wallet_transactions(wallet_id=123)
history = account.get_transactions_history(currency="ltc")

# deposits
deposits = account.get_deposits(wallet_id=123)
```

### Spot trading

```python
from nobitex.resources.spot import Spot

spot = Spot(client)

# place a limit buy order
order = spot.add_order(
    type_="buy",
    src_currency="btc",
    dst_currency="rls",
    amount="0.01",
    price=500000000,
    client_order_id="order1",
)

# market order (with safety price)
order = spot.add_order(
    type_="sell",
    src_currency="usdt",
    dst_currency="rls",
    amount="50",
    execution="market",
    price=310000,
)

# stop‑loss
order = spot.add_order(
    type_="sell",
    src_currency="doge",
    dst_currency="rls",
    amount="64",
    execution="stop_market",
    stop_price="47500",
)

# OCO
orders = spot.add_order(
    type_="buy",
    src_currency="btc",
    dst_currency="usdt",
    amount="0.01",
    mode="oco",
    price="42390",
    stop_price="42700",
    stop_limit_price="42715",
)

# check status
status = spot.get_order_status(order_id=order["order"]["id"])

# list orders
active = spot.get_orders_list(status="open", src_currency="btc")

# cancel
spot.update_order_status(status="canceled", order_id=100)
spot.cancel_old_orders(hours=2.4, src_currency="btc")

# user trades
trades = spot.get_trades_list(src_currency="usdt", dst_currency="rls")
```

### Margin trading

```python
from nobitex.resources.margin import Margin

margin = Margin(client)

# available markets
markets = margin.get_markets()

# transfer collateral to margin wallet
margin.transfer(currency="rls", amount="5000000", src="spot", dst="margin")

# delegation limits
limits = margin.get_delegation_limits("BTCUSDT")

# open a short position
order = margin.add_order(
    type_="sell",
    src_currency="btc",
    dst_currency="usdt",
    amount="0.01",
    price="34000",
    leverage="2",
)

# positions
positions = margin.get_positions(status="active")
position = margin.get_position(position_id=128)

# close
close_order = margin.close_position(position_id=128, amount="0.01", price="33000")

# edit collateral
margin.edit_collateral(position_id=128, collateral="230000000")
```

### Withdrawals

```python
from nobitex.resources.withdrawals import Withdrawals

w = Withdrawals(client)

# crypto withdrawal
resp = w.crypto_withdraw(
    wallet=3456,
    amount="0.0123",
    address="destination-address",
    network="BTC",
    otp_header="123456",   # X‑TOTP header (if required)
)
# confirm with OTP
w.confirm_crypto_withdraw(withdraw_id=resp["withdraw"]["id"], otp=623005)

# get status
w.get_crypto_withdraw(433)

# rial withdrawal
resp = w.rial_withdraw(destination_bank_account_id=13568, amount="2500000000")
w.cancel_rial_withdraw(resp["result"]["id"])   # within 3 min if "New"

# list all
all_withdrawals = w.get_list()
```

### Address book & whitelist

```python
from nobitex.resources.address_book import AddressBook

ab = AddressBook(client)

# list addresses
addresses = ab.list_addresses()

# add
ab.add_address(
    title="My Binance",
    network="BSC",
    address="0x...",
    otp_code="123456",
    tfa_code="654321",
    tag="memo-tag",
)

# delete
ab.delete_address(address_id=5)

# whitelist mode
ab.activate_whitelist()
ab.deactivate_whitelist(otp_code="1234", tfa_code="12345")
```

### Security

```python
from nobitex.resources.security import Security

sec = Security(client)

# login history
sec.get_login_attempts()

# emergency cancel
sec.activate_emergency_cancel()

# anti‑phishing code
sec.create_anti_phishing_code(code="mySecret", otp_code="123456")
sec.get_anti_phishing_code()
```

### Referrals

```python
from nobitex.resources.referrals import Referrals

ref = Referrals(client)

# list existing codes
ref.get_links()

# create a new code (friend gets 10% fee share)
ref.create_link(friend_share=10)

# check if this user was invited
ref.get_referral_status()

# set referrer (within 24h of signup)
ref.set_referrer("40404")
```

### Profits

```python
from nobitex.resources.profits import Profits

profits = Profits(client)

# daily breakdown (last 7 days)
profits.get_last_week_daily_profit()

# 30‑day report
profits.get_last_week_daily_profit(monthly=True)

# total daily cumulative
profits.get_last_week_daily_total_profit()

# last month overall
profits.get_last_month_total_profit()
```

### WebSocket (async)

```python
import asyncio
from nobitex import Client
from nobitex.resources.websocket import WebSocketClient

async def handle_orderbook(data):
    print(f"Best ask: {data['asks'][0]}")

async def main():
    rest = Client(token="your-token")
    ws = WebSocketClient(rest)
    await ws.connect()

    # public channels
    await ws.subscribe_orderbook("BTCIRT", handle_orderbook)
    await ws.subscribe_trades("BTCIRT", lambda d: print(d["price"]))
    await ws.subscribe_candle("BTCUSDT", "15", lambda d: print(d["c"]))
    await ws.subscribe_market_stats("BTCIRT", lambda d: print(d["latest"]))

    # private channels (requires websocket_auth_param from profile)
    ws.websocket_auth_param = "your-auth-param"
    await ws.subscribe_private_orders(lambda d: print(d["status"]))
    await ws.subscribe_private_trades(lambda d: print(d["price"]))

    await asyncio.sleep(60)
    await ws.disconnect()

asyncio.run(main())
```

### Authentication helpers

```python
from nobitex.resources.auth import Auth

# Automatic login (if you really need it — panel tokens are preferred)
resp = Auth.login("email@example.com", "password", totp_code="123456")
token = resp["key"]

# Logout / revoke
Auth.logout(token)
```

### System options

```python
from nobitex.resources.options import Options

options = Options(client)
config = options.get()
print(config["coins"][0]["name"])
print(config["nobitex"]["minOrders"])
```

## Exception handling

All exceptions inherit from `APIError` and include `status_code`, `response_body`, and `headers`:

```python
from nobitex.exceptions import (
    APIError,
    AuthenticationError,    # 401
    AuthorizationError,     # 403
    NotFoundError,          # 404
    ValidationError,        # 422
    RateLimitError,         # 429 (has retry_after_seconds)
    ServerError,            # 5xx
)

try:
    account.get_profile()
except AuthenticationError:
    # wrong or expired token
    ...
except RateLimitError as e:
    print(f"Back off for {e.retry_after_seconds} seconds")
```


## Development

```bash
# install with dev dependencies
pip install -e ".[dev]"

# run unit tests (offline, no credentials)
pytest tests/ -v -m "not integration"

# run integration tests (requires real token)
export NOBITEX_TOKEN="your-token"
pytest tests/test_integration.py -v

# run WebSocket tests (requires centrifuge-python)
pip install -e ".[websocket]"
pytest tests/test_websocket.py
```

## License

MIT – see [LICENSE](LICENSE).
