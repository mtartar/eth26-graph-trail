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

- `fixture` (default) — reads `data/fixtures/sample_transfers.json`.
- `token_api` — real ERC-20 stablecoin transfers (USDC/USDT/PYUSD on Ethereum) from The Graph's Token API. Sign up at https://api.pinax.network for a key, then set `TOKEN_API_KEY` in `.env`.

If the live `token_api` integration breaks or rate-limits, set `DATA_SOURCE=fixture` and restart — that's the entire recovery procedure.

## NL query & summary

`POST /query` (question → filter → transfers) and `POST /summary` (transfers → short narrative) need `ANTHROPIC_API_KEY` in `.env`. See [docs/anthropic-api-key.md](docs/anthropic-api-key.md) for how to get one, set it, and verify it works.
