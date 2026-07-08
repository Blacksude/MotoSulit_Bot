from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings


RAW_FIELD_MAPPING = {
    "Motor Price List As of July 2026": "price_date",
    "Column2": "brand",
    "Column3": "model",
    "Column4": "cash",
    "Column5": "dp",
    "Column6": "months_12",
    "Column7": "months_18",
    "Column8": "months_24",
    "Column9": "months_30",
    "Column10": "months_36",
    "Column11": "income_rebate",
}

NUMERIC_FIELDS = {
    "cash",
    "dp",
    "months_12",
    "months_18",
    "months_24",
    "months_30",
    "months_36",
    "income_rebate",
}

NORMALIZED_SCHEMA = [
    "price_date",
    "brand",
    "model",
    "cash",
    "dp",
    "months_12",
    "months_18",
    "months_24",
    "months_30",
    "months_36",
    "income_rebate",
    "search_key",
]


def normalize_text(value: str) -> str:
    normalized = value.upper()
    normalized = re.sub(r"[^A-Z0-9]+", " ", normalized)
    normalized = re.sub(r"\b([A-Z]+)\s+(\d{2,3})\b", r"\1\2", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _parse_numeric(value: Any, field_name: str, row_number: int) -> int | float:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"Row {row_number}: {field_name} must be numeric.")

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value) if value.is_integer() else value

    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("PHP", "").replace("P", "")
        cleaned = cleaned.replace("₱", "").strip()
        if not cleaned:
            raise ValueError(f"Row {row_number}: {field_name} must be numeric.")
        try:
            parsed = Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(f"Row {row_number}: {field_name} must be numeric.") from exc
        if parsed == parsed.to_integral_value():
            return int(parsed)
        return float(parsed)

    raise ValueError(f"Row {row_number}: {field_name} must be numeric.")


def _normalize_record(raw_record: dict[str, Any], row_number: int) -> dict[str, Any]:
    missing = [raw_key for raw_key in RAW_FIELD_MAPPING if raw_key not in raw_record]
    if missing:
        raise ValueError(f"Row {row_number}: missing required fields: {', '.join(missing)}.")

    normalized: dict[str, Any] = {}
    for raw_key, normalized_key in RAW_FIELD_MAPPING.items():
        value = raw_record[raw_key]
        if normalized_key in NUMERIC_FIELDS:
            normalized[normalized_key] = _parse_numeric(value, normalized_key, row_number)
            continue

        text_value = str(value).strip() if value is not None else ""
        if not text_value:
            raise ValueError(f"Row {row_number}: {normalized_key} is required.")
        normalized[normalized_key] = text_value

    normalized["search_key"] = normalize_text(f"{normalized['brand']} {normalized['model']}")
    return {key: normalized[key] for key in NORMALIZED_SCHEMA}


@lru_cache(maxsize=8)
def _load_pricing_records_cached(path_text: str) -> tuple[tuple[tuple[str, Any], ...], ...]:
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Pricing JSON not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    raw_records = data.get("Motor Price List")
    if not isinstance(raw_records, list):
        raise ValueError("Pricing JSON must contain a 'Motor Price List' list.")
    if len(raw_records) < 2:
        raise ValueError("Pricing JSON must include a header row and at least one pricing record.")

    normalized_records = [
        _normalize_record(raw_record, row_number=index + 1)
        for index, raw_record in enumerate(raw_records[1:], start=1)
    ]
    return tuple(tuple(record.items()) for record in normalized_records)


def load_pricing_records() -> list[dict[str, Any]]:
    path = get_settings().pricing_json_path
    return [dict(record_items) for record_items in _load_pricing_records_cached(str(path))]


def get_all_models() -> list[str]:
    return [record["model"] for record in load_pricing_records()]


def get_models_by_brand(brand: str) -> list[str]:
    brand_key = normalize_text(brand)
    return [
        record["model"]
        for record in load_pricing_records()
        if normalize_text(record["brand"]) == brand_key
    ]


def search_pricing_records(query: str) -> list[dict[str, Any]]:
    query_key = normalize_text(query)
    if not query_key:
        return []

    query_tokens = set(query_key.split())
    matches: list[dict[str, Any]] = []
    for record in load_pricing_records():
        search_key = record["search_key"]
        search_tokens = set(search_key.split())
        if query_key in search_key or query_tokens.issubset(search_tokens):
            matches.append(record)
    return matches
