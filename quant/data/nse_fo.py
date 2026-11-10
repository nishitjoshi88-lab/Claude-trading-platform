"""NSE futures and options daily data, built from the derivatives bhavcopy.

Source (old "bhav.csv" format, one zip per trading day):

  https://nsearchives.nseindia.com/content/historical/DERIVATIVES/
      {YYYY}/{MON}/fo{DD}{MON}{YYYY}bhav.csv.zip

Command line (incremental: cached files are never fetched again):

  python -m quant.data.nse_fo build --start 2008-01-01 --end 2021-12-31

On disk, under the data root:

  raw/fo/zip/{YYYY}/fo{DD}{MON}{YYYY}bhav.csv.zip   files exactly as downloaded
  raw/fo/missing.json                               dates with no file (HTTP 404)
  raw/fo/parsed/{YYYY}.parquet                      rows kept from each year
  raw/fo/parsed/{YYYY}.lots.parquet                 lot-size evidence per contract-day
  fo/NIFTY.parquet, BANKNIFTY.parquet, FINNIFTY.parquet, STKFUT.parquet

See the section comments below for what each column holds and the places
where the raw file does not mean what its header suggests.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from .store import data_root

log = logging.getLogger("nse_fo")

HOSTS = ("nsearchives.nseindia.com", "archives.nseindia.com")
URL = "https://{host}/content/historical/DERIVATIVES/{y}/{mon}/fo{d:02d}{mon}{y}bhav.csv.zip"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
MAX_WORKERS = 6


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------
# Two files per trading day, told apart by `kind`:
#   "bhav"  the bhavcopy (every contract, prices, settlement, open interest)
#   "mkt"   the market activity report, used only for lot sizes: it prints
#           traded quantity next to the number of contracts. The archive
#           starts on MKT_START; nothing older exists.
MKT_URL = "https://{host}/archives/fo/mkt/fo{d:02d}{m:02d}{y}.zip"
MKT_START = pd.Timestamp("2011-02-01")
KINDS = ("bhav", "mkt")


def zip_name(date, kind: str = "bhav") -> str:
    d = pd.Timestamp(date)
    if kind == "mkt":
        return f"fo{d.day:02d}{d.month:02d}{d.year}.zip"
    return f"fo{d.day:02d}{MONTHS[d.month - 1]}{d.year}bhav.csv.zip"


def zip_path(date, root=None, kind: str = "bhav") -> Path:
    d = pd.Timestamp(date)
    sub = "mkt" if kind == "mkt" else "zip"
    return data_root(root) / "raw" / "fo" / sub / str(d.year) / zip_name(d, kind)


def zip_url(date, host: str = HOSTS[0], kind: str = "bhav") -> str:
    d = pd.Timestamp(date)
    if kind == "mkt":
        return MKT_URL.format(host=host, y=d.year, m=d.month, d=d.day)
    return URL.format(host=host, y=d.year, mon=MONTHS[d.month - 1], d=d.day)


def _missing_file(root=None, kind: str = "bhav") -> Path:
    name = "mkt_missing.json" if kind == "mkt" else "missing.json"
    return data_root(root) / "raw" / "fo" / name


def load_missing(root=None, kind: str = "bhav") -> set[str]:
    f = _missing_file(root, kind)
    return set(json.loads(f.read_text())["dates"]) if f.exists() else set()


def save_missing(dates: set[str], root=None, kind: str = "bhav") -> None:
    f = _missing_file(root, kind)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    note = ("trading days for which the archive has no market activity report (HTTP 404)"
            if kind == "mkt" else
            "dates for which the archive returned HTTP 404 (weekends, holidays)")
    tmp.write_text(json.dumps({"note": note, "dates": sorted(dates)}, indent=0))
    tmp.replace(f)


def _valid_zip(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            return any(n.lower().endswith(".csv") for n in z.namelist()) and z.testzip() is None
    except zipfile.BadZipFile:
        return False


_local = threading.local()


def _session():
    import requests
    if getattr(_local, "s", None) is None:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*",
                          "Accept-Language": "en-US,en;q=0.9"})
        _local.s = s
    return _local.s


def fetch_one(date, root=None, retries: int = 5, get=None, kind: str = "bhav") -> str:
    """Fetch one day's file into the cache. Returns 'ok', 'missing' (every
    host answered 404) or 'error' (anything else; nothing is cached, so the
    next run tries again). `get(url) -> (status, bytes)` can be injected."""
    path = zip_path(date, root, kind)
    if get is None:
        def get(url):
            r = _session().get(url, timeout=60)
            return r.status_code, r.content
    statuses = []
    for attempt in range(retries):
        statuses = []
        for host in HOSTS:
            try:
                status, content = get(zip_url(date, host, kind))
            except Exception as e:                       # network error: retry
                statuses.append(f"{type(e).__name__}")
                continue
            statuses.append(status)
            if status == 200 and _valid_zip(content):
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(".part")
                tmp.write_bytes(content)
                tmp.replace(path)
                return "ok"
        # The first host carries the whole archive; the second answers 403 for
        # older years. "No such file" is the first host's 404, provided the
        # second one did not contradict it with a file.
        if statuses and statuses[0] == 404 and all(s in (403, 404) for s in statuses):
            return "missing"
        time.sleep(min(30.0, 1.5 * 2 ** attempt))
    log.warning("could not fetch %s: %s", zip_name(date, kind), statuses)
    return "error"


def _fetch_many(todo, root, workers, get, kind, missing) -> dict:
    out = {"ok": 0, "missing": 0, "error": 0, "errors": []}
    if not todo:
        return out
    log.info("downloading %d %s file(s) with %d workers", len(todo), kind, workers)
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        results = ex.map(lambda d: fetch_one(d, root, get=get, kind=kind), todo)
        for i, (d, res) in enumerate(zip(todo, results)):
            out[res] += 1
            if res == "missing":
                missing.add(d.strftime("%Y-%m-%d"))
            elif res == "error":
                out["errors"].append(d.strftime("%Y-%m-%d"))
            if (i + 1) % 250 == 0:
                save_missing(missing, root, kind)
                log.info("  %d/%d  ok=%d missing=%d error=%d  %.0fs", i + 1, len(todo),
                         out["ok"], out["missing"], out["error"], time.time() - t0)
    save_missing(missing, root, kind)
    return out


def download(start, end, root=None, workers: int = MAX_WORKERS, recheck_missing: bool = False,
             get=None) -> dict:
    """Fetch the bhavcopy of every calendar day in [start, end] that is not
    cached yet. Weekends are probed too: NSE holds special sessions on some."""
    workers = max(1, min(workers, MAX_WORKERS))
    days = pd.date_range(start, end, freq="D")
    missing = set() if recheck_missing else load_missing(root)
    todo = [d for d in days if not zip_path(d, root).exists() and d.strftime("%Y-%m-%d") not in missing]
    out = _fetch_many(todo, root, workers, get, "bhav", missing)
    out["cached"] = len(days) - len(todo)
    # A long run of weekdays with no file means the archive has ended, not a holiday.
    have = [zip_path(d, root).exists() for d in days]
    gap = run = 0
    for d, h in zip(days, have):
        run = 0 if h else run + (d.weekday() < 5)
        gap = max(gap, run)
    if gap > 10:
        log.warning("%d consecutive weekdays without a file: this bhavcopy format may not "
                    "exist for part of the requested range", gap)
    out["longest_weekday_gap"] = gap
    return out


def download_mkt(start, end, root=None, workers: int = MAX_WORKERS, recheck_missing: bool = False,
                 get=None) -> dict:
    """Fetch the market activity report of every day in [start, end] that has
    a cached bhavcopy (i.e. was a trading day) and lies on or after MKT_START."""
    workers = max(1, min(workers, MAX_WORKERS))
    days = [d for d in cached_dates(max(pd.Timestamp(start), MKT_START), end, root)]
    missing = set() if recheck_missing else load_missing(root, "mkt")
    todo = [d for d in days if not zip_path(d, root, "mkt").exists()
            and d.strftime("%Y-%m-%d") not in missing]
    out = _fetch_many(todo, root, workers, get, "mkt", missing)
    out["cached"] = len(days) - len(todo)
    return out


def cached_dates(start, end, root=None, kind: str = "bhav") -> list[pd.Timestamp]:
    return [d for d in pd.date_range(start, end, freq="D") if zip_path(d, root, kind).exists()]


# --------------------------------------------------------------------------
# Parsing one day's file
# --------------------------------------------------------------------------
INDEX_SYMBOLS = ("NIFTY", "BANKNIFTY", "FINNIFTY")
_HEADER_ALIASES = {"OPTIONTYPE": "OPTION_TYP"}        # one 2008 file spells it this way
_TEXT = ("INSTRUMENT", "SYMBOL", "EXPIRY_DT", "OPTION_TYP", "TIMESTAMP")
_NUMERIC = ("STRIKE_PR", "OPEN", "HIGH", "LOW", "CLOSE", "SETTLE_PR", "CONTRACTS",
            "VAL_INLAKH", "OPEN_INT")
_DATE_FORMATS = ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d", "%d/%m/%Y")
RAW_COLUMNS = ["date", "inst", "symbol", "expiry", "strike", "right", "open", "high", "low",
               "close", "settle", "contracts", "value", "oi"]


def parse_date(text: str) -> pd.Timestamp:
    """'31-Jan-2008', '31-JAN-2008', '1-JAN-2008' and '31-Jan-08' all occur
    or have occurred in NSE files. Anything unrecognised raises."""
    from datetime import datetime
    t = text.strip()
    for fmt in _DATE_FORMATS:
        try:
            return pd.Timestamp(datetime.strptime(t, fmt))
        except ValueError:
            pass
    raise ValueError(f"unrecognised date {text!r}")


def _dates(col: pd.Series) -> pd.Series:
    table = {u: parse_date(u) for u in col.unique()}
    return col.map(table).astype("datetime64[ns]")


def read_bhavcopy(source) -> pd.DataFrame:
    """Every row of one bhavcopy, columns renamed to RAW_COLUMNS and typed.
    `source` is a path (.zip or .csv) or the bytes of either.

    inst is the file's INSTRUMENT (FUTIDX, FUTSTK, OPTIDX, OPTSTK, ...), right
    is CE/PE (CA/PA for the American stock options of 2008-2010) or "" for
    futures, value is VAL_INLAKH: lakh of rupees, premium turnover for futures
    and (strike + premium) turnover for options. oi is in units of the
    underlying, not contracts. contracts is left as a float: on the eve of
    a few corporate actions the file restates the day's volume in the new lot
    and prints fractions (LT on 2013-07-10: 5561.33)."""
    data = Path(source).read_bytes() if isinstance(source, (str, Path)) else bytes(source)
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError(f"expected one csv in the zip, found {z.namelist()}")
            data = z.read(names[0])
    header = data[:data.find(b"\n")].decode("latin-1").strip().split(",")
    names = [_HEADER_ALIASES.get(c.strip().upper(), c.strip().upper()) or f"_{i}"
             for i, c in enumerate(header)]
    lacking = [c for c in _TEXT + _NUMERIC if c not in names]
    if lacking:
        raise ValueError(f"bhavcopy lacks columns {lacking}; header was {header}")
    common = dict(names=names, header=0, usecols=list(_TEXT + _NUMERIC), encoding="latin-1",
                  skip_blank_lines=True, index_col=False)
    try:                                   # fast path: numbers parsed by the csv reader
        df = pd.read_csv(io.BytesIO(data), dtype={**{c: str for c in _TEXT},
                                                  **{c: "float64" for c in _NUMERIC}}, **common)
        num = {c: df[c] for c in _NUMERIC}
    except ValueError:                     # padded or quoted numbers: strip, then convert
        df = pd.read_csv(io.BytesIO(data), dtype=str, **common)
        num = {c: pd.to_numeric(df[c].str.strip(), errors="raise") for c in _NUMERIC}
    keep = df["INSTRUMENT"].notna() & df["SYMBOL"].notna()
    df, num = df[keep], {c: v[keep] for c, v in num.items()}
    text = {c: df[c].str.strip() for c in _TEXT}
    for c in _NUMERIC:
        if num[c].isna().any():
            raise ValueError(f"{c} has blanks")
    oi = num["OPEN_INT"].round().astype("int64")
    if not np.allclose(oi, num["OPEN_INT"]):
        raise ValueError("OPEN_INT is not a whole number everywhere")
    right = text["OPTION_TYP"].str.upper().replace({"XX": "", "FF": ""}).fillna("")
    out = pd.DataFrame({
        "date": _dates(text["TIMESTAMP"]),
        "inst": text["INSTRUMENT"].str.upper(),
        "symbol": text["SYMBOL"].str.upper(),
        "expiry": _dates(text["EXPIRY_DT"]),
        "strike": num["STRIKE_PR"],
        "right": right,
        "open": num["OPEN"], "high": num["HIGH"], "low": num["LOW"],
        "close": num["CLOSE"], "settle": num["SETTLE_PR"],
        "contracts": num["CONTRACTS"],
        "value": num["VAL_INLAKH"],
        "oi": oi,
    })
    return out.reset_index(drop=True)


# Lot-size evidence. The file has no lot column, but for every traded row
#   VAL_INLAKH * 1e5 = contracts * lot * (average traded price [+ strike, for options])
# and the average lies between LOW and HIGH, so each row brackets the lot.
# VAL_INLAKH is printed to 0.01 lakh, hence the allowance.
VALUE_TOLERANCE = 0.0101


def lot_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """Per (date, kind, symbol, expiry, src): the range [lo, hi] that the lot
    must lie in, intersected over the n traded rows. kind is IDX or STK; src
    is F (futures rows) or O (option rows). lo > hi means the rows disagree."""
    kind = df["inst"].str[3:]
    src = df["inst"].str[0]
    ok = (df["inst"].isin(["FUTIDX", "FUTSTK", "OPTIDX", "OPTSTK"]) & (df["contracts"] > 0)
          & (df["value"] > 0) & (df["low"] > 0) & (df["high"] >= df["low"]))
    d = df[ok]
    base = np.where(src[ok] == "O", d["strike"], 0.0)
    rupees = d["contracts"] * 1.0
    lo = (d["value"] - VALUE_TOLERANCE).clip(lower=0) * 1e5 / (rupees * (base + d["high"]))
    hi = (d["value"] + VALUE_TOLERANCE) * 1e5 / (rupees * (base + d["low"]))
    g = pd.DataFrame({"date": d["date"], "kind": kind[ok], "symbol": d["symbol"], "expiry": d["expiry"],
                      "src": src[ok], "lo": lo, "hi": hi})
    g = g.groupby(["date", "kind", "symbol", "expiry", "src"], sort=True).agg(
        lo=("lo", "max"), hi=("hi", "min"), n=("lo", "size")).reset_index()
    return g


# --------------------------------------------------------------------------
# Yearly cache of the rows that are kept
# --------------------------------------------------------------------------
PARSER_VERSION = 1
OUTPUTS = INDEX_SYMBOLS + ("STKFUT",)
PRICE_COLUMNS = ["open", "high", "low", "close", "settle"]
FO_COLUMNS = ["date", "instrument", "expiry", "strike", "right", "open", "high", "low", "close",
              "settle", "contracts", "oi", "lot", "underlying"]


def whole_contracts(c: pd.Series) -> pd.Series:
    """Contracts as integers. The rare fractional figure is rounded, and a
    traded row never rounds down to zero."""
    r = c.round()
    return r.mask((c > 0) & (r == 0), 1).astype("int64")


def to_store_rows(raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split one day's rows into the four outputs, in the store's column
    layout (lot and underlying are added later).

    What is changed relative to the file, and nothing else:
      * instrument is FUT or OPT; right is CE, PE or "" (the file says XX).
      * open/high/low are NaN where no contract traded (the file prints 0).
      * contracts is rounded to a whole number where the file has a fraction.
      * strike stays 0 for futures, close and settle stay exactly as given,
        including zeros.
    """
    kept = {}
    idx = raw["inst"].isin(["FUTIDX", "OPTIDX"])
    stk = raw["inst"] == "FUTSTK"
    for name in OUTPUTS:
        sel = raw[stk] if name == "STKFUT" else raw[idx & (raw["symbol"] == name)]
        out = pd.DataFrame({
            "date": sel["date"],
            "instrument": sel["inst"].str[:3],
            "expiry": sel["expiry"],
            "strike": sel["strike"].astype("float32"),
            "right": sel["right"],
        })
        untraded = sel["contracts"] == 0
        for c in PRICE_COLUMNS:
            v = sel[c]
            if c in ("open", "high", "low"):
                v = v.mask(untraded & (v == 0))
            out[c] = v.astype("float32")
        out["contracts"] = whole_contracts(sel["contracts"])
        out["oi"] = sel["oi"]
        if name == "STKFUT":
            out["symbol"] = sel["symbol"]
        kept[name] = out.reset_index(drop=True)
    return kept


def _parsed_dir(root=None) -> Path:
    return data_root(root) / "raw" / "fo" / "parsed"


def _year_manifest(year: int, root=None) -> dict:
    files = {}
    for d in cached_dates(f"{year}-01-01", f"{year}-12-31", root):
        files[d.strftime("%Y-%m-%d")] = zip_path(d, root).stat().st_size
    return {"version": PARSER_VERSION, "files": files}


def parse_year(year: int, root=None, force: bool = False) -> dict:
    """Parse every cached file of one calendar year into raw/fo/parsed.
    Skipped when the cache already reflects exactly the files on disk."""
    pdir = _parsed_dir(root)
    pdir.mkdir(parents=True, exist_ok=True)
    mf = pdir / f"{year}.json"
    want = _year_manifest(year, root)
    if not force and mf.exists():
        have = json.loads(mf.read_text())
        if have.get("version") == want["version"] and have.get("files") == want["files"]:
            return {"year": year, "days": len(want["files"]), "parsed": False, "problems": have.get("problems", [])}
    parts = {name: [] for name in OUTPUTS}
    lots, problems = [], []
    for day in want["files"]:
        try:
            raw = read_bhavcopy(zip_path(day, root))
        except Exception as e:
            problems.append(f"{day}: unreadable ({type(e).__name__}: {e})")
            continue
        stamps = raw["date"].unique()
        if len(stamps) != 1 or pd.Timestamp(stamps[0]) != pd.Timestamp(day):
            problems.append(f"{day}: file is stamped {[str(pd.Timestamp(s).date()) for s in stamps]}; skipped")
            continue
        frac = raw["contracts"] != raw["contracts"].round()
        if frac.any():
            who = sorted(raw.loc[frac, "symbol"].unique())
            problems.append(f"{day}: {int(frac.sum())} rows with fractional CONTRACTS ({', '.join(who)}); "
                            f"rounded in the kept rows")
        dup = raw.duplicated(["inst", "symbol", "expiry", "strike", "right"])
        if dup.any():
            problems.append(f"{day}: {int(dup.sum())} duplicate contract rows dropped")
            raw = raw[~dup]
        for name, part in to_store_rows(raw).items():
            parts[name].append(part)
        b = lot_bounds(raw)
        lots.append(b[(b["kind"] == "STK") | b["symbol"].isin(INDEX_SYMBOLS)])
    for name in OUTPUTS:
        f = pdir / f"{year}.{name}.parquet"
        frames = [p for p in parts[name] if len(p)]
        if frames:
            pd.concat(frames, ignore_index=True).to_parquet(f, index=False)
        elif f.exists():
            f.unlink()
    if lots:
        pd.concat(lots, ignore_index=True).to_parquet(pdir / f"{year}.lots.parquet", index=False)
    want["problems"] = problems
    mf.write_text(json.dumps(want))
    return {"year": year, "days": len(want["files"]), "parsed": True, "problems": problems}


def parse_years(years, root=None, workers: int = 3, force: bool = False) -> list[dict]:
    years = list(years)
    if workers <= 1 or len(years) <= 1:
        return [parse_year(y, root, force) for y in years]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(min(workers, len(years))) as ex:
        return list(ex.map(parse_year, years, [root] * len(years), [force] * len(years)))


# --------------------------------------------------------------------------
# Lot sizes derived from the files
# --------------------------------------------------------------------------
# Two facts pin the lot of a contract down exactly:
#   1. open interest is printed in units of the underlying, so it is a whole
#      multiple of the lot on every day;
#   2. traded value brackets the lot (lot_bounds above).
# The lot is the divisor of the open interest that lies inside the bracket.
# Option rows give a strict, narrow bracket. Futures rows do not: calendar
# spread trades count towards value at prices that can lie outside the day's
# low-high range, which shifts the bracket by up to about 2%, so it is
# widened by FUT_SLACK before use.
FUT_SLACK = 0.03
_NONE = np.empty(0, dtype=np.int64)


def contract_days(rows: pd.DataFrame, bounds: pd.DataFrame) -> pd.DataFrame:
    """One line per (symbol, expiry, date): g = greatest common divisor of the
    open interest of the contract's rows (0 if none), [lo, hi] = the bracket
    used for the lot (NaN on days without trades) and [slo, shi] = the same
    bracket without slack."""
    key = ["symbol", "expiry", "date"]
    r = rows[key + ["oi"]].sort_values(key, kind="stable")
    first = (r[key] != r[key].shift()).any(axis=1).to_numpy()
    starts = np.flatnonzero(first)
    out = r.loc[first, key].reset_index(drop=True)
    out["g"] = np.gcd.reduceat(r["oi"].to_numpy(np.int64), starts) if len(r) else _NONE
    b = bounds.pivot_table(index=key, columns="src", values=["lo", "hi"])
    b.columns = [f"{v}_{s}" for v, s in b.columns]
    for c in ("lo_F", "hi_F", "lo_O", "hi_O"):
        if c not in b.columns:
            b[c] = np.nan
    out = out.merge(b.reset_index(), on=key, how="left")
    opt = out["lo_O"] <= out["hi_O"]                    # option rows present and consistent
    out["lo"] = np.where(opt, out["lo_O"], out["lo_F"] * (1 - FUT_SLACK))
    out["hi"] = np.where(opt, out["hi_O"], out["hi_F"] * (1 + FUT_SLACK))
    out["slo"] = np.where(opt, out["lo_O"], out["lo_F"])
    out["shi"] = np.where(opt, out["hi_O"], out["hi_F"])
    return out[key + ["g", "lo", "hi", "slo", "shi"]]


def _candidates(g: int, lo: float, hi: float) -> np.ndarray:
    a, b = max(1, int(np.ceil(lo))), int(np.floor(hi))
    if b < a:
        return _NONE
    d = np.arange(a, b + 1, dtype=np.int64)
    return d[g % d == 0]


def _fits(c: np.ndarray, g: int, lo: float, hi: float) -> np.ndarray:
    return c[(g % c == 0) & (c >= lo) & (c <= hi)]


def lots_of_contract(g, lo, hi, slo, shi) -> np.ndarray:
    """Lot per day of one contract (days in date order), NaN where the files
    do not settle it. The lot is constant within a contract except across a
    corporate action, so days are grouped into runs that share a candidate."""
    n = len(g)
    use = np.flatnonzero((g > 0) & ~np.isnan(lo) & (lo <= hi))   # days that carry evidence
    runs = []                                            # [first day, last day, candidates]
    cand, s, e = None, -1, -1
    for i, t in enumerate(use):
        if cand is not None:
            keep = _fits(cand, g[t], lo[t], hi[t])
            if keep.size == 0 and lo[t] == slo[t]:       # see the note on option brackets below
                keep = cand[(cand >= slo[t]) & (cand <= shi[t])]
                keep = keep if np.floor(shi[t]) == np.ceil(slo[t]) else _NONE
            if keep.size:
                cand, e = keep, t
                continue
            if i + 1 < len(use):                         # one odd day, or a new lot?
                u = use[i + 1]
                if _fits(cand, g[u], lo[u], hi[u]).size:
                    continue                             # the old lot is back tomorrow: skip today
        fresh = _candidates(g[t], lo[t], hi[t])
        if fresh.size == 0 and lo[t] == slo[t]:
            # Option bracket, but the open interest is no multiple of anything in
            # it. That happens after an exchange-wide lot revision: positions
            # opened under the old lot stay on the books in their old units.
            # A strict bracket holding a single whole number is enough by itself.
            a, b = int(np.ceil(slo[t])), int(np.floor(shi[t]))
            if a == b:
                fresh = np.array([a], dtype=np.int64)
        if fresh.size == 0:
            continue                                     # the day contradicts itself
        if cand is not None:
            runs.append((s, e, cand))
        cand, s, e = fresh, t, t
    if cand is not None:
        runs.append((s, e, cand))

    value = []                                           # the lot of each run, or NaN
    for s, e, cand in runs:
        if cand.size > 1:                                # prefer the one inside most strict brackets
            days = use[(use >= s) & (use <= e)]
            support = np.array([((slo[days] <= c) & (c <= shi[days])).sum() for c in cand])
            cand = cand[support == support.max()]
        value.append(float(cand[0]) if cand.size == 1 else np.nan)

    lot = np.full(n, np.nan)
    if not runs:
        return lot
    starts = np.array([r[0] for r in runs])
    ends = np.array([r[1] for r in runs])
    for t in range(n):
        k = np.searchsorted(starts, t, side="right") - 1      # last run starting at or before t
        if k >= 0 and t <= ends[k]:
            lot[t] = value[k]
            continue
        a = value[k] if k >= 0 else None                      # run before t
        b = value[k + 1] if k + 1 < len(runs) else None       # run after t
        ok = [v for v in (a, b) if v is not None and not np.isnan(v)
              and (g[t] == 0 or g[t] % int(v) == 0)]
        if a is not None and b is not None:
            if np.isnan(a) or np.isnan(b):
                continue
            if a == b:
                lot[t] = a
            elif g[t] > 0 and len(ok) == 1:                   # open interest fits only one of them
                lot[t] = ok[0]
        elif len(ok) == 1:
            lot[t] = ok[0]
    return lot


def derive_lots(days: pd.DataFrame) -> pd.Series:
    """Lot for every line of contract_days() output (same index)."""
    d = days.sort_values(["symbol", "expiry", "date"], kind="stable")
    g = d["g"].to_numpy(np.int64)
    lo, hi = d["lo"].to_numpy(float), d["hi"].to_numpy(float)
    slo, shi = d["slo"].to_numpy(float), d["shi"].to_numpy(float)
    new = ((d["symbol"] != d["symbol"].shift()) | (d["expiry"] != d["expiry"].shift())).to_numpy()
    edges = np.append(np.flatnonzero(new), len(d))
    lot = np.full(len(d), np.nan)
    for a, b in zip(edges[:-1], edges[1:]):
        lot[a:b] = lots_of_contract(g[a:b], lo[a:b], hi[a:b], slo[a:b], shi[a:b])
    d = d.assign(lot=lot)

    # A corporate action changes the lot of every expiry of a symbol on the
    # same day. Lines before a contract's first evidence (or after its last)
    # were given that contract's nearest known lot; where a sibling expiry
    # shows a change in between, that is not safe.
    d["known"] = (d["g"] > 0) & d["lo"].notna() & d["lot"].notna()
    grp = d.groupby(["symbol", "expiry"], sort=False)
    prev = grp["lot"].shift()
    changed = d["known"] & prev.notna() & (prev != d["lot"])
    events = d.loc[changed, ["symbol", "date"]].drop_duplicates()
    if len(events):
        first = d[d["known"]].groupby(["symbol", "expiry"], sort=False)["date"].agg(["min", "max"])
        d = d.join(first, on=["symbol", "expiry"])
        for sym, when in events.groupby("symbol")["date"]:
            m = d["symbol"] == sym
            for e in when:
                lead = m & (d["date"] < e) & (d["min"] >= e)
                trail = m & (d["date"] >= e) & (d["max"] < e)
                d.loc[lead | trail, "lot"] = np.nan
        d = d.drop(columns=["min", "max"])

    # Lines still open take the lot of the symbol's other expiries on that
    # day, when those agree with each other and the line's own evidence backs
    # them: its open interest is a multiple, or its value bracket contains it.
    # With neither (no trade, no open interest) the peer lot is taken only if
    # the contract has evidence on some other day; a contract that never
    # traded and never had open interest stays NaN.
    has = d.groupby(["symbol", "expiry"], sort=False)["known"].transform("any")
    peers = d[d["lot"].notna()].groupby(["symbol", "date"])["lot"].agg(["min", "max"])
    peers = peers[peers["min"] == peers["max"]]["min"].rename("peer")
    d = d.join(peers, on=["symbol", "date"])
    multiple = (d["g"] > 0) & (d["g"] % d["peer"].fillna(1).astype("int64") == 0)
    inside = (d["lo"] <= d["peer"]) & (d["peer"] <= d["hi"])
    silent = (d["g"] == 0) & d["lo"].isna() & has
    take = d["lot"].isna() & d["peer"].notna() & (multiple | inside | silent)
    d.loc[take, "lot"] = d.loc[take, "peer"]
    return d["lot"].reindex(days.index)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m quant.data.nse_fo")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("download", "download-mkt"):
        b = sub.add_parser(name)
        b.add_argument("--start", required=True)
        b.add_argument("--end", required=True)
        b.add_argument("--root", default=None)
        b.add_argument("--workers", type=int, default=MAX_WORKERS)
        b.add_argument("--recheck-missing", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    if a.cmd == "download":
        print(json.dumps(download(a.start, a.end, a.root, a.workers, a.recheck_missing)))
    if a.cmd == "download-mkt":
        print(json.dumps(download_mkt(a.start, a.end, a.root, a.workers, a.recheck_missing)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
