"""Settings for Dumpyard Watch.

VERIFY every coordinate below on Google Maps before your demo. These are approximate.
"""
import os
from dotenv import load_dotenv

# Load variables from the .env file in the same directory as this script.
# override=True ensures values from .env take precedence over terminal environment.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

# Free key: https://firms.modaps.eosdis.nasa.gov/api/map_key/  (arrives by email)
FIRMS_MAP_KEY = os.environ.get("FIRMS_MAP_KEY", "")

# Optional: send alerts to a Telegram group (leave empty to skip)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Satellite sources. NRT = near real time (last ~2 months). SP = archive (older dates).
LIVE_SOURCES = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
HISTORY_SOURCES = ["VIIRS_SNPP_SP", "VIIRS_NOAA20_SP", "VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"]

# radius_km = how far from the centre point a satellite pixel still counts as "the dump".
SITES = {
    "Perungudi":   {"lat": 12.9600, "lon": 80.2400, "radius_km": 2.0},
    "Kodungaiyur": {"lat": 13.1380, "lon": 80.2560, "radius_km": 2.0},
}

# Neighbourhood centre points (approximate; verify and add your own).
NEIGHBOURHOODS = {
    "Perungudi": {
        "Perungudi": (12.9650, 80.2461),
        "Thoraipakkam": (12.9416, 80.2368),
        "Pallikaranai": (12.9347, 80.2146),
        "Velachery": (12.9791, 80.2209),
        "Kottivakkam": (12.9696, 80.2589),
        "Thiruvanmiyur": (12.9830, 80.2594),
        "Sholinganallur": (12.9010, 80.2279),
    },
    "Kodungaiyur": {
        "Kodungaiyur": (13.1290, 80.2520),
        "Vyasarpadi": (13.1170, 80.2530),
        "Perambur": (13.1160, 80.2400),
        "Madhavaram": (13.1480, 80.2310),
        "Manali": (13.1660, 80.2630),
        "Tondiarpet": (13.1260, 80.2880),
        "MKB Nagar": (13.1190, 80.2600),
    },
}
