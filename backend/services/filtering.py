"""Transfer-filtering logic shared by every data source."""

from backend.models import QueryFilter, Transfer


def matches_filter(transfer: Transfer, query: QueryFilter) -> bool:
    """Check whether a transfer satisfies every set field on the query filter."""
    if query.token and transfer.token.upper() != query.token.upper():
        return False
    if query.chain and transfer.chain.lower() != query.chain.lower():
        return False
    if query.min_amount_usd is not None and transfer.amount_usd < query.min_amount_usd:
        return False
    if query.since and transfer.timestamp < query.since:
        return False
    if query.until and transfer.timestamp > query.until:
        return False
    return True
