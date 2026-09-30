"""Cross-facility redistribution as a min-cost max-flow problem (Google OR-Tools, PRD §16).

    source --(surplus)--> donor --(travel cost)--> receiver --(need)--> sink

- Receivers: days of cover below `receiver_cover_below`, or stock-out risk >= 0.5, or stocked out.
  need = target_cover_days x daily demand - (on hand + in transit).
- Donors: days of cover >= `donor_min_cover`. surplus = on hand - donor_safety_days x daily demand, so a
  donor is NEVER taken below its safety stock.
- Arcs only within `max_travel_minutes` (Routes API or haversine estimate) and within the same district
  unless the state policy allows cross-district transfers. Near-expiry stock at the donor lowers the arc
  cost so it is used first.
- The solver maximises the quantity delivered at minimum total cost, where cost = travel minutes
  + 10 x receiver's current days of cover (urgency: when supply is short the most at-risk facility is
  served first) - 15 if the donor holds near-expiry stock. Gemini only explains the result.
"""
import math
from dataclasses import dataclass

from ortools.graph.python import min_cost_flow

from app.integrations.routes import travel_matrix

SOLVER = "OR-Tools SimpleMinCostFlow (max flow, min cost)"
IMPACT_HORIZON_DAYS = 30
NEAR_EXPIRY_BONUS_MIN = 15
URGENCY_MIN_PER_COVER_DAY = 10  # each day of cover a receiver already has costs 10 travel-minute equivalents


@dataclass
class Params:
    target_cover_days: float = 30
    receiver_cover_below: float = 14
    donor_min_cover: float = 60
    donor_safety_days: float = 45
    max_travel_minutes: float = 120
    min_transfer_units: int = 20
    allow_cross_district: bool = False
    max_transfers: int = 12
    tracer_only: bool = True


def _stockout_days(cover: float | None, horizon: int = IMPACT_HORIZON_DAYS) -> float:
    if cover is None:
        return 0.0
    return max(0.0, horizon - cover)


def optimize(rows: list[dict], p: Params) -> dict:
    """rows: one per facility x medicine with keys facility_id, drug_code, district, lat, lng, on_hand,
    in_transit, daily_demand, days_of_cover, stockout_risk, near_expiry_qty.
    Returns {"transfers": [...], "travel_mode": str, "receivers": n, "donors": n, "unmet": {...}}."""
    transfers: list[dict] = []
    modes: set[str] = set()
    n_recv = n_don = 0
    unmet: dict[str, int] = {}
    by_drug: dict[str, list[dict]] = {}
    for r in rows:
        if p.tracer_only and not r.get("is_tracer", True):
            continue
        by_drug.setdefault(r["drug_code"], []).append(r)

    for drug, items in by_drug.items():
        receivers, donors = [], []
        for r in items:
            dd = r["daily_demand"]
            if dd <= 0:
                continue
            avail = r["on_hand"] + r["in_transit"]
            cover = r["days_of_cover"] if r["days_of_cover"] is not None else math.inf
            if r["on_hand"] <= 0 or cover < p.receiver_cover_below or r["stockout_risk"] >= 0.5:
                need = math.ceil(p.target_cover_days * dd - avail)
                if need >= p.min_transfer_units:
                    receivers.append((r, need))
            elif cover >= p.donor_min_cover:
                surplus = math.floor(r["on_hand"] - p.donor_safety_days * dd)
                if surplus >= p.min_transfer_units:
                    donors.append((r, surplus))
        if not receivers or not donors:
            if receivers:
                unmet[drug] = sum(n for _, n in receivers)
            continue
        n_recv += len(receivers)
        n_don += len(donors)
        minutes, mode = travel_matrix([(d["lat"], d["lng"]) for d, _ in donors],
                                      [(r["lat"], r["lng"]) for r, _ in receivers])
        modes.add(mode)

        smcf = min_cost_flow.SimpleMinCostFlow()
        src, sink = 0, 1
        d_node = {i: 2 + i for i in range(len(donors))}
        r_node = {j: 2 + len(donors) + j for j in range(len(receivers))}
        arcs = {}
        for i, (_, surplus) in enumerate(donors):
            smcf.add_arc_with_capacity_and_unit_cost(src, d_node[i], surplus, 0)
        for j, (_, need) in enumerate(receivers):
            smcf.add_arc_with_capacity_and_unit_cost(r_node[j], sink, need, 0)
        for i, (d, surplus) in enumerate(donors):
            for j, (r, need) in enumerate(receivers):
                mins = minutes[i][j]
                cross = d["district"] != r["district"]
                if mins > p.max_travel_minutes or (cross and not p.allow_cross_district):
                    continue
                r_cover = (r["on_hand"] + r["in_transit"]) / r["daily_demand"]
                cost = max(1, int(round(mins + URGENCY_MIN_PER_COVER_DAY * min(r_cover, p.receiver_cover_below)))
                           - (NEAR_EXPIRY_BONUS_MIN if d["near_expiry_qty"] > 0 else 0))
                a = smcf.add_arc_with_capacity_and_unit_cost(d_node[i], r_node[j], min(surplus, need), cost)
                arcs[a] = (i, j)
        # Supplies bound the flow; the max-flow variant tolerates unbalanced supply/demand.
        smcf.set_node_supply(src, sum(sp for _, sp in donors))
        smcf.set_node_supply(sink, -sum(n for _, n in receivers))
        if not arcs or smcf.solve_max_flow_with_min_cost() != smcf.OPTIMAL:
            unmet[drug] = sum(n for _, n in receivers)
            continue

        delivered = {j: 0 for j in range(len(receivers))}
        given = {i: 0 for i in range(len(donors))}
        for a, (i, j) in sorted(arcs.items(), key=lambda kv: minutes[kv[1][0]][kv[1][1]]):
            q = smcf.flow(a)
            if q < p.min_transfer_units:
                continue
            d, surplus = donors[i]
            r, need = receivers[j]
            r_avail_before = r["on_hand"] + r["in_transit"] + delivered[j]
            cover_before = r_avail_before / r["daily_demand"]
            cover_after = (r_avail_before + q) / r["daily_demand"]
            donor_after = (d["on_hand"] - given[i] - q + d["in_transit"]) / d["daily_demand"]
            delivered[j] += q
            given[i] += q
            transfers.append({
                "drug_code": drug, "quantity": int(q),
                "from_facility_id": d["facility_id"], "to_facility_id": r["facility_id"],
                "travel_minutes": minutes[i][j], "travel_mode": mode,
                "cross_district": d["district"] != r["district"],
                "receiver_cover_before": round(cover_before, 1), "receiver_cover_after": round(cover_after, 1),
                "receiver_stockout_risk": r["stockout_risk"], "receiver_daily_demand": round(r["daily_demand"], 1),
                "donor_cover_before": d["days_of_cover"], "donor_cover_after": round(donor_after, 1),
                "donor_safety_days": p.donor_safety_days, "donor_near_expiry_qty": d["near_expiry_qty"],
                "donor_near_expiry_date": d.get("near_expiry_date"),
                "stockout_days_avoided": round(_stockout_days(cover_before) - _stockout_days(cover_after), 1),
            })
        short = sum(need - delivered[j] for j, (_, need) in enumerate(receivers))
        if short > 0:
            unmet[drug] = int(short)

    transfers.sort(key=lambda t: (-t["stockout_days_avoided"], -t["receiver_stockout_risk"], t["travel_minutes"]))
    return {"transfers": transfers[: p.max_transfers], "total_candidates": len(transfers),
            "travel_mode": ",".join(sorted(modes)) or "n/a", "receivers": n_recv, "donors": n_don,
            "unmet_need": unmet, "solver": SOLVER, "params": p.__dict__}
