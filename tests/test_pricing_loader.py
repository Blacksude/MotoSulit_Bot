from app.pricing_loader import get_models_by_brand, load_pricing_records


def test_pricing_loader_loads_51_records() -> None:
    records = load_pricing_records()

    assert len(records) == 51
    assert all(set(record) == {
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
    } for record in records)


def test_pricing_loader_maps_honda_click125_standard_correctly() -> None:
    records = load_pricing_records()
    record = next(item for item in records if item["brand"] == "Honda" and item["model"] == "CLICK125 Standard")

    assert record["price_date"] == "2026-07-01"
    assert record["cash"] == 86750
    assert record["dp"] == 8600
    assert record["months_12"] == 8818
    assert record["months_18"] == 6648
    assert record["months_24"] == 5562
    assert record["months_30"] == 4911
    assert record["months_36"] == 4477
    assert record["income_rebate"] == 200
    assert record["search_key"] == "HONDA CLICK125 STANDARD"


def test_get_models_by_brand_is_deterministic() -> None:
    honda_models = get_models_by_brand("honda")

    assert "CLICK125 Standard" in honda_models
    assert "AEROX155 (STD)" not in honda_models
