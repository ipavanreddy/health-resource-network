"""Gemini orchestration: structured context in, schema-validated JSON out, versioned."""
from datetime import UTC, datetime
from functools import lru_cache

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import REPO_ROOT, settings

PROMPTS_DIR = REPO_ROOT / "ai" / "prompts"


class AIProvenance(BaseModel):
    model_name: str
    model_version: str
    prompt_version: str
    generated_at: datetime


@lru_cache
def client() -> genai.Client:
    if settings.google_genai_use_vertexai:
        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    return genai.Client(api_key=settings.gemini_api_key)


def load_prompt(name: str, version: str) -> str:
    """Load ai/prompts/{name}_{version}.md."""
    return (PROMPTS_DIR / f"{name}_{version}.md").read_text()


def generate_structured[T: BaseModel](
    prompt: str,
    schema: type[T],
    prompt_version: str,
    parts: list[types.Part] | None = None,
) -> tuple[T, AIProvenance]:
    """Call Gemini with a response schema and return the validated object plus provenance."""
    response = client().models.generate_content(
        model=settings.gemini_model,
        contents=[prompt, *(parts or [])],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    result = schema.model_validate_json(response.text)
    provenance = AIProvenance(
        model_name=settings.gemini_model,
        model_version=response.model_version or settings.gemini_model,
        prompt_version=prompt_version,
        generated_at=datetime.now(UTC),
    )
    return result, provenance
