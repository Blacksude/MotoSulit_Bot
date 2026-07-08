from __future__ import annotations

from typing import Any

from app.pricing_loader import load_pricing_records, normalize_text


INQUIRY_STOP_WORDS = {
    "A",
    "AKO",
    "ANG",
    "ANO",
    "BA",
    "CASH",
    "DOWN",
    "DOWNPAYMENT",
    "DP",
    "FOR",
    "HM",
    "HOW",
    "HULOG",
    "INSTALLMENT",
    "KANO",
    "MAGKANO",
    "MAY",
    "MONTHLY",
    "MOS",
    "MOTOR",
    "MOTORCYCLE",
    "MUCH",
    "NG",
    "PO",
    "PRICE",
    "RATE",
    "RATES",
    "SA",
    "SIR",
    "THE",
    "YONG",
    "YUNG",
}


def _contains_phrase(text: str, phrase: str) -> bool:
    text_tokens = text.split()
    phrase_tokens = phrase.split()
    if not phrase_tokens or len(phrase_tokens) > len(text_tokens):
        return False
    return any(
        text_tokens[index : index + len(phrase_tokens)] == phrase_tokens
        for index in range(len(text_tokens) - len(phrase_tokens) + 1)
    )


def _contains_compact(text: str, phrase: str) -> bool:
    return phrase.replace(" ", "") in text.replace(" ", "")


def _model_exact_in_query(query_text: str, model_text: str) -> bool:
    return _contains_phrase(query_text, model_text) or _contains_compact(query_text, model_text)


def _summarize_candidates(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"brand": record["brand"], "model": record["model"]} for record in records[:8]]


def _record_meta(record: dict[str, Any]) -> dict[str, Any]:
    brand_key = normalize_text(record["brand"])
    model_key = normalize_text(record["model"])
    return {
        "record": record,
        "brand_key": brand_key,
        "model_key": model_key,
        "model_tokens": set(model_key.split()),
        "model_compact": model_key.replace(" ", ""),
    }


def _mentioned_brand_keys(query_key: str, metas: list[dict[str, Any]]) -> set[str]:
    brand_keys = {meta["brand_key"] for meta in metas}
    return {brand_key for brand_key in brand_keys if _contains_phrase(query_key, brand_key)}


def _meaningful_query_tokens(query_key: str, mentioned_brands: set[str]) -> list[str]:
    brand_tokens = {token for brand in mentioned_brands for token in brand.split()}
    return [
        token
        for token in query_key.split()
        if token not in INQUIRY_STOP_WORDS and token not in brand_tokens and len(token) > 1
    ]


def _token_matches_model(token: str, meta: dict[str, Any]) -> bool:
    if token in meta["model_tokens"]:
        return True
    if token == meta["model_compact"]:
        return True
    return any(model_token.startswith(token) for model_token in meta["model_tokens"])


def _base_result(
    *,
    confidence: int,
    match_type: str,
    matched_record: dict[str, Any] | None = None,
    matched_brand: str | None = None,
    matched_model: str | None = None,
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "confidence": confidence,
        "match_type": match_type,
        "matched_record": matched_record,
        "matched_brand": matched_brand,
        "matched_model": matched_model,
        "candidates": _summarize_candidates(candidates or []),
    }


def match_customer_message(message_text: str) -> dict[str, Any]:
    query_key = normalize_text(message_text)
    records = load_pricing_records()
    metas = [_record_meta(record) for record in records]

    if not query_key:
        return _base_result(confidence=20, match_type="no_match")

    mentioned_brands = _mentioned_brand_keys(query_key, metas)

    exact_brand_model_matches = [
        meta["record"]
        for meta in metas
        if meta["brand_key"] in mentioned_brands and _model_exact_in_query(query_key, meta["model_key"])
    ]
    if len(exact_brand_model_matches) == 1:
        record = exact_brand_model_matches[0]
        return _base_result(
            confidence=95,
            match_type="exact_brand_model",
            matched_record=record,
            matched_brand=record["brand"],
            matched_model=record["model"],
        )
    if len(exact_brand_model_matches) > 1:
        return _base_result(
            confidence=55,
            match_type="multiple_matches",
            candidates=exact_brand_model_matches,
        )

    exact_model_matches = [
        meta["record"] for meta in metas if _model_exact_in_query(query_key, meta["model_key"])
    ]
    if len(exact_model_matches) == 1:
        record = exact_model_matches[0]
        if mentioned_brands and normalize_text(record["brand"]) not in mentioned_brands:
            return _base_result(confidence=20, match_type="no_match")
        return _base_result(
            confidence=90,
            match_type="exact_model",
            matched_record=record,
            matched_brand=record["brand"],
            matched_model=record["model"],
        )
    if len(exact_model_matches) > 1:
        return _base_result(
            confidence=55,
            match_type="multiple_matches",
            candidates=exact_model_matches,
        )

    query_tokens = _meaningful_query_tokens(query_key, mentioned_brands)
    if mentioned_brands and not query_tokens:
        brand_key = sorted(mentioned_brands)[0]
        brand_records = [meta["record"] for meta in metas if meta["brand_key"] == brand_key]
        brand_name = brand_records[0]["brand"] if brand_records else None
        return _base_result(
            confidence=40,
            match_type="brand_only",
            matched_brand=brand_name,
            candidates=brand_records,
        )

    token_match_metas = metas
    if mentioned_brands:
        token_match_metas = [meta for meta in metas if meta["brand_key"] in mentioned_brands]

    token_matches = [
        meta["record"]
        for meta in token_match_metas
        if query_tokens and all(_token_matches_model(token, meta) for token in query_tokens)
    ]
    if len(token_matches) == 1:
        record = token_matches[0]
        return _base_result(
            confidence=80,
            match_type="model_token",
            matched_record=record,
            matched_brand=record["brand"],
            matched_model=record["model"],
            candidates=token_matches,
        )
    if len(token_matches) > 1:
        return _base_result(
            confidence=55,
            match_type="multiple_matches",
            candidates=token_matches,
        )

    if mentioned_brands:
        return _base_result(confidence=20, match_type="no_match")

    return _base_result(confidence=20, match_type="no_match")
