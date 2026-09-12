"""Tests for the /query endpoint (NL question -> filter -> transfers)."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.models import QueryFilter

client = TestClient(app)


def test_query_endpoint_resolves_question_and_returns_matching_transfers():
    """A mocked NL-to-filter call drives a real fixture-backed lookup."""
    with patch(
        "backend.routers.query.question_to_filter",
        return_value=QueryFilter(token="USDC", min_amount_usd=5_000_000),
    ):
        response = client.post("/query", json={"question": "USDC transfers over $5M"})

    assert response.status_code == 200
    body = response.json()
    assert body["resolved_filter"]["token"] == "USDC"
    assert body["result"]["count"] > 0
    assert all(t["amount_usd"] >= 5_000_000 for t in body["result"]["transfers"])
