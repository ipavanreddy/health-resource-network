"""Which Google integrations are live and which are running in labelled demo mode.

Adding the relevant env var(s) is the only step needed to switch an integration to real mode.
"""
from app.config import settings


def _live() -> bool:
    return not settings.force_demo_mode


def gemini_enabled() -> bool:
    if not _live():
        return False
    if settings.google_genai_use_vertexai:
        return bool(settings.google_cloud_project)
    return bool(settings.gemini_api_key)


def cloud_language_enabled() -> bool:
    return _live() and bool(settings.google_cloud_api_key)


def routes_enabled() -> bool:
    return _live() and bool(settings.maps_api_key)


def bigquery_enabled() -> bool:
    return _live() and bool(settings.google_cloud_project and settings.bigquery_dataset)


def firestore_enabled() -> bool:
    return _live() and bool(settings.firebase_project_id)


def forecast_bigquery_enabled() -> bool:
    return bigquery_enabled() and settings.forecast_backend == "bigquery"


def all_modes() -> list[dict]:
    rows = [
        ("gemini", "Gemini extraction, register photo reading and explanations", gemini_enabled(),
         "GEMINI_API_KEY (or GOOGLE_GENAI_USE_VERTEXAI=true + GOOGLE_CLOUD_PROJECT)",
         "Rule-based local parser + labelled fixtures"),
        ("speech", "Speech-to-Text, Text-to-Speech, Translation", cloud_language_enabled(),
         "GOOGLE_CLOUD_API_KEY", "Gemini audio transcription if Gemini is on, else demo transcript; "
         "browser speech synthesis; built-in UI translations"),
        ("routes", "Google Maps Routes API travel times", routes_enabled(), "MAPS_API_KEY",
         "Straight-line (haversine) distance x 1.35 road factor at 35 km/h"),
        ("bigquery", "BigQuery event sink (stock transactions, transfers, AI outputs)", bigquery_enabled(),
         "GOOGLE_CLOUD_PROJECT + BIGQUERY_DATASET (+ ADC credentials)", "In-memory store seeded from synthetic data"),
        ("forecast", "Demand forecast (BigQuery ML ARIMA_PLUS)", forecast_bigquery_enabled(),
         "FORECAST_BACKEND=bigquery + BigQuery", "Local seasonal exponential-smoothing baseline"),
        ("firestore", "Firebase / Firestore notifications", firestore_enabled(),
         "FIREBASE_PROJECT_ID (+ ADC credentials)", "In-memory notifications"),
    ]
    return [
        {"id": i, "label": label, "mode": "real" if on else "demo", "enable_with": env, "fallback": fb}
        for i, label, on, env, fb in rows
    ]


def any_demo() -> bool:
    return any(m["mode"] == "demo" for m in all_modes())
