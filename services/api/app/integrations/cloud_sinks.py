"""Best-effort writes to BigQuery (events), Cloud Storage (capture media) and Firestore (notifications).

In demo mode these are no-ops: the in-memory store is the system of record. In real mode a failure is
logged and never breaks the user journey. BigQuery inserts run on a background thread so they add no
latency to API requests.
"""
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import lru_cache

from app.config import settings
from app.integrations.modes import bigquery_enabled, firestore_enabled, storage_enabled

log = logging.getLogger(__name__)

# Event tables written by the API (created by infrastructure/bigquery/schema.sql). Columns not in a table are
# dropped (ignore_unknown_values); JSON columns are sent as serialised strings.
EVENT_TABLES = ("stock_transactions", "transfers", "ai_outputs")
JSON_COLUMNS = {"transfers": {"explanation", "optimiser", "history"}, "ai_outputs": {"items"}}

_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bq-sink")
_stats = {"written": 0, "failed": 0, "last_error": None}
_stats_lock = threading.Lock()


@lru_cache
def bq_client():
    from google.cloud import bigquery

    return bigquery.Client(project=settings.google_cloud_project)


@lru_cache
def gcs_client():
    from google.cloud import storage

    return storage.Client(project=settings.google_cloud_project or None)


@lru_cache
def firestore_client():
    import firebase_admin
    from firebase_admin import firestore

    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
    return firestore.client()


def _jsonable(row: dict) -> dict:
    return json.loads(json.dumps(row, default=str))


def _bq_row(table: str, row: dict) -> dict:
    out = _jsonable(row)
    for col in JSON_COLUMNS.get(table, ()):
        if col in out and out[col] is not None:
            out[col] = json.dumps(out[col], ensure_ascii=False)
    return out


def _insert(table: str, row: dict) -> bool:
    try:
        table_id = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.{table}"
        errors = bq_client().insert_rows_json(table_id, [row], ignore_unknown_values=True)
        ok = not errors
        if errors:
            log.warning("BigQuery insert errors for %s: %s", table, errors)
    except Exception as exc:  # noqa: BLE001
        log.warning("BigQuery sink unavailable: %s", exc)
        errors, ok = str(exc), False
    with _stats_lock:
        _stats["written" if ok else "failed"] += 1
        if not ok:
            _stats["last_error"] = str(errors)[:300]
    return ok


def record_event(table: str, row: dict) -> bool:
    """Queue one row for `{project}.{dataset}.{table}`. Returns True if queued for BigQuery."""
    if not bigquery_enabled():
        return False
    _pool.submit(_insert, table, _bq_row(table, row))
    return True


def sink_stats() -> dict:
    with _stats_lock:
        return dict(_stats)


MEDIA_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/heic": "heic",
             "audio/webm": "webm", "audio/ogg": "ogg", "audio/mpeg": "mp3", "audio/mp4": "m4a", "audio/wav": "wav"}


def store_media(kind: str, facility_id: str, capture_id: str, data: bytes | None, mime_type: str) -> dict | None:
    """Keep the original register photo / voice recording in Cloud Storage (PRD §28, §52).

    Objects live under `{project}/captures/{kind}/{date}/` so a bucket lifecycle rule on that prefix can enforce
    retention. Returns `{uri, bytes, content_type}` or None in demo mode / on failure.
    """
    if not data or not storage_enabled():
        return None
    mime = (mime_type or "application/octet-stream").split(";")[0].strip()
    name = (f"{settings.project_name}/captures/{kind}/{datetime.now(UTC):%Y-%m-%d}/"
            f"{facility_id}_{capture_id}.{MEDIA_EXT.get(mime, 'bin')}")
    try:
        t0 = time.perf_counter()
        blob = gcs_client().bucket(settings.gcs_bucket).blob(name)
        blob.metadata = {"facility_id": facility_id, "capture_id": capture_id, "kind": kind}
        blob.upload_from_string(data, content_type=mime)
        log.info("Stored %s (%d bytes) in %.0f ms", name, len(data), (time.perf_counter() - t0) * 1000)
        return {"uri": f"gs://{settings.gcs_bucket}/{name}", "bytes": len(data), "content_type": mime}
    except Exception as exc:  # noqa: BLE001
        log.warning("Cloud Storage unavailable: %s", exc)
        return None


def push_notification(notification: dict) -> bool:
    """Write a notification to Firestore `notifications/{id}` so facility apps can subscribe."""
    if not firestore_enabled():
        return False
    try:
        firestore_client().collection("notifications").document(notification["notification_id"]).set(
            _jsonable(notification))
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Firestore unavailable: %s", exc)
        return False


_forecast_cache: dict = {"at": 0.0, "rows": None}
_forecast_lock = threading.Lock()
FORECAST_TTL_S = 6 * 3600


def _all_bigquery_forecasts(horizon_weeks: int) -> dict[str, list[dict]]:
    """One ML.FORECAST query for every series, cached (a per-request query would add seconds of latency)."""
    with _forecast_lock:
        if _forecast_cache["rows"] is not None and time.time() - _forecast_cache["at"] < FORECAST_TTL_S:
            return _forecast_cache["rows"]
        ds = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"
        sql = (
            f"SELECT series_id, forecast_timestamp, forecast_value, prediction_interval_lower_bound AS lo, "
            f"prediction_interval_upper_bound AS hi FROM ML.FORECAST(MODEL `{ds}.weekly_demand_arima`, "
            f"STRUCT({int(horizon_weeks)} AS horizon, 0.8 AS confidence_level)) "
            f"ORDER BY series_id, forecast_timestamp"  # ML.FORECAST needs literal settings (no query parameters)
        )
        job = bq_client().query(sql)
        rows: dict[str, list[dict]] = {}
        for r in job.result():
            rows.setdefault(r["series_id"], []).append({
                "week_start": r["forecast_timestamp"].date().isoformat(),
                "demand_expected": round(max(0.0, float(r["forecast_value"])), 1),
                "demand_low": round(max(0.0, float(r["lo"])), 1), "demand_high": round(max(0.0, float(r["hi"])), 1)})
        _forecast_cache.update(at=time.time(), rows=rows)
        log.info("Loaded %d BigQuery ML forecast series", len(rows))
        return rows


def bigquery_forecast(facility_id: str, drug_code: str, horizon_weeks: int) -> list[dict] | None:
    """Real forecast path: BigQuery ML ARIMA_PLUS model trained by infrastructure/bigquery/forecast_model.sql."""
    try:
        return _all_bigquery_forecasts(horizon_weeks).get(f"{facility_id}|{drug_code}")
    except Exception as exc:  # noqa: BLE001
        log.warning("BigQuery ML forecast unavailable, using baseline: %s", exc)
        return None


@lru_cache
def arima_model_summary() -> dict | None:
    """Training summary of the shared BigQuery ML model (for its model card). None if unavailable."""
    if not bigquery_enabled():
        return None
    try:
        ds = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"
        model = bq_client().get_model(f"{ds}.weekly_demand_arima")
        sql = (f"SELECT COUNT(*) AS series, ROUND(APPROX_QUANTILES(AIC, 2)[OFFSET(1)], 1) AS median_aic, "
               f"COUNTIF(has_holiday_effect) AS with_holiday_effect, COUNTIF(has_spikes_and_dips) AS with_spikes, "
               f"COUNTIF(seasonal_periods[SAFE_OFFSET(0)] != 'NO_SEASONALITY') AS seasonal "
               f"FROM ML.ARIMA_EVALUATE(MODEL `{ds}.weekly_demand_arima`)")
        row = next(iter(bq_client().query(sql).result()))
        trained = model.created.isoformat() if model.created else None
        return {"model": f"{ds}.weekly_demand_arima", "trained_at": trained,
                "series": row["series"], "median_aic": row["median_aic"],
                "series_with_holiday_effect_IN": row["with_holiday_effect"],
                "series_with_spikes_and_dips": row["with_spikes"], "series_with_seasonality": row["seasonal"]}
    except Exception as exc:  # noqa: BLE001
        log.warning("BigQuery ML model summary unavailable: %s", exc)
        return None
