"""Synthetic minute-bar grids for unit tests. Not for research."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .grid import MINUTES, Grid


def flat_grid(days: int = 3, price: float = 100.0, volume: float = 10_000.0, start: str = "2022-01-03") -> Grid:
    idx = pd.bdate_range(start, periods=days)
    a = np.full((days, MINUTES), price, dtype=np.float32)
    return Grid(idx, a.copy(), a.copy(), a.copy(), a.copy(), np.full((days, MINUTES), volume, dtype=np.float32))


def set_bar(g: Grid, day: int, col: int, o=None, h=None, l=None, c=None) -> None:
    """Edit one bar in place; unspecified fields are made consistent."""
    o = g.open[day, col] if o is None else o
    c = o if c is None else c
    g.open[day, col], g.close[day, col] = o, c
    g.high[day, col] = max(o, c) if h is None else h
    g.low[day, col] = min(o, c) if l is None else l


def synthetic_grids(days: int = 60, symbols: int = 8, seed: int = 0, start: str = "2022-01-03") -> dict[str, Grid]:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, periods=days)
    out = {}
    for k in range(symbols):
        r = rng.normal(0, 0.0007, (days, MINUTES))
        r[:, 0] += rng.normal(0, 0.008, days)                    # overnight gap
        close = 100.0 * (k + 1) * np.exp(np.cumsum(r.reshape(-1))).reshape(days, MINUTES)
        open_ = np.empty_like(close)
        open_[:, 1:] = close[:, :-1]
        open_[:, 0] = close[:, 0] / np.exp(r[:, 0] * 0.2)
        wig = np.abs(rng.normal(0, 0.0004, (days, MINUTES)))
        high = np.maximum(open_, close) * (1 + wig)
        low = np.minimum(open_, close) * (1 - wig)
        shape = 1.5 - np.sin(np.linspace(0, np.pi, MINUTES))     # U-shaped volume
        vol = rng.lognormal(8, 0.5, (days, MINUTES)) * shape
        out[f"S{k:02d}"] = Grid(idx, *(x.astype(np.float32) for x in (open_, high, low, close, vol)))
    return out
