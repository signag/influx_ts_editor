"""
InfluxDB Editor – Flask backend
Provides REST API for browsing and modifying InfluxDB v2 time series data.
"""

import json
import logging
import os

from flask import Flask, jsonify, render_template, request, g
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from version import version
from version_doc import docversion

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

SETTINGS_FILE = os.environ.get(
    "SETTINGS_FILE",
    os.path.join(os.path.dirname(__file__), "data", "settings.json"),
)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "ERROR")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.ERROR),
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection manager (module-level singleton – single-user app)
# ---------------------------------------------------------------------------

class _ConnectionManager:
    def __init__(self):
        self.client: InfluxDBClient | None = None
        self.org: str | None = None
        self.url: str | None = None
        self.status: str = "disconnected"
        self.error: str | None = None

    # ------------------------------------------------------------------
    def connect_old(self, url: str, token: str, org: str) -> tuple[bool, str]:
        try:
            if self.client:
                self.client.close()
            client = InfluxDBClient(url=url, token=token, org=org, timeout=10_000)
            health = client.health()
            if health.status == "pass":
                self.client = client
                self.org = org
                self.url = url
                self.status = "connected"
                self.error = None
                return True, "Connected successfully"
            client.close()
            msg = f"Health check failed: {health.message}"
            self.status = "error"
            self.error = msg
            return False, msg
        except Exception:  # noqa: BLE001
            logger.exception("connect failed")
            self.status = "error"
            # Static message – full details are in server logs
            self.error = "Connection failed. Verify URL, organization and API token."
            return False, self.error
        
    def connect(self, url: str, token: str, org: str) -> tuple[bool, str]:
        try:
            if self.client:
                self.client.close()
            client = InfluxDBClient(url=url, token=token, org=org, timeout=10_000)
            health = client.health()
            if health.status != "pass":
                client.close()
                msg = f"Health check failed: {health.message}"
                self.status = "error"
                self.error = msg
                return False, msg

            # Health check alone doesn't validate org/token — probe with a real query
            try:
                client.query_api().query("buckets()", org=org)
            except Exception:
                client.close()
                msg = f'Organization "{org}" not found or token lacks access'
                self.status = "error"
                self.error = msg
                return False, msg

            self.client = client
            self.org = org
            self.url = url
            self.status = "connected"
            self.error = None
            return True, "Connected successfully"
        except Exception:
            logger.exception("connect failed")
            self.status = "error"
            self.error = "Connection failed. Verify URL, organization and API token."
            return False, self.error        

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
        self.status = "disconnected"
        self.org = None
        self.url = None
        self.error = None

    def is_connected(self) -> bool:
        return self.client is not None and self.status == "connected"

    def query_api(self):
        if not self.is_connected():
            raise RuntimeError("Not connected to InfluxDB")
        return self.client.query_api()

    def write_api(self):
        if not self.is_connected():
            raise RuntimeError("Not connected to InfluxDB")
        return self.client.write_api(write_options=SYNCHRONOUS)


conn = _ConnectionManager()


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

def _load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:  # noqa: BLE001
            logger.warning("Could not read settings file")
    return {}


def _save_settings(settings: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(SETTINGS_FILE)), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2)
        return True
    except Exception:  # noqa: BLE001
        logger.error("Could not save settings")
        return False


# ---------------------------------------------------------------------------
# Routes – UI
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    g.version = version
    g.docversion = docversion
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Routes – Settings
# ---------------------------------------------------------------------------

@app.route("/api/settings", methods=["GET"])
def get_settings():
    settings = _load_settings()
    if not settings.get("save_token", False):
        settings.pop("token", None)
    return jsonify(settings)


@app.route("/api/settings", methods=["POST"])
def post_settings():
    data = request.get_json(force=True) or {}
    settings = _load_settings()
    settings["url"] = data.get("url", "")
    settings["org"] = data.get("org", "")
    settings["save_token"] = bool(data.get("save_token", False))
    if settings["save_token"]:
        settings["token"] = data.get("token", "")
    else:
        settings.pop("token", None)
    if _save_settings(settings):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Failed to save settings"}), 500


# ---------------------------------------------------------------------------
# Routes – Connection
# ---------------------------------------------------------------------------

@app.route("/api/connect", methods=["POST"])
def api_connect():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    token = (data.get("token") or "").strip()
    org = (data.get("org") or "").strip()

    if not url or not token or not org:
        return jsonify({"success": False, "error": "URL, token and organization are required"}), 400

    ok, msg = conn.connect(url, token, org)
    if ok:
        return jsonify({"success": True, "message": "Connected successfully", "url": url, "org": org})
    return jsonify({"success": False, "error": conn.error or "Connection failed"}), 400


@app.route("/api/disconnect", methods=["POST"])
def api_disconnect():
    conn.disconnect()
    return jsonify({"success": True})


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(
        {
            "connected": conn.is_connected(),
            "url": conn.url,
            "org": conn.org,
            "status": conn.status,
            "error": conn.error,
        }
    )


# ---------------------------------------------------------------------------
# Routes – Schema discovery
# ---------------------------------------------------------------------------

def _require_connection():
    if not conn.is_connected():
        return jsonify({"error": "Not connected to InfluxDB"}), 400
    return None


@app.route("/api/buckets", methods=["GET"])
def api_buckets():
    err = _require_connection()
    if err:
        return err
    try:
        tables = conn.query_api().query("buckets()", org=conn.org)
        buckets = sorted(
            {row.values.get("name") for table in tables for row in table.records}
        )
        return jsonify({"buckets": buckets})
    except Exception:  # noqa: BLE001
        logger.exception("buckets query failed")
        return jsonify({"error": "Failed to retrieve buckets. See server logs for details."}), 500


@app.route("/api/measurements", methods=["GET"])
def api_measurements():
    err = _require_connection()
    if err:
        return err
    bucket = request.args.get("bucket", "").strip()
    if not bucket:
        return jsonify({"error": "bucket parameter required"}), 400
    try:
        q = f'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "{bucket}")'
        tables = conn.query_api().query(q, org=conn.org)
        measurements = sorted(
            {row.values.get("_value") for table in tables for row in table.records}
        )
        return jsonify({"measurements": measurements})
    except Exception:  # noqa: BLE001
        logger.exception("measurements query failed")
        return jsonify({"error": "Failed to retrieve measurements. See server logs for details."}), 500


@app.route("/api/tag-keys", methods=["GET"])
def api_tag_keys():
    err = _require_connection()
    if err:
        return err
    bucket = request.args.get("bucket", "").strip()
    measurement = request.args.get("measurement", "").strip()
    if not bucket or not measurement:
        return jsonify({"error": "bucket and measurement parameters required"}), 400
    try:
        q = (
            'import "influxdata/influxdb/schema"\n'
            f'schema.measurementTagKeys(bucket: "{bucket}", measurement: "{measurement}")'
        )
        tables = conn.query_api().query(q, org=conn.org)
        tag_keys = sorted(
            {
                row.values.get("_value")
                for table in tables
                for row in table.records
                if not (row.values.get("_value") or "").startswith("_")
            }
        )
        return jsonify({"tag_keys": tag_keys})
    except Exception:  # noqa: BLE001
        logger.exception("tag-keys query failed")
        return jsonify({"error": "Failed to retrieve tag keys. See server logs for details."}), 500


@app.route("/api/tag-values", methods=["GET"])
def api_tag_values():
    err = _require_connection()
    if err:
        return err
    bucket = request.args.get("bucket", "").strip()
    measurement = request.args.get("measurement", "").strip()
    tag_key = request.args.get("tag_key", "").strip()
    if not bucket or not measurement or not tag_key:
        return jsonify({"error": "bucket, measurement and tag_key parameters required"}), 400
    try:
        q = (
            'import "influxdata/influxdb/schema"\n'
            f'schema.measurementTagValues(bucket: "{bucket}", measurement: "{measurement}", tag: "{tag_key}")'
        )
        tables = conn.query_api().query(q, org=conn.org)
        tag_values = sorted(
            {row.values.get("_value") for table in tables for row in table.records}
        )
        return jsonify({"tag_values": tag_values})
    except Exception:  # noqa: BLE001
        logger.exception("tag-values query failed")
        return jsonify({"error": "Failed to retrieve tag values. See server logs for details."}), 500


@app.route("/api/field-keys", methods=["GET"])
def api_field_keys():
    err = _require_connection()
    if err:
        return err
    bucket = request.args.get("bucket", "").strip()
    measurement = request.args.get("measurement", "").strip()
    if not bucket or not measurement:
        return jsonify({"error": "bucket and measurement parameters required"}), 400
    try:
        q = (
            'import "influxdata/influxdb/schema"\n'
            f'schema.measurementFieldKeys(bucket: "{bucket}", measurement: "{measurement}")'
        )
        tables = conn.query_api().query(q, org=conn.org)
        field_keys = sorted(
            {row.values.get("_value") for table in tables for row in table.records}
        )
        return jsonify({"field_keys": field_keys})
    except Exception:  # noqa: BLE001
        logger.exception("field-keys query failed")
        return jsonify({"error": "Failed to retrieve field keys. See server logs for details."}), 500


# ---------------------------------------------------------------------------
# Routes – Data query & update
# ---------------------------------------------------------------------------

@app.route("/api/query", methods=["POST"])
def api_query():
    err = _require_connection()
    if err:
        return err
    data = request.get_json(force=True) or {}
    bucket = (data.get("bucket") or "").strip()
    measurement = (data.get("measurement") or "").strip()
    tags = data.get("tags") or []
    field = (data.get("field") or "").strip()
    start = (data.get("start") or "").strip()
    stop = (data.get("stop") or "").strip()

    if not all([bucket, measurement, field, start, stop]):
        return jsonify({"error": "bucket, measurement, field, start and stop are required"}), 400

    try:
        tag_filters = "".join(
            f'\n  |> filter(fn: (r) => r["{t["key"]}"] == "{t["value"]}")'
            for t in tags
            if (t.get("key") or "").strip() and (t.get("value") or "").strip()
        )
        query = (
            f'from(bucket: "{bucket}")\n'
            f'  |> range(start: {start}, stop: {stop})\n'
            f'  |> filter(fn: (r) => r._measurement == "{measurement}")\n'
            f'  |> filter(fn: (r) => r._field == "{field}")'
            f'{tag_filters}\n'
            f'  |> sort(columns: ["_time"])'
        )
        tables = conn.query_api().query(query, org=conn.org)
        records = [
            {
                "timestamp": row.get_time().isoformat(),
                "value": row.get_value(),
            }
            for table in tables
            for row in table.records
        ]
        return jsonify({"records": records, "count": len(records)})
    except Exception:  # noqa: BLE001
        logger.exception("query failed")
        return jsonify({"error": "Data query failed. See server logs for details."}), 500


@app.route("/api/update", methods=["POST"])
def api_update():
    err = _require_connection()
    if err:
        return err
    data = request.get_json(force=True) or {}
    bucket = (data.get("bucket") or "").strip()
    measurement = (data.get("measurement") or "").strip()
    tags = data.get("tags") or []
    field = (data.get("field") or "").strip()
    updates = data.get("updates") or []   # [{timestamp, new_value}]

    if not all([bucket, measurement, field]) or not updates:
        return jsonify({"error": "bucket, measurement, field and updates are required"}), 400

    try:
        points = []
        for upd in updates:
            ts = upd.get("timestamp")
            new_val = upd.get("new_value")
            if ts is None or new_val is None:
                continue
            pt = Point(measurement)
            for tag in tags:
                k = (tag.get("key") or "").strip()
                v = (tag.get("value") or "").strip()
                if k and v:
                    pt = pt.tag(k, v)
            # Preserve integer type when the value has no fractional part
            if isinstance(new_val, float) and new_val == int(new_val):
                new_val = int(new_val)
            pt = pt.field(field, new_val)
            pt = pt.time(ts)
            points.append(pt)

        conn.write_api().write(bucket=bucket, org=conn.org, record=points)
        return jsonify({"success": True, "updated": len(points)})
    except Exception:  # noqa: BLE001
        logger.exception("update failed")
        return jsonify({"error": "Update failed. See server logs for details."}), 500


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
