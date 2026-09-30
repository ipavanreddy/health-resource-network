"""Stock capture AI pipeline: speech → transcript → Gemini extraction (or labelled demo fallbacks)."""
import json

from google.genai import types

from app.ai.orchestrator import run_structured
from app.ai.schemas import RegisterExtraction, RegisterRow, StockExtraction, Transcript
from app.capture.parser import parse_stock_text
from app.integrations import cloud_language
from app.integrations.modes import gemini_enabled

LANG_NAMES = {"en": "English", "hi": "Hindi", "ta": "Tamil"}


def medicine_master_json(medicines: list[dict]) -> str:
    return json.dumps([{k: m[k] for k in ("drug_code", "name", "strength", "form", "unit", "local_names")}
                       for m in medicines], ensure_ascii=False)


def _validate(result: StockExtraction, medicines: list[dict]) -> StockExtraction:
    """Schema is validated by Pydantic; additionally drop drug codes not in the master (never trust blindly)."""
    codes = {m["drug_code"] for m in medicines}
    for it in result.items:
        if it.drug_code and it.drug_code not in codes:
            result.unrecognised.append(it.spoken_name)
            it.drug_code = None
    result.requires_confirmation = True
    return result


def extract_stock(text: str, language: str, medicines: list[dict]) -> tuple[StockExtraction, dict]:
    result, prov = run_structured(
        "extract_stock", "v1", StockExtraction,
        {"medicine_master": medicine_master_json(medicines), "language": LANG_NAMES.get(language, language),
         "text": text},
        demo=lambda: parse_stock_text(text, medicines), demo_model="demo-rule-parser",
    )
    return _validate(result, medicines), prov


def transcribe(audio: bytes | None, mime_type: str, language: str, browser_transcript: str | None) -> dict:
    """Priority: Cloud Speech-to-Text → Gemini audio → browser Web Speech transcript → demo transcript."""
    mime_type = (mime_type or "").split(";")[0].strip()
    if audio:
        stt = cloud_language.speech_to_text(audio, mime_type, language)
        if stt:
            return {"transcript": stt[0], "provider": "cloud_speech_to_text", "is_demo": False}
        if gemini_enabled():
            res, prov = run_structured(
                "transcribe", "v1", Transcript, {"language": LANG_NAMES.get(language, language)},
                demo=lambda: Transcript(transcript="", language=language), demo_model="none",
                parts=[types.Part.from_bytes(data=audio, mime_type=mime_type or "audio/webm")],
            )
            if res.transcript.strip() and not prov["is_demo"]:
                return {"transcript": res.transcript, "provider": "gemini_audio", "is_demo": False, "provenance": prov}
    if browser_transcript and browser_transcript.strip():
        return {"transcript": browser_transcript.strip(), "provider": "browser_web_speech", "is_demo": False}
    return {"transcript": cloud_language.DEMO_TRANSCRIPTS.get(language, cloud_language.DEMO_TRANSCRIPTS["en"]),
            "provider": "demo_transcript", "is_demo": True}


# Demo fixture: what the sample register page (apps/phc-web/public/sample-register.svg) contains.
DEMO_REGISTER = RegisterExtraction(
    register_date="29/09/2026",
    rows=[
        RegisterRow(medicine_text="Tab. Paracetamol 500", drug_code="PCM-500-TAB", opening=1500, received=0,
                    issued=300, closing=1200, match_confidence=0.96, illegible_cells=[]),
        RegisterRow(medicine_text="ORS pkt", drug_code="ORS-SACHET", opening=145, received=0, issued=105, closing=40,
                    match_confidence=0.94, illegible_cells=[]),
        RegisterRow(medicine_text="Zinc 20mg", drug_code="ZNC-20-TAB", opening=420, received=0, issued=150,
                    closing=270, match_confidence=0.93, illegible_cells=[]),
        RegisterRow(medicine_text="Cap. Amoxy 500", drug_code="AMX-500-CAP", opening=60, received=0, issued=60,
                    closing=0, match_confidence=0.9, illegible_cells=[]),
        RegisterRow(medicine_text="RL 500ml", drug_code="IVF-RL-500", opening=30, received=12, issued=9,
                    closing=None, match_confidence=0.88, illegible_cells=["closing"]),
        RegisterRow(medicine_text="Tab. Cetriz", drug_code=None, opening=200, received=0, issued=40, closing=160,
                    match_confidence=0.2, illegible_cells=[]),
    ],
    unrecognised=["Tab. Cetriz"],
    requires_confirmation=True,
)


def extract_register(image: bytes | None, mime_type: str, medicines: list[dict]) -> tuple[RegisterExtraction, dict]:
    parts = [types.Part.from_bytes(data=image, mime_type=mime_type or "image/png")] if image else None
    if not image:
        # Without a photo there is nothing for Gemini to read: always the labelled fixture.
        return DEMO_REGISTER.model_copy(deep=True), {
            "model_name": "demo-fixture", "model_version": "local-1.0", "prompt_version": "extract_register_v1",
            "mode": "demo", "is_demo": True, "generated_at": None}
    result, prov = run_structured(
        "extract_register", "v1", RegisterExtraction, {"medicine_master": medicine_master_json(medicines)},
        demo=lambda: DEMO_REGISTER.model_copy(deep=True), demo_model="demo-fixture", parts=parts,
        # Handwriting: let the model reason about smudged / crossed-out cells so it flags them instead of guessing.
        thinking_budget=-1,
    )
    codes = {m["drug_code"] for m in medicines}
    for r in result.rows:
        if r.drug_code and r.drug_code not in codes:
            result.unrecognised.append(r.medicine_text)
            r.drug_code = None
    result.requires_confirmation = True
    return result, prov
