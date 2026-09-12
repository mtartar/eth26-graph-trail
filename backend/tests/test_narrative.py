"""Tests for summarize_transfers."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from backend.models import Transfer
from backend.services.narrative import summarize_transfers

_TRANSFER = Transfer(
    token="USDC",
    chain="ethereum",
    amount_usd=1_500_000.0,
    from_address="0xabc",
    to_address="0xdef",
    timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc),
    tx_hash="0x123",
    explorer_url="https://etherscan.io/tx/0x123",
    source="fixture",
)


def test_summarize_transfers_returns_llm_text():
    """The summary is the concatenated text blocks from the LLM response."""
    text_block = Mock(type="text", text="1 transfer totaling $1.5M.")
    response = Mock(content=[text_block])
    client = Mock()
    client.messages.create.return_value = response

    with patch("backend.services.narrative.get_anthropic_client", return_value=client):
        summary = summarize_transfers([_TRANSFER])

    assert summary == "1 transfer totaling $1.5M."


def test_summarize_transfers_handles_empty_list_without_calling_llm():
    """An empty transfer list short-circuits to a fixed message, no LLM call needed."""
    with patch("backend.services.narrative.get_anthropic_client") as mock_get_client:
        summary = summarize_transfers([])

    assert summary == "No transfers match the current filters."
    mock_get_client.assert_not_called()
