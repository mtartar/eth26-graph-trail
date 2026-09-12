"""Regenerate data/fixtures/sample_transfers.json from real on-chain transfers.

The fixture must contain real tx hashes: FixtureDataSource builds each row's
explorer_url from tx_hash, and a fabricated hash 404s on Etherscan — which
directly contradicts this project's "traceable to a real source" trust story.

Queries a handful of large, real USDC/USDT/PYUSD Transfer events from a recent
block range via a public RPC endpoint (no API key needed), dedupes by tx_hash
(a single transaction can emit more than one Transfer log), and writes the
result as the new fixture. Run from the repo root: python scripts/regenerate_fixture_data.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

import httpx

RPC_URL = "https://ethereum.publicnode.com"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
MIN_AMOUNT_USD = 200_000
CHUNK_BLOCKS = 250
CHUNKS_PER_TOKEN = 8
MAX_PER_TOKEN = 4
MAX_TOTAL = 10
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "sample_transfers.json"


class TokenInfo(NamedTuple):
    """Contract address and decimal precision for one stablecoin."""

    address: str
    decimals: int


TOKENS: dict[str, TokenInfo] = {
    "USDC": TokenInfo("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 6),
    "USDT": TokenInfo("0xdac17f958d2ee523a2206206994597c13d831ec7", 6),
    "PYUSD": TokenInfo("0x6c3ea9036406852006290770bedfcaba0e23a0e8", 6),
}


def rpc_call(client: httpx.Client, method: str, params: list, retries: int = 3):
    """Call the RPC endpoint, retrying a couple of times on transient failures."""
    last_error = RuntimeError("rpc_call was given retries=0")
    for _ in range(retries):
        try:
            response = client.post(
                RPC_URL, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
            )
            response.raise_for_status()
            body = response.json()
            if "error" in body:
                raise RuntimeError(body["error"])
            return body["result"]
        except Exception as error:  # noqa: BLE001 - retry on anything, re-raise after
            last_error = error
            time.sleep(1)
    raise last_error


def fetch_candidates(client: httpx.Client, latest_block: int) -> list[dict]:
    """Fetch large Transfer events per token, deduped by tx_hash, across recent blocks."""
    candidates: list[dict] = []
    seen_tx_hashes: set[str] = set()

    for token, info in TOKENS.items():
        found = 0
        for chunk in range(CHUNKS_PER_TOKEN):
            to_block = latest_block - chunk * CHUNK_BLOCKS
            from_block = to_block - CHUNK_BLOCKS
            logs = rpc_call(
                client,
                "eth_getLogs",
                [
                    {
                        "address": info.address,
                        "topics": [TRANSFER_TOPIC],
                        "fromBlock": hex(from_block),
                        "toBlock": hex(to_block),
                    }
                ],
            )
            for log in logs:
                tx_hash = log["transactionHash"]
                if tx_hash in seen_tx_hashes:
                    continue
                amount = int(log["data"], 16) / (10**info.decimals)
                if amount < MIN_AMOUNT_USD:
                    continue
                seen_tx_hashes.add(tx_hash)
                candidates.append(
                    {
                        "token": token,
                        "chain": "ethereum",
                        "amount_usd": round(amount, 2),
                        "from_address": "0x" + log["topics"][1][-40:],
                        "to_address": "0x" + log["topics"][2][-40:],
                        "tx_hash": tx_hash,
                        "block_number": int(log["blockNumber"], 16),
                    }
                )
                found += 1
            if found >= MAX_PER_TOKEN:
                break
    return candidates


def select_and_timestamp(client: httpx.Client, candidates: list[dict]) -> list[dict]:
    """Pick a capped, varied selection and resolve each one's real block timestamp."""
    candidates.sort(key=lambda c: c["amount_usd"], reverse=True)
    per_token_count: dict[str, int] = {}
    selected = []
    for candidate in candidates:
        count = per_token_count.get(candidate["token"], 0)
        if count < MAX_PER_TOKEN and len(selected) < MAX_TOTAL:
            selected.append(candidate)
            per_token_count[candidate["token"]] = count + 1
    selected.sort(key=lambda c: c["amount_usd"], reverse=True)

    block_timestamps: dict[int, int] = {}
    for candidate in selected:
        block_number = candidate.pop("block_number")
        if block_number not in block_timestamps:
            block = rpc_call(client, "eth_getBlockByNumber", [hex(block_number), False])
            block_timestamps[block_number] = int(block["timestamp"], 16)
        timestamp = datetime.fromtimestamp(block_timestamps[block_number], tz=timezone.utc)
        candidate["timestamp"] = timestamp.isoformat().replace("+00:00", "Z")
        candidate["source"] = "fixture"
    return selected


def main() -> None:
    """Fetch real transfers and overwrite the fixture file."""
    with httpx.Client(timeout=30) as client:
        latest_block = int(rpc_call(client, "eth_blockNumber", []), 16)
        candidates = fetch_candidates(client, latest_block)
        selected = select_and_timestamp(client, candidates)

    tx_hashes = [row["tx_hash"] for row in selected]
    assert len(tx_hashes) == len(set(tx_hashes)), "duplicate tx_hash made it into the selection"

    OUTPUT_PATH.write_text(json.dumps(selected, indent=2) + "\n")
    print(f"Wrote {len(selected)} real transfers to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
