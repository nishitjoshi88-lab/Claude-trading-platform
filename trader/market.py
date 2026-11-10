"""Market data containers.

A Panel holds hourly bars for every symbol on one shared time index:
spot close, perpetual-futures close, and the funding rate settled in that bar
(0 when no settlement happened). A MarketView is the panel as seen at one bar:
it can only return data up to and including that bar, so strategies cannot
look ahead.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

COLS = ("spot", "perp", "funding")
SPOT, PERP = 0, 1


class Panel:
    def __init__(self, index: pd.DatetimeIndex, symbols: list[str],
                 spot: np.ndarray, perp: np.ndarray, funding: np.ndarray):
        self.index, self.symbols = index, list(symbols)
        self.spot, self.perp, self.funding = spot, perp, funding

    def __len__(self) -> int:
        return len(self.index)

    @classmethod
    def from_frames(cls, frames: dict[str, pd.DataFrame]) -> "Panel":
        symbols = list(frames)
        index = pd.DatetimeIndex(sorted(set().union(*[f.index for f in frames.values()])))
        cols = {}
        for c in COLS:
            cols[c] = np.column_stack(
                [frames[s][c].reindex(index).to_numpy(dtype=float) for s in symbols])
        cols["funding"] = np.nan_to_num(cols["funding"], nan=0.0)
        return cls(index, symbols, cols["spot"], cols["perp"], cols["funding"])

    def frames(self) -> dict[str, pd.DataFrame]:
        return {s: pd.DataFrame({"spot": self.spot[:, j], "perp": self.perp[:, j],
                                 "funding": self.funding[:, j]}, index=self.index)
                for j, s in enumerate(self.symbols)}

    def view(self, i: int) -> "MarketView":
        return MarketView(self, i)


class MarketView:
    def __init__(self, panel: Panel, i: int):
        self._p, self.i = panel, i
        self.symbols = panel.symbols
        self.ts = panel.index[i]

    @property
    def n(self) -> int:
        return len(self.symbols)

    def prices(self) -> np.ndarray:
        """Current prices, shape (2, N): row 0 spot, row 1 perp."""
        return np.vstack([self._p.spot[self.i], self._p.perp[self.i]])

    def funding(self) -> np.ndarray:
        return self._p.funding[self.i]

    def window(self, col: str, bars: int) -> np.ndarray:
        """Last `bars` rows of a column, ending at the current bar."""
        a = getattr(self._p, col)
        return a[max(0, self.i - bars + 1): self.i + 1]


def save_frames(frames: dict[str, pd.DataFrame], directory: str | Path) -> None:
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    for s, f in frames.items():
        f.to_csv(d / f"{s}.csv", index_label="ts")


def load_frames(directory: str | Path, symbols: list[str] | None = None) -> dict[str, pd.DataFrame]:
    d = Path(directory)
    out = {}
    for p in sorted(d.glob("*.csv")):
        if symbols is not None and p.stem not in symbols:
            continue
        f = pd.read_csv(p, index_col="ts", parse_dates=True)
        if f.index.tz is not None:
            f.index = f.index.tz_convert(None)
        out[p.stem] = f[list(COLS)]
    if symbols is not None:
        out = {s: out[s] for s in symbols if s in out}
    return out


def synthetic_frames(symbols: list[str], bars: int = 24 * 365, seed: int = 0,
                     start: str = "2023-01-01") -> dict[str, pd.DataFrame]:
    """Random market for tests and smoke runs. Says nothing about real edge."""
    rng = np.random.default_rng(seed)
    index = pd.date_range(start, periods=bars, freq="h")
    regime = np.cumsum(rng.normal(0, 0.02, bars))
    drift = 0.00004 * np.sin(regime)                       # slow bull/bear cycles
    market = rng.normal(0, 0.006, bars) + drift
    frames = {}
    for k, s in enumerate(symbols):
        ret = (0.8 * market + rng.normal(0, 0.005, bars))
        spot = (100.0 * (k + 1)) * np.exp(np.cumsum(ret))
        heat = pd.Series(ret).rolling(72, min_periods=1).sum().to_numpy()
        rate8h = 0.0001 + 0.002 * heat + rng.normal(0, 0.00005, bars)
        funding = np.where(index.hour % 8 == 0, np.clip(rate8h, -0.003, 0.003), 0.0)
        perp = spot * (1 + 0.3 * rate8h + rng.normal(0, 0.0002, bars))
        frames[s] = pd.DataFrame({"spot": spot, "perp": perp, "funding": funding}, index=index)
    return frames
