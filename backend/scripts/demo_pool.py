"""Walk through a group-buying pool on the console.

The pooling core has no API or UI yet, so this is how to see it work:

    cd backend && .venv/Scripts/python scripts/demo_pool.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.pooling import (  # noqa: E402
    Pool,
    Strategy,
    Tier,
    TierTable,
    format_paise,
)

SUGAR = TierTable(
    "SUP1", "SUGAR", "2026-09-01",
    (Tier(1, 19, 4500), Tier(20, 49, 4000), Tier(50, None, 3500)),
)
RICE = TierTable(
    "SUP2", "RICE", "2026-09-01",
    (Tier(1, 24, 6200), Tier(25, None, 5800)),
)

f = format_paise
RULE = "-" * 68


def build(**orders: int) -> Pool:
    pool = Pool("koramangala", "Koramangala Neighborhood Pool", {"SUGAR": SUGAR})
    pool.open()
    for store, qty in orders.items():
        pool.place_order(store, "SUGAR", qty)
    return pool


def show(pool: Pool, strategy: Strategy) -> None:
    s = pool.project(strategy)
    p = s.products[0]
    print(f"\n  strategy: {strategy.value}")
    print(f"    {p.total_qty}kg total -> tier {p.tier_label} @ {f(p.pooled_unit_price)}/kg")
    print(f"    supplier invoice {f(s.invoice_total)}, pool saved {f(s.total_savings)}")
    if p.units_to_next_tier:
        print(f"    {p.units_to_next_tier}kg more would drop to "
              f"{f(p.next_tier_unit_price)}/kg")
    for st in s.stores:
        print(f"      {st.store}: alone {f(st.cost_alone):>10}"
              f"  ->  pays {f(st.payable):>10}"
              f"   saves {f(st.savings):>9} ({st.savings_pct:4.1f}%)")


print(RULE)
print("SUPPLIER PRICE LIST -- sugar, SUP1, version 2026-09-01")
print(RULE)
for tier in SUGAR.tiers:
    print(f"  {tier.label:>8} kg   {f(tier.unit_price)}/kg")

print()
print(RULE)
print("1. S1 ALONE needs 15kg")
print(RULE)
show(build(S1=15), Strategy.UNIT_PRICE)

print()
print(RULE)
print("2. S1 (15kg) + S2 (20kg) pool -> 35kg reaches the middle tier")
print(RULE)
pool = build(S1=15, S2=20)
for strategy in Strategy:
    show(pool, strategy)
print("\n  Note how unit_price leaves S2 with nothing: it already qualified for")
print("  40/kg on its own, so a flat pooled price hands the whole gain to S1.")
print("  Shapley splits it evenly, because the saving needs both of them.")

print()
print(RULE)
print("3. S3 joins with 15kg -> 50kg unlocks the cheapest tier")
print(RULE)
show(build(S1=15, S2=20, S3=15), Strategy.SHAPLEY)

print()
print(RULE)
print("4. CLOSING THE POOL -- lock, settle, and refuse further changes")
print(RULE)
pool = build(S1=15, S2=20, S3=15)
final = pool.close(Strategy.SHAPLEY)
print(f"  status: {pool.status.value}")
print(f"  settled against price list version "
      f"{final.products[0].price_list_version}")
print(f"  invoice {f(final.invoice_total)}  |  saved {f(final.total_savings)}")
try:
    pool.place_order("S4", "SUGAR", 10)
except Exception as exc:
    print(f"  S4 tries to join late -> refused: {exc}")

print()
print(RULE)
print("5. THE SPARE PAISA ROTATES -- S1 and S3 order identically")
print(RULE)
totals: dict[str, int] = {}
for week in range(3):
    p = Pool("koramangala", "Pool", {"SUGAR": SUGAR}, rotation=week)
    p.open()
    p.place_order("S1", "SUGAR", 15)
    p.place_order("S2", "SUGAR", 20)
    p.place_order("S3", "SUGAR", 15)
    s = p.project(Strategy.SHAPLEY)
    row = {x.store: x.savings for x in s.stores}
    for k, v in row.items():
        totals[k] = totals.get(k, 0) + v
    print(f"  week {week}: " + "   ".join(f"{k} {f(v)}" for k, v in row.items()))
print(f"  3-week totals: " + "   ".join(f"{k} {f(v)}" for k, v in totals.items()))
print(f"  S1 vs S3 over a full cycle: {totals['S1'] - totals['S3']} paise apart")
print(RULE)
