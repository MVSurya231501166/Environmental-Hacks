"""Alert log: when a fire was flagged, when we alerted, when the corporation responded."""
import datetime as dt
import os

import pandas as pd
import requests

import config

PATH = os.path.join(config.DATA_DIR, "alerts.csv")
COLS = ["site", "first_detect_ist", "pixels", "max_frp", "alerted_ist", "responded_ist"]
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)


def load():
    if os.path.exists(PATH):
        return pd.read_csv(PATH)
    return pd.DataFrame(columns=COLS)


def message(site, verdict, downwind=None):
    text = (f"FIRE ALERT - {site} dump yard\n"
            f"Satellite heat detected from {verdict['first_ist']:%d %b %Y %H:%M} IST "
            f"({verdict['n_pixels']} pixels, max {verdict['max_frp']:.1f} MW).\n")
    if downwind:
        text += "Smoke likely towards: " + ", ".join(downwind) + ".\n"
    text += "Please send a fire crew to verify. (Source: NASA FIRMS, auto-generated.)"
    return text


def log_alert(site, verdict, text, cooldown_hours=12):
    """Add a row once per fire (skips if this site was alerted in the last `cooldown_hours`)."""
    df = load()
    now = now_ist()
    mine = df[df["site"] == site]
    if not mine.empty:
        last = pd.to_datetime(mine["alerted_ist"]).max()
        if now - last < pd.Timedelta(hours=cooldown_hours):
            return False
    row = {"site": site, "first_detect_ist": str(verdict["first_ist"])[:16],
           "pixels": verdict["n_pixels"], "max_frp": round(verdict["max_frp"], 1),
           "alerted_ist": str(now), "responded_ist": ""}
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(PATH, index=False)
    _telegram(text)
    return True


def mark_responded(site):
    df = load()
    open_rows = df[(df["site"] == site) & (df["responded_ist"].isna() | (df["responded_ist"] == ""))]
    if open_rows.empty:
        return False
    df["responded_ist"] = df["responded_ist"].astype(object)
    df.loc[open_rows.index[-1], "responded_ist"] = str(now_ist())
    df.to_csv(PATH, index=False)
    return True


def _telegram(text):
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        return
    try:
        requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": config.TELEGRAM_CHAT_ID, "text": text}, timeout=15)
    except Exception:
        pass  # never let a failed notification break the app
