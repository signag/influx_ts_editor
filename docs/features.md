# Influx Time Series Editor V1.0.x Features

[![Up](img/goup.gif)](./index.md)

## Feature Overview

* **Browse** buckets, measurements, tag key/value pairs and field keys via cascading dropdowns
* **Time range** selection with quick-range presets (1 h, 6 h, 12 h, 24 h, 7 d, 30 d)
* **Time Range shift** for shifting the region of interest on the time scale
* **Visualize** queried field values in an interactive line chart
* **Time Range selection** with **mouse** click-dragging within the chart
* **Auto Query** for immediate visualization update on time range change
* **Edit** individual data points directly in a scrollable table
* **Delete** individual data points by selecting action **DEL** in the Action column
* **Side-by-side chart** – original values (blue) and modified/filtered values (orange) shown simultaneously for review
* **Commit** writes the modified points back to InfluxDB 
<br>(same measurement/tags/timestamp → overwrites the field value) while preserving the queried field value type,
<br>and deletes points marked with **DEL** using the InfluxDB delete API
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
The editor uses this mechanism for value edits – only the changed field values
are re-written with the new values supplied by the user, retaining their original tag sets.

## Deleting data

Individual data points can be deleted using the InfluxDB v2 delete API.  
The editor sends a delete request with a 1-microsecond time window `[t, t+1μs)` and a
predicate that matches the exact **measurement** and **tag set** of the queried data,
ensuring only the selected point is removed.

> **Note:** The InfluxDB v2 OSS delete API does not support filtering by field name
> (`_field`). The delete therefore targets all fields stored for the given
> measurement, tag set, and timestamp.
>
> To avoid unintended mass deletions, the editor first counts points that match the
> exact deletion predicate and timestamp windows. If that count exceeds the number
> of selected rows, deletion is aborted and an error is shown.

---

## Credits

This tool was created with support of [GitHub Copilot](https://github.com/features/copilot)