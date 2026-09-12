"""Real data source: The Graph's Token API (operated by Pinax, api.pinax.network)."""

from datetime import datetime, timezone

import httpx

from backend.models import QueryFilter, Transfer
from backend.services.explorers import build_explorer_url
from backend.services.filtering import matches_filter

DEFAULT_BASE_URL = "https://api.pinax.network"

_CHAIN_TO_NETWORK: dict[str, str] = {
    "ethereum": "mainnet",
}

_STABLECOIN_CONTRACTS: dict[str, dict[str, str]] = {
    "ethereum": {
        "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "PYUSD": "0x6c3ea9036406852006290770bedfcaba0e23a0e8",
    },
}


class TokenApiDataSource:
    """Fetches ERC-20 stablecoin transfers from The Graph's Token API."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        """Store the API key and base URL used to authenticate requests."""
        self._api_key = api_key
        self._base_url = base_url

    def fetch_transfers(self, query: QueryFilter) -> list[Transfer]:
        """Fetch transfers for the query's token(s) on one chain, then apply the full filter."""
        chain = query.chain or "ethereum"
        network = _CHAIN_TO_NETWORK.get(chain.lower())
        if network is None:
            return []

        contracts = _STABLECOIN_CONTRACTS.get(chain.lower(), {})
        tokens_to_query = [query.token.upper()] if query.token else list(contracts)

        transfers: list[Transfer] = []
        for token in tokens_to_query:
            contract = contracts.get(token)
            if contract is not None:
                transfers.extend(self._fetch_one_token(token, chain, network, contract, query))
        return [t for t in transfers if matches_filter(t, query)]

    def _fetch_one_token(
        self, token: str, chain: str, network: str, contract: str, query: QueryFilter
    ) -> list[Transfer]:
        """Call the Token API for a single contract and map the response into Transfers."""
        params: dict[str, str] = {"network": network, "contract": contract, "limit": "100"}
        if query.since:
            params["start_time"] = query.since.isoformat()
        if query.until:
            params["end_time"] = query.until.isoformat()

        response = httpx.get(
            f"{self._base_url}/v1/evm/transfers",
            params=params,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json().get("data", [])
        return [self._to_transfer(token, chain, row) for row in rows]

    def _to_transfer(self, token: str, chain: str, row: dict) -> Transfer:
        """Map one Token API transfer row into our Transfer schema."""
        # Stablecoins are ~1:1 USD, so the token's normalized unit value stands in for amount_usd.
        if "value" in row:
            amount_usd = float(row["value"])
        else:
            amount_usd = float(row["amount"]) / 10 ** int(row.get("decimals", 0))

        tx_hash = row["transaction_id"]
        return Transfer(
            token=token,
            chain=chain,
            amount_usd=amount_usd,
            from_address=row["from"],
            to_address=row["to"],
            timestamp=datetime.fromtimestamp(int(row["timestamp"]), tz=timezone.utc),
            tx_hash=tx_hash,
            explorer_url=build_explorer_url(chain, tx_hash),
            source="token_api",
        )
