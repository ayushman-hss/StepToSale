# StepToSales

Retail analytics for small neighbourhood shops. Three tools that each answer
the same question — *are you above the line?* — for footfall, pricing, and
buying.

- **Sales vs footfall** — how many visitors actually buy, hour by hour
- **Bundles** — products customers already buy together, priced above your
  margin floor
- **Group buying** — pool orders with nearby shops to reach wholesale tiers

Built with FastAPI + PostgreSQL on the backend, React + TypeScript + Vite on
the frontend.

---

## Running it locally

**Prerequisites:** Python 3.11+, Node.js 18+, PostgreSQL 15+.

### 1. Database

Either run Postgres natively, or use the included compose file:

```bash
docker compose up -d db
```

If running natively, create the role and database:

```sql
CREATE USER footfall WITH PASSWORD 'footfall' LOGIN;
CREATE DATABASE footfall OWNER footfall;
\c footfall
GRANT ALL ON SCHEMA public TO footfall;
ALTER SCHEMA public OWNER TO footfall;
```

The `GRANT`/`ALTER` matter on Postgres 15+ — without them Alembic fails with
"permission denied for schema public".

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1         # Windows
source .venv/bin/activate          # macOS/Linux

pip install -r requirements.txt

cp .env.example .env               # edit DATABASE_URL if needed
alembic upgrade head
```

Load the demo dataset and start the server:

```bash
python scripts/reset_demo.py       # coherent demo data for both shops
uvicorn app.main:app --reload --port 8000
```

API docs at http://localhost:8000/docs.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

---

## What's in the box

### Sales vs footfall (`/dashboard`)

Upload hourly rows (date, hour, footfall, transactions, sales, store_id).
The dashboard computes conversion, average basket, and per-hour patterns,
then surfaces plain-language observations:

- *"18:00 is your busiest hour but conversion is 12% vs 21% average."*
- *"Tuesdays are 40% quieter — consider a Tuesday offer."*
- *"62% of your footfall happens in 3 hours."*

Ready to forward as a WhatsApp message with one button.

### Bundles (`/products`, `/bundles`)

Set cost and sell price per product once. Then upload transaction line
items, and the backend mines co-purchase pairs using confidence and lift —
market-basket analysis, not ML. Each suggestion shows:

- How often the pair appears together
- How much more likely than chance
- A bundle price that never drops margin below your floor

You approve, edit the price, or reject each one. Nothing is applied
automatically.

### Group buying (`/pools`)

Neighbouring shops combine orders to reach a supplier's volume tier. A
supplier might sell sugar at ₹45/kg for 1–19kg, ₹40 for 20–49kg, ₹35 for 50+.
S1 needs 15kg, S2 needs 20kg; alone they pay ₹45 and ₹40, together their
35kg reaches ₹40 for both.

The interesting problem is how the saving is split. Three answers, shown
side by side:

| Rule | S1 (15kg) | S2 (20kg) |
|---|---|---|
| Flat unit price | ₹75.00 | ₹0.00 |
| Pro-rata | ₹32.14 | ₹42.86 |
| Shapley | ₹37.50 | ₹37.50 |

A flat pooled unit price looks fair and is not — S2 already qualified for
₹40/kg alone, so it saves nothing while S1 takes the whole gain. Pro-rata
splits by quantity. Shapley splits by average marginal contribution across
every coalition, which is the defensible answer when one shop's volume is
what unlocks the tier.

Every state change is written to an append-only event log, so a dispute is
answered by replaying the pool rather than arguing about it.

---

## Why the numbers are trustworthy

- **Money is integer paise everywhere.** Floats are rejected at the boundary,
  not tolerated. A settlement that splits a discount has to add up exactly.
- **Splits use the largest-remainder method** and are asserted to sum to the
  penny. Store payables must equal the supplier invoice or the settlement
  raises rather than returning a wrong number.
- **The leftover paisa rotates.** Two shops with identical orders would
  otherwise see the same one collect the spare paisa in every pool forever.
  A pool's cycle number shifts where tie-breaking starts.
- **Price lists are versioned and pinned.** A closed pool records exactly
  which supplier price list it settled against, so later price changes
  cannot rewrite history.

---

## Out of scope for this build

Each of these is stubbed at a real seam rather than faked:

- **Payment flows.** Settlement computes exactly what each shop owes and the
  supplier invoice total, but nothing collects money.
- **Supplier portal.** Suppliers, price lists and versioned tiers are
  modelled and seeded, but there is no interface for a supplier to maintain
  them.
- **Multi-pool management.** The schema is multi-pool throughout; the UI
  shows one.
- **Notifications.** The event log records everything worth notifying on
  ("pool crossed a tier", "closes in 6h"), but nothing is dispatched.
- **Concurrency.** Orders are validated against the domain before they are
  written, but there is no optimistic locking, so two shops committing in
  the same instant could both price against a stale tier.

---

## Project layout

```
backend/
  app/
    main.py              FastAPI app
    models.py            SQLModel tables (features 1 & 2)
    models_pooling.py    SQLModel tables (feature 3)
    routers/             one per feature
    services/
      metrics.py         hourly / daily / heatmap aggregates
      insights.py        rule-based plain-language callouts
      associations.py    market-basket co-purchase mining
      pricing.py         margin-floor bundle pricing
      pooling/           pure domain layer for group buying
  alembic/               migrations
  scripts/               sample data generators
  tests/                 pooling tests (money, tiers, allocation, pool)

frontend/
  src/
    pages/               one per route
    components/          feature-specific UI
    lib/ui/              design system (controls, ThresholdBar, wordmark)
    lib/charts/          ECharts theme
    api.ts               typed API client
    store.ts             dashboard filter state
```

---

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

178 tests cover the tier maths, the pool lifecycle, and property-based
checks that the books balance for any combination of orders and any split
rule.

---

## License

MIT