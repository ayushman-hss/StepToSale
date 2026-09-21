import pandas as pd
from typing import List, Dict
from .metrics import (
    hourly_series,
    compute_kpis,
    complete_days,
    daily_totals_by_weekday,
)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def generate_insights(df: pd.DataFrame, partial_date: str | None = None) -> List[Dict[str, str]]:
    """
    Returns a list of {kind, text} dicts where kind is one of:
    warning | opportunity | observation | win
    """
    insights: List[Dict[str, str]] = []

    # Hourly figures are an average day; say so when the range is longer
    # than one day, so "22 visitors" is never mistaken for a total.
    days = int(df["date"].nunique())
    per_day = "" if days == 1 else " on an average day"

    def n(x: float) -> str:
        return f"{round(x):,}"

    def people(x: float) -> str:
        return f"{n(x)} {'person' if round(x) == 1 else 'people'}"

    hourly = hourly_series(df)
    non_empty = [h for h in hourly if h["footfall"] > 0]
    if not non_empty:
        return insights

    k = compute_kpis(df)
    avg_conv = sum(h["conversion"] for h in non_empty) / len(non_empty)

    peak_ff = max(non_empty, key=lambda h: h["footfall"])
    peak_sales = max(non_empty, key=lambda h: h["sales"])
    # An hour with one visitor who bought is "100% conversion" and means
    # nothing. Only hours with a real share of the traffic can win.
    floor = max(3.0, peak_ff["footfall"] * 0.3)
    substantial = [h for h in non_empty if h["footfall"] >= floor] or [peak_ff]
    best_conv = max(substantial, key=lambda h: h["conversion"])

    # ------------------------------------------------------------------
    # 1. WARNING: busiest hour converts poorly
    # ------------------------------------------------------------------
    if peak_ff["conversion"] < avg_conv * 0.8:
        insights.append({
            "kind": "warning",
            "text": (
                f"{peak_ff['hour']}:00 is your busiest hour ({n(peak_ff['footfall'])} visitors{per_day}) "
                f"but conversion is only {peak_ff['conversion']*100:.1f}% vs "
                f"{avg_conv*100:.1f}% average. Check staffing or impulse-buy placement."
            ),
        })

    # ------------------------------------------------------------------
    # 2. WIN: busiest hour also converts well
    # ------------------------------------------------------------------
    elif peak_ff["conversion"] > avg_conv * 1.1:
        lift = (peak_ff["conversion"] - avg_conv) * 100
        insights.append({
            "kind": "win",
            "text": (
                f"{peak_ff['hour']}:00 is your busiest hour and it converts at "
                f"{peak_ff['conversion']*100:.1f}% — {lift:.1f} points above your average. "
                f"Whatever you're doing then, do more of it."
            ),
        })

    # ------------------------------------------------------------------
    # 3. OPPORTUNITY: best conversion hour is not your busiest
    # ------------------------------------------------------------------
    if best_conv["hour"] != peak_ff["hour"]:
        insights.append({
            "kind": "opportunity",
            "text": (
                f"{best_conv['hour']}:00 converts at {best_conv['conversion']*100:.1f}% "
                f"— your best hour — but only {people(best_conv['footfall'])} walk in{per_day}. "
                f"Drive more footfall into this window."
            ),
        })

    # ------------------------------------------------------------------
    # 4. OBSERVATION: footfall concentration
    # ------------------------------------------------------------------
    total_ff = sum(h["footfall"] for h in non_empty)
    top3 = sorted(non_empty, key=lambda h: -h["footfall"])[:3]
    top3_ff = sum(h["footfall"] for h in top3)
    if total_ff > 0:
        pct = round(top3_ff / total_ff * 100)
        hours_str = ", ".join(f"{h['hour']}:00" for h in sorted(top3, key=lambda h: h["hour"]))
        if pct >= 35:
            insights.append({
                "kind": "observation",
                "text": (
                    f"{pct}% of your footfall happens in 3 hours: {hours_str}. "
                    f"Make sure those windows are always fully staffed."
                ),
            })

    # ------------------------------------------------------------------
    # 5. OPPORTUNITY: quietest day
    # ------------------------------------------------------------------
    # Mean per weekday over complete days: sums would favour weekdays that
    # happen to occur more often in the range, and a half-finished today
    # would make its weekday look quiet.
    daily_dow = daily_totals_by_weekday(df, partial_date)
    if len(daily_dow) > 1:
        avg_dow = daily_dow.mean()
        quietest = int(daily_dow.idxmin())
        quiet_val = daily_dow.min()
        if avg_dow > 0 and quiet_val < avg_dow * 0.85:
            pct = round((1 - quiet_val / avg_dow) * 100)
            insights.append({
                "kind": "opportunity",
                "text": (
                    f"{DAY_NAMES[quietest]} is {pct}% quieter than your average day. "
                    f"Consider a {DAY_NAMES[quietest]} offer to smooth demand."
                ),
            })

    # ------------------------------------------------------------------
    # 6. OBSERVATION: sales lag footfall
    # ------------------------------------------------------------------
    # One day's peak-sales hour is often a single large bill; needs a few days.
    lag = peak_sales["hour"] - peak_ff["hour"]
    if abs(lag) >= 2 and days >= 3:
        insights.append({
            "kind": "observation",
            "text": (
                f"Footfall peaks at {peak_ff['hour']}:00 but sales peak at "
                f"{peak_sales['hour']}:00 — a{'n' if abs(lag) in (8, 11, 18) else ''} "
                f"{abs(lag)}-hour gap. "
                f"People browse early and buy late."
            ),
        })

    # ------------------------------------------------------------------
    # 7. WIN: basket size
    # ------------------------------------------------------------------
    if k["avg_basket"] > 0:
        uplift = k["avg_basket"] * 0.1
        full = complete_days(df, partial_date)
        full_days = int(full["date"].nunique())
        if full_days >= 2:
            # Project from complete days only, scaled to a real week.
            weekly = float(full["sales"].sum()) / full_days * 7 * 0.1
            gain = f"roughly ₹{weekly:,.0f} a week"
        elif full_days == 1:
            # One day is too thin to project a week from.
            gain = f"₹{float(full['sales'].sum()) * 0.1:,.0f} on a day like this"
        else:
            gain = f"₹{float(df['sales'].sum()) * 0.1:,.0f} on today's bills so far"
        insights.append({
            "kind": "observation",
            "text": (
                f"Average bill is ₹{k['avg_basket']:.0f}. ₹{uplift:.0f} more per bill "
                f"would add {gain}."
            ),
        })

    # Cap at 5, keep order of importance
    return insights[:5]

def whatsapp_summary(
    df: pd.DataFrame, title: str = "Summary", partial_date: str | None = None
) -> str:
    k = compute_kpis(df)
    hourly = hourly_series(df)
    non_empty = [h for h in hourly if h["footfall"] > 0]
    peak = max(non_empty, key=lambda h: h["footfall"]) if non_empty else None

    lines = [
        f"📊 *{title}*",
        "",
        f"👣 Footfall: {k['total_footfall']:,}",
        f"💰 Sales: ₹{k['total_sales']:,.0f}",
        f"🎯 Conversion: {k['conversion_rate']*100:.1f}%",
        f"🛒 Avg basket: ₹{k['avg_basket']:.0f}",
    ]
    if peak:
        days = int(df["date"].nunique())
        note = "" if days == 1 else " a day"
        lines.append(f"⏰ Busiest: {peak['hour']}:00 ({round(peak['footfall']):,} visitors{note})")

    top = generate_insights(df, partial_date)[:2]
    if top:
        lines.append("")
        for i in top:
            prefix = {"warning": "⚠️", "opportunity": "💡", "win": "✅", "observation": "ℹ️"}.get(i["kind"], "•")
            lines.append(f"{prefix} {i['text']}")

    return "\n".join(lines)