# 🌿 Dumpyard Watch

> **Early warning and monitoring system for dumpyard fires and odor dispersal.**  
> Combines near-real-time satellite thermal anomaly detection (**NASA FIRMS**), atmospheric plume dispersion modeling (**Open-Meteo wind vectors**), and crowdsourced resident odor reporting with optional automated alerts (**Telegram**).

---

## 📋 Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Step-by-Step Setup & Running Guide](#step-by-step-setup--running-guide)
  - [Step 1: Open the Project Directory](#step-1-open-the-project-directory)
  - [Step 2: Create and Activate a Virtual Environment](#step-2-create-and-activate-a-virtual-environment)
  - [Step 3: Install Required Dependencies](#step-3-install-required-dependencies)
  - [Step 4: Configure Environment Variables (.env)](#step-4-configure-environment-variables-env)
  - [Step 5: (Optional) Run Historical Backtest](#step-5-optional-run-historical-backtest)
  - [Step 6: Launch the Streamlit Web Dashboard](#step-6-launch-the-streamlit-web-dashboard)
- [Application Features & Usage](#application-features--usage)
- [Configuration & Customization](#configuration--customization)
- [Project Structure](#project-structure)
- [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## 🔭 Overview

- **🔥 Satellite Smoke Detection (`fire.py`):** Queries NASA VIIRS (SNPP, NOAA-20, NOAA-21) thermal data within a customizable radius around dump sites to detect open fires early.
- **💨 Wind-Based Smell Risk Map (`smell.py`):** Fetches hourly multi-altitude wind vectors and precipitation from Open-Meteo (with built-in offline diurnal fallback) to model the odor dispersal cone across surrounding neighborhoods.
- **👥 Resident Reports (`app.py`):** Enables residents to log live odor intensity ratings (1 to 5) and notes to calibrate and validate predictive models over time.
- **🚨 Automated Alert Dispatch (`alerts.py`):** Generates ready-to-dispatch emergency messages and optionally sends live notifications directly to municipal response teams via Telegram.

---

## 🛠️ Prerequisites

- **Python 3.8+** (Python 3.10 or 3.11 recommended)
- **pip** package manager
- **NASA FIRMS MAP Key** (Free, takes ~1 minute to receive via email: [Get NASA FIRMS Key](https://firms.modaps.eosdis.nasa.gov/api/map_key/))

---

## 🚀 Step-by-Step Setup & Running Guide

Follow these steps in order to set up and run the application.

### Step 1: Open the Project Directory

Open your terminal (PowerShell, Command Prompt, or Bash) and navigate into the project directory:

```bash
cd "d:/code/environmental hack/files"
```

---

### Step 2: Create and Activate a Virtual Environment

Using an isolated Python virtual environment is strongly recommended:

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> *Tip: If PowerShell gives a script execution policy error, run:*  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

#### On Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Required Dependencies

Ensure `pip` is up to date, then install all required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*Installed dependencies:*
- `streamlit` (interactive web dashboard framework)
- `pandas` (tabular data manipulation)
- `requests` (HTTP API communication)
- `folium` (interactive geospatial mapping and plumes)
- `python-dotenv` (automated `.env` file environment loader)

---

### Step 4: Configure Environment Variables (.env)

Open the `.env` file in the project folder (or create one if it doesn't exist):

```env
# NASA FIRMS API Map Key (Required for satellite smoke detection)
# Register for free at: https://firms.modaps.eosdis.nasa.gov/api/map_key/
FIRMS_MAP_KEY=your_firms_key_here

# Telegram Alerts (Optional: leave empty to skip Telegram push notifications)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

> **Alternative via Terminal:** You can also set `FIRMS_MAP_KEY` as an environment variable in your session:
> - **PowerShell:** `$env:FIRMS_MAP_KEY="your_firms_key_here"`
> - **Command Prompt:** `set FIRMS_MAP_KEY=your_firms_key_here`
> - **macOS / Linux:** `export FIRMS_MAP_KEY="your_firms_key_here"`

---

### Step 5: (Optional) Run Historical Backtest

You can test the satellite fire detection algorithm against known historical fire dates or measure false alarm rates during quiet periods:

```bash
python backtest.py
```

To test for false alarm rates over a quiet 30-day window:
```bash
python backtest.py --quiet-site Perungudi --quiet-start 2026-07-01 --quiet-days 30
```

---

### Step 6: Launch the Streamlit Web Dashboard

Start the live interactive dashboard:

```bash
streamlit run app.py
```

Upon launching, Streamlit will display the local address in your terminal:
```text
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Open `http://localhost:8501` in your browser.

---

## 🖥️ Application Features & Usage

Once the dashboard is open in your browser:

### 1. Sidebar Controls
- **Dump site selector:** Switch between monitored dump sites (e.g., `Perungudi`, `Kodungaiyur`).
- **Status alerts:** Warns if `FIRMS_MAP_KEY` is missing or if fallback weather is active.

### 2. 🛰️ Smoke Tab (Satellite Detection)
- Use the **Look back (days)** slider (1–3 days) to check recent satellite passes.
- Satellite heat detections (~375 m pixel resolution) appear as red dots with Fire Radiative Power (FRP) and confidence scores.
- An 80m high-altitude smoke dispersion cone illustrates the downwind direction.
- If a fire signal is detected:
  - Generates a ready-to-copy message for the fire department / corporation.
  - Automatically logs the incident in `data/alerts.csv` (and sends a Telegram message if configured).
  - Click **"Log: corporation responded now"** when emergency services acknowledge the alert to compute and record response time.

### 3. 💨 Smell Risk Map Tab
- Slide through hourly forecasts (IST) over past and future 48-hour periods.
- Displays live wind speed, wind direction, and rainfall metrics.
- Neighborhood circles are highlighted and color-coded by estimated odor risk:
  - 🟢 **Low**
  - 🟡 **Moderate**
  - 🔴 **High**
- Displays a downwind footprint cone (10m ground wind) and issues health advisories (e.g., closing windows during high risk).

### 4. 📝 Resident Reports Tab
- **Report Odor:** Residents select their neighborhood, rate odor intensity on a 1–5 scale, and optionally attach notes.
- **Complaint Heatmap / Clusters:** Aggregates submitted complaints by neighborhood and average intensity.
- **Model Calibration Check:** Correlates reported incidents with model risk levels to validate whether predictions match on-the-ground reality.

---

## ⚙️ Configuration & Customization

Coordinates, neighborhoods, and detection parameters are managed in [config.py](file:///d:/code/environmental%20hack/files/config.py):

- **Dump Site Coordinates (`SITES`):**
  Adjust center coordinates and radius:
  ```python
  SITES = {
      "Perungudi":   {"lat": 12.9600, "lon": 80.2400, "radius_km": 2.0},
      "Kodungaiyur": {"lat": 13.1380, "lon": 80.2560, "radius_km": 2.0},
  }
  ```
- **Neighborhood Coordinates (`NEIGHBOURHOODS`):**
  Add or refine center points for surrounding residential areas.
- **Satellite Sources (`LIVE_SOURCES` & `HISTORY_SOURCES`):**
  Toggle between near-real-time (`NRT`) and archival science (`SP`) VIIRS feeds.

---

## 📁 Project Structure

```text
├── app.py              # Main Streamlit web application & UI
├── config.py           # Site coordinates, neighborhoods & environment loader
├── fire.py             # NASA FIRMS API connector & fire classification logic
├── smell.py            # Wind data fetcher, fallback model & smell dispersion
├── alerts.py           # Incident logger, response timing & Telegram dispatch
├── backtest.py         # Validation suite for testing known past fires
├── requirements.txt    # Python dependencies
├── .env                # Local environment secrets & API credentials
├── known_fires.csv     # Benchmark dataset for backtesting fire recall
└── data/               # Persistent data storage (auto-generated)
    ├── alerts.csv      # Fire alerts and corporation response log
    └── reports.csv     # Crowdsourced resident odor reports
```

---

## ❓ Troubleshooting & FAQs

1. **"FIRMS_MAP_KEY not set" warning:**
   - Verify that your `.env` file exists and has `FIRMS_MAP_KEY=<your_key>` without spaces or quotes, or export it in your shell prior to running the app.

2. **Open-Meteo connection failure / Offline networks:**
   - `smell.py` includes a built-in realistic diurnal fallback generator modeled after Chennai's coastal wind patterns (daytime sea breezes and night land breezes). The app will automatically fall back to this mode if Open-Meteo is unreachable.

3. **Port 8501 is already in use:**
   - Run Streamlit on a custom port:
     ```bash
     streamlit run app.py --server.port 8502
     ```

4. **Resetting submitted reports or alert logs:**
   - Delete or clear the files inside the `data/` directory (`data/reports.csv` and `data/alerts.csv`). The app will regenerate fresh CSV files when new alerts or reports occur.
