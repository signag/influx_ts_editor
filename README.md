# InfluxDB Editor

A browser-based editor for time series data stored in an **InfluxDB v2** database.  
The application is a Flask backend + W3.css/Chart.js frontend, packaged as a Docker container.

---

## Features

* **Browse** buckets, measurements, tag key/value pairs and field keys via cascading dropdowns
* **Time range** selection with quick-range presets (1 h, 6 h, 24 h, 7 d, 30 d)
* **Visualise** queried field values in an interactive line chart (Chart.js)
* **Edit** individual data points directly in a scrollable table
* **Side-by-side chart** – original values (blue) and modified values (orange) shown simultaneously for review
* **Commit** writes the modified points back to InfluxDB (same measurement/tags/timestamp → overwrites the field value)
* **Persistent settings** – URL, organisation and optionally the API token are saved across sessions

---

## Quick start with Docker Compose

```bash
git clone https://github.com/signag/influx_editor.git
cd influx_editor
docker compose up --build
```

Then open **http://localhost:5000** in your browser.

Connection settings (URL, organisation, optionally token) are stored in a named Docker volume
so they survive container restarts.

---

## Running locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The app starts on **http://localhost:5000**.  
Settings are stored in `data/settings.json` (created automatically).

---

## Environment variables

| Variable       | Default                          | Description                          |
|----------------|----------------------------------|--------------------------------------|
| `SETTINGS_FILE`| `./data/settings.json`           | Path to the persisted settings file  |
| `PORT`         | `5000`                           | HTTP port the server listens on      |
| `LOG_LEVEL`    | `INFO`                           | Python logging level                 |
| `DEBUG`        | `false`                          | Set to `true` for Flask debug mode   |

---

## Architecture

```
Browser (W3.css + Chart.js)
        │  HTTP / JSON
        ▼
Flask backend (app.py)
        │  influxdb-client-python
        ▼
InfluxDB v2
```

The backend is a single-process, single-worker Flask/Gunicorn application.  
The InfluxDB connection is held as a module-level singleton, which is appropriate
for a single-user container deployment.

---

## Modifying data

InfluxDB v2 supports in-place field replacement: writing a new `Point` with the
same **measurement + tags + timestamp** simply overwrites the stored field value.  
The editor uses this mechanism – no data is deleted; only the changed field values
are re-written with the new values supplied by the user.
