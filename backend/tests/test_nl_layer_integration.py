"""Integration tests hitting the real Anthropic API — no mocking of the LLM boundary.

These are excluded from the default `pytest` run (see [tool.pytest.ini_options] in
pyproject.toml) since they cost real API credit and need ANTHROPIC_API_KEY set.
Run them explicitly with: pytest -m integration
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app
from backend.models import Transfer
from backend.services.narrative import summarize_transfers
from backend.services.nl_to_filter import question_to_filter

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not settings.anthropic_api_key, reason="ANTHROPIC_API_KEY not set"),
]

client = TestClient(app)

_SAMPLE_TRANSFERS = [
    Transfer(
        token="USDC",
        chain="ethereum",
        amount_usd=15_234_000.00,
        from_address="0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
        to_address="0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e",
        timestamp=datetime(2026, 9, 10, 3, 22, 10, tzinfo=timezone.utc),
        tx_hash="0xa1b2c3d4e5f60718293a4b5c6d7e8f9012345678a1b2c3d4e5f60718293a4b5",
        explorer_url="https://etherscan.io/tx/0xa1b2c3d4e5f60718293a4b5c6d7e8f9012345678a1b2c3d4e5f60718293a4b5",
        source="fixture",
    ),
    Transfer(
        token="USDC",
        chain="ethereum",
        amount_usd=6_100_000.00,
        from_address="0x4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e",
        to_address="0x6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b",
        timestamp=datetime(2026, 9, 6, 22, 11, 37, tzinfo=timezone.utc),
        tx_hash="0xd4e5f60718293a4b5c6d7e8f9012345678a1b2c3d4e5f60718293a4b5c6d7e8",
        explorer_url="https://etherscan.io/tx/0xd4e5f60718293a4b5c6d7e8f9012345678a1b2c3d4e5f60718293a4b5c6d7e8",
        source="fixture",
    ),
]


def test_question_to_filter_extracts_token_and_amount():
    """A question naming a token and a dollar threshold resolves both fields."""
    query = question_to_filter("Show me USDC transfers over $1 million")
    assert query.token == "USDC"
    assert query.min_amount_usd is not None
    assert query.min_amount_usd >= 900_000


def test_question_to_filter_extracts_relative_time_window():
    """A relative time phrase ('last 7 days') resolves to a non-null since date."""
    query = question_to_filter("What USDT transfers happened in the last 7 days?")
    assert query.token == "USDT"
    assert query.since is not None


def test_question_to_filter_leaves_amount_null_when_unspecified():
    """A question with no dollar amount doesn't get one invented."""
    query = question_to_filter("Show me all recent USDC transfers")
    assert query.min_amount_usd is None


def test_summarize_transfers_mentions_the_actual_token():
    """The narrative summary references data that's actually in the input, not invented figures."""
    summary = summarize_transfers(_SAMPLE_TRANSFERS)
    assert len(summary) > 20
    assert "USDC" in summary


def test_query_endpoint_end_to_end_against_fixture_data():
    """Full round trip: real NL extraction, run against the real fixture data source."""
    response = client.post("/query", json={"question": "USDC transfers over $1M"})
    assert response.status_code == 200
    body = response.json()
    assert body["resolved_filter"]["token"] == "USDC"
    assert body["result"]["count"] > 0
    assert all(t["amount_usd"] >= 1_000_000 for t in body["result"]["transfers"])


def test_summary_endpoint_end_to_end_against_real_transfers_endpoint():
    """Full round trip: real /transfers result summarized by the real model."""
    transfers = client.get("/transfers", params={"min_amount_usd": 1_000_000}).json()["transfers"]
    response = client.post("/summary", json={"transfers": transfers})
    assert response.status_code == 200
    assert len(response.json()["summary"]) > 20
