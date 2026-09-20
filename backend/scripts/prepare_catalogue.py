import pandas as pd
import random

random.seed(42)

# 1. Load — new schema
df = pd.read_csv("BigBasket.csv")

# 2. Rename to our internal convention
df = df.rename(columns={
    "ProductName": "name",
    "Brand": "brand",
    "Price": "market_price",        # MRP
    "DiscountPrice": "sale_price",  # what the shop charges
    "Category": "category",
    "SubCategory": "sub_category",
})

# 3. Filter to kirana-appropriate categories
KEEP_CATEGORIES = [
    "Snacks & Branded Foods",
    "Beverages",
    "Bakery, Cakes & Dairy",
    "Foodgrains, Oil & Masala",
    "Cleaning & Household",
    "Beauty & Hygiene",
]
df = df[df["category"].isin(KEEP_CATEGORIES)]

# 4. Drop missing prices/names
df = df.dropna(subset=["name", "market_price", "sale_price"])

# 5. Some rows have sale_price = 0 → fall back to MRP
df.loc[df["sale_price"] <= 0, "sale_price"] = df["market_price"]

# 6. Dedupe by product name
df = df.drop_duplicates(subset=["name"], keep="first")

# 7. Sample a manageable set: up to 40 per category
MAX_PER_CATEGORY = 40
sampled = []
for cat, group in df.groupby("category"):
    n = min(len(group), MAX_PER_CATEGORY)
    sampled.append(group.sample(n=n, random_state=42))
df = pd.concat(sampled).reset_index(drop=True)

# 8. Assign SKUs
df["sku"] = [f"BB{idx:04d}" for idx in range(1, len(df) + 1)]

# 9. Derive cost from MRP — assume 75% of MRP is the shop's cost
df["cost_price"] = (df["market_price"] * 0.75).round(2)
df["sell_price"] = df["sale_price"].round(2)

# 10. Drop any product where sell < cost (data noise)
df = df[df["sell_price"] > df["cost_price"]].reset_index(drop=True)

# 11. Final catalog
catalog = df[["sku", "name", "brand", "category", "cost_price", "sell_price"]]

# 12. Two stores, different economics
for store_code, cost_multiplier in [("S1", 1.00), ("S2", 1.15)]:
    store_catalog = catalog.copy()
    store_catalog["cost_price"] = (store_catalog["cost_price"] * cost_multiplier).round(2)
    # After raising cost, drop anything that would be unprofitable
    store_catalog = store_catalog[store_catalog["sell_price"] > store_catalog["cost_price"]]
    store_catalog.to_excel(f"product_catalog_{store_code}.xlsx", index=False)
    print(f"Wrote product_catalog_{store_code}.xlsx ({len(store_catalog)} products)")

# 13. Persist curated catalog for the transaction generator
catalog.to_csv("curated_catalog.csv", index=False)
print(f"Total curated products: {len(catalog)}")
print("\nCategory breakdown:")
print(catalog["category"].value_counts())