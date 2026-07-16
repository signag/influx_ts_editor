# Influx Time Series Editor V1.0.x Features

[![Up](img/goup.gif)](./index.md)

## Feature Overview

* **Browse** buckets, measurements, tag key/value pairs and field keys via cascading dropdowns
* **Time range** selection with quick-range presets (1 h, 6 h, 12 h, 24 h, 7 d, 30 d)
* **Time Range shift** for shifting the region of interest on the time scale
* **Visualize** queried field values in an interactive line chart
* **Auto Query** for immediate visualization update on time range change
* **Edit** individual data points directly in a scrollable table
* **Side-by-side chart** – original values (blue) and modified values (orange) shown simultaneously for review
* **Commit** writes the modified points back to InfluxDB (same measurement/tags/timestamp → overwrites the field value)
* **Persistent settings** – URL, organisation and optionally the API token are saved across sessions

---

## Architecture

The application is a Flask backend + W3.css/Chart.js frontend, packaged as a Docker container.


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
are re-written with the new values supplied by the user, retaining their original tag sets.

---

## Credits

The initial version for this tool was created with [GitHub Copilot](https://github.com/features/copilot)