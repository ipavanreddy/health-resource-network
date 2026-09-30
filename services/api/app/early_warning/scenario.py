"""Emergency scenario view (PRD §15.3, FR-11): apply a demand multiplier to a region and medicine group and
project stock-outs by week, plus how much of the shortfall surplus stock in the same scope could cover.

A what-if only: nothing is written and no alert or transfer is created (those still need human approval).
"""
from app.store import HORIZON_WEEKS, Store

SAFETY_WEEKS = 45 / 7  # same donor safety stock as the optimiser (45 days)


def _stockout_week(avail: float, demand: list[float]) -> int | None:
    """First week index (0-based) in which cumulative demand exceeds what is available, else None."""
    cum = 0.0
    for h, d in enumerate(demand):
        cum += d
        if cum > avail:
            return h
    return None


def simulate(store: Store, state: str, district: str | None, drug_codes: list[str], multiplier: float,
             duration_weeks: int, blocks: list[str] | None = None) -> dict:
    facilities = [f for f in store.dispensing(state, district) if not blocks or f["block"] in blocks]
    h_n = HORIZON_WEEKS
    weeks = [{"week": h + 1, "week_start": store.week_start(h + 1).isoformat(), "baseline_stocked_out": 0,
              "scenario_stocked_out": 0, "scenario_shortfall_units": 0.0} for h in range(h_n)]
    rows, shortfall_total, surplus_total = [], 0.0, 0.0
    for code in drug_codes:
        j = store.midx[code]
        med = store.medicines[code]
        for f in facilities:
            i = store.fidx[f["facility_id"]]
            s = store.stock[(f["facility_id"], code)]
            avail = float(s["on_hand"] + s["in_transit"])
            base = [float(store.fc_expected[i, j, h]) for h in range(h_n)]
            scen = [d * (multiplier if h < duration_weeks else 1.0) for h, d in enumerate(base)]
            wb, ws = _stockout_week(avail, base), _stockout_week(avail, scen)
            cum = 0.0
            for h in range(h_n):
                cum += scen[h]
                if wb is not None and h >= wb:
                    weeks[h]["baseline_stocked_out"] += 1
                if ws is not None and h >= ws:
                    weeks[h]["scenario_stocked_out"] += 1
                    weeks[h]["scenario_shortfall_units"] += max(0.0, cum - avail) - max(0.0, cum - scen[h] - avail)
            short = max(0.0, sum(scen) - avail)
            # Surplus = stock beyond the horizon's scenario demand plus the optimiser's safety stock.
            surplus = max(0.0, avail - sum(scen) - SAFETY_WEEKS * (sum(base) / h_n))
            shortfall_total += short
            surplus_total += surplus
            if ws is not None:
                rows.append({"facility_id": f["facility_id"], "name": f["name"], "block": f["block"],
                             "drug_code": code, "medicine": f"{med['name']} {med['strength']}", "unit": med["unit"],
                             "available": int(avail), "baseline_stockout_week": None if wb is None else wb + 1,
                             "scenario_stockout_week": ws + 1, "shortfall_units": round(short)})
    for w in weeks:
        w["scenario_shortfall_units"] = round(w["scenario_shortfall_units"])
    rows.sort(key=lambda r: (r["scenario_stockout_week"], -r["shortfall_units"]))
    coverable = min(shortfall_total, surplus_total)
    return {
        "scope": {"state": state, "district": district, "blocks": blocks or [], "facilities": len(facilities)},
        "drug_codes": drug_codes, "multiplier": multiplier, "duration_weeks": duration_weeks,
        "horizon_weeks": h_n, "weeks": weeks, "facilities_at_risk": rows[:50],
        "facilities_at_risk_total": len(rows),
        "redistribution": {
            "shortfall_units": round(shortfall_total), "surplus_units_in_scope": round(surplus_total),
            "coverable_units": round(coverable),
            "coverable_share": round(coverable / shortfall_total, 3) if shortfall_total else 1.0,
            "note": "Surplus above each donor's 45-day safety stock after its own scenario demand. Run the optimiser "
                    "to turn this into concrete transfers (each needs DHO approval).",
        },
        "method": "Local shared forecast x multiplier for the first duration_weeks; stock-out = first week "
                  "cumulative demand exceeds on hand + in transit. What-if only: nothing is saved.",
        "data_label": store.data_label(),
    }
