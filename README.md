# nobitex

Python client for the [Nobitex](https://nobitex.ir/) API v2.

![Demo](assets/demo.gif)

## Installation

```bash
pip install nobitex
```

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

API‑Key authentication with Ed25519 signatures is also supported:

```python
client = Client(
    api_key="public-key",
    private_key="private-key",
)
```

## Usage examples

**Public market data**

```python
from nobitex import Client
from nobitex.resources.market import Market

market = Market(Client(token="dummy"))  # token ignored for public endpoints
stats = market.get_stats(src_currency="btc", dst_currency="rls")
trades = market.get_trades("BTCIRT")
```

**Account & wallets**

```python
from nobitex import Client
from nobitex.resources.account import Account

client = Client(token="your-token")
account = Account(client)

profile = account.get_profile()
balance = account.get_balance("rls")
wallets = account.get_wallets_list()
```

**Spot trading**

```python
from nobitex import Client
from nobitex.resources.spot import Spot

client = Client(token="your-token")
spot = Spot(client)

# place a limit buy order
order = spot.add_order(
    type_="buy",
    src_currency="btc",
    dst_currency="rls",
    amount="0.01",
    price=500000000,
)

# check status
status = spot.get_order_status(order_id=order["order"]["id"])
```

**Margin trading**

```python
from nobitex import Client
from nobitex.resources.margin import Margin

client = Client(token="your-token")
margin = Margin(client)

positions = margin.get_positions(status="active")
```

## Exceptions

The library raises typed exceptions for different error conditions:

```python
from nobitex.exceptions import AuthenticationError, RateLimitError, NotFoundError

try:
    account.get_profile()
except AuthenticationError:
    # invalid or expired token
    pass
except RateLimitError as e:
    retry_after = e.retry_after_seconds
```

## Development

```bash
# install with dev dependencies
pip install -e ".[dev]"

# run unit tests (offline)
pytest tests/ -v

# run integration tests (requires a live token)
export NOBITEX_TOKEN="your-token"
pytest tests/test_integration.py -v
```

## License

MIT
