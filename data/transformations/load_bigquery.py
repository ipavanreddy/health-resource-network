"""Set up the BigQuery side of PHC Pulse (real-mode path for PRD §28 / §42 data).

    python data/generator/synth.py --out data/generated
    cd services/api && uv run python ../../data/transformations/load_bigquery.py --all

Steps (each can be run on its own):
  --create-tables  apply infrastructure/bigquery/schema.sql (canonical + event tables; dataset must exist)
  --load           load the synthetic facilities + daily consumption (replaces table contents)
  --train          train the shared BigQuery ML ARIMA_PLUS model (infrastructure/bigquery/forecast_model.sql)

Requires GOOGLE_CLOUD_PROJECT + BIGQUERY_DATASET in .env and ADC credentials. Idempotent.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "api"))

from google.cloud import bigquery  # noqa: E402

from app.config import settings  # noqa: E402

SQL_DIR = ROOT / "infrastructure" / "bigquery"


def _statements(path: Path) -> list[str]:
    sql = path.read_text().replace("${PROJECT}", settings.google_cloud_project)
    sql = sql.replace("${DATASET}", settings.bigquery_dataset).replace("${BIGQUERY_DATASET}", settings.bigquery_dataset)
    sql = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
    # The dataset is provisioned separately (not by this script).
    return [s.strip() for s in sql.split(";") if s.strip() and not re.match(r"CREATE SCHEMA", s.strip(), re.I)]


def run_sql(client: bigquery.Client, path: Path) -> None:
    for stmt in _statements(path):
        head = " ".join(stmt.split()[:6])
        t0 = time.time()
        client.query(stmt, location="asia-south1").result()
        print(f"  ok ({time.time() - t0:.0f}s): {head} ...")


def load(client: bigquery.Client, data: Path, ds: str) -> None:
    fac = json.loads((data / "facilities.json").read_text())
    meta = fac["metadata"]
    cols = {"facility_id", "hfr_id", "name", "type", "state", "district", "district_name", "block", "lat", "lng",
            "warehouse_id", "lead_time_days", "beds_total", "staff_sanctioned"}
    rows = [{k: v for k, v in f.items() if k in cols} | {"is_synthetic": True,
                                                          "dataset_version": meta["dataset_version"]}
            for f in fac["facilities"]]
    truncate = bigquery.WriteDisposition.WRITE_TRUNCATE
    client.load_table_from_json(rows, f"{ds}.facilities",
                                job_config=bigquery.LoadJobConfig(write_disposition=truncate)).result()
    job_cfg = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1,
                                     write_disposition=truncate)
    with open(data / "daily_consumption.csv.gz", "rb") as fh:
        job = client.load_table_from_file(fh, f"{ds}.daily_consumption", job_config=job_cfg)
        job.result()
    print(f"  loaded {len(rows)} facilities and {job.output_rows:,} daily consumption rows into {ds}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, default=ROOT / "data" / "generated")
    p.add_argument("--create-tables", action="store_true")
    p.add_argument("--load", action="store_true")
    p.add_argument("--train", action="store_true")
    p.add_argument("--all", action="store_true")
    a = p.parse_args()
    if not settings.google_cloud_project:
        sys.exit("Set GOOGLE_CLOUD_PROJECT (and BIGQUERY_DATASET) in .env first")
    if not (a.create_tables or a.load or a.train or a.all):
        a.load = True  # backwards compatible default
    client = bigquery.Client(project=settings.google_cloud_project)
    ds = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"
    if a.create_tables or a.all:
        print("Creating tables")
        run_sql(client, SQL_DIR / "schema.sql")
    if a.load or a.all:
        print("Loading synthetic data")
        load(client, a.data, ds)
    if a.train or a.all:
        print("Training BigQuery ML ARIMA_PLUS (a few minutes)")
        run_sql(client, SQL_DIR / "forecast_model.sql")


if __name__ == "__main__":
    main()
