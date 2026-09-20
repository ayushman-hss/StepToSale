import pandas as pd
from typing import List
from sqlmodel import Session, select
from .associations import find_co_purchase_pairs
from .pricing import suggest_bundle_price
from ..models import Product, BundleSuggestion


def generate_suggestions(
    session: Session,
    store_id: int,
    lines: pd.DataFrame,
    margin_floor_pct: float,
    min_support_tx: int | None = None,
    min_lift: float = 1.3,
    stats: dict | None = None,
) -> List[BundleSuggestion]:
    products = {
        p.sku: p
        for p in session.exec(select(Product).where(Product.store_id == store_id)).all()
    }

    pairs = find_co_purchase_pairs(lines, min_support_tx=min_support_tx, min_lift=min_lift)
    suggestions = []
    dropped_missing_product = 0
    dropped_no_discount = 0

    for pair in pairs:
        a = products.get(pair["sku_a"])
        b = products.get(pair["sku_b"])
        if not a or not b:
            dropped_missing_product += 1
            continue

        pricing = suggest_bundle_price(
            sell_a=a.sell_price, cost_a=a.cost_price,
            sell_b=b.sell_price, cost_b=b.cost_price,
            margin_floor_pct=margin_floor_pct,
        )
        if pricing["suggested_price"] >= pricing["separate_price"]:
            dropped_no_discount += 1
            continue

        s = BundleSuggestion(
            store_id=store_id,
            sku_a=pair["sku_a"], sku_b=pair["sku_b"],
            transactions_with_both=pair["both"],
            transactions_with_a=pair["count_a"],
            transactions_with_b=pair["count_b"],
            total_transactions=pair["total_tx"],
            confidence=pair["confidence"], lift=pair["lift"],
            separate_price=pricing["separate_price"],
            separate_cost=pricing["separate_cost"],
            suggested_price=pricing["suggested_price"],
            suggested_margin_pct=pricing["suggested_margin_pct"],
            margin_floor_pct=margin_floor_pct,
        )
        session.add(s)
        suggestions.append(s)

    session.commit()
    if stats is not None:
        stats["candidate_pairs"] = len(pairs)
        stats["dropped_missing_product"] = dropped_missing_product
        stats["dropped_no_discount"] = dropped_no_discount
    return suggestions