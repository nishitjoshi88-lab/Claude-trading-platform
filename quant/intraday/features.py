"""Building blocks for intraday signals. Every function returns values that
depend only on bars up to and including the minute (or day) they describe.

Arrays are (days, 375). "Cumulative" means from the open up to each minute.
"""
from __future__ import annotations

import warnings

import numpy as np

from .grid import Grid


def _ffill_rows(a: np.ndarray) -> np.ndarray:
    """Forward-fill NaNs along each day (no carry-over between days)."""
    mask = np.isfinite(a)
    idx = np.where(mask, np.arange(a.shape[1])[None, :], 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    out = np.take_along_axis(a, idx, axis=1)
    out[~np.maximum.accumulate(mask, axis=1)] = np.nan
    return out


def last_price(g: Grid) -> np.ndarray:
    """Latest traded price as of each minute (fills minutes with no trade)."""
    return _ffill_rows(g.close)


def day_open(g: Grid) -> np.ndarray:
    """First traded price of each day, shape (days,)."""
    o = g.open
    first = np.argmax(np.isfinite(o), axis=1)
    out = o[np.arange(len(o)), first]
    out[~np.isfinite(o).any(axis=1)] = np.nan
    return out


def day_close(g: Grid) -> np.ndarray:
    """Last traded price of each day, shape (days,). Not known until the
    session ends: use `prev_close` inside signals."""
    return last_price(g)[:, -1]


def prev_close(g: Grid) -> np.ndarray:
    """Previous session's close, shape (days,); NaN on the first day."""
    c = day_close(g)
    return np.concatenate([[np.nan], c[:-1]])


def gap(g: Grid) -> np.ndarray:
    """Opening gap versus the previous close, shape (days,). Known at 09:15."""
    return day_open(g) / prev_close(g) - 1


def cum_high(g: Grid) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return np.fmax.accumulate(np.where(np.isfinite(g.high), g.high, -np.inf), axis=1)


def cum_low(g: Grid) -> np.ndarray:
    return np.fmin.accumulate(np.where(np.isfinite(g.low), g.low, np.inf), axis=1)


def opening_range(g: Grid, minutes: int) -> tuple[np.ndarray, np.ndarray]:
    """High and low of the first `minutes` minutes, shape (days,).
    Known from column minutes-1 onward."""
    return cum_high(g)[:, minutes - 1], cum_low(g)[:, minutes - 1]


def cum_volume(g: Grid) -> np.ndarray:
    return np.cumsum(np.nan_to_num(g.volume), axis=1)


def vwap(g: Grid) -> np.ndarray:
    """Volume-weighted average price from the open up to each minute."""
    typical = (g.high + g.low + g.close) / 3
    v = np.nan_to_num(g.volume)
    pv = np.cumsum(np.nan_to_num(typical) * v, axis=1)
    cv = np.cumsum(v, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, pv / cv, np.nan)


def relative_volume(g: Grid, lookback: int = 20) -> np.ndarray:
    """Cumulative volume so far today divided by the average cumulative
    volume at the same minute over the previous `lookback` sessions."""
    cv = cum_volume(g)
    avg = _prior_days_mean(cv, lookback)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(avg > 0, cv / avg, np.nan)


def _prior_days_mean(a: np.ndarray, lookback: int) -> np.ndarray:
    """Mean over the previous `lookback` rows (excluding the current row)."""
    c = np.cumsum(np.nan_to_num(a), axis=0)
    c = np.vstack([np.zeros((1, a.shape[1])), c])
    n = np.arange(len(a))[:, None]
    lo = np.maximum(n - lookback, 0)
    total = c[n, np.arange(a.shape[1])[None, :]] - c[lo, np.arange(a.shape[1])[None, :]]
    count = (n - lo).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(count > 0, total / count, np.nan)


def daily_range_avg(g: Grid, lookback: int = 14) -> np.ndarray:
    """Average of (high - low) / close over the previous `lookback` sessions,
    shape (days,). A simple volatility yardstick known before the open."""
    hi, lo, cl = cum_high(g)[:, -1], cum_low(g)[:, -1], day_close(g)
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = np.where(np.isfinite(hi) & np.isfinite(lo) & (cl > 0), (hi - lo) / cl, np.nan)
    return _prior_days_mean(rng[:, None], lookback)[:, 0]


def prev_day(values: np.ndarray) -> np.ndarray:
    """Shift a per-day array by one session (yesterday's value)."""
    out = np.empty_like(values, dtype=float)
    out[0] = np.nan
    out[1:] = values[:-1]
    return out


def returns_since_open(g: Grid) -> np.ndarray:
    """Return from the day's open to each minute."""
    return last_price(g) / day_open(g)[:, None] - 1


def minute_returns(g: Grid) -> np.ndarray:
    p = last_price(g)
    out = np.full_like(p, np.nan)
    out[:, 1:] = p[:, 1:] / p[:, :-1] - 1
    return out
