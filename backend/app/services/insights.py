import pandas as pd
from typing import List, Dict
from .metrics import hourly_series, peak_hours, compute_kpis

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def generate_insights(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Returns a list of {kind, text} dicts where kind is one of:
    warning | opportunity | observation | win
    """
    insights: List[Dict[str, str]] = []

    hourly = hourly_series(df)
    non_empty = [h for h in hourly if h["footfall"] > 0]
    if not non_empty:
        return insights

    k = compute_kpis(df)
    avg_conv = sum(h["conversion"] for h in non_empty) / len(non_empty)

    peak_ff = max(non_empty, key=lambda h: h["footfall"])
    peak_sales = max(non_empty, key=lambda h: h["sales"])
    best_conv = max(non_empty, key=lambda h: h["conversion"])

    # ------------------------------------------------------------------
    # 1. WARNING: busiest hour converts poorly
    # ------------------------------------------------------------------
    if peak_ff["conversion"] < avg_conv * 0.8:
        insights.append({
            "kind": "warning",
            "text": (
                f"{peak_ff['hour']}:00 is your busiest hour ({peak_ff['footfall']} visitors) "
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
                f"— your best hour — but only {best_conv['footfall']} people walk in. "
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
    df_dow = df.copy()
    df_dow["dow"] = pd.to_datetime(df_dow["date"]).dt.dayofweek
    daily_dow = df_dow.groupby("dow")["footfall"].sum()
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
    lag = peak_sales["hour"] - peak_ff["hour"]
    if abs(lag) >= 2:
        insights.append({
            "kind": "observation",
            "text": (
                f"Footfall peaks at {peak_ff['hour']}:00 but sales peak at "
                f"{peak_sales['hour']}:00 — a {abs(lag)}-hour gap. "
                f"People browse early and buy late."
            ),
        })

    # ------------------------------------------------------------------
    # 7. WIN: basket size
    # ------------------------------------------------------------------
    if k["avg_basket"] > 0:
        insights.append({
            "kind": "observation",
            "text": (
                f"Average basket is ₹{k['avg_basket']:.0f}. A ₹{k['avg_basket']*0.1:.0f} "
                f"increase per bill would add roughly "
                f"₹{k['total_sales']*0.1:,.0f} to your weekly revenue."
            ),
        })

    # Cap at 5, keep order of importance
    return insights[:5]

def whatsapp_summary(df: pd.DataFrame) -> str:
    k = compute_kpis(df)
    hourly = hourly_series(df)
    non_empty = [h for h in hourly if h["footfall"] > 0]
    peak = max(non_empty, key=lambda h: h["footfall"]) if non_empty else None

    lines = [
        "📊 *Daily Summary*",
        "",
        f"👣 Footfall: {k['total_footfall']:,}",
        f"💰 Sales: ₹{k['total_sales']:,.0f}",
        f"🎯 Conversion: {k['conversion_rate']*100:.1f}%",
        f"🛒 Avg basket: ₹{k['avg_basket']:.0f}",
    ]
    if peak:
        lines.append(f"⏰ Busiest: {peak['hour']}:00 ({peak['footfall']} visitors)")

    top = generate_insights(df)[:2]
    if top:
        lines.append("")
        for i in top:
            prefix = {"warning": "⚠️", "opportunity": "💡", "win": "✅", "observation": "ℹ️"}.get(i["kind"], "•")
            lines.append(f"{prefix} {i['text']}")

    return "\n".join(lines)