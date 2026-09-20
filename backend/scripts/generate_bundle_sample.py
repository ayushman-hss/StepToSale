import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

# ----------------------------------------------------------------------
# 1. Load the curated BigBasket catalog produced by prepare_catalogue.py
# ----------------------------------------------------------------------
catalog = pd.read_csv("curated_catalog.csv")
sku_to_price = dict(zip(catalog["sku"], catalog["sell_price"]))

print(f"Loaded {len(catalog)} products from curated_catalog.csv")
print(f"Categories: {sorted(catalog['category'].unique().tolist())}")

# ----------------------------------------------------------------------
# 2. Pairing rules, resolved per store
#    A store can only sell what its own catalogue stocks, so pools are
#    built from product_catalog_<store>.xlsx rather than the global list.
# ----------------------------------------------------------------------
RAW_RULES = [
    ("Snacks & Branded Foods",   "Beverages",                 0.25),  # chips + cold drink
    ("Snacks & Branded Foods",   "Bakery, Cakes & Dairy",     0.20),  # biscuits + milk
    ("Bakery, Cakes & Dairy",    "Beverages",                 0.15),  # bread + tea
    ("Foodgrains, Oil & Masala", "Cleaning & Household",      0.10),  # monthly restock
    ("Snacks & Branded Foods",   "Snacks & Branded Foods",    0.15),  # party shopping
    ("Beauty & Hygiene",         "Beauty & Hygiene",          0.10),  # personal care
    ("Foodgrains, Oil & Masala", "Foodgrains, Oil & Masala",  0.05),  # oil + masala
]


def build_rules(store_catalog):
    """Resolve the category rules against one store's catalogue."""
    def pool(name):
        return store_catalog[store_catalog["category"] == name]["sku"].tolist()

    rules = []
    for cat_a, cat_b, weight in RAW_RULES:
        a, b = pool(cat_a), pool(cat_b)
        if a and b:
            rules.append((a, b, weight))
        else:
            print(f"  skipping rule {cat_a} + {cat_b} (not stocked)")
    if not rules:
        raise SystemExit("No valid pairing rules for this store's catalogue")
    total = sum(w for _, _, w in rules)
    return [(a, b, w / total) for a, b, w in rules]


def pick_pair(rules):
    """Return (sku_a, sku_b) from a weighted pairing rule."""
    r = random.random()
    cumulative = 0.0
    chosen = rules[-1]
    for a_pool, b_pool, weight in rules:
        cumulative += weight
        if r <= cumulative:
            chosen = (a_pool, b_pool, weight)
            break
    a_pool, b_pool, _ = chosen
    sku_a = random.choice(a_pool)
    sku_b = random.choice(b_pool)
    attempts = 0
    while sku_b == sku_a and attempts < 10:
        sku_b = random.choice(b_pool)
        attempts += 1
    return sku_a, sku_b

# ----------------------------------------------------------------------
# 4. Store profiles — S1 neighbourhood kirana, S2 station kiosk
# ----------------------------------------------------------------------
STORES = {
    # A residential kirana: steady all day, busiest mid-morning and after
    # work, and busier still at the weekend when people do a bigger shop.
    "S1": {
        "tx_per_day": 45,
        "pairing_bias": 0.55,
        "open_hours": list(range(8, 22)),
        "peak_hours": [9, 10, 11, 18, 19, 20],
        # Mon..Sun
        "day_factor": [1.00, 0.88, 0.98, 1.05, 1.15, 1.40, 1.30],
    },
    # A kiosk by the station: commuter rushes either side of the working
    # day, and it empties out at the weekend when nobody is commuting.
    "S2": {
        "tx_per_day": 70,
        "pairing_bias": 0.40,
        "open_hours": list(range(6, 23)),
        "peak_hours": [7, 8, 9, 18, 19, 20, 21],
        "day_factor": [1.22, 1.20, 1.15, 1.20, 1.28, 0.58, 0.42],
    },
}


def pick_hour(profile) -> int:
    """Trade happens all day; peaks are weighted, not exclusive."""
    hours = profile["open_hours"]
    weights = [3.2 if h in profile["peak_hours"] else 1.0 for h in hours]
    return random.choices(hours, weights=weights, k=1)[0]


# ----------------------------------------------------------------------
# 5. Generate sale lines per store
# ----------------------------------------------------------------------
for store_code, profile in STORES.items():
    store_catalog = pd.read_excel(f"product_catalog_{store_code}.xlsx")
    store_skus = store_catalog["sku"].tolist()
    price_of = dict(zip(store_catalog["sku"], store_catalog["sell_price"]))
    print(f"{store_code}: {len(store_skus)} SKUs stocked")
    rules = build_rules(store_catalog)

    rows = []
    start = datetime(2024, 5, 1)
    tx_id = 1

    for day in range(7):
        current = start + timedelta(days=day)
        date = current.strftime("%Y-%m-%d")
        factor = profile["day_factor"][current.weekday()]
        tx_today = max(1, round(profile["tx_per_day"] * factor * random.uniform(0.9, 1.1)))
        for _ in range(tx_today):
            hour = pick_hour(profile)

            if random.random() < profile["pairing_bias"]:
                sku_a, sku_b = pick_pair(rules)
                basket = [sku_a, sku_b]
            else:
                basket = [random.choice(store_skus)]

            for sku in basket:
                rows.append({
                    "date": date,
                    "hour": hour,
                    "transaction_id": f"{store_code}_T{tx_id:05d}",
                    "sku": sku,
                    "qty": 1,
                    "unit_price": price_of[sku],
                })
            tx_id += 1

    df = pd.DataFrame(rows)
    unknown = set(df["sku"]) - set(store_skus)
    assert not unknown, f"{store_code} sold SKUs it does not stock: {unknown}"
    out = f"sales_lines_{store_code}.xlsx"
    df.to_excel(out, index=False)
    print(f"  wrote {out} ({len(df)} lines, {tx_id - 1} transactions, "
          f"{df['sku'].nunique()}/{len(store_skus)} SKUs sold)")

print("")
print("Now upload in the UI:")
print("  Products page -> S1 -> product_catalog_S1.xlsx")
print("  Products page -> S2 -> product_catalog_S2.xlsx")
print("  Bundles page  -> S1 -> sales_lines_S1.xlsx")
print("  Bundles page  -> S2 -> sales_lines_S2.xlsx")
