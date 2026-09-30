"""Structured Gemini outputs (PRD §33). Exported as JSON Schema to ai/schemas/ (scripts/export_schemas.py)."""
from typing import Literal

from pydantic import BaseModel, Field


class ExtractedItem(BaseModel):
    spoken_name: str = Field(description="Medicine name exactly as said/written by staff")
    drug_code: str | None = Field(description="Matched drug_code from the medicine master, or null if no match")
    quantity: float | None = Field(description="Quantity stated. null if not stated. 0 only if stated as finished/nil")
    unit: str | None = Field(description="Unit as stated or from the medicine master")
    match_confidence: float = Field(ge=0, le=1)


class StockExtraction(BaseModel):
    items: list[ExtractedItem]
    unrecognised: list[str] = Field(description="Mentions that could not be matched to the medicine master")
    requires_confirmation: bool = True


class RegisterRow(BaseModel):
    medicine_text: str = Field(description="Medicine name as written in the register")
    drug_code: str | None
    opening: float | None = Field(description="null if illegible or missing")
    received: float | None
    issued: float | None
    closing: float | None
    match_confidence: float = Field(ge=0, le=1)
    illegible_cells: list[str] = Field(description="Names of cells that could not be read, e.g. ['closing']")


class RegisterExtraction(BaseModel):
    register_date: str | None = Field(description="Date written on the page (as written), or null")
    rows: list[RegisterRow]
    unrecognised: list[str]
    requires_confirmation: bool = True


class Transcript(BaseModel):
    transcript: str = Field(description="Verbatim transcript in the spoken language; empty if inaudible")
    language: str


class RedistributionExplanation(BaseModel):
    summary: str
    risk_level: Literal["low", "medium", "high"]
    reasons: list[str]
    impact: str
    uncertainties: list[str]
    travel_minutes: float
    confidence: float = Field(ge=0, le=1)
    transfer_note: str = Field(description="Short note to accompany the physical transfer")
    requires_human_review: bool = True


EXPORTED = {
    "stock_extraction_v1": StockExtraction,
    "register_extraction_v1": RegisterExtraction,
    "transcript_v1": Transcript,
    "redistribution_explanation_v1": RedistributionExplanation,
}
