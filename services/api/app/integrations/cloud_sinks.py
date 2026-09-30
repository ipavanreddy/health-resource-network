"""Best-effort writes to BigQuery (events) and Firestore (notifications).

In demo mode these are no-ops: the in-memory store is the system of record. In real mode a failure is
logged and never breaks the user journey.
"""
import json
import logging
from functools import lru_cache

from app.config import settings
from app.integrations.modes import bigquery_enabled, firestore_enabled

log = logging.getLogger(__name__)


@lru_cache
def _bq_client():
    from google.cloud import bigquery

    return bigquery.Client(project=settings.google_cloud_project)


@lru_cache
def _firestore_client():
    import firebase_admin
    from firebase_admin import firestore

    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
    return firestore.client()


def _jsonable(row: dict) -> dict:
    return json.loads(json.dumps(row, default=str))


def record_event(table: str, row: dict) -> bool:
    """Insert one row into `{project}.{dataset}.{table}`. Returns True if written to BigQuery."""
    if not bigquery_enabled():
        return False
    try:
        table_id = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.{table}"
        errors = _bq_client().insert_rows_json(table_id, [_jsonable(row)])
        if errors:
            log.warning("BigQuery insert errors for %s: %s", table, errors)
            return False
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("BigQuery sink unavailable: %s", exc)
        return False


def push_notification(notification: dict) -> bool:
    """Write a notification to Firestore `notifications/{id}` so facility apps can subscribe."""
    if not firestore_enabled():
        return False
    try:
        _firestore_client().collection("notifications").document(notification["notification_id"]).set(
            _jsonable(notification))
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Firestore unavailable: %s", exc)
        return False


def bigquery_forecast(facility_id: str, drug_code: str, horizon_weeks: int) -> list[dict] | None:
    """Real forecast path: BigQuery ML ARIMA_PLUS model trained by infrastructure/bigquery/forecast_model.sql."""
    try:
        from google.cloud import bigquery

        ds = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"
        sql = (
            f"SELECT forecast_timestamp, forecast_value, prediction_interval_lower_bound AS lo, "
            f"prediction_interval_upper_bound AS hi FROM ML.FORECAST(MODEL `{ds}.weekly_demand_arima`, "
            f"STRUCT(@h AS horizon, 0.8 AS confidence_level)) WHERE series_id = @sid ORDER BY forecast_timestamp"
        )
        job = _bq_client().query(sql, job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("h", "INT64", horizon_weeks),
            bigquery.ScalarQueryParameter("sid", "STRING", f"{facility_id}|{drug_code}"),
        ]))
        rows = list(job.result())
        if not rows:
            return None
        return [{"week_start": r["forecast_timestamp"].date().isoformat(),
                 "demand_expected": float(r["forecast_value"]),
                 "demand_low": max(0.0, float(r["lo"])), "demand_high": float(r["hi"])} for r in rows]
    except Exception as exc:  # noqa: BLE001
        log.warning("BigQuery ML forecast unavailable, using baseline: %s", exc)
        return None
