"""Operator planner: recommend work windows based on modelled odour risk.

Uses the existing risk_table from smell.py to identify lower-risk periods
for scheduling odour-heavy activities (excavation, waste handling, leachate).
"""
import pandas as pd
import config
import smell


def classify_hour(avg_risk):
    """Classify a single hour for operational suitability based on average risk score."""
    if isinstance(avg_risk, (pd.Series, pd.DataFrame)):
        avg_risk = float(avg_risk.mean())
    avg_risk = float(avg_risk)
    if avg_risk < 0.15:
        return "recommended"
    elif avg_risk < 0.35:
        return "moderate"
    else:
        return "avoid"


def build_planner_data(risk_df, wind_df, site):
    """Build 48-hour planner timeline from existing risk and wind data.

    Returns a list of dicts, one per hour, each containing:
      - time (ISO string)
      - hour (int)
      - avg_risk (float)
      - max_risk (float)
      - worst_neighbourhood (str)
      - classification (recommended/moderate/avoid)
      - wind_dir, wind_speed, precipitation, temperature
      - is_night (bool)
      - reason (human-readable string)
    """
    now = smell.forecast_start()
    future_risk = risk_df[risk_df["time"] >= now].copy()

    if future_risk.empty:
        future_risk = risk_df.copy()

    hours = []
    for t, group in future_risk.groupby("time"):
        wind_row = wind_df[wind_df["time"] == t]
        if wind_row.empty:
            continue

        w = wind_row.iloc[0]
        avg_risk = group["risk"].mean()
        max_risk = group["risk"].max()
        worst = group.loc[group["risk"].idxmax()]

        h = t.hour
        is_night = h >= 20 or h < 6

        classification = classify_hour(avg_risk)

        # Build reason
        reasons = []
        if classification == "recommended":
            reasons.append("Wind direction carries odour away from populated areas")
            if w["precipitation"] > 2:
                reasons.append("rainfall suppresses odour dispersion")
        elif classification == "avoid":
            reasons.append(f"Wind blowing towards {worst['neighbourhood']}")
            if is_night:
                reasons.append("night-time inversion may trap odour near ground")
            if w["wind_speed_10m"] < 1.5:
                reasons.append("calm wind allows odour to linger")
        else:
            reasons.append("Moderate risk — some neighbourhoods may be affected")

        hours.append({
            "time": t.isoformat(),
            "hour": h,
            "avg_risk": round(avg_risk, 3),
            "max_risk": round(max_risk, 3),
            "worst_neighbourhood": worst["neighbourhood"],
            "classification": classification,
            "wind_dir": round(w["wind_direction_10m"], 1),
            "wind_speed": round(w["wind_speed_10m"], 1),
            "precipitation": round(w["precipitation"], 1),
            "temperature": round(w.get("temperature_2m", 28), 1),
            "is_night": is_night,
            "reason": "; ".join(reasons),
        })

    return hours[:48]  # Cap at 48 hours


def summarise_windows(planner_data):
    """Group consecutive hours of the same classification into windows."""
    if not planner_data:
        return []

    windows = []
    current = {
        "start": planner_data[0]["time"],
        "end": planner_data[0]["time"],
        "classification": planner_data[0]["classification"],
        "hours": 1,
        "avg_risk": planner_data[0]["avg_risk"],
    }

    for h in planner_data[1:]:
        if h["classification"] == current["classification"]:
            current["end"] = h["time"]
            current["hours"] += 1
            current["avg_risk"] = (current["avg_risk"] * (current["hours"] - 1) + h["avg_risk"]) / current["hours"]
        else:
            current["avg_risk"] = round(current["avg_risk"], 3)
            windows.append(current)
            current = {
                "start": h["time"],
                "end": h["time"],
                "classification": h["classification"],
                "hours": 1,
                "avg_risk": h["avg_risk"],
            }

    current["avg_risk"] = round(current["avg_risk"], 3)
    windows.append(current)
    return windows
