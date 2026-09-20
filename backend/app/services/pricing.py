def suggest_bundle_price(
    sell_a: float, cost_a: float,
    sell_b: float, cost_b: float,
    margin_floor_pct: float,
    target_discount_pct: float = 0.10,
) -> dict:
    separate_price = sell_a + sell_b
    separate_cost = cost_a + cost_b

    if margin_floor_pct >= 1.0:
        floor_price = separate_cost
    else:
        floor_price = separate_cost / (1 - margin_floor_pct)

    target_price = separate_price * (1 - target_discount_pct)
    suggested = floor_price if target_price < floor_price else target_price

    suggested = round(suggested / 5) * 5
    if suggested < floor_price:
        suggested = round((floor_price + 5) / 5) * 5

    margin_amount = suggested - separate_cost
    margin_pct = margin_amount / suggested if suggested else 0

    return {
        "separate_price": round(separate_price, 2),
        "separate_cost": round(separate_cost, 2),
        "suggested_price": suggested,
        "suggested_margin_pct": margin_pct,
        "floor_price": round(floor_price, 2),
    }