"""Optimiser → Gemini explanation → proposed transfers awaiting District Health Officer approval."""
import uuid

from app.redistribution.explain import build_context, explain
from app.redistribution.optimizer import Params, optimize
from app.store import Store


def run_optimization(store: Store, state: str | None, district: str | None, drug_code: str | None,
                     params: Params, language: str = "en") -> dict:
    if state and params.allow_cross_district is False:
        params.allow_cross_district = bool(
            store.states.get(state, {}).get("config", {}).get("cross_district_transfers", False)) and not district
    rows = store.optimizer_rows(state, district, drug_code)
    result = optimize(rows, params)
    proposals = []
    surge_by_f: dict[str, set[str]] = {}
    for t in result["transfers"]:
        donor, recv = store.facility(t["from_facility_id"]), store.facility(t["to_facility_id"])
        med = store.medicines[t["drug_code"]]
        if recv["facility_id"] not in surge_by_f:
            surge_by_f[recv["facility_id"]] = store.surge_groups(store.stock_rows(recv["facility_id"]))
        ctx = build_context(
            t, donor, recv, med, med["group"] in surge_by_f[recv["facility_id"]],
            store.hours_since(store.status[donor["facility_id"]]["last_stock_report_at"]),
            store.hours_since(store.status[recv["facility_id"]]["last_stock_report_at"]),
        )
        explanation, prov = explain(ctx, language)
        now = store.now()
        proposals.append({
            "transfer_id": f"TRF-{uuid.uuid4().hex[:8]}", "state": recv["state"], "district": recv["district"],
            "from_facility_id": donor["facility_id"], "to_facility_id": recv["facility_id"],
            "from_name": donor["name"], "to_name": recv["name"],
            "from_location": {"lat": donor["lat"], "lng": donor["lng"]},
            "to_location": {"lat": recv["lat"], "lng": recv["lng"]},
            "drug_code": t["drug_code"], "medicine": f"{med['name']} {med['strength']}", "unit": med["unit"],
            "quantity": t["quantity"], "reason": explanation["summary"], "travel_minutes": t["travel_minutes"],
            "travel_mode": t["travel_mode"], "cross_district": t["cross_district"], "status": "proposed",
            "approved_by": None, "explanation": explanation, "optimiser": t, "context": ctx,
            "created_at": now, "model_name": prov["model_name"], "model_version": prov["model_version"],
            "prompt_version": prov["prompt_version"], "ai_mode": prov["mode"], "is_demo": prov["is_demo"],
            "requires_human_approval": True,
            "history": [{"status": "proposed", "at": now, "by": "optimiser", "note": result["solver"]}],
        })
    created = store.add_transfers(proposals, {"state": state, "district": district})
    return {"transfers": created, "summary": {k: v for k, v in result.items() if k != "transfers"}}
