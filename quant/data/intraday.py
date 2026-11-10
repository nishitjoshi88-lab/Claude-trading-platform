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
    Source("hf_calender", "hf", "calender/indian-stock-hourly-2017-2021",
           "https://huggingface.co/datasets/calender/indian-stock-hourly-2017-2021", "CC-BY-4.0",
           "IST, separate date and HH:00 columns (clock-hour buckets)",
           "hourly bars May 2017 - Dec 2021 for NIFTY, BANKNIFTY, INDIAVIX and front-month futures",
           lambda files, end: [(p, s) for p, s in files if p.endswith("_2017-2021.csv")]),
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch"])
    ap.add_argument("--root")
    ap.add_argument("--end")
    ap.add_argument("--only")
    a = ap.parse_args()
    r = data_root(a.root)
    e = pd.Timestamp(a.end) if a.end else default_end(r)
    print(json.dumps(fetch(r, e, a.only.split(",") if a.only else None), indent=1)[:3000])
