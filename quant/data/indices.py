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


# --------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------

# Names used in the daily file over the years -> today's official name (upper
# case, as listed on niftyindices.com). Keys are upper case with single
# spaces. Every entry was checked against the data: the old name's last day
# and the new name's first day are consecutive trading days and the index
# level is continuous across the change. A name not listed here is kept as is.
ALIASES: dict[str, str] = {}


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
    Rows without a closing value are dropped.
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
    return pd.DataFrame(out, columns=LONG_COLS)


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


def compare_sources(a: pd.DataFrame, b: pd.DataFrame, tol: float) -> pd.DataFrame:
    """Per index: cells present in both, how many differ by more than `tol`
    (relative), and the largest relative difference."""
    cols = a.columns.intersection(b.columns)
    idx = a.index.intersection(b.index)
    x, y = a.reindex(index=idx, columns=cols), b.reindex(index=idx, columns=cols)
    both = x.notna() & y.notna()
    rel = ((x - y).abs() / y.abs().where(y != 0)).where(both)
    out = pd.DataFrame({"n_both": both.sum(), "n_differ": (rel > tol).sum(), "max_rel": rel.max()})
    return out[out["n_both"] > 0]


def longest_gap(s: pd.Series) -> tuple[int, str | None]:
    """Longest run of calendar days between consecutive observations."""
    d = s.dropna().index
    if len(d) < 2:
        return 0, None
    gaps = (d[1:] - d[:-1]).days
    i = int(np.argmax(gaps))
    return int(gaps[i]), str(d[i].date())


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


def fetch_index_list(raw: Path, refresh: bool = False, log=print) -> dict:
    """The index catalogue of niftyindices.com: {"indices": {official name:
    category}, "trading_names": {...}}. Cached in niftyindices/catalogue.json."""
    f = raw / "niftyindices" / "catalogue.json"
    if f.exists() and not refresh:
        return json.loads(f.read_text())
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
    return raw / "niftyindices" / (kind + "_alt" if alt else kind) / slug(name) / f"{s:%Y%m%d}_{e:%Y%m%d}.json"


def fetch_ni(raw: Path, kind: str, name: str, req_name: str, s: date, e: date, alt: bool = False) -> list[dict]:
    """One history window for one index, through the cache. Rows dated
    outside [s, e] are discarded before anything is written to disk.
    `alt` marks a second attempt under another spelling (cached separately)."""
    p = ni_path(raw, kind, name, s, e, alt)
    if p.exists():
        return json.loads(p.read_text())["rows"]
    date_key = _NI_COLS[kind][0]

    def go():
        rows = decode_ni(_ni_post(NI_ENDPOINT[kind], headers={"Content-Type": "application/json; charset=UTF-8"},
                                  data=ni_body(req_name, name, s, e).encode("utf-8")))
        return [r for r in rows if pd.Timestamp(s) <= _parse_date(r[date_key]) <= pd.Timestamp(e)]

    rows = _retry(go, f"niftyindices {kind} {name} {s}..{e}")
    _write_atomic(p, json.dumps({"name": name, "request_name": req_name, "kind": kind, "start": str(s),
                                 "end": str(e), "rows": rows}, ensure_ascii=False).encode())
    return rows


def _run_ni_jobs(raw: Path, jobs: list[tuple], workers: int, failed: list, log, label: str) -> dict:
    """jobs: (kind, name, request name, start, end, alt). Returns {(kind, name): rows}."""
    rows: dict[tuple[str, str], list] = {(k, n): [] for k, n, *_ in jobs}
    todo = sum(not ni_path(raw, k, n, s, e, alt).exists() for k, n, _, s, e, alt in jobs)
    log(f"niftyindices {label}: {len(jobs)} requests, {todo} not cached")

    def one(job):
        k, n, rn, s, e, alt = job
        try:
            return job, fetch_ni(raw, k, n, rn, s, e, alt), None
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


def download_ni(raw: Path, catalogue: dict, start: date, end: date, workers: int = 4, log=print) -> dict:
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
    rows = _run_ni_jobs(raw, jobs, workers, failed, log, "history")
    # The site sends its short "trading" name. The valuation endpoint needs
    # it; the price and total-return endpoints also accept the official name.
    # Where the trading name produced nothing at all, try the official name.
    again = [(k, n, squash(n), s, e, True) for (k, n), r in rows.items()
             if not r and request_name(n, tn) != squash(n) for s, e in blocks]
    if again:
        for key, r in _run_ni_jobs(raw, again, workers, failed, log, "second spelling").items():
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
            parts.append(df)
        d += timedelta(1)
    long = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=LONG_COLS)
    return long, problems
