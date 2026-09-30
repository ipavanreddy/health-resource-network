"""Facilities, visibility, forecast, alerts and district overview (PRD §37)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.routers.deps import require_dho, store
from app.store import Store

router = APIRouter(prefix="/api", tags=["facilities"])


@router.get("/facilities")
def list_facilities(state: str | None = None, district: str | None = None, include_warehouses: bool = True,
                    s: Store = Depends(store)) -> dict:
    facs = [f for f in s.facilities.values() if (not state or f["state"] == state)
            and (not district or f["district"] == district) and (include_warehouses or f["type"] != "DWH")]
    return {"facilities": [s.summary(f["facility_id"]) for f in facs], "data_label": s.data_label()}


@router.get("/facilities/{facility_id}")
def get_facility(facility_id: str, s: Store = Depends(store)) -> dict:
    f = s.facility(facility_id)
    out = {**s.summary(facility_id), "warehouse": s.summary(f["warehouse_id"]) if f.get("warehouse_id") else None}
    if f["type"] != "DWH":
        st = s.status[facility_id]
        out |= {"freshness": s.freshness(facility_id), "opd_today": st["opd_today"],
                "state_config": s.states.get(f["state"], {}).get("config")}
    return out


@router.get("/facilities/{facility_id}/stock")
def facility_stock(facility_id: str, s: Store = Depends(store)) -> dict:
    return {"facility_id": facility_id, "stock": s.stock_rows(facility_id), "freshness": s.freshness(facility_id),
            "data_label": s.data_label()}


@router.get("/facilities/{facility_id}/readiness")
def facility_readiness(facility_id: str, s: Store = Depends(store)) -> dict:
    return {"facility_id": facility_id, **s.readiness(facility_id)}


@router.get("/facilities/{facility_id}/forecast")
def facility_forecast(facility_id: str, drug_code: str | None = None, s: Store = Depends(store)) -> dict:
    return s.forecast(facility_id, drug_code)


@router.get("/facilities/{facility_id}/canonical")
def facility_canonical(facility_id: str, s: Store = Depends(store)) -> dict:
    return s.canonical(facility_id)


class BedsIn(BaseModel):
    occupied: int = Field(ge=0)
    total: int | None = Field(default=None, ge=0)


@router.post("/facilities/{facility_id}/beds")
def update_beds(facility_id: str, body: BedsIn, s: Store = Depends(store)) -> dict:
    return s.update_beds(facility_id, body.occupied, body.total)


class CheckIn(BaseModel):
    lat: float
    lng: float
    token: str | None = Field(default=None, description="Opaque per-device token; no identity is stored")


@router.post("/facilities/{facility_id}/attendance")
def attendance(facility_id: str, body: CheckIn, s: Store = Depends(store)) -> dict:
    return s.check_in(facility_id, body.lat, body.lng, body.token)


@router.get("/facilities/{facility_id}/notifications")
def notifications(facility_id: str, s: Store = Depends(store)) -> dict:
    return {"notifications": s.notifications_for(facility_id)}


@router.get("/districts/{district}/notifications")
def dho_notifications(district: str, s: Store = Depends(store)) -> dict:
    return {"notifications": s.notifications_for(f"DHO-{district}")}


@router.get("/alerts")
def alerts(state: str | None = None, district: str | None = None, facility_id: str | None = None,
           language: str = "en", s: Store = Depends(store)) -> dict:
    return {"alerts": s.alerts(state, district, facility_id, language), "data_label": s.data_label()}


class AlertReview(BaseModel):
    action: str = Field(description="verify | dismiss")
    reviewed_by: str = "District Health Officer"


@router.post("/alerts/{alert_id}/review")
def review_alert(alert_id: str, body: AlertReview, _: str = Depends(require_dho), s: Store = Depends(store)) -> dict:
    return s.review_alert(alert_id, body.action, body.reviewed_by)


@router.get("/overview")
def overview(state: str | None = None, district: str | None = None, s: Store = Depends(store)) -> dict:
    return s.overview(state, district)


@router.get("/medicines")
def medicines(s: Store = Depends(store)) -> dict:
    return {"medicines": list(s.medicines.values())}
