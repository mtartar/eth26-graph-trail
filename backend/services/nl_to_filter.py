"""One LLM call turning a natural-language question into a structured QueryFilter."""

from datetime import datetime, timedelta, timezone

from anthropic.types import ToolParam

from backend.config import settings
from backend.models import QueryFilter
from backend.services.llm_client import get_anthropic_client

_TOOL_NAME = "extract_query_filter"

_TOOL_SCHEMA: ToolParam = {
    "name": _TOOL_NAME,
    "description": "Extract structured transfer-search filters from a natural-language question.",
    "input_schema": {
        "type": "object",
        "properties": {
            "token": {
                "type": ["string", "null"],
                "description": "Stablecoin symbol, e.g. USDC, USDT, PYUSD. Null if not mentioned.",
            },
            "min_amount_usd": {
                "type": ["number", "null"],
                "description": "Minimum amount in USD, e.g. 1000000 for '$1M'. Null if unset.",
            },
            "since_days_ago": {
                "type": ["integer", "null"],
                "description": "Days back the question refers to, e.g. 7 for 'last week'.",
            },
        },
        "required": [],
    },
}

_SYSTEM_PROMPT = (
    "You extract search filters for a stablecoin transfer ledger from a compliance "
    "officer's plain-English question. Only extract what's explicitly stated or "
    "clearly implied; leave fields null rather than guessing."
)


def question_to_filter(question: str) -> QueryFilter:
    """Turn a natural-language question into a QueryFilter via one forced tool call."""
    client = get_anthropic_client()
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=256,
        system=_SYSTEM_PROMPT,
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": _TOOL_NAME},
        messages=[{"role": "user", "content": question}],
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    extracted = tool_use.input
    assert isinstance(extracted, dict)  # guaranteed by the forced tool schema above

    since = None
    since_days_ago = extracted.get("since_days_ago")
    if isinstance(since_days_ago, int):
        since = datetime.now(timezone.utc) - timedelta(days=since_days_ago)

    token = extracted.get("token")
    min_amount_usd = extracted.get("min_amount_usd")

    return QueryFilter(
        token=token if isinstance(token, str) else None,
        min_amount_usd=min_amount_usd if isinstance(min_amount_usd, int | float) else None,
        since=since,
    )
