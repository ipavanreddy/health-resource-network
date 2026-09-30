"""Unit tests: days of cover, readiness, forecast, risk, optimiser, parser, adapters."""
import numpy as np
import pytest

from app.capture.parser import parse_stock_text
from app.early_warning.risk import is_surge, stockout_risk, surge_ratios
from app.forecasting import baseline as fc
from app.interop.adapters import AdapterError, to_canonical
from app.redistribution.optimizer import Params, optimize
from app.visibility.cover import days_of_cover, recent_daily_demand, stock_status
from app.visibility.readiness import readiness

MEDS = [
    {"drug_code": "PCM-500-TAB", "name": "Paracetamol", "unit": "tablet", "strength_number": 500,
     "local_names": ["para", "பாராசிட்டமால்", "पैरासिटामोल"]},
    {"drug_code": "ORS-SACHET", "name": "Oral Rehydration Salts", "unit": "sachet", "strength_number": None,
     "local_names": ["ors", "ஓஆர்எஸ்", "ओआरएस"]},
    {"drug_code": "AMX-500-CAP", "name": "Amoxicillin", "unit": "capsule", "strength_number": 500,
     "local_names": ["amoxicillin", "அமாக்ஸிசிலின்"]},
]


# ---------------------------------------------------------------- days of cover
def test_days_of_cover_basic():
    assert days_of_cover(40, 0, 13.3) == pytest.approx(3.0, abs=0.1)
    assert days_of_cover(100, 50, 10) == 15.0
    assert days_of_cover(100, 0, 0) is None


def test_stock_status_thresholds():
    assert stock_status(0, 0) == "stocked_out"
    assert stock_status(40, 3) == "critical"
    assert stock_status(100, 11) == "low"
    assert stock_status(1000, 42) == "adequate"
    assert stock_status(5, None) == "adequate"


def test_recent_demand_excludes_stockout_days():
    c = np.array([10.0] * 21 + [0, 0, 0, 0, 12, 12, 12])
    s = np.array([False] * 21 + [True] * 4 + [False] * 3)
    assert recent_daily_demand(c, s) == pytest.approx(12.0)


# ---------------------------------------------------------------- readiness
def _rows(*covers):
    return [{"is_tracer": True, "days_of_cover": c, "status": stock_status(0 if c == 0 else 1, c)} for c in covers]


def test_readiness_perfect_and_weights():
    r = readiness(_rows(60, 45), 6, 2, 6, 6, 2, 0)
    assert r["score"] == 100 and r["band"] == "Good"
    assert [c["weight"] for c in r["components"]] == [40, 20, 20, 10, 10]


def test_readiness_breakdown_matches_formula():
    # stock (0 + 0.1 + 1)/3 -> 36.7; beds 1 of 6 free -> 1/1.5 -> 66.7; staff 4/6 -> 66.7;
    # freshness 30 h -> 60; one surge group -> 50
    r = readiness(_rows(0, 3, 42), 6, 5, 4, 6, 30, 1)
    expected = 0.4 * 36.67 + 0.2 * 66.67 + 0.2 * 66.67 + 0.1 * 60 + 0.1 * 50
    assert r["score"] == round(expected)
    assert r["band"] == "Moderate"


def test_readiness_custom_weights():
    r = readiness(_rows(0), 6, 0, 6, 6, 1, 0, {"stock_cover": 100, "beds": 0, "staff": 0, "freshness": 0,
                                                "surge_stability": 0})
    assert r["score"] == 0 and r["band"] == "Poor"


# ---------------------------------------------------------------- forecast & risk
def test_forecast_recovers_flat_series_and_ranges():
    weeks = 156
    adj = np.full((1, 1, weeks), 70.0)
    valid = np.ones_like(adj, dtype=bool)
    f = fc.forecast_at(adj, valid, weeks - 1, 4)
    assert np.allclose(f, 70.0)
    lo, hi = fc.ranges(f, np.array([[0.2]]))
    assert (lo < f).all() and (hi > f).all()


def test_forecast_skips_censored_weeks():
    adj = np.full((1, 1, 156), 70.0)
    valid = np.ones_like(adj, dtype=bool)
    adj[..., -2:] = 0.0          # stocked out -> recorded 0
    valid[..., -2:] = False
    assert fc.forecast_at(adj, valid, 155, 1)[0, 0, 0] == pytest.approx(70.0)


def test_backtest_model_beats_naive_on_seasonal_series():
    rng = np.random.default_rng(1)
    t = np.arange(156)
    base = 100 * (1 + 0.5 * np.cos(2 * np.pi * t / 52))
    adj = rng.poisson(np.tile(base, (20, 1, 1))).astype(float)
    bt = fc.backtest(adj, np.ones_like(adj, dtype=bool))
    assert fc.wape(bt["abs_err"]["model"], bt["actual"]) < fc.wape(bt["abs_err"]["same_week_last_year"], bt["actual"])


def test_stockout_risk_monotonic():
    wk = [70.0] * 8
    low = stockout_risk(1000, wk, 0.2, 14)
    mid = stockout_risk(140, wk, 0.2, 14)
    high = stockout_risk(20, wk, 0.2, 14)
    assert low < 0.05 and 0.3 < mid < 0.7 and high > 0.95


def test_surge_detection():
    daily = np.concatenate([np.full(60, 10.0), np.full(7, 32.0)])[None, :]
    ratio, last7 = surge_ratios(daily, np.zeros_like(daily, dtype=bool))
    assert ratio[0] == pytest.approx(3.2)
    assert is_surge(float(ratio[0]), float(last7[0]))
    assert not is_surge(1.2, 100)


# ---------------------------------------------------------------- optimiser
def _fac(fid, lat, on_hand, demand, near=0, district="MDU", risk=0.0):
    return {"facility_id": fid, "drug_code": "ORS-SACHET", "district": district, "lat": lat, "lng": 78.1,
            "on_hand": on_hand, "in_transit": 0, "daily_demand": demand,
            "days_of_cover": days_of_cover(on_hand, 0, demand), "stockout_risk": risk, "near_expiry_qty": near,
            "is_tracer": True}


def test_optimizer_moves_surplus_and_respects_safety_stock():
    rows = [_fac("R1", 9.90, 40, 50, risk=0.99), _fac("D1", 9.95, 3000, 20, near=600), _fac("D2", 9.70, 900, 10)]
    out = optimize(rows, Params())
    assert out["transfers"], out
    for t in out["transfers"]:
        assert t["to_facility_id"] == "R1"
        donor = next(r for r in rows if r["facility_id"] == t["from_facility_id"])
        assert donor["on_hand"] - t["quantity"] >= Params().donor_safety_days * donor["daily_demand"]
    total = sum(t["quantity"] for t in out["transfers"])
    assert total == 30 * 50 - 40          # receiver filled to 30 days of cover
    assert out["transfers"][0]["from_facility_id"] == "D1"  # nearer + near-expiry donor first


def test_optimizer_respects_travel_limit_and_district_policy():
    rows = [_fac("R1", 9.90, 0, 50, risk=1.0), _fac("FAR", 12.0, 5000, 10), _fac("OTHER", 9.91, 5000, 10, district="X")]
    assert optimize(rows, Params())["transfers"] == []
    out = optimize(rows, Params(allow_cross_district=True))
    assert [t["from_facility_id"] for t in out["transfers"]] == ["OTHER"]
    assert out["transfers"][0]["cross_district"] is True


def test_optimizer_prioritises_most_urgent_receiver_when_short():
    rows = [_fac("URGENT", 9.90, 10, 50, risk=1.0), _fac("LESS", 9.905, 500, 50, risk=0.6),
            _fac("D1", 9.95, 1100, 10)]  # surplus 650 only
    out = optimize(rows, Params())
    got = {t["to_facility_id"]: t["quantity"] for t in out["transfers"]}
    assert got.get("URGENT", 0) >= 600


# ---------------------------------------------------------------- parser (demo extraction)
def test_parser_english_prd_example():
    r = parse_stock_text("Paracetamol 500, 1,200 tablets left. ORS 40 packets. Amoxicillin finished.", MEDS)
    got = {i.drug_code: i.quantity for i in r.items}
    assert got == {"PCM-500-TAB": 1200, "ORS-SACHET": 40, "AMX-500-CAP": 0}
    assert r.requires_confirmation


def test_parser_tamil_and_hindi():
    ta = parse_stock_text("பாராசிட்டமால் 500, 1200 மாத்திரைகள் உள்ளன. ஓஆர்எஸ் 40 பாக்கெட். அமாக்ஸிசிலின் தீர்ந்துவிட்டது.", MEDS)
    assert {i.drug_code: i.quantity for i in ta.items} == {"PCM-500-TAB": 1200, "ORS-SACHET": 40, "AMX-500-CAP": 0}
    hi = parse_stock_text("पैरासिटामोल 500, 900 गोलियां बची हैं। ओआरएस 150 पैकेट।", MEDS)
    assert {i.drug_code: i.quantity for i in hi.items} == {"PCM-500-TAB": 900, "ORS-SACHET": 150}


def test_parser_never_invents_quantities_and_flags_unknown():
    r = parse_stock_text("ORS some left. Cetirizine 50 tablets.", MEDS)
    ors = next(i for i in r.items if i.drug_code == "ORS-SACHET")
    assert ors.quantity is None
    assert any("Cetirizine" in u for u in r.unrecognised)


# ---------------------------------------------------------------- adapters
def test_adapters_map_three_state_formats_to_same_canonical():
    idx = {"IN331": "PHC-TN-X", "IN091": "PHC-UP-X", "IN211": "PHC-OD-X"}
    tn = to_canonical("TN", {"HFR_ID": "IN331", "ITEM_CODE": "TN-D0412", "CLOSING_STOCK": 40, "IN_TRANSIT_QTY": 0,
                             "NEAR_EXPIRY_QTY": 5, "REPORT_DT": "29/09/2026 10:30"}, idx)
    up = to_canonical("UP", {"nin": "IN091", "drugId": "UPD-71", "balanceQty": 6, "pipelineQty": 1.5,
                             "expiringQty90d": 0, "asOn": "2026-09-29T10:30:00+05:30"}, idx)
    od = to_canonical("OD", {"inst_id": "IN211", "med_cd": "ODM/AM/003", "stock_in_hand": 0, "stock_in_transit": 0,
                             "expiry_lt_90": 0, "rpt_date": "2026-09-29", "rpt_time": "10:30"}, idx)
    assert set(tn) == set(up) == set(od)
    assert (tn["drug_code"], tn["on_hand"], tn["facility_id"]) == ("ORS-SACHET", 40, "PHC-TN-X")
    assert (up["drug_code"], up["on_hand"], up["in_transit"]) == ("IVF-RL-500", 12, 3)  # litres -> 500 ml bottles
    assert od["drug_code"] == "ACT-AL-TAB" and od["updated_at"].utcoffset().total_seconds() == 5.5 * 3600
    assert tn["updated_at"] == up["updated_at"] == od["updated_at"]


def test_adapter_rejects_unknown_codes():
    with pytest.raises(AdapterError):
        rec = {"HFR_ID": "IN331", "ITEM_CODE": "NOPE", "CLOSING_STOCK": 1, "REPORT_DT": "29/09/2026 10:30"}
        to_canonical("TN", rec, {"IN331": "F"})
    with pytest.raises(AdapterError):
        to_canonical("ZZ", {}, {})
