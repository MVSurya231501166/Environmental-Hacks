"""Smoke module: NASA FIRMS satellite fire detections near a dump site + a simple fire/not-fire rule."""
import io
import math
from datetime import timedelta

import pandas as pd
import requests

import config

URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{source}/{bbox}/{days}/{day}"
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)
EMPTY_COLS = ["latitude", "longitude", "acq_date", "acq_time", "confidence", "frp",
              "dist_km", "conf", "time_utc", "time_ist"]


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(a))


def _bbox(site):
    s = config.SITES[site]
    dlat = s["radius_km"] / 111.0
    dlon = s["radius_km"] / (111.0 * math.cos(math.radians(s["lat"])))
    # FIRMS wants: west,south,east,north
    return f"{s['lon']-dlon:.4f},{s['lat']-dlat:.4f},{s['lon']+dlon:.4f},{s['lat']+dlat:.4f}"


def _get(source, bbox, start, days, key):
    url = URL.format(key=key, source=source, bbox=bbox, days=days, day=start.isoformat())
    text = requests.get(url, timeout=60).text.strip()
    if not text.startswith("latitude"):  # errors come back as plain text
        raise RuntimeError(f"{source}: {text[:150]}")
    return pd.read_csv(io.StringIO(text))


def fetch_detections(site, start, days=1, sources=None):
    """Return (detections_df, warnings). `start` is a UTC date. Covers start .. start+days-1."""
    key = config.FIRMS_MAP_KEY
    if not key:
        return pd.DataFrame(columns=EMPTY_COLS), ["FIRMS_MAP_KEY is not set."]
    bbox = _bbox(site)
    s = config.SITES[site]
    frames, warnings, ok_sources = [], [], 0
    for source in sources or config.LIVE_SOURCES:
        day, remaining, failed = start, days, False
        while remaining > 0:
            n = min(5, remaining)  # the area API serves a few days per call
            try:
                f = _get(source, bbox, day, n, key)
                if not f.empty:
                    frames.append(f)
            except Exception as e:  # one bad source should not kill the run
                warnings.append(str(e))
                failed = True
                break
            day += timedelta(days=n)
            remaining -= n
        ok_sources += 0 if failed else 1
    if ok_sources == 0:
        raise RuntimeError("All FIRMS sources failed: " + " | ".join(warnings))
    if not frames:
        return pd.DataFrame(columns=EMPTY_COLS), warnings

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=["latitude", "longitude", "acq_date", "acq_time"])
    df["dist_km"] = [haversine_km(s["lat"], s["lon"], a, b) for a, b in zip(df["latitude"], df["longitude"])]
    df = df[df["dist_km"] <= s["radius_km"]].copy()
    if df.empty:
        return pd.DataFrame(columns=EMPTY_COLS), warnings
    df["conf"] = df["confidence"].astype(str).str.lower().str[0]  # VIIRS: l / n / h
    hhmm = df["acq_time"].astype(int).astype(str).str.zfill(4)
    df["time_utc"] = pd.to_datetime(df["acq_date"].astype(str) + " " + hhmm, format="%Y-%m-%d %H%M")
    df["time_ist"] = df["time_utc"] + IST_OFFSET
    return df.sort_values("time_utc").reset_index(drop=True), warnings


def classify(df, min_pixels=3, strong_frp=10.0):
    """Fire-or-not rule. The numbers are STARTING values: tune them on your known fire dates.

    Ignore low-confidence pixels. Call it a fire if there are >= min_pixels pixels,
    or any single pixel has fire radiative power >= strong_frp (MW).
    """
    out = {"is_fire": False, "n_pixels": 0, "max_frp": 0.0,
           "first_utc": None, "first_ist": None, "reason": "no detections"}
    if df is None or df.empty:
        return out
    ok = df[df["conf"].isin(["n", "h"])]
    if ok.empty:
        out["reason"] = "only low-confidence detections"
        return out
    out["n_pixels"] = int(len(ok))
    out["max_frp"] = float(ok["frp"].max())
    out["first_utc"] = ok["time_utc"].min()
    out["first_ist"] = ok["time_ist"].min()
    if len(ok) >= min_pixels:
        out["is_fire"], out["reason"] = True, f"{len(ok)} pixels (>= {min_pixels})"
    elif out["max_frp"] >= strong_frp:
        out["is_fire"], out["reason"] = True, f"strong pixel, FRP {out['max_frp']:.1f} MW"
    else:
        out["reason"] = "too few / too weak to call a fire"
    return out


def fetch_status(site, days=2):
    """Live FIRMS query with an explicit, distinguishable outcome.

    Returns {"status": {...}, "detections": [...], "verdict": {...}} where
    status.state is one of: no_key | error | ok | ok_empty.
    """
    import datetime as _dt
    now_utc = _dt.datetime.now(_dt.timezone.utc)
    start = now_utc.date() - _dt.timedelta(days=days - 1)
    status = {
        "state": "ok",
        "site": site,
        "days": days,
        "sources": list(config.LIVE_SOURCES),
        "query_time_utc": now_utc.isoformat(timespec="seconds"),
        "range_start_utc": start.isoformat(),
        "range_end_utc": (start + _dt.timedelta(days=days - 1)).isoformat(),
        "error": None,
        "warnings": [],
    }
    if not config.FIRMS_MAP_KEY:
        status["state"] = "no_key"
        status["error"] = "FIRMS_MAP_KEY is not set. Get a free key at firms.modaps.eosdis.nasa.gov/api/map_key/."
        return {"status": status, "detections": [],
                "verdict": classify(pd.DataFrame(columns=EMPTY_COLS))}
    try:
        det, warnings = fetch_detections(site, start, days, config.LIVE_SOURCES)
    except Exception as e:
        status["state"] = "error"
        status["error"] = str(e)
        return {"status": status, "detections": [],
                "verdict": classify(pd.DataFrame(columns=EMPTY_COLS))}
    status["warnings"] = list(warnings)
    if det is None or det.empty:
        if warnings:
            status["state"] = "error"
            status["error"] = " | ".join(warnings)
            return {"status": status, "detections": [],
                    "verdict": classify(pd.DataFrame(columns=EMPTY_COLS))}
        status["state"] = "ok_empty"
    records = []
    if det is not None and not det.empty:
        for r in det.to_dict("records"):
            r = {k: (None if isinstance(v, float) and v != v else v) for k, v in r.items()}
            for k in ("time_utc", "time_ist"):
                if hasattr(r.get(k), "isoformat"):
                    r[k] = r[k].isoformat(timespec="minutes")
            records.append(r)
    verdict = classify(det)
    for k in ("first_utc", "first_ist"):
        if hasattr(verdict.get(k), "isoformat"):
            verdict[k] = verdict[k].isoformat(timespec="minutes")
    return {"status": status, "detections": records, "verdict": verdict}
