"""Export JSON Schemas: Gemini output schemas → ai/schemas/, canonical schema → data/schemas/.

Run: cd services/api && uv run python -m scripts.export_schemas
"""
import json

from app.ai.schemas import EXPORTED
from app.config import REPO_ROOT
from app.interop.canonical import CanonicalFacilityRecord


def schema_files() -> dict:
    out = {REPO_ROOT / "ai" / "schemas" / f"{name}.json": model.model_json_schema() for name, model in EXPORTED.items()}
    out[REPO_ROOT / "data" / "schemas" / "canonical_v1.json"] = CanonicalFacilityRecord.model_json_schema()
    return out


def render(schema: dict) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    for path, schema in schema_files().items():
        path.write_text(render(schema))
        print("wrote", path.relative_to(REPO_ROOT))
