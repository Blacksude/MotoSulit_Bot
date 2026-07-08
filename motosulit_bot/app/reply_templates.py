from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import BASE_DIR


TEMPLATES_PATH = BASE_DIR / "data" / "approved_replies.json"
REQUIREMENTS_TEXT = "2 valid ID and 1 month proof of income"


def format_money(value: int | float) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"₱{value:,.2f}"
    return f"₱{int(value):,}"


def load_templates() -> dict[str, str]:
    with Path(TEMPLATES_PATH).open("r", encoding="utf-8") as file:
        templates = json.load(file)
    if not isinstance(templates, dict):
        raise ValueError("approved_replies.json must contain a JSON object.")
    return templates


def render_template(template_key: str, context: dict[str, Any] | None = None) -> str:
    templates = load_templates()
    if template_key not in templates:
        raise KeyError(f"Unknown approved reply template: {template_key}")
    return templates[template_key].format(**(context or {}))


def build_price_context(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "price_date": record["price_date"],
        "brand": record["brand"],
        "model": record["model"],
        "cash": format_money(record["cash"]),
        "dp": format_money(record["dp"]),
        "months_12": format_money(record["months_12"]),
        "months_18": format_money(record["months_18"]),
        "months_24": format_money(record["months_24"]),
        "months_30": format_money(record["months_30"]),
        "months_36": format_money(record["months_36"]),
        "income_rebate": format_money(record["income_rebate"]),
        "requirements": REQUIREMENTS_TEXT,
    }


def format_candidate_list(candidates: list[dict[str, str]]) -> str:
    if not candidates:
        return "Walang exact match"
    return "; ".join(f"{candidate['brand']} {candidate['model']}" for candidate in candidates)
