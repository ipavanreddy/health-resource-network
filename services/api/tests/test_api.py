"""API endpoint tests (demo mode) and one end-to-end journey (PRD §8 / §44)."""
from tests.conftest import DHO

HERO = "PHC-TN-MDU-001"  # PHC Melur, Madurai (Scenario A)


def test_health_reports_demo_mode(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["demo_mode"] is True
    assert body["integrations"]["gemini"] == "demo"


def test_system_modes_lists_every_integration(client):
    body = client.get("/api/system/modes").json()
    ids = {m["id"] for m in body["integrations"]}
    assert ids == {"gemini", "speech", "routes", "bigquery", "forecast", "storage", "firestore"}
    assert body["synthetic_data"] is True and body["data_label"]["is_synthetic"] is True
    assert all(m["mode"] == "demo" for m in body["integrations"])  # tests force demo mode


def test_configured_but_failing_integration_is_reported_as_demo(monkeypatch):
    """The badge must never claim "live" for a key that does not work."""
    from app.config import settings
    from app.integrations import modes

    monkeypatch.setattr(settings, "force_demo_mode", False)
    monkeypatch.setattr(settings, "maps_api_key", "bad-key")
    monkeypatch.setattr(settings, "gcs_bucket", "some-bucket")
    monkeypatch.setattr(settings, "google_cloud_api_key", "")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "google_genai_use_vertexai", False)
    monkeypatch.setattr(settings, "google_cloud_project", "")
    monkeypatch.setattr(settings, "firebase_project_id", "")

    def boom():
        raise RuntimeError("API key not valid")

    monkeypatch.setitem(modes.PROBES, "routes", boom)
    monkeypatch.setitem(modes.PROBES, "storage", lambda: "ok")
    monkeypatch.setattr(modes, "_status", {})
    modes.run_probes()
    by_id = {m["id"]: m for m in modes.all_modes()}
    assert by_id["routes"]["mode"] == "demo" and by_id["routes"]["verified"] is False
    assert "API key not valid" in by_id["routes"]["detail"]
    assert not modes.routes_enabled()
    assert by_id["storage"]["mode"] == "real" and by_id["storage"]["verified"] is True
    assert by_id["speech"]["mode"] == "demo" and by_id["speech"]["detail"] == "not configured"


def test_facilities_scope_and_labels(client):
    all_f = client.get("/api/facilities").json()["facilities"]
    assert 190 <= len(all_f) <= 210
    assert {f["state"] for f in all_f} == {"TN", "UP", "OD"}
    mdu = client.get("/api/facilities?state=TN&district=MDU&include_warehouses=false").json()["facilities"]
    assert mdu and all(f["district"] == "MDU" and f["is_synthetic"] for f in mdu)
    assert client.get("/api/facilities/NOPE").status_code == 404


def test_stock_readiness_forecast_canonical(client):
    stock = client.get(f"/api/facilities/{HERO}/stock").json()
    ors = next(r for r in stock["stock"] if r["drug_code"] == "ORS-SACHET")
    assert ors["status"] == "critical" and ors["surge"] is True and ors["stockout_risk"] > 0.8
    rd = client.get(f"/api/facilities/{HERO}/readiness").json()
    assert 0 <= rd["score"] <= 100 and len(rd["components"]) == 5
    fc = client.get(f"/api/facilities/{HERO}/forecast?drug_code=ORS-SACHET").json()["forecasts"][0]
    assert len(fc["weeks"]) == 8
    assert all(w["demand_low"] <= w["demand_expected"] <= w["demand_high"] for w in fc["weeks"])
    can = client.get(f"/api/facilities/{HERO}/canonical").json()
    assert can["schema_version"] == "canonical-v1" and can["risk"]["surge_flag"] is True
    assert can["data_label"]["is_synthetic"] is True


def test_beds_and_attendance_geofence(client):
    fac = client.get(f"/api/facilities/{HERO}").json()
    assert client.post(f"/api/facilities/{HERO}/beds", json={"occupied": 3}).json()["beds"]["occupied"] == 3
    assert client.post(f"/api/facilities/{HERO}/beds", json={"occupied": 99}).status_code == 400
    ok = client.post(f"/api/facilities/{HERO}/attendance", json={"lat": fac["lat"], "lng": fac["lng"], "token": "a"})
    assert ok.json()["accepted"] is True
    far = client.post(f"/api/facilities/{HERO}/attendance", json={"lat": fac["lat"] + 0.1, "lng": fac["lng"]})
    assert far.json()["accepted"] is False


def test_capture_text_and_photo_and_form(client):
    t = client.post("/api/capture/text",
                    json={"facility_id": HERO, "text": "ORS 40 packets, zinc 200", "language": "en"})
    body = t.json()
    assert body["status"] == "pending_confirmation" and body["provenance"]["is_demo"] is True
    assert {i["drug_code"] for i in body["items"]} == {"ORS-SACHET", "ZNC-20-TAB"}
    for k in ("model_name", "model_version", "prompt_version"):
        assert body["provenance"][k]
    p = client.post("/api/capture/photo", data={"facility_id": HERO, "language": "hi"}).json()
    assert p["rows"] and "Tab. Cetriz" in p["unrecognised"]
    assert any(r["closing"] is None and "closing" in r["illegible_cells"] for r in p["rows"])
    f = client.post("/api/capture/form",
                    json={"facility_id": HERO, "items": [{"drug_code": "IFA-TAB", "quantity": 500}]})
    assert f.json()["items"][0]["quantity"] == 500


def test_confirm_rejects_double_confirmation(client):
    items = [{"drug_code": "IFA-TAB", "quantity": 5}]
    cap = client.post("/api/capture/form", json={"facility_id": HERO, "items": items}).json()
    assert client.post(f"/api/capture/{cap['capture_id']}/confirm", json={"items": items}).status_code == 200
    assert client.post(f"/api/capture/{cap['capture_id']}/confirm", json={"items": items}).status_code == 400


def test_alerts_surge_requires_dho_review(client):
    alerts = client.get("/api/alerts?state=TN&district=MDU").json()["alerts"]
    surge = next(a for a in alerts if a["type"] == "surge")
    assert surge["status"] == "pending_review" and "not a confirmed outbreak" in surge["summary"]
    assert surge["context"]["group"] == "diarrhoea"
    fid = surge["facility_ids"][0]
    assert not any(a["type"] == "surge" for a in client.get(f"/api/alerts?facility_id={fid}").json()["alerts"])
    assert client.post(f"/api/alerts/{surge['alert_id']}/review", json={"action": "verify"}).status_code == 403
    r = client.post(f"/api/alerts/{surge['alert_id']}/review", json={"action": "verify"}, headers=DHO)
    assert r.json()["status"] == "verified"
    assert any(a["type"] == "surge" for a in client.get(f"/api/alerts?facility_id={fid}&language=ta").json()["alerts"])


def test_states_models_and_ingest(client):
    states = client.get("/api/states").json()["states"]
    assert {s["id"] for s in states} == {"TN", "UP", "OD"}
    assert len({s["adapter"]["adapter_id"] for s in states}) == 3
    ex = client.get("/api/states/UP/sample-export").json()["records"]
    assert all(set(r["canonical"]) >= {"facility_id", "drug_code", "on_hand"} for r in ex)
    card = client.get("/api/models/phc-demand-baseline/card").json()
    assert {s["state"] for s in card["evaluation"]["per_state"]} == {"TN", "UP", "OD"}
    native = ex[0]["native"]
    res = client.post("/api/states/UP/ingest", json={"records": [native, {"nin": "bad"}], "dry_run": True}).json()
    assert res["accepted"] == 1 and res["rejected"] == 1
    an = client.get("/api/states/TN/analytics").json()
    assert {d["id"] for d in an["districts"]} == {"MDU", "TNJ"}


def test_language_endpoints_demo(client):
    assert client.post("/api/text-to-speech", json={"text": "hello", "language": "ta"}).json()["mode"] == "demo"
    assert client.post("/api/translate", json={"text": "hello", "target": "hi"}).json()["text"] == "hello"
    stt = client.post("/api/speech-to-text", data={"language": "hi"}).json()
    assert stt["is_demo"] is True and stt["transcript"]


def test_transfer_role_and_state_machine(client):
    opt = client.post("/api/redistribution/optimize", json={"state": "OD", "district": "KPT"}).json()
    t = opt["transfers"][0]
    tid = t["transfer_id"]
    assert client.post(f"/api/transfers/{tid}/dispatch", json={}).status_code == 400  # not approved yet
    assert client.post(f"/api/transfers/{tid}/approve", json={}).status_code == 403    # PHC staff cannot approve
    assert client.post(f"/api/transfers/{tid}/reject", json={}, headers=DHO).json()["status"] == "rejected"


def test_end_to_end_demo_journey(client):
    """Voice report → extraction → confirm → days of cover → forecast/risk → optimise → explain → approve →
    notify → dispatch → receive, entirely in demo mode."""
    # 1. Tamil voice stock report (no audio → labelled demo transcript), extraction for confirmation
    cap = client.post("/api/capture/voice", data={"facility_id": HERO, "language": "ta"}).json()
    assert cap["transcript"]["is_demo"] is True
    got = {i["drug_code"]: i["quantity"] for i in cap["items"]}
    assert got == {"PCM-500-TAB": 1200, "ORS-SACHET": 40, "AMX-500-CAP": 0}
    assert "உறுதிசெய்" in cap["confirmation_text"]  # confirmation in Tamil

    # 2. Staff confirm → ledger updated
    conf = client.post(f"/api/capture/{cap['capture_id']}/confirm",
                       json={"items": [{"drug_code": k, "quantity": v} for k, v in got.items()]}).json()
    status = {r["drug_code"]: r["status"] for r in conf["stock"]}
    assert status["ORS-SACHET"] == "critical" and status["AMX-500-CAP"] == "stocked_out"

    # 3. Days of cover + readiness + forecast/risk
    stock = {r["drug_code"]: r for r in client.get(f"/api/facilities/{HERO}/stock").json()["stock"]}
    assert stock["ORS-SACHET"]["on_hand"] == 40 and stock["ORS-SACHET"]["days_of_cover"] < 3
    assert stock["ORS-SACHET"]["stockout_risk"] > 0.8
    assert client.get(f"/api/facilities/{HERO}/forecast").json()["forecasts"]

    # 4. Optimiser recommendation with explanation (ORS in Madurai)
    opt = client.post("/api/redistribution/optimize",
                      json={"state": "TN", "district": "MDU", "drug_code": "ORS-SACHET"}).json()
    to_hero = [t for t in opt["transfers"] if t["to_facility_id"] == HERO]
    assert to_hero, "hero PHC should receive ORS"
    t = to_hero[0]
    assert t["status"] == "proposed" and t["requires_human_approval"] is True
    assert t["explanation"]["summary"] and t["explanation"]["requires_human_review"] is True
    assert t["explanation"]["travel_minutes"] == t["travel_minutes"]  # Gemini/template never changes numbers
    assert t["optimiser"]["donor_cover_after"] >= t["optimiser"]["donor_safety_days"]
    for k in ("model_name", "model_version", "prompt_version"):
        assert t[k]

    # 5. DHO approves → both facilities notified
    tid = t["transfer_id"]
    appr = client.post(f"/api/transfers/{tid}/approve", json={"by": "DHO Madurai"}, headers=DHO).json()
    assert appr["status"] == "approved"
    for fid in (t["from_facility_id"], HERO):
        notes = client.get(f"/api/facilities/{fid}/notifications").json()["notifications"]
        assert any(n["transfer_id"] == tid and n["type"] == "transfer_approved" and n["texts"]["ta"] for n in notes)

    # 6. Dispatch and receipt confirmed → stock updated
    donor_before = client.get(f"/api/facilities/{t['from_facility_id']}/stock").json()["stock"]
    donor_before = next(r for r in donor_before if r["drug_code"] == "ORS-SACHET")["on_hand"]
    assert client.post(f"/api/transfers/{tid}/dispatch", json={}).json()["status"] == "dispatched"
    assert client.post(f"/api/transfers/{tid}/receive", json={}).json()["status"] == "received"
    after = {r["drug_code"]: r for r in client.get(f"/api/facilities/{HERO}/stock").json()["stock"]}
    assert after["ORS-SACHET"]["on_hand"] == 40 + t["quantity"]
    donor_after = next(r for r in client.get(f"/api/facilities/{t['from_facility_id']}/stock").json()["stock"]
                       if r["drug_code"] == "ORS-SACHET")["on_hand"]
    assert donor_after == donor_before - t["quantity"]
    hist = [h["status"] for h in client.get(f"/api/transfers?facility_id={HERO}").json()["transfers"][0]["history"]]
    assert hist == ["proposed", "approved", "dispatched", "received"]


def test_emergency_scenario_projects_more_stockouts(client):
    """FR-11: a demand multiplier on a region + medicine group shows projected stock-outs by week."""
    body = {"state": "UP", "district": "GKP", "group": "fever", "multiplier": 3, "duration_weeks": 4}
    res = client.post("/api/scenarios/simulate", json=body)
    assert res.status_code == 200
    d = res.json()
    assert d["drug_codes"] == ["PCM-500-TAB", "IVF-RL-500"]
    assert len(d["weeks"]) == d["horizon_weeks"] == 8
    for w in d["weeks"]:
        assert w["scenario_stocked_out"] >= w["baseline_stocked_out"]
    assert d["weeks"][-1]["scenario_stocked_out"] > d["weeks"][-1]["baseline_stocked_out"]
    assert 0 <= d["redistribution"]["coverable_share"] <= 1
    assert d["data_label"]["is_synthetic"] is True
    assert client.post("/api/scenarios/simulate", json={**body, "group": "nope"}).status_code == 400
