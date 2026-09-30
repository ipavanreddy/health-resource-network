"""Load the synthetic dataset into BigQuery (real-mode path for PRD §42 data).

    python data/generator/synth.py --out data/generated
    cd services/api && uv run python ../../data/transformations/load_bigquery.py --data ../../data/generated

Requires GOOGLE_CLOUD_PROJECT + BIGQUERY_DATASET in .env and ADC credentials. Tables are created by
infrastructure/bigquery/schema.sql (replace ${PROJECT} / ${DATASET}).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from google.cloud import bigquery  # noqa: E402

from app.config import settings  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, default=Path("data/generated"))
    a = p.parse_args()
    if not settings.google_cloud_project:
        sys.exit("Set GOOGLE_CLOUD_PROJECT (and BIGQUERY_DATASET) in .env first")
    client = bigquery.Client(project=settings.google_cloud_project)
    ds = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"
    fac = json.loads((a.data / "facilities.json").read_text())
    meta = fac["metadata"]
    cols = {"facility_id", "hfr_id", "name", "type", "state", "district", "district_name", "block", "lat", "lng",
            "warehouse_id", "lead_time_days", "beds_total", "staff_sanctioned"}
    rows = [{k: v for k, v in f.items() if k in cols} | {"is_synthetic": True,
                                                          "dataset_version": meta["dataset_version"]}
            for f in fac["facilities"]]
    client.load_table_from_json(rows, f"{ds}.facilities").result()
    job_cfg = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1)
    with open(a.data / "daily_consumption.csv.gz", "rb") as fh:
        client.load_table_from_file(fh, f"{ds}.daily_consumption", job_config=job_cfg).result()
    print(f"loaded {len(rows)} facilities and daily consumption into {ds}")


if __name__ == "__main__":
    main()
