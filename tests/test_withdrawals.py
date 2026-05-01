"""Tests for the Withdrawals resource (crypto & rial endpoints)."""

import json
import pytest
import responses

from nobitex.resources.withdrawals import Withdrawals


# ---------------------------------------------------------------
# crypto_withdraw
# ---------------------------------------------------------------
def test_crypto_withdraw_minimal(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "withdraw": {"id": 432}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/withdraw",
        json=expected,
    )

    result = Withdrawals(client_token).crypto_withdraw(
        wallet=3456,
        amount="0.0123",
        address="SaMpLeWaLlEtAdDrEsS",
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["wallet"] == 3456
    assert body["amount"] == "0.0123"
    assert body["address"] == "SaMpLeWaLlEtAdDrEsS"
    # No extra headers for X-TOTP
    assert "X-TOTP" not in mocked_responses.calls[0].request.headers


def test_crypto_withdraw_with_otp_header(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "withdraw": {"id": 433}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/withdraw",
        json=expected,
    )

    result = Withdrawals(client_token).crypto_withdraw(
        wallet=3456,
        amount="0.5",
        address="abc123",
        otp_header="123456",
    )

    assert result == expected
    headers = mocked_responses.calls[0].request.headers
    assert headers["X-TOTP"] == "123456"


def test_crypto_withdraw_with_network_and_tag(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "withdraw": {"id": 434}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/withdraw",
        json=expected,
    )

    result = Withdrawals(client_token).crypto_withdraw(
        wallet=3456,
        network="BSC",
        tag="123456",
        no_tag=False,
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["network"] == "BSC"
    assert body["tag"] == "123456"
    assert "noTag" not in body   # false by default, not sent


def test_crypto_withdraw_no_tag(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "withdraw": {}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/withdraw",
        json=expected,
    )

    Withdrawals(client_token).crypto_withdraw(
        wallet=3456,
        no_tag=True,
    )

    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["noTag"] is True


def test_crypto_withdraw_with_invoice(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "withdraw": {"id": 435}}
    invoice = "lnbc123..."
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/withdraw",
        json=expected,
    )

    result = Withdrawals(client_token).crypto_withdraw(
        wallet=3456,
        invoice=invoice,
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["invoice"] == invoice
    # amount and address not sent
    assert "amount" not in body
    assert "address" not in body


def test_crypto_withdraw_extra_headers(mocked_responses, client_token, base_url):
    expected = {"status": "ok"}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/withdraw",
        json=expected,
    )

    Withdrawals(client_token).crypto_withdraw(
        wallet=3456,
        extra_headers={"Custom-Header": "value"},
    )

    headers = mocked_responses.calls[0].request.headers
    assert headers["Custom-Header"] == "value"


# ---------------------------------------------------------------
# confirm_crypto_withdraw
# ---------------------------------------------------------------
def test_confirm_crypto_withdraw_with_otp(mocked_responses, client_token, base_url):
    withdraw_id = 432
    expected = {"status": "ok", "withdraw": {"id": withdraw_id, "status": "Verified"}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/withdraw-confirm",
        json=expected,
    )

    result = Withdrawals(client_token).confirm_crypto_withdraw(
        withdraw_id=withdraw_id,
        otp=623005,
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["withdraw"] == withdraw_id
    assert body["otp"] == 623005


def test_confirm_crypto_withdraw_without_otp(mocked_responses, client_token, base_url):
    withdraw_id = 432
    expected = {"status": "ok", "withdraw": {"id": withdraw_id}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/users/wallets/withdraw-confirm",
        json=expected,
    )

    result = Withdrawals(client_token).confirm_crypto_withdraw(
        withdraw_id=withdraw_id,
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["withdraw"] == withdraw_id
    assert "otp" not in body


# ---------------------------------------------------------------
# get_crypto_withdraw
# ---------------------------------------------------------------
def test_get_crypto_withdraw(mocked_responses, client_token, base_url):
    withdraw_id = 433
    expected = {"status": "ok", "withdraw": {"id": withdraw_id}}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/withdraws/{withdraw_id}",
        json=expected,
    )

    result = Withdrawals(client_token).get_crypto_withdraw(withdraw_id)
    assert result == expected


# ---------------------------------------------------------------
# rial_withdraw
# ---------------------------------------------------------------
def test_rial_withdraw(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "result": {"id": "CW430542"}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/cobank/withdraw",
        json=expected,
    )

    result = Withdrawals(client_token).rial_withdraw(
        destination_bank_account_id=13568,
        amount="2500000000",
    )

    assert result == expected
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body["destinationBankAccountId"] == 13568
    assert body["amount"] == "2500000000"


# ---------------------------------------------------------------
# cancel_rial_withdraw
# ---------------------------------------------------------------
def test_cancel_rial_withdraw(mocked_responses, client_token, base_url):
    withdraw_id = "CW430542"
    expected = {"status": "ok", "result": {"id": withdraw_id, "status": "Canceled"}}
    mocked_responses.add(
        responses.POST,
        f"{base_url}/cobank/withdraw/{withdraw_id}/cancel",
        json=expected,
    )

    result = Withdrawals(client_token).cancel_rial_withdraw(withdraw_id)
    assert result == expected


# ---------------------------------------------------------------
# get_rial_withdraw
# ---------------------------------------------------------------
def test_get_rial_withdraw(mocked_responses, client_token, base_url):
    withdraw_id = "CW430542"
    expected = {"status": "ok", "result": {"id": withdraw_id}}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/cobank/withdraw/{withdraw_id}",
        json=expected,
    )

    result = Withdrawals(client_token).get_rial_withdraw(withdraw_id)
    assert result == expected


# ---------------------------------------------------------------
# get_list
# ---------------------------------------------------------------
def test_get_withdraws_list(mocked_responses, client_token, base_url):
    expected = {"status": "ok", "withdraws": [], "hasNext": False}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/wallets/withdraws/list",
        json=expected,
    )

    result = Withdrawals(client_token).get_list()
    assert result == expected
