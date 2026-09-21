"""Generate per-store sale lines (one row per item on a bill).

The history always ends *now*: twelve full weeks up to yesterday, plus today
up to the current hour in India Standard Time. Run it before a demo and the
dashboard's "today" is actually today.

Patterns layered onto every bill, each one a known feature of Indian
neighbourhood retail rather than noise:

* time of day   -- trade all day, heavier at each shop's own peaks
* day of week   -- the kirana fills up at the weekend, the station kiosk
                   empties out when nobody commutes
* month cycle   -- the first days after salaries land bring a monthly
                   stock-up at the kirana: more bills and more rice and oil
                   bought two at a time
* day to day    -- no two days are alike even with the same weekday
* affinities    -- a few specific products are bought together far more
                   than chance (this biscuit with that tea), with a long
                   tail of weak pairings behind them. That skew is what
                   real basket data looks like, and what bundling relies on.

Deliberately NOT modelled here yet: weather and festivals (planned as their
own step, from real Open-Meteo history and the official holiday list).

    cd backend && python scripts/generate_bundle_sample.py
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]

# India has one time zone and no daylight saving, so a fixed offset is exact
# and avoids depending on the OS time zone database (absent on Windows).
IST = timezone(timedelta(hours=5, minutes=30))
WEEKS = 12

# Share of two-item bills that are one of the shop's signature pairings; the
# rest are random pairs within the category rules.
SIGNATURE_SHARE = 0.25
SIGNATURE_PAIRS = 6

# Categories a household buys in bulk at month start.
STAPLES = {"Foodgrains, Oil & Masala", "Cleaning & Household"}

RAW_RULES = [
    ("Snacks & Branded Foods",   "Beverages",                 0.25),  # chips + cold drink
    ("Snacks & Branded Foods",   "Bakery, Cakes & Dairy",     0.20),  # biscuits + milk
    ("Bakery, Cakes & Dairy",    "Beverages",                 0.15),  # bread + tea
    ("Foodgrains, Oil & Masala", "Cleaning & Household",      0.10),  # monthly restock
    ("Snacks & Branded Foods",   "Snacks & Branded Foods",    0.15),  # party shopping
    ("Beauty & Hygiene",         "Beauty & Hygiene",          0.10),  # personal care
    ("Foodgrains, Oil & Masala", "Foodgrains, Oil & Masala",  0.05),  # oil + masala
]

STORES = {
    # A residential kirana: steady all day, busiest mid-morning and after
    # work, busier at the weekend, and strongly tied to the salary cycle.
    "S1": {
        "tx_per_day": 45,
        "pairing_bias": 0.55,
        "open_hours": list(range(8, 22)),
        "peak_hours": [9, 10, 11, 18, 19, 20],
        "day_factor": [1.00, 0.88, 0.98, 1.05, 1.15, 1.40, 1.30],  # Mon..Sun
        "salary_effect": True,
    },
    # A kiosk by the station: commuter rushes either side of the working
    # day, near-empty at the weekend. People buy singles on the way past,
    # so the month cycle barely touches it.
    "S2": {
        "tx_per_day": 70,
        "pairing_bias": 0.40,
        "open_hours": list(range(6, 23)),
        "peak_hours": [7, 8, 9, 18, 19, 20, 21],
        "day_factor": [1.22, 1.20, 1.15, 1.20, 1.28, 0.58, 0.42],
        "salary_effect": False,
    },
}


def build_rules(store_catalog: pd.DataFrame):
    """Resolve the category rules against one store's own catalogue."""
    def pool(name):
        return store_catalog[store_catalog["category"] == name]["sku"].tolist()

    rules = []
    for cat_a, cat_b, weight in RAW_RULES:
        a, b = pool(cat_a), pool(cat_b)
        if a and b:
            rules.append((a, b, weight))
    if not rules:
        raise SystemExit("No valid pairing rules for this store's catalogue")
    total = sum(w for _, _, w in rules)
    return [(a, b, w / total) for a, b, w in rules]


def pick_pair(rules):
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


def signature_pairs(code: str, rules) -> list[tuple[str, str]]:
    """The shop's handful of habitual pairings.

    Drawn from their own seed so they stay the same every time the data is
    regenerated -- a demo that suggests different bundles each day would be
    less believable than one that shows the same habits sharpening.
    """
    rng = random.Random(f"signature-{code}")
    pairs: list[tuple[str, str]] = []
    # The complementary rules come first in RAW_RULES; prefer them.
    candidates = rules[: max(3, len(rules) // 2)]
    attempts = 0
    while len(pairs) < SIGNATURE_PAIRS and attempts < 200:
        attempts += 1
        a_pool, b_pool, _ = rng.choice(candidates)
        a, b = rng.choice(a_pool), rng.choice(b_pool)
        pair = tuple(sorted((a, b)))
        if a != b and pair not in pairs:
            pairs.append(pair)
    return pairs


def pick_signature(pairs: list[tuple[str, str]]) -> tuple[str, str]:
    """Zipf-like: the first pairing is the strongest, each next one weaker."""
    weights = [1 / (i + 1) for i in range(len(pairs))]
    return random.choices(pairs, weights=weights, k=1)[0]


def pick_hour(profile) -> int:
    """Trade happens all day; peaks are weighted, not exclusive."""
    hours = profile["open_hours"]
    weights = [3.2 if h in profile["peak_hours"] else 1.0 for h in hours]
    return random.choices(hours, weights=weights, k=1)[0]


def month_factor(day_of_month: int, profile) -> float:
    """More bills in the first days after salaries, fewer as the month runs out."""
    if not profile["salary_effect"]:
        return 1.02 if day_of_month <= 5 else 1.0
    if day_of_month <= 5:
        return 1.20
    if day_of_month <= 7:
        return 1.08
    if day_of_month >= 26:
        return 0.92
    return 1.0


def quantity(category: str, day_of_month: int, profile) -> int:
    """Singles, except staples -- which are bought in twos at month start."""
    if category not in STAPLES:
        return 1
    if profile["salary_effect"] and day_of_month <= 7:
        r = random.random()
        return 3 if r < 0.10 else 2 if r < 0.55 else 1
    return 2 if random.random() < (0.15 if profile["salary_effect"] else 0.05) else 1


def generate_store(code: str, profile, now: datetime) -> pd.DataFrame:
    catalog = pd.read_excel(BASE / f"product_catalog_{code}.xlsx")
    skus = catalog["sku"].tolist()
    price_of = dict(zip(catalog["sku"], catalog["sell_price"]))
    category_of = dict(zip(catalog["sku"], catalog["category"]))
    rules = build_rules(catalog)
    signatures = signature_pairs(code, rules)

    today = now.date()
    first = today - timedelta(weeks=WEEKS)
    elapsed = now.minute / 60  # share of the current hour already gone

    rows = []
    bill = 0
    day = first
    while day <= today:
        factor = (
            profile["day_factor"][day.weekday()]
            * month_factor(day.day, profile)
            * random.uniform(0.88, 1.12)
        )
        bills_today = max(1, round(profile["tx_per_day"] * factor))

        for _ in range(bills_today):
            hour = pick_hour(profile)
            # Today stops at the present moment: nothing from later hours,
            # and only the elapsed share of the hour we are in.
            if day == today and (
                hour > now.hour or (hour == now.hour and random.random() > elapsed)
            ):
                continue

            if random.random() < profile["pairing_bias"]:
                if signatures and random.random() < SIGNATURE_SHARE:
                    basket = list(pick_signature(signatures))
                else:
                    basket = list(pick_pair(rules))
            else:
                basket = [random.choice(skus)]

            bill += 1
            for sku in basket:
                rows.append({
                    "date": day.isoformat(),
                    "hour": hour,
                    "transaction_id": f"{code}-{bill:06d}",
                    "sku": sku,
                    "qty": quantity(category_of[sku], day.day, profile),
                    "unit_price": price_of[sku],
                })
        day += timedelta(days=1)

    df = pd.DataFrame(rows)
    unknown = set(df["sku"]) - set(skus)
    assert not unknown, f"{code} sold SKUs it does not stock: {unknown}"
    return df


def main(now: datetime | None = None) -> datetime:
    now = now or datetime.now(IST)
    random.seed(42)
    print(f"Sale lines: {WEEKS} weeks to {now:%a %d %b %Y, %H:%M} IST")
    for code, profile in STORES.items():
        df = generate_store(code, profile, now)
        out = BASE / f"sales_lines_{code}.xlsx"
        df.to_excel(out, index=False)
        bills = df["transaction_id"].nunique()
        days = df["date"].nunique()
        print(
            f"  {code}: {len(df):,} lines, {bills:,} bills over {days} days "
            f"({df['date'].min()} to {df['date'].max()})"
        )
    return now


if __name__ == "__main__":
    main()
