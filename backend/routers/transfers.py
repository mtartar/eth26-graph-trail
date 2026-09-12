"""Transfer listing endpoint."""

from datetime import datetime

from fastapi import APIRouter

from backend.models import FlagResult, QueryFilter
from backend.services.data_source import get_data_source

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.get("", response_model=FlagResult)
def list_transfers(
    token: str | None = None,
    chain: str | None = None,
    min_amount_usd: float | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> FlagResult:
    """Return transfers matching the given filters, plus their totals."""
    query = QueryFilter(
        token=token,
        chain=chain,
        min_amount_usd=min_amount_usd,
        since=since,
        until=until,
    )
    transfers = get_data_source().fetch_transfers(query)
    return FlagResult.from_transfers(transfers)
