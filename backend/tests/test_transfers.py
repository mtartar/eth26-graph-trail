"""Tests for the /transfers endpoint against the fixture data source."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_list_transfers_returns_fixture_data():
    """The endpoint returns fixture rows with a count matching the list length."""
    response = client.get("/transfers")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    assert body["count"] == len(body["transfers"])


def test_min_amount_filter_excludes_smaller_transfers():
    """min_amount_usd excludes every transfer below the threshold."""
    response = client.get("/transfers", params={"min_amount_usd": 5_000_000})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    assert all(t["amount_usd"] >= 5_000_000 for t in body["transfers"])


def test_token_filter_is_case_insensitive():
    """A lowercase token filter still matches uppercase-stored tokens."""
    response = client.get("/transfers", params={"token": "usdc"})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    assert all(t["token"] == "USDC" for t in body["transfers"])
