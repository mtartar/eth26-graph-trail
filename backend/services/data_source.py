"""Pluggable sources of transfer data, behind one shared interface."""

import json
from pathlib import Path
from typing import Protocol

from backend.config import settings
from backend.models import QueryFilter, Transfer
from backend.services.explorers import build_explorer_url
from backend.services.filtering import matches_filter
from backend.services.token_api_client import TokenApiDataSource


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
        transfers = [
            Transfer(**row, explorer_url=build_explorer_url(row["chain"], row["tx_hash"]))
            for row in raw
        ]
        return [t for t in transfers if matches_filter(t, query)]


def get_data_source() -> TransferDataSource:
    """Build the configured TransferDataSource for the current environment.

    DATA_SOURCE is a config flag, not a code branch you pick at build time: if the
    live token_api integration breaks or rate-limits mid-demo, flipping it back to
    "fixture" in .env restores a working /transfers endpoint with no code change.
    """
    if settings.data_source == "fixture":
        return FixtureDataSource(Path(settings.fixture_path))
    if settings.data_source == "token_api":
        if not settings.token_api_key:
            raise RuntimeError("TOKEN_API_KEY must be set in .env when DATA_SOURCE=token_api")
        return TokenApiDataSource(
            api_key=settings.token_api_key, base_url=settings.token_api_base_url
        )
    raise NotImplementedError(f"Data source '{settings.data_source}' is not implemented yet")
