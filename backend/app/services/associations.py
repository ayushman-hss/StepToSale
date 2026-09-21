import pandas as pd
from typing import List, Dict
from collections import defaultdict


#: Bought together at least twice as often as chance. With realistic basket
#: sizes (a kirana bill averages 2-3 items) two popular products share a bill
#: often by coincidence; 1.3 let dozens of those through as "bundles".
DEFAULT_MIN_LIFT = 2.0


def multi_item_baskets(lines: pd.DataFrame, key: str | None = None) -> int:
    """Bills with two or more distinct products -- the only ones that can
    contain a pair. Support is judged against these, not all bills, so a
    shop whose customers mostly buy one thing is not held to a stricter bar
    for the pairs it does have."""
    key = key or ("basket_id" if "basket_id" in lines.columns else "transaction_id")
    return int((lines.groupby(key)["sku"].nunique() >= 2).sum())


def default_min_support(total_tx: int) -> int:
    # A flat floor silently wipes out every pair in a small or wide-catalogue
    # dataset: a few hundred baskets spread over ~50 SKUs tops out around 4
    # co-purchases per pair. Scale with basket count but never drop below 3
    # (two co-purchases is noise, not a pattern).
    return max(3, round(total_tx * 0.005))


def find_co_purchase_pairs(
    lines: pd.DataFrame,
    min_support_tx: int | None = None,
    min_lift: float = DEFAULT_MIN_LIFT,
) -> List[Dict]:
    # transaction_id is only unique *within* one upload -- exports normally
    # restart numbering at T00001 -- so grouping on it alone silently merges
    # baskets from different uploads. Callers pass basket_id to avoid that.
    key = "basket_id" if "basket_id" in lines.columns else "transaction_id"

    baskets = lines.groupby(key)["sku"].apply(set).to_dict()
    total_tx = len(baskets)
    if total_tx == 0:
        return []

    if min_support_tx is None:
        min_support_tx = default_min_support(multi_item_baskets(lines, key))

    sku_tx_count = defaultdict(int)
    for basket in baskets.values():
        for sku in basket:
            sku_tx_count[sku] += 1

    pair_count = defaultdict(int)
    for basket in baskets.values():
        skus = sorted(basket)
        for i in range(len(skus)):
            for j in range(i + 1, len(skus)):
                pair_count[(skus[i], skus[j])] += 1

    results = []
    for (a, b), both in pair_count.items():
        if both < min_support_tx:
            continue
        if sku_tx_count[a] >= sku_tx_count[b]:
            antecedent, consequent = a, b
        else:
            antecedent, consequent = b, a

        confidence = both / sku_tx_count[antecedent]
        p_consequent = sku_tx_count[consequent] / total_tx
        lift = confidence / p_consequent if p_consequent else 0
        if lift < min_lift:
            continue

        results.append({
            "sku_a": a, "sku_b": b,
            "both": both,
            "count_a": sku_tx_count[a], "count_b": sku_tx_count[b],
            "total_tx": total_tx,
            "confidence": confidence, "lift": lift,
        })

    return sorted(results, key=lambda r: -r["lift"])
