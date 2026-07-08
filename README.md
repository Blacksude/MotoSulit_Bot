# MotoSulit Messenger Pricing Bot

Production-ready beta v1 backend for a deterministic Facebook Page Messenger motorcycle pricing bot.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` or export the same variables in your shell.
4. Keep the uploaded pricing file at `data/pricing_raw.json`.

## Run Locally

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Test a Message

POST to `/test-message`:

```bash
curl -X POST http://127.0.0.1:8000/test-message \
  -H "Content-Type: application/json" \
  -d "{\"sender_id\":\"test-user\",\"message_text\":\"hm honda click 125 standard\"}"
```

The response includes the matched record, confidence, action, reply text, and whether a human handoff is needed.

## Environment Variables

```bash
META_VERIFY_TOKEN=
META_PAGE_ACCESS_TOKEN=
SEND_ENABLED=false
PRICING_JSON_PATH=data/pricing_raw.json
SQLITE_PATH=storage/motosulit.sqlite
```

`SEND_ENABLED=false` keeps Messenger sends disabled for local testing. In that mode, `send_messenger_reply` returns a mock success response and does not call Meta.

## Webhook

Meta verification uses:

```text
GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
```

The verify token must match `META_VERIFY_TOKEN`.

Messenger events are received at:

```text
POST /webhook
```

The app extracts sender ID and message text, runs the deterministic bot engine, and sends a reply only when no human handoff is required.

## Tests

```bash
pytest
```

The test suite covers pricing loading, matching, clarification behavior, human handoff, and the rule that unknown models must not receive invented prices.

## Safety Rules

- The bot never invents motorcycle prices, DP, monthly values, or rebates.
- Pricing comes only from `data/pricing_raw.json`.
- Matching is deterministic and does not use AI or external APIs.
- Vague or multiple matches ask for clarification.
- Risky messages such as complaints, refund issues, legal concerns, or wrong-price reports trigger human handoff.
- Money values are formatted as Philippine peso with comma separators.
- All processed messages are logged to SQLite at `storage/motosulit.sqlite`.
