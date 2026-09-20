import pandas as pd
from typing import Dict, List, Tuple

def compute_kpis(df: pd.DataFrame) -> Dict:
    total_footfall = int(df["footfall"].sum())
    total_sales = float(df["sales"].sum())
    total_tx = int(df["transactions"].sum())

    return {
        "total_footfall": total_footfall,
        "total_sales": total_sales,
        "total_transactions": total_tx,
        "conversion_rate": (total_tx / total_footfall) if total_footfall else 0.0,
        "avg_basket": (total_sales / total_tx) if total_tx else 0.0,
        "sales_per_visitor": (total_sales / total_footfall) if total_footfall else 0.0,
    }

def hourly_series(df: pd.DataFrame) -> List[Dict]:
    g = df.groupby("hour", as_index=False).agg(
        footfall=("footfall", "sum"),
        sales=("sales", "sum"),
        transactions=("transactions", "sum"),
    )
    full = pd.DataFrame({"hour": range(24)}).merge(g, on="hour", how="left").fillna(0)
    # The left join turns counts into floats for the missing hours, which then
    # reach the insight text as "20.0 people walk in".
    full["footfall"] = full["footfall"].astype(int)
    full["transactions"] = full["transactions"].astype(int)
    full["conversion"] = full.apply(
        lambda r: (r["transactions"] / r["footfall"]) if r["footfall"] else 0.0, axis=1
    )
    return full.to_dict(orient="records")

def daily_series(df: pd.DataFrame) -> List[Dict]:
    g = df.groupby("date", as_index=False).agg(
        footfall=("footfall", "sum"),
        sales=("sales", "sum"),
        transactions=("transactions", "sum"),
    )
    g["conversion"] = g.apply(
        lambda r: (r["transactions"] / r["footfall"]) if r["footfall"] else 0.0, axis=1
    )
    g = g.sort_values("date")
    return g.to_dict(orient="records")

def peak_hours(df: pd.DataFrame) -> Tuple[int, int]:
    hourly = hourly_series(df)
    non_empty = [h for h in hourly if h["footfall"] > 0]
    if not non_empty:
        return (0, 0)
    peak_ff = max(non_empty, key=lambda h: h["footfall"])["hour"]
    peak_sales = max(non_empty, key=lambda h: h["sales"])["hour"]
    return peak_ff, peak_sales

def heatmap_series(df: pd.DataFrame) -> List[Dict]:
    df = df.copy()
    df["dow"] = pd.to_datetime(df["date"]).dt.dayofweek
    g = df.groupby(["dow", "hour"], as_index=False)["footfall"].sum()
    return g.to_dict(orient="records")