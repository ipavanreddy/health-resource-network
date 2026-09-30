"""Shared forecast model registry + model card (PRD §19). Local registry in demo; Vertex AI in production."""
import numpy as np

from app.forecasting import baseline as fc
from app.integrations.cloud_sinks import arima_model_summary
from app.integrations.modes import forecast_bigquery_enabled
from app.store import Store


def _state_metrics(store: Store) -> list[dict]:
    bt = store.backtest
    out = []
    tracer = [store.midx[c] for c in store.med_codes if store.medicines[c]["is_tracer"]]
    for state, doc in store.states.items():
        rows = [store.fidx[f["facility_id"]] for f in store.dispensing(state)]
        if not rows:
            continue
        sel = np.ix_(rows, tracer)
        m = {k: fc.wape(v[sel], bt["actual"][sel]) for k, v in bt["abs_err"].items()}
        out.append({
            "state": state, "state_name": doc["config"]["name"], "facilities": len(rows),
            "series": len(rows) * len(tracer), "wape_model": m["model"],
            "wape_same_week_last_year": m["same_week_last_year"], "wape_moving_average_4w": m["moving_average_4w"],
            "improvement_vs_same_week_last_year": round(1 - m["model"] / m["same_week_last_year"], 3),
            "config_uses_model": doc["config"].get("forecast_model") == fc.MODEL_ID,
        })
    return out


def models(store: Store) -> list[dict]:
    return [
        {"id": fc.MODEL_ID, "version": fc.MODEL_VERSION, "type": "Seasonal exponential-smoothing baseline",
         "status": "active" if not forecast_bigquery_enabled() else "fallback",
         "registry": "local (demo); register in Vertex AI Model Registry for production",
         "shared_by_states": [s for s, d in store.states.items() if d["config"].get("forecast_model") == fc.MODEL_ID]},
        {"id": "weekly_demand_arima", "version": "bqml-arima-plus", "type": "BigQuery ML ARIMA_PLUS (per series)",
         "status": "active" if forecast_bigquery_enabled() else
         "trained in BigQuery ML (serve with FORECAST_BACKEND=bigquery)" if arima_model_summary() else
         "available (run data/transformations/load_bigquery.py --all)",
         "registry": "BigQuery ML (infrastructure/bigquery/forecast_model.sql)",
         "shared_by_states": ["TN", "UP", "OD"]},
    ]


def model_card(store: Store, model_id: str) -> dict | None:
    if model_id != fc.MODEL_ID:
        if model_id == "weekly_demand_arima":
            return {"id": model_id, "summary": "Per facility x medicine weekly ARIMA_PLUS model trained in BigQuery ML "
                    "on the canonical weekly demand table (stock-out weeks excluded, India holiday calendar); "
                    "see infrastructure/bigquery/forecast_model.sql.",
                    "status": models(store)[1]["status"], "training_summary": arima_model_summary(),
                    "note": "Challenger to the shared baseline: ARIMA_PLUS smooths over a surge that started days "
                            "ago, so the dashboard keeps the baseline (whose level term reacts within a week) as the "
                            "serving model and uses surge detection for the gap."}
        return None
    per_state = _state_metrics(store)
    return {
        "id": fc.MODEL_ID, "version": fc.MODEL_VERSION, "name": "PHC weekly demand forecast (shared base model)",
        "type": "Seasonal exponential-smoothing baseline (transparent, no learned weights)",
        "method": fc.__doc__.strip(),
        "features": ["canonical weekly demand per facility x medicine (from any state adapter)",
                     "stock-out day counts (censoring flag)", "week of year (via seasonal ratio)"],
        "horizon_weeks": 8, "output": "weekly demand low / expected / high (80% range)",
        "training_data_scope": {
            "dataset": store.meta["dataset_version"], "is_synthetic": True,
            "history": f"{store.meta['history_start']} to {store.meta['history_end']}",
            "states": list(store.states), "facility_level_data_leaves_state": False,
        },
        "evaluation": {"metric": "WAPE, 1-week ahead, last 26 weeks, tracer medicines (lower is better)",
                       "per_state": per_state},
        "shared_use": "Every state configuration consumes the same canonical features, so the same model runs for "
                      "all states; each state publishes its own accuracy back (above). Only models and aggregate "
                      "metrics are shared, never facility-level data.",
        "limitations": [
            "Evaluated on SYNTHETIC data only; real accuracy must be measured on state data.",
            "Does not yet use weather, surveillance or holiday features.",
            "Sudden outbreaks are picked up with ~1 week lag via the level term; surge detection covers the gap.",
            "Stock-out weeks are excluded, but long stock-outs reduce the data available for a series.",
        ],
        "intended_use": "Decision support for stock planning; every transfer still needs human approval.",
        "registry": "local (demo). Production: Vertex AI Model Registry with this card as model metadata.",
    }
