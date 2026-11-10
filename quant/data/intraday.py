"""Free intraday history for Indian markets: download, normalise, split, validate.

Everything here works from files that anybody can download without an account.
Nothing is interpolated or synthesised: a bar exists in the output only if a
source file contains it.

Command line (run from the repository root)::

    python -m quant.data.intraday fetch            # download raw files (incremental)
    python -m quant.data.intraday build            # raw cache -> data/intraday + data/holdout/intraday
    python -m quant.data.intraday validate         # quality report on the research part only
    python -m quant.data.intraday all              # the three steps in order

    common options:  --root DATA_ROOT  --start YYYY-MM-DD  --end YYYY-MM-DD
                     --only SOURCE[,SOURCE]  --symbols SYM[,SYM]

``--end`` is the last research date (default: the date in <root>/LOCK, else
2021-12-31).  Rows dated after it are written, unseen, to
<root>/holdout/intraday/ with the same file names.  To extend the research
range later, re-run ``build`` with a later ``--end`` (and ``fetch`` first if
the upstream files have grown).

Output layout (see quant/data/store.py, ``load_intraday``)::

    <root>/intraday/<SYMBOL>_<interval>.parquet   ts, open, high, low, close, volume
    <root>/intraday/options/<UNDERLYING>_<interval>/<EXPIRY>.parquet
                                                  ts, expiry, strike, right, open,
                                                  high, low, close, volume, oi
    <root>/intraday/manifest.json                 what was built, from which source
    <root>/intraday/quality.json                  output of ``validate``

``ts`` is the bar START time in IST, timezone-naive.  Prices are float32.
``volume`` is float32 and NaN where the source carries no volume (all spot
indices, and stock bars that come from the volume-less mirror).

The module is self-contained on purpose (no imports from the rest of the
package) so it can also be run as ``python -I quant/data/intraday.py ...``.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Iterator
from urllib.parse import quote

import numpy as np
import pandas as pd

DEFAULT_END = "2021-12-31"
COLS = ["ts", "open", "high", "low", "close", "volume"]
OPT_COLS = ["ts", "expiry", "strike", "right", "open", "high", "low", "close", "volume", "oi"]
SESSION_OPEN = pd.Timedelta(hours=9, minutes=15)
SESSION_CLOSE = pd.Timedelta(hours=15, minutes=30)      # last 1-min bar starts 15:29
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36")
MAX_WORKERS = 6


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------

def data_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(os.environ.get("QUANT_DATA", Path(__file__).resolve().parents[2] / "data"))


def default_end(root: Path) -> pd.Timestamp:
    f = root / "LOCK"
    return pd.Timestamp(f.read_text().strip() if f.exists() else DEFAULT_END)


def raw_dir(root: Path, source: str) -> Path:
    return root / "raw" / "intraday" / source


# --------------------------------------------------------------------------
# downloading
# --------------------------------------------------------------------------

_tls = threading.local()


def _session():
    import requests
    s = getattr(_tls, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Accept": "*/*"})
        _tls.s = s
    return s


def http_get(url: str, *, stream: bool = False, tries: int = 6, timeout: int = 120, headers=None):
    """GET with exponential backoff on network errors, 429 and 5xx."""
    import requests
    delay = 2.0
    last = None
    for attempt in range(tries):
        try:
            r = _session().get(url, stream=stream, timeout=timeout, headers=headers, allow_redirects=True)
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                r.close()
            else:
                return r
        except requests.RequestException as e:          # connection reset, timeout ...
            last = f"{type(e).__name__}: {e}"
        time.sleep(delay)
        delay = min(delay * 2, 60)
    raise IOError(f"GET failed after {tries} tries: {url} ({last})")


def download(url: str, dest: Path, expect_size: int | None = None) -> str:
    """Download to `dest` atomically. Returns 'cached', 'ok' or raises."""
    if dest.exists() and dest.stat().st_size > 0 and (expect_size is None or dest.stat().st_size == expect_size):
        return "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    for attempt in range(4):
        r = http_get(url, stream=True)
        if r.status_code != 200:
            r.close()
            raise IOError(f"HTTP {r.status_code} for {url}")
        n = 0
        try:
            with open(part, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
                    n += len(chunk)
        except Exception:                                # truncated transfer: retry
            time.sleep(3 * (attempt + 1))
            continue
        finally:
            r.close()
        want = expect_size if expect_size is not None else int(r.headers.get("Content-Length") or n)
        if r.headers.get("Content-Encoding"):            # length header is of the encoded body
            want = expect_size if expect_size is not None else n
        if n == want and n > 0:
            os.replace(part, dest)
            return "ok"
        time.sleep(3 * (attempt + 1))
    raise IOError(f"size mismatch for {url}")


def github_listing(repo: str, cache: Path, refresh: bool = False) -> dict:
    """File listing of a public GitHub repository: {'branch':..., 'files': [[path, size], ...]}.

    api.github.com is not usable anonymously from every network, so the
    listing comes from the ungh.cc mirror of the GitHub tree API (fallback:
    jsDelivr's data API) and is cached next to the raw files.  File contents
    always come from raw.githubusercontent.com itself.
    """
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    out = None
    for br in ("main", "master"):
        try:
            r = http_get(f"https://ungh.cc/repos/{repo}/files/{br}", tries=3)
            if r.status_code == 200 and r.json().get("files"):
                out = {"repo": repo, "branch": br, "via": "ungh.cc",
                       "files": [[f["path"], int(f.get("size") or 0)] for f in r.json()["files"]]}
                break
        except Exception:
            pass
        try:
            r = http_get(f"https://data.jsdelivr.com/v1/packages/gh/{repo}@{br}?structure=flat", tries=3)
            if r.status_code == 200 and r.json().get("files"):
                out = {"repo": repo, "branch": br, "via": "data.jsdelivr.com",
                       "files": [[f["name"].lstrip("/"), int(f.get("size") or 0)] for f in r.json()["files"]]}
                break
        except Exception:
            pass
    if out is None:
        raise IOError(f"could not list {repo}")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out))
    return out


def hf_listing(dataset: str, cache: Path, refresh: bool = False) -> dict:
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    r = http_get(f"https://huggingface.co/api/datasets/{dataset}?blobs=true")
    if r.status_code != 200:
        raise IOError(f"HTTP {r.status_code} listing {dataset}")
    j = r.json()
    out = {"repo": dataset, "branch": "main", "via": "huggingface.co/api", "sha": j.get("sha"),
           "license": (j.get("cardData") or {}).get("license"),
           "files": [[s["rfilename"], int(s.get("size") or 0)] for s in j.get("siblings", [])]}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out))
    return out


def github_raw_url(repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{quote(path)}"


def hf_url(dataset: str, path: str) -> str:
    return f"https://huggingface.co/datasets/{dataset}/resolve/main/{quote(path)}"


class HttpRangeFile:
    """Minimal read-only seekable file over HTTP range requests (for parquet footers)."""

    def __init__(self, url: str):
        r = http_get(url, headers={"Range": "bytes=0-0"})
        if r.status_code not in (200, 206):
            raise IOError(f"HTTP {r.status_code} for {url}")
        self.url = r.url
        self.size = int(r.headers["Content-Range"].split("/")[1])
        self.pos = 0
        self.closed = False

    def seekable(self): return True
    def readable(self): return True
    def writable(self): return False
    def tell(self): return self.pos
    def close(self): self.closed = True
    def flush(self): pass

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.pos + n, self.size) - 1
        r = http_get(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        b = r.content
        self.pos += len(b)
        return b


def run_downloads(jobs: list[tuple[str, Path, int | None]], label: str) -> dict:
    """jobs: (url, dest, expected_size). At most MAX_WORKERS concurrent."""
    stats = {"ok": 0, "cached": 0, "failed": []}
    if not jobs:
        return stats
    t0 = time.time()
    with cf.ThreadPoolExecutor(MAX_WORKERS) as ex:
        futs = {ex.submit(download, u, d, s): (u, d) for u, d, s in jobs}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            u, d = futs[fut]
            try:
                stats[fut.result()] += 1
            except Exception as e:
                stats["failed"].append([u, str(e)[:200]])
            if i % 200 == 0 or i == len(jobs):
                print(f"  [{label}] {i}/{len(jobs)} files ({stats['ok']} new, {stats['cached']} cached, "
                      f"{len(stats['failed'])} failed) {time.time() - t0:.0f}s", flush=True)
    return stats


# --------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------

@dataclass
class Source:
    name: str
    kind: str                     # 'github' | 'hf'
    repo: str
    url: str
    licence: str
    timezone: str
    note: str
    select: Callable[[list, pd.Timestamp], list] = field(repr=False, default=None)


_AERON_NAMES = re.compile(r"^(NIFTY|BANKNIFTY|NIFTY_F1|BANKNIFTY_F1|NIFTY_F2|BANKNIFTY_F2|INDIAVIX)\.txt$")


def _sel_aeron(files, end):
    out = []
    for p, s in files:
        year = p.split("/")[0]
        if not year.isdigit() or pd.Timestamp(f"{year}-01-01") > end:
            continue
        if _AERON_NAMES.match(p.rsplit("/", 1)[-1]):
            out.append((p, s))
    return out


def _sel_akshaj(files, end):
    keep = {"multi_index_strategy/data/NIFTY_50_minute_data.csv",
            "multi_index_strategy/data/NIFTY_BANK_minute_data.csv"}
    return [(p, s) for p, s in files
            if p in keep or (p.startswith("Nifty 100 stocks/Data/") and p.endswith("_minute.csv"))]


def _sel_technovus(files, end):
    out = []
    for p, s in files:
        m = re.match(r"^1min/(\d{4})/NIFTY50_1min_(\d{4})(-\d\d)?\.csv$", p)
        if m and pd.Timestamp(f"{m.group(2)}-01-01") <= end:        # skip files that start after `end`
            out.append((p, s))
    return out


def _sel_trademarkk(files, end):
    """Index files plus NIFTY/BANKNIFTY option files that can contain rows up to `end`.

    Each option file holds roughly the last two weeks before its expiry, so
    files expiring more than 45 days after `end` are not downloaded at all.
    """
    out = []
    for p, s in files:
        if p in ("index/NIFTY.parquet", "index/BANKNIFTY.parquet"):
            out.append((p, s))
            continue
        m = re.match(r"^options/(NIFTY|BANKNIFTY)/(\d{4}-\d\d-\d\d)\.parquet$", p)
        if m and pd.Timestamp(m.group(2)) <= end + pd.Timedelta(days=45):
            out.append((p, s))
    return out


SOURCES: dict[str, Source] = {s.name: s for s in [
    Source("gh_akshaj23", "github", "akshaj23/INTRADAY-PAIR-TRADING-NIFTY-100-STOCKS",
           "https://github.com/akshaj23/INTRADAY-PAIR-TRADING-NIFTY-100-STOCKS",
           "none stated in the repository (files are a copy of the Kaggle 'Nifty 100 minute data' "
           "series by debashis74017; Kaggle itself could not be reached anonymously to read its licence)",
           "IST, timezone-naive strings, bar start time",
           "1-min OHLCV for NIFTY 50, NIFTY BANK, INDIA VIX and 85 large-cap stocks, Feb 2015 onward",
           _sel_akshaj),
    Source("hf_tiru8055", "hf", "Tiru8055/NSE_top100_OHLC_1min_tf",
           "https://huggingface.co/datasets/Tiru8055/NSE_top100_OHLC_1min_tf",
           "none stated on the dataset card",
           "IST with explicit +05:30 offset in the string, bar start time",
           "1-min OHLC (no volume) for 99 large-cap stocks + NIFTY 50 + NIFTY BANK, 2015 onward",
           lambda files, end: [(p, s) for p, s in files if p.startswith("data/") and p.endswith(".parquet")]),
    Source("gh_sandeepkapri_nifty", "github", "sandeepkapri/Nifty50-Minute-Data",
           "https://github.com/sandeepkapri/Nifty50-Minute-Data", "MIT",
           "IST, separate date and time columns, bar start time",
           "NIFTY 50 1-min OHLC from 2015-01-09",
           lambda files, end: [(p, s) for p, s in files if p == "nifty50_candlestick_data.csv"]),
    Source("gh_sandeepkapri_banknifty", "github", "sandeepkapri/BankNifty-Data",
           "https://github.com/sandeepkapri/BankNifty-Data", "MIT",
           "IST, separate date and time columns, bar start time",
           "NIFTY BANK 1-min OHLC from 2015-01-09",
           lambda files, end: [(p, s) for p, s in files if p == "bank-nifty-1m-data.csv"]),
    Source("gh_technovusin", "github", "technovusin/nifty50-historical-data",
           "https://github.com/technovusin/nifty50-historical-data", "MIT",
           "IST (ISO timestamp column) plus a Unix epoch column, bar start time",
           "NIFTY 50 1-min OHLC from 2017-04-03, one file per year",
           _sel_technovus),
    Source("gh_aeron7", "github", "aeron7/nifty-banknifty-intraday-data",
           "https://github.com/aeron7/nifty-banknifty-intraday-data",
           "none stated in the repository",
           "IST, YYYYMMDD and HH:MM columns; the HH:MM label is the bar END time (see README)",
           "1-min bars 2012-2018: NIFTY, BANKNIFTY, INDIAVIX, continuous front/next month futures "
           "NIFTY_F1/F2, BANKNIFTY_F1/F2 with volume and open interest",
           _sel_aeron),
    Source("hf_thetrademarkk", "hf", "thetrademarkk/india-index-options-1m",
           "https://huggingface.co/datasets/thetrademarkk/india-index-options-1m", "CC-BY-NC-4.0",
           "timezone-aware IST (+05:30), bar start time",
           "1-min NIFTY/BANKNIFTY spot from 2021-05-24 and option chains (last days before each expiry)",
           _sel_trademarkk),
]}


def source_listing(src: Source, root: Path, refresh: bool = False) -> dict:
    cache = raw_dir(root, src.name) / "_listing.json"
    return github_listing(src.repo, cache, refresh) if src.kind == "github" else hf_listing(src.repo, cache, refresh)


def selected_files(src: Source, root: Path, end: pd.Timestamp, refresh: bool = False) -> tuple[dict, list]:
    lst = source_listing(src, root, refresh)
    return lst, src.select([tuple(f) for f in lst["files"]], end)


def fetch(root: Path, end: pd.Timestamp, only: Iterable[str] | None = None, refresh: bool = False) -> dict:
    """Download every selected raw file that is not already cached."""
    report = {}
    for name, src in SOURCES.items():
        if only and name not in only:
            continue
        lst, files = selected_files(src, root, end, refresh)
        base = raw_dir(root, name)
        jobs = []
        for p, s in files:
            url = github_raw_url(src.repo, lst["branch"], p) if src.kind == "github" else hf_url(src.repo, p)
            jobs.append((url, base / p, s or None))
        print(f"[{name}] {len(jobs)} files, {sum(s or 0 for _, _, s in jobs) / 1e6:.0f} MB", flush=True)
        st = run_downloads(jobs, name)
        report[name] = {"files": len(jobs), **st}
        (base / "_fetch.json").write_text(json.dumps(
            {"source": src.url, "licence": src.licence, "fetched_utc": pd.Timestamp.now("UTC").isoformat(),
             "end": str(end.date()), "files": len(jobs), "new": st["ok"], "cached": st["cached"],
             "failed": st["failed"]}, indent=1))
    return report


# --------------------------------------------------------------------------
# parsing: every parser returns a frame with COLS (ts = bar start, IST naive)
# --------------------------------------------------------------------------

def _finish(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce column order and dtypes. Does not sort or drop anything."""
    out = pd.DataFrame({"ts": pd.DatetimeIndex(df["ts"]).as_unit("ns")})
    for c in ("open", "high", "low", "close"):
        out[c] = pd.to_numeric(df[c].to_numpy(), errors="coerce").astype("float32")
    if "volume" in df.columns:
        out["volume"] = pd.to_numeric(df["volume"].to_numpy(), errors="coerce").astype("float32")
    else:
        out["volume"] = np.float32("nan")
    for c in df.columns:                       # extra columns (oi, expiry ...) pass through
        if c not in out.columns:
            out[c] = df[c].to_numpy()
    return out


def _parse_dt(text: pd.Series, formats: list[str]) -> pd.DatetimeIndex:
    """Parse with the first format; rows that fail are retried with the next ones.
    Raises if anything is left unparsed (never guesses)."""
    ts = pd.to_datetime(text, format=formats[0], errors="coerce")
    for fmt in formats[1:]:
        bad = ts.isna()
        if not bad.any():
            break
        ts[bad] = pd.to_datetime(text[bad], format=fmt, errors="coerce")
    n_bad = int(ts.isna().sum())
    if n_bad:
        raise ValueError(f"{n_bad} timestamps could not be parsed with {formats}")
    return pd.DatetimeIndex(ts)


def parse_akshaj(path) -> pd.DataFrame:
    """date,open,high,low,close,volume  ('2015-02-02 09:15:00', IST, bar start)."""
    df = pd.read_csv(path, dtype={"open": "float64", "high": "float64", "low": "float64",
                                  "close": "float64", "volume": "float64"})
    df.columns = [c.strip().lower() for c in df.columns]
    df["ts"] = _parse_dt(df["date"].astype(str).str.slice(0, 19), ["%Y-%m-%d %H:%M:%S"])
    return _finish(df[["ts", "open", "high", "low", "close", "volume"]])


def parse_sandeepkapri(path) -> pd.DataFrame:
    """Instrument,Date,Time,Open,High,Low,Close  ('09-01-2015','9:15:00', IST, bar start)."""
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]
    text = df["date"].str.strip() + " " + df["time"].str.strip()
    df["ts"] = _parse_dt(text, ["%d-%m-%Y %H:%M:%S", "%d-%m-%y %H:%M:%S", "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S"])
    return _finish(df[["ts", "open", "high", "low", "close"]])


def parse_technovus(path) -> pd.DataFrame:
    """Epoch,Timestamp,Open,High,Low,Close[,Volume]  (Timestamp is IST ISO-8601, bar start)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df["ts"] = _parse_dt(df["timestamp"].astype(str), ["%Y-%m-%dT%H:%M:%S"])
    # the epoch column must agree with the IST wall clock (UTC + 05:30)
    wall = pd.to_datetime(df["epoch"].astype("int64") + 19800, unit="s")
    if not (wall.to_numpy() == df["ts"].to_numpy()).all():
        raise ValueError(f"{path}: Epoch and Timestamp columns disagree")
    cols = ["ts", "open", "high", "low", "close"] + (["volume"] if "volume" in df.columns else [])
    return _finish(df[cols])


def parse_aeron(path_or_buf) -> pd.DataFrame:
    """SYMBOL,YYYYMMDD,HH:MM,O,H,L,C[,VOLUME[,OI]] without header.

    The HH:MM label is the END of the minute (a full session runs 09:16 ..
    15:30), so one minute is subtracted to get the bar start.
    Returns COLS + 'oi' (NaN when the file has no such column)."""
    df = pd.read_csv(path_or_buf, header=None, names=["symbol", "d", "t", "open", "high", "low", "close", "volume", "oi"],
                     dtype={"symbol": str, "d": str, "t": str}, skip_blank_lines=True, on_bad_lines="error")
    if df.empty:
        return _finish(pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume", "oi"]))
    df["ts"] = _parse_dt(df["d"].str.strip() + " " + df["t"].str.strip(), ["%Y%m%d %H:%M", "%Y%m%d %H:%M:%S"]) \
        - pd.Timedelta(minutes=1)
    out = _finish(df[["ts", "open", "high", "low", "close", "volume", "oi"]])
    out["oi"] = pd.to_numeric(out["oi"], errors="coerce").astype("float32")
    return out


def parse_trademarkk_index(path) -> pd.DataFrame:
    """timestamp (tz-aware IST), open, high, low, close, volume, trading_day, symbol."""
    df = pd.read_parquet(path, columns=["timestamp", "open", "high", "low", "close", "volume"])
    ts = df["timestamp"]
    if ts.dt.tz is None:
        raise ValueError(f"{path}: expected timezone-aware timestamps")
    df["ts"] = ts.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    return _finish(df[["ts", "open", "high", "low", "close", "volume"]])


def parse_trademarkk_options(path) -> pd.DataFrame:
    """One expiry file -> OPT_COLS (ts bar start IST naive; right in {'CE','PE'})."""
    df = pd.read_parquet(path)
    ts = df["timestamp"]
    if ts.dt.tz is None:
        raise ValueError(f"{path}: expected timezone-aware timestamps")
    out = pd.DataFrame({
        "ts": pd.DatetimeIndex(ts.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)).as_unit("ns"),
        "expiry": pd.DatetimeIndex(pd.to_datetime(df["expiry"], format="%Y-%m-%d")).as_unit("ns"),
        "strike": df["strike"].astype("float32").to_numpy(),
        "right": df["option_type"].astype(str).str.upper().to_numpy(),
    })
    for c in ("open", "high", "low", "close", "volume"):
        out[c] = df[c].astype("float32").to_numpy()
    out["oi"] = df["open_interest"].astype("float32").to_numpy()
    return out[OPT_COLS]


def iter_tiru(paths: list[Path]) -> Iterator[tuple[str, pd.DataFrame]]:
    """Stream the long-format shards and yield (stock_name, frame) one symbol at a time.

    Rows are grouped by stock_name inside the shards (a symbol may straddle two
    shards), so only one shard plus one pending symbol is held in memory."""
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    pending_name, pending = None, []
    for path in sorted(paths):
        tbl = pq.read_table(path, columns=["stock_name", "date", "open", "high", "low", "close"])
        date = tbl["date"]
        if not pc.all(pc.ends_with(date, "+05:30")).as_py():
            raise ValueError(f"{path}: timestamps without the +05:30 offset")
        ts = pc.strptime(pc.utf8_slice_codeunits(date, 0, 19), format="%Y-%m-%d %H:%M:%S", unit="s")
        names = tbl["stock_name"].combine_chunks().dictionary_encode()
        codes = names.indices.to_numpy(zero_copy_only=False)
        labels = names.dictionary.to_pylist()
        frame = pd.DataFrame({
            "ts": pd.DatetimeIndex(ts.to_numpy(zero_copy_only=False)).as_unit("ns"),
            "open": tbl["open"].to_numpy().astype("float32"), "high": tbl["high"].to_numpy().astype("float32"),
            "low": tbl["low"].to_numpy().astype("float32"), "close": tbl["close"].to_numpy().astype("float32"),
        })
        del tbl, date, ts
        # contiguous runs of the same code
        cut = np.flatnonzero(np.diff(codes)) + 1
        starts = np.concatenate([[0], cut])
        stops = np.concatenate([cut, [len(codes)]])
        for a, b in zip(starts, stops):
            name = labels[codes[a]]
            if pending_name is not None and name != pending_name:
                yield pending_name, _finish(pd.concat(pending, ignore_index=True))
                pending = []
            pending_name = name
            pending.append(frame.iloc[a:b])
    if pending_name is not None:
        yield pending_name, _finish(pd.concat(pending, ignore_index=True))


# --------------------------------------------------------------------------
# cleaning and splitting (pure functions, unit-tested)
# --------------------------------------------------------------------------

def clean_bars(df: pd.DataFrame, interval_minutes: int = 1, session_only: bool = True) -> tuple[pd.DataFrame, dict]:
    """Sort, drop exact and timestamp duplicates, drop impossible bars.

    Rules (each one only removes rows, nothing is ever filled in):
      * rows with a missing or non-positive O/H/L/C are dropped;
      * rows where high < low are dropped;
      * duplicate timestamps keep the first occurrence in source order;
      * with session_only, bars starting outside 09:15 <= t < 15:30 IST are
        dropped (Muhurat and other special evening sessions go with them)
        and counted in the returned statistics.  Weekend dates are kept: NSE
        held regular Saturday sessions on budget days (2015-02-28, 2020-02-01).
    """
    st = {"rows_in": int(len(df))}
    px = df[["open", "high", "low", "close"]]
    bad = px.isna().any(axis=1) | (px <= 0).any(axis=1)
    st["dropped_bad_price"] = int(bad.sum())
    inv = (~bad) & (df["high"] < df["low"])
    st["dropped_high_below_low"] = int(inv.sum())
    df = df[~(bad | inv)]
    dup = df["ts"].duplicated(keep="first")
    st["dropped_duplicate_ts"] = int(dup.sum())
    df = df[~dup]
    unsorted = not df["ts"].is_monotonic_increasing
    st["was_out_of_order"] = bool(unsorted)
    if unsorted:
        df = df.sort_values("ts", kind="stable")
    if session_only:
        tod = df["ts"] - df["ts"].dt.normalize()
        out = (tod < SESSION_OPEN) | (tod >= SESSION_CLOSE)
        st["dropped_outside_session"] = int(out.sum())
        df = df[~out]
    # OHLC envelope: count (do not alter) bars whose open/close fall outside [low, high]
    env = (df["open"] > df["high"]) | (df["open"] < df["low"]) | (df["close"] > df["high"]) | (df["close"] < df["low"])
    st["bars_open_or_close_outside_range"] = int(env.sum())
    st["rows_out"] = int(len(df))
    return df.reset_index(drop=True), st


def split_holdout(df: pd.DataFrame, end, start=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(research, holdout): research has start <= ts.date <= end, holdout has ts.date > end.
    Purely mechanical; the holdout part is never inspected by the caller."""
    cut = pd.Timestamp(end).normalize() + pd.Timedelta(days=1)
    research = df[df["ts"] < cut]
    if start is not None:
        research = research[research["ts"] >= pd.Timestamp(start).normalize()]
    return research.reset_index(drop=True), df[df["ts"] >= cut].reset_index(drop=True)


def resample_bars(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Aggregate 1-min bars into `minutes`-min bars anchored at the 09:15 open.
    Buckets with no source bar do not appear in the result."""
    if df.empty:
        return df.copy()
    day = df["ts"].dt.normalize()
    off = ((df["ts"] - day - SESSION_OPEN) // pd.Timedelta(minutes=minutes)) * pd.Timedelta(minutes=minutes)
    key = day + SESSION_OPEN + off
    g = df.groupby(key, sort=True)
    out = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                        "close": g["close"].last(), "volume": g["volume"].sum(min_count=1)})
    out.index.name = "ts"
    return out.reset_index().astype({c: "float32" for c in ("open", "high", "low", "close", "volume")})


def floor_to_minute(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Timestamps with stray seconds (09:20:01) are relabelled to their minute.
    Returns the frame and the number of rows that were relabelled."""
    sec = df["ts"].dt.second.to_numpy() != 0
    n = int(sec.sum())
    if n:
        df = df.copy()
        df["ts"] = df["ts"].dt.floor("min")
    return df, n


def drop_misfiled_blocks(df: pd.DataFrame, max_ratio: float, window: str = "9D") -> tuple[pd.DataFrame, dict]:
    """Remove bars that sit at a completely different price level from the
    surrounding days (another instrument's rows filed under this symbol).

    Reference level = centred rolling median (calendar window) of the daily
    median close.  A bar is dropped when close/reference is above `max_ratio`
    or below 1/max_ratio.  Use a ratio no market move can reach in the period
    (1.2 for index and index futures, 3.0 for India VIX)."""
    if df.empty:
        return df, {"dropped_misfiled": 0, "misfiled_days": []}
    day = df["ts"].dt.normalize()
    daily = df.groupby(day)["close"].median()
    ref = daily.rolling(window, center=True, min_periods=1).median()
    r = df["close"].to_numpy(dtype="float64") / ref.reindex(day).to_numpy(dtype="float64")
    bad = (r > max_ratio) | (r < 1.0 / max_ratio)
    days = sorted({str(d.date()) for d in day[bad].unique()})
    return df[~bad].reset_index(drop=True), {"dropped_misfiled": int(bad.sum()), "misfiled_days": days}


def normalise(df: pd.DataFrame, misfiled_ratio: float | None = None) -> tuple[pd.DataFrame, dict]:
    df, n_floor = floor_to_minute(df)
    df, st = clean_bars(df)
    st["relabelled_stray_seconds"] = n_floor
    if misfiled_ratio is not None:
        df, st2 = drop_misfiled_blocks(df, misfiled_ratio)
        st.update(st2)
        st["rows_out"] = int(len(df))
    return df, st


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

INDEX_PLAN = {
    # symbol: (official index name, aeron7 file stem, primary source, path inside source, parser)
    "NIFTY": ("NIFTY 50", "NIFTY", "gh_sandeepkapri_nifty", "nifty50_candlestick_data.csv", parse_sandeepkapri),
    "BANKNIFTY": ("NIFTY BANK", "BANKNIFTY", "gh_sandeepkapri_banknifty", "bank-nifty-1m-data.csv", parse_sandeepkapri),
    "INDIAVIX": ("INDIA VIX", "INDIAVIX", "gh_akshaj23", "Nifty 100 stocks/Data/INDIA VIX_minute.csv", parse_akshaj),
}
FUT_PLAN = {"NIFTY_FUT1": "NIFTY_F1", "NIFTY_FUT2": "NIFTY_F2",
            "BANKNIFTY_FUT1": "BANKNIFTY_F1", "BANKNIFTY_FUT2": "BANKNIFTY_F2"}
MISFILED_RATIO = {"INDIAVIX": 3.0}                    # default 1.2 for index levels and index futures
TIRU_ALIAS = {"MM": "M&M", "LTI": "LTIM"}             # same company, name used by the other source / NSE
TIRU_SKIP = {"NIFTY 50", "NIFTY BANK"}                # indices come from the primary index sources
AKSHAJ_STOCK_DIR = "Nifty 100 stocks/Data"


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    df.to_parquet(tmp, index=False, compression="zstd")
    os.replace(tmp, path)


def _span(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"rows": 0}
    return {"rows": int(len(df)), "first": str(df["ts"].iloc[0]), "last": str(df["ts"].iloc[-1]),
            "days": int(df["ts"].dt.normalize().nunique())}


def write_split(df: pd.DataFrame, rel: str, root: Path, start, end) -> dict:
    """Split at `end` and write <root>/intraday/<rel> and <root>/holdout/intraday/<rel>.
    Only the row count and first/last timestamp of the holdout part are computed."""
    research, holdout = split_holdout(df, end, start)
    r_path, h_path = root / "intraday" / rel, root / "holdout" / "intraday" / rel
    info = {"research": _span(research),
            "holdout": {"rows": int(len(holdout)),
                        **({"first": str(holdout["ts"].min()), "last": str(holdout["ts"].max())} if len(holdout) else {})}}
    for part, path in ((research, r_path), (holdout, h_path)):
        if len(part):
            _write_parquet(part, path)
        elif path.exists():
            path.unlink()
    return info


def load_aeron_symbol(root: Path, stem: str, end: pd.Timestamp) -> tuple[pd.DataFrame, dict]:
    """All cached aeron7 files called <stem>.txt, concatenated in a fixed order.
    Monthly and daily files come first; the 2018 whole-year dump last, so that
    the monthly/daily files win where both contain a bar."""
    base = raw_dir(root, "gh_aeron7")
    lst, files = selected_files(SOURCES["gh_aeron7"], root, end)
    paths = [p for p, _ in files if p.rsplit("/", 1)[-1] == f"{stem}.txt" and (base / p).exists()]
    paths.sort(key=lambda p: ("IntradayData_2018" in p, p))
    parts, skipped = [], []
    for p in paths:
        try:
            parts.append(parse_aeron(base / p))
        except Exception as e:                      # e.g. one day delivered in another layout
            skipped.append([p, str(e)[:120]])
    if not parts:
        return _finish(pd.DataFrame(columns=COLS + ["oi"])), {"files": 0, "skipped_files": skipped}
    return pd.concat(parts, ignore_index=True), {"files": len(parts), "skipped_files": skipped}


def build_index(sym: str, root: Path, start, end) -> dict:
    name, stem, src, rel_path, parser = INDEX_PLAN[sym]
    primary, st_p = normalise(parser(raw_dir(root, src) / rel_path)[COLS])
    first_day = primary["ts"].iloc[0].normalize()
    older, meta = load_aeron_symbol(root, stem, end)
    older, st_o = normalise(older[COLS], MISFILED_RATIO.get(sym, 1.2))
    older = older[older["ts"] < first_day]
    df = pd.concat([older, primary], ignore_index=True)
    df["volume"] = np.float32("nan")                # a spot index has no traded volume
    info = write_split(df[COLS], f"{sym}_1min.parquet", root, start, end)
    info.update({"kind": "index", "index_name": name, "interval": "1min",
                 "segments": [
                     {"source": "gh_aeron7", "until": str((first_day - pd.Timedelta(days=1)).date()),
                      "rows": int(len(older)), "cleaning": st_o, **meta},
                     {"source": src, "from": str(first_day.date()), "rows": int(len(primary)), "cleaning": st_p}]})
    return info


def build_future(sym: str, root: Path, start, end) -> dict:
    df, meta = load_aeron_symbol(root, FUT_PLAN[sym], end)
    df, st = normalise(df, 1.2)
    info = write_split(df[COLS + ["oi"]], f"{sym}_1min.parquet", root, start, end)
    info.update({"kind": "index_future_continuous", "interval": "1min",
                 "segments": [{"source": "gh_aeron7", "rows": int(len(df)), "cleaning": st, **meta}]})
    return info


def build_stock(sym: str, df: pd.DataFrame, source: str, root: Path, start, end, has_volume: bool) -> dict:
    df, st = normalise(df[COLS])
    if not has_volume:
        df["volume"] = np.float32("nan")
    info = write_split(df[COLS], f"{sym}_1min.parquet", root, start, end)
    info.update({"kind": "stock", "interval": "1min", "has_volume": has_volume,
                 "segments": [{"source": source, "rows": int(len(df)), "cleaning": st}]})
    return info


def build_options(und: str, root: Path, start, end) -> dict:
    base = raw_dir(root, "hf_thetrademarkk") / "options" / und
    out = {}
    for f in sorted(base.glob("*.parquet")):
        df = parse_trademarkk_options(f)
        n_in = len(df)
        df = df.drop_duplicates(["ts", "strike", "right"], keep="first")
        tod = df["ts"] - df["ts"].dt.normalize()
        inside = (tod >= SESSION_OPEN) & (tod < SESSION_CLOSE)
        bad = (df[["open", "high", "low", "close"]] <= 0).any(axis=1) | (df["high"] < df["low"]) | (df["ts"] > df["expiry"] + pd.Timedelta(days=1))
        df2 = df[inside & ~bad].sort_values(["ts", "strike", "right"], kind="stable").reset_index(drop=True)
        info = write_split(df2[OPT_COLS], f"options/{und}_1min/{f.stem}.parquet", root, start, end)
        info["cleaning"] = {"rows_in": int(n_in), "dropped_duplicate_rows": int(n_in - len(df)),
                            "dropped_outside_session": int((~inside).sum()), "dropped_bad": int((inside & bad).sum())}
        out[f.stem] = info
    return out


def build(root: Path, start=None, end=None, symbols: Iterable[str] | None = None, only: Iterable[str] | None = None) -> dict:
    """Rebuild <root>/intraday and <root>/holdout/intraday from the raw cache.

    `symbols` limits the build to those output symbols; `only` to the groups
    'index', 'futures', 'stocks', 'options'.  A partial build updates the
    matching entries of manifest.json and leaves the others alone."""
    end = pd.Timestamp(end) if end is not None else default_end(root)
    start = pd.Timestamp(start) if start is not None else None
    want = set(symbols) if symbols else None
    groups = set(only) if only else {"index", "futures", "stocks", "options"}
    man_path = root / "intraday" / "manifest.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {}
    man.setdefault("symbols", {})
    man.setdefault("options", {})
    t0 = time.time()

    def log(sym, info):
        r, h = info["research"], info["holdout"]
        print(f"  {sym:16s} research {r.get('rows', 0):8d} rows {r.get('first', '-')[:10]} .. {r.get('last', '-')[:10]}"
              f" | holdout {h['rows']:8d} rows  [{time.time() - t0:.0f}s]", flush=True)

    if "index" in groups:
        for sym in INDEX_PLAN:
            if want is None or sym in want:
                man["symbols"][sym] = build_index(sym, root, start, end)
                log(sym, man["symbols"][sym])
    if "futures" in groups:
        for sym in FUT_PLAN:
            if want is None or sym in want:
                man["symbols"][sym] = build_future(sym, root, start, end)
                log(sym, man["symbols"][sym])
    if "stocks" in groups:
        done = set()
        base = raw_dir(root, "gh_akshaj23") / AKSHAJ_STOCK_DIR
        for f in sorted(base.glob("*_minute.csv")):
            sym = f.name[:-len("_minute.csv")]
            if sym == "INDIA VIX":
                continue
            done.add(sym)
            if want is None or sym in want:
                man["symbols"][sym] = build_stock(sym, parse_akshaj(f), "gh_akshaj23", root, start, end, True)
                log(sym, man["symbols"][sym])
        shards = sorted((raw_dir(root, "hf_tiru8055") / "data").glob("*.parquet"))
        need_tiru = want is None or any(s not in done and s not in INDEX_PLAN and s not in FUT_PLAN for s in want)
        if shards and need_tiru:
            for name, df in iter_tiru(shards):
                sym = TIRU_ALIAS.get(name, name)
                if name in TIRU_SKIP or sym in done or (want is not None and sym not in want):
                    continue
                man["symbols"][sym] = build_stock(sym, df, "hf_tiru8055", root, start, end, False)
                if sym != name:
                    man["symbols"][sym]["source_symbol"] = name
                log(sym, man["symbols"][sym])
    if "options" in groups:
        for und in ("NIFTY", "BANKNIFTY"):
            if want is None or und in want or f"{und}_OPT" in want:
                man["options"][und] = build_options(und, root, start, end)
                tot = sum(v["research"].get("rows", 0) for v in man["options"][und].values())
                hold = sum(v["holdout"]["rows"] for v in man["options"][und].values())
                print(f"  {und + ' options':16s} research {tot:8d} rows in "
                      f"{sum(1 for v in man['options'][und].values() if v['research'].get('rows'))} expiry files"
                      f" | holdout {hold:8d} rows  [{time.time() - t0:.0f}s]", flush=True)
    man.update({"built_utc": pd.Timestamp.now("UTC").isoformat(), "end": str(end.date()),
                "start": str(start.date()) if start is not None else None,
                "timestamp_convention": "bar start, IST, timezone-naive",
                "sources": {k: {"url": s.url, "licence": s.licence, "timezone": s.timezone, "note": s.note}
                            for k, s in SOURCES.items()}})
    man_path.parent.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps(man, indent=1))
    return man


# --------------------------------------------------------------------------
# readers for the parts that do not fit load_intraday
# --------------------------------------------------------------------------

def _lock(root: Path) -> pd.Timestamp | None:
    if os.environ.get("QUANT_UNLOCK_HOLDOUT") == "1":
        return None
    f = root / "LOCK"
    return pd.Timestamp(f.read_text().strip()) if f.exists() else None


def list_option_expiries(underlying: str, interval: str = "1min", root=None) -> list[pd.Timestamp]:
    d = data_root(root) / "intraday" / "options" / f"{underlying}_{interval}"
    return sorted(pd.Timestamp(f.stem) for f in d.glob("*.parquet"))


def load_option_chain(underlying: str, expiry, interval: str = "1min", start=None, end=None, root=None) -> pd.DataFrame:
    """1-min bars of every strike of one expiry (columns OPT_COLS). Rows after
    the LOCK date are dropped, as in quant.data.store."""
    root = data_root(root)
    f = root / "intraday" / "options" / f"{underlying}_{interval}" / f"{pd.Timestamp(expiry).date()}.parquet"
    df = pd.read_parquet(f)
    lock = _lock(root)
    if lock is not None:
        df = df[df["ts"] < lock + pd.Timedelta(days=1)]
    if start is not None:
        df = df[df["ts"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["ts"] < pd.Timestamp(end) + pd.Timedelta(days=1)]
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="quant.data.intraday", description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", choices=["fetch", "build", "validate", "all"])
    ap.add_argument("--root", help="data root (default: <repo>/data or $QUANT_DATA)")
    ap.add_argument("--start", help="first research date (default: everything available)")
    ap.add_argument("--end", help="last research date (default: <root>/LOCK or 2021-12-31)")
    ap.add_argument("--only", help="fetch: source names; build: groups index,futures,stocks,options")
    ap.add_argument("--symbols", help="build/validate: comma-separated output symbols")
    ap.add_argument("--refresh-listings", action="store_true", help="fetch: re-read upstream file listings")
    ap.add_argument("--no-reference", action="store_true", help="validate: do not download NSE daily index files")
    a = ap.parse_args(argv)
    root = data_root(a.root)
    end = pd.Timestamp(a.end) if a.end else default_end(root)
    only = a.only.split(",") if a.only else None
    syms = a.symbols.split(",") if a.symbols else None
    if a.cmd in ("fetch", "all"):
        rep = fetch(root, end, only if a.cmd == "fetch" else None, a.refresh_listings)
        failed = {k: v["failed"] for k, v in rep.items() if v["failed"]}
        if failed:
            print("FAILED DOWNLOADS:", json.dumps(failed, indent=1)[:4000])
            return 1
    if a.cmd in ("build", "all"):
        build(root, a.start, end, syms, only if a.cmd == "build" else None)
    if a.cmd in ("validate", "all"):
        validate(root, end, syms, fetch_reference=not a.no_reference)
    return 0


if __name__ == "__main__":
    sys.exit(main())
