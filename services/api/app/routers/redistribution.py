"""Redistribution optimisation and the transfer approval workflow (PRD §16, FR-07)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.redistribution.optimizer import Params
from app.redistribution.service import run_optimization
from app.routers.deps import DHO, require_dho, role, store
from app.store import Store

router = APIRouter(prefix="/api", tags=["redistribution"])


class OptimizeIn(BaseModel):
    state: str | None = None
    district: str | None = None
    drug_code: str | None = None
    language: str = "en"
    target_cover_days: float = Field(30, gt=0)
    receiver_cover_below: float = Field(14, gt=0)
    donor_min_cover: float = Field(60, gt=0)
    donor_safety_days: float = Field(45, gt=0)
    max_travel_minutes: float = Field(120, gt=0)
    allow_cross_district: bool = False
    max_transfers: int = Field(12, ge=1, le=50)
    tracer_only: bool = True


@router.post("/redistribution/optimize")
def optimize(body: OptimizeIn, s: Store = Depends(store)) -> dict:
    if body.donor_safety_days >= body.donor_min_cover:
        raise HTTPException(400, "donor_safety_days must be below donor_min_cover")
    p = Params(**body.model_dump(exclude={"state", "district", "drug_code", "language"}))
    return run_optimization(s, body.state, body.district, body.drug_code, p, body.language)


@router.get("/transfers")
def transfers(state: str | None = None, district: str | None = None, status: str | None = None,
              facility_id: str | None = None, s: Store = Depends(store)) -> dict:
    return {"transfers": s.list_transfers(state, district, status, facility_id)}


class ActionIn(BaseModel):
    by: str | None = None
    note: str | None = None


@router.post("/transfers/{transfer_id}/approve")
def approve(transfer_id: str, body: ActionIn, _: str = Depends(require_dho), s: Store = Depends(store)) -> dict:
    return s.transition(transfer_id, "approve", body.by or "District Health Officer", body.note)


@router.post("/transfers/{transfer_id}/reject")
def reject(transfer_id: str, body: ActionIn, _: str = Depends(require_dho), s: Store = Depends(store)) -> dict:
    return s.transition(transfer_id, "reject", body.by or "District Health Officer", body.note)


@router.post("/transfers/{transfer_id}/dispatch")
def dispatch(transfer_id: str, body: ActionIn, r: str = Depends(role), s: Store = Depends(store)) -> dict:
    return s.transition(transfer_id, "dispatch", body.by or ("District Health Officer" if r == DHO else "PHC staff"),
                        body.note)


@router.post("/transfers/{transfer_id}/receive")
def receive(transfer_id: str, body: ActionIn, r: str = Depends(role), s: Store = Depends(store)) -> dict:
    return s.transition(transfer_id, "receive", body.by or ("District Health Officer" if r == DHO else "PHC staff"),
                        body.note)
