"""Helpers shared by strategies. Everything here is safe against look-ahead:
no function needs rows after the one it is producing."""
from __future__ import annotations

import numpy as np
import pandas as pd


def period_starts(dates: pd.DatetimeIndex, freq: str = "M") -> np.ndarray:
    """True on the first trading day of each week ("W"), month ("M"),
    quarter ("Q") or year ("Y"). Known on the day itself, unlike "last
    trading day of the month", which needs tomorrow's date."""
    key = {"W": dates.isocalendar().week.to_numpy() + 100 * dates.isocalendar().year.to_numpy(),
           "M": dates.month + 100 * dates.year,
           "Q": dates.quarter + 10 * dates.year,
           "Y": dates.year}[freq]
    key = np.asarray(key)
    out = np.ones(len(dates), bool)
    out[1:] = key[1:] != key[:-1]
    return out


def every_n(dates: pd.DatetimeIndex, n: int, offset: int = 0) -> np.ndarray:
    """True on every n-th trading day, counted from the first date."""
    return (np.arange(len(dates)) - offset) % n == 0


def on_rows(weights: pd.DataFrame, rows: np.ndarray) -> pd.DataFrame:
    """Keep decisions only on the given rows; other days mean "no change"."""
    return weights[np.asarray(rows)]


def top_n(score: pd.DataFrame, n: int, eligible: pd.DataFrame | None = None,
          ascending: bool = False) -> pd.DataFrame:
    """Equal weights (1/n each) on the n best scores per row among eligible
    names. Rows with fewer than n candidates hold fewer names, not bigger ones."""
    s = score.where(eligible) if eligible is not None else score
    rank = s.rank(axis=1, ascending=ascending, method="first")
    return (rank <= n).astype(float) / n


def inverse_vol(picks: pd.DataFrame, vol: pd.DataFrame, gross: float = 1.0) -> pd.DataFrame:
    """Reweight chosen names (non-zero in `picks`) by 1/volatility, summing to `gross`."""
    w = (1.0 / vol).where(picks > 0)
    return w.div(w.sum(axis=1), axis=0).fillna(0.0) * gross


def realised_vol(close: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """Annualised volatility of daily returns over a trailing window."""
    return close.pct_change(fill_method=None).rolling(window, min_periods=window // 2).std() * np.sqrt(252)
