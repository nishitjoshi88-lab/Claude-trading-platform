"""Minute-bar data arranged as a grid: one row per trading day, one column
per minute of the session (09:15 to 15:29, 375 columns).

Strategies read bars only through an `ICtx`. Cutting a context off at a
(day, minute) blanks everything after it, which is how the harness proves a
strategy does not use information from later in the day or from later days.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from ..data import upstox
from ..data.store import data_root

OPEN_MIN = 9 * 60 + 15
MINUTES = 375                      # 09:15 ... 15:29
FIELDS = ("open", "high", "low", "close", "volume")


def minute(hhmm: str) -> int:
    """Column index of a clock time, e.g. minute("09:30") == 15."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m) - OPEN_MIN


def clock(col: int) -> str:
    t = OPEN_MIN + col
    return f"{t // 60:02d}:{t % 60:02d}"


@dataclass(frozen=True)
class Grid:
    days: pd.DatetimeIndex
    open: np.ndarray               # each (len(days), 375), float32, NaN where no trade
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray

    def cut(self, day_i: int, col: int) -> "Grid":
        """Only what was known at the close of minute `col` on day `day_i`."""
        out = {}
        for f in FIELDS:
            a = getattr(self, f)[: day_i + 1].copy()
            a[day_i, col + 1:] = np.nan
            out[f] = a
        return Grid(self.days[: day_i + 1], **out)


def bars_to_grid(bars: pd.DataFrame, days: pd.DatetimeIndex) -> Grid:
    ts = pd.DatetimeIndex(bars["ts"])
    col = ts.hour * 60 + ts.minute - OPEN_MIN
    row = days.get_indexer(ts.normalize())
    ok = (col >= 0) & (col < MINUTES) & (row >= 0)
    out = {}
    for f in FIELDS:
        a = np.full((len(days), MINUTES), np.nan, dtype=np.float32)
        a[row[ok], col[ok]] = bars[f].to_numpy(dtype=np.float32)[ok]
        out[f] = a
    return Grid(days, **out)


def session_days(bars: pd.DataFrame, min_bars: int = 300) -> pd.DatetimeIndex:
    """Normal full sessions only (drops Muhurat and other short sessions)."""
    ts = pd.DatetimeIndex(bars["ts"])
    inside = (ts.hour * 60 + ts.minute >= OPEN_MIN) & (ts.hour * 60 + ts.minute < OPEN_MIN + MINUTES)
    counts = pd.Series(1, index=ts[inside].normalize()).groupby(level=0).sum()
    return pd.DatetimeIndex(counts[counts >= min_bars].index)


def build_grids(root=None, calendar_symbol: str = "NIFTY") -> dict:
    """Convert every downloaded symbol to a grid file. Returns bar counts."""
    days = session_days(upstox.load_bars(calendar_symbol, root=root))
    out_dir = data_root(root) / "intraday1m" / "grid"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.Series(days).to_frame("day").to_parquet(out_dir / "_days.parquet")
    report = {}
    for s in upstox.available(root):
        g = bars_to_grid(upstox.load_bars(s, root=root), days)
        np.savez_compressed(out_dir / f"{s}.npz", **{f: getattr(g, f) for f in FIELDS})
        report[s] = int(np.isfinite(g.close).sum())
    return report


@lru_cache(maxsize=64)
def _load(path: str) -> dict:
    with np.load(path) as z:
        return {f: z[f] for f in FIELDS}


class ICtx:
    """What an intraday strategy may look at."""

    def __init__(self, days: pd.DatetimeIndex, symbols: list[str], ranks: dict[str, int],
                 loader, cut: tuple[int, int] | None = None):
        self.days, self.symbols, self.ranks = days, list(symbols), ranks
        self._loader, self._cut = loader, cut
        self._cache: dict[str, Grid] = {}

    def grid(self, symbol: str) -> Grid:
        """Bars for a stock or for "NIFTY", "BANKNIFTY", "INDIAVIX"."""
        if symbol not in self._cache:
            g = self._loader(symbol)
            if self._cut is not None:
                g = g.cut(*self._cut)
            if len(self._cache) > 40:
                self._cache.pop(next(iter(self._cache)))
            self._cache[symbol] = g
        return self._cache[symbol]

    def subset(self, symbols: list[str]) -> "ICtx":
        return ICtx(self.days, symbols, self.ranks, self._loader, self._cut)

    def cut(self, day_i: int, col: int) -> "ICtx":
        return ICtx(self.days[: day_i + 1], self.symbols, self.ranks, self._loader, (day_i, col))

    def day_slice(self, start=None, end=None) -> tuple[int, int]:
        a = int(self.days.searchsorted(pd.Timestamp(start))) if start is not None else 0
        b = int(self.days.searchsorted(pd.Timestamp(end), side="right")) if end is not None else len(self.days)
        return a, b


def load_ictx(root=None, max_rank: int | None = None) -> ICtx:
    """Context over the downloaded universe (stocks only in `symbols`;
    indices are available through ctx.grid)."""
    d = data_root(root) / "intraday1m"
    days = pd.DatetimeIndex(pd.read_parquet(d / "grid" / "_days.parquet")["day"])
    uni = upstox.load_universe(root)["symbols"]
    have = {p.stem for p in (d / "grid").glob("*.npz")}
    ranks = {s: v["rank"] for s, v in uni.items() if s in have}
    symbols = sorted((s for s, r in ranks.items() if r > 0 and (max_rank is None or r <= max_rank)),
                     key=lambda s: ranks[s])

    def loader(symbol: str) -> Grid:
        return Grid(days, **_load(str(d / "grid" / f"{symbol}.npz")))

    return ICtx(days, symbols, ranks, loader)


def ictx_from_grids(grids: dict[str, Grid], ranks: dict[str, int] | None = None) -> ICtx:
    """Context over in-memory grids (tests)."""
    days = next(iter(grids.values())).days
    ranks = ranks or {s: k + 1 for k, s in enumerate(grids)}
    stocks = [s for s in grids if s not in ("NIFTY", "BANKNIFTY", "INDIAVIX")]
    return ICtx(days, stocks, ranks, lambda s: grids[s])
