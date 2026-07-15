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
