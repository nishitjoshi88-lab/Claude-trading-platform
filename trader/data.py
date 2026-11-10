"""Data sources.

* download_history: bulk hourly history from Binance's public data archive
  (no account needed) for backtesting.
* ExchangeFeed: recent bars from a live exchange through ccxt, for the
  automated runner. Uses public endpoints only.
"""
from __future__ import annotations

import io
import time
import zipfile

import numpy as np
import pandas as pd
import requests

ARCHIVE = "https://data.binance.vision/data"


def _archive_csv(url: str) -> pd.DataFrame | None:
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                raw = z.read(z.namelist()[0]).decode()
            header = 0 if raw[:1].isalpha() else None
            return pd.read_csv(io.StringIO(raw), header=header)
        except (requests.RequestException, zipfile.BadZipFile):
            time.sleep(2 ** attempt)
    raise RuntimeError(f"could not download {url}")


def _to_ts(ms: pd.Series) -> pd.DatetimeIndex:
    v = ms.astype("int64").to_numpy()
    v = np.where(v > 10 ** 14, v // 1000, v)        # newer files use microseconds
    return pd.to_datetime(v, unit="ms")


def _closes(kind: str, pair: str, month: str) -> pd.Series | None:
    df = _archive_csv(f"{ARCHIVE}/{kind}/monthly/klines/{pair}/1h/{pair}-1h-{month}.zip")
    if df is None:
        return None
    return pd.Series(df.iloc[:, 4].to_numpy(dtype=float), index=_to_ts(df.iloc[:, 0]))


def _funding(pair: str, month: str) -> pd.Series | None:
    df = _archive_csv(f"{ARCHIVE}/futures/um/monthly/fundingRate/{pair}/{pair}-fundingRate-{month}.zip")
    if df is None:
        return None
    return pd.Series(df.iloc[:, -1].to_numpy(dtype=float), index=_to_ts(df.iloc[:, 0]).floor("h"))


def download_history(symbol: str, start: str, end: str, quote: str = "USDT") -> pd.DataFrame:
    """Hourly spot close, perp close and funding for [start, end] months (YYYY-MM)."""
    pair = f"{symbol}{quote}"
    spot, perp, fund = [], [], []
    for m in pd.period_range(start, end, freq="M").strftime("%Y-%m"):
        for kind, bucket in (("spot", spot), ("futures/um", perp)):
            s = _closes(kind, pair, m)
            if s is not None:
                bucket.append(s)
        f = _funding(pair, m)
        if f is not None:
            fund.append(f)
    if not spot or not perp:
        return pd.DataFrame(columns=["spot", "perp", "funding"])
    df = pd.DataFrame({"spot": pd.concat(spot), "perp": pd.concat(perp)})
    df = df[~df.index.duplicated()].sort_index()
    f = pd.concat(fund) if fund else pd.Series(dtype=float)
    f = f[~f.index.duplicated()]
    df["funding"] = f.reindex(df.index).fillna(0.0)
    return df.dropna(subset=["spot", "perp"], how="all")


class ExchangeFeed:
    """Closed hourly bars from a live exchange (public data, no keys)."""

    def __init__(self, exchange: str = "okx", quote: str = "USDT"):
        import ccxt
        # trust_env: honour the standard proxy and CA environment variables
        self.ex = getattr(ccxt, exchange)({"enableRateLimit": True, "requests_trust_env": True})
        self.quote = quote

    def _ohlcv(self, market: str, since: pd.Timestamp) -> pd.Series:
        ms, rows = int(since.timestamp() * 1000), []
        while True:
            batch = self.ex.fetch_ohlcv(market, "1h", since=ms, limit=100)
            batch = [b for b in batch if not rows or b[0] > rows[-1][0]]
            if not batch:
                break
            rows += batch
            ms = rows[-1][0] + 1
        if not rows:
            return pd.Series(dtype=float)
        a = np.array(rows, dtype=float)
        return pd.Series(a[:, 4], index=pd.to_datetime(a[:, 0], unit="ms"))

    def fetch(self, symbol: str, since: pd.Timestamp) -> pd.DataFrame:
        spot = self._ohlcv(f"{symbol}/{self.quote}", since)
        swap = f"{symbol}/{self.quote}:{self.quote}"
        perp = self._ohlcv(swap, since)
        df = pd.DataFrame({"spot": spot, "perp": perp})
        hist = self.ex.fetch_funding_rate_history(swap, since=int(since.timestamp() * 1000), limit=100)
        f = pd.Series({pd.to_datetime(h["timestamp"], unit="ms").floor("h"): h["fundingRate"] for h in hist},
                      dtype=float)
        df["funding"] = f.reindex(df.index).fillna(0.0)
        # drop the bar that is still forming
        now = pd.Timestamp.now("UTC").tz_localize(None)
        return df[df.index + pd.Timedelta(hours=1) <= now]
