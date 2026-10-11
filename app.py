"""Dumpyard Watch: immersive environmental monitoring UI.

Combines satellite smoke alerts, wind-based smell-risk mapping, resident reports,
operator planning, and an animated environmental scene.

All original business logic from config, smell, fire, alerts is preserved.
The UI is a custom HTML/JS scene rendered via st.iframe; it talks back through
a localhost bridge (bridge.py) for report persistence and live FIRMS re-queries.

Run:  streamlit run app.py
"""
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import alerts
import bridge
import config
import demo
import fire
import planner
import scene
import smell

IST = ZoneInfo("Asia/Kolkata")
REPORTS = os.path.join(config.DATA_DIR, "reports.csv")

st.set_page_config(
    page_title="Dumpyard Watch",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit chrome for immersive experience
st.markdown("""
<style>
    /* Hide Streamlit default elements for immersive view */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {display: none;}
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    .stMainBlockContainer {
        padding: 0 !important;
        max-width: 100% !important;
    }
    iframe {
        border: none !important;
    }
    /* Remove any top padding/margin */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---- LOCALHOST BRIDGE (report saving + live FIRMS re-queries from the UI) ----
@st.cache_resource
def _start_bridge():
    return bridge.start_bridge()


_bridge_server, BRIDGE_PORT = _start_bridge()

# ---- SIDEBAR (collapsed by default for immersive view) ----
site = st.sidebar.selectbox("Default dump site (UI can switch)", list(config.SITES))

if not config.FIRMS_MAP_KEY:
    st.sidebar.warning("FIRMS_MAP_KEY not set: satellite smoke detection unavailable.")

st.sidebar.markdown("---")
st.sidebar.markdown("**Dumpyard Watch**")
st.sidebar.markdown(
    "Smoke is detected from satellites. Smell is a wind-based risk estimate "
    "(pilot, not validated) that resident reports will calibrate."
)
st.sidebar.markdown("---")
days = st.sidebar.slider("Satellite look-back (days)", 1, 3, 2)


# ---- LOAD DATA (both sites, live + demo) ----
@st.cache_data(ttl=1800, show_spinner="Fetching wind forecast…")
def load_wind(lat, lon):
    return smell.get_wind(lat, lon)


@st.cache_data(ttl=600, show_spinner="Querying NASA FIRMS…")
def load_fire_status(site_name, days):
    return fire.fetch_status(site_name, days)


def iso_records(df):
    """DataFrame -> JSON-safe list with tz-aware ISO timestamps."""
    out = []
    for r in df.to_dict("records"):
        for k, v in r.items():
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
            elif isinstance(v, float) and v != v:
                r[k] = None
        out.append(r)
    return out


sites_data = {}
warnings = []
for sname, scfg in config.SITES.items():
    try:
        wind = load_wind(scfg["lat"], scfg["lon"])
    except Exception as e:
        st.error(f"Could not load wind data for {sname}: {e}")
        wind = smell.generate_fallback_wind(scfg["lat"], scfg["lon"], past_days=1, forecast_days=3)
        warnings.append(f"{sname}: wind fetch failed ({e}); using fallback estimate.")
    is_fallback = bool(wind.attrs.get("is_fallback", False))

    live_wind = smell.forecast_window(wind)
    live_risk = smell.risk_table(sname, live_wind)

    demo_wind = demo.build_demo_wind(sname)
    demo_risk = smell.risk_table(sname, demo_wind)

    try:
        fire_payload = load_fire_status(sname, days)
    except Exception as e:
        fire_payload = {
            "status": {"state": "error", "site": sname, "error": str(e),
                       "query_time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "days": days, "sources": config.LIVE_SOURCES,
                       "range_start_utc": None, "range_end_utc": None, "warnings": []},
            "detections": [],
            "verdict": {"is_fire": False, "n_pixels": 0, "max_frp": 0, "reason": "satellite data unavailable",
                        "first_utc": None, "first_ist": None},
        }

    # Log + alert when a real fire signal shows up (original behaviour preserved)
    verdict = fire_payload.get("verdict") or {}
    if verdict.get("is_fire"):
        now_row = live_risk[live_risk["time"] == live_wind["time"].iloc[0]]
        downwind = list(now_row.sort_values("risk", ascending=False).head(3)["neighbourhood"])
        try:
            alert_verdict = dict(verdict)
            if isinstance(alert_verdict.get("first_ist"), str):
                alert_verdict["first_ist"] = datetime.fromisoformat(alert_verdict["first_ist"])
            alerts.log_alert(sname, alert_verdict, alerts.message(sname, alert_verdict, downwind))
        except Exception:
            pass

    sites_data[sname] = {
        "config": scfg,
        "neighbourhoods": {name: list(coords) for name, coords in config.NEIGHBOURHOODS[sname].items()},
        "live": {
            "is_fallback": is_fallback,
            "wind": iso_records(live_wind),
            "risk": iso_records(live_risk),
            "planner": planner.build_planner_data(live_risk, live_wind, sname),
            "planner_windows": planner.summarise_windows(
                planner.build_planner_data(live_risk, live_wind, sname)),
        },
        "demo": {
            "wind": iso_records(demo_wind),
            "risk": iso_records(demo_risk),
            "planner": planner.build_planner_data(demo_risk, demo_wind, sname),
            "planner_windows": planner.summarise_windows(
                planner.build_planner_data(demo_risk, demo_wind, sname)),
        },
        "fire": fire_payload,
    }

# Load existing reports (all sites; UI filters)
reports_list = []
if os.path.exists(REPORTS):
    try:
        rep_df = bridge._read_reports()
        if not rep_df.empty:
            reports_list = rep_df.to_dict("records")
    except Exception:
        pass

app_data = {
    "generated_at_ist": datetime.now(IST).isoformat(timespec="seconds"),
    "forecast_start": smell.forecast_start().isoformat(),
    "bridge_port": BRIDGE_PORT,
    "default_site": site,
    "sites": sites_data,
    "satellite_days": days,
    "reports": reports_list,
    "demo_scenario": {
        "name": demo.SCENARIO_NAME,
        "note": demo.SCENARIO_NOTE,
        "cleanup_schedule": demo.demo_cleanup_schedule(),
    },
    "data_warnings": warnings,
}

# ---- RENDER IMMERSIVE UI ----
html_content = scene.generate_scene_html(app_data)
st.iframe(html_content, height=900)

# ---- BACKUP REPORT FORM (sidebar; same CSV + dedupe as the UI) ----
homes = config.NEIGHBOURHOODS[site]
with st.sidebar.expander("Quick Report (backup)", expanded=False):
    with st.form("smell_form_sidebar", clear_on_submit=True):
        where = st.selectbox("Your area", list(homes))
        inten = st.slider("Intensity (0=none, 4=very strong)", 0, 4, 2)
        note = st.text_input("Note (optional)")
        if st.form_submit_button("Report smell"):
            import uuid
            lat, lon = homes[where]
            res = bridge._append_report({
                "id": str(uuid.uuid4()),
                "site": site,
                "time_ist": datetime.now(IST).isoformat(timespec="seconds"),
                "neighbourhood": where,
                "lat": lat, "lon": lon,
                "intensity": inten,
                "note": note,
                "windows_open": False,
            })
            st.success("Report saved." if res.get("ok") else f"Save failed: {res.get('error')}")
            if res.get("ok"):
                st.rerun()

# ---- ALERT LOG (sidebar) ----
with st.sidebar.expander("Alert Log", expanded=False):
    log = alerts.load()
    if not log.empty:
        st.dataframe(log, use_container_width=True)
    else:
        st.info("No alerts logged yet.")
