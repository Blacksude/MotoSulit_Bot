from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import get_settings


CREATE_MESSAGE_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS message_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    sender_id TEXT,
    customer_message TEXT,
    intent TEXT,
    matched_brand TEXT,
    matched_model TEXT,
    confidence INTEGER,
    action TEXT,
    reply_text TEXT,
    human_needed INTEGER,
    sent_status TEXT,
    error_message TEXT
)
"""


def get_db_path() -> Path:
    return get_settings().sqlite_path


def init_db() -> None:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(CREATE_MESSAGE_LOGS_TABLE)
        connection.commit()


def log_message(
    result: dict[str, Any],
    *,
    sent_status: str = "processed",
    error_message: str | None = None,
) -> int:
    init_db()
    created_at = datetime.now(UTC).isoformat()
    with sqlite3.connect(get_db_path()) as connection:
        cursor = connection.execute(
            """
            INSERT INTO message_logs (
                created_at,
                sender_id,
                customer_message,
                intent,
                matched_brand,
                matched_model,
                confidence,
                action,
                reply_text,
                human_needed,
                sent_status,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                result.get("sender_id"),
                result.get("customer_message"),
                result.get("intent"),
                result.get("matched_brand"),
                result.get("matched_model"),
                result.get("confidence"),
                result.get("action"),
                result.get("reply_text"),
                1 if result.get("human_needed") else 0,
                sent_status,
                error_message,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
