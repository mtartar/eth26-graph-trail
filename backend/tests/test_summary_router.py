"""Tests for the /summary endpoint."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

_TRANSFER_PAYLOAD = {
    "token": "USDC",
    "chain": "ethereum",
    "amount_usd": 1500000.0,
    "from_address": "0xabc",
    "to_address": "0xdef",
    "timestamp": "2026-09-10T00:00:00Z",
    "tx_hash": "0x123",
    "explorer_url": "https://etherscan.io/tx/0x123",
    "source": "fixture",
}


def test_summary_endpoint_returns_generated_text():
    """The endpoint returns whatever summarize_transfers produces."""
    with patch(
        "backend.routers.summary.summarize_transfers",
        return_value="1 transfer totaling $1.5M.",
    ):
        response = client.post("/summary", json={"transfers": [_TRANSFER_PAYLOAD]})

    assert response.status_code == 200
    assert response.json()["summary"] == "1 transfer totaling $1.5M."
