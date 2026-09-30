"""Gemini explanation of an optimiser-decided transfer (PRD §34.3). Gemini never changes quantities."""
import json

from app.ai.orchestrator import run_structured
from app.ai.schemas import RedistributionExplanation

LANG_NAMES = {"en": "English", "hi": "Hindi", "ta": "Tamil"}


def _risk_level(risk: float) -> str:
    return "high" if risk > 0.8 else "medium" if risk >= 0.5 else "low"


def build_context(t: dict, donor: dict, receiver: dict, medicine: dict, receiver_surge: bool,
                  donor_fresh_h: float | None, receiver_fresh_h: float | None) -> dict:
    return {
        "medicine": f"{medicine['name']} {medicine['strength']} ({medicine['drug_code']})",
        "unit": medicine["unit"],
        "quantity": t["quantity"],
        "from": {"name": donor["name"], "block": donor["block"], "district": donor["district_name"],
                 "days_of_cover_before": t["donor_cover_before"], "days_of_cover_after": t["donor_cover_after"],
                 "safety_stock_days": t["donor_safety_days"], "near_expiry_qty": t["donor_near_expiry_qty"],
                 "near_expiry_date": t["donor_near_expiry_date"], "hours_since_stock_report": donor_fresh_h},
        "to": {"name": receiver["name"], "block": receiver["block"], "district": receiver["district_name"],
               "days_of_cover_before": t["receiver_cover_before"], "days_of_cover_after": t["receiver_cover_after"],
               "daily_demand": t["receiver_daily_demand"],
               "stockout_risk_within_lead_time": t["receiver_stockout_risk"],
               "possible_demand_surge": receiver_surge, "hours_since_stock_report": receiver_fresh_h},
        "travel_minutes": t["travel_minutes"], "travel_time_source": t["travel_mode"],
        "cross_district": t["cross_district"],
        "stockout_days_avoided_next_30_days": t["stockout_days_avoided"],
    }


def _demo(ctx: dict) -> RedistributionExplanation:
    fr, to = ctx["from"], ctx["to"]
    qty, unit = ctx["quantity"], ctx["unit"]
    reasons = [
        f"{to['name']} has {to['days_of_cover_before']} days of cover and a "
        f"{round(to['stockout_risk_within_lead_time'] * 100)}% risk of running out before the next supply"
        + (" during a possible demand surge." if to["possible_demand_surge"] else "."),
        f"{fr['name']} has {fr['days_of_cover_before']} days of cover"
        + (f", with {fr['near_expiry_qty']} {unit}s expiring soon." if fr["near_expiry_qty"] else "."),
        f"After the transfer {fr['name']} keeps {fr['days_of_cover_after']} days of cover, above its "
        f"{fr['safety_stock_days']:.0f}-day safety stock.",
    ]
    uncertainties = ["Demand is a forecast and may be higher or lower than expected."]
    if to["possible_demand_surge"]:
        uncertainties.append("The demand surge is a possible signal that needs verification, not a confirmed outbreak.")
    stale = [f["name"] for f in (fr, to) if (f["hours_since_stock_report"] or 0) > 72]
    if stale:
        uncertainties.append(f"Stock data for {', '.join(stale)} is more than 3 days old.")
    if ctx["travel_time_source"] == "haversine":
        uncertainties.append("Travel time is a straight-line estimate (demo mode), not a road route.")
    return RedistributionExplanation(
        summary=f"Move {qty:,} {unit}s of {ctx['medicine']} from {fr['name']} to {to['name']}.",
        risk_level=_risk_level(to["stockout_risk_within_lead_time"]),
        reasons=reasons,
        impact=f"Avoids an estimated {ctx['stockout_days_avoided_next_30_days']} stock-out days at {to['name']} "
               f"over the next 30 days (cover {to['days_of_cover_before']} → {to['days_of_cover_after']} days).",
        uncertainties=uncertainties,
        travel_minutes=ctx["travel_minutes"],
        confidence=0.8,
        transfer_note=f"{qty:,} {unit}s {ctx['medicine']}: {fr['name']} → {to['name']} "
                      f"(~{ctx['travel_minutes']:.0f} min). Approved transfer; confirm receipt in PHC Pulse.",
    )


def explain(ctx: dict, language: str = "en") -> tuple[dict, dict]:
    result, prov = run_structured(
        "explain_transfer", "v1", RedistributionExplanation,
        {"context": json.dumps(ctx, ensure_ascii=False, indent=1), "language": LANG_NAMES.get(language, "English")},
        demo=lambda: _demo(ctx), demo_model="demo-template-explainer",
    )
    out = result.model_dump()
    # Guardrail: the explanation must not alter optimiser numbers.
    out["travel_minutes"] = ctx["travel_minutes"]
    out["requires_human_review"] = True
    return out, prov
