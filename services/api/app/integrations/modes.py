"""Which Google integrations are live and which are running in labelled demo mode.

An integration is **live** only when it is configured (env vars present) *and* a lightweight start-up probe
succeeded, so the UI badge never claims "live" for a key that is wrong, restricted or whose API is disabled.
Adding the relevant env var(s) is the only step needed to switch an integration on.

Probes run once in a background thread at start-up (`start_probes`) and again on
`GET /api/system/modes?refresh=true`. Until a probe has finished, a configured integration is treated as
usable (the adapters still fall back per call on any error).
"""
import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from app.config import settings

log = logging.getLogger(__name__)

_status: dict[str, dict] = {}
_lock = threading.Lock()
_probed = threading.Event()


def _live() -> bool:
    return not settings.force_demo_mode


# ------------------------------------------------------------------------------------------ configured?

def _gemini_configured() -> bool:
    if settings.google_genai_use_vertexai:
        return bool(settings.google_cloud_project)
    return bool(settings.gemini_api_key)


CONFIGURED: dict[str, Callable[[], bool]] = {
    "gemini": _gemini_configured,
    "speech": lambda: bool(settings.google_cloud_api_key),
    "routes": lambda: bool(settings.maps_api_key),
    "bigquery": lambda: bool(settings.google_cloud_project and settings.bigquery_dataset),
    "forecast": lambda: bool(settings.google_cloud_project and settings.bigquery_dataset)
    and settings.forecast_backend == "bigquery",
    "storage": lambda: bool(settings.gcs_bucket),
    "firestore": lambda: bool(settings.firebase_project_id),
}


def _usable(integration: str) -> bool:
    if not _live() or not CONFIGURED[integration]():
        return False
    st = _status.get(integration)
    return st is None or st["ok"]


def gemini_enabled() -> bool:
    return _usable("gemini")


def cloud_language_enabled() -> bool:
    return _usable("speech")


def routes_enabled() -> bool:
    return _usable("routes")


def bigquery_enabled() -> bool:
    return _usable("bigquery")


def forecast_bigquery_enabled() -> bool:
    return bigquery_enabled() and _usable("forecast")


def storage_enabled() -> bool:
    return _usable("storage")


def firestore_enabled() -> bool:
    return _usable("firestore")


# ------------------------------------------------------------------------------------------ probes

def _probe_gemini() -> str:
    from app.ai.gemini import client

    m = client().models.get(model=settings.gemini_model)
    backend = f"Vertex AI ({settings.gemini_location})" if settings.google_genai_use_vertexai else "Gemini API key"
    return f"{m.name or settings.gemini_model} via {backend}"


def _probe_speech() -> str:
    import httpx

    key = {"key": settings.google_cloud_api_key}
    tr = httpx.post("https://translation.googleapis.com/language/translate/v2", params=key, timeout=10,
                    json={"q": "ok", "target": "hi", "format": "text"})
    tr.raise_for_status()
    tts = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize", params=key, timeout=10,
                     json={"input": {"text": "ok"}, "voice": {"languageCode": "en-IN"},
                           "audioConfig": {"audioEncoding": "MP3"}})
    tts.raise_for_status()
    # An empty request is rejected with 400 when the key is authorised; 401/403 mean it is not.
    stt = httpx.post("https://speech.googleapis.com/v1/speech:recognize", params=key, timeout=10,
                     json={"config": {"languageCode": "en-IN"}, "audio": {"content": ""}})
    if stt.status_code in (401, 403):
        stt.raise_for_status()
    return "Translation, Text-to-Speech and Speech-to-Text reachable"


def _probe_routes() -> str:
    from app.integrations.routes import _routes_matrix

    m = _routes_matrix([(9.9252, 78.1198)], [(10.0333, 78.3333)])
    if m[0][0] is None:
        raise RuntimeError("Routes API returned no route")
    return f"Routes API computeRouteMatrix OK ({m[0][0]} min test route)"


def _probe_bigquery() -> str:
    from app.integrations.cloud_sinks import EVENT_TABLES, bq_client

    ds = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"
    missing = []
    for t in EVENT_TABLES:
        try:
            bq_client().get_table(f"{ds}.{t}")
        except Exception:  # noqa: BLE001
            missing.append(t)
    if missing:
        raise RuntimeError(f"dataset {ds} is missing tables {missing}; run data/transformations/load_bigquery.py "
                           "--create-tables")
    return f"dataset {ds}: event tables present"


def _probe_forecast() -> str:
    from app.integrations.cloud_sinks import _all_bigquery_forecasts

    series = _all_bigquery_forecasts(8)  # also warms the forecast cache
    if not series:
        raise RuntimeError("weekly_demand_arima returned no forecasts")
    return f"BigQuery ML weekly_demand_arima: {len(series)} series forecast"


def _probe_storage() -> str:
    from app.integrations.cloud_sinks import gcs_client

    list(gcs_client().list_blobs(settings.gcs_bucket, prefix=f"{settings.project_name}/", max_results=1))
    return f"gs://{settings.gcs_bucket}/{settings.project_name}/ readable"


def _probe_firestore() -> str:
    from app.integrations.cloud_sinks import firestore_client

    firestore_client().collection("notifications").document("_probe").get()
    return f"Firestore (default) database in {settings.firebase_project_id}"


PROBES: dict[str, Callable[[], str]] = {
    "gemini": _probe_gemini, "speech": _probe_speech, "routes": _probe_routes, "bigquery": _probe_bigquery,
    "forecast": _probe_forecast, "storage": _probe_storage, "firestore": _probe_firestore,
}


def _run_probe(integration: str) -> None:
    try:
        detail, ok = PROBES[integration](), True
    except Exception as exc:  # noqa: BLE001 - a failed probe means "use the fallback", never a crash
        detail, ok = f"configured but unavailable: {str(exc).splitlines()[0][:240]}", False
        log.warning("Integration %s unavailable, using demo fallback: %s", integration, detail)
    with _lock:
        _status[integration] = {"ok": ok, "detail": detail, "checked_at": datetime.now(UTC).isoformat()}


def run_probes() -> None:
    """Probe every configured integration (in parallel). Safe to call repeatedly."""
    todo = [i for i in PROBES if _live() and CONFIGURED[i]()]
    with _lock:
        for i in PROBES:
            if i not in todo:
                _status.pop(i, None)
    # forecast depends on bigquery's client; order does not matter because each probe is independent.
    with ThreadPoolExecutor(max_workers=len(PROBES)) as pool:
        list(pool.map(_run_probe, todo))
    _probed.set()


def start_probes() -> None:
    """Kick off probes in the background (called at app start-up)."""
    if not _live():
        _probed.set()
        return
    threading.Thread(target=run_probes, name="integration-probes", daemon=True).start()


# ------------------------------------------------------------------------------------------ report

ROWS = [
    ("gemini", "Gemini extraction, register photo reading and explanations",
     "GEMINI_API_KEY (or GOOGLE_GENAI_USE_VERTEXAI=true + GOOGLE_CLOUD_PROJECT)",
     "Rule-based local parser + labelled fixtures"),
    ("speech", "Speech-to-Text, Text-to-Speech, Translation", "GOOGLE_CLOUD_API_KEY",
     "Gemini audio transcription if Gemini is on, else demo transcript; browser speech synthesis; "
     "built-in UI translations"),
    ("routes", "Google Maps Routes API travel times", "MAPS_API_KEY",
     "Straight-line (haversine) distance x 1.35 road factor at 35 km/h"),
    ("bigquery", "BigQuery event sink (stock transactions, transfers, AI outputs)",
     "GOOGLE_CLOUD_PROJECT + BIGQUERY_DATASET (+ ADC credentials)", "In-memory store seeded from synthetic data"),
    ("forecast", "Demand forecast (BigQuery ML ARIMA_PLUS)", "FORECAST_BACKEND=bigquery + BigQuery",
     "Local seasonal exponential-smoothing baseline"),
    ("storage", "Cloud Storage for register photos and voice recordings", "GCS_BUCKET (+ ADC credentials)",
     "Media is processed in memory and not retained"),
    ("firestore", "Firebase / Firestore notifications", "FIREBASE_PROJECT_ID (+ ADC credentials)",
     "In-memory notifications"),
]


def all_modes(wait_seconds: float = 20.0) -> list[dict]:
    if _live():
        _probed.wait(timeout=wait_seconds)
    out = []
    for i, label, env, fb in ROWS:
        on = _usable(i)
        st = _status.get(i) or {}
        configured = _live() and CONFIGURED[i]()
        if on:
            detail = st.get("detail", "configured (probe pending)")
        elif settings.force_demo_mode:
            detail = "FORCE_DEMO_MODE=true"
        elif not configured:
            detail = "not configured"
        else:
            detail = st.get("detail", "unavailable")
        out.append({"id": i, "label": label, "mode": "real" if on else "demo", "configured": configured,
                    "verified": st.get("ok") if configured else None, "detail": detail,
                    "checked_at": st.get("checked_at"), "enable_with": env, "fallback": fb})
    return out


def any_demo() -> bool:
    return any(m["mode"] == "demo" for m in all_modes())
