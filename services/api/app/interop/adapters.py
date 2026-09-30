"""State data adapters (PRD §22.3): state-native records → canonical stock snapshot.

Each state is described declaratively in data/adapters/<state>.json (field map, drug-code map, timestamp
format, unit factors). One generic engine applies them, so adding a state means adding a JSON file.
"""
import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from app.config import REPO_ROOT

ADAPTERS_DIR = REPO_ROOT / "data" / "adapters"


@lru_cache
def load_state_files() -> dict[str, dict]:
    out = {}
    for p in sorted(ADAPTERS_DIR.glob("*.json")):
        doc = json.loads(p.read_text())
        out[doc["state"]] = doc
    return out


class AdapterError(ValueError):
    pass


def _parse_ts(rec: dict, spec: dict) -> datetime:
    raw = " ".join(str(rec[f]) for f in spec["fields"])
    if spec["format"] == "iso":
        ts = datetime.fromisoformat(raw)
    else:
        ts = datetime.strptime(raw, spec["format"])
    if ts.tzinfo is None:
        sign = -1 if spec.get("utc_offset", "+00:00").startswith("-") else 1
        hh, mm = spec.get("utc_offset", "+00:00")[1:].split(":")
        ts = ts.replace(tzinfo=timezone(sign * timedelta(hours=int(hh), minutes=int(mm))))
    return ts


def to_canonical(state: str, record: dict, hfr_index: dict[str, str]) -> dict:
    """Map one native record to a canonical snapshot. `hfr_index` maps HFR id → canonical facility_id."""
    cfg = load_state_files().get(state)
    if not cfg:
        raise AdapterError(f"No adapter for state {state}")
    a = cfg["adapter"]
    try:
        hfr = str(record[a["facility_key"]])
        native_code = str(record[a["fields"]["drug_code"]])
    except KeyError as exc:
        raise AdapterError(f"Missing field {exc} for adapter {a['adapter_id']}") from exc
    if hfr not in hfr_index:
        raise AdapterError(f"Unknown facility HFR id {hfr}")
    drug = a["drug_code_map"].get(native_code)
    if not drug:
        raise AdapterError(f"Unmapped drug code {native_code}")
    factor = a.get("unit_factors", {}).get(drug, 1)

    def qty(key: str) -> int:
        v = record.get(a["fields"][key], 0) or 0
        return int(round(float(v) * factor))

    return {
        "facility_id": hfr_index[hfr], "hfr_id": hfr, "drug_code": drug,
        "on_hand": qty("on_hand"), "in_transit": qty("in_transit"), "near_expiry_qty": qty("near_expiry_qty"),
        "updated_at": _parse_ts(record, a["timestamp"]),
        "source": f"adapter:{a['adapter_id']}",
    }


def adapter_summary(state: str) -> dict:
    cfg = load_state_files()[state]["adapter"]
    return {k: cfg[k] for k in ("adapter_id", "description", "facility_key", "fields", "timestamp", "unit_factors")} | {
        "drug_code_map": cfg["drug_code_map"]}
