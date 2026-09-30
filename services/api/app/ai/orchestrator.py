"""Run a structured Gemini task, or a deterministic labelled demo fallback when Gemini is unavailable.

Every result carries provenance (model_name, model_version, prompt_version) and a `mode`:
- "gemini": validated Gemini output
- "demo": Gemini not configured; deterministic local implementation / fixture
- "demo_fallback": Gemini configured but the call failed; deterministic local implementation used
"""
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from google.genai import types
from pydantic import BaseModel

from app.ai.gemini import generate_structured, load_prompt
from app.integrations.modes import gemini_enabled

log = logging.getLogger(__name__)


def render_prompt(name: str, version: str, **values: str) -> str:
    text = load_prompt(name, version)
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def run_structured[T: BaseModel](
    name: str,
    version: str,
    schema: type[T],
    values: dict[str, str],
    demo: Callable[[], T],
    demo_model: str,
    parts: list[types.Part] | None = None,
    thinking_budget: int | None = None,
) -> tuple[T, dict]:
    prompt_version = f"{name}_{version}"
    if gemini_enabled():
        try:
            result, prov = generate_structured(render_prompt(name, version, **values), schema, prompt_version, parts,
                                               thinking_budget)
            return result, {**prov.model_dump(mode="json"), "mode": "gemini", "is_demo": False}
        except Exception as exc:  # noqa: BLE001 - never break the journey; label the fallback
            log.warning("Gemini call %s failed, using demo fallback: %s", prompt_version, exc)
            mode = "demo_fallback"
    else:
        mode = "demo"
    return demo(), {
        "model_name": demo_model, "model_version": "local-1.0", "prompt_version": prompt_version,
        "generated_at": datetime.now(UTC).isoformat(), "mode": mode, "is_demo": True,
    }
