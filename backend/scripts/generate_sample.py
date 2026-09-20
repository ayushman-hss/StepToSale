"""Build the hourly footfall file from the per-store sale lines.

Two things were wrong before:

1. Footfall, transactions and sales were computed once per hour and then
   written for BOTH stores, so S1 and S2 had byte-identical data.
2. This file and sales_lines_S*.xlsx were generated independently, so the
   dashboard claimed 902 transactions in a week while the bundle engine saw
   315 of them -- and they were not even in the same year.

Now transactions and sales are derived from the sale lines, which are the
record of what actually sold. Only footfall is modelled, because footfall is
the one number a POS genuinely cannot tell you -- it needs a door counter.
Each store gets its own conversion profile, so the two look like different
businesses because they are.

    cd backend && python scripts/generate_sample.py
"""
import random
from datetime import date as date_type
from pathlib import Path

import pandas as pd

random.seed(7)

BASE = Path(__file__).resolve().parents[1]
STORES = ["S1", "S2"]

PROFILES = {
    # A neighbourhood kirana: people arrive intending to buy, so most of them
    # do. It gets busier at the peaks, and conversion dips a little then
    # because queues put some people off.
    "S1": {
        "open_hours": range(8, 22),
        "peak_hours": {9, 10, 11, 18, 19, 20},
        "conversion_peak": (0.52, 0.62),
        "conversion_offpeak": (0.64, 0.78),
        "idle_footfall": (0, 3),
    },
    # A kiosk by the station: enormous passing trade, most of which walks
    # straight past the counter. High footfall, low conversion.
    "S2": {
        "open_hours": range(6, 23),
        "peak_hours": {7, 8, 9, 18, 19, 20, 21},
        "conversion_peak": (0.24, 0.34),
        "conversion_offpeak": (0.36, 0.50),
        "idle_footfall": (1, 6),
    },
}


def build(store: str) -> list[dict]:
    lines = pd.read_excel(BASE / f"sales_lines_{store}.xlsx")
    lines["date"] = pd.to_datetime(lines["date"]).dt.strftime("%Y-%m-%d")
    lines["value"] = lines["qty"] * lines["unit_price"]

    sold = (
        lines.groupby(["date", "hour"])
        .agg(transactions=("transaction_id", "nunique"), sales=("value", "sum"))
        .to_dict("index")
    )

    profile = PROFILES[store]
    rows: list[dict] = []
    for day in sorted(lines["date"].unique()):
        for hour in profile["open_hours"]:
            actual = sold.get((day, hour))
            transactions = int(actual["transactions"]) if actual else 0
            sales = float(actual["sales"]) if actual else 0.0

            if transactions:
                lo, hi = (
                    profile["conversion_peak"]
                    if hour in profile["peak_hours"]
                    else profile["conversion_offpeak"]
                )
                conversion = random.uniform(lo, hi)
                # At least as many visitors as buyers, always.
                footfall = max(transactions, round(transactions / conversion))
            else:
                # The door still opens in a quiet hour; nobody buys.
                footfall = random.randint(*profile["idle_footfall"])

            rows.append(
                {
                    "date": day,
                    "hour": hour,
                    "footfall": footfall,
                    "transactions": transactions,
                    "sales": round(sales, 2),
                    "store_id": store,
                }
            )
    return rows


def main() -> None:
    rows: list[dict] = []
    for store in STORES:
        store_rows = build(store)
        rows.extend(store_rows)

        ff = sum(r["footfall"] for r in store_rows)
        tx = sum(r["transactions"] for r in store_rows)
        sales = sum(r["sales"] for r in store_rows)
        first = date_type.fromisoformat(store_rows[0]["date"])
        print(
            f"  {store}: {len(store_rows)} hours, {ff:,} visitors, {tx:,} bills, "
            f"Rs{sales:,.0f}, {tx / ff * 100:.1f}% bought, "
            f"Rs{sales / tx:.0f} per bill (week of {first})"
        )

    df = pd.DataFrame(rows)
    df.to_excel(BASE / "sample-data.xlsx", index=False)
    print(f"Wrote {len(df)} rows to sample-data.xlsx")


if __name__ == "__main__":
    main()
