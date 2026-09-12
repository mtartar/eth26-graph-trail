# Graph Trail, ETHOnline 2026 (The Graph tracks)

A ledger of large stablecoin transfers where every number traces back to its onchain source.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload --port 8010
```

Open `http://127.0.0.1:8010/docs` and try `GET /transfers` (optionally with `token`, `chain`, `min_amount_usd`, `since`, `until` query params).

## Data sources

`DATA_SOURCE` in `.env` picks where `/transfers` reads from — no code change needed to switch:

- `fixture` (default) — reads `data/fixtures/sample_transfers.json`. **These are real, on-chain transactions** (fetched from a live Ethereum block range via public RPC `eth_getLogs`, not fabricated) — every `tx_hash` genuinely exists and its explorer link resolves to a real transaction. This matters: `explorer_url` is built from `tx_hash`, and a fake hash would 404, contradicting the whole "traceable to a real source" premise. Regenerate with `python scripts/regenerate_fixture_data.py` to pull a fresh set.
- `token_api` — real ERC-20 stablecoin transfers (USDC/USDT/PYUSD on Ethereum) from The Graph's Token API. Sign up at https://api.pinax.network for a key, then set `TOKEN_API_KEY` in `.env`.

If the live `token_api` integration breaks or rate-limits, set `DATA_SOURCE=fixture` and restart — that's the entire recovery procedure.

## NL query & summary

`POST /query` (question → filter → transfers) and `POST /summary` (transfers → short narrative) need `ANTHROPIC_API_KEY` in `.env`. See [docs/anthropic-api-key.md](docs/anthropic-api-key.md) for how to get one, set it, and verify it works.

## Frontend

With the backend running (above), in a second terminal:

```bash
source .venv/bin/activate
streamlit run frontend/app.py
```

Opens at `http://localhost:8501`. The frontend only talks to the backend over HTTP (`BACKEND_URL`, default `http://127.0.0.1:8010`) — it never imports backend code or touches a data source directly. The "Or browse directly" panel works with no `ANTHROPIC_API_KEY` at all; only the NL question bar needs it.

## Development

```bash
pip install -r requirements-dev.txt
ruff check . --fix && ruff format .   # lint + format
ty check .                            # types
pytest                                # default suite — no API key needed, no real API calls
pytest -m integration                 # real Anthropic API calls, needs ANTHROPIC_API_KEY
```

## AI assistance

Scaffolding and iteration on this repo were assisted by Claude Code. Integration decisions, data-source wiring, and the demo were driven and verified by the team.
