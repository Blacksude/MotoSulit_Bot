from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    meta_verify_token: str
    meta_page_access_token: str
    send_enabled: bool
    pricing_json_path: Path
    sqlite_path: Path


def get_settings() -> Settings:
    return Settings(
        meta_verify_token=os.getenv("META_VERIFY_TOKEN", ""),
        meta_page_access_token=os.getenv("META_PAGE_ACCESS_TOKEN", ""),
        send_enabled=_env_bool("SEND_ENABLED", "false"),
        pricing_json_path=_resolve_path(os.getenv("PRICING_JSON_PATH", "data/pricing_raw.json")),
        sqlite_path=_resolve_path(os.getenv("SQLITE_PATH", "storage/motosulit.sqlite")),
    )
