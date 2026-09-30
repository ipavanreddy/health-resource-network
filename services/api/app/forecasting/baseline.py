"""Explainable weekly demand forecast: seasonal exponential-smoothing baseline (PRD §14).

    expected[t+h] = level[t] x seasonal_ratio(h)

- level[t]: exponentially weighted mean (alpha 0.3) of the last 8 weeks of *demand*, where weeks with
  >= 2 stock-out days are skipped and weeks with 1 stock-out day are scaled up by 7/(7-1) (censoring).
- seasonal_ratio(h): average over the previous 1-2 years of demand around week (t+h-52y) (3-week mean)
  divided by the level at (t-52y): "last year, demand h weeks after this point was X times the level at this point".
- range: expected x (1 +/- 1.28 x relative error sd x sqrt(h)), relative error sd from a 26-week backtest.

Compared against two naive baselines (same week last year; 4-week moving average) in the model card.
All functions are vectorised over leading (facility, medicine) axes.
"""
import numpy as np

MODEL_ID = "phc-demand-baseline"
MODEL_VERSION = "1.0.0"
ALPHA = 0.3  # chosen on the 26-week backtest (0.2-0.5 x 6-12 weeks grid)
LEVEL_WEEKS = 8
Z80 = 1.2816
MIN_REL_SD = 0.12


def to_weekly(daily: np.ndarray, stockout: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Aggregate (..., D) daily arrays into complete weeks ending on the last day."""
    d = daily.shape[-1]
    w = d // 7
    cut = d - w * 7
    shape = daily.shape[:-1] + (w, 7)
    return daily[..., cut:].reshape(shape).sum(-1), stockout[..., cut:].reshape(shape).sum(-1)


def demand_weekly(weekly: np.ndarray, so_days: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Censoring-adjusted weekly demand and a validity mask (weeks with >= 2 stock-out days invalid)."""
    valid = so_days < 2
    adj = np.where(so_days == 1, weekly * 7 / 6, weekly)
    return adj, valid


def level_at(adj: np.ndarray, valid: np.ndarray, t: int) -> np.ndarray:
    lo = max(0, t - LEVEL_WEEKS + 1)
    x, ok = adj[..., lo:t + 1], valid[..., lo:t + 1]
    n = x.shape[-1]
    wts = ALPHA * (1 - ALPHA) ** np.arange(n - 1, -1, -1) * ok
    s = wts.sum(-1)
    fallback = adj[..., max(0, t - 11):t + 1].mean(-1)
    return np.where(s > 0, (x * wts).sum(-1) / np.maximum(s, 1e-9), fallback)


def forecast_at(adj: np.ndarray, valid: np.ndarray, t: int, horizon: int) -> np.ndarray:
    """Expected weekly demand for weeks t+1..t+horizon. Returns (..., horizon)."""
    lvl = level_at(adj, valid, t)
    out = np.empty(adj.shape[:-1] + (horizon,))
    for h in range(1, horizon + 1):
        ratios, n = np.zeros(adj.shape[:-1]), np.zeros(adj.shape[:-1])
        for y in (1, 2):
            past_t, past_target = t - 52 * y, t + h - 52 * y
            if past_t - LEVEL_WEEKS < 0 or past_target >= adj.shape[-1]:
                continue
            past_lvl = level_at(adj, valid, past_t)
            # Smooth the past target over 3 weeks (target +/- 1) to reduce noise in the seasonal ratio.
            lo, hi = past_target - 1, min(past_target + 2, adj.shape[-1])
            win, wok = adj[..., lo:hi], valid[..., lo:hi]
            past_dem = (win * wok).sum(-1) / np.maximum(wok.sum(-1), 1)
            ok = (wok.sum(-1) > 0) & (past_lvl > 0)
            r = np.clip(past_dem / np.maximum(past_lvl, 1e-9), 0.3, 3.0)
            ratios += np.where(ok, r, 0)
            n += ok
        ratio = np.where(n > 0, ratios / np.maximum(n, 1), 1.0)
        out[..., h - 1] = lvl * ratio
    return out


def backtest(adj: np.ndarray, valid: np.ndarray, origins: int = 26) -> dict:
    """1-week-ahead backtest over the last `origins` weeks for the model and two naive baselines."""
    w = adj.shape[-1]
    errs = {"model": [], "same_week_last_year": [], "moving_average_4w": []}
    actuals, rel_err = [], []
    for t in range(w - origins - 1, w - 1):
        actual, ok = adj[..., t + 1], valid[..., t + 1]
        preds = {
            "model": forecast_at(adj, valid, t, 1)[..., 0],
            "same_week_last_year": adj[..., t + 1 - 52],
            "moving_average_4w": adj[..., t - 3:t + 1].mean(-1),
        }
        for k, p in preds.items():
            errs[k].append(np.where(ok, np.abs(p - actual), 0))
        actuals.append(np.where(ok, actual, 0))
        rel_err.append(np.where(ok & (actual > 0), (preds["model"] - actual) / np.maximum(actual, 1e-9), np.nan))
    total_actual = np.sum(actuals, axis=0)
    rel = np.stack(rel_err, axis=-1)
    with np.errstate(all="ignore"):
        rel_sd = np.nan_to_num(np.nanstd(rel, axis=-1), nan=0.3)
    return {
        "abs_err": {k: np.sum(v, axis=0) for k, v in errs.items()},
        "actual": total_actual,
        "rel_sd": np.clip(rel_sd, MIN_REL_SD, 1.0),
    }


def wape(abs_err: np.ndarray, actual: np.ndarray) -> float:
    a = float(np.sum(actual))
    return round(float(np.sum(abs_err)) / a, 4) if a > 0 else float("nan")


def ranges(expected: np.ndarray, rel_sd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h = np.arange(1, expected.shape[-1] + 1)
    spread = Z80 * rel_sd[..., None] * np.sqrt(h)
    return np.maximum(expected * (1 - spread), 0), expected * (1 + spread)
