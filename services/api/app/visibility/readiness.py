"""Facility Readiness score (PRD §13): transparent, configurable weighted model."""

DEFAULT_WEIGHTS = {"stock_cover": 40, "beds": 20, "staff": 20, "freshness": 10, "surge_stability": 10}
TARGET_COVER_DAYS = 30        # full stock score at >= 30 days of cover
BED_FREE_TARGET = 0.25        # full bed score when >= 25% of beds are free
LABELS = {
    "stock_cover": "Essential medicine stock cover",
    "beds": "Bed availability",
    "staff": "Staff presence",
    "freshness": "Reporting freshness",
    "surge_stability": "Surge stability",
}


def stock_cover_score(rows: list[dict]) -> tuple[float, str]:
    """Mean over tracer medicines of min(days_of_cover / 30, 1); stocked out = 0; no demand = full."""
    tracer = [r for r in rows if r.get("is_tracer", True)]
    if not tracer:
        return 100.0, "No tracer medicines tracked"
    parts = []
    for r in tracer:
        if r["status"] == "stocked_out":
            parts.append(0.0)
        elif r["days_of_cover"] is None:
            parts.append(1.0)
        else:
            parts.append(min(r["days_of_cover"] / TARGET_COVER_DAYS, 1.0))
    out = sum(1 for r in tracer if r["status"] == "stocked_out")
    crit = sum(1 for r in tracer if r["status"] == "critical")
    return 100 * sum(parts) / len(parts), f"{len(tracer)} tracer medicines · {out} stocked out · {crit} critical"


def bed_score(total: int, occupied: int) -> tuple[float, str]:
    if total <= 0:
        return 100.0, "No inpatient beds"
    free = max(total - occupied, 0)
    return 100 * min(free / (BED_FREE_TARGET * total), 1.0), f"{free} of {total} beds available"


def staff_score(present: int, sanctioned: int) -> tuple[float, str]:
    if sanctioned <= 0:
        return 100.0, "No sanctioned posts"
    return 100 * min(present / sanctioned, 1.0), f"{present} of {sanctioned} staff present"


def freshness_score(hours_since_report: float | None) -> tuple[float, str]:
    if hours_since_report is None:
        return 0.0, "Never reported"
    if hours_since_report <= 24:
        s = 100.0
    elif hours_since_report <= 72:
        s = 60.0
    elif hours_since_report <= 168:
        s = 30.0
    else:
        s = 0.0
    return s, f"Last stock report {hours_since_report:.0f} h ago"


def surge_score(surge_groups: int) -> tuple[float, str]:
    return max(0.0, 100.0 - 50.0 * surge_groups), (
        "No unusual demand" if surge_groups == 0 else f"Possible demand surge in {surge_groups} medicine group(s)")


def band(score: float) -> str:
    return "Good" if score >= 75 else "Moderate" if score >= 50 else "Poor"


def readiness(
    stock_rows: list[dict], beds_total: int, beds_occupied: int, staff_present: int, staff_sanctioned: int,
    hours_since_report: float | None, surge_groups: int, weights: dict[str, float] | None = None,
) -> dict:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    total_w = sum(w.values())
    comps = {
        "stock_cover": stock_cover_score(stock_rows),
        "beds": bed_score(beds_total, beds_occupied),
        "staff": staff_score(staff_present, staff_sanctioned),
        "freshness": freshness_score(hours_since_report),
        "surge_stability": surge_score(surge_groups),
    }
    components = []
    total = 0.0
    for key, (score, detail) in comps.items():
        points = score * w[key] / total_w
        total += points
        components.append({"key": key, "label": LABELS[key], "weight": w[key], "score": round(score, 1),
                           "points": round(points, 1), "detail": detail})
    return {"score": round(total), "band": band(total), "components": components, "weights": w,
            "method": "Transparent weighted model (PRD §13); weights configurable per state"}
