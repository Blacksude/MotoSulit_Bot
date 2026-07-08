from app.bot_engine import process_customer_message


def test_bot_engine_never_invents_price_for_unknown_model() -> None:
    result = process_customer_message("test-user", "hm honda unicorn 999")

    assert result["matched_record"] is None
    assert result["confidence"] == 20
    assert "₱" not in result["reply_text"]
    assert "exact brand at model" in result["reply_text"]


def test_bot_engine_asks_clarification_for_multiple_matches() -> None:
    result = process_customer_message("test-user", "hm click")

    assert result["matched_record"] is None
    assert result["confidence"] == 55
    assert result["action"] == "ask_clarification_or_human_handoff"
    assert "CLICK125 Standard" in result["reply_text"]
    assert "₱" not in result["reply_text"]


def test_bot_engine_triggers_human_handoff_for_complaint_messages() -> None:
    result = process_customer_message("test-user", "complaint wrong price honda click 125 standard")

    assert result["intent"] == "human_handoff"
    assert result["action"] == "human_handoff"
    assert result["human_needed"] is True
    assert "₱" not in result["reply_text"]


def test_bot_engine_exact_match_uses_uploaded_price_only() -> None:
    result = process_customer_message("test-user", "hm honda click 125 standard")

    assert result["confidence"] == 95
    assert result["action"] == "auto_reply"
    assert result["matched_record"]["cash"] == 86750
    assert "₱86,750" in result["reply_text"]
    assert "₱8,600" in result["reply_text"]
