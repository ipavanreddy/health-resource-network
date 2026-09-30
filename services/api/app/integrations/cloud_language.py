"""Cloud Speech-to-Text, Text-to-Speech and Translation (REST, API key) with labelled demo fallbacks."""
import base64
import logging

import httpx

from app.config import settings
from app.integrations.modes import cloud_language_enabled

log = logging.getLogger(__name__)

LANG_CODES = {"en": "en-IN", "hi": "hi-IN", "ta": "ta-IN"}

# Demo-mode transcripts: what the scripted demo voice report says in each language (PRD §10 / §44).
DEMO_TRANSCRIPTS = {
    "en": "Paracetamol 500, 1,200 tablets left. ORS 40 packets. Amoxicillin finished.",
    "ta": "பாராசிட்டமால் 500, 1200 மாத்திரைகள் உள்ளன. ஓஆர்எஸ் 40 பாக்கெட் உள்ளது. அமாக்ஸிசிலின் தீர்ந்துவிட்டது.",
    "hi": "पैरासिटामोल 500, 900 गोलियां बची हैं। आईवी फ्लूइड 12 बोतल। ओआरएस 150 पैकेट।",
}


def _key() -> dict:
    return {"key": settings.google_cloud_api_key}


def speech_to_text(audio: bytes, mime_type: str, language: str) -> tuple[str, str] | None:
    """Cloud Speech-to-Text v1. Returns (transcript, 'cloud_speech') or None if unavailable."""
    if not cloud_language_enabled() or not audio:
        return None
    encoding = "WEBM_OPUS" if "webm" in mime_type else "OGG_OPUS" if "ogg" in mime_type else None
    config: dict = {"languageCode": LANG_CODES.get(language, "en-IN"), "enableAutomaticPunctuation": True}
    if encoding:
        config.update(encoding=encoding, sampleRateHertz=48000)
    try:
        res = httpx.post("https://speech.googleapis.com/v1/speech:recognize", params=_key(), timeout=30,
                         json={"config": config, "audio": {"content": base64.b64encode(audio).decode()}})
        res.raise_for_status()
        text = " ".join(r["alternatives"][0]["transcript"] for r in res.json().get("results", []))
        return (text.strip(), "cloud_speech") if text.strip() else None
    except Exception as exc:  # noqa: BLE001
        log.warning("Speech-to-Text failed: %s", exc)
        return None


def text_to_speech(text: str, language: str) -> dict:
    """Cloud Text-to-Speech v1 (MP3). Demo mode tells the client to use browser speech synthesis."""
    if cloud_language_enabled():
        try:
            res = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize", params=_key(), timeout=30,
                             json={"input": {"text": text},
                                   "voice": {"languageCode": LANG_CODES.get(language, "en-IN")},
                                   "audioConfig": {"audioEncoding": "MP3"}})
            res.raise_for_status()
            return {"mode": "real", "provider": "cloud_tts", "audio_base64": res.json()["audioContent"],
                    "mime_type": "audio/mpeg", "language": language}
        except Exception as exc:  # noqa: BLE001
            log.warning("Text-to-Speech failed: %s", exc)
    return {"mode": "demo", "provider": "browser_speech_synthesis", "audio_base64": None,
            "mime_type": None, "language": language, "lang_tag": LANG_CODES.get(language, "en-IN")}


def translate(text: str, target: str, source: str | None = None) -> dict:
    """Cloud Translation v2. Demo mode returns the text unchanged (UI strings are pre-translated)."""
    if cloud_language_enabled() and target != source:
        try:
            body = {"q": text, "target": target, "format": "text"}
            if source:
                body["source"] = source
            res = httpx.post("https://translation.googleapis.com/language/translate/v2", params=_key(), json=body,
                             timeout=20)
            res.raise_for_status()
            return {"mode": "real", "provider": "cloud_translation", "language": target,
                    "text": res.json()["data"]["translations"][0]["translatedText"]}
        except Exception as exc:  # noqa: BLE001
            log.warning("Translation failed: %s", exc)
    return {"mode": "demo", "provider": "none (untranslated)", "language": source or target, "text": text}
