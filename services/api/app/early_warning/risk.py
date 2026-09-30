"""Stock-out risk (PRD §15.1) and simple threshold surge detection (PRD §15.2)."""
import math

import numpy as np

SURGE_RATIO = 2.0          # last 7 days vs. the 4 weeks ending 3 weeks ago
SURGE_MIN_UNITS = 20       # ignore tiny counts
CLUSTER_MIN_FACILITIES = 3
RISK_HIGH, RISK_MEDIUM = 0.8, 0.5
GROUP_LABELS = {
    "diarrhoea": "Possible acute diarrhoea cluster",
    "fever": "Possible fever / vector-borne cluster",
    "malaria": "Possible malaria rise",
    "antibiotic": "Unusual antibiotic demand",
    "chronic": "Unusual chronic-care demand",
}


def stockout_risk(available: float, weekly_expected: list[float], rel_sd: float, lead_days: int) -> float:
    """P(demand during the replenishment lead time > on hand + in transit).

    Demand over the lead time ~ Normal(mu, sigma): mu sums the weekly forecast pro rata over the lead
    time; sigma combines forecast error (rel_sd) and Poisson noise.
    """
    if lead_days <= 0:
        return 0.0
    mu, days_left = 0.0, lead_days
    for wk in weekly_expected:
        take = min(7, days_left)
        mu += wk * take / 7
        days_left -= take
        if days_left <= 0:
            break
    if days_left > 0 and weekly_expected:
        mu += weekly_expected[-1] * days_left / 7
    if mu <= 0:
        return 0.0 if available > 0 else 1.0
    sigma = math.sqrt((rel_sd * mu * math.sqrt(7 / max(lead_days, 1))) ** 2 + mu)
    z = (available - mu) / sigma
    return round(0.5 * (1 - math.erf(z / math.sqrt(2))), 3)


def risk_band(risk: float, on_hand: float) -> str:
    if on_hand <= 0:
        return "stocked_out"
    return "high" if risk > RISK_HIGH else "medium" if risk >= RISK_MEDIUM else "low"


def surge_ratios(daily: np.ndarray, stockout: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Ratio of last-7-day use to the weekly average of days -49..-22 (stock-out days excluded).

    Returns (ratio, last7). Works on (..., D) arrays.
    """
    last7 = daily[..., -7:].sum(-1)
    base_c, base_s = daily[..., -49:-21], stockout[..., -49:-21]
    ok = ~base_s
    base_week = np.where(ok.sum(-1) > 0, (base_c * ok).sum(-1) / np.maximum(ok.sum(-1), 1) * 7, 0)
    ratio = np.where(base_week > 0, last7 / np.maximum(base_week, 1e-9), 0)
    return ratio, last7


def is_surge(ratio: float, last7: float) -> bool:
    return ratio >= SURGE_RATIO and last7 >= SURGE_MIN_UNITS
