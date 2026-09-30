from app.ai.gemini import PROMPTS_DIR
from scripts.export_schemas import render, schema_files


def test_exported_schemas_are_in_sync():
    for path, schema in schema_files().items():
        assert path.exists(), f"run scripts/export_schemas.py ({path.name} missing)"
        assert path.read_text() == render(schema), f"{path.name} is stale; re-run scripts/export_schemas.py"


def test_prompts_exist_and_are_versioned():
    for name in ("extract_stock_v1", "extract_register_v1", "transcribe_v1", "explain_transfer_v1"):
        assert (PROMPTS_DIR / f"{name}.md").exists()


def test_golden_extraction_set_demo_parser():
    from scripts.eval_extraction import evaluate

    report = evaluate()
    assert report["model"].startswith("demo-rule-parser")
    assert report["exact_match"] == report["cases"], [r for r in report["results"] if not r["exact"]]
