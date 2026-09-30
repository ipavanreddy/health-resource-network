"""Stock capture: voice / text / register photo / form → extraction → staff confirmation (PRD §10, FR-02)."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.capture.extraction import extract_register, extract_stock, transcribe
from app.routers.deps import store
from app.store import Store

router = APIRouter(prefix="/api/capture", tags=["capture"])
MAX_UPLOAD = 10 * 1024 * 1024


class TextIn(BaseModel):
    facility_id: str
    text: str = Field(min_length=1, max_length=2000)
    language: str = "en"


class FormItem(BaseModel):
    drug_code: str
    quantity: float | None = Field(default=None, ge=0)
    spoken_name: str | None = None


class FormIn(BaseModel):
    facility_id: str
    language: str = "en"
    items: list[FormItem]


class ConfirmIn(BaseModel):
    items: list[FormItem]
    confirmed_by: str = "PHC staff"


async def _read(upload: UploadFile | None) -> tuple[bytes | None, str]:
    if upload is None:
        return None, ""
    data = await upload.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "File too large (max 10 MB)")
    return (data or None), (upload.content_type or "")


@router.post("/text")
def capture_text(body: TextIn, s: Store = Depends(store)) -> dict:
    s.facility(body.facility_id)
    result, prov = extract_stock(body.text, body.language, list(s.medicines.values()))
    return s.create_capture(body.facility_id, "text", body.language, [i.model_dump() for i in result.items],
                            result.unrecognised, prov, transcript={"transcript": body.text, "provider": "typed"})


@router.post("/voice")
async def capture_voice(facility_id: str = Form(...), language: str = Form("en"), transcript: str | None = Form(None),
                        audio: UploadFile | None = File(None), s: Store = Depends(store)) -> dict:
    s.facility(facility_id)
    data, mime = await _read(audio)
    tr = transcribe(data, mime, language, transcript)
    result, prov = extract_stock(tr["transcript"], language, list(s.medicines.values()))
    return s.create_capture(facility_id, "voice", language, [i.model_dump() for i in result.items],
                            result.unrecognised, prov, transcript=tr)


@router.post("/photo")
async def capture_photo(facility_id: str = Form(...), language: str = Form("en"),
                        image: UploadFile | None = File(None), s: Store = Depends(store)) -> dict:
    s.facility(facility_id)
    data, mime = await _read(image)
    result, prov = extract_register(data, mime, list(s.medicines.values()))
    items = [{"spoken_name": r.medicine_text, "drug_code": r.drug_code, "quantity": r.closing,
              "unit": None, "match_confidence": r.match_confidence} for r in result.rows if r.drug_code]
    return s.create_capture(facility_id, "photo", language, items, result.unrecognised, prov,
                            rows=[r.model_dump() for r in result.rows], register_date=result.register_date)


@router.post("/form")
def capture_form(body: FormIn, s: Store = Depends(store)) -> dict:
    s.facility(body.facility_id)
    items = [{"spoken_name": i.spoken_name or i.drug_code, "drug_code": i.drug_code, "quantity": i.quantity,
              "unit": None, "match_confidence": 1.0} for i in body.items if i.drug_code in s.medicines]
    prov = {"model_name": "none (structured form)", "model_version": "n/a", "prompt_version": "n/a", "mode": "form",
            "is_demo": False}
    return s.create_capture(body.facility_id, "form", body.language, items, [], prov)


@router.get("/{capture_id}")
def get_capture(capture_id: str, s: Store = Depends(store)) -> dict:
    cap = s.captures.get(capture_id)
    if not cap:
        raise HTTPException(404, "Unknown capture")
    return cap


@router.post("/{capture_id}/confirm")
def confirm(capture_id: str, body: ConfirmIn, s: Store = Depends(store)) -> dict:
    return s.confirm_capture(capture_id, [i.model_dump() for i in body.items], body.confirmed_by)
