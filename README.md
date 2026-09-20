# StepToSale

Retail analytics for small stores: hourly footfall vs sales, product bundling
from real basket data, and group buying across neighbouring shops.

## Running it

```bash
make db-up                   # postgres in docker
cd backend && alembic upgrade head
cd backend && python scripts/reset_demo.py     # seed a coherent demo dataset
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Tests:

```bash
cd backend && python -m pytest tests/ -q
```

---

# Group Buying

Neighbouring stores combine their wholesale orders to reach volume price
tiers. A supplier sells sugar at ₹45/kg for 1–19kg, ₹40 for 20–49kg, ₹35 for
50+. S1 needs 15kg and S2 needs 20kg; alone they pay ₹45 and ₹40, together
their 35kg reaches ₹40 for both. A third store tips them into the ₹35 tier.

Run `python scripts/demo_pool.py` to see the whole model work on the console
without the app.

## How savings are split

This is the interesting problem, and the UI exposes three answers side by side.

| Rule | S1 (15kg) | S2 (20kg) |
|---|---|---|
| Flat unit price | ₹75.00 | ₹0.00 |
| Pro-rata | ₹32.14 | ₹42.86 |
| Shapley | ₹37.50 | ₹37.50 |

A flat pooled unit price looks fair and is not: S2 already qualified for ₹40/kg
on its own, so it saves nothing while S1 takes the entire gain. Pro-rata (the
default, and what real buying groups use) splits by quantity. Shapley splits by
average marginal contribution across every coalition, which is the defensible
answer when one store's volume is what unlocks the tier.

## What makes the numbers trustworthy

- **Money is integer paise everywhere.** Floats are rejected at the boundary,
  not tolerated. A settlement that splits a discount has to add up exactly.
- **Splits use the largest-remainder method** and are asserted to sum to the
  penny. Store payables must equal the supplier invoice or the settlement
  raises instead of returning a wrong number.
- **The leftover paisa rotates.** Two stores with identical orders would
  otherwise see the same one collect the spare paisa in every pool forever;
  a pool's cycle number shifts where tie-breaking starts.
- **Price lists are versioned and pinned.** A closed pool records exactly which
  supplier price list it settled against, so later price changes cannot rewrite
  history.
- **Every state change is in an append-only event log**, so a disagreement is
  answered by replaying the pool rather than arguing about it.

178 tests cover the tier maths, the lifecycle, and property-based checks that
the books balance for any combination of orders and any split rule.

## Out of scope for this build

Each of these is stubbed at a real seam rather than faked — the note says what
exists and what is missing.

- **Payment flows.** Settlement computes exactly what each store owes and the
  supplier invoice total, but nothing collects money. The seam is a per-store
  payable; wiring Razorpay Payment Links (test mode) with HMAC webhook
  verification would close it without changing the settlement code.
- **Supplier portal.** Suppliers, price lists and versioned tiers are modelled
  and seeded, but there is no interface for a supplier to maintain them. The
  versioning already supports it: new prices insert a new version rather than
  updating rows.
- **Multi-pool management.** The schema is multi-pool throughout — pools are
  first-class rows with their own lifecycle and members. The UI just shows one.
- **Notifications.** The event log records everything worth notifying on
  ("pool crossed a tier", "closes in 6h"), but nothing is dispatched. The
  missing piece is an outbox with retry and idempotency.
- **Dispute resolution.** No workflow exists, but the append-only log plus
  pinned price-list versions mean any past state is reconstructable, which is
  the part disputes actually need.
- **Concurrency.** Orders are validated against the domain before they are
  written, but there is no optimistic locking, so two stores committing in the
  same instant could both price against a stale tier.
