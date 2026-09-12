"""Tests for question_to_filter's mapping of a mocked Anthropic tool-use response."""

from unittest.mock import Mock, patch

from backend.services.nl_to_filter import question_to_filter


def _mock_client(extracted: dict):
    tool_use_block = Mock(type="tool_use", input=extracted)
    response = Mock(content=[tool_use_block])
    client = Mock()
    client.messages.create.return_value = response
    return client


def test_question_to_filter_maps_tool_use_response():
    """The tool-use response's fields map onto QueryFilter, since_days_ago resolved to a date."""
    extracted = {"token": "USDC", "min_amount_usd": 1_000_000.0, "since_days_ago": 7}
    with patch(
        "backend.services.nl_to_filter.get_anthropic_client",
        return_value=_mock_client(extracted),
    ):
        query = question_to_filter("USDC transfers over $1M last week")

    assert query.token == "USDC"
    assert query.min_amount_usd == 1_000_000.0
    assert query.since is not None


def test_question_to_filter_leaves_unset_fields_null():
    """Fields the model didn't extract stay None rather than defaulting to something guessed."""
    extracted = {"token": None, "min_amount_usd": None, "since_days_ago": None}
    with patch(
        "backend.services.nl_to_filter.get_anthropic_client",
        return_value=_mock_client(extracted),
    ):
        query = question_to_filter("show me everything")

    assert query.token is None
    assert query.min_amount_usd is None
    assert query.since is None
