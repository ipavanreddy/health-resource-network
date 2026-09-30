"""In-memory demo store (system of record in demo mode), seeded from the synthetic generator.

Data flow at start-up (PRD §30): synthetic generator → state-native exports → state adapters →
canonical snapshots → derived features (weekly demand, forecast, risk, surge) → views.
Mutations (confirmed stock reports, beds, attendance, transfers) are applied in memory and mirrored to
BigQuery / Firestore when those integrations are configured.
"""
import hashlib
import importlib.util
import sys
import threading
import uuid
from datetime import date, datetime, timedelta, timezone

import numpy as np

from app.config import REPO_ROOT, settings
from app.early_warning import risk as ew
from app.forecasting import baseline as fc
from app.integrations import cloud_sinks
from app.integrations.modes import forecast_bigquery_enabled
from app.interop.adapters import load_state_files, to_canonical
from app.localization import messages as msg
from app.visibility import cover as cv
from app.visibility import readiness as rd

IST = timezone(timedelta(hours=5, minutes=30))
HORIZON_WEEKS = 8
GEOFENCE_METERS = 500


def load_generator():
    path = REPO_ROOT / "data" / "generator" / "synth.py"
    spec = importlib.util.spec_from_file_location("phc_synth", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phc_synth"] = mod
    spec.loader.exec_module(mod)
    return mod


def _reference_time() -> datetime:
    if settings.demo_reference_time:
        ts = datetime.fromisoformat(settings.demo_reference_time)
        return ts if ts.tzinfo else ts.replace(tzinfo=IST)
    return datetime.now(IST)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


class NotFound(KeyError):
    pass


class InvalidAction(ValueError):
    pass


class Store:
    def __init__(self, reference_time: datetime | None = None, seed: int | None = None):
        self.lock = threading.RLock()
        gen = load_generator()
        self.reference_time = reference_time or _reference_time()
        ds = gen.generate(seed or settings.data_seed, self.reference_time)
        self.meta = ds.metadata
        self.scenarios = ds.scenarios
        self.events = ds.events
        self.medicines = {m["drug_code"]: m for m in ds.medicines}
        self.med_codes = [m["drug_code"] for m in ds.medicines]
        self.midx = {c: j for j, c in enumerate(self.med_codes)}
        self.facilities = {f["facility_id"]: f for f in ds.facilities}
        self.fidx = {fid: i for i, fid in enumerate(ds.dispensing_ids)}
        self.daily, self.stockout, self.dates = ds.consumption, ds.stockout, ds.dates
        self.states = load_state_files()
        self.status = ds.facility_status
        self.checkins: dict[str, set[str]] = {}
        self.captures: dict[str, dict] = {}
        self.transfers: dict[str, dict] = {}
        self.notifications: list[dict] = []
        self.transactions: list[dict] = []
        self.alert_reviews: dict[str, dict] = {}

        # State-native exports → adapters → canonical stock snapshots.
        hfr_index = {f["hfr_id"]: fid for fid, f in self.facilities.items()}
        expiry = {(s["facility_id"], s["drug_code"]): s["near_expiry_date"] for s in ds.snapshots}
        self.stock: dict[tuple[str, str], dict] = {}
        for state, records in ds.native_exports.items():
            for rec in records:
                c = to_canonical(state, rec, hfr_index)
                c["near_expiry_date"] = expiry.get((c["facility_id"], c["drug_code"]))
                self.stock[(c["facility_id"], c["drug_code"])] = c

        # Derived features (history is immutable during a demo session).
        weekly, so_w = fc.to_weekly(self.daily, self.stockout)
        self.adj, self.valid = fc.demand_weekly(weekly, so_w)
        self.weekly, self.weekly_so = weekly, so_w
        t = weekly.shape[-1] - 1
        self.fc_expected = fc.forecast_at(self.adj, self.valid, t, HORIZON_WEEKS)
        bt = fc.backtest(self.adj, self.valid)
        self.rel_sd = bt["rel_sd"]
        self.fc_low, self.fc_high = fc.ranges(self.fc_expected, self.rel_sd)
        self.backtest = bt
        self.forecast_generated_at = self.reference_time
        self.daily_demand = np.zeros((len(self.fidx), len(self.med_codes)))
        for i in range(len(self.fidx)):
            for j in range(len(self.med_codes)):
                self.daily_demand[i, j] = cv.recent_daily_demand(self.daily[i, j, -28:], self.stockout[i, j, -28:])
        self.surge_ratio, self.last7 = ew.surge_ratios(self.daily, self.stockout)

    # ------------------------------------------------------------------ basics
    def now(self) -> datetime:
        return datetime.now(IST)

    def hours_since(self, ts: datetime | None) -> float | None:
        if ts is None:
            return None
        return max(0.0, (self.now() - ts).total_seconds() / 3600)

    def facility(self, fid: str) -> dict:
        if fid not in self.facilities:
            raise NotFound(f"Unknown facility {fid}")
        return self.facilities[fid]

    def dispensing(self, state: str | None = None, district: str | None = None) -> list[dict]:
        return [f for f in self.facilities.values() if f["type"] != "DWH"
                and (not state or f["state"] == state) and (not district or f["district"] == district)]

    def data_label(self) -> dict:
        return {"source": self.meta["source"], "dataset_version": self.meta["dataset_version"],
                "is_synthetic": True, "reference_timestamp": self.meta["reference_timestamp"]}

    def weights(self, state: str) -> dict:
        return self.states.get(state, {}).get("config", {}).get("readiness_weights", rd.DEFAULT_WEIGHTS)

    # ------------------------------------------------------------------ visibility
    def stock_rows(self, fid: str) -> list[dict]:
        f = self.facility(fid)
        if f["type"] == "DWH":
            return []
        i = self.fidx[fid]
        rows = []
        for code in self.med_codes:
            j = self.midx[code]
            s = self.stock[(fid, code)]
            med = self.medicines[code]
            dd = float(self.daily_demand[i, j])
            doc = cv.days_of_cover(s["on_hand"], s["in_transit"], dd)
            risk = 1.0 if s["on_hand"] <= 0 else ew.stockout_risk(
                s["on_hand"] + s["in_transit"], list(self.fc_expected[i, j]), float(self.rel_sd[i, j]),
                f["lead_time_days"])
            surge = ew.is_surge(float(self.surge_ratio[i, j]), float(self.last7[i, j]))
            rows.append({
                "drug_code": code, "name": med["name"], "strength": med["strength"], "unit": med["unit"],
                "group": med["group"], "is_tracer": med["is_tracer"], "on_hand": s["on_hand"],
                "in_transit": s["in_transit"], "daily_demand": round(dd, 1), "days_of_cover": doc,
                "status": cv.stock_status(s["on_hand"], doc), "stockout_risk": risk,
                "risk_band": ew.risk_band(risk, s["on_hand"]), "lead_time_days": f["lead_time_days"],
                "near_expiry_qty": s["near_expiry_qty"], "near_expiry_date": s.get("near_expiry_date"),
                "updated_at": s["updated_at"], "source": s["source"],
                "hours_since_update": round(self.hours_since(s["updated_at"]) or 0, 1),
                "surge": surge, "surge_ratio": round(float(self.surge_ratio[i, j]), 2),
                "forecast_next_week": round(float(self.fc_expected[i, j, 0]), 1),
                "is_synthetic": True,
            })
        return rows

    def surge_groups(self, rows: list[dict]) -> set[str]:
        return {r["group"] for r in rows if r["surge"]}

    def readiness(self, fid: str, rows: list[dict] | None = None) -> dict:
        f = self.facility(fid)
        rows = rows if rows is not None else self.stock_rows(fid)
        st = self.status[fid]
        return rd.readiness(rows, st["beds_total"], st["beds_occupied"], self.staff_present(fid),
                            st["staff_sanctioned"], self.hours_since(st["last_stock_report_at"]),
                            len(self.surge_groups(rows)), self.weights(f["state"]))

    def staff_present(self, fid: str) -> int:
        st = self.status[fid]
        return min(st["staff_sanctioned"], st["staff_present"] + len(self.checkins.get(fid, set())))

    def freshness(self, fid: str) -> dict:
        st = self.status[fid]
        return {
            "stock": {"at": st["last_stock_report_at"], "source": st["last_stock_report_source"],
                      "hours_ago": round(self.hours_since(st["last_stock_report_at"]) or 0, 1)},
            "beds": {"at": st["beds_updated_at"], "hours_ago": round(self.hours_since(st["beds_updated_at"]) or 0, 1)},
            "attendance": {"at": st["attendance_updated_at"],
                           "hours_ago": round(self.hours_since(st["attendance_updated_at"]) or 0, 1)},
            "forecast": {"at": self.forecast_generated_at, "model": f"{fc.MODEL_ID}@{fc.MODEL_VERSION}"},
            "stale": (self.hours_since(st["last_stock_report_at"]) or 0) > 72,
        }

    def summary(self, fid: str) -> dict:
        f = self.facility(fid)
        base = {k: f[k] for k in ("facility_id", "hfr_id", "name", "type", "state", "district", "district_name",
                                  "block", "lat", "lng", "warehouse_id", "lead_time_days")}
        if f["type"] == "DWH":
            return base | {"readiness": None, "is_warehouse": True}
        rows = self.stock_rows(fid)
        st = self.status[fid]
        tracer = [r for r in rows if r["is_tracer"]]
        worst = max(tracer, key=lambda r: cv.STATUS_RANK[r["status"]])["status"]
        r = self.readiness(fid, rows)
        return base | {
            "is_warehouse": False, "readiness": {"score": r["score"], "band": r["band"]},
            "worst_status": worst,
            "stocked_out": [x["drug_code"] for x in tracer if x["status"] == "stocked_out"],
            "critical": [x["drug_code"] for x in tracer if x["status"] == "critical"],
            "high_risk": [x["drug_code"] for x in tracer if x["risk_band"] in ("high", "stocked_out")],
            "max_stockout_risk": max(x["stockout_risk"] for x in tracer),
            "surge_groups": sorted(self.surge_groups(rows)),
            "beds": {"total": st["beds_total"], "occupied": st["beds_occupied"]},
            "staff": {"sanctioned": st["staff_sanctioned"], "present": self.staff_present(fid)},
            "freshness_hours": round(self.hours_since(st["last_stock_report_at"]) or 0, 1),
            "stale": (self.hours_since(st["last_stock_report_at"]) or 0) > 72,
            "near_expiry_qty": sum(x["near_expiry_qty"] for x in rows),
            "is_synthetic": True,
        }

    def canonical(self, fid: str) -> dict:
        f = self.facility(fid)
        rows = self.stock_rows(fid)
        st = self.status[fid]
        return {
            "schema_version": "canonical-v1", "state": f["state"], "district": f["district_name"],
            "block": f["block"], "facility_id": fid, "hfr_id": f["hfr_id"], "timestamp": self.now(),
            "stock": [{"drug_code": r["drug_code"], "on_hand": r["on_hand"], "in_transit": r["in_transit"],
                       "days_of_cover": r["days_of_cover"], "status": r["status"],
                       "stockout_risk": r["stockout_risk"], "near_expiry_qty": r["near_expiry_qty"],
                       "updated_at": r["updated_at"], "source": r["source"]} for r in rows],
            "beds": {"total": st["beds_total"], "occupied": st["beds_occupied"]},
            "staff": {"sanctioned": st["staff_sanctioned"], "present": self.staff_present(fid)},
            "footfall": {"opd_today": st["opd_today"]},
            "risk": {"stockout_risk": max((r["stockout_risk"] for r in rows if r["is_tracer"]), default=0.0),
                     "surge_flag": bool(self.surge_groups(rows))},
            "data_label": self.data_label(),
        }

    # ------------------------------------------------------------------ forecast
    def week_start(self, h: int) -> date:
        return self.dates[-1] + timedelta(days=1 + 7 * (h - 1))

    def forecast(self, fid: str, drug_code: str | None = None) -> dict:
        f = self.facility(fid)
        if f["type"] == "DWH":
            raise InvalidAction("Warehouses have no dispensing forecast")
        i = self.fidx[fid]
        codes = [drug_code] if drug_code else [c for c in self.med_codes if self.medicines[c]["is_tracer"]]
        out = []
        for code in codes:
            if code not in self.midx:
                raise NotFound(f"Unknown drug {code}")
            j = self.midx[code]
            weeks = None
            model = {"id": fc.MODEL_ID, "version": fc.MODEL_VERSION, "backend": "local_baseline", "is_demo": True}
            if forecast_bigquery_enabled():
                weeks = cloud_sinks.bigquery_forecast(fid, code, HORIZON_WEEKS)
                if weeks:
                    model = {"id": "weekly_demand_arima", "version": "bqml-arima-plus", "backend": "bigquery_ml",
                             "is_demo": False}
            if not weeks:
                weeks = [{"week_start": self.week_start(h + 1).isoformat(),
                          "demand_low": round(float(self.fc_low[i, j, h]), 1),
                          "demand_expected": round(float(self.fc_expected[i, j, h]), 1),
                          "demand_high": round(float(self.fc_high[i, j, h]), 1)} for h in range(HORIZON_WEEKS)]
            n_hist = 12
            hist = [{"week_start": (self.dates[-1] - timedelta(days=7 * (n_hist - k) - 1)).isoformat(),
                     "consumption": int(self.weekly[i, j, -n_hist + k]),
                     "stockout_days": int(self.weekly_so[i, j, -n_hist + k])} for k in range(n_hist)]
            m = self.medicines[code]
            out.append({"drug_code": code, "name": m["name"], "strength": m["strength"], "unit": m["unit"],
                        "weeks": weeks, "history": hist, "model": model,
                        "relative_error_sd": round(float(self.rel_sd[i, j]), 3),
                        "note": "Weeks with >= 2 stock-out days are excluded (censored demand)."})
        return {"facility_id": fid, "generated_at": self.forecast_generated_at, "forecasts": out,
                "data_label": self.data_label()}

    # ------------------------------------------------------------------ alerts
    def alerts(self, state: str | None = None, district: str | None = None, facility_id: str | None = None,
               language: str = "en") -> list[dict]:
        language = msg.lang(language)
        facs = [self.facility(facility_id)] if facility_id else self.dispensing(state, district)
        out: list[dict] = []
        now = self.now()
        rows_by_f = {f["facility_id"]: self.stock_rows(f["facility_id"]) for f in facs}
        for f in facs:
            rows = rows_by_f[f["facility_id"]]
            tracer = [r for r in rows if r["is_tracer"]]
            so = [r for r in tracer if r["status"] == "stocked_out"]
            hi = [r for r in tracer if r["risk_band"] == "high"]
            for kind, items, sev in (("stocked_out", so, "high"), ("stockout_risk", hi, "high")):
                if not items:
                    continue
                names = ", ".join(f"{r['name']} {r['strength']}" for r in items)
                key = "alert_stocked_out" if kind == "stocked_out" else "alert_risk"
                out.append(self._alert(kind, [f["facility_id"]], [r["drug_code"] for r in items], sev,
                                       msg.t(key, language, medicines=names), language, now,
                                       {"facility_name": f["name"], "district": f["district"], "state": f["state"],
                                        "max_risk": max(r["stockout_risk"] for r in items)}))
        # Surge clusters: district x medicine group across facilities (threshold rule).
        scope = facs if not facility_id else self.dispensing(district=facs[0]["district"])
        groups: dict[tuple[str, str], list[tuple[dict, list[dict]]]] = {}
        for f in scope:
            rows = rows_by_f.get(f["facility_id"]) or self.stock_rows(f["facility_id"])
            for g in self.surge_groups(rows):
                surged = [r for r in rows if r["surge"] and r["group"] == g]
                groups.setdefault((f["district"], g), []).append((f, surged))
        for (dist, g), members in groups.items():
            if len(members) < ew.CLUSTER_MIN_FACILITIES:
                continue
            fids = [f["facility_id"] for f, _ in members]
            if facility_id and facility_id not in fids:
                continue
            codes = sorted({r["drug_code"] for _, rs in members for r in rs})
            ratio = np.mean([r["surge_ratio"] for _, rs in members for r in rs])
            names = ", ".join(self.medicines[c]["name"] for c in codes)
            dname = members[0][0]["district_name"]
            alert = self._alert("surge", fids, codes, "high" if len(members) >= 5 else "medium",
                                msg.t("alert_surge", language, label=ew.GROUP_LABELS[g], medicines=names,
                                      ratio=f"{ratio:.1f}", n=len(members), district=dname),
                                language, now, {"group": g, "label": ew.GROUP_LABELS[g], "district": dist,
                                                "state": members[0][0]["state"], "ratio": round(float(ratio), 2),
                                                "blocks": sorted({f["block"] for f, _ in members}),
                                                "is_possible_signal": True})
            review = self.alert_reviews.get(alert["alert_id"])
            alert["status"] = review["status"] if review else "pending_review"
            alert["review"] = review
            if facility_id and alert["status"] != "verified":
                continue  # facilities only see surge signals after the DHO verifies them
            out.append(alert)
        sev_rank = {"high": 0, "medium": 1, "low": 2}
        out.sort(key=lambda a: (a["type"] != "surge", sev_rank[a["severity"]], -a["context"].get("max_risk", 0)))
        return out

    def _alert(self, kind, fids, codes, severity, summary, language, now, ctx) -> dict:
        aid = "ALT-" + hashlib.sha1(f"{kind}|{'|'.join(sorted(fids))}|{'|'.join(codes)}".encode()).hexdigest()[:10]
        return {"alert_id": aid, "type": kind, "facility_ids": fids, "drug_codes": codes, "severity": severity,
                "summary": summary, "created_at": now, "language": language, "status": "active",
                "model_name": "early-warning-rules", "model_version": "1.0", "prompt_version": "n/a",
                "context": ctx, "is_synthetic": True}

    def review_alert(self, alert_id: str, action: str, by: str) -> dict:
        if action not in ("verify", "dismiss"):
            raise InvalidAction("action must be verify or dismiss")
        match = next((a for a in self.alerts() if a["alert_id"] == alert_id), None)
        if not match or match["type"] != "surge":
            raise NotFound(f"Unknown surge alert {alert_id}")
        with self.lock:
            review = {"status": "verified" if action == "verify" else "dismissed", "by": by, "at": self.now()}
            self.alert_reviews[alert_id] = review
            if action == "verify":
                texts = {}
                for lg in msg.SUPPORTED:
                    loc = next(a for a in self.alerts(district=match["context"]["district"], language=lg)
                               if a["alert_id"] == alert_id)
                    texts[lg] = loc["summary"]
                for fid in match["facility_ids"]:
                    self._notify(fid, "surge_verified", {"label": match["context"]["label"]}, texts, None)
                self._notify(f"DHO-{match['context']['district']}", "surge_verified",
                             {"label": match["context"]["label"]}, texts, None)
        return {**match, "status": review["status"], "review": review}

    # ------------------------------------------------------------------ overview
    def overview(self, state: str | None = None, district: str | None = None) -> dict:
        facs = self.dispensing(state, district)
        sums = [self.summary(f["facility_id"]) for f in facs]
        alerts = self.alerts(state, district)
        by_drug: dict[str, int] = {}
        for s in sums:
            for c in set(s["high_risk"]) | set(s["stocked_out"]):
                by_drug[c] = by_drug.get(c, 0) + 1
        transfers = self.list_transfers(state=state, district=district)
        return {
            "scope": {"state": state, "district": district},
            "facilities": len(sums),
            "reporting_24h": sum(1 for s in sums if s["freshness_hours"] <= 24),
            "stale_72h": sum(1 for s in sums if s["stale"]),
            "facilities_at_risk": sum(1 for s in sums if s["high_risk"] or s["stocked_out"]),
            "medicines_at_risk": sum(by_drug.values()),
            "at_risk_by_drug": [{"drug_code": c, "name": self.medicines[c]["name"], "facilities": n}
                                for c, n in sorted(by_drug.items(), key=lambda kv: -kv[1])],
            "beds_total": sum(s["beds"]["total"] for s in sums),
            "beds_available": sum(s["beds"]["total"] - s["beds"]["occupied"] for s in sums),
            "staff_sanctioned": sum(s["staff"]["sanctioned"] for s in sums),
            "staff_present": sum(s["staff"]["present"] for s in sums),
            "surge_alerts": sum(1 for a in alerts if a["type"] == "surge"),
            "pending_transfers": sum(1 for t in transfers if t["status"] == "proposed"),
            "active_transfers": sum(1 for t in transfers if t["status"] in ("approved", "dispatched")),
            "near_expiry_qty": sum(s["near_expiry_qty"] for s in sums),
            "avg_readiness": round(float(np.mean([s["readiness"]["score"] for s in sums])), 1) if sums else None,
            "data_label": self.data_label(),
        }

    # ------------------------------------------------------------------ capture
    def create_capture(self, fid: str, source: str, language: str, items: list[dict], unrecognised: list[str],
                       provenance: dict, transcript: dict | None = None, rows: list[dict] | None = None,
                       register_date: str | None = None) -> dict:
        self.facility(fid)
        current = {r["drug_code"]: r for r in self.stock_rows(fid)}
        enriched = []
        for it in items:
            med = self.medicines.get(it.get("drug_code") or "")
            enriched.append({**it, "standard_name": msg.medicine_label(med) if med else None,
                             "unit": (med or {}).get("unit", it.get("unit")),
                             "current_on_hand": current[it["drug_code"]]["on_hand"] if med else None,
                             "needs_review": med is None or it.get("quantity") is None
                             or it.get("match_confidence", 1) < 0.7})
        cap = {
            "capture_id": _id("CAP"), "facility_id": fid, "source": source, "language": msg.lang(language),
            "status": "pending_confirmation", "created_at": self.now(), "items": enriched,
            "unrecognised": unrecognised, "rows": rows, "register_date": register_date, "transcript": transcript,
            "confirmation_text": msg.confirmation_text(enriched, unrecognised, self.medicines, language),
            "provenance": provenance, "requires_confirmation": True,
        }
        with self.lock:
            self.captures[cap["capture_id"]] = cap
        cloud_sinks.record_event("ai_outputs", {"capture_id": cap["capture_id"], "facility_id": fid, "source": source,
                                                "items": enriched, **provenance})
        return cap

    def confirm_capture(self, capture_id: str, items: list[dict], confirmed_by: str = "PHC staff") -> dict:
        with self.lock:
            cap = self.captures.get(capture_id)
            if not cap:
                raise NotFound(f"Unknown capture {capture_id}")
            if cap["status"] != "pending_confirmation":
                raise InvalidAction(f"Capture already {cap['status']}")
            fid = cap["facility_id"]
            now = self.now()
            saved = []
            for it in items:
                code, qty = it.get("drug_code"), it.get("quantity")
                if code not in self.medicines or qty is None:
                    continue
                qty = int(round(float(qty)))
                if qty < 0:
                    raise InvalidAction("Quantities cannot be negative")
                s = self.stock[(fid, code)]
                delta = qty - s["on_hand"]
                s.update(on_hand=qty, updated_at=now, source=cap["source"])
                prov = cap["provenance"]
                tx = {"transaction_id": _id("TX"), "facility_id": fid, "drug_code": code, "type": "adjustment",
                      "quantity": qty, "delta": delta, "batch": None, "expiry_date": None, "source": cap["source"],
                      "created_at": now, "capture_id": capture_id, "confirmed_by": confirmed_by,
                      "model_name": prov.get("model_name"), "model_version": prov.get("model_version"),
                      "prompt_version": prov.get("prompt_version")}
                self.transactions.append(tx)
                cloud_sinks.record_event("stock_transactions", tx)
                saved.append(code)
            if not saved:
                raise InvalidAction("No valid items to save")
            st = self.status[fid]
            st["last_stock_report_at"], st["last_stock_report_source"] = now, cap["source"]
            cap.update(status="confirmed", confirmed_at=now, confirmed_by=confirmed_by, confirmed_items=items)
        rows = [r for r in self.stock_rows(fid) if r["drug_code"] in saved]
        return {"capture": cap, "saved": saved, "stock": rows, "readiness": self.readiness(fid),
                "message": msg.t("saved", cap["language"], n=len(saved))}

    # ------------------------------------------------------------------ beds & attendance
    def update_beds(self, fid: str, occupied: int, total: int | None) -> dict:
        with self.lock:
            st = self.status[self.facility(fid)["facility_id"]]
            if total is not None:
                st["beds_total"] = total
            if occupied < 0 or occupied > st["beds_total"]:
                raise InvalidAction("occupied must be between 0 and total beds")
            st.update(beds_occupied=occupied, beds_updated_at=self.now())
        return {"beds": {"total": st["beds_total"], "occupied": occupied}, "updated_at": st["beds_updated_at"]}

    def check_in(self, fid: str, lat: float, lng: float, token: str | None) -> dict:
        from app.integrations.routes import haversine_km

        f = self.facility(fid)
        dist_m = haversine_km((lat, lng), (f["lat"], f["lng"])) * 1000
        accepted = dist_m <= GEOFENCE_METERS
        with self.lock:
            if accepted:
                self.checkins.setdefault(fid, set()).add(token or uuid.uuid4().hex)
                self.status[fid]["attendance_updated_at"] = self.now()
        return {"accepted": accepted, "distance_m": round(dist_m), "geofence_m": GEOFENCE_METERS,
                "staff": {"present": self.staff_present(fid), "sanctioned": self.status[fid]["staff_sanctioned"]},
                "note": "Only aggregate presence is shown; individual locations are not stored."}

    # ------------------------------------------------------------------ redistribution
    def optimizer_rows(self, state: str | None, district: str | None, drug_code: str | None) -> list[dict]:
        pending_in: dict[tuple[str, str], int] = {}
        pending_out: dict[tuple[str, str], int] = {}
        for t in self.transfers.values():
            if t["status"] == "approved":
                kin, kout = (t["to_facility_id"], t["drug_code"]), (t["from_facility_id"], t["drug_code"])
                pending_in[kin] = pending_in.get(kin, 0) + t["quantity"]
                pending_out[kout] = pending_out.get(kout, 0) + t["quantity"]
        rows = []
        for f in self.dispensing(state, district):
            for r in self.stock_rows(f["facility_id"]):
                if drug_code and r["drug_code"] != drug_code:
                    continue
                key = (f["facility_id"], r["drug_code"])
                on_hand = max(0, r["on_hand"] - pending_out.get(key, 0))
                in_transit = r["in_transit"] + pending_in.get(key, 0)
                dd = r["daily_demand"]
                rows.append({**r, "facility_id": f["facility_id"], "district": f["district"], "lat": f["lat"],
                             "lng": f["lng"], "on_hand": on_hand, "in_transit": in_transit,
                             "days_of_cover": cv.days_of_cover(on_hand, in_transit, dd)})
        return rows

    def add_transfers(self, proposals: list[dict], scope: dict) -> list[dict]:
        with self.lock:
            for tid in [k for k, t in self.transfers.items() if t["status"] == "proposed"
                        and (not scope.get("state") or t["state"] == scope["state"])
                        and (not scope.get("district") or t["district"] == scope["district"])]:
                del self.transfers[tid]
            created = []
            for p in proposals:
                self.transfers[p["transfer_id"]] = p
                created.append(p)
                cloud_sinks.record_event("transfers", p)
        return created

    def list_transfers(self, state=None, district=None, status=None, facility_id=None) -> list[dict]:
        out = [t for t in self.transfers.values()
               if (not state or t["state"] == state) and (not district or t["district"] == district)
               and (not status or t["status"] == status)
               and (not facility_id or facility_id in (t["from_facility_id"], t["to_facility_id"]))]
        return sorted(out, key=lambda t: (t["status"] != "proposed", -t["optimiser"]["stockout_days_avoided"]))

    def transition(self, transfer_id: str, action: str, by: str, note: str | None = None) -> dict:
        allowed = {"approve": ("proposed", "approved"), "reject": ("proposed", "rejected"),
                   "dispatch": ("approved", "dispatched"), "receive": ("dispatched", "received")}
        if action not in allowed:
            raise InvalidAction(f"Unknown action {action}")
        with self.lock:
            t = self.transfers.get(transfer_id)
            if not t:
                raise NotFound(f"Unknown transfer {transfer_id}")
            frm, to = allowed[action]
            if t["status"] != frm:
                raise InvalidAction(f"Cannot {action} a transfer that is {t['status']}")
            now = self.now()
            q, code = t["quantity"], t["drug_code"]
            if action == "dispatch":
                donor = self.stock[(t["from_facility_id"], code)]
                if donor["on_hand"] < q:
                    raise InvalidAction("Donor no longer has enough stock; re-run the optimiser")
                donor.update(on_hand=donor["on_hand"] - q, updated_at=now, source="transfer_out")
                self.stock[(t["to_facility_id"], code)]["in_transit"] += q
                self._tx(t["from_facility_id"], code, "transfer_out", q, now, t)
            elif action == "receive":
                recv = self.stock[(t["to_facility_id"], code)]
                recv.update(on_hand=recv["on_hand"] + q, in_transit=max(0, recv["in_transit"] - q), updated_at=now,
                            source="transfer_in")
                self._tx(t["to_facility_id"], code, "transfer_in", q, now, t)
            t["status"] = to
            t[f"{to}_at"] = now
            t[f"{to}_by"] = by
            if action == "approve":
                t["approved_by"] = by
            t["history"].append({"status": to, "at": now, "by": by, "note": note})
            params = {"qty": f"{q:,}", "medicine": t["medicine"], "from_name": t["from_name"], "to_name": t["to_name"]}
            key = {"approve": "transfer_approved", "dispatch": "transfer_dispatched",
                   "receive": "transfer_received"}.get(action)
            if key:
                texts = {lg: msg.t(key, lg, unit=msg.unit_word(t["unit"], lg), **params) for lg in msg.SUPPORTED}
                targets = {"approve": [t["from_facility_id"], t["to_facility_id"]],
                           "dispatch": [t["to_facility_id"]],
                           "receive": [t["from_facility_id"], f"DHO-{t['district']}"]}[action]
                for fid in targets:
                    self._notify(fid, key, params, texts, transfer_id)
            cloud_sinks.record_event("transfers", t)
        return t

    def _tx(self, fid, code, kind, q, now, t) -> None:
        tx = {"transaction_id": _id("TX"), "facility_id": fid, "drug_code": code, "type": kind, "quantity": q,
              "delta": q if kind == "transfer_in" else -q, "batch": None, "expiry_date": None, "source": "transfer",
              "created_at": now, "transfer_id": t["transfer_id"], "model_name": t["model_name"],
              "model_version": t["model_version"], "prompt_version": t["prompt_version"]}
        self.transactions.append(tx)
        cloud_sinks.record_event("stock_transactions", tx)

    def _notify(self, target: str, kind: str, params: dict, texts: dict, transfer_id: str | None) -> None:
        n = {"notification_id": _id("NTF"), "target": target, "type": kind, "params": params, "texts": texts,
             "transfer_id": transfer_id, "created_at": self.now()}
        n["channel"] = "firestore" if cloud_sinks.push_notification(n) else "in_app"
        self.notifications.append(n)

    def notifications_for(self, target: str) -> list[dict]:
        return sorted([n for n in self.notifications if n["target"] == target], key=lambda n: n["created_at"],
                      reverse=True)


_store: Store | None = None
_store_lock = threading.Lock()


def get_store() -> Store:
    global _store
    with _store_lock:
        if _store is None:
            _store = Store()
        return _store


def reset_store(reference_time: datetime | None = None) -> Store:
    global _store
    with _store_lock:
        _store = Store(reference_time)
        return _store
