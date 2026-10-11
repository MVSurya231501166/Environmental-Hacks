"""Scene generator: produces the immersive HTML/CSS/JS frontend for Dumpyard Watch.

This module generates a self-contained HTML document with:
  - Canvas-based animated landfill environment scene (risk- and cleanup-driven)
  - SVG character with expression states (comfortable / concerned / distressed)
  - Leaflet wind map with animated particles, plume cone and distance analysis
  - 48-hour IST timeline coloured by modelled risk, with Live and Demo modes
  - Interactive operator planner, resident reports (HTTP bridge persistence)
  - Evidence summary and per-site satellite (FIRMS) status panel

All data is injected from Python as JSON. No external animation services required.
"""
import json


def generate_scene_html(app_data):
    """Generate the complete immersive HTML interface.

    app_data: dict with keys:
      generated_at_ist, forecast_start, bridge_port, default_site,
      satellite_days, reports, demo_scenario{name,note,cleanup_schedule},
      data_warnings,
      sites: { name: { config{lat,lon,radius_km}, neighbourhoods{name:[lat,lon]},
              live{is_fallback, wind[], risk[], planner[], planner_windows[]},
              demo{wind[], risk[], planner[], planner_windows[]},
              fire{status, detections[], verdict} } }
    """
    data_json = json.dumps(app_data, default=str).replace("<", "\\u003c")
    script_end = "</" + "script>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dumpyard Watch — Chennai</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">{script_end}
<style>
{_get_css()}
</style>
</head>
<body>
<div id="app-root">
  <!-- Top Navigation -->
  <nav id="top-nav">
    <div class="nav-brand">
      <div class="brand-icon">
        <svg viewBox="0 0 32 32" width="28" height="28"><circle cx="16" cy="16" r="14" fill="none" stroke="url(#brandGrad)" stroke-width="2.5"/><path d="M10 20 Q16 8 22 20" fill="none" stroke="url(#brandGrad)" stroke-width="2" stroke-linecap="round"/><path d="M12 18 Q16 12 20 18" fill="none" stroke="url(#brandGrad)" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/><defs><linearGradient id="brandGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#4ade80"/><stop offset="100%" stop-color="#22d3ee"/></linearGradient></defs></svg>
      </div>
      <span class="brand-text">Dumpyard Watch</span>
      <button class="brand-site" id="site-badge" onclick="openLocationModal()" title="Change your dumpyard and neighbourhood">--</button>
      <span class="demo-chip hidden" id="nav-demo-chip">DEMO</span>
    </div>
    <div class="nav-tabs" id="nav-tabs">
      <button class="nav-tab active" data-tab="environment" onclick="switchTab('environment')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M5 21V7l7-4 7 4v14"/><path d="M9 21v-6h6v6"/></svg>
        Environment
      </button>
      <button class="nav-tab" data-tab="map" onclick="switchTab('map')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4z"/></svg>
        Wind Map
      </button>
      <button class="nav-tab" data-tab="planner" onclick="switchTab('planner')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
        Planner
      </button>
      <button class="nav-tab" data-tab="reports" onclick="switchTab('reports')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>
        Reports
      </button>
      <button class="nav-tab" data-tab="evidence" onclick="switchTab('evidence')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        Evidence
      </button>
      <button class="nav-tab" data-tab="smoke" onclick="switchTab('smoke')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/><path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"/></svg>
        Satellite
      </button>
    </div>
  </nav>

  <!-- Main Content Area -->
  <main id="main-content">
    <!-- ============ ENVIRONMENT TAB ============ -->
    <section id="tab-environment" class="tab-content active">
      <div class="env-container">
        <div class="scene-wrapper" id="scene-wrapper">
          <canvas id="scene-canvas"></canvas>
          <div id="character-container">
            <div id="character-svg-wrapper"></div>
            <div id="character-speech" class="speech-bubble"></div>
          </div>
          <div class="scene-overlay-info" id="scene-overlay-info">
            <div class="scene-metric" id="scene-user-info"></div>
            <div class="scene-metric" id="scene-wind-info"></div>
            <div class="scene-metric" id="scene-risk-info"></div>
            <div class="scene-metric" id="scene-time-info"></div>
          </div>
          <div class="demo-ribbon hidden" id="scene-demo-ribbon">DEMO SCENARIO — simulated wind and risk, not a real forecast</div>
        </div>

        <div class="timeline-container" id="timeline-container">
          <div class="timeline-header" id="timeline-header">
            <div class="mode-toggle" id="mode-toggle">
              <button class="mode-btn active" id="btn-mode-live" onclick="setMode('live')">Live forecast</button>
              <button class="mode-btn" id="btn-mode-demo" onclick="setMode('demo')">Demo scenario</button>
            </div>
            <div class="legend" id="timeline-legend">
              <span class="legend-dot recommended"></span> Lower risk
              <span class="legend-dot moderate"></span> Moderate
              <span class="legend-dot high"></span> Higher risk
              <span class="legend-note" id="legend-mode-note">Modelled odour risk, next 48 hours (IST)</span>
            </div>
            <div class="tl-time" id="tl-current-time"></div>
          </div>
          <div class="timeline-track" id="timeline-track">
            <div class="timeline-segments" id="timeline-segments"></div>
            <input type="range" id="time-slider" min="0" max="47" value="0" step="1" class="time-slider">
          </div>
          <div class="timeline-strip-labels" id="timeline-strip-labels"></div>
          <div class="timeline-controls">
            <button class="tl-btn" id="btn-play" onclick="togglePlayback()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
            </button>
            <span class="tl-now-chip" id="tl-now-chip"></span>
            <span class="legend-note">Timeline colour = highest modelled risk across all neighbourhoods that hour.</span>
          </div>
        </div>

        <div class="condition-cards" id="condition-cards">
          <div class="cond-card" id="card-wind">
            <div class="cond-icon" id="wind-arrow-icon">&#8599;</div>
            <div class="cond-label">Wind</div>
            <div class="cond-value" id="card-wind-val">-- m/s</div>
            <div class="cond-sub" id="card-wind-dir">from --&#176;</div>
          </div>
          <div class="cond-card" id="card-risk">
            <div class="cond-icon">&#9888;</div>
            <div class="cond-label">Risk for you</div>
            <div class="cond-value" id="card-risk-val">--</div>
            <div class="cond-sub" id="card-risk-area">--</div>
          </div>
          <div class="cond-card" id="card-temp">
            <div class="cond-icon">&#127777;</div>
            <div class="cond-label">Temperature</div>
            <div class="cond-value" id="card-temp-val">--&#176;C</div>
            <div class="cond-sub" id="card-rain-val">-- mm rain</div>
          </div>
          <div class="cond-card" id="card-ops">
            <div class="cond-icon">&#127959;</div>
            <div class="cond-label">Operations</div>
            <div class="cond-value" id="card-ops-val">--</div>
            <div class="cond-sub" id="card-ops-sub">--</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============ MAP TAB ============ -->
    <section id="tab-map" class="tab-content">
      <div class="map-container">
        <div id="wind-map" class="wind-map"></div>
        <canvas id="wind-canvas" class="wind-canvas"></canvas>
        <div class="map-controls" id="map-controls">
          <label class="map-toggle"><input type="checkbox" id="toggle-wind" checked onchange="toggleWindLayer()"> Wind flow</label>
          <label class="map-toggle"><input type="checkbox" id="toggle-risk" checked onchange="toggleLayer('risk')"> Risk overlay</label>
          <label class="map-toggle"><input type="checkbox" id="toggle-plume" checked onchange="toggleLayer('plume')"> Odour plume</label>
          <label class="map-toggle"><input type="checkbox" id="toggle-reports" checked onchange="toggleLayer('reports')"> Reports</label>
        </div>
        <div class="map-infopanel" id="map-infopanel"></div>
        <div class="map-legend" id="map-legend">
          <div><span class="lg-swatch wind"></span> Wind direction &amp; flow (particles)</div>
          <div><span class="lg-swatch plume"></span> Modelled plume cone (estimate)</div>
          <div><span class="lg-swatch risk"></span> Modelled risk per neighbourhood</div>
          <div><span class="lg-swatch obs"></span> Resident observations (not measurements)</div>
        </div>
        <div class="map-timeline" id="map-timeline">
          <input type="range" id="map-time-slider" min="0" max="47" value="0" class="time-slider" oninput="setIdx(parseInt(this.value))">
          <span class="map-time-label" id="map-time-label"></span>
        </div>
      </div>
    </section>

    <!-- ============ PLANNER TAB ============ -->
    <section id="tab-planner" class="tab-content">
      <div class="planner-container">
        <h2 class="section-title">48-Hour Operation Planner</h2>
        <p class="section-desc">Schedule odour-heavy activities during lower-risk windows. All figures are model estimates to help prioritise work — they are not measured exposure reductions.</p>
        <div class="planner-controls" id="planner-controls">
          <div class="pc-field">
            <label>Activity</label>
            <select id="planner-activity" class="form-select" onchange="plannerActivityChanged()">
              <option value="excavation" data-dur="6">Excavation (default 6 h)</option>
              <option value="uncovering" data-dur="4">Uncovering waste (default 4 h)</option>
              <option value="leachate" data-dur="3">Leachate handling (default 3 h)</option>
            </select>
          </div>
          <div class="pc-field">
            <label>Duration (hours)</label>
            <input type="number" id="planner-duration" min="1" max="12" value="6" onchange="renderPlanner()">
          </div>
          <div class="pc-field">
            <label>Current proposed start</label>
            <select id="planner-start" class="form-select" onchange="renderPlanner()"></select>
          </div>
        </div>
        <div class="planner-grid" id="planner-grid"></div>
        <div class="planner-detail" id="planner-detail">
          <h3 id="planner-detail-title">Select a time window</h3>
          <p id="planner-detail-body">Click any hour in the timeline above to see details.</p>
        </div>
        <div class="planner-compare" id="planner-compare"></div>
        <div class="planner-alternatives" id="planner-alternatives"></div>
        <div class="planner-summary" id="planner-summary"></div>
      </div>
    </section>

    <!-- ============ REPORTS TAB ============ -->
    <section id="tab-reports" class="tab-content">
      <div class="reports-container">
        <div class="report-form-section">
          <h2 class="section-title">Report a Smell</h2>
          <p class="section-desc">Your observation helps validate the model. Reports are personal observations — not pollution measurements — and you are never obliged to report.</p>
          <div class="reports-loc-context" id="reports-loc-context"></div>
          <div class="report-character" id="report-character">
            <div id="report-char-svg"></div>
            <div class="report-char-speech" id="report-char-speech">Have you noticed any smell from the dumpyard? Your observation helps us improve predictions.</div>
          </div>
          <form id="smell-form" class="smell-form" onsubmit="submitReport(event)">
            <div class="form-group">
              <label>Your neighbourhood</label>
              <select id="report-area" class="form-select"></select>
            </div>
            <div class="form-group">
              <label>Smell intensity</label>
              <div class="intensity-scale" id="intensity-scale">
                <button type="button" class="intensity-btn" data-val="1" onclick="setIntensity(1)">1 &#128522; None</button>
                <button type="button" class="intensity-btn" data-val="2" onclick="setIntensity(2)">2 &#129300; Slight</button>
                <button type="button" class="intensity-btn" data-val="3" onclick="setIntensity(3)">3 &#128528; Moderate</button>
                <button type="button" class="intensity-btn" data-val="4" onclick="setIntensity(4)">4 &#128533; Strong</button>
                <button type="button" class="intensity-btn" data-val="5" onclick="setIntensity(5)">5 &#129322; Very Strong</button>
              </div>
              <div class="intensity-readout" id="intensity-readout"></div>
            </div>
            <div class="form-group">
              <label>Note (optional)</label>
              <input type="text" id="report-note" class="form-input" placeholder="Any additional details...">
            </div>
            <div class="form-group">
              <label class="window-check">
                <input type="checkbox" id="report-windows"> My windows are currently open
              </label>
            </div>
            <button type="submit" class="btn-submit" id="btn-submit-report">Submit Observation</button>
            <p class="form-note" id="report-error"></p>
            <p class="form-note">Closing/opening windows is your choice — a lower modelled risk does not guarantee clean air.</p>
            <div class="demo-obs-box hidden" id="demo-obs-box">
              <span>Demo mode: real submissions still save normally, but you can drop a fictional observation to test the UI.</span>
              <button type="button" class="btn-demo-obs" onclick="addDemoObservation()">Add DEMO observation</button>
            </div>
          </form>
        </div>
        <div class="report-history-section">
          <h3>Recent Reports</h3>
          <div id="report-list" class="report-list"></div>
          <div id="report-stats" class="report-stats"></div>
        </div>
      </div>
    </section>

    <!-- ============ EVIDENCE TAB ============ -->
    <section id="tab-evidence" class="tab-content">
      <div class="evidence-container">
        <h2 class="section-title">Evidence Summary</h2>
        <p class="section-desc">Generate a timestamped evidence pack suitable for municipal authorities, TNPCB, and NGT documentation.</p>
        <div class="evidence-sections" id="evidence-sections"></div>
        <button class="btn-evidence" onclick="generateEvidence()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>
          Generate Evidence Pack
        </button>
      </div>
    </section>

    <!-- ============ SATELLITE TAB ============ -->
    <section id="tab-smoke" class="tab-content">
      <div class="smoke-container">
        <h2 class="section-title">Satellite Fire Detection</h2>
        <p class="section-desc">NASA FIRMS thermal anomalies near the selected dump. Satellite passes are intermittent — a quiet map is not a guarantee of safety. A thermal anomaly is not a confirmed fire.</p>
        <div class="sat-site-chips" id="sat-site-chips"></div>
        <div id="fire-verdict" class="fire-verdict"></div>
        <div class="sat-actions">
          <button class="btn-live-query" id="btn-live-query" onclick="runLiveFireQuery()">Re-query FIRMS now</button>
          <div class="sat-query-meta" id="sat-query-meta"></div>
        </div>
        <div id="smoke-map-container" class="smoke-map-container">
          <div id="smoke-map" class="smoke-map"></div>
          <div class="demo-ribbon hidden" id="sat-demo-ribbon">DEMO — fictional test anomaly below. It does NOT prove the live integration works.</div>
        </div>
        <div class="sat-demo-controls">
          <label class="window-check"><input type="checkbox" id="sat-demo-toggle" onchange="setSatDemo(this.checked)"> Enable satellite demo / test mode</label>
          <select id="sat-scenario" class="form-select" onchange="setSatScenario(this.value)">
            <option value="clear">Scenario: no detections (clean sky)</option>
            <option value="anomaly">Scenario: demo anomaly near dump</option>
            <option value="stale">Scenario: detection with old timestamp</option>
            <option value="error">Scenario: API failure</option>
            <option value="empty_records">Scenario: successful query, no records for site+range</option>
          </select>
        </div>
        <div id="fire-timeline" class="fire-timeline"></div>
      </div>
    </section>
  </main>

  <!-- Location modal -->
  <div class="loc-modal-overlay hidden" id="loc-modal">
    <div class="loc-modal">
      <h3>Where are you watching from?</h3>
      <p class="loc-intro">Choose the dump you care about and your neighbourhood. This only changes what <em>you</em> see — the model recomputes distance and downwind impact for your selection. Nothing precise is stored: only the names you pick.</p>
      <div class="loc-section">
        <label class="loc-label">Dumpyard</label>
        <div class="loc-site-chips" id="loc-site-chips"></div>
      </div>
      <div class="loc-section">
        <label class="loc-label">Your neighbourhood</label>
        <input type="text" id="loc-search" class="form-input" placeholder="Search Chennai localities..." oninput="renderLocList()">
        <div class="loc-list" id="loc-list"></div>
      </div>
      <div class="loc-section loc-geo">
        <p class="geo-explain">You may instead share your approximate browser location once, so we can suggest the nearest supported locality. We never store the precise coordinates — only the neighbourhood name it maps to.</p>
        <button type="button" class="btn-geo" id="btn-geolocate" onclick="requestGeolocation()">Use my browser location</button>
        <div class="geo-status" id="geo-status"></div>
      </div>
      <div class="loc-actions">
        <button type="button" class="btn-submit" id="btn-loc-save" onclick="saveLocation()">Save selection</button>
        <button type="button" class="btn-skip" id="btn-loc-skip" onclick="skipLocation()">Keep defaults</button>
        <button type="button" class="btn-skip" id="btn-loc-close" onclick="closeLocationModal()">Close</button>
      </div>
    </div>
  </div>

  <!-- Fallback Banner -->
  <div id="fallback-banner" class="fallback-banner hidden">
    &#9888; Using estimated wind patterns — live weather service unreachable. Maps remain functional with synthetic data.
  </div>
</div>

<script>
{_get_js()}

// Inject data and initialise
const APP_DATA = {data_json};
document.addEventListener('DOMContentLoaded', () => initApp(APP_DATA));
{script_end}
</body>
</html>"""


def _get_css():
    return r"""

/* ============================================
   DUMPYARD WATCH — IMMERSIVE UI STYLES
   ============================================ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg-primary: #0f1419;
  --bg-secondary: #1a2332;
  --bg-card: #1e2d3d;
  --bg-card-hover: #243447;
  --text-primary: #e8edf2;
  --text-secondary: #8899aa;
  --text-muted: #5c6e7e;
  --accent-green: #4ade80;
  --accent-amber: #fbbf24;
  --accent-red: #ef4444;
  --accent-cyan: #22d3ee;
  --accent-blue: #3b82f6;
  --border-color: #2a3a4a;
  --glass-bg: rgba(15, 20, 25, 0.85);
  --glass-border: rgba(255,255,255,0.08);
  --radius: 12px;
  --radius-sm: 8px;
  --radius-xs: 6px;
  --shadow: 0 4px 24px rgba(0,0,0,0.3);
  --shadow-lg: 0 8px 48px rgba(0,0,0,0.4);
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

html, body { 
  height: 100%; overflow: hidden;
  font-family: var(--font); background: var(--bg-primary); color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}

#app-root { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

/* ---------- NAV ---------- */
#top-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 56px; min-height: 56px;
  background: var(--glass-bg); border-bottom: 1px solid var(--glass-border);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  z-index: 100;
}
.nav-brand { display: flex; align-items: center; gap: 10px; }
.brand-icon { display: flex; align-items: center; }
.brand-text { font-weight: 700; font-size: 16px; letter-spacing: -0.3px; }
.brand-site {
  font-size: 11px; font-weight: 600; padding: 3px 10px;
  background: rgba(74, 222, 128, 0.15); color: var(--accent-green);
  border-radius: 20px; border: 1px solid rgba(74, 222, 128, 0.2);
}
.nav-tabs { display: flex; gap: 2px; }
.nav-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px; border: none; background: transparent;
  color: var(--text-secondary); font-family: var(--font); font-size: 13px; font-weight: 500;
  border-radius: var(--radius-sm); cursor: pointer; transition: var(--transition);
  white-space: nowrap;
}
.nav-tab:hover { background: rgba(255,255,255,0.06); color: var(--text-primary); }
.nav-tab.active { background: rgba(74, 222, 128, 0.12); color: var(--accent-green); }
.nav-tab svg { opacity: 0.7; }
.nav-tab.active svg { opacity: 1; }

/* ---------- MAIN ---------- */
#main-content { flex: 1; overflow-y: auto; overflow-x: hidden; }
.tab-content { display: none; height: 100%; }
.tab-content.active { display: flex; flex-direction: column; }

/* ---------- ENVIRONMENT ---------- */
.env-container { display: flex; flex-direction: column; height: 100%; }
.scene-wrapper {
  position: relative; flex: 1; min-height: 300px; overflow: hidden;
  background: #1a2332;
}
#scene-canvas { width: 100%; height: 100%; display: block; }
#character-container {
  position: absolute; bottom: 20px; right: 30px;
  display: flex; flex-direction: row-reverse; align-items: flex-end; gap: 12px;
  z-index: 10; pointer-events: none;
}
#character-svg-wrapper {
  width: 100px; height: 140px;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,0.4));
}
/* Idle motion lives INSIDE the SVG so the character's position never shifts.
   No transform on the wrapper itself — that caused visible jitter. */
#character-svg-wrapper svg { display: block; width: 100%; height: 100%; animation: charFade 0.5s ease; }
.char-head { transform-box: fill-box; transform-origin: 50% 90%; animation: charHeadSway 7s ease-in-out infinite; }
.char-body { transform-box: fill-box; transform-origin: 50% 100%; animation: charBreathe 4s ease-in-out infinite; }
.char-eyes { transform-box: fill-box; transform-origin: 50% 50%; animation: charBlink 6.5s ease-in-out infinite; }
@keyframes charBreathe { 0%, 100% { transform: scaleY(1); } 50% { transform: scaleY(1.015); } }
@keyframes charHeadSway { 0%, 100% { transform: rotate(0deg); } 35% { transform: rotate(1.4deg); } 70% { transform: rotate(-1.1deg); } }
@keyframes charBlink { 0%, 91%, 100% { transform: scaleY(1); } 94%, 96.5% { transform: scaleY(0.12); } }
@keyframes charFade { from { opacity: 0.35; } to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) {
  #character-svg-wrapper svg, .char-head, .char-body, .char-eyes { animation: none; }
}
.speech-bubble {
  max-width: 250px; padding: 12px 16px;
  background: var(--glass-bg); border: 1px solid var(--glass-border);
  border-radius: 16px 16px 4px 16px; backdrop-filter: blur(12px);
  font-size: 13px; line-height: 1.5; color: var(--text-primary);
  pointer-events: auto; opacity: 0; transform: translateY(10px);
  transition: opacity 0.4s, transform 0.4s;
}
.speech-bubble.visible { opacity: 1; transform: translateY(0); }

.scene-overlay-info {
  position: absolute; top: 16px; right: 16px;
  display: flex; flex-direction: column; gap: 8px; z-index: 10;
}
.scene-metric {
  padding: 8px 14px; background: var(--glass-bg);
  border: 1px solid var(--glass-border); border-radius: var(--radius-sm);
  backdrop-filter: blur(12px); font-size: 12px; font-weight: 500;
  color: var(--text-primary); white-space: nowrap;
}

/* ---------- TIMELINE ---------- */
.timeline-container {
  padding: 12px 20px 8px; background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}
.timeline-label { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.timeline-track { position: relative; }
.time-slider {
  width: 100%; height: 6px; -webkit-appearance: none; appearance: none;
  background: linear-gradient(90deg, var(--accent-green) 0%, var(--accent-amber) 50%, var(--accent-red) 100%);
  border-radius: 3px; outline: none; cursor: pointer;
}
.time-slider::-webkit-slider-thumb {
  -webkit-appearance: none; width: 18px; height: 18px;
  background: white; border-radius: 50%; cursor: grab;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.time-slider::-moz-range-thumb {
  width: 18px; height: 18px;
  background: white; border-radius: 50%; cursor: grab;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3); border: none;
}
.timeline-markers { display: flex; justify-content: space-between; margin-top: 4px; }
.timeline-controls { display: flex; align-items: center; gap: 12px; margin-top: 6px; }
.tl-btn {
  width: 32px; height: 32px; border: none; border-radius: 50%;
  background: rgba(74, 222, 128, 0.15); color: var(--accent-green);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: var(--transition);
}
.tl-btn:hover { background: rgba(74, 222, 128, 0.25); }
.tl-btn.playing { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
.tl-time { font-size: 13px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); }
.timeline-legend { margin-left: auto; display: flex; align-items: center; gap: 10px; font-size: 11px; color: var(--text-secondary); }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 3px; }
.legend-dot.recommended { background: var(--accent-green); }
.legend-dot.moderate { background: var(--accent-amber); }
.legend-dot.high { background: var(--accent-red); }

/* ---------- CONDITION CARDS ---------- */
.condition-cards {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  padding: 12px 20px 16px; background: var(--bg-secondary);
}
.cond-card {
  padding: 14px 16px; background: var(--bg-card);
  border: 1px solid var(--border-color); border-radius: var(--radius);
  transition: var(--transition);
}
.cond-card:hover { background: var(--bg-card-hover); border-color: rgba(74, 222, 128, 0.2); }
.cond-icon { font-size: 20px; margin-bottom: 6px; }
.cond-label { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.cond-value { font-size: 22px; font-weight: 700; margin-top: 4px; }
.cond-sub { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* ---------- MAP ---------- */
.map-container { position: relative; flex: 1; height: 100%; }
.wind-map { width: 100%; height: 100%; z-index: 1; }
.wind-canvas {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 2; pointer-events: none;
}
.map-controls {
  position: absolute; bottom: 96px; right: 12px; z-index: 1000;
  display: flex; flex-direction: column; gap: 6px;
  background: var(--glass-bg); border: 1px solid var(--glass-border);
  border-radius: var(--radius-sm); padding: 10px 14px;
  backdrop-filter: blur(12px);
}
.map-toggle { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-primary); cursor: pointer; }
.map-toggle input { accent-color: var(--accent-green); }
.map-timeline {
  position: absolute; bottom: 16px; left: 16px; right: 16px; z-index: 1000;
  background: var(--glass-bg); border: 1px solid var(--glass-border);
  border-radius: var(--radius); padding: 12px 16px;
  backdrop-filter: blur(12px); display: flex; align-items: center; gap: 12px;
}
.map-time-label { font-size: 12px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); white-space: nowrap; min-width: 140px; }

/* ---------- PLANNER ---------- */
.planner-container { padding: 24px; overflow-y: auto; max-height: 100%; }
.section-title { font-size: 24px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.5px; }
.section-desc { font-size: 14px; color: var(--text-secondary); margin-bottom: 20px; max-width: 700px; line-height: 1.6; }
.planner-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(52px, 1fr)); gap: 4px;
  margin-bottom: 20px;
}
.planner-cell {
  aspect-ratio: 1; border-radius: var(--radius-xs);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 600; cursor: pointer;
  transition: var(--transition); border: 2px solid transparent;
}
.planner-cell:hover { transform: scale(1.1); z-index: 2; }
.planner-cell.selected { border-color: white; box-shadow: 0 0 0 2px rgba(255,255,255,0.3); }
.planner-cell.recommended { background: rgba(74, 222, 128, 0.2); color: var(--accent-green); }
.planner-cell.moderate { background: rgba(251, 191, 36, 0.2); color: var(--accent-amber); }
.planner-cell.avoid { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
.planner-detail {
  padding: 20px; background: var(--bg-card); border-radius: var(--radius);
  border: 1px solid var(--border-color); margin-bottom: 20px;
}
.planner-detail h3 { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
.planner-detail p { font-size: 14px; color: var(--text-secondary); line-height: 1.6; }
.planner-summary { padding: 16px; background: rgba(74, 222, 128, 0.08); border-radius: var(--radius); border: 1px solid rgba(74, 222, 128, 0.15); }

/* ---------- REPORTS ---------- */
.reports-container { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; padding: 24px; overflow-y: auto; max-height: 100%; }
.report-form-section, .report-history-section { min-width: 0; }
.report-character { display: flex; align-items: flex-end; gap: 12px; margin-bottom: 20px; padding: 16px; background: var(--bg-card); border-radius: var(--radius); }
#report-char-svg { width: 60px; height: 80px; flex-shrink: 0; }
.report-char-speech { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.smell-form { display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.form-select, .form-input {
  padding: 10px 14px; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); color: var(--text-primary); font-family: var(--font);
  font-size: 14px; outline: none; transition: var(--transition);
}
.form-select:focus, .form-input:focus { border-color: var(--accent-green); }
.intensity-scale { display: flex; gap: 6px; flex-wrap: wrap; }
.intensity-btn {
  padding: 8px 12px; border: 1px solid var(--border-color);
  background: var(--bg-card); border-radius: var(--radius-sm);
  color: var(--text-secondary); font-size: 12px; cursor: pointer;
  transition: var(--transition); font-family: var(--font);
}
.intensity-btn:hover { border-color: var(--accent-amber); }
.intensity-btn.selected { border-color: var(--accent-green); background: rgba(74,222,128,0.12); color: var(--accent-green); }
.window-check { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; color: var(--text-primary); text-transform: none; font-weight: 400; letter-spacing: normal; }
.btn-submit {
  padding: 12px 24px; background: linear-gradient(135deg, var(--accent-green), #22c55e);
  border: none; border-radius: var(--radius-sm); color: #0f1419;
  font-weight: 700; font-size: 14px; cursor: pointer; transition: var(--transition);
  font-family: var(--font);
}
.btn-submit:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(74, 222, 128, 0.3); }
.form-note { font-size: 11px; color: var(--text-muted); line-height: 1.5; font-style: italic; }
.report-list { display: flex; flex-direction: column; gap: 8px; max-height: 400px; overflow-y: auto; }
.report-item {
  padding: 12px 16px; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center;
}
.report-item-left { display: flex; flex-direction: column; gap: 2px; }
.report-item-area { font-size: 13px; font-weight: 600; }
.report-item-time { font-size: 11px; color: var(--text-muted); }
.report-item-intensity { font-size: 18px; font-weight: 700; }
.report-stats { margin-top: 16px; padding: 16px; background: var(--bg-card); border-radius: var(--radius); }

/* ---------- EVIDENCE ---------- */
.evidence-container { padding: 24px; overflow-y: auto; max-height: 100%; }
.evidence-sections { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }
.evidence-block {
  padding: 20px; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius);
}
.evidence-block h4 { font-size: 14px; font-weight: 700; margin-bottom: 8px; color: var(--accent-cyan); }
.evidence-block p, .evidence-block li { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.evidence-block ul { list-style: none; padding: 0; }
.evidence-block li::before { content: "• "; color: var(--accent-green); }
.btn-evidence {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 24px; background: var(--bg-card); border: 1px solid var(--accent-cyan);
  border-radius: var(--radius-sm); color: var(--accent-cyan);
  font-weight: 600; font-size: 14px; cursor: pointer; transition: var(--transition);
  font-family: var(--font);
}
.btn-evidence:hover { background: rgba(34,211,238,0.1); }

/* ---------- SMOKE ---------- */
.smoke-container { padding: 24px; overflow-y: auto; max-height: 100%; display: flex; flex-direction: column; }
.fire-verdict { padding: 16px; border-radius: var(--radius); margin-bottom: 16px; }
.fire-verdict.fire { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3); }
.fire-verdict.clear { background: rgba(74,222,128,0.08); border: 1px solid rgba(74,222,128,0.15); }
.smoke-map-container { flex: 1; min-height: 350px; border-radius: var(--radius); overflow: hidden; margin-bottom: 16px; }
.smoke-map { width: 100%; height: 100%; min-height: 350px; }
.fire-timeline { display: flex; flex-direction: column; gap: 8px; }

/* ---------- FALLBACK ---------- */
.fallback-banner {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 10px 20px; background: rgba(251,191,36,0.15);
  border-top: 1px solid rgba(251,191,36,0.3); color: var(--accent-amber);
  font-size: 12px; text-align: center; z-index: 200;
}
.hidden { display: none !important; }

/* ---------- SCROLLBAR ---------- */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ---------- RESPONSIVE ---------- */
@media (max-width: 900px) {
  .condition-cards { grid-template-columns: repeat(2, 1fr); }
  .reports-container { grid-template-columns: 1fr; }
  .nav-tabs { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .nav-tab span { display: none; }
}
@media (max-width: 600px) {
  #top-nav { padding: 0 12px; }
  .brand-text { font-size: 14px; }
  .nav-tab { padding: 6px 10px; font-size: 12px; }
  .condition-cards { grid-template-columns: 1fr 1fr; gap: 8px; padding: 8px 12px; }
  .planner-grid { grid-template-columns: repeat(auto-fill, minmax(40px, 1fr)); }
  #character-svg-wrapper { width: 70px; height: 100px; }
  .speech-bubble { max-width: 200px; font-size: 12px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}

/* ============================================
   V2 ADDITIONS — timeline strip, demo, modals,
   infopanel, planner workflow, satellite states
   ============================================ */
#site-badge { cursor: pointer; font-family: var(--font); }
#site-badge:hover { background: rgba(74,222,128,0.25); }
.demo-chip { font-size: 10px; font-weight: 800; letter-spacing: 1px; padding: 3px 9px;
  border-radius: 20px; background: rgba(168,85,247,0.18); color: #c084fc;
  border: 1px solid rgba(168,85,247,0.45); }
.demo-ribbon { position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
  z-index: 800; background: #9333ea; color: white; font-weight: 700; font-size: 11px;
  padding: 6px 16px; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.45);
  letter-spacing: 0.4px; pointer-events: none; white-space: nowrap; }

/* Timeline v2 */
.timeline-header { display: flex; align-items: center; gap: 14px; margin-bottom: 8px; flex-wrap: wrap; }
.mode-toggle { display: flex; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); overflow: hidden; }
.mode-btn { padding: 6px 14px; border: none; background: transparent; color: var(--text-secondary);
  font-family: var(--font); font-size: 12px; font-weight: 600; cursor: pointer; transition: var(--transition); }
.mode-btn.active { background: rgba(74,222,128,0.15); color: var(--accent-green); }
.legend { display: flex; align-items: center; gap: 8px; font-size: 11px; color: var(--text-secondary); flex-wrap: wrap; }
.legend-note { font-size: 10.5px; color: var(--text-muted); }
.tl-now-chip { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 12px;
  background: rgba(34,211,238,0.14); color: var(--accent-cyan); border: 1px solid rgba(34,211,238,0.3); }
.timeline-track { position: relative; height: 26px; }
.timeline-segments { position: absolute; inset: 0; display: flex; border-radius: 7px;
  overflow: hidden; border: 1px solid var(--border-color); }
.tseg { flex: 1 1 0; cursor: pointer; border-right: 1px solid rgba(0,0,0,0.3); transition: background 0.35s; }
.tseg:last-child { border-right: none; }
.tseg.recommended { background: rgba(74,222,128,0.6); }
.tseg.moderate { background: rgba(251,191,36,0.6); }
.tseg.high { background: rgba(239,68,68,0.65); }
.tseg.selected { box-shadow: inset 0 0 0 2px white; z-index: 2; }
.timeline-track .time-slider { position: absolute; inset: 0; width: 100%; height: 26px;
  background: transparent; z-index: 6; -webkit-appearance: none; appearance: none; border-radius: 7px; }
.timeline-track .time-slider::-webkit-slider-runnable-track { background: transparent; height: 26px; }
.timeline-track .time-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 10px; height: 26px;
  background: rgba(255,255,255,0.92); border-radius: 3px; cursor: grab; box-shadow: 0 0 8px rgba(0,0,0,0.6); margin-top: 0; }
.timeline-track .time-slider::-moz-range-thumb { width: 10px; height: 26px; background: rgba(255,255,255,0.92);
  border-radius: 3px; cursor: grab; border: none; }
.timeline-strip-labels { position: relative; height: 15px; margin-top: 3px; }
.strip-label { position: absolute; transform: translateX(-50%); font-size: 9.5px;
  color: var(--text-muted); white-space: nowrap; font-family: var(--font-mono); }
.map-timeline .time-slider { background: var(--border-color); }

/* Wind map v2 panels */
#map-infopanel { position: absolute; top: 12px; right: 12px; z-index: 620; width: 272px;
  background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: var(--radius-sm);
  padding: 12px 14px; backdrop-filter: blur(12px); font-size: 12px; box-shadow: var(--shadow); }
.infopanel-title { font-size: 11px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;
  letter-spacing: 0.6px; margin-bottom: 8px; }
.infopanel-row { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 4px; color: var(--text-secondary); }
.infopanel-row b { color: var(--text-primary); font-weight: 600; }
.impact-badge { display: inline-block; margin: 8px 0 4px; padding: 5px 10px; border-radius: 7px;
  font-weight: 700; font-size: 11px; }
.impact-badge.downwind-high { background: rgba(239,68,68,0.2); color: #fca5a5; }
.impact-badge.downwind-mod { background: rgba(251,191,36,0.18); color: #fcd34d; }
.impact-badge.away { background: rgba(74,222,128,0.15); color: #86efac; }
.impact-badge.uncertain { background: rgba(100,116,139,0.25); color: #cbd5e1; }
.infopanel-note { font-size: 10.5px; color: var(--text-muted); margin-top: 6px; line-height: 1.5; }
.map-legend { position: absolute; bottom: 58px; left: 12px; z-index: 620; background: var(--glass-bg);
  border: 1px solid var(--glass-border); border-radius: var(--radius-sm); padding: 10px 12px;
  font-size: 11px; color: var(--text-secondary); display: flex; flex-direction: column; gap: 5px;
  backdrop-filter: blur(12px); }
.lg-swatch { display: inline-block; width: 15px; height: 8px; border-radius: 2px; margin-right: 7px; vertical-align: middle; }
.lg-swatch.wind { background: linear-gradient(90deg, #93c5fd, rgba(147,197,253,0.1)); }
.lg-swatch.plume { background: rgba(251,191,36,0.45); border: 1px solid rgba(251,191,36,0.7); }
.lg-swatch.risk { background: radial-gradient(circle, #ef4444, #fbbf24); }
.lg-swatch.obs { background: #a855f7; }

/* Planner v2 */
.planner-controls { display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.pc-field { display: flex; flex-direction: column; gap: 4px; min-width: 190px; }
.pc-field label { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.4px; }
.planner-cell.ops-on { box-shadow: inset 0 0 0 2px var(--accent-cyan); }
.planner-compare, .planner-alternatives { margin-top: 16px; padding: 16px; background: var(--bg-card);
  border: 1px solid var(--border-color); border-radius: var(--radius); }
.cmp-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
.cmp-table th, .cmp-table td { padding: 7px 10px; text-align: left; border-bottom: 1px solid var(--border-color); }
.cmp-table th { color: var(--text-muted); font-size: 11px; text-transform: uppercase; }
.delta-good { color: var(--accent-green); font-weight: 700; }
.delta-bad { color: var(--accent-red); font-weight: 700; }
.delta-neutral { color: var(--text-secondary); font-weight: 700; }
.alt-btn { margin: 6px 8px 0 0; padding: 7px 12px; border-radius: 8px; border: 1px solid rgba(34,211,238,0.35);
  background: rgba(34,211,238,0.1); color: var(--accent-cyan); font-size: 12px; font-weight: 600; cursor: pointer; }
.alt-btn:hover { background: rgba(34,211,238,0.2); }
.btn-apply-ops { margin-top: 10px; padding: 9px 16px; border-radius: 8px; border: none;
  background: var(--accent-green); color: #06281a; font-weight: 700; font-size: 13px; cursor: pointer; }
.btn-apply-ops:hover { filter: brightness(1.1); }

/* Reports v2 */
.intensity-readout { margin-top: 8px; font-size: 13px; font-weight: 600; color: var(--text-primary); }
.reports-loc-context { font-size: 12.5px; color: var(--text-secondary); background: var(--bg-card);
  padding: 9px 13px; border-radius: var(--radius-sm); margin-bottom: 14px; border: 1px solid var(--border-color); }
.reports-loc-context button { background: none; border: none; color: var(--accent-cyan); cursor: pointer;
  font-size: 12px; text-decoration: underline; font-family: var(--font); }
.demo-obs-box { margin-top: 12px; padding: 10px 12px; border: 1px dashed #a855f7; border-radius: 8px;
  font-size: 12px; color: var(--text-secondary); display: flex; justify-content: space-between;
  align-items: center; gap: 12px; flex-wrap: wrap; }
.btn-demo-obs { background: rgba(168,85,247,0.18); color: #c084fc; border: 1px solid rgba(168,85,247,0.45);
  border-radius: 7px; padding: 6px 12px; cursor: pointer; font-size: 12px; font-weight: 600; }
.report-item.demo { border-style: dashed; opacity: 0.85; }
.demo-tag { font-size: 9px; background: rgba(168,85,247,0.22); color: #c084fc; padding: 2px 6px;
  border-radius: 4px; margin-left: 6px; font-weight: 800; letter-spacing: 0.5px; }
.obs-tag { font-size: 9px; background: rgba(34,211,238,0.16); color: var(--accent-cyan); padding: 2px 6px;
  border-radius: 4px; margin-left: 6px; font-weight: 700; }
.stat-bar-row { display: flex; align-items: center; gap: 8px; font-size: 11.5px; color: var(--text-secondary); margin: 3px 0; }
.stat-bar-track { flex: 1; height: 7px; background: var(--bg-card); border-radius: 4px; overflow: hidden; }
.stat-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #4ade80, #fbbf24, #ef4444); }

/* Satellite v2 */
.sat-site-chips, .loc-site-chips { display: flex; gap: 8px; margin: 6px 0 14px; flex-wrap: wrap; }
.site-chip { padding: 7px 15px; border-radius: 20px; border: 1px solid var(--border-color);
  background: var(--bg-card); color: var(--text-secondary); cursor: pointer; font-size: 13px; font-weight: 600; }
.site-chip.active { border-color: var(--accent-green); color: var(--accent-green); background: rgba(74,222,128,0.1); }
.sat-actions { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; flex-wrap: wrap; }
.btn-live-query { padding: 8px 15px; border-radius: 8px; border: 1px solid rgba(34,211,238,0.4);
  background: rgba(34,211,238,0.12); color: var(--accent-cyan); font-weight: 600; font-size: 12.5px; cursor: pointer; }
.btn-live-query:hover { background: rgba(34,211,238,0.22); }
.btn-live-query:disabled { opacity: 0.5; cursor: wait; }
.sat-query-meta { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); line-height: 1.5; }
.sat-demo-controls { display: flex; gap: 14px; align-items: center; margin: 12px 0; flex-wrap: wrap; }
#sat-scenario { min-width: 320px; }
.fire-row { display: flex; justify-content: space-between; gap: 10px; padding: 8px 11px;
  background: var(--bg-card); border-radius: 7px; margin-bottom: 6px; font-size: 12px;
  border: 1px solid var(--border-color); }
.fire-row.demo-det { border-style: dashed; border-color: rgba(168,85,247,0.5); }
.fire-row .fr-when { font-family: var(--font-mono); }
.fire-row .fr-meta { color: var(--text-muted); font-size: 11px; text-align: right; }
.smoke-map-container { position: relative; }
.fire-verdict.warn { background: rgba(251,191,36,0.12); border: 1px solid rgba(251,191,36,0.3); }
.fire-verdict.err { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); }
.fire-verdict.info { background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.3); }

/* Location modal */
.loc-modal-overlay { position: fixed; inset: 0; background: rgba(5,10,15,0.72);
  backdrop-filter: blur(4px); z-index: 3000; display: flex; align-items: center; justify-content: center; }
.loc-modal { width: min(580px, 92vw); max-height: 88vh; overflow-y: auto; background: var(--bg-secondary);
  border: 1px solid var(--border-color); border-radius: var(--radius); padding: 22px 24px; box-shadow: var(--shadow-lg); }
.loc-modal h3 { font-size: 19px; font-weight: 800; margin-bottom: 8px; }
.loc-intro { font-size: 13px; color: var(--text-secondary); margin-bottom: 14px; line-height: 1.55; }
.loc-section { margin-bottom: 14px; }
.loc-label { display: block; font-size: 11px; font-weight: 700; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.loc-list { max-height: 230px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.loc-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 13px;
  border: 1px solid var(--border-color); border-radius: 8px; background: var(--bg-card);
  cursor: pointer; font-size: 13px; color: var(--text-primary); }
.loc-item:hover { border-color: var(--accent-cyan); }
.loc-item.active { border-color: var(--accent-cyan); background: rgba(34,211,238,0.12); }
.loc-item .dist { color: var(--text-muted); font-size: 11px; font-family: var(--font-mono); }
.geo-explain { font-size: 11.5px; color: var(--text-muted); margin-bottom: 8px; line-height: 1.55; }
.btn-geo { padding: 7px 13px; background: rgba(34,211,238,0.12); color: var(--accent-cyan);
  border: 1px solid rgba(34,211,238,0.35); border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; }
.geo-status { font-size: 12px; margin-top: 8px; color: var(--text-secondary); line-height: 1.5; }
.loc-actions { display: flex; gap: 10px; margin-top: 18px; flex-wrap: wrap; }
.btn-skip { padding: 9px 15px; border-radius: 8px; border: 1px solid var(--border-color);
  background: transparent; color: var(--text-secondary); font-size: 13px; cursor: pointer; }
.btn-skip:hover { color: var(--text-primary); border-color: var(--text-muted); }
.loc-warn { font-size: 11.5px; color: var(--accent-amber); margin-top: 6px; }

@media (max-width: 900px) {
  .timeline-header { gap: 8px; }
  #map-infopanel { width: 210px; font-size: 11px; }
  .map-legend { display: none; }
  #top-nav { flex-wrap: wrap; height: auto; min-height: 56px; padding: 8px 12px; }
  .nav-tabs { overflow-x: auto; max-width: 100%; }
}
"""


def _get_js():
    return r"""

/* ============================================
   DUMPYARD WATCH — IMMERSIVE UI ENGINE v2
   Single state model, IST everywhere, live+demo.
   ============================================ */

let state = {
  site: 'Perungudi', hood: null, mode: 'live', idx: 0, locationSet: false,
  ops: null,               // applied planner schedule {start,dur,activity,isDefault}
  satDemo: false, satScenario: 'clear',
};
const LS_KEY = 'dw.state.v2', DEMO_OBS_KEY = 'dw.demoobs.v2';
const RISK_MOD = 0.2, RISK_HIGH = 0.5;

let currentTab = 'environment';
let playbackInterval = null;
let selectedIntensity = 3;
let windMap = null, smokeMap = null, mapBase = null, mapDynamic = null, satLayers = null;
let sceneCtx = null, windCanvasCtx = null;
let sceneAnimFrame = null, sceneW = 0, sceneH = 0;
let windParticles = [], sceneParticles = [];
let showWind = true;
let showLayers = { risk: true, plume: true, reports: true };
let hoursCache = {};
let lastCharExpr = null;
window.liveReports = [];

// Animated visual state (lerped) and its targets — every visual is state-driven
let vis = { risk: 0, hoodRisk: 0, cleanup: 0, downwindToUser: 0 };
let visTarget = { risk: 0, hoodRisk: 0, cleanup: 0, downwindToUser: 0 };
window.__dw = { get vis() { return vis; }, get visTarget() { return visTarget; }, get state() { return state; } };

/* ---------- IST FORMATTERS (browser-timezone independent) ---------- */
const fmtHM = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: false });
const fmtDay = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', weekday: 'short', day: 'numeric', month: 'short' });
const fmtLong = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false });
const fmtFull = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', weekday: 'long', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
function istHM(iso) { return fmtHM.format(new Date(iso)).replace(/^24:/, '00:'); }
function istHour(iso) { return parseInt(istHM(iso).slice(0, 2), 10); }
function istNowStr() { return fmtLong.format(new Date()); }

/* ---------- GEOMETRY (mirrors smell.py) ---------- */
function haversineKm(lat1, lon1, lat2, lon2) {
  const toR = Math.PI / 180;
  const p1 = lat1 * toR, p2 = lat2 * toR;
  const a = Math.sin((p2 - p1) / 2) ** 2
    + Math.cos(p1) * Math.cos(p2) * Math.sin((lon2 - lon1) * toR / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(a));
}
function bearingDeg(lat1, lon1, lat2, lon2) {
  const toR = Math.PI / 180;
  const p1 = lat1 * toR, p2 = lat2 * toR, dl = (lon2 - lon1) * toR;
  const x = Math.sin(dl) * Math.cos(p2);
  const y = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
  return (Math.atan2(x, y) * 180 / Math.PI + 360) % 360;
}
function angleDiff(a, b) { return Math.abs(((a - b) % 360 + 540) % 360 - 180); }
function toRad(deg) { return deg * Math.PI / 180; }
function destinationPoint(lat, lon, bearingDeg_, km) {
  const d = km / 6371.0, b = toRad(bearingDeg_);
  const p1 = toRad(lat), l1 = toRad(lon);
  const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(b));
  const l2 = l1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2));
  return [p2 * 180 / Math.PI, l2 * 180 / Math.PI];
}
function seededRand(n) { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }

/* ---------- DATA ACCESS ---------- */
function siteData(name) { return APP_DATA.sites[name || state.site]; }
function currentSet() { return siteData()[state.mode]; }
function hours() {
  const key = state.site + '|' + state.mode;
  if (!hoursCache[key]) hoursCache[key] = buildHours(state.site, state.mode);
  return hoursCache[key];
}
function buildHours(site, mode) {
  const d = APP_DATA.sites[site][mode];
  const wind = d.wind || [];
  const byTime = {};
  (d.risk || []).forEach(r => { (byTime[r.time] = byTime[r.time] || []).push(r); });
  const pBy = {};
  (d.planner || []).forEach(p => { pBy[p.time] = p; });
  const hoods = siteData(site).neighbourhoods;
  return wind.map(w => {
    const rs = byTime[w.time] || [];
    let maxRisk = 0, worst = null;
    rs.forEach(r => { if (r.risk > maxRisk) { maxRisk = r.risk; worst = r; } });
    const hr = state.hood && hoods[state.hood]
      ? rs.find(r => r.neighbourhood === state.hood) : null;
    return {
      time: w.time, wind: w, risks: rs, maxRisk, worst,
      hoodRisk: hr ? hr.risk : null, hoodLevel: hr ? hr.level : null,
      plumeTo: (w.wind_direction_10m + 180) % 360,
      p: pBy[w.time] || null,
    };
  });
}
function invalidateHoursCache() { hoursCache = {}; }
function bridgeUrl(path) { return 'http://127.0.0.1:' + APP_DATA.bridge_port + path; }
function uuid4() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 3 | 8);
    return v.toString(16);
  });
}
function levelOf(r) { return r >= RISK_HIGH ? 'high' : r >= RISK_MOD ? 'moderate' : 'recommended'; }
function levelWord(l) { return l === 'high' ? 'Higher' : l === 'moderate' ? 'Moderate' : 'Lower'; }
function riskColorCss(l) { return l === 'high' ? 'var(--accent-red)' : l === 'moderate' ? 'var(--accent-amber)' : 'var(--accent-green)'; }
function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

/* ---------- PERSISTENCE ---------- */
function loadState() {
  let loaded = null;
  try { loaded = JSON.parse(localStorage.getItem(LS_KEY)); } catch (e) {}
  if (loaded && loaded.site && APP_DATA.sites[loaded.site]) {
    Object.assign(state, loaded);
  } else {
    state.site = APP_DATA.default_site || Object.keys(APP_DATA.sites)[0];
  }
  const hoods = siteData().neighbourhoods;
  if (!state.hood || !hoods[state.hood]) state.hood = Object.keys(hoods)[0];
  if (typeof state.idx !== 'number' || isNaN(state.idx)) state.idx = 0;
}
function saveState() {
  try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (e) {}
}

/* ---------- TAB SWITCHING ---------- */
function switchTab(tab) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelector('[data-tab="' + tab + '"]').classList.add('active');
  currentTab = tab;
  if (tab === 'map') { initMap(); }
  if (tab === 'smoke') { initSmokeMap(); }
  if (tab === 'environment') { resizeSceneCanvas(); }
  if (tab === 'planner') { renderPlanner(); }
}

/* ---------- SITE / MODE / INDEX ---------- */
function updateSiteBadge() {
  const b = document.getElementById('site-badge');
  if (b) b.textContent = state.site + ' · ' + state.hood;
  document.title = 'Dumpyard Watch — ' + state.site;
}
function setSite(site, skipRender) {
  if (!APP_DATA.sites[site] || site === state.site) return;
  state.site = site;
  const hoods = siteData().neighbourhoods;
  if (!hoods[state.hood]) state.hood = Object.keys(hoods)[0];
  invalidateHoursCache();
  state.idx = Math.min(state.idx, Math.max(0, hours().length - 1));
  saveState();
  updateSiteBadge();
  populateReportAreaSelect();
  renderSatelliteChips();
  if (!skipRender) {
    renderTimeline();
    updateAll(state.idx);
    renderPlanner();
    renderReportList();
    renderSatellite();
    if (windMap) updateWindMap();
  }
}
function setMode(mode) {
  state.mode = mode;
  saveState();
  document.getElementById('btn-mode-live').classList.toggle('active', mode === 'live');
  document.getElementById('btn-mode-demo').classList.toggle('active', mode === 'demo');
  document.getElementById('nav-demo-chip').classList.toggle('hidden', mode !== 'demo');
  document.getElementById('scene-demo-ribbon').classList.toggle('hidden', mode !== 'demo');
  document.getElementById('demo-obs-box').classList.toggle('hidden', mode !== 'demo');
  const note = document.getElementById('legend-mode-note');
  note.textContent = mode === 'demo'
    ? 'DEMO scenario — ' + APP_DATA.demo_scenario.name + ' (deterministic, repeatable, not a real forecast)'
    : (siteData().live.is_fallback
        ? 'Estimated wind (live service unreachable) · next 48 h (IST)'
        : 'Live forecast (Open-Meteo) · next 48 h (IST)');
  state.idx = Math.min(state.idx, Math.max(0, hours().length - 1));
  renderTimeline();
  updateAll(state.idx);
  renderPlanner();
  renderReportsLocContext();
}
function setIdx(i) {
  state.idx = Math.max(0, Math.min(i, Math.max(0, hours().length - 1)));
  highlightTimeline();
  updateAll(state.idx);
}

/* ---------- INITIALISE ---------- */
function initApp(data) {
  window.liveReports = (data.reports || []).slice();
  loadState();
  updateSiteBadge();
  if (data.sites[state.site].live.is_fallback) {
    document.getElementById('fallback-banner').classList.remove('hidden');
  }
  document.getElementById('btn-mode-live').classList.toggle('active', state.mode === 'live');
  document.getElementById('btn-mode-demo').classList.toggle('active', state.mode === 'demo');
  document.getElementById('nav-demo-chip').classList.toggle('hidden', state.mode !== 'demo');
  document.getElementById('scene-demo-ribbon').classList.toggle('hidden', state.mode !== 'demo');
  document.getElementById('demo-obs-box').classList.toggle('hidden', state.mode !== 'demo');

  initScene();
  populateReportAreaSelect();
  setIntensity(3);
  renderTimeline();
  renderPlanner();
  renderReportList();
  renderReportsLocContext();
  renderSatelliteChips();
  renderSatellite();
  updateAll(state.idx);
  document.getElementById('time-slider').addEventListener('input', e => setIdx(parseInt(e.target.value, 10)));

  // Smooth visual transitions between risk/cleanup states
  setInterval(() => {
    for (const k of Object.keys(vis)) vis[k] += (visTarget[k] - vis[k]) * 0.06;
    const expr = characterExpr();
    if (expr !== lastCharExpr) renderCharacter(expr);
  }, 120);

  if (!state.locationSet) openLocationModal();
}

/* ---------- LOCATION MODAL ---------- */
let locDraft = { site: null, hood: null };

function openLocationModal() {
  locDraft.site = state.site;
  locDraft.hood = state.hood;
  document.getElementById('btn-loc-close').classList.toggle('hidden', !state.locationSet);
  document.getElementById('btn-loc-skip').classList.toggle('hidden', state.locationSet);
  document.getElementById('geo-status').textContent = '';
  renderSatelliteChips(document.getElementById('loc-site-chips'), true);
  renderLocList();
  document.getElementById('loc-modal').classList.remove('hidden');
}
function closeLocationModal() {
  document.getElementById('loc-modal').classList.add('hidden');
}
function selectLocSite(site) {
  locDraft.site = site;
  locDraft.hood = Object.keys(APP_DATA.sites[site].neighbourhoods)[0];
  renderSatelliteChips(document.getElementById('loc-site-chips'), true);
  renderLocList();
}
function renderLocList() {
  const list = document.getElementById('loc-list');
  if (!list) return;
  const q = (document.getElementById('loc-search').value || '').toLowerCase();
  const cfg = APP_DATA.sites[locDraft.site].config;
  const names = Object.keys(APP_DATA.sites[locDraft.site].neighbourhoods)
    .filter(n => n.toLowerCase().includes(q));
  list.innerHTML = '';
  names.forEach(n => {
    const coords = APP_DATA.sites[locDraft.site].neighbourhoods[n];
    const km = haversineKm(cfg.lat, cfg.lon, coords[0], coords[1]);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'loc-item' + (n === locDraft.hood ? ' active' : '');
    btn.innerHTML = '<span>' + esc(n) + '</span><span class="dist">' + km.toFixed(1) + ' km from dump</span>';
    btn.onclick = () => { locDraft.hood = n; renderLocList(); };
    list.appendChild(btn);
  });
  if (!names.length) {
    list.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:8px;">No supported locality matches that search. Pick the closest one or enter your own neighbourhood name in the Reports form. Nothing unrelated is substituted silently.</div>';
  }
}
function requestGeolocation() {
  const st = document.getElementById('geo-status');
  if (!navigator.geolocation) {
    st.textContent = 'This browser does not provide location. Pick your neighbourhood from the list instead — nothing else changes.';
    return;
  }
  st.textContent = 'Requesting browser location (only used once to suggest the nearest supported locality)...';
  navigator.geolocation.getCurrentPosition(
    pos => {
      const lat = pos.coords.latitude, lon = pos.coords.longitude;
      const hoods = APP_DATA.sites[locDraft.site].neighbourhoods;
      let best = null, bestKm = 1e9;
      Object.entries(hoods).forEach(([n, c]) => {
        const km = haversineKm(lat, lon, c[0], c[1]);
        if (km < bestKm) { bestKm = km; best = n; }
      });
      if (best && bestKm <= 12) {
        locDraft.hood = best;
        st.textContent = 'Nearest supported locality found: ' + best + ' (~' + bestKm.toFixed(1) + ' km from you). '
          + 'We map to this locality name only — your precise coordinates are not stored or sent anywhere. '
          + 'Confirm with Save, or choose another from the list.';
      } else {
        st.textContent = 'You appear to be outside the modelled areas, so no neighbourhood was preselected. '
          + 'Please pick one from the list — we never substitute an unrelated location.';
      }
      renderLocList();
    },
    err => {
      const why = err.code === 1 ? 'permission was denied' : 'the location service is unavailable';
      st.textContent = 'Could not use browser location (' + why + '). That is fine — select your neighbourhood from the list above; everything else keeps working.';
    },
    { timeout: 8000, maximumAge: 600000 }
  );
}
function saveLocation() {
  const changedSite = locDraft.site !== state.site;
  state.site = locDraft.site;
  state.hood = locDraft.hood;
  state.locationSet = true;
  invalidateHoursCache();
  saveState();
  closeLocationModal();
  updateSiteBadge();
  populateReportAreaSelect();
  if (changedSite) {
    renderTimeline(); updateAll(state.idx); renderPlanner();
    renderReportList(); renderSatelliteChips(); renderSatellite();
    if (windMap) updateWindMap();
  } else {
    renderTimeline(); updateAll(state.idx); renderReportsLocContext();
    if (windMap) updateWindMap();
  }
}
function skipLocation() {
  state.locationSet = true;
  saveState();
  closeLocationModal();
}

/* ---------- TIMELINE ---------- */
function renderTimeline() {
  const hs = hours();
  const strip = document.getElementById('timeline-segments');
  const labels = document.getElementById('timeline-strip-labels');
  const slider = document.getElementById('time-slider');
  slider.max = Math.max(0, hs.length - 1);
  strip.innerHTML = '';
  labels.innerHTML = '';
  let lastLabelDay = null;
  hs.forEach((h, i) => {
    const seg = document.createElement('div');
    seg.className = 'tseg ' + levelOf(h.maxRisk);
    seg.title = fmtLong.format(new Date(h.time)) + ' IST — site max risk '
      + Math.round(h.maxRisk * 100) + '%' + (h.worst ? ' (worst: ' + h.worst.neighbourhood + ')' : '');
    seg.onclick = () => setIdx(i);
    strip.appendChild(seg);
    // Label at 00:00 (day change) and every 6 hours
    const hr = istHour(h.time);
    const dayKey = fmtDay.format(new Date(h.time));
    if (hr % 6 === 0 || dayKey !== lastLabelDay) {
      const lab = document.createElement('span');
      lab.className = 'strip-label';
      lab.style.left = ((i + 0.5) / hs.length * 100) + '%';
      lab.textContent = (dayKey !== lastLabelDay && i > 0 && hr !== 0)
        ? dayKey : (hr === 0 ? dayKey : istHM(h.time));
      labels.appendChild(lab);
      lastLabelDay = dayKey;
    }
  });
  highlightTimeline();
}
function highlightTimeline() {
  const hs = hours();
  if (!hs.length) return;
  document.getElementById('time-slider').value = state.idx;
  const ms = document.getElementById('map-time-slider');
  if (ms) { ms.max = hs.length - 1; ms.value = state.idx; }
  document.querySelectorAll('#timeline-segments .tseg').forEach((el, i) =>
    el.classList.toggle('selected', i === state.idx));
  const h = hs[state.idx];
  document.getElementById('tl-current-time').textContent = fmtLong.format(new Date(h.time)) + ' IST';
  const chip = document.getElementById('tl-now-chip');
  chip.textContent = state.idx === 0 ? 'NOW' : '+' + state.idx + ' h from now';
  chip.style.display = state.idx === 0 ? '' : 'none';
}
function togglePlayback() {
  const btn = document.getElementById('btn-play');
  if (playbackInterval) {
    clearInterval(playbackInterval);
    playbackInterval = null;
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>';
  } else {
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>';
    playbackInterval = setInterval(() => {
      const next = (state.idx + 1) % Math.max(1, hours().length);
      setIdx(next);
      if (currentTab === 'map' || currentTab === 'environment') { /* handled inside setIdx */ }
    }, 700);
  }
}

/* ---------- OPERATION / CLEANUP STATE (independent of risk!) ---------- */
function cleanupProgress(i) {
  // Demo cleanup ONLY ever advances when the operation schedule says work happens.
  // It is never derived from the risk level.
  if (state.mode !== 'demo') return 0;
  let p = 0;
  (APP_DATA.demo_scenario.cleanup_schedule || []).forEach(w => {
    if (i >= w.start_offset) {
      p += w.cleanup_gain * Math.min(1, (i - w.start_offset + 1) / w.duration);
    }
  });
  return Math.min(1, p / 0.55);
}
function demoOpsAt(i) {
  if (state.mode !== 'demo') return null;
  return (APP_DATA.demo_scenario.cleanup_schedule || [])
    .find(w => i >= w.start_offset && i < w.start_offset + w.duration) || null;
}
function opsWindowAt(i) {
  const o = state.ops;
  if (o && i >= o.start && i < o.start + o.dur) return o;
  return null;
}
function machineryActive(i) {
  return !!(demoOpsAt(i) || opsWindowAt(i));
}

/* ---------- HOOD-RELATIVE STATE ---------- */
function hoodCoords(name) { return siteData().neighbourhoods[name || state.hood]; }
function bearingDumpToHood(coords) {
  const cfg = siteData().config;
  return bearingDeg(cfg.lat, cfg.lon, coords[0], coords[1]);
}
function isHoodDownwind(h) {
  const coords = hoodCoords();
  if (!coords) return false;
  return angleDiff(h.plumeTo, bearingDumpToHood(coords)) < 50;
}
function hoodDistanceKm() {
  const coords = hoodCoords();
  const cfg = siteData().config;
  return coords ? haversineKm(cfg.lat, cfg.lon, coords[0], coords[1]) : null;
}

/* ---------- UPDATE ALL VIEWS FOR INDEX ---------- */
function updateAll(i) {
  const hs = hours();
  if (!hs.length) return;
  i = Math.max(0, Math.min(i, hs.length - 1));
  const h = hs[i];
  const w = h.wind;
  highlightTimeline();

  // Wind card — meteorological convention: direction is where wind blows FROM
  document.getElementById('card-wind-val').textContent = w.wind_speed_10m + ' m/s';
  document.getElementById('card-wind-dir').textContent =
    'from ' + Math.round(w.wind_direction_10m) + '° → to ' + Math.round(h.plumeTo) + '°';
  const arrow = document.getElementById('wind-arrow-icon');
  arrow.textContent = '↑';
  arrow.style.transform = 'rotate(' + Math.round(h.plumeTo) + 'deg)';

  // Risk card — for the user's selected neighbourhood
  const hoodRisk = h.hoodRisk != null ? h.hoodRisk : h.maxRisk;
  const lvl = levelOf(hoodRisk);
  const rv = document.getElementById('card-risk-val');
  rv.textContent = levelWord(lvl);
  rv.style.color = riskColorCss(lvl);
  document.getElementById('card-risk-area').textContent =
    state.hood + ' · ' + (hoodDistanceKm() != null ? hoodDistanceKm().toFixed(1) + ' km' : '--')
    + ' · site max ' + Math.round(h.maxRisk * 100) + '%';

  // Temp card
  document.getElementById('card-temp-val').textContent = (w.temperature_2m != null ? w.temperature_2m : '--') + '°C';
  document.getElementById('card-rain-val').textContent = (w.precipitation || 0) + ' mm rain';

  // Operations card — reflects the operation schedule, NOT the risk
  const opsW = opsWindowAt(i), demoW = demoOpsAt(i);
  const ov = document.getElementById('card-ops-val');
  const os = document.getElementById('card-ops-sub');
  if (opsW) {
    ov.textContent = 'Scheduled';
    ov.style.color = 'var(--accent-cyan)';
    os.textContent = (opsW.isDefault ? 'Default plan: ' : 'You scheduled: ') + opsW.activity;
  } else if (demoW) {
    ov.textContent = 'Demo ops';
    ov.style.color = '#c084fc';
    os.textContent = demoW.activity + ' (scenario schedule)';
  } else {
    ov.textContent = 'No work';
    ov.style.color = 'var(--text-secondary)';
    os.textContent = 'No odour-heavy work scheduled this hour';
  }

  // Scene overlays
  document.getElementById('scene-time-info').textContent = '🕐 ' + fmtLong.format(new Date(h.time)) + ' IST';
  document.getElementById('scene-wind-info').textContent =
    '💨 ' + w.wind_speed_10m + ' m/s from ' + Math.round(w.wind_direction_10m) + '°';
  const sr = document.getElementById('scene-risk-info');
  sr.textContent = '⚠ ' + levelWord(lvl) + ' modelled risk — ' + state.hood;
  sr.style.color = riskColorCss(lvl);
  document.getElementById('scene-user-info').textContent =
    '📍 ' + state.site + ' → ' + state.hood + (state.mode === 'demo' ? ' · DEMO' : '');

  // Visual targets for the animated scene
  visTarget.risk = h.maxRisk;
  visTarget.hoodRisk = hoodRisk;
  visTarget.cleanup = cleanupProgress(i);
  visTarget.downwindToUser = isHoodDownwind(h) ? 1 : 0;

  updateCharacterSpeech(h, lvl, hoodRisk);

  if (windMap && currentTab === 'map') updateWindMap();
}

/* ---------- CHARACTER STATE + SPEECH ---------- */
function characterExpr() {
  if (vis.hoodRisk >= RISK_HIGH && vis.downwindToUser > 0.4) return 'distressed';
  if (vis.hoodRisk >= RISK_HIGH || (vis.hoodRisk >= RISK_MOD && vis.downwindToUser > 0.6)) return 'concerned';
  if (vis.hoodRisk >= RISK_MOD) return 'concerned';
  return 'comfortable';
}
function updateCharacterSpeech(h, lvl, hoodRisk) {
  const speech = document.getElementById('character-speech');
  if (!speech) return;
  const prefix = state.mode === 'demo' ? '[DEMO scenario] ' : '';
  const down = isHoodDownwind(h);
  let message;
  if (lvl === 'high') {
    message = prefix + 'Higher modelled odour risk. The wind is carrying the estimated plume towards '
      + state.hood + '. Consider keeping windows closed and postponing odour-heavy work.';
  } else if (lvl === 'moderate') {
    message = prefix + 'Moderate modelled risk for ' + state.hood + '. '
      + (down ? 'The plume cone points roughly towards you.' : 'The main plume direction is not directly towards you.')
      + ' Wind ' + h.wind.wind_speed_10m + ' m/s from ' + Math.round(h.wind.wind_direction_10m) + '°.';
  } else {
    message = prefix + 'Lower modelled risk for ' + state.hood + ' right now. '
      + (down ? 'Conditions are calmer, but low risk is not zero — this is an estimate, not a measurement.'
              : 'Wind is carrying the estimated plume away from your direction.');
  }
  speech.textContent = message;
  speech.classList.add('visible');
}

/* ---------- SCENE CANVAS ---------- */
function initScene() {
  if (sceneAnimFrame) cancelAnimationFrame(sceneAnimFrame);  // never stack loops
  sceneCtx = document.getElementById('scene-canvas').getContext('2d');
  resizeSceneCanvas();
  window.addEventListener('resize', resizeSceneCanvas);
  if (!sceneParticles.length) {
    for (let i = 0; i < 60; i++) {
      sceneParticles.push({
        x: seededRand(i * 3 + 1) * 2000,
        y: seededRand(i * 3 + 2) * 800,
        size: seededRand(i * 7 + 3) * 3 + 1,
        speed: seededRand(i * 11 + 5) * 0.5 + 0.2,
        opacity: seededRand(i * 13 + 7) * 0.4 + 0.1,
      });
    }
  }
  animateScene();
}
function resizeSceneCanvas() {
  const canvas = document.getElementById('scene-canvas');
  const wrapper = document.getElementById('scene-wrapper');
  if (!canvas || !wrapper) return;
  const dpr = window.devicePixelRatio || 1;
  sceneW = wrapper.clientWidth;
  sceneH = wrapper.clientHeight;
  // Integer CSS size + DPR backing store: avoids fractional resampling shimmer
  canvas.style.width = sceneW + 'px';
  canvas.style.height = sceneH + 'px';
  canvas.width = Math.round(sceneW * dpr);
  canvas.height = Math.round(sceneH * dpr);
  sceneCtx = canvas.getContext('2d');
  sceneCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
function animateScene() {
  if (!sceneCtx) { sceneAnimFrame = requestAnimationFrame(animateScene); return; }
  const w = sceneW, h = sceneH;
  if (w === 0 || h === 0 || !hours().length) { sceneAnimFrame = requestAnimationFrame(animateScene); return; }
  const hs = hours();
  const cur = hs[Math.max(0, Math.min(state.idx, hs.length - 1))];
  const hour = istHour(cur.time);

  drawSky(sceneCtx, w, h, hour, vis.risk);
  drawTerrain(sceneCtx, w, h, hour);
  drawGround(sceneCtx, w, h, hour);
  drawLandfill(sceneCtx, w, h);
  drawBuildings(sceneCtx, w, h, hour);
  drawTrees(sceneCtx, w, h);
  drawMachinery(sceneCtx, w, h);
  drawAtmosphericParticles(sceneCtx, w, h, cur);
  sceneAnimFrame = requestAnimationFrame(animateScene);
}

function drawSky(ctx, w, h, hour, risk) {
  const grad = ctx.createLinearGradient(0, 0, 0, h * 0.6);
  let skyTop, skyMid, skyBot;
  if (hour >= 6 && hour < 10) {
    skyTop = `hsl(210, 60%, ${28 - risk * 10}%)`;
    skyMid = `hsl(30, 70%, ${55 - risk * 15}%)`;
    skyBot = `hsl(40, 50%, ${65 - risk * 12}%)`;
  } else if (hour >= 10 && hour < 17) {
    skyTop = `hsl(200, 55%, ${45 - risk * 15}%)`;
    skyMid = `hsl(190, 40%, ${55 - risk * 12}%)`;
    skyBot = `hsl(180, 30%, ${60 - risk * 10}%)`;
  } else if (hour >= 17 && hour < 20) {
    skyTop = `hsl(240, 50%, ${25 - risk * 8}%)`;
    skyMid = `hsl(20, 60%, ${45 - risk * 12}%)`;
    skyBot = `hsl(30, 50%, ${50 - risk * 10}%)`;
  } else {
    skyTop = `hsl(230, 40%, ${12 - risk * 5}%)`;
    skyMid = `hsl(220, 35%, ${18 - risk * 6}%)`;
    skyBot = `hsl(210, 30%, ${22 - risk * 7}%)`;
  }
  grad.addColorStop(0, skyTop); grad.addColorStop(0.5, skyMid); grad.addColorStop(1, skyBot);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  if (risk > 0.3) {
    ctx.fillStyle = `rgba(120, 100, 60, ${risk * 0.15})`;
    ctx.fillRect(0, 0, w, h);
  }

  if (hour >= 6 && hour < 20) {
    const sunProgress = (hour - 6) / 14;
    const sunX = w * 0.1 + w * 0.8 * sunProgress;
    const sunY = h * 0.15 + Math.sin(sunProgress * Math.PI) * (-h * 0.1);
    const sunGrad = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, 40);
    sunGrad.addColorStop(0, `rgba(255, 220, 100, ${0.9 - risk * 0.3})`);
    sunGrad.addColorStop(0.5, `rgba(255, 180, 60, ${0.4 - risk * 0.15})`);
    sunGrad.addColorStop(1, 'rgba(255, 150, 50, 0)');
    ctx.fillStyle = sunGrad;
    ctx.fillRect(sunX - 60, sunY - 60, 120, 120);
    ctx.beginPath();
    ctx.arc(sunX, sunY, 18, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255, 230, 120, ${0.9 - risk * 0.2})`;
    ctx.fill();
  } else {
    ctx.beginPath();
    ctx.arc(w * 0.8, h * 0.12, 14, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(200, 210, 230, 0.8)';
    ctx.fill();
    for (let i = 0; i < 30; i++) {
      const sx = (i * 67 + 13) % w;
      const sy = (i * 43 + 7) % (h * 0.3);
      ctx.beginPath();
      ctx.arc(sx, sy, 1, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${0.3 + Math.sin(Date.now() / 1000 + i) * 0.2})`;
      ctx.fill();
    }
  }
}

function drawTerrain(ctx, w, h, hour) {
  ctx.beginPath();
  ctx.moveTo(0, h * 0.45);
  for (let x = 0; x <= w; x += 20) {
    ctx.lineTo(x, h * 0.45 + Math.sin(x / 150) * 15 + Math.sin(x / 80) * 8);
  }
  ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath();
  const hillGrad = ctx.createLinearGradient(0, h * 0.4, 0, h);
  hillGrad.addColorStop(0, hour >= 6 && hour < 20 ? '#3d5c3a' : '#1a2d1a');
  hillGrad.addColorStop(1, hour >= 6 && hour < 20 ? '#2a3d28' : '#0f1a0f');
  ctx.fillStyle = hillGrad;
  ctx.fill();
}

/* ---------- LANDFILL GEOMETRY (shared by mound, machinery, plume source) ---------- */
function rr(ctx, x, y, w2, h2, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w2, y, x + w2, y + h2, r);
  ctx.arcTo(x + w2, y + h2, x, y + h2, r);
  ctx.arcTo(x, y + h2, x, y, r);
  ctx.arcTo(x, y, x + w2, y, r);
  ctx.closePath();
}
function moundGeom(w, h) {
  const baseY = h * 0.685;
  const x0 = w * 0.26, x1 = w * 0.66;
  // Cut line advances ONLY with cleanup progress — never with wind or risk.
  // Mound size reflects ACCUMULATED WASTE minus what operations have removed —
  // a low-risk hour with no cleanup still shows the full garbage mound.
  const cx = x0 + (x1 - x0) * 0.85 * vis.cleanup;
  const mh = Math.max(14, h * 0.27 * (1 - 0.45 * vis.cleanup));
  return { x0, x1, cx, baseY, mh, span: Math.max(30, x1 - cx) };
}
function moundApex(w, h) {
  const g = moundGeom(w, h);
  return { x: g.cx + g.span * 0.47, y: g.baseY - g.mh * 0.92 };
}
function moundPathShape(ctx, g) {
  ctx.beginPath();
  ctx.moveTo(g.cx, g.baseY + 6);
  ctx.quadraticCurveTo(g.cx + g.span * 0.12, g.baseY - g.mh * 0.5, g.cx + g.span * 0.28, g.baseY - g.mh * 0.82);
  ctx.quadraticCurveTo(g.cx + g.span * 0.4, g.baseY - g.mh * 1.06, g.cx + g.span * 0.54, g.baseY - g.mh * 0.68);
  ctx.quadraticCurveTo(g.cx + g.span * 0.66, g.baseY - g.mh * 0.94, g.cx + g.span * 0.8, g.baseY - g.mh * 0.42);
  ctx.quadraticCurveTo(g.cx + g.span * 0.9, g.baseY - g.mh * 0.18, g.x1, g.baseY + 6);
  ctx.closePath();
}

function drawLandfill(ctx, w, h) {
  const g = moundGeom(w, h);

  // Exposed ground where waste has been excavated (soil, tyre tracks, leftover litter)
  if (vis.cleanup > 0.01) {
    const soil = ctx.createLinearGradient(0, g.baseY - 8, 0, g.baseY + 30);
    soil.addColorStop(0, '#57482f');
    soil.addColorStop(1, '#3c3222');
    ctx.fillStyle = soil;
    ctx.fillRect(g.x0 - 30, g.baseY - 8, (g.cx - g.x0) + 14, 40);
    ctx.strokeStyle = 'rgba(30, 25, 15, 0.5)';
    ctx.lineWidth = 2;
    for (const off of [8, 15]) {
      ctx.beginPath();
      ctx.moveTo(g.x0 - 20, g.baseY + off);
      ctx.lineTo(g.cx + 6, g.baseY + off);
      ctx.stroke();
    }
    for (let i = 0; i < 14; i++) {
      const rx = g.x0 - 10 + seededRand(i * 4 + 31) * (g.cx - g.x0 + 10);
      const ry = g.baseY + 2 + seededRand(i * 4 + 32) * 18;
      ctx.fillStyle = ['#8a8577', '#997', '#6b5b3a', '#aab2bd'][i % 4];
      ctx.globalAlpha = 0.7;
      ctx.beginPath();
      ctx.ellipse(rx, ry, 2 + seededRand(i + 33) * 3, 1.5 + seededRand(i + 34) * 2, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  // Mound body
  moundPathShape(ctx, g);
  const dumpGrad = ctx.createLinearGradient(0, g.baseY - g.mh, 0, g.baseY + 10);
  dumpGrad.addColorStop(0, '#6d5c3c');
  dumpGrad.addColorStop(0.45, '#57482e');
  dumpGrad.addColorStop(1, '#38301e');
  ctx.fillStyle = dumpGrad;
  ctx.fill();

  // Waste layers embedded in the mound — deterministic, clipped to silhouette
  ctx.save();
  moundPathShape(ctx, g);
  ctx.clip();
  const bagColors = ['#c9ced8', '#a9b8c9', '#8a9a7d', '#c4b39a', '#9d8fae', '#d8d3c6', '#7f8c9a', '#b0654f', '#5f6f5f'];
  const n = 90;
  for (let i = 0; i < n; i++) {
    const u = seededRand(i * 5 + 101), v = seededRand(i * 5 + 102);
    const kind = seededRand(i * 5 + 103);
    const x = g.cx + u * g.span;
    const y = g.baseY - v * g.mh * 1.02;
    const rot = (seededRand(i * 5 + 104) - 0.5) * 1.2;
    if (kind < 0.55) {
      const rw = 4 + seededRand(i + 201) * 5, rh = 3 + seededRand(i + 202) * 4;
      ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
      ctx.fillStyle = bagColors[i % bagColors.length];
      ctx.beginPath(); ctx.ellipse(0, 0, rw, rh, 0, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(-rw * 0.3, -rh * 0.3, rw * 0.4, 0.6, 2.2); ctx.stroke();
      ctx.restore();
    } else if (kind < 0.72) {
      ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
      ctx.fillStyle = '#a98b5d'; ctx.fillRect(-8, -1.5, 16, 3);
      ctx.strokeStyle = '#7c6642'; ctx.strokeRect(-8, -1.5, 16, 3);
      ctx.restore();
    } else if (kind < 0.85) {
      ctx.fillStyle = '#9aa3ad';
      ctx.fillRect(x - 2, y - 3.5, 4, 7);
      ctx.strokeStyle = '#5f6a75'; ctx.strokeRect(x - 2, y - 3.5, 4, 7);
    } else if (kind < 0.93) {
      ctx.strokeStyle = '#20242a'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.stroke();
    } else {
      ctx.fillStyle = '#4a4438';
      ctx.beginPath(); ctx.arc(x, y, 2 + seededRand(i + 203) * 2, 0, Math.PI * 2); ctx.fill();
    }
  }
  // Compacted-waste layer seams
  ctx.strokeStyle = 'rgba(40, 32, 18, 0.35)';
  ctx.lineWidth = 1.5;
  for (let k = 1; k <= 3; k++) {
    const sy = g.baseY - g.mh * (k / 4) * 0.85;
    ctx.beginPath();
    ctx.moveTo(g.cx, sy + 6);
    for (let x = g.cx; x <= g.x1; x += 18) ctx.lineTo(x, sy + Math.sin(x / 40 + k) * 3);
    ctx.stroke();
  }
  ctx.restore();

  // Sheared excavation face + outline
  ctx.strokeStyle = 'rgba(25, 20, 10, 0.5)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(g.cx, g.baseY + 4);
  ctx.lineTo(g.cx + g.span * 0.06, g.baseY - g.mh * 0.55);
  ctx.stroke();
  moundPathShape(ctx, g);
  ctx.strokeStyle = '#4a3f28';
  ctx.lineWidth = 1;
  ctx.stroke();

  // Leachate pond — shrinks with cleanup
  ctx.beginPath();
  ctx.ellipse(g.x1 + w * 0.02, g.baseY + 12, 26 * (1 - 0.6 * vis.cleanup), 7 * (1 - 0.6 * vis.cleanup), 0, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(80, 100, 60, 0.6)';
  ctx.fill();

  // Odour wisps rising from the mound top, tied to modelled risk (continuous, smooth)
  if (vis.risk > 0.2) {
    const t = Date.now() / 2000;
    const apex = moundApex(w, h);
    for (let i = 0; i < 5; i++) {
      const sx = apex.x - 30 + i * 15;
      const sy = apex.y + 10;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.quadraticCurveTo(sx + Math.sin(t + i) * 20, sy - 24 - i * 8,
        sx + Math.sin(t * 0.7 + i * 0.7) * 40, sy - 50 - i * 12);
      ctx.strokeStyle = `rgba(150, 130, 80, ${vis.risk * 0.25 - i * 0.03})`;
      ctx.lineWidth = 3 - i * 0.4;
      ctx.stroke();
    }
  }
}

function drawBuildings(ctx, w, h, hour) {
  const baseY = h * 0.58;
  const lit = hour < 6 || hour >= 18;
  // Windows are shown shut when the model estimates the plume heads this way
  const closed = vis.downwindToUser > 0.5 && vis.hoodRisk >= RISK_MOD;
  const buildings = [
    { x: w * 0.72, w: 35, h: 55 }, { x: w * 0.76, w: 28, h: 70 },
    { x: w * 0.80, w: 32, h: 48 }, { x: w * 0.84, w: 25, h: 62 },
    { x: w * 0.88, w: 30, h: 45 }, { x: w * 0.92, w: 28, h: 38 },
  ];
  buildings.forEach((b, i) => {
    const by = baseY + 30 - b.h;
    ctx.fillStyle = `hsl(${30 + i * 8}, 15%, ${lit ? 25 : 45}%)`;
    ctx.fillRect(b.x, by, b.w, b.h);
    ctx.fillStyle = `hsl(${20 + i * 5}, 20%, ${lit ? 20 : 35}%)`;
    ctx.fillRect(b.x - 3, by - 5, b.w + 6, 8);
    let k = 0;
    for (let wy = by + 10; wy < by + b.h - 8; wy += 14) {
      for (let wx = b.x + 5; wx < b.x + b.w - 8; wx += 12) {
        k++;
        if (closed) {
          ctx.fillStyle = 'rgba(20, 24, 30, 0.85)';   // shutters closed
          ctx.fillRect(wx, wy, 6, 8);
          ctx.strokeStyle = 'rgba(90, 100, 115, 0.5)';
          ctx.strokeRect(wx + 0.5, wy + 0.5, 5, 7);
        } else {
          ctx.fillStyle = lit ? `rgba(255, 220, 120, ${0.35 + seededRand(i * 17 + k) * 0.45})`
                              : 'rgba(150, 200, 255, 0.3)';
          ctx.fillRect(wx, wy, 6, 8);
        }
      }
    }
  });
}

function drawTrees(ctx, w, h) {
  const baseY = h * 0.62;
  const treePositions = [w * 0.67, w * 0.69, w * 0.70, w * 0.685, w * 0.10, w * 0.12, w * 0.07, w * 0.93, w * 0.95];
  const t = Date.now() / 3000;
  treePositions.forEach((tx, i) => {
    const ty = baseY + 5 + (i % 3) * 8;
    const sway = Math.sin(t + i * 0.8) * 2;
    ctx.fillStyle = '#4a3520';
    ctx.fillRect(tx - 2, ty - 15, 4, 20);
    ctx.beginPath();
    ctx.arc(tx + sway, ty - 22, 12 + (i % 3) * 2, 0, Math.PI * 2);
    ctx.fillStyle = `hsl(${110 + i * 5}, ${45 + i * 3}%, ${28 + (i % 4) * 3}%)`;
    ctx.fill();
    ctx.beginPath();
    ctx.arc(tx + sway - 4, ty - 28, 8, 0, Math.PI * 2);
    ctx.fillStyle = `hsl(${115 + i * 4}, ${50 + i * 2}%, ${32 + (i % 3) * 2}%)`;
    ctx.fill();
  });
}

function drawMachinery(ctx, w, h) {
  // Machines move ONLY when the operation schedule says work is happening —
  // never because risk happened to drop.
  const active = machineryActive(state.idx);
  const t = Date.now() / 1000;
  const g = moundGeom(w, h);
  const roadY = h * 0.725;

  // Waste truck: deterministic 12 s arrive-empty -> load -> haul-away cycle
  const parkX = Math.max(w * 0.10, g.cx - w * 0.14);
  // Truck hauls in/out from the LEFT edge so it never passes behind the
  // bottom-right character. The load itself happens beside the active cut face.
  const haulX = w * 0.05;
  let truckX = parkX, load = 0;
  if (active) {
    const ph = (t % 12) / 12;
    if (ph < 0.2)       { truckX = parkX + (haulX - parkX) * (1 - ph / 0.2); load = 0; }
    else if (ph < 0.75) { truckX = parkX; load = Math.min(1, (ph - 0.2) / 0.5); }
    else if (ph < 0.95) { truckX = parkX + (haulX - parkX) * ((ph - 0.75) / 0.2); load = 1; }
    else                { truckX = haulX + 90; load = 0; }
  }
  drawWasteTruck(ctx, truckX, roadY + 12, load);
  drawExcavator(ctx, g.cx + w * 0.035, roadY + 10, active ? t : null);
}

function drawExcavator(ctx, x, y, t) {
  ctx.save();
  ctx.translate(x, y);
  // Tracks with rollers and tread bars
  ctx.fillStyle = '#23272c';
  rr(ctx, -24, -8, 48, 12, 6); ctx.fill();
  ctx.fillStyle = '#3a3f45';
  for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(-15 + i * 10, -2, 3.4, 0, Math.PI * 2); ctx.fill(); }
  ctx.strokeStyle = 'rgba(0,0,0,0.4)'; ctx.lineWidth = 1;
  for (let i = 0; i < 9; i++) { const tx = -21 + i * 5.2; ctx.beginPath(); ctx.moveTo(tx, -8); ctx.lineTo(tx, 4); ctx.stroke(); }
  // House, cab, exhaust, counterweight
  ctx.fillStyle = '#d4a017'; rr(ctx, -17, -22, 28, 15, 3); ctx.fill();
  ctx.fillStyle = '#8a6d12'; rr(ctx, -22, -20, 6, 11, 2); ctx.fill();
  ctx.fillStyle = '#b8901a'; rr(ctx, -14, -32, 15, 11, 2); ctx.fill();
  ctx.fillStyle = 'rgba(160, 210, 255, 0.5)'; ctx.fillRect(-11, -30, 9, 7);
  ctx.fillStyle = '#555'; ctx.fillRect(7, -28, 2, 6);

  // Dig cycle (6 s): reach down -> curl full -> lift -> swing to truck -> dump -> return
  let boom = -0.9, stick = 0.7, curl = 0.4, swing = 0, carry = 0;
  if (t !== null) {
    const ph = (t % 6) / 6;
    if (ph < 0.25)      { const k = ph / 0.25;         boom = -0.9 + 0.75 * k; curl = 0.4 - 0.2 * k; }
    else if (ph < 0.4)  { const k = (ph - 0.25) / 0.15; curl = 0.2 + 1.0 * k;   boom = -0.15 - 0.1 * k; carry = k; }
    else if (ph < 0.55) { const k = (ph - 0.4) / 0.15;  boom = -0.25 - 0.65 * k; curl = 1.2 - 0.9 * k; carry = 1; }
    else if (ph < 0.7)  { const k = (ph - 0.55) / 0.15; swing = k;              carry = 1; }
    else if (ph < 0.8)  { const k = (ph - 0.7) / 0.1;   swing = 1; curl = 0.3 + 1.2 * k; carry = 1 - k; }
    else                { const k = (ph - 0.8) / 0.2;   swing = 1 - k; }
  }
  ctx.save();
  ctx.translate(9, -26);                       // Shoulder pivot
  ctx.rotate(-swing * 0.8);                    // Slew stand-in: arm rotates towards the truck
  ctx.rotate(boom);
  ctx.fillStyle = '#c89518'; rr(ctx, 0, -3, 27, 6, 2); ctx.fill();
  ctx.strokeStyle = 'rgba(90,60,10,0.5)'; ctx.stroke();
  ctx.translate(27, 0); ctx.rotate(stick - boom * 0.6);
  ctx.fillStyle = '#d4a017'; rr(ctx, 0, -2.5, 19, 5, 2); ctx.fill();
  ctx.translate(19, 0); ctx.rotate(curl - 0.4);
  // Bucket with teeth
  ctx.fillStyle = '#6b7076';
  ctx.beginPath();
  ctx.moveTo(0, -4); ctx.lineTo(10, -2); ctx.lineTo(10, 7); ctx.lineTo(-2, 9); ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = '#3f444a'; ctx.stroke();
  ctx.fillStyle = '#3f444a';
  for (let i = 0; i < 3; i++) ctx.fillRect(9, -1 + i * 3, 3.5, 1.6);
  if (carry > 0.15) {                          // Waste held in the bucket
    ctx.fillStyle = '#6b5b3a';
    ctx.beginPath(); ctx.ellipse(4, 0, 5.5 * carry, 3.4 * carry, 0, Math.PI, 0); ctx.fill();
    ctx.fillStyle = '#c9ced8';
    ctx.beginPath(); ctx.arc(2, -1.5, 1.6 * carry, 0, Math.PI * 2); ctx.fill();
  }
  if (swing > 0.95 && curl > 1.1) {            // Dumping into the truck bed
    for (let i = 0; i < 5; i++) {
      const fx = 4 - seededRand(i + 401) * 10;
      const fy = 10 + (curl - 1.1) * 40 + seededRand(i + 402) * 8;
      ctx.fillStyle = ['#6b5b3a', '#c9ced8', '#9d8fae'][i % 3];
      ctx.beginPath(); ctx.arc(fx, fy, 1.6, 0, Math.PI * 2); ctx.fill();
    }
  }
  ctx.restore();
  ctx.restore();
}

function drawWasteTruck(ctx, x, y, load) {
  ctx.save();
  ctx.translate(x, y);
  // Wheels
  [[-26, 8], [14, 8], [24, 8]].forEach(([wx, wy]) => {
    ctx.fillStyle = '#1c1f23';
    ctx.beginPath(); ctx.arc(wx, wy, 5.5, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#4b5158';
    ctx.beginPath(); ctx.arc(wx, wy, 2.2, 0, Math.PI * 2); ctx.fill();
  });
  // Chassis + cab (facing the excavation) + dump bed
  ctx.fillStyle = '#2f3640'; ctx.fillRect(-30, 2, 62, 4);
  ctx.fillStyle = '#3a6ea5'; rr(ctx, 18, -14, 14, 18, 3); ctx.fill();
  ctx.fillStyle = 'rgba(160, 210, 255, 0.5)'; ctx.fillRect(22, -11, 8, 7);
  ctx.fillStyle = '#4a5568'; rr(ctx, -30, -12, 44, 15, 2); ctx.fill();
  ctx.fillStyle = '#3b4454'; ctx.fillRect(-30, -12, 44, 3);
  ctx.strokeStyle = 'rgba(255,255,255,0.08)'; ctx.lineWidth = 1;
  for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.moveTo(-24 + i * 11, -9); ctx.lineTo(-24 + i * 11, 1); ctx.stroke(); }
  if (load > 0.05) {
    ctx.save();
    ctx.beginPath(); ctx.rect(-30, -24, 44, 26); ctx.clip();
    const lvl = -9 - load * 10;
    ctx.fillStyle = '#6b5b3a';
    ctx.beginPath();
    ctx.moveTo(-29, 2);
    ctx.lineTo(-29, lvl);
    for (let px = -29; px <= 13; px += 6) ctx.lineTo(px, lvl + seededRand(px + 500) * 3 - 1.5);
    ctx.lineTo(13, 2);
    ctx.closePath(); ctx.fill();
    const bagCols = ['#c9ced8', '#9d8fae', '#8a9a7d', '#b0654f'];
    for (let i = 0; i < 4; i++) {
      const bx = -26 + seededRand(i + 520) * 36;
      ctx.fillStyle = bagCols[i];
      ctx.beginPath(); ctx.ellipse(bx, lvl + 1, 3, 2, 0, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }
  ctx.restore();
}

function drawAtmosphericParticles(ctx, w, h, cur) {
  const windSpd = cur.wind.wind_speed_10m || 2;
  const radians = toRad(cur.plumeTo - 90);       // screen direction the air travels
  const dirX = Math.cos(radians), dirY = Math.sin(radians);

  sceneParticles.forEach((p, i) => {
    p.x += dirX * windSpd * p.speed;
    p.y += dirY * windSpd * p.speed * 0.3;
    if (p.x > w + 20) p.x = -20;
    if (p.x < -20) p.x = w + 20;
    if (p.y > h) p.y = 0;
    if (p.y < 0) p.y = h;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    if (vis.risk > 0.3) {
      ctx.fillStyle = `rgba(180, 150, 80, ${p.opacity * vis.risk})`;
    } else {
      ctx.fillStyle = `rgba(200, 220, 240, ${p.opacity * 0.5})`;
    }
    ctx.fill();
    if (windSpd > 3) {
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(p.x - dirX * windSpd * 3, p.y - dirY * windSpd * 1.5);
      ctx.strokeStyle = vis.risk > 0.3
        ? `rgba(180, 150, 80, ${p.opacity * vis.risk * 0.3})`
        : `rgba(200, 220, 240, ${p.opacity * 0.15})`;
      ctx.lineWidth = p.size * 0.5;
      ctx.stroke();
    }
  });

  // ---- Odour waves: translucent expanding wavefronts + ribbon streamlines ----
  const strength = vis.risk * (0.4 + 0.6 * vis.downwindToUser);
  if (strength > 0.08) {
    const apex = moundApex(w, h);
    const apexX = apex.x, apexY = apex.y;
    const face = Math.atan2(dirY, dirX);
    const t = Date.now() / 2600;
    for (let k = 0; k < 4; k++) {
      const prog = ((t + k / 4) % 1);
      const r = prog * w * 0.55;
      ctx.beginPath();
      ctx.arc(apexX, apexY, r, face - 0.75, face + 0.75);
      ctx.strokeStyle = `rgba(196, 164, 90, ${(1 - prog) * 0.22 * strength})`;
      ctx.lineWidth = 5 - 3 * prog;
      ctx.stroke();
    }
    for (let i = 0; i < 5; i++) {
      const phase = Date.now() / 3000 + i * 0.7;
      ctx.beginPath();
      const startX = apexX, startY = apexY + (i - 2) * 14;
      ctx.moveTo(startX, startY);
      for (let step = 1; step <= 8; step++) {
        const wob = Math.sin(phase + step * 0.5) * 9;
        const px = startX + dirX * step * w * 0.055 - Math.sin(radians) * wob * 0.3;
        const py = startY + dirY * step * w * 0.055 + Math.cos(radians) * wob * 0.3;
        ctx.lineTo(px, py);
      }
      ctx.strokeStyle = `rgba(160, 130, 60, ${0.05 + strength * 0.1 - i * 0.012})`;
      ctx.lineWidth = 7 - i;
      ctx.stroke();
    }
  }
}

function drawGround(ctx, w, h, hour) {
  const baseY = h * 0.65;
  ctx.fillStyle = '#3a3a3a';
  ctx.fillRect(0, baseY + 20, w, 12);
  ctx.setLineDash([15, 20]);
  ctx.strokeStyle = '#666';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(0, baseY + 26);
  ctx.lineTo(w, baseY + 26);
  ctx.stroke();
  ctx.setLineDash([]);

  const gGrad = ctx.createLinearGradient(0, baseY + 32, 0, h);
  gGrad.addColorStop(0, '#2d3a24');
  gGrad.addColorStop(1, '#1a2418');
  ctx.fillStyle = gGrad;
  ctx.fillRect(0, baseY + 32, w, h - baseY - 32);

  for (let x = 0; x < w; x += 25) {
    const gy = baseY + 35 + (x % 7) * 3;
    ctx.beginPath();
    ctx.moveTo(x, gy);
    ctx.lineTo(x - 3, gy - 6);
    ctx.lineTo(x + 1, gy - 4);
    ctx.lineTo(x + 4, gy - 7);
    ctx.lineTo(x + 6, gy);
    ctx.fillStyle = `hsl(110, 35%, ${22 + (x % 5) * 2}%)`;
    ctx.fill();
  }

  [w * 0.08, w * 0.65, w * 0.85].forEach(lx => {
    ctx.fillStyle = '#555';
    ctx.fillRect(lx - 1, baseY - 5, 3, 28);
    ctx.fillStyle = '#666';
    ctx.fillRect(lx - 6, baseY - 5, 15, 3);
    if (hour < 6 || hour >= 18) {
      const lg = ctx.createRadialGradient(lx + 2, baseY, 0, lx + 2, baseY, 30);
      lg.addColorStop(0, 'rgba(255, 220, 120, 0.3)');
      lg.addColorStop(1, 'rgba(255, 220, 120, 0)');
      ctx.fillStyle = lg;
      ctx.fillRect(lx - 30, baseY - 30, 64, 60);
    }
  });
}

/* ---------- CHARACTER ---------- */
function createCharacterSVG(expr, scale) {
  const s = scale || 1;
  let eyes, brows, mouth, arms, hands = '';
  if (expr === 'distressed') {
    eyes = '<path d="M38 42 Q42 45 46 42" fill="none" stroke="#2d3748" stroke-width="2" stroke-linecap="round"/>'
         + '<path d="M54 42 Q58 45 62 42" fill="none" stroke="#2d3748" stroke-width="2" stroke-linecap="round"/>';
    brows = '<path d="M37 35 L46 38" stroke="#5a3e28" stroke-width="2" stroke-linecap="round"/>'
          + '<path d="M63 35 L54 38" stroke="#5a3e28" stroke-width="2" stroke-linecap="round"/>';
    mouth = '<path d="M42 58 Q50 53 58 58" fill="none" stroke="#c0392b" stroke-width="2" stroke-linecap="round"/>';
    arms = '<path d="M26 78 Q20 62 40 52" fill="none" stroke="#e8b894" stroke-width="11" stroke-linecap="round"/>'
         + '<path d="M74 78 Q80 62 60 52" fill="none" stroke="#e8b894" stroke-width="11" stroke-linecap="round"/>';
    hands = '<ellipse cx="43" cy="50" rx="7" ry="6" fill="#fcd9b6" stroke="#e8b894"/>'
          + '<ellipse cx="57" cy="50" rx="7" ry="6" fill="#fcd9b6" stroke="#e8b894"/>';
  } else if (expr === 'concerned') {
    eyes = '<ellipse cx="42" cy="42" rx="3.5" ry="4" fill="#2d3748"/><ellipse cx="58" cy="42" rx="3.5" ry="4" fill="#2d3748"/>'
         + '<circle cx="43" cy="41" r="1.2" fill="white"/><circle cx="59" cy="41" r="1.2" fill="white"/>';
    brows = '<path d="M36 35 Q42 36 46 38" fill="none" stroke="#5a3e28" stroke-width="1.8" stroke-linecap="round"/>'
          + '<path d="M64 35 Q58 36 54 38" fill="none" stroke="#5a3e28" stroke-width="1.8" stroke-linecap="round"/>';
    mouth = '<path d="M41 55 L59 55" fill="none" stroke="#c0392b" stroke-width="2" stroke-linecap="round"/>';
    arms = '<rect x="20" y="70" width="12" height="30" rx="6" fill="#fcd9b6" stroke="#e8b894" stroke-width="1"/>'
         + '<rect x="68" y="70" width="12" height="30" rx="6" fill="#fcd9b6" stroke="#e8b894" stroke-width="1"/>';
  } else {
    eyes = '<ellipse cx="42" cy="42" rx="3.5" ry="4" fill="#2d3748"/><ellipse cx="58" cy="42" rx="3.5" ry="4" fill="#2d3748"/>'
         + '<circle cx="43" cy="41" r="1.2" fill="white"/><circle cx="59" cy="41" r="1.2" fill="white"/>';
    brows = '<path d="M36 36 Q42 33 46 36" fill="none" stroke="#5a3e28" stroke-width="1.5" stroke-linecap="round"/>'
          + '<path d="M54 36 Q58 33 64 36" fill="none" stroke="#5a3e28" stroke-width="1.5" stroke-linecap="round"/>';
    mouth = '<path d="M40 53 Q50 60 60 53" fill="none" stroke="#c0392b" stroke-width="2" stroke-linecap="round"/>';
    arms = '<rect x="20" y="70" width="12" height="30" rx="6" fill="#fcd9b6" stroke="#e8b894" stroke-width="1"/>'
         + '<rect x="68" y="70" width="12" height="30" rx="6" fill="#fcd9b6" stroke="#e8b894" stroke-width="1"/>';
  }
  return '<svg viewBox="0 0 100 140" width="' + (100 * s) + '" height="' + (140 * s) + '">'
    + '<g class="char-head">'
    + '<ellipse cx="50" cy="28" rx="28" ry="12" fill="#f59e0b" stroke="#d97706" stroke-width="1.5"/>'
    + '<rect x="22" y="20" width="56" height="10" rx="5" fill="#f59e0b" stroke="#d97706" stroke-width="1"/>'
    + '<circle cx="50" cy="45" r="22" fill="#fcd9b6" stroke="#e8b894" stroke-width="1"/>'
    + brows
    + '<g class="char-eyes">' + eyes + '</g>'
    + mouth
    + '</g>'
    + '<g class="char-body">'
    + '<rect x="32" y="67" width="36" height="40" rx="6" fill="#f97316"/>'
    + '<line x1="35" y1="75" x2="65" y2="75" stroke="#fbbf24" stroke-width="3"/>'
    + '<line x1="35" y1="95" x2="65" y2="95" stroke="#fbbf24" stroke-width="3"/>'
    + '</g>'
    + arms
    + hands
    + '<rect x="36" y="105" width="12" height="25" rx="4" fill="#1e3a5f"/>'
    + '<rect x="52" y="105" width="12" height="25" rx="4" fill="#1e3a5f"/>'
    + '<rect x="34" y="126" width="16" height="8" rx="4" fill="#4a3520"/>'
    + '<rect x="50" y="126" width="16" height="8" rx="4" fill="#4a3520"/>'
    + '</svg>';
}
function renderCharacter(expr) {
  lastCharExpr = expr;
  const wrapper = document.getElementById('character-svg-wrapper');
  if (wrapper) wrapper.innerHTML = createCharacterSVG(expr, 1);
}

/* ---------- WIND MAP (LEAFLET) ---------- */
let mapBaseSite = null;
function initMap() {
  if (windMap) { windMap.invalidateSize(); updateWindMap(); return; }
  const cfg = siteData().config;
  windMap = L.map('wind-map', { center: [cfg.lat, cfg.lon], zoom: 12, zoomControl: true });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors', maxZoom: 19,
  }).addTo(windMap);
  windMap.getContainer().querySelector('.leaflet-tile-pane').style.filter =
    'brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3) brightness(0.7)';
  mapBase = L.layerGroup().addTo(windMap);
  mapDynamic = L.layerGroup().addTo(windMap);

  const canvas = document.getElementById('wind-canvas');
  windCanvasCtx = canvas.getContext('2d');
  const resizeWindCanvas = () => {
    const container = document.querySelector('.map-container');
    if (container) { canvas.width = container.clientWidth; canvas.height = container.clientHeight; }
  };
  resizeWindCanvas();
  window.addEventListener('resize', resizeWindCanvas);
  windParticles = [];
  for (let i = 0; i < 200; i++) {
    windParticles.push({
      x: seededRand(i * 3 + 1) * canvas.width, y: seededRand(i * 3 + 2) * canvas.height,
      age: seededRand(i * 5 + 3) * 100, maxAge: 80 + seededRand(i * 7 + 4) * 40,
      speed: 0.5 + seededRand(i * 11 + 5) * 1.5,
    });
  }
  updateWindMap();
  animateWindMap();
  setTimeout(() => windMap.invalidateSize(), 200);
}
function rebuildMapBase() {
  mapBase.clearLayers();
  const cfg = siteData().config;
  L.marker([cfg.lat, cfg.lon], {
    icon: L.divIcon({
      html: '<div style="width:20px;height:20px;background:rgba(239,68,68,0.8);border-radius:50%;border:2px solid #ef4444;box-shadow:0 0 10px rgba(239,68,68,0.5);"></div>',
      iconSize: [20, 20], className: '',
    }),
  }).bindTooltip(state.site + ' Dumpyard', { permanent: true, direction: 'top', className: 'map-tooltip' }).addTo(mapBase);
  L.circle([cfg.lat, cfg.lon], {
    radius: cfg.radius_km * 1000, color: 'rgba(239,68,68,0.3)', fillColor: 'rgba(239,68,68,0.05)',
    fillOpacity: 0.5, weight: 1, dashArray: '5,5',
  }).addTo(mapBase);
  Object.entries(siteData().neighbourhoods).forEach(([name, coords]) => {
    L.marker(coords, {
      icon: L.divIcon({
        html: '<div style="width:10px;height:10px;background:rgba(34,211,238,0.5);border-radius:50%;border:1.5px solid #22d3ee;"></div>',
        iconSize: [10, 10], className: '',
      }),
    }).bindTooltip(name, { direction: 'top', className: 'map-tooltip' }).addTo(mapBase);
  });
  mapBaseSite = state.site;
}
function plumeLengthKm(w) { return Math.min(Math.max(w.wind_speed_10m * 3.6, 2), 10); }

function updateWindMap() {
  if (!windMap) return;
  const hs = hours();
  if (!hs.length) return;
  const h = hs[Math.min(state.idx, hs.length - 1)];
  const cfg = siteData().config;
  if (mapBaseSite !== state.site) {
    windMap.setView([cfg.lat, cfg.lon], 12);
    rebuildMapBase();
  }
  mapDynamic.clearLayers();
  document.getElementById('map-time-label').textContent = fmtLong.format(new Date(h.time)) + ' IST';

  if (showLayers.risk) {
    h.risks.forEach(r => {
      const color = r.level === 'High' ? '#ef4444' : r.level === 'Moderate' ? '#fbbf24' : '#4ade80';
      L.circleMarker([r.lat, r.lon], {
        radius: 7 + r.risk * 18, color: color, fillColor: color, fillOpacity: 0.22, weight: 2,
      }).bindTooltip(r.neighbourhood + ': modelled ' + r.level + ' (' + Math.round(r.risk * 100) + '%)',
        { direction: 'top' }).addTo(mapDynamic);
    });
  }
  if (showLayers.plume) {
    const reach = plumeLengthKm(h.wind);
    const pts = [[cfg.lat, cfg.lon]];
    for (let a = -20; a <= 20; a += 5) pts.push(destinationPoint(cfg.lat, cfg.lon, h.plumeTo + a, reach));
    L.polygon(pts, {
      color: levelOf(h.maxRisk) === 'high' ? 'rgba(239,68,68,0.5)'
        : levelOf(h.maxRisk) === 'moderate' ? 'rgba(251,191,36,0.5)' : 'rgba(100,150,200,0.35)',
      fillOpacity: 0.13, weight: 1,
    }).bindTooltip('Modelled plume cone — estimate only. Extent grows with wind speed; absence of overlap does not mean no smell.').addTo(mapDynamic);
  }
  const home = hoodCoords();
  if (home) {
    L.marker(home, {
      icon: L.divIcon({
        html: '<div style="width:16px;height:16px;background:#22d3ee;border-radius:50%;border:2.5px solid white;box-shadow:0 0 8px rgba(34,211,238,0.7);"></div>',
        iconSize: [16, 16], className: '',
      }),
    }).bindTooltip('You: ' + state.hood, { permanent: true, direction: 'top', className: 'map-tooltip' }).addTo(mapDynamic);
    L.polyline([[cfg.lat, cfg.lon], home], { color: '#22d3ee', weight: 1.5, dashArray: '6,6', opacity: 0.7 }).addTo(mapDynamic);
    const km = haversineKm(cfg.lat, cfg.lon, home[0], home[1]);
    L.marker([(cfg.lat + home[0]) / 2, (cfg.lon + home[1]) / 2]).bindTooltip(
      km.toFixed(1) + ' km straight-line', { direction: 'center', className: 'map-tooltip' }).addTo(mapDynamic);
  }
  if (showLayers.reports) {
    allReportsForSite(state.site).forEach(r => {
      if (r.lat == null || r.lon == null) return;
      L.circleMarker([r.lat, r.lon], {
        radius: 5, color: r.demo ? '#c084fc' : '#a855f7', fillColor: r.demo ? 'transparent' : '#a855f7',
        fillOpacity: 0.6, weight: 1, dashArray: r.demo ? '3,3' : null,
      }).bindTooltip((r.demo ? '[DEMO] ' : 'Observation: ') + r.neighbourhood + ' — '
        + intensityLabel(r.intensity) + ' (resident report, not a measurement)').addTo(mapDynamic);
    });
  }
  renderMapInfoPanel(h);
}

function renderMapInfoPanel(h) {
  const panel = document.getElementById('map-infopanel');
  const home = hoodCoords();
  if (!home) { panel.innerHTML = ''; return; }
  const cfg = siteData().config;
  const dist = haversineKm(cfg.lat, cfg.lon, home[0], home[1]);
  const b = bearingDumpToHood(home);
  const diff = angleDiff(h.plumeTo, b);
  const diffFrom = angleDiff(h.wind.wind_direction_10m, b);
  const hoodRisk = h.hoodRisk != null ? h.hoodRisk : h.maxRisk;
  const pos = diff < 45 ? 'Downwind' : diffFrom < 45 ? 'Upwind' : 'Crosswind';
  const reach = plumeLengthKm(h.wind);

  let badgeClass, badgeText;
  if (pos === 'Downwind') {
    badgeClass = hoodRisk >= RISK_HIGH ? 'downwind-high' : 'downwind-mod';
    badgeText = 'Potential downwind impact — model estimate';
  } else if (pos === 'Upwind') {
    badgeClass = 'away';
    badgeText = 'Wind blows from your side towards the dump — lower modelled impact';
  } else {
    badgeClass = 'uncertain';
    badgeText = 'Crosswind — impact uncertain in this simple model';
  }
  let note = 'Estimates use wind direction, distance, time of day and rain only — not measured gas concentrations. ';
  if (dist > reach) {
    note += 'Your locality sits beyond the modelled plume reach (~' + reach.toFixed(1)
      + ' km at this wind speed), so downwind position alone does not imply odour arrives here.';
  } else if (pos === 'Downwind') {
    note += 'Distance (' + dist.toFixed(1) + ' km) is inside the modelled reach at this wind speed.';
  }
  panel.innerHTML =
    '<div class="infopanel-title">' + (state.mode === 'demo' ? 'DEMO impact · ' : '') + state.hood + '</div>'
    + '<div class="infopanel-row"><span>Straight-line distance</span><b>' + dist.toFixed(1) + ' km</b></div>'
    + '<div class="infopanel-row"><span>Wind</span><b>' + h.wind.wind_speed_10m + ' m/s from '
      + Math.round(h.wind.wind_direction_10m) + '°</b></div>'
    + '<div class="infopanel-row"><span>Air travels towards</span><b>' + Math.round(h.plumeTo) + '°</b></div>'
    + '<div class="infopanel-row"><span>Your position vs plume</span><b>' + pos + '</b></div>'
    + '<div class="infopanel-row"><span>Modelled risk for you</span><b style="color:'
      + riskColorCss(levelOf(hoodRisk)) + '">' + levelWord(levelOf(hoodRisk)) + ' (' + Math.round(hoodRisk * 100) + '%)</b></div>'
    + '<div class="impact-badge ' + badgeClass + '">' + badgeText + '</div>'
    + '<div class="infopanel-note">' + note + '</div>';
}

function createWindParticle(w, h) {
  return { x: Math.random() * w, y: Math.random() * h, age: Math.random() * 100,
           maxAge: 80 + Math.random() * 40, speed: 0.5 + Math.random() * 1.5 };
}
function animateWindMap() {
  if (!windCanvasCtx || currentTab !== 'map') { requestAnimationFrame(animateWindMap); return; }
  const canvas = windCanvasCtx.canvas;
  const w = canvas.width, h = canvas.height;
  if (w === 0 || h === 0 || !hours().length || !windMap) { requestAnimationFrame(animateWindMap); return; }
  const cur = hours()[Math.min(state.idx, hours().length - 1)];
  windCanvasCtx.clearRect(0, 0, w, h);
  if (!showWind) { requestAnimationFrame(animateWindMap); return; }

  const windSpd = cur.wind.wind_speed_10m || 2;
  const radians = toRad(cur.plumeTo - 90);
  const vx = Math.cos(radians) * windSpd * 0.8;
  const vy = Math.sin(radians) * windSpd * 0.8;
  const risk = cur.maxRisk;

  windParticles.forEach(p => {
    p.x += vx * p.speed; p.y += vy * p.speed; p.age++;
    if (p.age > p.maxAge || p.x < -10 || p.x > w + 10 || p.y < -10 || p.y > h + 10) {
      Object.assign(p, createWindParticle(w, h)); p.age = 0;
    }
    const alpha = Math.sin((p.age / p.maxAge) * Math.PI) * 0.6;
    windCanvasCtx.beginPath();
    windCanvasCtx.moveTo(p.x, p.y);
    windCanvasCtx.lineTo(p.x - vx * 3, p.y - vy * 3);
    windCanvasCtx.strokeStyle = risk > 0.3 ? `rgba(251, 191, 36, ${alpha})` : `rgba(200, 230, 255, ${alpha * 0.7})`;
    windCanvasCtx.lineWidth = 1.5;
    windCanvasCtx.stroke();
  });

  // Wavefronts sweeping out of the dump in the wind direction
  if (showLayers.plume && risk > 0.1) {
    const cfgp = siteData().config;
    const pt = windMap.latLngToContainerPoint([cfgp.lat, cfgp.lon]);
    const face = Math.atan2(vy, vx);
    const t = Date.now() / 16;
    for (let k = 0; k < 3; k++) {
      const r = ((t + k * 70) % 210) + 12;
      windCanvasCtx.beginPath();
      windCanvasCtx.arc(pt.x, pt.y, r, face - 0.6, face + 0.6);
      windCanvasCtx.strokeStyle = `rgba(196, 164, 90, ${(1 - r / 222) * 0.3 * (0.3 + 0.7 * risk)})`;
      windCanvasCtx.lineWidth = 2.5;
      windCanvasCtx.stroke();
    }
  }
  requestAnimationFrame(animateWindMap);
}
function toggleWindLayer() { showWind = document.getElementById('toggle-wind').checked; }
function toggleLayer(name) { showLayers[name] = document.getElementById('toggle-' + name).checked; updateWindMap(); }

/* ---------- PLANNER ---------- */
function plannerPdata() {
  const hs = hours();
  return hs.map(h => h.p || {
    time: h.time, hour: istHour(h.time), avg_risk: h.maxRisk, max_risk: h.maxRisk,
    worst_neighbourhood: h.worst ? h.worst.neighbourhood : '-',
    classification: h.maxRisk < 0.15 ? 'recommended' : h.maxRisk < 0.35 ? 'moderate' : 'avoid',
    wind_dir: Math.round(h.wind.wind_direction_10m), wind_speed: h.wind.wind_speed_10m,
    precipitation: h.wind.precipitation, temperature: h.wind.temperature_2m,
    is_night: istHour(h.time) >= 20 || istHour(h.time) < 6,
    reason: 'Derived from modelled risk for this hour.',
  });
}
function initPlannerControls() {
  const sel = document.getElementById('planner-start');
  const pdata = plannerPdata();
  sel.innerHTML = '';
  pdata.forEach((p, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = fmtLong.format(new Date(p.time)) + ' IST';
    sel.appendChild(opt);
  });
  sel.value = state.ops ? Math.min(state.ops.start, pdata.length - 1) : 0;
}
function plannerActivityChanged() {
  const act = document.getElementById('planner-activity');
  const dur = act.options[act.selectedIndex].getAttribute('data-dur');
  document.getElementById('planner-duration').value = dur;
  renderPlanner();
}
function windowScore(pdata, start, dur) {
  let avoid = 0, mod = 0, sum = 0, n = 0;
  for (let i = start; i < Math.min(start + dur, pdata.length); i++) {
    const c = pdata[i].classification;
    if (c === 'avoid') avoid++; else if (c === 'moderate') mod++;
    sum += pdata[i].avg_risk; n++;
  }
  return { avoid, mod, avg: n ? sum / n : 0, full: n === dur };
}
function findAlternatives(pdata, dur) {
  const scored = [];
  for (let s = 0; s + dur <= pdata.length; s++) scored.push({ s, sc: windowScore(pdata, s, dur) });
  scored.sort((a, b) => (a.sc.avoid - b.sc.avoid) || (a.sc.avg - b.sc.avg));
  const picked = [];
  for (const cand of scored) {
    if (picked.length >= 3) break;
    if (picked.every(p => cand.s < p.s || cand.s >= p.s + dur)) picked.push({ s: cand.s, sc: cand.sc });
  }
  return picked;
}
function renderPlanner() {
  const pdata = plannerPdata();
  if (!pdata.length) return;
  const sel = document.getElementById('planner-start');
  const pkey = state.site + '|' + state.mode + '|' + pdata.length;
  if (renderPlanner._key !== pkey) { initPlannerControls(); renderPlanner._key = pkey; }
  const startProp = Math.min(parseInt(sel.value || '0', 10) || 0, pdata.length - 1);
  const dur = Math.max(1, Math.min(12, parseInt(document.getElementById('planner-duration').value || '6', 10) || 6));

  const grid = document.getElementById('planner-grid');
  grid.innerHTML = '';
  pdata.forEach((p, i) => {
    const cell = document.createElement('div');
    cell.className = 'planner-cell ' + p.classification;
    if (state.ops && i >= state.ops.start && i < state.ops.start + state.ops.dur) cell.classList.add('ops-on');
    if (i >= startProp && i < startProp + dur) cell.classList.add('selected');
    cell.textContent = istHM(p.time);
    cell.title = fmtLong.format(new Date(p.time)) + ' IST — ' + p.reason;
    cell.onclick = () => { sel.value = i; showPlannerHour(i); renderPlanner(); setIdx(i); };
    grid.appendChild(cell);
  });

  const baseline = state.ops ? state.ops.start : 0;
  const baseScore = windowScore(pdata, baseline, dur);
  const propScore = windowScore(pdata, startProp, dur);
  const dAvoid = propScore.avoid - baseScore.avoid;
  const dAvg = propScore.avg - baseScore.avg;
  const actName = document.getElementById('planner-activity').selectedOptions[0].textContent;
  const cmp = document.getElementById('planner-compare');
  cmp.innerHTML =
    '<h3 style="font-size:15px;font-weight:700;">Current vs proposed window</h3>'
    + '<p style="font-size:12px;color:var(--text-muted);margin:4px 0 2px;">Activity: ' + esc(actName) + ' for ' + dur
    + ' h — ' + (propScore.full ? 'window fits inside the 48 h horizon' : 'window extends past the modelled horizon; scores cover available hours only')
    + '. Baseline: ' + (state.ops ? 'applied schedule' : 'start of horizon (immediately)') + '.</p>'
    + '<table class="cmp-table"><tr><th></th><th>Higher-risk hours</th><th>Moderate hours</th><th>Avg modelled risk</th></tr>'
    + '<tr><td>Current start</td><td>' + baseScore.avoid + '</td><td>' + baseScore.mod + '</td><td>' + Math.round(baseScore.avg * 100) + '%</td></tr>'
    + '<tr><td>Proposed start</td><td>' + propScore.avoid + '</td><td>' + propScore.mod + '</td><td>' + Math.round(propScore.avg * 100) + '%</td></tr>'
    + '<tr><td><b>Change</b></td><td class="' + (dAvoid < 0 ? 'delta-good' : dAvoid > 0 ? 'delta-bad' : 'delta-neutral') + '">'
    + (dAvoid > 0 ? '+' : '') + dAvoid + '</td><td></td><td class="' + (dAvg < 0 ? 'delta-good' : dAvg > 0 ? 'delta-bad' : 'delta-neutral') + '">'
    + (dAvg > 0 ? '+' : '') + Math.round(dAvg * 100) + ' pts</td></tr></table>'
    + '<p style="font-size:11.5px;color:var(--text-muted);margin-top:8px;">These are model estimates to help prioritise work — they do NOT claim a measured reduction in community exposure.</p>'
    + '<button class="btn-apply-ops" onclick="applyOps(' + startProp + ',' + dur + ')">Apply this window (scene + map reflect it)</button>';

  const alts = findAlternatives(pdata, dur).filter(a => a.s !== startProp);
  const altBox = document.getElementById('planner-alternatives');
  altBox.innerHTML = '<h3 style="font-size:15px;font-weight:700;">Alternative windows</h3>'
    + (alts.length ? alts.map(a =>
        '<button class="alt-btn" onclick="useAltStart(' + a.s + ')">'
        + fmtLong.format(new Date(pdata[a.s].time)) + ' IST · ' + a.sc.avoid + ' higher-risk h · avg '
        + Math.round(a.sc.avg * 100) + '% — use this window</button>').join('')
      : '<p style="font-size:12.5px;color:var(--text-muted);">No distinct alternatives found within the horizon for this duration.</p>');

  const counts = { recommended: 0, moderate: 0, avoid: 0 };
  pdata.forEach(p => counts[p.classification]++);
  document.getElementById('planner-summary').innerHTML =
    '<strong>48-Hour Summary:</strong> '
    + '<span style="color:var(--accent-green)">' + counts.recommended + ' lower-risk hours</span> · '
    + '<span style="color:var(--accent-amber)">' + counts.moderate + ' moderate hours</span> · '
    + '<span style="color:var(--accent-red)">' + counts.avoid + ' higher-risk hours</span>'
    + ' — totals are over the ' + pdata.length + ' modelled hours actually in the horizon.'
    + '<br><em style="color:var(--text-muted);font-size:12px;">Based on modelled wind-based odour risk. A planning aid, not a measured air-quality forecast. '
    + (state.mode === 'demo' ? 'DEMO scenario data — deterministic and repeatable, not a real forecast.' : '') + '</em>';
}
function useAltStart(s) {
  document.getElementById('planner-start').value = s;
  renderPlanner();
  setIdx(s);
}
function applyOps(start, dur) {
  const actLabel = document.getElementById('planner-activity').selectedOptions[0].textContent;
  state.ops = { start, dur, activity: actLabel, isDefault: false };
  saveState();
  setIdx(start);
  renderPlanner();
}
function showPlannerHour(i) {
  const pdata = plannerPdata();
  const p = pdata[i];
  if (!p) return;
  const classLabel = p.classification === 'recommended' ? '✅ Recommended for operations'
    : p.classification === 'moderate' ? '⚡ Moderate risk — proceed with caution'
    : '⛔ Higher risk — consider rescheduling';
  document.getElementById('planner-detail-title').textContent = fmtFull.format(new Date(p.time)) + ' IST';
  document.getElementById('planner-detail-body').innerHTML =
    '<div style="font-size:15px;font-weight:600;margin-bottom:8px;color:'
    + (p.classification === 'recommended' ? 'var(--accent-green)' : p.classification === 'moderate' ? 'var(--accent-amber)' : 'var(--accent-red)')
    + '">' + classLabel + (state.mode === 'demo' ? ' <span class="demo-tag">DEMO</span>' : '') + '</div>'
    + '<p><strong>Wind:</strong> ' + p.wind_speed + ' m/s from ' + p.wind_dir + '° · <strong>Temp:</strong> '
    + p.temperature + '°C · <strong>Rain:</strong> ' + p.precipitation + ' mm</p>'
    + '<p><strong>Max modelled risk:</strong> ' + Math.round(p.max_risk * 100) + '% — worst for ' + esc(p.worst_neighbourhood) + '</p>'
    + '<p><strong>Reason:</strong> ' + esc(p.reason) + '</p>'
    + (p.is_night ? '<p style="color:var(--text-muted);font-size:12px;">Night hours — atmospheric inversions may trap odour closer to ground level.</p>' : '');
}

/* ---------- REPORTS ---------- */
function parseIST(s) {
  if (!s) return null;
  let t = String(s).trim().replace(' ', 'T');
  if (/^\d{4}-\d{2}-\d{2}T/.test(t) && !/[+Z]/.test(t)) t += '+05:30';  // naive = IST by convention
  const d = new Date(t);
  return isNaN(d) ? null : d;
}
function istISO(d) {
  const t = new Date(d.getTime() + 5.5 * 3600 * 1000);
  const p = n => String(n).padStart(2, '0');
  return t.getUTCFullYear() + '-' + p(t.getUTCMonth() + 1) + '-' + p(t.getUTCDate())
    + 'T' + p(t.getUTCHours()) + ':' + p(t.getUTCMinutes()) + ':' + p(t.getUTCSeconds())
    + '.' + String(t.getUTCMilliseconds()).padStart(3, '0') + '+05:30';
}
function intensityCategory(v) {
  v = parseInt(v, 10);
  if (isNaN(v)) return 'Unknown';
  if (v <= 1) return 'None';
  if (v === 2) return 'Slight';
  if (v === 3) return 'Moderate';
  if (v === 4) return 'Strong';
  return 'Very Strong';
}
function intensityLabel(v) { return 'Smell intensity: ' + v + ' of 5 — ' + intensityCategory(v); }
function getDemoObs() { try { return JSON.parse(localStorage.getItem(DEMO_OBS_KEY)) || []; } catch (e) { return []; } }
function allReportsForSite(site) {
  const real = window.liveReports.filter(r => r.site === site)
    .map(r => Object.assign({ demo: false }, r));
  const demo = getDemoObs().filter(r => r.site === site);
  return real.concat(demo);
}
function populateReportAreaSelect() {
  const sel = document.getElementById('report-area');
  sel.innerHTML = '';
  Object.keys(siteData().neighbourhoods).forEach(n => {
    const opt = document.createElement('option');
    opt.value = n; opt.textContent = n;
    sel.appendChild(opt);
  });
  if (state.hood) sel.value = state.hood;
}
function setIntensity(v) {
  selectedIntensity = v;
  document.querySelectorAll('.intensity-btn').forEach(b =>
    b.classList.toggle('selected', parseInt(b.dataset.val, 10) === v));
  const rd = document.getElementById('intensity-readout');
  if (rd) rd.textContent = intensityLabel(v);
}
function renderReportsLocContext() {
  const el = document.getElementById('reports-loc-context');
  if (!el) return;
  const km = hoodDistanceKm();
  el.innerHTML = 'You are reporting as <b>' + esc(state.hood) + '</b> near the <b>' + esc(state.site)
    + '</b> dump' + (km != null ? ' (' + km.toFixed(1) + ' km away)' : '')
    + ' · selected hour ' + fmtLong.format(new Date(hours()[state.idx] ? hours()[state.idx].time : Date.now())) + ' IST. '
    + '<button type="button" onclick="openLocationModal()">Change location</button>'
    + (state.mode === 'demo' ? ' <span class="demo-tag">DEMO MODE — model context is the scripted scenario</span>' : '');
}
async function submitReport(e) {
  e.preventDefault();
  const hoodName = document.getElementById('report-area').value;
  const coords = siteData().neighbourhoods[hoodName];
  if (!coords) return;
  const btn = document.getElementById('btn-submit-report');
  const err = document.getElementById('report-error');
  err.textContent = '';
  const payload = {
    id: uuid4(),
    site: state.site,
    time_ist: istISO(new Date()),
    neighbourhood: hoodName,
    lat: coords[0], lon: coords[1],
    intensity: selectedIntensity,
    note: document.getElementById('report-note').value,
    windows_open: document.getElementById('report-windows').checked,
  };
  btn.disabled = true;
  btn.textContent = 'Saving...';
  try {
    const r = await fetch(bridgeUrl('/api/report'), {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'save failed');
    await refreshReports();
    document.getElementById('report-note').value = '';
    btn.textContent = j.deduped ? '✓ Already saved' : '✓ Observation Saved';
    const cs = document.getElementById('report-char-speech');
    if (cs) cs.textContent = selectedIntensity <= 1
      ? 'Thanks! Knowing there is no smell right now helps too — it tests the model from both sides.'
      : 'Thank you. ' + (selectedIntensity >= 4 ? 'Sorry about the conditions. ' : '')
        + 'Your note is stored as a resident observation alongside the modelled risk for this hour.';
  } catch (ex) {
    err.textContent = 'Could not reach the local save service (' + ex.message
      + '). Your report was NOT stored. Retry, or use the backup report form in the Streamlit sidebar — it writes to the same file.';
  } finally {
    btn.disabled = false;
    setTimeout(() => { btn.textContent = 'Submit Observation'; }, 2500);
  }
}
async function refreshReports() {
  try {
    const r = await fetch(bridgeUrl('/api/reports'));
    const j = await r.json();
    window.liveReports = j.reports || [];
  } catch (e) { /* keep the snapshot injected at page load */ }
  renderReportList();
}
function addDemoObservation() {
  const h = hours()[state.idx];
  const risk = h ? (h.hoodRisk != null ? h.hoodRisk : h.maxRisk) : 0;
  const intensity = risk < 0.15 ? 1 : risk < 0.3 ? 2 : risk < 0.5 ? 3 : risk < 0.75 ? 4 : 5;
  const obs = getDemoObs();
  const coords = siteData().neighbourhoods[state.hood];
  obs.push({
    id: uuid4(), demo: true, site: state.site, neighbourhood: state.hood,
    lat: coords[0], lon: coords[1], time_ist: istISO(new Date()),
    intensity, note: 'Fictional demo observation generated from modelled risk — not a real resident report.',
    windows_open: false,
  });
  try { localStorage.setItem(DEMO_OBS_KEY, JSON.stringify(obs)); } catch (e) {}
  renderReportList();
}
function renderReportList() {
  const list = document.getElementById('report-list');
  if (!list) return;
  const reports = allReportsForSite(state.site)
    .map(r => ({ r, d: parseIST(r.time_ist) }))
    .sort((a, b) => (b.d ? b.d.getTime() : 0) - (a.d ? a.d.getTime() : 0));
  list.innerHTML = '';
  if (!reports.length) {
    list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">No reports yet for '
      + esc(state.site) + '. Be the first to share an observation.</div>';
    renderReportStats(reports);
    return;
  }
  reports.slice(0, 30).forEach(({ r }) => {
    const d = parseIST(r.time_ist);
    const div = document.createElement('div');
    div.className = 'report-item' + (r.demo ? ' demo' : '');
    div.innerHTML =
      '<div class="report-item-left">'
      + '<div class="report-item-area">' + esc(r.neighbourhood)
      + (r.demo ? '<span class="demo-tag">DEMO</span>' : '<span class="obs-tag">OBSERVATION</span>')
      + '</div>'
      + '<div class="report-item-time">' + intensityLabel(r.intensity)
      + ' · ' + (d ? fmtLong.format(d) + ' IST' : esc(r.time_ist))
      + (r.windows_open ? ' · windows open' : '') + '</div>'
      + (r.note ? '<div class="report-item-time" style="font-style:italic;">"' + esc(r.note) + '"</div>' : '')
      + '</div>'
      + '<div class="report-item-intensity" style="color:'
      + (r.intensity >= 4 ? 'var(--accent-red)' : r.intensity >= 3 ? 'var(--accent-amber)' : 'var(--accent-green)')
      + '">' + r.intensity + '/5</div>';
    list.appendChild(div);
  });
  renderReportStats(reports);
}
function renderReportStats(reports) {
  const stats = document.getElementById('report-stats');
  if (!stats) return;
  const real = reports.filter(x => !x.r.demo);
  const demoN = reports.length - real.length;
  if (!reports.length) { stats.innerHTML = ''; return; }
  const dist = [1, 2, 3, 4, 5].map(v => real.filter(x => parseInt(x.r.intensity, 10) === v).length);
  const maxD = Math.max(1, ...dist);
  let html = '<h4 style="font-size:13px;font-weight:700;margin-bottom:6px;">Report Summary — ' + esc(state.site) + '</h4>'
    + '<p style="font-size:13px;color:var(--text-secondary);">' + real.length + ' resident observation'
    + (real.length === 1 ? '' : 's') + (demoN ? ' · ' + demoN + ' demo record' + (demoN === 1 ? '' : 's') + ' (separate, clearly marked)' : '')
    + ' — observations, not pollution measurements.</p>'
    + [1, 2, 3, 4, 5].map((v, i) =>
        '<div class="stat-bar-row"><span style="min-width:96px;">' + intensityLabel(v) + '</span>'
        + '<div class="stat-bar-track"><div class="stat-bar-fill" style="width:' + (dist[i] / maxD * 100) + '%"></div></div>'
        + '<span>' + dist[i] + '</span></div>').join('');
  if (real.length) {
    html += '<p style="font-size:11.5px;color:var(--text-muted);margin-top:6px;">Latest: '
      + real.slice(0, 3).map(x => x.d ? fmtLong.format(x.d) + ' IST' : '').filter(Boolean).join(' · ') + '</p>';
  }
  // Report-rate vs modelled-risk-period comparison (counts opportunities)
  if (real.length >= 5) {
    const hs = hours();
    if (hs.length > 1) {
      const t0 = new Date(hs[0].time).getTime();
      const catHours = { high: 0, mid: 0, low: 0 };
      hs.forEach(h => { const l = levelOf(h.maxRisk); catHours[l === 'high' ? 'high' : l === 'moderate' ? 'mid' : 'low']++; });
      const catReps = { high: 0, mid: 0, low: 0 };
      let matched = 0;
      real.forEach(({ d }) => {
        if (!d) return;
        const idx = Math.round((d.getTime() - t0) / 3600000);
        if (idx < 0 || idx >= hs.length) return;
        matched++;
        const l = levelOf(hs[idx].maxRisk);
        catReps[l === 'high' ? 'high' : l === 'moderate' ? 'mid' : 'low']++;
      });
      if (matched >= 3) {
        const rate = c => catHours[c] ? (catReps[c] / catHours[c]).toFixed(2) : '—';
        html += '<p style="font-size:11.5px;color:var(--text-secondary);margin-top:8px;">Within the modelled horizon, '
          + matched + ' observations fall in: ' + catReps.high + ' during ' + catHours.high
          + ' higher-risk hours (' + rate('high') + '/h), ' + catReps.mid + ' during ' + catHours.mid
          + ' moderate hours (' + rate('mid') + '/h), ' + catReps.low + ' during ' + catHours.low
          + ' lower-risk hours (' + rate('low') + '/h). Rates account for how many hours of each kind actually occurred.</p>';
      } else {
        html += '<p style="font-size:11.5px;color:var(--text-muted);margin-top:8px;">Too few observations fall inside the current modelled horizon for a risk-period comparison.</p>';
      }
    }
  } else {
    html += '<p style="font-size:11.5px;color:var(--text-muted);margin-top:8px;">Statistical comparison of report rates with risk periods needs at least 5 real reports.</p>';
  }
  stats.innerHTML = html;
}

/* ---------- SATELLITE ---------- */
function renderSatelliteChips(container, forLoc) {
  const el = container || document.getElementById('sat-site-chips');
  if (!el) return;
  el.innerHTML = '';
  Object.keys(APP_DATA.sites).forEach(s => {
    const active = forLoc ? (s === locDraft.site) : (s === state.site);
    const b = document.createElement('button');
    b.className = 'site-chip' + (active ? ' active' : '');
    b.textContent = s;
    b.onclick = () => { forLoc ? selectLocSite(s) : setSite(s); };
    el.appendChild(b);
  });
}
function satPayload(site) {
  return (state.satLive && state.satLive[site]) || APP_DATA.sites[site].fire;
}
function satStateText(p) {
  const st = p.status;
  const days = st.days != null ? st.days : APP_DATA.satellite_days;
  const radius = APP_DATA.sites[st.site] ? APP_DATA.sites[st.site].config.radius_km : st.radius;
  if (st.state === 'ok') {
    return { cls: p.verdict && p.verdict.is_fire ? 'fire' : 'clear',
      head: p.verdict && p.verdict.is_fire ? '🔥 Thermal anomalies suggest fire' : '✅ Live FIRMS query succeeded',
      body: p.detections.length + ' detection(s) within ' + radius + ' km of ' + st.site
        + ' over the last ' + days + ' day(s). ' + (p.verdict ? p.verdict.reason : '') };
  }
  if (st.state === 'ok_empty') {
    return { cls: 'clear', head: '✅ Live FIRMS query succeeded — no detections',
      body: '0 thermal anomalies within ' + radius + ' km of ' + st.site + ' for the queried range. '
        + 'A quiet map is NOT a guarantee of safety: satellite passes are intermittent.' };
  }
  if (st.state === 'no_key') {
    return { cls: 'warn', head: '🔑 Satellite integration not configured',
      body: st.error || 'FIRMS_MAP_KEY is not set. A missing key is different from a successful query that returned nothing.' };
  }
  return { cls: 'err', head: '❌ Live query failed (integration problem)',
    body: String(st.error || 'unknown error') + ' — this is a failed query, not a clean sky.' };
}
function renderSatellite() {
  const p = satPayload(state.site);
  const el = document.getElementById('fire-verdict');
  const meta = document.getElementById('sat-query-meta');
  if (!el || !p) return;
  if (!p.status) {
    el.className = 'fire-verdict err';
    el.innerHTML = '<strong>❌ Malformed satellite payload</strong><p>' + esc(JSON.stringify(p).slice(0, 200)) + '</p>';
    return;
  }
  const t = satStateText(p);
  document.getElementById('sat-demo-toggle').checked = !!state.satDemo;
  document.getElementById('sat-scenario').value = state.satScenario;
  document.getElementById('sat-demo-ribbon').classList.toggle('hidden', !state.satDemo);

  let html = '<strong style="color:' + (t.cls === 'fire' ? 'var(--accent-red)' : t.cls === 'clear' ? 'var(--accent-green)' : t.cls === 'warn' ? 'var(--accent-amber)' : '#f87171')
    + '">' + t.head + '</strong><p>' + esc(t.body) + '</p>';
  if (p.verdict && p.verdict.is_fire && p.verdict.first_ist) {
    html += '<p style="font-size:12px;">First detection (IST): ' + fmtLong.format(parseIST(p.verdict.first_ist) || new Date(p.verdict.first_ist))
      + ' · ' + p.verdict.n_pixels + ' pixels · max FRP ' + Number(p.verdict.max_frp).toFixed(1) + ' MW. Thermal anomaly — verify with ground observation.</p>';
  }
  if (state.satDemo) {
    html += '<p style="margin-top:8px;color:#c084fc;font-size:12px;"><b>DEMO test mode is ON</b> — scenario "' + state.satScenario
      + '". Demo markers/panels below are fictional and prove NOTHING about the live integration; check the live status above.</p>';
  }
  el.className = 'fire-verdict ' + t.cls;
  el.innerHTML = html;

  let mhtml = 'Last live query: ' + (p.status.query_time_utc
    ? fmtLong.format(new Date(p.status.query_time_utc)) + ' IST' : 'never')
    + '<br>Queried range (UTC): ' + (p.status.range_start_utc || '?') + ' → ' + (p.status.range_end_utc || '?')
    + ' · sources: ' + (p.status.sources || []).join(', ');
  if (p.status.warnings && p.status.warnings.length) mhtml += '<br>Warnings: ' + esc(p.status.warnings.join(' | '));
  meta.innerHTML = mhtml;

  if (smokeMap) renderSatelliteLayers(p);
  renderFireTimeline(p);
}
function demoSatDetection(cfg, scenario) {
  const now = new Date();
  const daysAgo = scenario === 'stale' ? 4 : 0;
  const t = new Date(now.getTime() - daysAgo * 86400000 - 3 * 3600000);
  return {
    latitude: cfg.lat + 0.002, longitude: cfg.lon - 0.0015,
    frp: 24.6, confidence: 'H', conf: 'h',
    time_utc: t.toISOString(), time_ist: t.toISOString(),
    dist_km: haversineKm(cfg.lat, cfg.lon, cfg.lat + 0.002, cfg.lon - 0.0015),
    demo: true,
  };
}
function renderSatelliteLayers(p) {
  satLayers.clearLayers();
  const cfg = siteData().config;
  L.marker([cfg.lat, cfg.lon], {
    icon: L.divIcon({
      html: '<div style="width:16px;height:16px;background:#ef4444;border-radius:50%;border:2px solid white;"></div>',
      iconSize: [16, 16], className: '',
    }),
  }).bindTooltip(state.site + ' Dumpyard').addTo(satLayers);
  L.circle([cfg.lat, cfg.lon], { radius: cfg.radius_km * 1000, color: 'rgba(239,68,68,0.35)',
    weight: 1, dashArray: '5,5', fillOpacity: 0 }).addTo(satLayers);
  (p.detections || []).forEach(d => addDetMarker(d, false));
  if (state.satDemo && (state.satScenario === 'anomaly' || state.satScenario === 'stale')) {
    addDetMarker(demoSatDetection(cfg, state.satScenario), true);
  }
  const h = hours()[state.idx];
  if (h) {
    const plumeDir = (h.wind.wind_direction_80m + 180) % 360;
    const length = Math.min(Math.max(h.wind.wind_speed_80m * 3.6, 2), 10);
    const pts = [[cfg.lat, cfg.lon]];
    for (let a = -20; a <= 20; a += 5) pts.push(destinationPoint(cfg.lat, cfg.lon, plumeDir + a, length));
    L.polygon(pts, { color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.1, weight: 1 })
      .bindTooltip('Modelled smoke direction (80 m wind) — estimate').addTo(satLayers);
  }
}
function addDetMarker(d, isDemo) {
  const km = d.dist_km != null ? Number(d.dist_km).toFixed(2) : '--';
  L.circleMarker([d.latitude, d.longitude], {
    radius: 7, color: isDemo ? '#a855f7' : '#ef4444',
    fillColor: isDemo ? 'rgba(168,85,247,0.25)' : '#ef4444',
    fillOpacity: isDemo ? 0.5 : 0.7, weight: 2, dashArray: isDemo ? '4,4' : null,
  }).bindTooltip((isDemo ? '[DEMO FICTIONAL] ' : '') + 'FRP ' + d.frp + ' MW · conf ' + d.confidence
    + ' · ' + km + ' km · ' + fmtLong.format(new Date(d.time_ist)) + ' IST').addTo(satLayers);
}
function renderFireTimeline(p) {
  const box = document.getElementById('fire-timeline');
  const rows = [];
  (p.detections || []).forEach(d => rows.push({ d, demo: false }));
  if (state.satDemo && (state.satScenario === 'anomaly' || state.satScenario === 'stale')) {
    rows.push({ d: demoSatDetection(siteData().config, state.satScenario), demo: true });
  }
  rows.sort((a, b) => new Date(b.d.time_ist) - new Date(a.d.time_ist));
  let scenarioNote = '';
  if (state.satDemo) {
    const notes = {
      clear: 'Scenario: successful query, no detections — the map stays empty and the panel says so.',
      anomaly: 'Scenario: one fictional anomaly (~3 h old) added with a dashed DEMO marker. Live status above is unchanged.',
      stale: 'Scenario: fictional detection with a ~4-day-old timestamp — check the STALE warning chip.',
      error: 'Scenario: simulated API failure banner. No markers; this state is distinct from an empty sky.',
      empty_records: 'Scenario: successful query, no records for this exact site + range.',
    };
    scenarioNote = '<div class="fire-row" style="border-color:rgba(168,85,247,0.5);"><span class="fr-when" style="color:#c084fc;">DEMO scenario</span><span class="fr-meta">' + esc(notes[state.satScenario] || '') + '</span></div>';
  }
  box.innerHTML = (rows.length
    ? rows.map(({ d, demo }) => {
        const stale = demo && state.satScenario === 'stale';
        const ageD = (Date.now() - new Date(d.time_ist)) / 86400000;
        return '<div class="fire-row' + (demo ? ' demo-det' : '') + '">'
          + '<span class="fr-when">' + fmtLong.format(new Date(d.time_ist)) + ' IST'
          + (stale || ageD > 3 ? ' <span class="demo-tag" style="background:rgba(251,191,36,0.2);color:#fcd34d;">STALE / OLD PASS</span>' : '')
          + (demo ? '<span class="demo-tag">DEMO</span>' : '')
          + '</span>'
          + '<span class="fr-meta">FRP ' + d.frp + ' MW · conf ' + d.confidence + ' · '
          + (d.dist_km != null ? Number(d.dist_km).toFixed(2) : '--') + ' km · UTC '
          + esc(String(d.time_utc).slice(0, 16)) + '</span></div>';
      }).join('')
    : '<div style="padding:10px;color:var(--text-muted);font-size:12px;">No detections listed for the current state.</div>')
    + scenarioNote
    + '<p style="font-size:11px;color:var(--text-muted);margin-top:8px;">A thermal anomaly is a hint of heat, not a confirmed fire — satellites pass intermittently. '
    + 'Demo markers do not prove the live integration works; the live query status above does.</p>';
}
function runLiveFireQuery() {
  const btn = document.getElementById('btn-live-query');
  btn.disabled = true;
  btn.textContent = 'Querying FIRMS...';
  fetch(bridgeUrl('/api/fire?site=' + encodeURIComponent(state.site) + '&days=' + APP_DATA.satellite_days))
    .then(r => r.json())
    .then(j => {
      state.satLive = state.satLive || {};
      state.satLive[state.site] = j;
      renderSatellite();
      btn.textContent = 'Re-query FIRMS now';
    })
    .catch(ex => {
      document.getElementById('sat-query-meta').innerHTML =
        '<span style="color:#f87171;">Bridge request failed: ' + esc(ex.message)
        + ' — the embedded page may be sandboxed. Use the "Refresh satellite data" button in the Streamlit sidebar instead.</span>';
      btn.textContent = 'Re-query FIRMS now';
    })
    .finally(() => { btn.disabled = false; });
}
function setSatDemo(on) { state.satDemo = on; saveState(); renderSatellite(); }
function setSatScenario(v) { state.satScenario = v; saveState(); renderSatellite(); }

function initSmokeMap() {
  if (smokeMap) { smokeMap.invalidateSize(); renderSatellite(); return; }
  const cfg = siteData().config;
  smokeMap = L.map('smoke-map', { center: [cfg.lat, cfg.lon], zoom: 12 });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors', maxZoom: 19,
  }).addTo(smokeMap);
  smokeMap.getContainer().querySelector('.leaflet-tile-pane').style.filter =
    'brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3) brightness(0.7)';
  satLayers = L.layerGroup().addTo(smokeMap);
  renderSatellite();
  setTimeout(() => smokeMap.invalidateSize(), 200);
}

/* ---------- EVIDENCE ---------- */
function generateEvidence() {
  const sections = document.getElementById('evidence-sections');
  if (!sections) return;
  const hs = hours();
  const h = hs[Math.min(state.idx, hs.length - 1)];
  const p = satPayload(state.site);
  const modeTag = state.mode === 'demo' ? ' (DEMO scenario data)' : '';
  const reports = allReportsForSite(state.site);
  const realReports = reports.filter(x => !x.r.demo);
  const km = hoodDistanceKm();
  sections.innerHTML = `
    <div class="evidence-block">
      <h4>📋 Report Generated</h4>
      <p>Timestamp: ${istNowStr()} IST · Dataset generated: ${fmtLong.format(new Date(APP_DATA.generated_at_ist))} IST<br>
      Site: ${esc(state.site)} (${siteData().config.lat}°N, ${siteData().config.lon}°E, radius ${siteData().config.radius_km} km)<br>
      Resident context: ${esc(state.hood)}${km != null ? ' — ' + km.toFixed(1) + ' km straight-line from the dump' : ''}<br>
      Viewed hour: ${h ? fmtLong.format(new Date(h.time)) + ' IST' + modeTag : '--'} · Mode: ${state.mode.toUpperCase()}</p>
    </div>
    <div class="evidence-block">
      <h4>💨 Wind Conditions (viewed hour)${modeTag}</h4>
      ${h ? `<p>Wind speed: ${h.wind.wind_speed_10m} m/s (10 m), ${h.wind.wind_speed_80m} m/s (80 m)<br>
      Wind direction (FROM, meteorological): ${h.wind.wind_direction_10m}° — air travels towards ${Math.round(h.plumeTo)}°<br>
      Temperature: ${h.wind.temperature_2m}°C · Precipitation: ${h.wind.precipitation} mm<br>
      Source: ${state.mode === 'demo' ? 'SCRIPTED DEMO SCENARIO — ' + esc(APP_DATA.demo_scenario.name)
        : (siteData().live.is_fallback ? 'Estimated fallback (Open-Meteo unreachable)' : 'Open-Meteo API (live)')}</p>` : '<p>Wind data unavailable</p>'}
    </div>
    <div class="evidence-block">
      <h4>⚠️ Modelled Odour Risk (viewed hour)${modeTag}</h4>
      <ul>${h ? h.risks.map(r => `<li>${esc(r.neighbourhood)}: ${r.level} (${Math.round(r.risk * 100)}%)${r.neighbourhood === state.hood ? ' ← your locality' : ''}</li>`).join('') : ''}</ul>
      <p style="font-size:11px;color:var(--text-muted);margin-top:8px;">Uncalibrated model estimates from wind direction, distance, time of day and rain — NOT measured pollutant concentrations.</p>
    </div>
    <div class="evidence-block">
      <h4>👥 Resident Observations</h4>
      ${realReports.length ? `<p>${realReports.length} real observation(s) on file for ${esc(state.site)}${reports.length - realReports.length ? ' (+ ' + (reports.length - realReports.length) + ' clearly-marked demo records, excluded here)' : ''}.</p>
      <ul>${realReports.slice(0, 5).map(x => `<li>${esc(x.r.neighbourhood)}: ${intensityLabel(x.r.intensity)} at ${x.d ? fmtLong.format(x.d) + ' IST' : esc(x.r.time_ist)}</li>`).join('')}</ul>`
        : '<p>No resident observations on file for this site yet.</p>'}
      <p style="font-size:11px;color:var(--text-muted);margin-top:6px;">Reports are self-reported observations and may be sparse; they are not calibration data on their own.</p>
    </div>
    <div class="evidence-block">
      <h4>🛰️ Satellite Fire Detection (live status)</h4>
      <p>${esc(satStateText(p).head)} — ${esc(satStateText(p).body)}</p>
      <p style="font-size:11px;color:var(--text-muted);margin-top:6px;">Source: NASA FIRMS (${(p.status.sources || []).join(', ')}). Queried ${p.status.query_time_utc ? esc(String(p.status.query_time_utc).slice(0, 16)) + ' UTC' : 'never'}, range ${p.status.range_start_utc || '?'} → ${p.status.range_end_utc || '?'} (UTC). A thermal anomaly is not a confirmed fire.</p>
    </div>
    <div class="evidence-block">
      <h4>📊 Data Sources & Limitations</h4>
      <ul>
        <li>Wind data: Open-Meteo hourly forecast${state.mode === 'demo' ? ' — overridden by DEMO scenario in this view' : (siteData().live.is_fallback ? ' — currently using synthetic fallback' : ' (live)')}</li>
        <li>Fire detection: NASA FIRMS VIIRS (status shown above, per selected site)</li>
        <li>Risk model: uncalibrated wind/distance scoring (smell.py); plume cone is a footprint guess, not dispersion modelling</li>
        <li>Reports: resident observations stored locally via the app bridge (CSV)</li>
        <li>Neighbourhood points are approximate centres — verify on the map</li>
        ${(APP_DATA.data_warnings || []).map(x => '<li>Warning: ' + esc(x) + '</li>').join('')}
      </ul>
      <p style="font-size:11px;color:var(--text-muted);margin-top:8px;">This tool provides modelled estimates and planning aids. It does not measure air quality. Supplement with official monitoring data where available.</p>
    </div>`;
}
"""
