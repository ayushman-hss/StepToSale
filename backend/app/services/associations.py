import pandas as pd
from typing import List, Dict
from collections import defaultdict


def default_min_support(total_tx: int) -> int:
    # A flat floor silently wipes out every pair in a small or wide-catalogue
    # dataset: a few hundred baskets spread over ~50 SKUs tops out around 4
    # co-purchases per pair. Scale with basket count but never drop below 3
    # (two co-purchases is noise, not a pattern).
    return max(3, round(total_tx * 0.005))


def find_co_purchase_pairs(
    lines: pd.DataFrame,
    min_support_tx: int | None = None,
    min_lift: float = 1.3,
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
        min_support_tx = default_min_support(total_tx)

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
