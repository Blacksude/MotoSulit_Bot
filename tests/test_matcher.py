from app.matcher import match_customer_message


def test_matcher_exact_brand_and_model_match() -> None:
    result = match_customer_message("hm honda click 125 standard")

    assert result["confidence"] == 95
    assert result["match_type"] == "exact_brand_model"
    assert result["matched_brand"] == "Honda"
    assert result["matched_model"] == "CLICK125 Standard"


def test_matcher_exact_model_only_match() -> None:
    result = match_customer_message("hm click125 standard")

    assert result["confidence"] == 90
    assert result["match_type"] == "exact_model"
    assert result["matched_brand"] == "Honda"
    assert result["matched_model"] == "CLICK125 Standard"


def test_matcher_vague_model_returns_multiple_matches() -> None:
    result = match_customer_message("hm click")

    assert result["confidence"] == 55
    assert result["match_type"] == "multiple_matches"
    assert {candidate["model"] for candidate in result["candidates"]} >= {
        "CLICK125 Smart Edition",
        "CLICK125 Standard",
        "CLICK160",
    }
