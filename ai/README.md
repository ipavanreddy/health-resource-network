# AI assets

- `prompts/`: one file per prompt version, `<name>_v<N>.md`. Never edit a released version; add `_v2`.
  `extract_stock_v1`, `extract_register_v1`, `transcribe_v1`, `explain_transfer_v1`.
- `schemas/`: JSON schemas for every structured Gemini output, exported from `services/api/app/ai/schemas.py`
  (`cd services/api && uv run python -m scripts.export_schemas`; a test fails if they drift).
- `evaluation/`: golden test cases (`extraction_golden_v1.json`) scored by
  `cd services/api && uv run python -m scripts.eval_extraction` (Gemini if configured, else demo parser).
