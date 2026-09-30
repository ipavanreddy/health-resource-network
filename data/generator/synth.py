"""PHC Pulse transparent synthetic data generator (PRD §42).

EVERYTHING THIS MODULE PRODUCES IS SYNTHETIC. It is not real facility, stock or patient data.

What it generates (deterministic for a given ``seed`` and ``now``):
- ~200 facilities (PHC / CHC / district warehouse) across Tamil Nadu, Uttar Pradesh and Odisha,
  placed around real district / block names with jittered coordinates.
- A medicine master (tracer subset of the national essential medicine list) with local names.
- ~3 years (1,096 days) of daily consumption per dispensing facility x medicine, built as:
      expected = facility footfall x medicine base rate x state seasonality(day of year)
                 x weekday pattern x slow trend x injected outbreak multiplier
      recorded = Poisson(expected x Gamma noise), then set to 0 on injected stock-out days
  Stock-out days are returned as a separate flag array, because zero recorded consumption during a
  stock-out does NOT mean zero demand (PRD §14).
- Injected historical outbreaks (one per district per year) and the three live demo scenarios
  (PRD §43): TN Madurai post-flood diarrhoea, UP Gorakhpur vector-borne fever, OD Koraput malaria.
- Current stock snapshots, beds, staff presence and reporting freshness, plus each state's snapshot
  in its own illustrative *native export format* (mapped to the canonical schema by state adapters).

Seasonality amplitudes/peaks are hand-set to be plausible (monsoon diarrhoea, post-monsoon dengue,
Odisha malaria peak); they are documented in ``SEASONALITY`` below, not fitted to real HMIS data.

CLI:  python data/generator/synth.py --out data/generated            (full dataset, gitignored)
      python data/generator/synth.py --sample --out data/sample      (small committed sample)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

GENERATOR_VERSION = "1.0.0"
DATASET_VERSION = f"phc-pulse-synthetic-{GENERATOR_VERSION}"
DEFAULT_SEED = 20260930
HISTORY_DAYS = 3 * 365 + 1
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SOURCE = "PHC Pulse synthetic generator (data/generator/synth.py)"

# ---------------------------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------------------------

MEDICINES: list[dict] = [
    {
        "drug_code": "PCM-500-TAB", "name": "Paracetamol", "strength": "500 mg", "form": "tablet",
        "unit": "tablet", "group": "fever", "is_tracer": True, "base_daily": 60.0, "strength_number": 500,
        "local_names": ["paracetamol", "para", "pcm", "crocin", "dolo", "பாராசிட்டமால்", "பாராசிட்டமோல்",
                        "காய்ச்சல் மாத்திரை", "पैरासिटामोल", "पेरासिटामोल", "बुखार की गोली"],
    },
    {
        "drug_code": "ORS-SACHET", "name": "Oral Rehydration Salts", "strength": "20.5 g/L", "form": "sachet",
        "unit": "sachet", "group": "diarrhoea", "is_tracer": True, "base_daily": 12.0, "strength_number": None,
        "local_names": ["ors", "oral rehydration", "jeevan jal", "ஓஆர்எஸ்", "ஓ.ஆர்.எஸ்", "உப்பு சர்க்கரை கரைசல்",
                        "ओआरएस", "ओ आर एस", "जीवन जल"],
    },
    {
        "drug_code": "ZNC-20-TAB", "name": "Zinc (dispersible)", "strength": "20 mg", "form": "tablet",
        "unit": "tablet", "group": "diarrhoea", "is_tracer": True, "base_daily": 10.0, "strength_number": 20,
        "local_names": ["zinc", "துத்தநாகம்", "ஜிங்க்", "ஜிங்க் மாத்திரை", "जिंक", "ज़िंक"],
    },
    {
        "drug_code": "AMX-500-CAP", "name": "Amoxicillin", "strength": "500 mg", "form": "capsule",
        "unit": "capsule", "group": "antibiotic", "is_tracer": True, "base_daily": 25.0, "strength_number": 500,
        "local_names": ["amoxicillin", "amoxycillin", "amoxy", "amox", "அமாக்ஸிசிலின்", "அமோக்ஸிசிலின்",
                        "எமோக்ஸிசிலின்", "एमोक्सिसिलिन", "अमोक्सिसिलिन"],
    },
    {
        "drug_code": "IVF-RL-500", "name": "Ringer Lactate (IV fluid)", "strength": "500 ml", "form": "bottle",
        "unit": "bottle", "group": "fever", "is_tracer": True, "base_daily": 2.5, "strength_number": 500,
        "local_names": ["ringer lactate", "ringer", "rl", "iv fluid", "iv fluids", "drip", "ரிங்கர்",
                        "சலைன்", "குளுக்கோஸ் பாட்டில்", "आईवी फ्लूइड", "आईवी", "ड्रिप", "रिंगर", "बोतल चढ़ाने"],
    },
    {
        "drug_code": "ACT-AL-TAB", "name": "Artemether + Lumefantrine", "strength": "20/120 mg", "form": "tablet",
        "unit": "tablet", "group": "malaria", "is_tracer": True, "base_daily": 6.0, "strength_number": None,
        "local_names": ["act", "artemether", "lumefantrine", "coartem", "malaria tablet", "malaria medicine",
                        "மலேரியா மாத்திரை", "मलेरिया की दवा", "मलेरिया की गोली", "आर्टेमिथर"],
    },
    {
        "drug_code": "MTF-500-TAB", "name": "Metformin", "strength": "500 mg", "form": "tablet",
        "unit": "tablet", "group": "chronic", "is_tracer": False, "base_daily": 40.0, "strength_number": 500,
        "local_names": ["metformin", "glycomet", "மெட்ஃபார்மின்", "சர்க்கரை மாத்திரை", "मेटफॉर्मिन", "शुगर की गोली"],
    },
    {
        "drug_code": "IFA-TAB", "name": "Iron + Folic Acid", "strength": "60 mg + 0.5 mg", "form": "tablet",
        "unit": "tablet", "group": "chronic", "is_tracer": False, "base_daily": 50.0, "strength_number": None,
        "local_names": ["ifa", "iron folic", "iron", "folic", "இரும்புச்சத்து மாத்திரை", "அயர்ன்", "आयरन",
                        "आयरन की गोली", "आयरन फोलिक"],
    },
]

# Seasonality: 1 + amplitude * cos(2*pi*(day_of_year - peak_day)/365.25). Hand-set, documented.
SEASONALITY: dict[str, dict[str, tuple[float, int]]] = {
    # state: {group: (amplitude, peak day-of-year)}
    "TN": {"diarrhoea": (0.45, 320), "fever": (0.30, 320), "malaria": (0.15, 300), "antibiotic": (0.15, 330),
           "chronic": (0.02, 1)},
    "UP": {"diarrhoea": (0.45, 200), "fever": (0.60, 265), "malaria": (0.35, 255), "antibiotic": (0.20, 15),
           "chronic": (0.02, 1)},
    "OD": {"diarrhoea": (0.40, 205), "fever": (0.40, 225), "malaria": (0.80, 215), "antibiotic": (0.15, 200),
           "chronic": (0.02, 1)},
}

# Malaria burden differs a lot between states: scales ACT base demand.
STATE_DRUG_FACTOR = {"TN": {"ACT-AL-TAB": 0.25}, "UP": {"ACT-AL-TAB": 0.7}, "OD": {"ACT-AL-TAB": 3.0}}

STATES: dict[str, dict] = {
    "TN": {
        "name": "Tamil Nadu", "census_code": "33", "language": "ta",
        "districts": {
            "MDU": {"name": "Madurai", "centre": (9.93, 78.12),
                    "blocks": ["Melur", "Madurai East", "Thirumangalam", "Vadipatti", "Usilampatti",
                               "Kottampatti", "Alanganallur", "Kallikudi"]},
            "TNJ": {"name": "Thanjavur", "centre": (10.79, 79.14),
                    "blocks": ["Kumbakonam", "Orathanadu", "Pattukkottai", "Papanasam", "Thiruvaiyaru",
                               "Budalur", "Peravurani", "Thiruvidaimarudur"]},
        },
    },
    "UP": {
        "name": "Uttar Pradesh", "census_code": "09", "language": "hi",
        "districts": {
            "GKP": {"name": "Gorakhpur", "centre": (26.76, 83.37),
                    "blocks": ["Campierganj", "Pipraich", "Sahjanwa", "Khorabar", "Chargawan", "Bhathat",
                               "Gola", "Bansgaon"]},
            "DEO": {"name": "Deoria", "centre": (26.50, 83.78),
                    "blocks": ["Rudrapur", "Salempur", "Bhatpar Rani", "Gauri Bazar", "Baitalpur",
                               "Lar", "Pathardewa", "Bhaluani"]},
        },
    },
    "OD": {
        "name": "Odisha", "census_code": "21", "language": "en",
        "districts": {
            "KPT": {"name": "Koraput", "centre": (18.81, 82.71),
                    "blocks": ["Jeypore", "Kotpad", "Boipariguda", "Lamtaput", "Pottangi", "Semiliguda",
                               "Borigumma", "Kundura"]},
            "RGD": {"name": "Rayagada", "centre": (19.17, 83.42),
                    "blocks": ["Gunupur", "Bissam Cuttack", "Kashipur", "Muniguda", "Kolnara",
                               "Padmapur", "Gudari", "Chandrapur"]},
        },
    },
}
FACILITIES_PER_DISTRICT = 32  # dispensing facilities (4 per block: CHC in first 4 blocks)

# Live demo scenarios (PRD §43), injected relative to the reference date.
SCENARIOS: list[dict] = [
    {
        "id": "A", "state": "TN", "district": "MDU", "surge_blocks": ["Melur", "Madurai East"],
        "donor_blocks": ["Thirumangalam", "Vadipatti"], "group": "diarrhoea", "multiplier": 3.2,
        "start_days_ago": 9, "language": "ta",
        "title": "Tamil Nadu · Madurai: post-flood diarrhoea surge, ORS stock-out risk",
        "hero_block": "Melur", "focus_drugs": ["ORS-SACHET", "ZNC-20-TAB"],
    },
    {
        "id": "B", "state": "UP", "district": "GKP", "surge_blocks": ["Campierganj", "Pipraich"],
        "donor_blocks": ["Sahjanwa", "Khorabar"], "group": "fever", "multiplier": 2.4,
        "start_days_ago": 18, "language": "hi",
        "title": "Uttar Pradesh · Gorakhpur: vector-borne season, paracetamol / IV fluid demand",
        "hero_block": "Campierganj", "focus_drugs": ["IVF-RL-500", "PCM-500-TAB"],
    },
    {
        "id": "C", "state": "OD", "district": "KPT", "surge_blocks": ["Jeypore", "Kotpad"],
        "donor_blocks": ["Lamtaput", "Boipariguda"], "group": "malaria", "multiplier": 2.5,
        "start_days_ago": 16, "language": "en",
        "title": "Odisha · Koraput: malaria season, antimalarial redistribution",
        "hero_block": "Jeypore", "focus_drugs": ["ACT-AL-TAB"],
    },
]

ROMAN = ["", " II", " III", " IV", " V", " VI"]
WEEKDAY_FACTOR = np.array([1.108, 1.108, 1.108, 1.108, 1.108, 1.108, 0.352])  # Mon..Sun, mean 1.0


@dataclass
class SyntheticDataset:
    metadata: dict
    medicines: list[dict]
    facilities: list[dict]                 # all facilities incl. warehouses
    dispensing_ids: list[str]              # row order of the consumption arrays
    dates: list[dt.date]                   # column order of the consumption arrays
    consumption: np.ndarray                # (F, M, D) recorded daily consumption (float32)
    stockout: np.ndarray                   # (F, M, D) bool: facility was stocked out that day
    snapshots: list[dict]                  # canonical current stock (reference; API uses native+adapters)
    native_exports: dict[str, list[dict]]  # state -> records in the state's own export format
    facility_status: dict[str, dict]       # beds, staff, freshness per facility
    scenarios: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)


def _seasonal(state: str, group: str, doy: np.ndarray) -> np.ndarray:
    amp, peak = SEASONALITY[state][group]
    return 1.0 + amp * np.cos(2 * np.pi * (doy - peak) / 365.25)


def _hfr_id(rng: np.random.Generator, census_code: str) -> str:
    return f"IN{census_code}{rng.integers(10**7, 10**8)}"


def _build_facilities(rng: np.random.Generator) -> list[dict]:
    out: list[dict] = []
    for st_id, st in STATES.items():
        for d_code, d in st["districts"].items():
            lat0, lng0 = d["centre"]
            wh_id = f"DWH-{st_id}-{d_code}"
            out.append({
                "facility_id": wh_id, "hfr_id": _hfr_id(rng, st["census_code"]),
                "name": f"{d['name']} District Drug Warehouse", "type": "DWH",
                "state": st_id, "district": d_code, "district_name": d["name"], "block": d["blocks"][0],
                "lat": round(lat0, 5), "lng": round(lng0, 5), "warehouse_id": None,
                "lead_time_days": 0, "beds_total": 0, "staff_sanctioned": 8, "footfall_factor": 0.0,
            })
            blocks = d["blocks"]
            per_block = FACILITIES_PER_DISTRICT // len(blocks)
            seq = 0
            for b_i, block in enumerate(blocks):
                ang = 2 * math.pi * b_i / len(blocks) + rng.uniform(-0.2, 0.2)
                radius = rng.uniform(0.12, 0.26)
                b_lat, b_lng = lat0 + radius * math.sin(ang), lng0 + radius * math.cos(ang)
                phc_n = 0
                for j in range(per_block):
                    seq += 1
                    is_chc = j == 1 and b_i < 4
                    ftype = "CHC" if is_chc else "PHC"
                    if is_chc:
                        name = f"CHC {block}"
                    else:
                        name = f"PHC {block}{ROMAN[phc_n]}"
                        phc_n += 1
                    lead = int(rng.integers(10, 22)) if st_id == "OD" else int(rng.integers(7, 15))
                    out.append({
                        "facility_id": f"{ftype}-{st_id}-{d_code}-{seq:03d}",
                        "hfr_id": _hfr_id(rng, st["census_code"]),
                        "name": name, "type": ftype, "state": st_id, "district": d_code,
                        "district_name": d["name"], "block": block,
                        "lat": round(b_lat + rng.normal(0, 0.03), 5), "lng": round(b_lng + rng.normal(0, 0.03), 5),
                        "warehouse_id": wh_id, "lead_time_days": lead,
                        "beds_total": 30 if is_chc else 6,
                        "staff_sanctioned": 20 if is_chc else int(rng.integers(6, 10)),
                        "footfall_factor": round(float(rng.lognormal(0, 0.25)) * (2.5 if is_chc else 1.0), 3),
                    })
    return out


def _native_record(state: str, fac: dict, med: dict, snap: dict, adapter_cfg: dict | None) -> dict:
    """Render a canonical snapshot in the state's illustrative native export format."""
    ts: dt.datetime = snap["updated_at"]
    if state == "TN":
        return {
            "HFR_ID": fac["hfr_id"], "ITEM_CODE": TN_ITEM_CODES[med["drug_code"]], "ITEM_NAME": med["name"].upper(),
            "CLOSING_STOCK": snap["on_hand"], "IN_TRANSIT_QTY": snap["in_transit"],
            "NEAR_EXPIRY_QTY": snap["near_expiry_qty"], "REPORT_DT": ts.strftime("%d/%m/%Y %H:%M"),
        }
    if state == "UP":
        qty = snap["on_hand"]
        transit = snap["in_transit"]
        expiring = snap["near_expiry_qty"]
        if med["drug_code"] == "IVF-RL-500":  # UP reports IV fluid in litres (2 bottles = 1 L)
            qty, transit, expiring = qty / 2, transit / 2, expiring / 2
        return {
            "nin": fac["hfr_id"], "drugId": UP_DRUG_IDS[med["drug_code"]], "balanceQty": qty,
            "pipelineQty": transit, "expiringQty90d": expiring, "asOn": ts.isoformat(),
        }
    return {  # OD
        "inst_id": fac["hfr_id"], "med_cd": OD_MED_CODES[med["drug_code"]], "stock_in_hand": snap["on_hand"],
        "stock_in_transit": snap["in_transit"], "expiry_lt_90": snap["near_expiry_qty"],
        "rpt_date": ts.strftime("%Y-%m-%d"), "rpt_time": ts.strftime("%H:%M"),
    }


# Illustrative state drug codes (NOT real state catalogue codes).
TN_ITEM_CODES = {"PCM-500-TAB": "TN-D0101", "ORS-SACHET": "TN-D0412", "ZNC-20-TAB": "TN-D0415",
                 "AMX-500-CAP": "TN-D0220", "IVF-RL-500": "TN-D0810", "ACT-AL-TAB": "TN-D0633",
                 "MTF-500-TAB": "TN-D0901", "IFA-TAB": "TN-D0950"}
UP_DRUG_IDS = {"PCM-500-TAB": "UPD-17", "ORS-SACHET": "UPD-52", "ZNC-20-TAB": "UPD-53", "AMX-500-CAP": "UPD-08",
               "IVF-RL-500": "UPD-71", "ACT-AL-TAB": "UPD-66", "MTF-500-TAB": "UPD-90", "IFA-TAB": "UPD-31"}
OD_MED_CODES = {"PCM-500-TAB": "ODM/AN/001", "ORS-SACHET": "ODM/GI/004", "ZNC-20-TAB": "ODM/GI/005",
                "AMX-500-CAP": "ODM/AB/012", "IVF-RL-500": "ODM/IV/002", "ACT-AL-TAB": "ODM/AM/003",
                "MTF-500-TAB": "ODM/DM/001", "IFA-TAB": "ODM/NU/007"}


def generate(seed: int = DEFAULT_SEED, now: dt.datetime | None = None) -> SyntheticDataset:
    """Generate the full synthetic dataset. Deterministic for (seed, now)."""
    now = (now or dt.datetime.now(IST)).astimezone(IST).replace(second=0, microsecond=0)
    end = now.date()
    rng = np.random.default_rng(seed)
    facilities = _build_facilities(rng)
    disp = [f for f in facilities if f["type"] != "DWH"]
    F, M, D = len(disp), len(MEDICINES), HISTORY_DAYS
    dates = [end - dt.timedelta(days=D - 1 - i) for i in range(D)]
    doy = np.array([d.timetuple().tm_yday for d in dates], dtype=float)
    weekday = WEEKDAY_FACTOR[np.array([d.weekday() for d in dates])]
    trend = 1.0 + 0.03 * (np.arange(D) - (D - 1)) / 365.0  # +3%/year, 1.0 at the end

    fidx = {f["facility_id"]: i for i, f in enumerate(disp)}
    midx = {m["drug_code"]: j for j, m in enumerate(MEDICINES)}

    # Expected daily demand (F, M, D)
    expected = np.empty((F, M, D), dtype=np.float64)
    for i, f in enumerate(disp):
        for j, m in enumerate(MEDICINES):
            state_factor = STATE_DRUG_FACTOR.get(f["state"], {}).get(m["drug_code"], 1.0)
            base = f["footfall_factor"] * m["base_daily"] * state_factor
            expected[i, j] = base * _seasonal(f["state"], m["group"], doy)
    expected *= (weekday * trend)[None, None, :]

    mult = np.ones((F, M, D))
    events: list[dict] = []
    group_drugs = {g: [midx[m["drug_code"]] for m in MEDICINES if m["group"] == g] for g in
                   {m["group"] for m in MEDICINES}}
    key_group = {"TN": "diarrhoea", "UP": "fever", "OD": "malaria"}

    # Historical outbreaks: one per district per full year, near the key group's seasonal peak.
    for st_id, st in STATES.items():
        g = key_group[st_id]
        _, peak = SEASONALITY[st_id][g]
        for d_code, d in st["districts"].items():
            for year_back in (1, 2):
                centre_day = D - 1 - 365 * year_back + int(peak - doy[-1]) + int(rng.integers(-30, 30))
                start = max(0, min(D - 120, centre_day - 10))
                length = int(rng.integers(14, 29))
                peak_mult = float(rng.uniform(1.8, 2.8))
                block = d["blocks"][int(rng.integers(0, len(d["blocks"])))]
                shape = peak_mult - (peak_mult - 1) * np.abs(np.linspace(-1, 1, length))
                rows = [fidx[f["facility_id"]] for f in disp if f["district"] == d_code and f["block"] == block]
                for r in rows:
                    for c in group_drugs[g]:
                        mult[r, c, start:start + length] *= shape[: max(0, min(length, D - start))]
                events.append({"type": "historical_outbreak", "state": st_id, "district": d_code, "block": block,
                               "group": g, "start": dates[start].isoformat(), "days": length,
                               "peak_multiplier": round(peak_mult, 2)})

    # Live demo scenarios.
    for sc in SCENARIOS:
        start = D - sc["start_days_ago"]
        ramp = np.clip(np.linspace(1.0, sc["multiplier"], 4), 1, None)
        profile = np.concatenate([ramp, np.full(max(0, D - start - 4), sc["multiplier"])])[: D - start]
        for f in disp:
            if f["district"] == sc["district"] and f["block"] in sc["surge_blocks"]:
                for c in group_drugs[sc["group"]]:
                    mult[fidx[f["facility_id"]], c, start:] *= profile
        events.append({"type": "live_scenario", "scenario": sc["id"], "state": sc["state"],
                       "district": sc["district"], "blocks": sc["surge_blocks"], "group": sc["group"],
                       "start": dates[start].isoformat(), "multiplier": sc["multiplier"]})

    noise = rng.gamma(shape=10.0, scale=0.1, size=(F, M, D))
    lam = expected * mult * noise
    consumption = rng.poisson(lam).astype(np.float32)

    # Historical stock-out episodes (censored demand): recorded consumption 0, flagged.
    stockout = np.zeros((F, M, D), dtype=bool)
    n_eps = rng.poisson(1.2, size=(F, M))
    for i in range(F):
        for j in range(M):
            for _ in range(int(n_eps[i, j])):
                s = int(rng.integers(0, D - 60))
                stockout[i, j, s:s + int(rng.integers(3, 21))] = True

    # Current snapshot design (days of cover targets), then derive on-hand from recent demand.
    recent = consumption[:, :, -7:].mean(axis=2)  # pre-masking recent daily use
    cover = rng.uniform(22, 80, size=(F, M))
    in_transit_frac = np.where(rng.random((F, M)) < 0.15, rng.uniform(0.2, 0.5, size=(F, M)), 0.0)
    near_frac = np.where(rng.random((F, M)) < 0.15, rng.uniform(0.1, 0.3, size=(F, M)), 0.0)
    rand_out = rng.random((F, M)) < 0.03
    rand_low = rng.random((F, M)) < 0.08
    cover = np.where(rand_low, rng.uniform(8, 16, size=(F, M)), cover)
    overrides: dict[tuple[int, int], dict] = {}

    scenario_meta = []
    for sc in SCENARIOS:
        focus = [midx[c] for c in sc["focus_drugs"]]
        surge_rows = [f for f in disp if f["district"] == sc["district"] and f["block"] in sc["surge_blocks"]]
        donor_rows = [f for f in disp if f["district"] == sc["district"] and f["block"] in sc["donor_blocks"]]
        for f in surge_rows:
            for c in focus:
                cover[fidx[f["facility_id"]], c] = rng.uniform(2, 6)
                in_transit_frac[fidx[f["facility_id"]], c] = 0.0
        for k, f in enumerate(donor_rows):
            for c in focus:
                cover[fidx[f["facility_id"]], c] = rng.uniform(100, 140) if k % 2 == 0 else rng.uniform(70, 95)
                near_frac[fidx[f["facility_id"]], c] = 0.3 if k % 2 == 0 else 0.0
        hero = next(f for f in surge_rows if f["block"] == sc["hero_block"] and f["type"] == "PHC")
        h = fidx[hero["facility_id"]]
        if sc["id"] == "A":
            # PRD §12 example, *before* today's voice report (the demo voice report lowers ORS to 40).
            for code, cov in {"PCM-500-TAB": 44, "ORS-SACHET": 2.5, "ZNC-20-TAB": 11, "AMX-500-CAP": 9}.items():
                cover[h, midx[code]] = cov
        elif sc["id"] == "C":
            overrides[(h, midx["ACT-AL-TAB"])] = {"on_hand": 0, "stockout_days": 3}
        scenario_meta.append({**{k: v for k, v in sc.items()}, "hero_facility_id": hero["facility_id"],
                              "hero_facility_name": hero["name"]})

    snapshots: list[dict] = []
    for i, f in enumerate(disp):
        fresh_h = float(rng.exponential(10)) if rng.random() > 0.15 else float(rng.uniform(72, 240))
        if any(f["facility_id"] == s["hero_facility_id"] for s in scenario_meta):
            fresh_h = 30.0
        reported = now - dt.timedelta(hours=fresh_h)
        for j, m in enumerate(MEDICINES):
            ov = overrides.get((i, j))
            if ov is None and rand_out[i, j] and not any(
                f["facility_id"] == s["hero_facility_id"] for s in scenario_meta
            ):
                ov = {"on_hand": 0, "stockout_days": int(rng.integers(1, 5))}
            if ov is not None:
                on_hand = ov["on_hand"]
                stockout[i, j, D - ov["stockout_days"]:] = True
            else:
                on_hand = int(round(max(recent[i, j], 0.2) * cover[i, j]))
            in_transit = int(round(on_hand * in_transit_frac[i, j])) if on_hand else 0
            near = int(round(on_hand * near_frac[i, j]))
            snapshots.append({
                "facility_id": f["facility_id"], "drug_code": m["drug_code"], "on_hand": on_hand,
                "in_transit": in_transit, "near_expiry_qty": near,
                "near_expiry_date": (end + dt.timedelta(days=int(rng.integers(30, 90)))).isoformat() if near else None,
                "updated_at": reported, "source": "adapter",
            })
    consumption[stockout] = 0.0

    status: dict[str, dict] = {}
    for f in facilities:
        if f["type"] == "DWH":
            continue
        present = int(rng.binomial(f["staff_sanctioned"], 0.78))
        occupied = int(rng.binomial(f["beds_total"], 0.55))
        if any(f["facility_id"] == s["hero_facility_id"] for s in scenario_meta):
            present, occupied = min(4, f["staff_sanctioned"]), 5
        snap_ts = next(s["updated_at"] for s in snapshots if s["facility_id"] == f["facility_id"])
        status[f["facility_id"]] = {
            "beds_total": f["beds_total"], "beds_occupied": occupied,
            "beds_updated_at": now - dt.timedelta(hours=float(rng.uniform(1, 20))),
            "staff_sanctioned": f["staff_sanctioned"], "staff_present": present,
            "attendance_updated_at": now.replace(hour=9, minute=int(rng.integers(0, 59))) if now.hour >= 10
            else now - dt.timedelta(hours=float(rng.uniform(1, 3))),
            "opd_today": int(rng.poisson(110 * f["footfall_factor"])),
            "last_stock_report_at": snap_ts, "last_stock_report_source": "adapter",
        }

    meds_by_code = {m["drug_code"]: m for m in MEDICINES}
    fac_by_id = {f["facility_id"]: f for f in facilities}
    native: dict[str, list[dict]] = {s: [] for s in STATES}
    for s in snapshots:
        f = fac_by_id[s["facility_id"]]
        native[f["state"]].append(_native_record(f["state"], f, meds_by_code[s["drug_code"]], s, None))

    metadata = {
        "source": SOURCE, "dataset_version": DATASET_VERSION, "generator_version": GENERATOR_VERSION,
        "seed": seed, "reference_timestamp": now.isoformat(), "history_start": dates[0].isoformat(),
        "history_end": dates[-1].isoformat(), "history_days": D,
        "geographic_scope": {s: [d["name"] for d in st["districts"].values()] for s, st in STATES.items()},
        "facility_count": len(facilities), "dispensing_facility_count": F, "medicine_count": M,
        "is_synthetic": True, "is_sample": True,
        "notice": "SYNTHETIC DATA: generated for demonstration; not real facility, stock or patient data.",
    }
    public_meds = [{k: v for k, v in m.items() if k not in ("base_daily", "strength_number")} | {
        "strength_number": m["strength_number"]} for m in MEDICINES]
    return SyntheticDataset(
        metadata=metadata, medicines=public_meds, facilities=facilities,
        dispensing_ids=[f["facility_id"] for f in disp], dates=dates, consumption=consumption,
        stockout=stockout, snapshots=snapshots, native_exports=native, facility_status=status,
        scenarios=scenario_meta, events=events,
    )


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def _json_default(o):
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    raise TypeError(type(o))


def write(ds: SyntheticDataset, out: Path, sample: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    manifest = {**ds.metadata, "events": ds.events, "scenarios": ds.scenarios,
                "files": {}, "sample_only": sample}
    (out / "medicines.json").write_text(json.dumps({"metadata": ds.metadata, "medicines": ds.medicines},
                                                    ensure_ascii=False, indent=1))
    (out / "facilities.json").write_text(json.dumps({"metadata": ds.metadata, "facilities": ds.facilities},
                                                     ensure_ascii=False, indent=1))
    exports = out / "state_exports"
    exports.mkdir(exist_ok=True)
    for st, rows in ds.native_exports.items():
        (exports / f"{st.lower()}_stock_export.json").write_text(
            json.dumps({"metadata": ds.metadata, "state": st, "records": rows}, ensure_ascii=False, indent=1))
    codes = [m["drug_code"] for m in ds.medicines]
    rows_idx = range(len(ds.dispensing_ids))
    day_idx = range(len(ds.dates))
    if sample:  # small committed sample: Scenario A hero PHC, last 365 days
        hero = ds.scenarios[0]["hero_facility_id"]
        rows_idx = [ds.dispensing_ids.index(hero)]
        day_idx = range(len(ds.dates) - 365, len(ds.dates))
        name = "daily_consumption_sample.csv"
        opener = open
    else:
        name = "daily_consumption.csv.gz"
        opener = gzip.open  # type: ignore[assignment]
    with opener(out / name, "wt", newline="") as fh:  # type: ignore[operator]
        w = csv.writer(fh)
        w.writerow(["facility_id", "drug_code", "date", "consumption", "stocked_out", "source", "is_synthetic",
                    "dataset_version"])
        for i in rows_idx:
            for j, code in enumerate(codes):
                for k in day_idx:
                    d = ds.dates[k]
                    w.writerow([ds.dispensing_ids[i], code, d.isoformat(), int(ds.consumption[i, j, k]),
                                int(ds.stockout[i, j, k]), "synthetic", 1, ds.metadata["dataset_version"]])
    manifest["files"] = ["medicines.json", "facilities.json", "state_exports/", name]
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=_json_default))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path("data/generated"))
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--now", type=str, default=None, help="reference timestamp (ISO, IST); default: now")
    p.add_argument("--sample", action="store_true", help="write the small committed sample only")
    a = p.parse_args()
    now = dt.datetime.fromisoformat(a.now).replace(tzinfo=IST) if a.now else None
    ds = generate(a.seed, now)
    write(ds, a.out, a.sample)
    print(f"wrote {a.out} ({ds.metadata['facility_count']} facilities, {ds.metadata['history_days']} days)")


if __name__ == "__main__":
    main()
