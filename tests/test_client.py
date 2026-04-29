import json
import re

import pytest
import responses

from nobitex.client import Client
from nobitex.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)


# ---------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------
def test_client_requires_auth(base_url):
    with pytest.raises(ValueError, match="Either a token or both api_key"):
        Client(base_url=base_url)


def test_client_with_token(token, base_url):
    client = Client(token=token, base_url=base_url)
    assert client._token == token


def test_client_with_api_key(api_key, private_key_hex, base_url):
    client = Client(api_key=api_key, private_key=private_key_hex, base_url=base_url)
    assert client._api_key == api_key
    assert client._private_key is not None


# ---------------------------------------------------------------
# Trailing slash enforcement
# ---------------------------------------------------------------
@responses.activate
def test_get_appends_trailing_slash(mocked_responses, client_token, base_url):
    # Mock any GET to /users/profile/ (with slash)
    mocked_responses.add(
        responses.GET,
        re.compile(rf"{base_url}/users/profile/?$"),
        json={"status": "ok"},
    )
    # Request without trailing slash
    client_token.get("/users/profile")  # no slash
    # Check that the called URL ended with /
    assert mocked_responses.calls[0].request.url.endswith("/users/profile/")


# ---------------------------------------------------------------
# Authentication headers
# ---------------------------------------------------------------
@responses.activate
def test_token_auth_header(mocked_responses, client_token, base_url):
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/profile/",
        json={},
    )
    client_token.get("/users/profile")
    headers = mocked_responses.calls[0].request.headers
    assert headers["Authorization"] == f"Token {client_token._token}"


@responses.activate
def test_api_key_auth_headers(mocked_responses, client_api_key, base_url):
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/profile/",
        json={},
    )
    client_api_key.get("/users/profile")
    headers = mocked_responses.calls[0].request.headers
    assert "Nobitex-Key" in headers
    assert "Nobitex-Signature" in headers
    assert "Nobitex-Timestamp" in headers
    assert headers["Nobitex-Key"] == client_api_key._api_key
    # Signature is non‑empty
    assert len(headers["Nobitex-Signature"]) > 0


# ---------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------
@responses.activate
def test_401_raises_authentication_error(mocked_responses, client_token, base_url):
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/profile/",
        json={"message": "Invalid token"},
        status=401,
    )
    with pytest.raises(AuthenticationError) as exc_info:
        client_token.get("/users/profile")
    assert exc_info.value.status_code == 401
    assert "Invalid token" in str(exc_info.value)


@responses.activate
def test_404_raises_not_found_error(mocked_responses, client_token, base_url):
    mocked_responses.add(
        responses.GET,
        f"{base_url}/some/endpoint/",
        json={"message": "Not found"},
        status=404,
    )
    with pytest.raises(NotFoundError) as exc_info:
        client_token.get("/some/endpoint")
    assert exc_info.value.status_code == 404


@responses.activate
def test_429_raises_rate_limit_error_with_retry(mocked_responses, client_token, base_url):
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/profile/",
        json={"message": "Too many requests"},
        status=429,
        headers={"Retry-After": "30"},
    )
    with pytest.raises(RateLimitError) as exc_info:
        client_token.get("/users/profile")
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after_seconds == 30


# ---------------------------------------------------------------
# Success case – returns JSON
# ---------------------------------------------------------------
@responses.activate
def test_successful_get_returns_parsed_json(mocked_responses, client_token, base_url):
    expected = {"data": "test"}
    mocked_responses.add(
        responses.GET,
        f"{base_url}/users/profile/",
        json=expected,
    )
    result = client_token.get("/users/profile")
    assert result == expected
