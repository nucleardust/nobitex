# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] – 2026-05-01

### Added
- Initial release of the Nobitex Python API wrapper.
- Sync HTTP client with token and API‑Key (Ed25519) authentication.
- Full exception hierarchy (`APIError`, `AuthenticationError`, `RateLimitError`, …).
- Resource modules for all API sections:
  - `Market` – public orderbook, trades, stats, OHLC.
  - `Account` – profile, wallets, balances, transactions, deposits, favorite markets.
  - `Spot` – spot trading (limit, market, stop‑loss, OCO orders, cancel, list).
  - `Margin` – margin trading (markets, positions, orders, collateral, delegation limits).
  - `Withdrawals` – crypto withdrawal (create, confirm, status), rial withdrawal (create, cancel, status), list all.
  - `AddressBook` – address book management and withdrawal whitelist.
  - `Security` – login history, emergency cancel, anti‑phishing code.
  - `Referrals` – referral codes, status, set referrer.
  - `Auth` – automatic login/logout helpers.
  - `Profits` – daily/weekly/monthly portfolio profit/loss reports.
  - `WebSocketClient` – async real‑time client for orderbook, trades, candles, private orders (Centrifugo).
  - `Options` – system‑wide configuration and coin info.
- Full test suite with mocked HTTP responses (pytest + responses).
- Integration smoke tests (requires real token).
- Comprehensive README with usage examples for every resource.
