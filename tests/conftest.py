import pytest
import responses as responses_lib

from nobitex.client import Client
from nobitex.exceptions import (
    AuthenticationError,
    RateLimitError,
    NotFoundError,
)


@pytest.fixture
def base_url():
    return "https://apiv2.nobitex.ir"


@pytest.fixture
def token():
    return "test-token-123"


@pytest.fixture
def api_key():
    return "public-key-abc"


@pytest.fixture
def private_key_hex():
    # A valid Ed25519 private key as a hex string for signing tests.
    # This is only used when you want to test the real signing path.
    # For most tests you’ll mock the signature.
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    pk = Ed25519PrivateKey.generate()
    return pk.private_bytes_raw().hex()


@pytest.fixture
def client_token(base_url, token):
    return Client(token=token, base_url=base_url)


@pytest.fixture
def client_api_key(base_url, api_key, private_key_hex):
    # This fixture will fail if cryptography is not installed.
    return Client(api_key=api_key, private_key=private_key_hex, base_url=base_url)


@pytest.fixture
def mocked_responses():
    """Empty responses start, automatically stops after test."""
    with responses_lib.RequestsMock() as rsps:
        yield rsps
