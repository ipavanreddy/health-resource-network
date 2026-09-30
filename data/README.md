# Data

Every dataset (file or table) must carry: `source`, `reference_timestamp`, `dataset_version`,
`geographic_scope`, and `is_sample` / `is_synthetic`. Labelled in the UI as well.

- `generator/synth.py`: transparent synthetic data generator (PRD §42). Deterministic for a seed + reference
  time. ~200 facilities (TN, UP, OD), 3 years of daily consumption, seasonality, injected outbreaks and
  stock-outs, the three live demo scenarios, and each state's snapshot in its own native export format.
  - `python data/generator/synth.py --out data/generated` → full dataset (gitignored; ~7.5 MB gzip)
  - `python data/generator/synth.py --sample --out data/sample` → small committed sample
  (run with the API environment: `cd services/api && uv run python ../../data/generator/synth.py ...`)
- `schemas/canonical_v1.json`: canonical facility record (PRD §21), exported from
  `services/api/app/interop/canonical.py` by `services/api/scripts/export_schemas.py`
- `adapters/`: one JSON per state = state configuration + declarative adapter (native → canonical)
- `sample/`: small, committed, labelled demo data (metadata in every file; `manifest.json` lists injected events)
- `transformations/load_bigquery.py`: loads the generated dataset into BigQuery (real-mode path)
