"""NSE index daily data: download, parse, merge and write data/index/*.parquet.

Command line
  python -m quant.data.indices build --start 2003-01-01 --end 2021-12-31
  python -m quant.data.indices validate

Sources (all official NSE / NSE Indices Ltd; nothing is interpolated or filled)
  ni     niftyindices.com history endpoints, POST /BackPage/<endpoint> with a
         JSON body {"cinfo": "{'name':..,'startDate':..,'endDate':..,'indexName':..}"}:
           getHistoricaldatatabletoString    open high low close
           getTotalReturnIndexString         total-return index
           getpepbHistoricaldataDBtoString   P/E, P/B, dividend yield
         History goes back to each index's base date (NIFTY 50: 1990-07-03).
  daily  The NSE daily all-index file
           nsearchives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv
         First file is 2012-02-21. One row per index: open high low close,
         volume, turnover, P/E, P/B, dividend yield.

Where both sources have a value, `ni` is kept and `daily` only fills the
holes; the two are compared cell by cell and the disagreement is recorded in
meta.json. Indices that niftyindices.com no longer lists (renamed away or
discontinued) come from the daily file alone.

Outputs under <data root>/index/, wide, float32, index = date, columns =
official index name in upper case:
  close open high low      index level
  tri                      total-return index (fixed-income indices are total
                           return by construction, so their close is copied)
  pe pb dy                 valuation as published on the day
  volume turnover          constituents' shares traded / rupees crore (daily
                           file only, so from 2012-02-21)
  meta.json                per index: category, names used in the daily file,
                           first/last date, row count and source per field

Rows are NSE equity trading days only (days on which NIFTY 50 has a close).

Raw downloads are cached under <data root>/raw/index/ so a re-run only
fetches what is missing. To extend the range later, re-run `build` with a
later --end. An --end beyond <data root>/LOCK is refused unless
QUANT_UNLOCK_HOLDOUT=1, so the holdout cannot be downloaded by accident.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from quant.data import store

MAX_WORKERS = 6          # hard cap on concurrent downloads
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")

DAILY_URL = "https://nsearchives.nseindia.com/content/indices/ind_close_all_{d:%d%m%Y}.csv"
DAILY_FIRST = date(2012, 2, 21)       # first all-index file on the NSE archive

NI_BASE = "https://www.niftyindices.com"
NI_PAGE = NI_BASE + "/reports/historical-data"
NI_MAPPING_URL = "https://liveindexsa.niftyindices.com/assets/json/IndexMapping.json"
NI_ENDPOINT = {
    "price": "getHistoricaldatatabletoString",
    "tri": "getTotalReturnIndexString",
    "pepb": "getpepbHistoricaldataDBtoString",
}
NI_BLOCK_YEARS = 5                    # one request covers at most this many calendar years
NI_GROUP = "Historical Index Data"    # the menu whose index list we use

PRICE_FIELDS = ("open", "high", "low", "close")
VALUATION_FIELDS = ("pe", "pb", "dy")
DAILY_ONLY_FIELDS = ("volume", "turnover")
FIELDS = ("close", "open", "high", "low", "tri", "pe", "pb", "dy", "volume", "turnover")

VIX = "INDIA VIX"
CALENDAR_INDEX = "NIFTY 50"
CLEAN_PRICE = "NIFTY 10 YR BENCHMARK G-SEC (CLEAN PRICE)"
DIVIDEND_POINTS = "NIFTY50 DIVIDEND POINTS"   # restarts from zero every April: zero is a real value
SCALE_LIMIT = 5.0                             # open/high/low this many times off the close = another scale


# --------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------

# Names used in the daily file over the years -> today's official name (upper
# case, as listed on niftyindices.com). Keys are upper case with single
# spaces. Every entry was checked against the data: the old name's last day
# and the new name's first day are consecutive trading days and the index
# level is continuous across the change. A name not listed here is kept as is.
ALIASES: dict[str, str] = {
    # 2012-02-21 .. 2013-02-07 (S&P branding), then CNX until 2015-11-06
    "S&P CNX NIFTY": "NIFTY 50", "CNX NIFTY": "NIFTY 50",
    "S&P CNX 500": "NIFTY 500", "CNX 500": "NIFTY 500",
    "S&P CNX 500 SHARIAH": "NIFTY500 SHARIAH", "CNX 500 SHARIAH": "NIFTY500 SHARIAH",
    "S&P CNX NIFTY SHARIAH": "NIFTY50 SHARIAH", "CNX NIFTY SHARIAH": "NIFTY50 SHARIAH",
    "S&P CNX NIFTY DIVIDEND": "NIFTY50 DIVIDEND POINTS", "CNX NIFTY DIVIDEND": "NIFTY50 DIVIDEND POINTS",
    "CNX NIFTY JUNIOR": "NIFTY NEXT 50",
    "CNX 100": "NIFTY 100", "CNX 200": "NIFTY 200",
    "CNX MIDCAP": "NIFTY MIDCAP 100", "NIFTY FREE FLOAT MIDCAP 100": "NIFTY MIDCAP 100",
    "CNX SMALLCAP": "NIFTY SMALLCAP 100", "NIFTY FREE FLOAT SMALLCAP 100": "NIFTY SMALLCAP 100",
    "CNX AUTO": "NIFTY AUTO", "CNX BANK": "NIFTY BANK", "CNX ENERGY": "NIFTY ENERGY",
    "CNX FINANCE": "NIFTY FINANCIAL SERVICES", "CNX FMCG": "NIFTY FMCG", "CNX IT": "NIFTY IT",
    "CNX MEDIA": "NIFTY MEDIA", "CNX METAL": "NIFTY METAL", "CNX MNC": "NIFTY MNC",
    "CNX PHARMA": "NIFTY PHARMA", "CNX PSE": "NIFTY PSE", "CNX PSU BANK": "NIFTY PSU BANK",
    "CNX REALTY": "NIFTY REALTY", "CNX COMMODITIES": "NIFTY COMMODITIES",
    "CNX CONSUMPTION": "NIFTY INDIA CONSUMPTION", "CNX INFRASTRUCTURE": "NIFTY INFRASTRUCTURE",
    "CNX SERVICE SECTOR": "NIFTY SERVICES SECTOR",
    "CNX DIVIDEND OPPORTUNITIES": "NIFTY DIVIDEND OPPORTUNITIES 50",
    "CNX ALPHA INDEX": "NIFTY ALPHA 50", "CNX HIGH BETA": "NIFTY HIGH BETA 50",
    "CNX LOW VOLATILITY": "NIFTY LOW VOLATILITY 50",
    "CNX DEFTY": "NIFTY50 USD", "CNX 100 EQUAL WEIGHT": "NIFTY100 EQUAL WEIGHT",
    "LIX 15": "NIFTY100 LIQUID 15", "LIX15 MIDCAP": "NIFTY MIDCAP LIQUID 15",
    "CPSE": "NIFTY CPSE", "NV 20": "NIFTY50 VALUE 20", "NI15": "NIFTY GROWTH SECTORS 15",
    "CNX SHARIAH25": "NIFTY SHARIAH 25",
    "NSE QUALITY 30": "NIFTY100 QUALITY 30", "NIFTY QUALITY 30": "NIFTY100 QUALITY 30",
    "GSEC10 NSE INDEX": "NIFTY 8-13 YR G-SEC",
    "GSECBM NSE INDEX": "NIFTY 10 YR BENCHMARK G-SEC",
    "NSE GSECBM CLEAN PRICE INDEX": "NIFTY 10 YR BENCHMARK G-SEC (CLEAN PRICE)",
    "NIFTY TR 1X INVERSE": "NIFTY50 TR 1X INVERSE", "NIFTY TR 2X LEVERAGE": "NIFTY50 TR 2X LEVERAGE",
    "NIFTY PR 1X INVERSE": "NIFTY50 PR 1X INVERSE", "NIFTY PR 2X LEVERAGE": "NIFTY50 PR 2X LEVERAGE",
    # names still printed in the daily file in 2021 that differ from the official list
    "NIFTY ADITYA BIRLA GROUP": "NIFTY INDIA CORPORATE GROUP INDEX - ADITYA BIRLA GROUP",
    "NIFTY MAHINDRA GROUP": "NIFTY INDIA CORPORATE GROUP INDEX - MAHINDRA GROUP",
    "NIFTY TATA GROUP": "NIFTY INDIA CORPORATE GROUP INDEX - TATA GROUP",
    "NIFTY TATA GROUP 25% CAP": "NIFTY INDIA CORPORATE GROUP INDEX - TATA GROUP 25% CAP",
    "NIFTY 50 FUTURES INDEX": "NIFTY 50 FUTURES PR", "NIFTY 50 FUTURES TR INDEX": "NIFTY 50 FUTURES TR",
    "NIFTY HEALTHCARE INDEX": "NIFTY HEALTHCARE",
}


def squash(name: str) -> str:
    """Upper case, single spaces, plain hyphens."""
    s = str(name).replace("–", "-").replace("—", "-").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip().upper()


def canon(name: str) -> str:
    """Official upper-case index name for any name seen in a source."""
    s = squash(name)
    return ALIASES.get(s, s)


def slug(name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", squash(name)).strip("_")


# --------------------------------------------------------------------------
# Parsing (pure functions, no network)
# --------------------------------------------------------------------------

_NULLS = {"", "-", "--", "NA", "N/A", "NAN", "NULL", "NIL"}


def to_float(x) -> float:
    """'1,234.5' -> 1234.5; '-', '' and None -> NaN. Anything else raises."""
    if x is None:
        return float("nan")
    s = str(x).strip().replace(",", "")
    if s.upper() in _NULLS:
        return float("nan")
    return float(s)


def _parse_date(s: str) -> pd.Timestamp:
    s = str(s).strip()
    for fmt in ("%d-%m-%Y", "%d %b %Y", "%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return pd.Timestamp(datetime.strptime(s, fmt))
        except ValueError:
            pass
    raise ValueError(f"unrecognised date {s!r}")


_DAILY_COLS = {
    "index name": "raw_name",
    "index date": "date",
    "open index value": "open",
    "high index value": "high",
    "low index value": "low",
    "closing index value": "close",
    "volume": "volume",
    "turnover (rs. cr.)": "turnover",
    "p/e": "pe",
    "p/b": "pb",
    "div yield": "dy",
}
_DAILY_NUM = ("open", "high", "low", "close", "volume", "turnover", "pe", "pb", "dy")
LONG_COLS = ["name", "raw_name", "date", *_DAILY_NUM]


def parse_daily_csv(text: str) -> pd.DataFrame:
    """One NSE all-index file -> long frame with columns LONG_COLS.

    `name` is the official name, `raw_name` the name as printed that day.
    Rows without a closing value are dropped. If a file prints the same
    index twice, identical rows collapse to one; rows that disagree are all
    dropped (one of them is mislabelled and we cannot tell which) and the
    names are listed in `.attrs["conflicts"]`.
    """
    rows = [r for r in csv.reader(io.StringIO(text.lstrip("﻿"))) if any(c.strip() for c in r)]
    if not rows:
        raise ValueError("empty file")
    header = [re.sub(r"\s+", " ", h).strip().lower() for h in rows[0]]
    missing = [c for c in ("index name", "index date", "closing index value") if c not in header]
    if missing:
        raise ValueError(f"not an all-index file, header lacks {missing}: {rows[0][:6]}")
    pos = {out: header.index(col) for col, out in _DAILY_COLS.items() if col in header}
    out = []
    for r in rows[1:]:
        get = lambda k: r[pos[k]] if k in pos and pos[k] < len(r) else None
        raw = (get("raw_name") or "").strip()
        if not raw:
            continue
        rec = {"name": canon(raw), "raw_name": raw, "date": _parse_date(get("date"))}
        for k in _DAILY_NUM:
            rec[k] = to_float(get(k))
        if np.isnan(rec["close"]):
            continue
        out.append(rec)
    df = pd.DataFrame(out, columns=LONG_COLS).drop_duplicates(["name", "date", *_DAILY_NUM])
    clash = df.duplicated(["name", "date"], keep=False)
    conflicts = sorted(set(df.loc[clash, "name"]))
    df = df[~clash].reset_index(drop=True)
    df.attrs["conflicts"] = conflicts
    return df


_NI_COLS = {
    "price": ("HistoricalDate", {"OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close"}),
    "tri": ("Date", {"TotalReturnsIndex": "tri"}),
    "pepb": ("DATE", {"pe": "pe", "pb": "pb", "divYield": "dy"}),
}


def parse_ni(kind: str, rows: list[dict]) -> pd.DataFrame:
    """niftyindices.com JSON rows -> frame indexed by date, one column per field."""
    date_key, cols = _NI_COLS[kind]
    rec = [{"date": _parse_date(r[date_key]), **{out: to_float(r.get(src)) for src, out in cols.items()}}
           for r in rows]
    df = pd.DataFrame(rec, columns=["date", *cols.values()])
    df = df.dropna(how="all", subset=list(cols.values()))
    df = df.drop_duplicates("date", keep="last").set_index("date").sort_index()
    return df


def decode_ni(text: str) -> list[dict]:
    """Body of a niftyindices response -> list of row dicts. The site answers
    with a JSON array (older versions wrapped it as {"d": "<json>"}); an HTML
    error page raises ValueError."""
    j = json.loads(text)
    if isinstance(j, dict) and "d" in j:
        j = json.loads(j["d"]) if isinstance(j["d"], str) else j["d"]
    if not isinstance(j, list):
        raise ValueError(f"expected a JSON list, got {type(j).__name__}")
    return j


def ni_blocks(start: date, end: date, years: int = NI_BLOCK_YEARS) -> list[tuple[date, date]]:
    """Split [start, end] into windows on fixed calendar boundaries (years
    divisible by `years`), so finished windows keep the same cache key when
    the range is extended later."""
    if end < start:
        return []
    out = []
    y = start.year - start.year % years
    while y <= end.year:
        s, e = max(start, date(y, 1, 1)), min(end, date(y + years - 1, 12, 31))
        if s <= e:
            out.append((s, e))
        y += years
    return out


def ni_body(request_name: str, display_name: str, start: date, end: date) -> str:
    cinfo = "{'name':'%s','startDate':'%s','endDate':'%s','indexName':'%s'}" % (
        request_name, start.strftime("%d-%b-%Y"), end.strftime("%d-%b-%Y"), display_name)
    return json.dumps({"cinfo": cinfo})


def trading_names(mapping: list[dict]) -> dict[str, str]:
    """IndexMapping.json -> {official name: name the site sends to its API}.
    Mirrors the site's own lookup (upper case, whitespace ignored)."""
    out = {}
    for m in mapping:
        trade = squash(m.get("Trading_Index_Name", ""))
        for k in (m.get("Index_long_name", ""), m.get("Trading_Index_Name", "")):
            if k and trade:
                out.setdefault(re.sub(r"\s+", "", squash(k)), trade)
    return out


def request_name(official: str, tnames: dict[str, str]) -> str:
    return tnames.get(re.sub(r"\s+", "", squash(official)), squash(official))


# --------------------------------------------------------------------------
# Assembly (pure functions)
# --------------------------------------------------------------------------

def to_wide(long: pd.DataFrame, field: str) -> pd.DataFrame:
    """Long frame (name, date, field) -> wide frame, dropping empty cells."""
    d = long[["name", "date", field]].dropna(subset=[field])
    if d.empty:
        return pd.DataFrame(index=pd.DatetimeIndex([], name="date"))
    w = d.pivot_table(index="date", columns="name", values=field, aggfunc="last")
    w.index.name, w.columns.name = "date", None
    return w.sort_index()


def merge_sources(primary: pd.DataFrame, secondary: pd.DataFrame) -> pd.DataFrame:
    """Cell-wise: keep primary, fill its holes from secondary. No other filling."""
    idx = primary.index.union(secondary.index)
    cols = primary.columns.union(secondary.columns)
    out = primary.reindex(index=idx, columns=cols).combine_first(secondary.reindex(index=idx, columns=cols))
    out.index.name = "date"
    return out


def clean(w: dict[str, pd.DataFrame]) -> dict:
    """Blank cells that cannot be right, rather than guess a correction.

      non_positive  a level, P/E or P/B of zero or less (a dividend yield of
                    zero is real, and so is a zero in NIFTY50 DIVIDEND POINTS)
      off_scale     open/high/low more than SCALE_LIMIT times away from the
                    close: niftyindices.com serves NIFTY IT's open/high/low
                    before the index was re-based on 2004-05-28 ten times
                    larger than its close

    Works in place on {field: wide frame}; returns {rule: {field: {index: cells}}}."""
    dropped: dict[str, dict] = {"non_positive": {}, "off_scale": {}}

    def blank(f: str, bad: pd.DataFrame, rule: str):
        n = bad.sum()
        n = n[n > 0]
        if len(n):
            dropped[rule][f] = {k: int(v) for k, v in n.items()}
            w[f] = w[f].mask(bad)

    for f in (*PRICE_FIELDS, "tri", "pe", "pb"):
        if f in w and w[f].size:
            bad = w[f] <= 0
            if f == "close" and DIVIDEND_POINTS in bad:
                bad[DIVIDEND_POINTS] = False
            blank(f, bad, "non_positive")
    if "close" in w and w["close"].size:
        for f in ("open", "high", "low"):
            if f in w and w[f].size:
                r = w[f] / w["close"].reindex(index=w[f].index, columns=w[f].columns)
                blank(f, (r > SCALE_LIMIT) | (r < 1 / SCALE_LIMIT), "off_scale")
    return dropped


def longest_gap(s: pd.Series) -> tuple[int, str | None]:
    """Longest run of calendar days between consecutive observations."""
    d = s.dropna().index
    if len(d) < 2:
        return 0, None
    gaps = (d[1:] - d[:-1]).days
    i = int(np.argmax(gaps))
    return int(gaps[i]), str(d[i].date())


def continuous_from(present: np.ndarray, days: pd.DatetimeIndex, max_absent: int = 5) -> pd.Timestamp | None:
    """First day of the last unbroken run of an index in the daily files.

    `present[i]` says whether the index is printed in the file of `days[i]`.
    A run survives up to `max_absent` consecutive files without the index.
    The index was certainly being published from this day on, so it is an
    upper bound on the launch date; history before it may be back-calculated
    (the daily files start in 2012 and NSE re-issued a few of them later with
    every index that exists today)."""
    idx = np.flatnonzero(present)
    if len(idx) == 0:
        return None
    first = idx[-1]
    for i in idx[::-1]:
        if first - i - 1 > max_absent:
            break
        first = i
    return days[first]


def field_stats(s: pd.Series) -> dict | None:
    v = s.dropna()
    if v.empty:
        return None
    return {"first": str(v.index[0].date()), "last": str(v.index[-1].date()), "n": int(len(v))}


def check_end(end: date, root=None) -> None:
    """Refuse to touch the holdout period."""
    lock = store.lock_date(root)
    if lock is not None and pd.Timestamp(end) > lock:
        raise SystemExit(
            f"--end {end} is after the holdout lock {lock.date()} ({store.data_root(root) / 'LOCK'}). "
            "Data after the lock is withheld until strategy code is frozen. "
            "Set QUANT_UNLOCK_HOLDOUT=1 (and move LOCK) to extend the range.")


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------

_local = threading.local()


def _session():
    import requests
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9", "Accept": "*/*"})
        _local.s = s
    return s


def _retry(fn, what: str, tries: int = 6):
    """Run fn() with exponential backoff. fn returns a value or raises."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # network errors, bad status, bad body
            if i == tries - 1:
                raise RuntimeError(f"{what}: {type(e).__name__}: {str(e)[:200]}") from e
            time.sleep(min(60, 1.5 * 2 ** i) * (0.5 + random.random()))


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}_{threading.get_ident()}")
    tmp.write_bytes(data)
    tmp.replace(path)


def daily_path(raw: Path, d: date) -> Path:
    return raw / "daily" / f"{d.year}" / f"ind_close_all_{d:%d%m%Y}.csv"


def fetch_daily(raw: Path, d: date) -> str:
    """Download one daily file into the cache. Returns 'cached', 'ok' or 'absent' (HTTP 404)."""
    p = daily_path(raw, d)
    if p.exists():
        return "cached"

    def go():
        r = _session().get(DAILY_URL.format(d=d), timeout=40)
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            raise IOError(f"HTTP {r.status_code}")
        if not r.content.lstrip(b"\xef\xbb\xbf").lower().startswith(b"index name"):
            raise IOError(f"unexpected body {r.content[:60]!r}")
        return r.content

    body = _retry(go, f"daily file {d}")
    if body is None:
        return "absent"
    _write_atomic(p, body)
    return "ok"


def download_daily(raw: Path, start: date, end: date, workers: int = MAX_WORKERS,
                   recheck: set[date] | None = None, log=print) -> dict:
    """Fetch every daily file in [start, end]. Every calendar day is tried
    (special sessions fall on weekends); days the server answers 404 for are
    remembered in daily/absent.json. `recheck` forces another try for days
    that should exist."""
    start = max(start, DAILY_FIRST)
    absent_file = raw / "daily" / "absent.json"
    absent = set(json.loads(absent_file.read_text())) if absent_file.exists() else set()
    recheck = {str(d) for d in (recheck or ())}
    days = [start + timedelta(n) for n in range((end - start).days + 1)] if end >= start else []
    todo = [d for d in days if not daily_path(raw, d).exists() and (str(d) not in absent or str(d) in recheck)]
    stats = {"days": len(days), "requested": len(todo), "ok": 0, "absent": 0, "failed": []}
    if todo:
        log(f"daily files: {len(todo)} to request ({len(days) - len(todo)} already known)")
        done = 0

        def one(d):
            try:
                return d, fetch_daily(raw, d)
            except Exception as e:
                return d, f"failed: {e}"

        with ThreadPoolExecutor(max_workers=min(workers, MAX_WORKERS)) as ex:
            for d, res in ex.map(one, todo):
                done += 1
                if res == "absent":
                    absent.add(str(d)); stats["absent"] += 1
                elif res in ("ok", "cached"):
                    absent.discard(str(d)); stats["ok"] += 1
                else:
                    stats["failed"].append([str(d), res])
                if done % 500 == 0:
                    log(f"  daily files: {done}/{len(todo)}")
                    _write_atomic(absent_file, json.dumps(sorted(absent)).encode())
        _write_atomic(absent_file, json.dumps(sorted(absent)).encode())
    stats["files"] = sum(daily_path(raw, d).exists() for d in days)
    return stats


def _ni_headers() -> dict:
    return {"Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest", "Origin": NI_BASE, "Referer": NI_PAGE}


def _ni_post(endpoint: str, **kw) -> str:
    r = _session().post(f"{NI_BASE}/BackPage/{endpoint}", headers={**_ni_headers(), **kw.pop("headers", {})},
                        timeout=120, **kw)
    if r.status_code != 200:
        raise IOError(f"HTTP {r.status_code}")
    return r.content.decode("utf-8-sig")


def fetch_index_list(raw: Path, refresh: bool = False, offline: bool = False, log=print) -> dict:
    """The index catalogue of niftyindices.com: {"indices": {official name:
    category}, "trading_names": {...}}. Cached in niftyindices/catalogue.json."""
    f = raw / "niftyindices" / "catalogue.json"
    if f.exists() and not (refresh and not offline):
        return json.loads(f.read_text())
    if offline:
        raise FileNotFoundError(f"not cached: {f}")
    log("niftyindices: reading the index catalogue")
    jpost = {"Content-Type": "application/json; charset=UTF-8"}
    types = [x["indextype"] for x in _retry(lambda: decode_ni(_ni_post("gethistoricaltypedata1")), "index types")
             if x.get("indextype")]
    indices: dict[str, str] = {}
    for typ in types:
        subs = _retry(lambda: decode_ni(_ni_post(
            "gethistoricaltypeSubindexdata", headers=jpost,
            data=json.dumps({"cinfo": {"indextype": typ, "indexgroup": NI_GROUP}}))), f"sub-types of {typ}")
        for sub in [x["indextype"] for x in subs if x.get("indextype")]:
            names = _retry(lambda: decode_ni(_ni_post(
                "gethistoricaltypeindexdata",
                data={"cinfo[indextype]": sub, "cinfo[indexgroup]": NI_GROUP})), f"indices of {sub}")
            for x in names:
                if x.get("indextype"):
                    indices.setdefault(str(x["indextype"]).strip(), f"{typ} / {sub}")

    def mapping():
        r = _session().get(NI_MAPPING_URL, timeout=60)
        if r.status_code != 200:
            raise IOError(f"HTTP {r.status_code}")
        return json.loads(r.content.decode("utf-8-sig"))

    cat = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "indices": indices, "trading_names": trading_names(_retry(mapping, "IndexMapping.json"))}
    if not indices:
        raise RuntimeError("niftyindices returned an empty index catalogue")
    _write_atomic(f, json.dumps(cat, indent=1, ensure_ascii=False).encode())
    return cat


def ni_path(raw: Path, kind: str, name: str, s: date, e: date, alt: bool = False) -> Path:
    return raw / "niftyindices" / (kind + "_alt" if alt else kind) / slug(name) / f"{s:%Y%m%d}_{e:%Y%m%d}.json.gz"


def _read_gz(p: Path) -> dict:
    return json.loads(gzip.decompress(p.read_bytes()).decode("utf-8"))


def _gz(obj) -> bytes:
    return gzip.compress(json.dumps(obj, ensure_ascii=False).encode("utf-8"), mtime=0)


def fetch_ni(raw: Path, kind: str, name: str, req_name: str, s: date, e: date, alt: bool = False,
             offline: bool = False) -> list[dict]:
    """One history window for one index, through the cache. Rows dated
    outside [s, e] are discarded before anything is written to disk.
    `alt` marks a second attempt under another spelling (cached separately)."""
    p = ni_path(raw, kind, name, s, e, alt)
    if p.exists():
        return _read_gz(p)["rows"]
    if offline:
        raise FileNotFoundError(f"not cached: {p}")
    date_key = _NI_COLS[kind][0]

    def go():
        rows = decode_ni(_ni_post(NI_ENDPOINT[kind], headers={"Content-Type": "application/json; charset=UTF-8"},
                                  data=ni_body(req_name, name, s, e).encode("utf-8")))
        return [{k: v for k, v in r.items() if k != "RequestNumber"} for r in rows
                if pd.Timestamp(s) <= _parse_date(r[date_key]) <= pd.Timestamp(e)]

    rows = _retry(go, f"niftyindices {kind} {name} {s}..{e}")
    _write_atomic(p, _gz({"name": name, "request_name": req_name, "kind": kind, "start": str(s),
                          "end": str(e), "rows": rows}))
    return rows


def _run_ni_jobs(raw: Path, jobs: list[tuple], workers: int, failed: list, log, label: str,
                 offline: bool = False) -> dict:
    """jobs: (kind, name, request name, start, end, alt). Returns {(kind, name): rows}."""
    rows: dict[tuple[str, str], list] = {(k, n): [] for k, n, *_ in jobs}
    todo = sum(not ni_path(raw, k, n, s, e, alt).exists() for k, n, _, s, e, alt in jobs)
    log(f"niftyindices {label}: {len(jobs)} requests, {todo} not cached")

    def one(job):
        k, n, rn, s, e, alt = job
        try:
            return job, fetch_ni(raw, k, n, rn, s, e, alt, offline), None
        except Exception as ex_:
            return job, [], str(ex_)

    with ThreadPoolExecutor(max_workers=max(1, min(workers, MAX_WORKERS))) as ex:
        for done, ((k, n, rn, s, e, alt), r, err) in enumerate(ex.map(one, jobs), 1):
            if err:
                failed.append([k, n, str(s), str(e), err])
            rows[(k, n)].extend(r)
            if todo and done % 500 == 0:
                log(f"  niftyindices {label}: {done}/{len(jobs)}")
    return rows


def download_ni(raw: Path, catalogue: dict, start: date, end: date, workers: int = 4,
                offline: bool = False, log=print) -> dict:
    """Fetch price, total-return and valuation history for every catalogued
    index (plus INDIA VIX). Returns {"frames": {kind: {name: DataFrame}}, ...}."""
    names = dict(catalogue["indices"])
    names.setdefault(VIX, "Volatility")
    tn = catalogue["trading_names"]
    seen: dict[str, str] = {}
    for n in names:
        if seen.setdefault(slug(n), n) != n:
            raise RuntimeError(f"cache name collision: {n!r} and {seen[slug(n)]!r}")
    blocks = ni_blocks(start, end)
    failed: list[list[str]] = []
    jobs = [(k, n, request_name(n, tn), s, e, False) for k in NI_ENDPOINT for n in names for s, e in blocks
            if not (n == VIX and k != "price")]
    rows = _run_ni_jobs(raw, jobs, workers, failed, log, "history", offline)
    # The site sends its short "trading" name. The valuation endpoint needs
    # it; the price and total-return endpoints also accept the official name.
    # Where the trading name produced nothing at all, try the official name.
    again = [(k, n, squash(n), s, e, True) for (k, n), r in rows.items()
             if not r and request_name(n, tn) != squash(n) for s, e in blocks]
    if again:
        for key, r in _run_ni_jobs(raw, again, workers, failed, log, "second spelling", offline).items():
            rows[key] = r
    out: dict[str, dict[str, pd.DataFrame]] = {k: {} for k in NI_ENDPOINT}
    for (k, n), r in rows.items():
        if r:
            df = parse_ni(k, r)
            if not df.empty:
                out[k][canon(n)] = df
    return {"frames": out, "failed": failed, "names": names, "requests": len(jobs) + len(again)}


def read_daily(raw: Path, start: date, end: date) -> tuple[pd.DataFrame, list]:
    """Parse every cached daily file in [start, end] into one long frame."""
    parts, problems = [], []
    d = max(start, DAILY_FIRST)
    while d <= end:
        p = daily_path(raw, d)
        if p.exists():
            try:
                df = parse_daily_csv(p.read_text(encoding="utf-8-sig", errors="replace"))
            except Exception as e:
                problems.append([str(d), f"unparseable: {e}"])
                d += timedelta(1)
                continue
            bad = df["date"] != pd.Timestamp(d)
            if bad.any():
                problems.append([str(d), f"{int(bad.sum())} rows dated {sorted(set(df.loc[bad, 'date'].dt.date.astype(str)))}"])
                df = df[~bad]
            if df.attrs.get("conflicts"):
                problems.append([str(d), f"same index printed twice with different values, rows dropped: {df.attrs['conflicts']}"])
            parts.append(df)
        d += timedelta(1)
    long = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=LONG_COLS)
    return long, problems


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def _ni_wide(frames: dict[str, pd.DataFrame], field: str) -> pd.DataFrame:
    cols = {n: df[field].dropna() for n, df in frames.items() if field in df and df[field].notna().any()}
    w = pd.DataFrame(cols)
    w.index.name = "date"
    return w.sort_index()


def _differs(a: pd.DataFrame, b: pd.DataFrame, atol: float, rtol: float) -> dict:
    """Cell-by-cell comparison of two wide frames on their common cells."""
    cols, idx = a.columns.intersection(b.columns), a.index.intersection(b.index)
    x, y = a.reindex(index=idx, columns=cols), b.reindex(index=idx, columns=cols)
    both = x.notna() & y.notna()
    diff = (x - y).abs().where(both)
    bad = diff > (atol + rtol * y.abs())
    per = pd.DataFrame({"n_both": both.sum(), "n_differ": bad.sum(),
                        "max_abs": diff.max(), "max_rel": (diff / y.abs().where(y != 0)).max()})
    per = per[per["n_both"] > 0]
    worst = per[per["n_differ"] > 0].sort_values("n_differ", ascending=False)
    return {"cells_compared": int(per["n_both"].sum()), "cells_differ": int(per["n_differ"].sum()),
            "indices_compared": int(len(per)), "indices_differ": int(len(worst)),
            "worst": {n: {"n_both": int(r.n_both), "n_differ": int(r.n_differ),
                          "max_abs": round(float(r.max_abs), 4), "max_rel": round(float(r.max_rel), 6)}
                      for n, r in worst.head(15).iterrows()}}


def assemble(ni_frames: dict, daily_long: pd.DataFrame, categories: dict[str, str],
             start: date, end: date) -> tuple[dict[str, pd.DataFrame], dict]:
    """Merge the two sources into one wide frame per field and describe the
    result. Pure: takes parsed frames, returns frames + metadata."""
    kind_of = {**{f: "price" for f in PRICE_FIELDS}, "tri": "tri", **{f: "pepb" for f in VALUATION_FIELDS}}
    ni = {f: _ni_wide(ni_frames.get(k, {}), f) for f, k in kind_of.items()}
    daily = {f: to_wide(daily_long, f) for f in (*PRICE_FIELDS, *VALUATION_FIELDS, *DAILY_ONLY_FIELDS)}
    dropped = {"niftyindices": clean(ni), "daily_file": clean(daily)}
    empty = pd.DataFrame(index=pd.DatetimeIndex([], name="date"))
    wide = {f: merge_sources(ni.get(f, empty), daily.get(f, empty)) for f in FIELDS}

    agreement = {f: _differs(ni[f], daily[f], atol=0.011, rtol=1e-5 if f in PRICE_FIELDS else 0.0)
                 for f in (*PRICE_FIELDS, *VALUATION_FIELDS)}

    lo, hi = pd.Timestamp(start), pd.Timestamp(end)
    wide = {f: w.loc[lo:hi] for f, w in wide.items()}
    if CALENDAR_INDEX not in wide["close"]:
        raise RuntimeError(f"{CALENDAR_INDEX} has no close; cannot define the trading calendar")
    cal = wide["close"][CALENDAR_INDEX].dropna().index
    off = {}
    for f, w in wide.items():
        extra = w.loc[w.index.difference(cal)].dropna(how="all", axis=1).dropna(how="all")
        if len(extra):
            off[f] = {"rows": int(len(extra)), "cells": int(extra.notna().sum().sum()),
                      "indices": int(extra.shape[1])}
    wide = {f: w.reindex(cal) for f, w in wide.items()}

    # Fixed-income indices are total-return by construction ("All fixed income
    # indices [except Nifty 10 yr Benchmark G-Sec (Clean Price)] are Total
    # Return", niftyindices.com historical-data page): expose them in tri too.
    tri_copy = [n for n, c in categories.items()
                if c.startswith("Fixed Income") and n != CLEAN_PRICE
                and n in wide["close"] and n not in wide["tri"]]
    if tri_copy:
        wide["tri"] = pd.concat([wide["tri"], wide["close"][tri_copy]], axis=1)

    for f in FIELDS:
        w = wide[f].dropna(how="all", axis=1)
        w = w[sorted(w.columns)].astype("float32")
        w.index.name, w.columns.name = "date", None
        wide[f] = w

    raw_names = (daily_long.groupby("name")["raw_name"].agg(lambda s: list(dict.fromkeys(s)))
                 if len(daily_long) else pd.Series(dtype=object))
    file_days = pd.DatetimeIndex(sorted(daily_long["date"].unique())) if len(daily_long) else pd.DatetimeIndex([])
    printed = daily["close"].reindex(file_days).notna()
    names = sorted(set().union(*[set(w.columns) for w in wide.values()]))
    indices = {}
    for n in names:
        rec = {"category": categories.get(n, "not listed on niftyindices.com (daily file only)"), "fields": {}}
        if n in raw_names.index:
            rec["daily_file_names"] = raw_names[n]
            rec["daily_file_continuous_from"] = str(continuous_from(printed[n].to_numpy(), file_days).date())
        for f in FIELDS:
            if n not in wide[f]:
                continue
            st = field_stats(wide[f][n])
            if st is None:
                continue
            if f == "tri" and n in tri_copy:
                st["source"] = "copy of close (fixed-income index is total return by construction)"
            else:
                n_ni = int(ni[f][n].reindex(cal).notna().sum()) if f in ni and n in ni[f] else 0
                st["n_niftyindices"], st["n_daily_file"] = n_ni, st["n"] - n_ni
                st["source"] = "+".join(s for s, k in (("niftyindices", n_ni), ("daily_file", st["n"] - n_ni)) if k)
            rec["fields"][f] = st
        indices[n] = rec
    meta = {
        "start": str(start), "end": str(end),
        "calendar": {"rule": f"rows are the days on which {CALENDAR_INDEX} has a close",
                     "days": int(len(cal)), "first": str(cal[0].date()), "last": str(cal[-1].date()),
                     "dropped_off_calendar": off},
        "shapes": {f: list(wide[f].shape) for f in FIELDS},
        "dropped_cells": dropped,
        "source_agreement": agreement,
        "indices": indices,
    }
    return wide, meta


SOURCES = {
    "niftyindices": "https://www.niftyindices.com/BackPage/{getHistoricaldatatabletoString,"
                    "getTotalReturnIndexString,getpepbHistoricaldataDBtoString}",
    "daily_file": "https://nsearchives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv (from 2012-02-21)",
}


def build(start: date, end: date, root=None, workers: int = MAX_WORKERS, offline: bool = False,
          refresh_catalogue: bool = False, log=print) -> dict:
    """Download whatever is missing for [start, end], then write the outputs."""
    check_end(end, root)
    if end < start:
        raise SystemExit("--end is before --start")
    droot = store.data_root(root)
    raw, out = droot / "raw" / "index", droot / "index"
    raw.mkdir(parents=True, exist_ok=True)

    cat = fetch_index_list(raw, refresh=refresh_catalogue, offline=offline, log=log)
    ni = download_ni(raw, cat, start, end, workers=min(workers, 4), offline=offline, log=log)
    cal_hint = set()
    if CALENDAR_INDEX in ni["frames"]["price"]:
        cal_hint = {d.date() for d in ni["frames"]["price"][CALENDAR_INDEX].index}
    dstats = {"skipped": "offline"} if offline else download_daily(raw, start, end, workers, recheck=cal_hint, log=log)
    daily_long, problems = read_daily(raw, start, end)
    log(f"daily files parsed: {daily_long['date'].nunique() if len(daily_long) else 0} days, {len(daily_long)} rows")

    categories = {canon(n): c for n, c in ni["names"].items()}
    wide, meta = assemble(ni["frames"], daily_long, categories, start, end)

    have = set(daily_long["date"].dt.date) if len(daily_long) else set()
    no_file = sorted(str(d) for d in cal_hint if max(start, DAILY_FIRST) <= d <= end and d not in have)
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": SOURCES,
        **meta,
        "download": {
            "niftyindices_requests": ni["requests"], "niftyindices_failed": ni["failed"],
            "daily": dstats, "daily_file_problems": problems,
            "trading_days_without_daily_file": no_file,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    for f in FIELDS:
        tmp = out / f"{f}.parquet.tmp"
        wide[f].to_parquet(tmp)
        tmp.replace(out / f"{f}.parquet")
        log(f"wrote {out / (f + '.parquet')}  {wide[f].shape[0]} x {wide[f].shape[1]}")
    _write_atomic(out / "meta.json", json.dumps(meta, indent=1, ensure_ascii=False).encode())
    log(f"wrote {out / 'meta.json'}  {len(meta['indices'])} indices")
    return meta


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

# NIFTY 50 closes that are a matter of public record (year-end closes, the
# 2008 and 2020 crash lows, two famous single days).
KNOWN_NIFTY50_CLOSE = {
    "2007-12-31": 6138.60, "2008-01-08": 6287.85, "2008-10-27": 2524.20, "2008-12-31": 2959.15,
    "2009-05-18": 4323.15, "2009-12-31": 5201.05, "2010-12-31": 6134.50, "2011-12-30": 4624.30,
    "2012-12-31": 5905.10, "2013-12-31": 6304.00, "2014-05-16": 7203.00, "2014-12-31": 8282.70,
    "2015-12-31": 7946.35, "2016-12-30": 8185.80, "2017-12-29": 10530.70, "2018-12-31": 10862.55,
    "2019-12-31": 12168.45, "2020-03-23": 7610.25, "2020-12-31": 13981.75, "2021-12-31": 17354.05,
}

WANTED = (
    "NIFTY 50", "NIFTY NEXT 50", "NIFTY 100", "NIFTY 200", "NIFTY 500", "NIFTY MIDCAP 150",
    "NIFTY MIDCAP 100", "NIFTY SMALLCAP 250", "NIFTY SMALLCAP 100", "NIFTY BANK", "NIFTY IT",
    "NIFTY FMCG", "NIFTY PHARMA", "NIFTY AUTO", "NIFTY METAL", "NIFTY REALTY", "NIFTY ENERGY",
    "NIFTY PSU BANK", "NIFTY FINANCIAL SERVICES", "NIFTY INFRASTRUCTURE", "NIFTY MEDIA",
    "NIFTY COMMODITIES", "INDIA VIX", "NIFTY200 MOMENTUM 30", "NIFTY100 LOW VOLATILITY 30",
    "NIFTY200 QUALITY 30", "NIFTY ALPHA 50", "NIFTY50 VALUE 20", "NIFTY500 VALUE 50",
    "NIFTY ALPHA LOW-VOLATILITY 30", "NIFTY MIDCAP150 MOMENTUM 50", "NIFTY500 MOMENTUM 50",
    "NIFTY 1D RATE INDEX",
)


def missing_days(s: pd.Series) -> int:
    """Calendar rows without a value between the series' first and last value."""
    v = s.dropna()
    return 0 if v.empty else int(s.loc[v.index[0]:v.index[-1]].isna().sum())


def validate(root=None, log=print) -> list[dict]:
    """Checks on the written files, read back through quant.data.store."""
    res: list[dict] = []

    def add(check: str, ok: bool, result: str):
        res.append({"check": check, "pass": bool(ok), "result": result})
        log(f"[{'PASS' if ok else 'FAIL'}] {check}: {result}")

    droot = store.data_root(root)
    meta = json.loads((droot / "index" / "meta.json").read_text())
    end = pd.Timestamp(meta["end"])
    w = {f: store.load_index(f, root=root) for f in FIELDS}
    close, tri = w["close"], w["tri"]

    bad = [f for f, d in w.items() if not (isinstance(d.index, pd.DatetimeIndex) and d.index.name == "date"
                                            and d.index.is_monotonic_increasing and d.index.is_unique
                                            and (d.dtypes == "float32").all() and d.columns.is_unique)]
    add("files load through store.load_index (DatetimeIndex 'date', sorted, unique, float32)", not bad,
        "; ".join(f"{f} {d.shape[0]}x{d.shape[1]}" for f, d in w.items()) + (f"; BAD: {bad}" if bad else ""))

    last = max(d.index.max() for d in w.values() if len(d))
    add("no row after the requested end / holdout lock", last <= end, f"last date {last.date()}, end {end.date()}")

    n50 = close[CALENDAR_INDEX]
    rows = []
    for d, exp in KNOWN_NIFTY50_CLOSE.items():
        if pd.Timestamp(d) < n50.index[0] or pd.Timestamp(d) > n50.index[-1]:
            continue
        got = float(n50.get(pd.Timestamp(d), np.nan))
        rows.append((d, exp, got, abs(got - exp) <= 0.011))
    add("NIFTY 50 close on well-known dates", bool(rows) and all(r[3] for r in rows),
        f"{sum(r[3] for r in rows)}/{len(rows)} match to the paisa; " +
        ", ".join(f"{d} {got:.2f}" + ("" if ok else f" (expected {exp:.2f})") for d, exp, got, ok in rows))

    for label, lo, hi in (("October 2008", "2008-10-01", "2008-10-31"), ("March 2020", "2020-03-01", "2020-03-31")):
        seg = n50.loc[lo:hi].dropna()
        low = w["low"].get(CALENDAR_INDEX, pd.Series(dtype="float32")).loc[lo:hi].dropna()
        if len(seg) > 15 and len(low) > 15:
            add(f"NIFTY 50 {label} low", True,
                f"lowest close {seg.min():.2f} on {seg.idxmin().date()}, intraday low {low.min():.2f} on {low.idxmin().date()}")

    both = [c for c in tri.columns if c in close.columns and meta["indices"][c]["fields"].get("tri", {}).get("source", "")
            .startswith("niftyindices")]
    slower, cmp_n = [], 0
    for c in both:
        j = pd.concat([close[c], tri[c]], axis=1, keys=["p", "t"]).dropna()
        if len(j) < 250:
            continue
        cmp_n += 1
        if j["t"].iloc[-1] / j["t"].iloc[0] <= j["p"].iloc[-1] / j["p"].iloc[0]:
            slower.append(c)
    j = pd.concat([n50, tri.get(CALENDAR_INDEX, pd.Series(dtype="float32"))], axis=1, keys=["p", "t"]).dropna()
    if len(j) < 250:
        add("NIFTY 50 total-return index grows faster than the price index", False,
            f"only {len(j)} days with both series")
    else:
        yrs = (j.index[-1] - j.index[0]).days / 365.25
        gp, gt = j["p"].iloc[-1] / j["p"].iloc[0], j["t"].iloc[-1] / j["t"].iloc[0]
        add("NIFTY 50 total-return index grows faster than the price index", gt > gp,
            f"{j.index[0].date()}..{j.index[-1].date()}: price x{gp:.2f} ({gp ** (1 / yrs) - 1:.2%}/yr), "
            f"TRI x{gt:.2f} ({gt ** (1 / yrs) - 1:.2%}/yr), dividend pick-up {(gt / gp) ** (1 / yrs) - 1:.2%}/yr")
    add("total return >= price return for every index with both series", not slower,
        f"{cmp_n - len(slower)}/{cmp_n} indices" + (f"; slower: {slower[:10]}" if slower else ""))

    g, at = longest_gap(n50)
    add("NIFTY 50: no gap longer than a long holiday weekend (<= 5 calendar days)", g <= 5,
        f"longest gap {g} calendar days after {at}; {len(n50.dropna())} trading days {n50.index[0].date()}..{n50.index[-1].date()}")

    miss = {c: missing_days(close[c]) for c in close.columns}
    holes = {c: m for c, m in miss.items() if m}
    wanted_holes = {c: m for c, m in holes.items() if c in WANTED}
    add("requested indices: close present on every trading day between first and last value", not wanted_holes,
        "no missing trading days" if not wanted_holes else f"missing trading days: {wanted_holes}")
    add("all indices: close present on every trading day between first and last value",
        len(holes) <= 0.1 * close.shape[1],
        f"{close.shape[1] - len(holes)}/{close.shape[1]} indices complete; with holes: "
        + (", ".join(f"{c} ({m})" for c, m in sorted(holes.items(), key=lambda x: -x[1])[:12]) or "none"))

    absent = [c for c in WANTED if c not in close.columns]
    add("every requested index is present in close", not absent,
        "; ".join(f"{c} {meta['indices'][c]['fields']['close']['first']}" for c in WANTED if c in close.columns)
        + (f"; ABSENT: {absent}" if absent else ""))
    no_tri = [c for c in WANTED if c not in tri.columns and c != VIX]
    add("every requested index (except INDIA VIX) has a total-return series", not no_tri,
        f"{len([c for c in WANTED if c in tri.columns])} present" + (f"; missing: {no_tri}" if no_tri else ""))

    o, h, l, c_ = (w[f].reindex(columns=close.columns) for f in ("open", "high", "low", "close"))
    full = o.notna() & h.notna() & l.notna() & c_.notna()
    viol = (full & ((h < np.maximum(o, c_) - 0.011) | (l > np.minimum(o, c_) + 0.011))).sum()
    add("high >= max(open, close) and low <= min(open, close)", int(viol.sum()) <= 1e-4 * int(full.sum().sum()),
        f"{int(viol.sum())} violations in {int(full.sum().sum())} bars"
        + (f"; worst: {viol[viol > 0].sort_values(ascending=False).head(6).to_dict()}" if viol.sum() else ""))

    nonpos = int((close <= 0).sum().sum())
    add("close is strictly positive", nonpos == 0, f"{nonpos} non-positive cells")

    eq = [c for c in close.columns if c != VIX]
    r = close[eq].pct_change(fill_method=None).abs()
    big = r.stack()
    big = big[big > 0.25]
    add("no one-day move above 25% in any index other than INDIA VIX", len(big) == 0,
        f"{len(big)} such moves" + (": " + ", ".join(f"{n} {d.date()} {v:.0%}" for (d, n), v in big.head(10).items()) if len(big) else ""))

    ag = meta["source_agreement"]
    tot = sum(a["cells_compared"] for a in ag.values())
    dif = sum(a["cells_differ"] for a in ag.values())
    add("niftyindices.com and the NSE daily file agree where both have a value", dif <= 0.005 * max(tot, 1),
        "; ".join(f"{f} {a['cells_differ']}/{a['cells_compared']} differ" for f, a in ag.items()))
    return res


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m quant.data.indices", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="download what is missing and write data/index/*.parquet")
    b.add_argument("--start", default="2003-01-01", type=date.fromisoformat)
    b.add_argument("--end", required=True, type=date.fromisoformat)
    b.add_argument("--root", default=None, help="data root (default: QUANT_DATA or <repo>/data)")
    b.add_argument("--workers", default=MAX_WORKERS, type=int, help=f"concurrent downloads (max {MAX_WORKERS})")
    b.add_argument("--offline", action="store_true", help="use only what is already cached")
    b.add_argument("--refresh-catalogue", action="store_true", help="re-read the index list from niftyindices.com")
    v = sub.add_parser("validate", help="check the written files")
    v.add_argument("--root", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build(a.start, a.end, root=a.root, workers=a.workers, offline=a.offline,
              refresh_catalogue=a.refresh_catalogue)
        return 0
    res = validate(a.root)
    return 0 if all(r["pass"] for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
