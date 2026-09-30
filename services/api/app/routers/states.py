"""States (canonical schema + adapters), analytics, shared models, system modes and demo controls."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.forecasting.model_card import model_card, models
from app.integrations.modes import all_modes, any_demo
from app.interop.adapters import AdapterError, adapter_summary, to_canonical
from app.interop.canonical import CanonicalFacilityRecord
from app.routers.deps import store
from app.store import Store, load_generator, reset_store

router = APIRouter(prefix="/api", tags=["states"])


def _state(s: Store, state_id: str) -> dict:
    doc = s.states.get(state_id.upper())
    if not doc:
        raise HTTPException(404, f"Unknown state {state_id}")
    return doc


def _state_view(s: Store, state_id: str) -> dict:
    doc = _state(s, state_id)
    districts = sorted({(f["district"], f["district_name"]) for f in s.dispensing(state_id)})
    return {"id": doc["state"], **doc["config"], "adapter": adapter_summary(doc["state"]),
            "districts": [{"id": d, "name": n} for d, n in districts],
            "scenarios": [sc for sc in s.scenarios if sc["state"] == doc["state"]]}


@router.get("/states")
def states(s: Store = Depends(store)) -> dict:
    return {"states": [_state_view(s, sid) for sid in s.states]}


@router.get("/states/{state_id}")
def state(state_id: str, s: Store = Depends(store)) -> dict:
    return _state_view(s, state_id)


@router.get("/states/{state_id}/analytics")
def analytics(state_id: str, s: Store = Depends(store)) -> dict:
    view = _state_view(s, state_id)
    return {"state": view["id"], "name": view["name"], "overall": s.overview(view["id"]),
            "districts": [{"id": d["id"], "name": d["name"], **s.overview(view["id"], d["id"])}
                          for d in view["districts"]]}


@router.get("/states/{state_id}/sample-export")
def sample_export(state_id: str, limit: int = 3, s: Store = Depends(store)) -> dict:
    """Side-by-side: state-native records and their canonical form (for the interoperability demo)."""
    doc = _state(s, state_id)
    gen = load_generator()
    hero = next((sc["hero_facility_id"] for sc in s.scenarios if sc["state"] == doc["state"]), None)
    f = s.facility(hero)
    rows = []
    for code in s.med_codes[:limit]:
        snap = s.stock[(hero, code)]
        native = gen._native_record(doc["state"], f, s.medicines[code], snap, None)
        rows.append({"native": native, "canonical": to_canonical(doc["state"], native, {f["hfr_id"]: hero})})
    return {"state": doc["state"], "adapter": adapter_summary(doc["state"]), "records": rows}


class IngestIn(BaseModel):
    records: list[dict]
    dry_run: bool = False


@router.post("/states/{state_id}/ingest")
def ingest(state_id: str, body: IngestIn, s: Store = Depends(store)) -> dict:
    doc = _state(s, state_id)
    hfr_index = {f["hfr_id"]: fid for fid, f in s.facilities.items() if f["state"] == doc["state"]}
    ok, errors = [], []
    for n, rec in enumerate(body.records):
        try:
            ok.append(to_canonical(doc["state"], rec, hfr_index))
        except AdapterError as exc:
            errors.append({"index": n, "error": str(exc)})
    if not body.dry_run:
        with s.lock:
            for c in ok:
                s.stock[(c["facility_id"], c["drug_code"])].update(
                    on_hand=c["on_hand"], in_transit=c["in_transit"], near_expiry_qty=c["near_expiry_qty"],
                    updated_at=c["updated_at"], source=c["source"])
    return {"accepted": len(ok), "rejected": len(errors), "canonical": ok, "errors": errors,
            "applied": not body.dry_run}


@router.get("/schema/canonical")
def canonical_schema() -> dict:
    return CanonicalFacilityRecord.model_json_schema()


@router.get("/models")
def list_models(s: Store = Depends(store)) -> dict:
    return {"models": models(s)}


@router.get("/models/{model_id}/card")
def card(model_id: str, s: Store = Depends(store)) -> dict:
    c = model_card(s, model_id)
    if not c:
        raise HTTPException(404, "Unknown model")
    return c


@router.get("/system/modes")
def modes(s: Store = Depends(store)) -> dict:
    return {"integrations": all_modes(), "demo_mode": any_demo(), "synthetic_data": True,
            "data_label": s.data_label(), "notice": s.meta["notice"]}


@router.get("/demo/scenarios")
def scenarios(s: Store = Depends(store)) -> dict:
    return {"scenarios": s.scenarios, "events": s.events, "data_label": s.data_label()}


class ResetIn(BaseModel):
    reference_time: datetime | None = None


@router.post("/demo/reset")
def reset(body: ResetIn | None = None) -> dict:
    s = reset_store(body.reference_time if body else None)
    return {"reset": True, "reference_time": s.reference_time}
