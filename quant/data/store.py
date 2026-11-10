"""On-disk data layout and loaders. Every other module reads data through here.

Layout under the data root (default <repo>/data, override with QUANT_DATA):

  LOCK                      ISO date. Loaders drop every row after it unless
                            QUANT_UNLOCK_HOLDOUT=1. Protects the holdout period.
  cm/<field>.parquet        NSE cash market, daily, wide: index = date,
                            columns = symbol. Fields:
                              open high low close   adjusted for splits/bonuses
                              volume                shares, adjusted the same way
                              turnover              rupees traded (unadjusted)
                              factor                adjusted = raw * factor
                              eq                    True where the series is EQ
  index/<field>.parquet     NSE indices, daily, wide: columns = index name.
                            Fields: close, tri (total return, where available),
                            pe, pb, dy.
  fo/<SYMBOL>.parquet       Futures and options, daily, long. Columns: date,
                            instrument (FUT|OPT), expiry, strike, right
                            (CE|PE|""), open, high, low, close, settle,
                            contracts, oi, lot, underlying.
  intraday/<SYMBOL>_<interval>.parquet
                            Columns: ts, open, high, low, close, volume.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

import pandas as pd

CM_FIELDS = ("open", "high", "low", "close", "volume", "turnover", "factor", "eq")


def data_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(os.environ.get("QUANT_DATA", Path(__file__).resolve().parents[2] / "data"))


def lock_date(root: str | Path | None = None) -> pd.Timestamp | None:
    """Last date research code may see, or None if the holdout is unlocked."""
    if os.environ.get("QUANT_UNLOCK_HOLDOUT") == "1":
        return None
    f = data_root(root) / "LOCK"
    return pd.Timestamp(f.read_text().strip()) if f.exists() else None


def _clip(df: pd.DataFrame, start, end, root) -> pd.DataFrame:
    lock = lock_date(root)
    if lock is not None:
        end = lock if end is None else min(pd.Timestamp(end), lock)
    return df.loc[start:end]


@dataclass(frozen=True)
class Market:
    """Daily cash-market panel. All frames share the same index and columns."""
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame
    turnover: pd.DataFrame
    factor: pd.DataFrame
    eq: pd.DataFrame

    @property
    def dates(self) -> pd.DatetimeIndex:
        return self.close.index

    @property
    def symbols(self) -> pd.Index:
        return self.close.columns

    def raw(self, field: str = "close") -> pd.DataFrame:
        """Price as actually quoted on the day (not adjusted)."""
        return getattr(self, field) / self.factor

    def upto(self, date) -> "Market":
        """The panel as it was known at the close of `date`."""
        return replace(self, **{f: getattr(self, f).loc[:date] for f in CM_FIELDS})

    def window(self, start=None, end=None) -> "Market":
        return replace(self, **{f: getattr(self, f).loc[start:end] for f in CM_FIELDS})

    def select(self, symbols) -> "Market":
        cols = [s for s in symbols if s in self.close.columns]
        return replace(self, **{f: getattr(self, f)[cols] for f in CM_FIELDS})

    def liquidity_rank(self, window: int = 126, min_days: int = 60) -> pd.DataFrame:
        """Rank (1 = most traded) by trailing median daily turnover, using
        only data up to each day. Symbols not in the EQ series are unranked."""
        med = self.turnover.where(self.eq).rolling(window, min_periods=min_days).median()
        return med.rank(axis=1, ascending=False, method="first")


def load_market(start=None, end=None, symbols=None, root=None, subset: str = "cm") -> Market:
    d = data_root(root) / subset
    frames = {}
    for f in CM_FIELDS:
        df = pd.read_parquet(d / f"{f}.parquet", columns=list(symbols) if symbols is not None else None)
        df.index = pd.DatetimeIndex(df.index)
        frames[f] = _clip(df, start, end, root)
    frames["eq"] = frames["eq"].fillna(False).astype(bool)
    return Market(**frames)


def load_index(field: str = "close", start=None, end=None, root=None) -> pd.DataFrame:
    df = pd.read_parquet(data_root(root) / "index" / f"{field}.parquet")
    df.index = pd.DatetimeIndex(df.index)
    return _clip(df, start, end, root)


def load_fo(symbol: str, start=None, end=None, root=None) -> pd.DataFrame:
    df = pd.read_parquet(data_root(root) / "fo" / f"{symbol}.parquet")
    lock = lock_date(root)
    if lock is not None:
        end = lock if end is None else min(pd.Timestamp(end), lock)
    if start is not None:
        df = df[df["date"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["date"] <= pd.Timestamp(end)]
    return df.reset_index(drop=True)


def load_intraday(symbol: str, interval: str = "1min", start=None, end=None, root=None) -> pd.DataFrame:
    df = pd.read_parquet(data_root(root) / "intraday" / f"{symbol}_{interval}.parquet")
    lock = lock_date(root)
    if lock is not None:
        df = df[df["ts"] < lock + pd.Timedelta(days=1)]
    if start is not None:
        df = df[df["ts"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["ts"] < pd.Timestamp(end) + pd.Timedelta(days=1)]
    return df.reset_index(drop=True)
