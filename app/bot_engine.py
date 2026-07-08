from __future__ import annotations

from typing import Any

from app.confidence import contains_risky_terms, decide_action
from app.logger import log_message
from app.matcher import INQUIRY_STOP_WORDS, match_customer_message
from app.pricing_loader import get_all_models, load_pricing_records, normalize_text
from app.reply_templates import (
    build_price_context,
    format_candidate_list,
    render_template,
)


PRICING_TERMS = {
    "CASH",
    "DOWN",
    "DP",
    "HM",
    "HOW",
    "HULOG",
    "INSTALLMENT",
    "MAGKANO",
    "MONTHLY",
    "MOTOR",
    "MOTORCYCLE",
    "MUCH",
    "PRICE",
}


def _known_vehicle_terms() -> set[str]:
    terms = set()
    for record in load_pricing_records():
        terms.update(normalize_text(record["brand"]).split())
        terms.update(normalize_text(record["model"]).split())
    return terms


def _detect_intent(message_text: str) -> str:
    if contains_risky_terms(message_text):
        return "human_handoff"

    message_tokens = set(normalize_text(message_text).split())
    if message_tokens & PRICING_TERMS:
        return "pricing_inquiry"

    model_or_brand_terms = _known_vehicle_terms() - INQUIRY_STOP_WORDS
    if message_tokens & model_or_brand_terms:
        return "pricing_inquiry"

    return "unknown"


def _build_reply(match_result: dict[str, Any], action: str) -> str:
    matched_record = match_result.get("matched_record")
    match_type = match_result.get("match_type")
    candidates = match_result.get("candidates") or []

    if action == "human_handoff":
        return render_template("human_handoff")

    if action == "auto_reply" and matched_record:
        return render_template("price_exact_match", build_price_context(matched_record))

    if match_type == "brand_only":
        return render_template(
            "ask_exact_model",
            {
                "brand": match_result.get("matched_brand") or "brand",
                "matches": format_candidate_list(candidates),
            },
        )

    if match_type == "multiple_matches":
        return render_template(
            "multiple_matches",
            {"matches": format_candidate_list(candidates)},
        )

    if action == "ask_confirmation_or_clarification" and matched_record:
        return render_template(
            "ask_exact_model",
            {
                "brand": matched_record["brand"],
                "matches": f"{matched_record['brand']} {matched_record['model']}",
            },
        )

    return render_template("no_match")


def _result_payload(
    *,
    sender_id: str,
    message_text: str,
    intent: str,
    match_result: dict[str, Any],
    action: str,
    human_needed: bool,
    reply_text: str,
) -> dict[str, Any]:
    return {
        "sender_id": sender_id,
        "customer_message": message_text,
        "intent": intent,
        "matched_brand": match_result.get("matched_brand"),
        "matched_model": match_result.get("matched_model"),
        "confidence": int(match_result.get("confidence", 0)),
        "action": action,
        "reply_text": reply_text,
        "human_needed": human_needed,
        "matched_record": match_result.get("matched_record"),
    }


def process_customer_message(sender_id: str, message_text: str) -> dict[str, Any]:
    try:
        intent = _detect_intent(message_text)
        match_result = match_customer_message(message_text)
        if intent == "unknown" and match_result["confidence"] >= 40:
            intent = "pricing_inquiry"
        decision = decide_action(
            confidence=match_result["confidence"],
            message_text=message_text,
            matched_record=match_result.get("matched_record"),
        )

        if decision["action"] == "human_handoff":
            intent = "human_handoff"

        reply_text = _build_reply(match_result, decision["action"])
        result = _result_payload(
            sender_id=sender_id,
            message_text=message_text,
            intent=intent,
            match_result=match_result,
            action=decision["action"],
            human_needed=decision["human_needed"],
            reply_text=reply_text,
        )
        log_message(result)
        return result
    except Exception as exc:  # pragma: no cover - exercised only on unexpected runtime failures.
        fallback_match = {
            "confidence": 0,
            "matched_brand": None,
            "matched_model": None,
            "matched_record": None,
        }
        result = _result_payload(
            sender_id=sender_id,
            message_text=message_text,
            intent="unknown",
            match_result=fallback_match,
            action="human_handoff",
            human_needed=True,
            reply_text=render_template("error_fallback"),
        )
        log_message(result, sent_status="error", error_message=str(exc))
        return result
