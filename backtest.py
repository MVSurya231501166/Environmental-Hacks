"""Run the 20-minute test: does the smoke module catch known fires, and how many false alarms?

1. Fill known_fires.csv (site, date, optional news_time_ist) from news reports.
2. python backtest.py
3. Optional false-alarm check on a month you KNOW was quiet:
   python backtest.py --quiet-site Perungudi --quiet-start 2026-07-01 --quiet-days 30
"""
import argparse
from datetime import date, timedelta

import pandas as pd

import config
import fire


def run_known_fires(path):
    fires = pd.read_csv(path)
    rows = []
    for r in fires.itertuples():
        d = date.fromisoformat(str(r.date))
        # window: the day before to the day after the reported date
        det, warns = fire.fetch_detections(r.site, d - timedelta(days=1), 3, config.HISTORY_SOURCES)
        v = fire.classify(det)
        news = pd.to_datetime(getattr(r, "news_time_ist", None), errors="coerce")
        lead = None
        if v["is_fire"] and pd.notna(news):
            lead = round((news - v["first_ist"]).total_seconds() / 3600, 1)
        rows.append({"site": r.site, "date": r.date, "detected": v["is_fire"], "pixels": v["n_pixels"],
                     "max_frp": round(v["max_frp"], 1), "first_detect_ist": v["first_ist"],
                     "lead_hours_before_news": lead})
    out = pd.DataFrame(rows)
    print("\n=== Known fires ===")
    print(out.to_string(index=False))
    print(f"\nRecall: {int(out['detected'].sum())} of {len(out)} known fires detected")
    leads = out["lead_hours_before_news"].dropna()
    if len(leads):
        print(f"Lead time over news (check each by hand): {leads.round(1).tolist()} hours")


def run_quiet(site, start, days):
    det, warns = fire.fetch_detections(site, date.fromisoformat(start), days, config.HISTORY_SOURCES)
    flagged = 0
    if not det.empty:
        for _, day_df in det.groupby(det["time_utc"].dt.date):
            if fire.classify(day_df)["is_fire"]:
                flagged += 1
    print(f"\n=== Quiet period: {site}, {start} + {days} days ===")
    print(f"Days flagged as fire: {flagged} -> about {flagged / days * 30:.1f} false alarms per month")
    print("(Only valid if no real fire happened in that period. Check the news.)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fires", default="known_fires.csv")
    ap.add_argument("--quiet-site")
    ap.add_argument("--quiet-start")
    ap.add_argument("--quiet-days", type=int, default=30)
    a = ap.parse_args()
    run_known_fires(a.fires)
    if a.quiet_site and a.quiet_start:
        run_quiet(a.quiet_site, a.quiet_start, a.quiet_days)
