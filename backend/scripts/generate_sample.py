import pandas as pd
import random

rows = []
for day in range(1, 8):
    date = f"2026-05-{day:02d}"
    for hour in range(9, 22):
        base = 80 if 18 <= hour <= 20 else 30
        footfall = base + random.randint(0, 30)
        transactions = int(footfall * random.uniform(0.10, 0.28))
        sales = transactions * random.randint(180, 500)
        for store in ["S1", "S2"]:
            rows.append({
                "date": date,
                "hour": hour,
                "footfall": footfall,
                "transactions": transactions,
                "sales": sales,
                "store_id": store,
            })

pd.DataFrame(rows).to_excel("sample-data.xlsx", index=False)
print(f"Wrote {len(rows)} rows to sample-data.xlsx")