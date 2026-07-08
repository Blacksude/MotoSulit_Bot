from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from app.config import get_settings


logger = logging.getLogger(__name__)


def send_messenger_reply(recipient_id: str, message_text: str) -> dict[str, object]:
    settings = get_settings()
    if not settings.send_enabled:
        logger.info("SEND_ENABLED is not true; Messenger reply was not actually sent.")
        return {
            "ok": True,
            "mock": True,
            "sent": False,
            "reason": "SEND_ENABLED is not true; message was not actually sent.",
        }

    if not settings.meta_page_access_token:
        return {
            "ok": False,
            "mock": False,
            "sent": False,
            "error": "META_PAGE_ACCESS_TOKEN is required when SEND_ENABLED=true.",
        }

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
    }
    request = urllib.request.Request(
        f"https://graph.facebook.com/v20.0/me/messages?access_token={settings.meta_page_access_token}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        return {"ok": False, "mock": False, "sent": False, "error": str(exc)}

    return {"ok": True, "mock": False, "sent": True, "response": response_body}
