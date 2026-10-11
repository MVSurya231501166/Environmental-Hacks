"""Smell module + smoke path: wind from Open-Meteo, downwind risk score, plume cone."""
import math

import pandas as pd
import requests

import config


def generate_fallback_wind(lat, lon, past_days=2, forecast_days=2):
    """Generate realistic synthetic hourly wind for Chennai area if Open-Meteo is unreachable.

    Times are tz-aware Asia/Kolkata (IST).
    """
    now = pd.Timestamp.now(tz="Asia/Kolkata").floor("h")
    start = now - pd.Timedelta(days=past_days)
    end = now + pd.Timedelta(days=forecast_days)
    times = pd.date_range(start=start, end=end, freq="h")

    rows = []
    for t in times:
        h = t.hour
        # Diurnal pattern in Chennai:
        # Daytime sea breeze: E / ESE wind ~80°-130°, 3.5 - 5.5 m/s
        # Night / early morning: land breeze ~200°-250°, 1.2 - 2.5 m/s
        if 11 <= h <= 18:
            dir_10m = 90.0 + 30.0 * math.sin((h - 11) / 7.0 * math.pi)
            spd_10m = 3.5 + 1.8 * math.sin((h - 11) / 7.0 * math.pi)
            temp = 31.0 + 3.0 * math.sin((h - 11) / 7.0 * math.pi)
        elif 6 <= h < 11:
            dir_10m = 160.0 - 70.0 * ((h - 6) / 5.0)
            spd_10m = 2.0 + 1.5 * ((h - 6) / 5.0)
            temp = 27.0 + 4.0 * ((h - 6) / 5.0)
        else:
            dir_10m = 220.0 + 15.0 * math.sin((h % 24) / 6.0)
            spd_10m = 1.5 + 0.8 * math.cos((h % 24) / 6.0)
            temp = 25.0 + 2.0 * math.cos((h % 24) / 6.0)

        rows.append({
            "time": t,
            "wind_speed_10m": round(max(0.5, spd_10m), 1),
            "wind_direction_10m": round((dir_10m + 360) % 360, 1),
            "wind_speed_80m": round(max(0.8, spd_10m * 1.35), 1),
            "wind_direction_80m": round((dir_10m + 10) % 360, 1),
            "temperature_2m": round(temp, 1),
            "precipitation": 0.0,
        })
    df = pd.DataFrame(rows)
    df.attrs["is_fallback"] = True
    return df


def get_wind(lat, lon, past_days=1, forecast_days=3):
    """Hourly wind. Direction is where the wind blows FROM. Times are IST."""
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "hourly": ("wind_speed_10m,wind_direction_10m,wind_speed_80m,"
                       "wind_direction_80m,temperature_2m,precipitation"),
            "wind_speed_unit": "ms", "timezone": "Asia/Kolkata",
            "past_days": past_days, "forecast_days": forecast_days,
        }, timeout=4)
        r.raise_for_status()
        df = pd.DataFrame(r.json()["hourly"])
        # Open-Meteo returns naive local times; timezone param guarantees they are IST.
        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Kolkata")
        df.attrs["is_fallback"] = False
        return df
    except Exception as e:
        df = generate_fallback_wind(lat, lon, past_days, forecast_days)
        df.attrs["error"] = str(e)
        return df



def bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def dist_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(a))


def smell_risk(dump, home, wind_from, speed, hour, rain_mm):
    """0..1 score. UNCALIBRATED: every number here is a starting guess."""
    plume_dir = (wind_from + 180) % 360              # where the air is going
    b = bearing(*dump, *home)                        # where the home is
    diff = abs((plume_dir - b + 180) % 360 - 180)    # 0 = directly downwind
    angle = math.exp(-(diff / 30) ** 2)
    near = math.exp(-dist_km(*dump, *home) / 3)
    calm = 0.5 if speed < 1 else 1.0
    night = 1.3 if (hour >= 20 or hour < 6) else 1.0
    wet = 1.2 if rain_mm > 5 else 1.0
    return min(1.0, angle * near * calm * night * wet)


def risk_label(score):
    if score >= 0.5:
        return "High"
    if score >= 0.2:
        return "Moderate"
    return "Low"


def forecast_start():
    """Canonical forecast start: the current hour, tz-aware IST."""
    return pd.Timestamp.now(tz="Asia/Kolkata").floor("h")


def forecast_window(df, start=None, hours=48):
    """Consecutive hourly rows [start, start+hours-1]; start defaults to the current hour (IST)."""
    start = forecast_start() if start is None else start
    end = start + pd.Timedelta(hours=hours - 1)
    out = df[(df["time"] >= start) & (df["time"] <= end)].copy()
    out = out.sort_values("time").reset_index(drop=True)
    return out


def risk_table(site, wind):
    """One row per (hour, neighbourhood)."""
    s = config.SITES[site]
    dump = (s["lat"], s["lon"])
    rows = []
    for w in wind.itertuples():
        for name, home in config.NEIGHBOURHOODS[site].items():
            score = smell_risk(dump, home, w.wind_direction_10m, w.wind_speed_10m,
                               w.time.hour, w.precipitation)
            rows.append({"time": w.time, "neighbourhood": name, "lat": home[0], "lon": home[1],
                         "risk": round(score, 3), "level": risk_label(score)})
    return pd.DataFrame(rows)


def destination(lat, lon, bearing_deg, km):
    d, b = km / 6371.0, math.radians(bearing_deg)
    p1, l1 = math.radians(lat), math.radians(lon)
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1),
                         math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


def plume_polygon(lat, lon, wind_from, speed_ms, hours=1.0, half_angle=20, min_km=2, max_km=10):
    """Rough downwind footprint (a cone), NOT a dispersion model."""
    plume_dir = (wind_from + 180) % 360
    length = min(max(speed_ms * 3.6 * hours, min_km), max_km)  # m/s * 3600 s / 1000 = km
    pts = [(lat, lon)]
    for a in range(-half_angle, half_angle + 1, 5):
        pts.append(destination(lat, lon, plume_dir + a, length))
    return pts
