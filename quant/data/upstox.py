"""One-minute bars from the Upstox public historical-candle endpoint.

The endpoint needs no login and serves one-minute candles for NSE stocks and
indices from January 2022 onward, one calendar month per request.

Intraday research has its own protected period, separate from the daily one:
the file <data>/INTRADAY_LOCK holds the last date research may see. The
downloader refuses to fetch past it and the loader drops later rows, unless
QUANT_UNLOCK_INTRADAY=1.

  python -m quant.data.upstox universe --asof 2021-12-31 --top 200
  python -m quant.data.upstox download --start 2022-01 --end 2024-12
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests

from .store import data_root

API = "https://api.upstox.com/v2/historical-candle/{key}/1minute/{to}/{frm}"
MASTER = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
BHAV = "https://archives.nseindia.com/content/historical/EQUITIES/{y}/{mon}/cm{d:02d}{mon}{y}bhav.csv.zip"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36", "Accept": "application/json"}
INDICES = {"NIFTY": "NSE_INDEX|Nifty 50", "BANKNIFTY": "NSE_INDEX|Nifty Bank", "INDIAVIX": "NSE_INDEX|India VIX"}
COLS = ["ts", "open", "high", "low", "close", "volume"]


def intraday_lock(root=None) -> pd.Timestamp | None:
    if os.environ.get("QUANT_UNLOCK_INTRADAY") == "1":
        return None
    f = data_root(root) / "INTRADAY_LOCK"
    return pd.Timestamp(f.read_text().strip()) if f.exists() else None


def _dir(root=None) -> Path:
    return data_root(root) / "intraday1m"


# --- universe ---------------------------------------------------------------
def _bhav(day: pd.Timestamp, root=None) -> pd.DataFrame | None:
    """Old-format daily bhavcopy, from the shared cache or the archive."""
    mon = day.strftime("%b").upper()
    cache = data_root(root) / "raw" / "cm" / "bhav" / str(day.year) / f"cm{day.day:02d}{mon}{day.year}bhav.csv.zip"
    if cache.exists():
        raw = cache.read_bytes()
    else:
        r = requests.get(BHAV.format(y=day.year, mon=mon, d=day.day), headers=HEADERS, timeout=40)
        if r.status_code != 200:
            return None
        raw = r.content
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return pd.read_csv(z.open(z.namelist()[0]))


def build_universe(asof: str, top: int = 200, sessions: int = 40, root=None) -> dict:
    """The `top` EQ-series stocks by median daily turnover over the last
    `sessions` trading days up to `asof`, using only data up to that date."""
    day, frames = pd.Timestamp(asof), []
    while len(frames) < sessions and day > pd.Timestamp(asof) - pd.Timedelta(days=120):
        if day.weekday() < 5:
            df = _bhav(day, root)
            if df is not None:
                frames.append(df[df["SERIES"] == "EQ"][["SYMBOL", "ISIN", "TOTTRDVAL"]].assign(date=day))
        day -= pd.Timedelta(days=1)
    allv = pd.concat(frames)
    med = allv.groupby("SYMBOL")["TOTTRDVAL"].median().sort_values(ascending=False)
    isin = allv.sort_values("date").groupby("SYMBOL")["ISIN"].last()
    master = json.load(gzip.open(io.BytesIO(requests.get(MASTER, headers=HEADERS, timeout=60).content)))
    by_isin = {m["isin"]: m for m in master if m.get("segment") == "NSE_EQ" and m.get("isin")}
    by_symbol = {m["trading_symbol"]: m for m in master
                 if m.get("segment") == "NSE_EQ" and m.get("instrument_type") == "EQ"}
    out, missing = {}, []
    for rank, sym in enumerate(med.index[:top], 1):
        m = by_isin.get(isin[sym]) or by_symbol.get(sym)
        if m is None:
            missing.append(sym)                       # merged, delisted or renamed since
            continue
        out[sym] = {"key": m["instrument_key"], "rank": rank, "now": m["trading_symbol"]}
    for sym, key in INDICES.items():
        out[sym] = {"key": key, "rank": 0, "now": sym}
    d = _dir(root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "universe.json").write_text(json.dumps(
        {"asof": asof, "sessions": len(frames), "top": top, "symbols": out, "missing": missing}, indent=1))
    return {"symbols": out, "missing": missing}


def load_universe(root=None) -> dict:
    return json.loads((_dir(root) / "universe.json").read_text())


# --- download ----------------------------------------------------------------
def fetch_month(key: str, month: pd.Period) -> pd.DataFrame:
    url = API.format(key=quote(key, safe=""), to=month.end_time.strftime("%Y-%m-%d"),
                     frm=month.start_time.strftime("%Y-%m-%d"))
    for attempt in range(6):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                candles = r.json().get("data", {}).get("candles", [])
                if not candles:
                    return pd.DataFrame(columns=COLS)
                a = pd.DataFrame(candles).iloc[:, :6]
                a.columns = COLS
                a["ts"] = pd.to_datetime(a["ts"].str.slice(0, 19))      # exchange local time (IST)
                return a.sort_values("ts").reset_index(drop=True)
            if r.status_code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"{r.status_code} {r.text[:200]}")
        except requests.RequestException:
            pass
        time.sleep(1.5 * 2 ** attempt)
    raise RuntimeError(f"gave up on {key} {month}")


def download(start: str, end: str, root=None, threads: int = 4, symbols: list[str] | None = None) -> dict:
    lock = intraday_lock(root)
    months = pd.period_range(start, end, freq="M")
    if lock is not None and months[-1].end_time.normalize() > lock:
        raise SystemExit(f"refusing to download past the intraday lock date {lock.date()}")
    uni = load_universe(root)["symbols"]
    names = symbols or list(uni)
    raw = data_root(root) / "raw" / "upstox"
    jobs = [(s, m) for s in names for m in months if not (raw / s / f"{m}.parquet").exists()]

    def one(job):
        s, m = job
        df = fetch_month(uni[s]["key"], m)
        (raw / s).mkdir(parents=True, exist_ok=True)
        df.to_parquet(raw / s / f"{m}.parquet")
        return len(df)

    done = 0
    with ThreadPoolExecutor(threads) as ex:
        for k, n in enumerate(ex.map(one, jobs), 1):
            done += n
            if k % 500 == 0:
                print(f"{k}/{len(jobs)} requests, {done:,} bars", flush=True)
    report = {}
    for s in names:
        parts = [pd.read_parquet(p) for p in sorted((raw / s).glob("*.parquet"))]
        parts = [p for p in parts if len(p)]
        if not parts:
            report[s] = 0
            continue
        df = pd.concat(parts).drop_duplicates("ts").sort_values("ts").reset_index(drop=True)
        for c in COLS[1:5]:
            df[c] = df[c].astype("float32")
        df["volume"] = df["volume"].astype("float64")
        df.to_parquet(_dir(root) / f"{s}.parquet")
        report[s] = len(df)
    return report


# --- loading -------------------------------------------------------------------
def load_bars(symbol: str, start=None, end=None, root=None) -> pd.DataFrame:
    """One-minute bars (ts is exchange local time), clipped to the lock date."""
    df = pd.read_parquet(_dir(root) / f"{symbol}.parquet")
    lock = intraday_lock(root)
    if lock is not None:
        df = df[df["ts"] < lock + pd.Timedelta(days=1)]
    if start is not None:
        df = df[df["ts"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["ts"] < pd.Timestamp(end) + pd.Timedelta(days=1)]
    return df.reset_index(drop=True)


def available(root=None) -> list[str]:
    return sorted(p.stem for p in _dir(root).glob("*.parquet"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="quant.data.upstox")
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("universe")
    u.add_argument("--asof", default="2021-12-31")
    u.add_argument("--top", type=int, default=200)
    d = sub.add_parser("download")
    d.add_argument("--start", required=True)
    d.add_argument("--end", required=True)
    d.add_argument("--threads", type=int, default=4)
    a = ap.parse_args(argv)
    if a.cmd == "universe":
        r = build_universe(a.asof, a.top)
        print(f"{len(r['symbols'])} instruments; not found at the broker: {r['missing']}")
    else:
        rep = download(a.start, a.end, threads=a.threads)
        counts = np.array(list(rep.values()))
        print(f"{len(rep)} symbols, {counts.sum():,} bars; empty: {[s for s, n in rep.items() if n == 0]}")


if __name__ == "__main__":
    main()
