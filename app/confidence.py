from __future__ import annotations

from typing import Any

from app.pricing_loader import NUMERIC_FIELDS, normalize_text


RISKY_TERMS = [
    "reklamo",
    "complaint",
    "galit",
    "scam",
    "refund",
    "cancel",
    "legal",
    "lawyer",
    "manager",
    "wrong price",
    "mali presyo",
    "downpayment issue",
    "payment issue",
    "branch issue",
    "agent issue",
]

REQUIRED_RECORD_FIELDS = {
    "price_date",
    "brand",
    "model",
    "search_key",
    *NUMERIC_FIELDS,
}


def contains_risky_terms(message_text: str) -> bool:
    message_key = normalize_text(message_text)
    return any(normalize_text(term) in message_key for term in RISKY_TERMS)


def has_missing_required_pricing_field(record: dict[str, Any] | None) -> bool:
    if record is None:
        return False
    for field_name in REQUIRED_RECORD_FIELDS:
        value = record.get(field_name)
        if value is None or value == "":
            return True
    return False


def decide_action(
    *,
    confidence: int,
    message_text: str,
    matched_record: dict[str, Any] | None,
) -> dict[str, Any]:
    if contains_risky_terms(message_text):
        return {"action": "human_handoff", "human_needed": True}

    if has_missing_required_pricing_field(matched_record):
        return {"action": "human_handoff", "human_needed": True}

    if confidence >= 90:
        return {"action": "auto_reply", "human_needed": False}

    if confidence >= 70:
        return {"action": "ask_confirmation_or_clarification", "human_needed": False}

    return {"action": "ask_clarification_or_human_handoff", "human_needed": False}
