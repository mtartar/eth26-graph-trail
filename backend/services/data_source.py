"""Pluggable sources of transfer data, behind one shared interface."""

import json
from pathlib import Path
from typing import Protocol

from backend.config import settings
from backend.models import QueryFilter, Transfer


class TransferDataSource(Protocol):
    """Interface every transfer data source (fixture, subgraph, token API) implements."""

    def fetch_transfers(self, query: QueryFilter) -> list[Transfer]:
        """Return transfers matching the given filter."""
        ...


class FixtureDataSource:
    """Reads transfers from data/fixtures/sample_transfers.json."""

    def __init__(self, fixture_path: Path):
        """Store the path to the fixture JSON file to read from."""
        self._fixture_path = fixture_path

    def fetch_transfers(self, query: QueryFilter) -> list[Transfer]:
        """Load fixture rows and return those matching the given filter."""
        raw = json.loads(self._fixture_path.read_text())
        transfers = [Transfer(**row) for row in raw]
        return [t for t in transfers if _matches(t, query)]


def _matches(transfer: Transfer, query: QueryFilter) -> bool:
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


def get_data_source() -> TransferDataSource:
    """Build the configured TransferDataSource for the current environment."""
    if settings.data_source == "fixture":
        return FixtureDataSource(Path(settings.fixture_path))
    raise NotImplementedError(f"Data source '{settings.data_source}' is not implemented yet")
