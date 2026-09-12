"""Tests for TokenApiDataSource's mapping of Token API responses to Transfers."""

from unittest.mock import Mock, patch

from backend.models import QueryFilter
from backend.services.token_api_client import TokenApiDataSource

_SAMPLE_RESPONSE = {
    "data": [
        {
            "block_num": 24278225,
            "datetime": "2026-01-20 19:57:11",
            "timestamp": 1768939031,
            "transaction_id": "0x589cbe12efa0cca5a29b17bf7ee49c99566f0e05e937d54104134a2d916ab26",
            "log_index": 24,
            "contract": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "from": "0x2393d38400cad1d0ffae85b37d76de05bb7eddc6",
            "to": "0xd4f1171683f1bc07b77d0307a01b64dba5369cf8",
            "symbol": "USDC",
            "amount": "2686000000",
            "decimals": 6,
            "network": "mainnet",
        }
    ]
}


def test_fetch_transfers_maps_token_api_response_to_transfer():
    """A Token API row maps to a Transfer with a computed USD amount and explorer link."""
    mock_response = Mock()
    mock_response.json.return_value = _SAMPLE_RESPONSE
    mock_response.raise_for_status.return_value = None

    with patch("backend.services.token_api_client.httpx.get", return_value=mock_response):
        source = TokenApiDataSource(api_key="test-key")
        transfers = source.fetch_transfers(QueryFilter(token="USDC"))

    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.token == "USDC"
    assert transfer.chain == "ethereum"
    assert transfer.amount_usd == 2686.0
    assert transfer.from_address == "0x2393d38400cad1d0ffae85b37d76de05bb7eddc6"
    assert transfer.tx_hash.startswith("0x589cbe12")
    assert transfer.explorer_url == f"https://etherscan.io/tx/{transfer.tx_hash}"
    assert transfer.source == "token_api"


def test_fetch_transfers_applies_min_amount_filter():
    """A min_amount_usd above the fixture row's value excludes it."""
    mock_response = Mock()
    mock_response.json.return_value = _SAMPLE_RESPONSE
    mock_response.raise_for_status.return_value = None

    with patch("backend.services.token_api_client.httpx.get", return_value=mock_response):
        source = TokenApiDataSource(api_key="test-key")
        transfers = source.fetch_transfers(QueryFilter(token="USDC", min_amount_usd=1_000_000))

    assert transfers == []


def test_fetch_transfers_skips_unknown_chain():
    """A chain with no configured network mapping returns no transfers, not an error."""
    source = TokenApiDataSource(api_key="test-key")
    transfers = source.fetch_transfers(QueryFilter(token="USDC", chain="solana"))
    assert transfers == []
