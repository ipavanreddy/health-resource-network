"""Speech-to-Text, Translation, Text-to-Speech (PRD §17, FR-08)."""
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field

from app.capture.extraction import transcribe
from app.integrations import cloud_language

router = APIRouter(prefix="/api", tags=["language"])


@router.post("/speech-to-text")
async def speech_to_text(language: str = Form("en"), transcript: str | None = Form(None),
                         audio: UploadFile | None = File(None)) -> dict:
    data = await audio.read() if audio else None
    return transcribe(data, (audio.content_type or "") if audio else "", language, transcript)


class TranslateIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    target: str
    source: str | None = None


@router.post("/translate")
def translate(body: TranslateIn) -> dict:
    return cloud_language.translate(body.text, body.target, body.source)


class SpeakIn(BaseModel):
    text: str = Field(min_length=1, max_length=3000)
    language: str = "en"


@router.post("/text-to-speech")
def text_to_speech(body: SpeakIn) -> dict:
    return cloud_language.text_to_speech(body.text, body.language)
