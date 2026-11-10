"""Small synthetic markets for unit tests. Not for research."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data.store import Market


def make_market(close: pd.DataFrame, open_: pd.DataFrame | None = None, high: pd.DataFrame | None = None,
                low: pd.DataFrame | None = None, factor: pd.DataFrame | None = None,
                turnover: float | pd.DataFrame = 5e8) -> Market:
    """Build a Market from a close table; other fields default sensibly."""
    close = close.astype(float)
    open_ = close.shift(1).fillna(close.iloc[0]) if open_ is None else open_.astype(float)
    high = np.maximum(open_, close) if high is None else high.astype(float)
    low = np.minimum(open_, close) if low is None else low.astype(float)
    ones = pd.DataFrame(1.0, index=close.index, columns=close.columns)
    factor = ones if factor is None else factor.astype(float)
    to = ones * turnover if not isinstance(turnover, pd.DataFrame) else turnover
    to = to.where(close.notna())
    return Market(open=open_, high=pd.DataFrame(high, index=close.index, columns=close.columns),
                  low=pd.DataFrame(low, index=close.index, columns=close.columns), close=close,
                  volume=to / close, turnover=to, factor=factor, eq=close.notna())


def synthetic_market(days: int = 600, symbols: int = 30, seed: int = 0, start: str = "2010-01-01") -> Market:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, periods=days)
    cols = [f"S{k:03d}" for k in range(symbols)]
    market = rng.normal(0.0004, 0.01, days)
    rets = 0.7 * market[:, None] + rng.normal(0, 0.015, (days, symbols))
    close = pd.DataFrame(100 * np.exp(np.cumsum(rets, axis=0)) * (1 + np.arange(symbols)), idx, cols)
    gap = rng.normal(0, 0.005, (days, symbols))
    open_ = close.shift(1).fillna(close.iloc[0]) * np.exp(gap)
    spread = np.abs(rng.normal(0, 0.008, (days, symbols)))
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread)
    turnover = pd.DataFrame(np.exp(rng.normal(18, 0.5, (days, symbols))) * (1 + np.arange(symbols)[::-1]), idx, cols)
    return make_market(close, open_, high, low, turnover=turnover)
