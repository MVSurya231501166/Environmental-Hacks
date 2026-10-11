"""Local HTTP bridge for Dumpyard Watch.

Streamlit's iframe host page cannot receive component values from st.iframe HTML,
so the immersive UI talks to this tiny localhost server instead:

  GET  /api/health              -> {ok: true}
  GET  /api/reports?site=NAME   -> {reports: [...]}
  POST /api/report  (JSON)      -> appends one report (deduped by client UUID)
  GET  /api/fire?site=NAME&days=N -> live NASA FIRMS re-query with rich status

Run inside the Streamlit process via start_bridge().
"""
import json
import os
import threading
from urllib.parse import urlparse, parse_qs

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pandas as pd

import config
import fire

REPORTS_PATH = os.path.join(config.DATA_DIR, "reports.csv")
REPORT_COLS = ["id", "site", "time_ist", "neighbourhood", "lat", "lon",
               "intensity", "note", "windows_open"]

_lock = threading.Lock()
_server = None


def _read_reports():
    if not os.path.exists(REPORTS_PATH):
        return pd.DataFrame(columns=REPORT_COLS)
    df = pd.read_csv(REPORTS_PATH)
    if "id" not in df.columns:  # legacy file without UUIDs
        df["id"] = ["legacy-%d" % i for i in range(len(df))]
    return df


def _append_report(payload):
    rid = str(payload.get("id") or "").strip()
    if not rid:
        return {"ok": False, "error": "missing report id"}
    with _lock:
        df = _read_reports()
        if rid in set(df["id"].astype(str)):
            return {"ok": True, "deduped": True}
        row = {
            "id": rid,
            "site": str(payload.get("site", "")),
            "time_ist": str(payload.get("time_ist", "")),
            "neighbourhood": str(payload.get("neighbourhood", "")),
            "lat": payload.get("lat"),
            "lon": payload.get("lon"),
            "intensity": int(payload.get("intensity", 0)),
            "note": str(payload.get("note", "")),
            "windows_open": bool(payload.get("windows_open", False)),
        }
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(
            REPORTS_PATH, index=False)
    return {"ok": True, "deduped": False}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep the Streamlit console clean
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == "/api/health":
            self._send(200, {"ok": True})
        elif parsed.path == "/api/reports":
            site = qs.get("site", [""])[0]
            df = _read_reports()
            if site and not df.empty:
                df = df[df["site"] == site]
            self._send(200, {"reports": df.to_dict("records")})
        elif parsed.path == "/api/fire":
            site = qs.get("site", [""])[0]
            try:
                days = max(1, min(3, int(qs.get("days", ["2"])[0])))
            except ValueError:
                days = 2
            if site not in config.SITES:
                self._send(400, {"error": f"unknown site: {site!r}"})
                return
            self._send(200, fire.fetch_status(site, days))
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/report":
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            self._send(400, {"ok": False, "error": f"bad JSON: {e}"})
            return
        self._send(200, _append_report(payload))


def start_bridge(port=0):
    """Start the bridge in a daemon thread; returns (server, actual_port)."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]
