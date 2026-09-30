"""Days of cover and stock status (PRD §12)."""
import numpy as np

CRITICAL_DAYS = 7
LOW_DAYS = 15
RECENT_WINDOW = 7
FALLBACK_WINDOW = 28


def recent_daily_demand(consumption: np.ndarray, stocked_out: np.ndarray) -> float:
    """Average daily use over the last 7 days on which the facility was NOT stocked out.

    Stock-out days are excluded because zero recorded use then does not mean zero demand (PRD §14).
    Falls back to the last 28 such days when fewer than 3 valid days are available.
    """
    for window in (RECENT_WINDOW, FALLBACK_WINDOW):
        c, s = consumption[-window:], stocked_out[-window:]
        valid = c[~s]
        if valid.size >= 3:
            return float(valid.mean())
    return 0.0


def days_of_cover(on_hand: float, in_transit: float, daily_demand: float) -> float | None:
    """(on hand + in transit) / recent daily demand. None when there is no recent demand."""
    if daily_demand <= 0:
        return None
    return round((max(on_hand, 0) + max(in_transit, 0)) / daily_demand, 1)


def stock_status(on_hand: float, cover: float | None) -> str:
    if on_hand <= 0:
        return "stocked_out"
    if cover is None:
        return "adequate"
    if cover < CRITICAL_DAYS:
        return "critical"
    if cover < LOW_DAYS:
        return "low"
    return "adequate"


STATUS_RANK = {"stocked_out": 3, "critical": 2, "low": 1, "adequate": 0}
