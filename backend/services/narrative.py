"""One LLM call turning a filtered transfer list into a short plain-English summary."""

from backend.config import settings
from backend.models import Transfer
from backend.services.llm_client import get_anthropic_client

_SYSTEM_PROMPT = (
    "You write a short, factual summary of a filtered list of stablecoin transfers "
    "for a compliance officer. Plain register, no hype, 2-3 sentences. State the "
    "count, total USD volume, and any notable concentration (e.g. few counterparties, "
    "a tight time window) if visible in the data. Don't invent figures not in the data."
)


def summarize_transfers(transfers: list[Transfer]) -> str:
    """Return a 2-3 sentence plain-English summary of the given transfers."""
    if not transfers:
        return "No transfers match the current filters."

    rows = "\n".join(
        f"- {t.timestamp.isoformat()} | {t.token} | ${t.amount_usd:,.2f} | "
        f"{t.from_address} -> {t.to_address}"
        for t in transfers
    )

    client = get_anthropic_client()
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=200,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": rows}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
