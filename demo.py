"""Deterministic Demo Simulation scenarios for Dumpyard Watch.

These scripts are clearly-labelled demonstrations of how the interface behaves
under low / moderate / higher odour risk. They NEVER replace live forecast data
silently: the UI shows a DEMO badge whenever a scenario is active.

The scenario drives real model inputs (wind direction/speed, temperature, rain)
through the same uncalibrated risk model in smell.py, so the timeline colours,
plume, character and map respond exactly as they would to live data.
"""
import math

import pandas as pd

import config
import smell

SCENARIO_NAME = "Coastal wind-shift sweep (scripted)"
SCENARIO_NOTE = (
    "Scripted 48-hour scenario: wind veers through two full turns so the plume "
    "sweeps past every neighbourhood; the second turn is stronger, with a rain "
    "window and a calm spell in between. Deterministic and repeatable."
)


def _speed(i, hour):
    """Deterministic hourly wind speed (m/s) for scenario hour index i (0..47)."""
    base = 1.6 + 0.9 * math.sin(2 * math.pi * i / 12.0)
    if i >= 24:
        base += 1.8  # stronger second sweep -> higher-risk periods
    if 18 <= i <= 21:
        base = max(0.7, base * 0.35)  # calm spell -> odour lingers near source
    return round(max(0.6, min(base, 8.0)), 1)


def _rain(i):
    """Scripted rain window (mm) — used to demonstrate model factor changes."""
    if 15 <= i <= 18:
        return 6.0
    if 38 <= i <= 40:
        return 1.0
    return 0.0


def build_demo_wind(site, hours=48):
    """48 tz-aware IST hourly wind rows for the demo scenario at `site`."""
    start = smell.forecast_start()
    times = pd.date_range(start=start, periods=hours, freq="h")
    rows = []
    for i, t in enumerate(times):
        h = t.hour
        direction = (200.0 + 15.0 * i) % 360.0  # 2 full veer cycles over 48 h
        speed = _speed(i, h)
        temp = 26.5 + 5.5 * math.sin((h - 9) / 24.0 * 2 * math.pi)
        rows.append({
            "time": t,
            "wind_speed_10m": speed,
            "wind_direction_10m": round(direction, 1),
            "wind_speed_80m": round(speed * 1.35, 1),
            "wind_direction_80m": round((direction + 10) % 360, 1),
            "temperature_2m": round(temp, 1),
            "precipitation": _rain(i),
        })
    df = pd.DataFrame(rows)
    df.attrs["is_fallback"] = False
    df.attrs["is_demo"] = True
    return df


def demo_cleanup_schedule():
    """Operational cleanup windows inside the demo scenario (hour offsets 0..47).

    Cleanup progress is a DEMO operation state — independent of modelled risk.
    """
    return [
        {"start_offset": 2, "duration": 4, "activity": "waste-loading", "cleanup_gain": 0.08},
        {"start_offset": 22, "duration": 6, "activity": "excavation", "cleanup_gain": 0.20},
        {"start_offset": 30, "duration": 6, "activity": "cover-soil spreading", "cleanup_gain": 0.18},
        {"start_offset": 42, "duration": 5, "activity": "leachate handling", "cleanup_gain": 0.12},
    ]
