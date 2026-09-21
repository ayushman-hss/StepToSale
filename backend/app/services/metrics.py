"""Aggregations behind the dashboard.

Totals are for the headline figures. Everything shaped by time of day or day
of week is an *average day*, because a sum over a range just measures how long
the range is: 12 weeks of 18:00 adds up to "1,800 visitors at 18:00", which is
true and useless to a shopkeeper.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd


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


def _per_date_hour(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (date, hour), with every shop in the filter added together."""
    return df.groupby(["date", "hour"], as_index=False)[
        ["footfall", "transactions", "sales"]
    ].sum()


def hourly_series(df: pd.DataFrame) -> List[Dict]:
    """The average day, hour by hour.

    Each hour is averaged over the days on which that hour actually exists in
    the data, so a partial today (no 20:00 yet) does not drag the evening down.
    Conversion is computed from the totals, not averaged, so a quiet hour with
    two visitors cannot outweigh a busy one.
    """
    per = _per_date_hour(df)
    g = per.groupby("hour").agg(
        footfall_sum=("footfall", "sum"),
        tx_sum=("transactions", "sum"),
        sales_sum=("sales", "sum"),
        days=("date", "nunique"),
    )
    out = []
    for hour in range(24):
        if hour in g.index:
            r = g.loc[hour]
            days = int(r["days"]) or 1
            ff, tx = float(r["footfall_sum"]), float(r["tx_sum"])
            out.append({
                "hour": hour,
                "footfall": round(ff / days, 1),
                "transactions": round(tx / days, 1),
                "sales": round(float(r["sales_sum"]) / days, 2),
                "conversion": (tx / ff) if ff else 0.0,
            })
        else:
            out.append({"hour": hour, "footfall": 0.0, "transactions": 0.0,
                        "sales": 0.0, "conversion": 0.0})
    return out


def daily_series(df: pd.DataFrame) -> List[Dict]:
    g = df.groupby("date", as_index=False).agg(
        footfall=("footfall", "sum"),
        sales=("sales", "sum"),
        transactions=("transactions", "sum"),
    )
    g["conversion"] = g.apply(
        lambda r: (r["transactions"] / r["footfall"]) if r["footfall"] else 0.0, axis=1
    )
    return g.sort_values("date").to_dict(orient="records")


def complete_days(df: pd.DataFrame, partial_date: str | None = None) -> pd.DataFrame:
    """Drop the final date if it stops earlier than the shop normally closes.

    That is today, still in progress. Left in, it would make today's weekday
    look quiet and pull any per-day average down.

    A single-day frame cannot tell on its own -- there is no "normally" to
    compare with -- so the caller can name the partial date explicitly.
    """
    if df.empty:
        return df
    if partial_date is not None:
        return df[df["date"] != partial_date]
    last_hour = df.groupby("date")["hour"].max()
    if len(last_hour) < 2:
        return df
    usual_close = int(last_hour.iloc[:-1].mode().iloc[0])
    final_date = last_hour.index.max()
    if int(last_hour[final_date]) < usual_close:
        return df[df["date"] != final_date]
    return df


def is_partial(df: pd.DataFrame) -> bool:
    return len(complete_days(df)) < len(df)


def peak_hours(df: pd.DataFrame) -> Tuple[int, int]:
    hourly = hourly_series(df)
    non_empty = [h for h in hourly if h["footfall"] > 0]
    if not non_empty:
        return (0, 0)
    peak_ff = max(non_empty, key=lambda h: h["footfall"])["hour"]
    peak_sales = max(non_empty, key=lambda h: h["sales"])["hour"]
    return peak_ff, peak_sales


def heatmap_series(df: pd.DataFrame) -> List[Dict]:
    """Average visitors per weekday and hour.

    Averaged over how many times each weekday occurs in the range, so a range
    with two Mondays and one Sunday does not make Monday look twice as busy.
    """
    per = _per_date_hour(df)
    per["dow"] = pd.to_datetime(per["date"]).dt.dayofweek
    g = per.groupby(["dow", "hour"], as_index=False)["footfall"].mean()
    g["footfall"] = g["footfall"].round(1)
    return g.to_dict(orient="records")


def daily_totals_by_weekday(df: pd.DataFrame, partial_date: str | None = None) -> pd.Series:
    """Mean daily visitors for each weekday, over complete days only."""
    full = complete_days(df, partial_date)
    per_day = full.groupby("date", as_index=False)["footfall"].sum()
    per_day["dow"] = pd.to_datetime(per_day["date"]).dt.dayofweek
    return per_day.groupby("dow")["footfall"].mean()
