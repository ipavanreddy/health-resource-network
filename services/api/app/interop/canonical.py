"""Canonical Health Resource Schema (PRD §21, §31). Exported to data/schemas/ by scripts/export_schemas.py."""
from datetime import datetime

from pydantic import BaseModel, Field

SCHEMA_VERSION = "canonical-v1"


class CanonicalStock(BaseModel):
    drug_code: str
    on_hand: int
    in_transit: int
    days_of_cover: float | None
    status: str
    stockout_risk: float
    near_expiry_qty: int
    updated_at: datetime
    source: str


class Beds(BaseModel):
    total: int
    occupied: int


class Staff(BaseModel):
    sanctioned: int
    present: int


class Risk(BaseModel):
    stockout_risk: float = Field(description="Max stock-out risk over tracer medicines")
    surge_flag: bool


class DataLabel(BaseModel):
    source: str
    dataset_version: str
    is_synthetic: bool
    reference_timestamp: str


class CanonicalFacilityRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    state: str
    district: str
    block: str
    facility_id: str
    hfr_id: str
    timestamp: datetime
    stock: list[CanonicalStock]
    beds: Beds
    staff: Staff
    footfall: dict
    risk: Risk
    data_label: DataLabel
