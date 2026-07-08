from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.bot_engine import process_customer_message
from app.config import get_settings
from app.models import BotEngineResult, TestMessageRequest
from app.send_api import send_messenger_reply


app = FastAPI(title="MotoSulit Pricing Bot", version="1.0.0-beta")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/test-message", response_model=BotEngineResult)
def test_message(payload: TestMessageRequest) -> dict[str, Any]:
    return process_customer_message(payload.sender_id, payload.message_text)


@app.get("/webhook")
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> PlainTextResponse:
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return PlainTextResponse(hub_challenge or "")
    raise HTTPException(status_code=403, detail="Invalid verification token.")


def _extract_messenger_events(body: dict[str, Any]) -> list[tuple[str, str]]:
    events: list[tuple[str, str]] = []
    for entry in body.get("entry", []):
        for item in entry.get("messaging", []):
            sender_id = item.get("sender", {}).get("id")
            message_text = item.get("message", {}).get("text")
            if sender_id and message_text:
                events.append((sender_id, message_text))
    return events


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, str]:
    body = await request.json()
    for sender_id, message_text in _extract_messenger_events(body):
        result = process_customer_message(sender_id, message_text)
        if result["human_needed"]:
            continue
        if result["action"] in {
            "auto_reply",
            "ask_confirmation_or_clarification",
            "ask_clarification_or_human_handoff",
        }:
            send_messenger_reply(sender_id, result["reply_text"])
    return {"status": "ok"}
