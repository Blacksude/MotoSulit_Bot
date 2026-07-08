from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TestMessageRequest(BaseModel):
    sender_id: str = Field(default="test-user", min_length=1)
    message_text: str = Field(min_length=1)


class BotEngineResult(BaseModel):
    sender_id: str
    customer_message: str
    intent: str
    matched_brand: str | None
    matched_model: str | None
    confidence: int
    action: str
    reply_text: str
    human_needed: bool
    matched_record: dict[str, Any] | None
