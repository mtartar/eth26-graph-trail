"""Pydantic schemas shared across the API."""

from datetime import datetime

from pydantic import BaseModel, Field


class Transfer(BaseModel):
    """A single stablecoin transfer, from whichever data source served it."""

    token: str
    chain: str
    amount_usd: float
    from_address: str
    to_address: str
    timestamp: datetime
    tx_hash: str
    explorer_url: str
    source: str = Field(description="Where this row came from: fixture | subgraph_mcp | token_api")


class QueryFilter(BaseModel):
    """Filters accepted by the transfers endpoint."""

    token: str | None = None
    chain: str | None = None
    min_amount_usd: float | None = None
    since: datetime | None = None
    until: datetime | None = None


class FlagResult(BaseModel):
    """A filtered set of transfers plus its summary totals."""

    transfers: list[Transfer]
    count: int
    total_amount_usd: float
