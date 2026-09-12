# Setting up ANTHROPIC_API_KEY

Needed for the `/query` (NL question → filter) and `/summary` (narrative) endpoints, implemented in `backend/services/nl_to_filter.py` and `backend/services/narrative.py`. Without it, those two endpoints return a `RuntimeError` from `get_anthropic_client()` — everything else (`/transfers`, `/health`) works fine without this key.

## 1. Get a key

1. Go to the [Anthropic Console](https://console.anthropic.com/settings/keys) and sign in (or create an account).
2. If this is a new account, add a payment method under **Billing** — the API is pay-as-you-go and won't run without it, though new accounts sometimes start with a small free credit grant.
3. Click **Create Key**, name it (e.g. `graph-trail-hackathon`), and copy it immediately — the full value is only shown once.
4. The key looks like `sk-ant-api03-...`.

## 2. Set it locally

In the repo root:

```bash
cp .env.example .env   # if you haven't already
```

Open `.env` and set:

```
ANTHROPIC_API_KEY=sk-ant-api03-...your-key...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

`.env` is already in `.gitignore` — it will not be committed. Never paste the key directly into code, a commit message, or the demo video.

## 3. Verify it works

Run the integration test suite — it hits the real API (unlike the default `pytest` run, which mocks the Anthropic client and needs no key):

```bash
pytest -v -m integration
```

`backend/tests/test_nl_layer_integration.py` covers token/amount/time-window extraction, the narrative summary, and both `/query` and `/summary` end to end against real fixture data. These are excluded from the default `pytest` run (see `[tool.pytest.ini_options]` in `pyproject.toml`) so the normal suite stays free and key-independent.

Alternatively, with the server running (`uvicorn backend.main:app --reload --port 8010`), hit `/query` from `/docs` or curl:

```bash
curl -s -X POST http://127.0.0.1:8010/query \
  -H "Content-Type: application/json" \
  -d '{"question": "USDC transfers over $1M last week"}' | python3 -m json.tool
```

A working key returns a `resolved_filter` and matching `result.transfers`. A missing/invalid key returns a 500 with the `RuntimeError` message from `llm_client.py`, or an Anthropic `authentication_error` if the key itself is malformed/revoked.

## Cost note

Both endpoints use `claude-haiku-4-5-20251001` by default — cheap and fast, appropriate for the narrow extraction/summary tasks here (see the model-choice rationale in the main conversation / `01_architecture.md`). Testing repeatedly against `/query` and `/summary` during development will use real API credit, just at a small fraction of a cent per call.

## If the key stops working mid-demo

This isn't behind the same `fixture` fallback as `DATA_SOURCE` — if `ANTHROPIC_API_KEY` is invalid, rate-limited, or out of credit, `/query` and `/summary` will fail outright. There's no automatic fallback for the NL layer today; if this is a risk for the live demo, pre-record the `/query` → `/summary` portion or have a backup key ready.
