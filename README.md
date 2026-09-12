# Graph Trail, ETHOnline 2026 (The Graph tracks)

A ledger of large stablecoin transfers where every number traces back to its onchain source.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload --port 8010
```

Port 8010 avoids the default 8000, which is often already bound by other local services (e.g. an unrelated Kong gateway on this machine) — pick any free port if 8010 is also taken.

Open `http://127.0.0.1:8010/docs` and try `GET /transfers` (optionally with `token`, `chain`, `min_amount_usd`, `since`, `until` query params).
