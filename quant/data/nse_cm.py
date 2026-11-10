"""NSE cash-market daily panel builder.

    python -m quant.data.nse_cm build --start 2003-01-01 --end 2021-12-31

Stages (each one is incremental and safe to re-run):

  download   bhavcopy zips (one per calendar day tried; a 404 means no session),
             security-wise delivery files (MTO), the daily "PR" press bundle
             (only its corporate-action and ETF members are kept), the NSE
             corporate-action feed and the symbol-change list.
  parse      raw files -> one long parquet per year under data/raw/cm/parsed.
  panel      symbol continuity, adjustment events, wide panels under data/cm
             and the liquid subset under data/cm_liquid.

Nothing here invents prices. Adjustment factors come from exchange-published
corporate actions (and a short, sourced, hand-verified list for the years the
feeds do not cover); see `build_events` and the `meta.json` written next to
the panels for the exact treatment of splits, bonuses, rights, demergers and
dividends.

HOLDOUT: the end date is clipped to data/LOCK unless QUANT_UNLOCK_HOLDOUT=1,
and every reference file that carries later rows (symbol changes, corporate
actions) is filtered to the end date before it is used.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import io
import json
import logging
import os
import re
import sys
import threading
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from quant.data import store

log = logging.getLogger("nse_cm")

HOSTS = ("https://nsearchives.nseindia.com", "https://archives.nseindia.com")
UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
KEEP_SERIES = ("EQ", "BE", "BZ")
SERIES_RANK = {"EQ": 0, "BE": 1, "BZ": 2}
MAX_WORKERS = 6
PR_FIRST_DATE = dt.date(2010, 1, 1)      # the PR press bundle does not exist before 2010
CA_API_FIRST_DATE = dt.date(2005, 1, 1)  # the corporate-action feed is empty before 2005


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------

def raw_dir(root=None) -> Path:
    return store.data_root(root) / "raw" / "cm"


def clip_end(end, root=None) -> dt.date:
    """Clip the requested end date to the holdout lock."""
    end = pd.Timestamp(end).date()
    lock = store.lock_date(root)
    if lock is not None and end > lock.date():
        log.warning("end %s is after the holdout lock %s; clipped", end, lock.date())
        end = lock.date()
    return end


def bhav_path(d: dt.date, root=None) -> Path:
    mon = d.strftime("%b").upper()
    return raw_dir(root) / "bhav" / str(d.year) / f"cm{d:%d}{mon}{d.year}bhav.csv.zip"


def bhav_url_path(d: dt.date) -> str:
    mon = d.strftime("%b").upper()
    return f"/content/historical/EQUITIES/{d.year}/{mon}/cm{d:%d}{mon}{d.year}bhav.csv.zip"


def mto_path(d: dt.date, root=None) -> Path:
    return raw_dir(root) / "mto" / str(d.year) / f"MTO_{d:%d%m%Y}.DAT"


def mto_url_path(d: dt.date) -> str:
    return f"/archives/equities/mto/MTO_{d:%d%m%Y}.DAT"


def pr_dir(d: dt.date, root=None) -> Path:
    return raw_dir(root) / "pr" / str(d.year)


def pr_url_path(d: dt.date) -> str:
    return f"/archives/equities/bhavcopy/pr/PR{d:%d%m%y}.zip"


# --------------------------------------------------------------------------
# download
# --------------------------------------------------------------------------

_tls = threading.local()


def _session():
    import requests
    s = getattr(_tls, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update(UA)
        _tls.s = s
    return s


class FetchError(RuntimeError):
    pass


def http_get(url_path: str, tries: int = 6, timeout: int = 60, hosts=HOSTS):
    """GET from the archive hosts. Returns bytes, or None for a confirmed 404.

    The primary host (`nsearchives`) answers a clean 404 for a file that does
    not exist; that answer is asked for twice before it is believed. The older
    `archives` host answers 403 both for missing files and for many files the
    primary serves, so it is only used as a fallback when the primary fails
    with something other than 404. Failures are retried with backoff.
    """
    last = None
    n404 = 0
    for i in range(tries):
        host = hosts[0] if (i % 3 != 2 or n404) else hosts[-1]
        try:
            r = _session().get(host + url_path, timeout=timeout)
            if r.status_code == 200:
                return r.content
            if r.status_code == 404 and host == hosts[0]:
                n404 += 1
                if n404 >= 2:
                    return None
                time.sleep(0.3)
                continue
            last = f"HTTP {r.status_code} from {host}"
        except Exception as e:  # network errors: retry
            last = f"{type(e).__name__}: {str(e)[:120]}"
        time.sleep(min(30.0, 1.0 * 2 ** i))
    raise FetchError(f"{url_path}: {last}")


def _atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, path)


class MissingSet:
    """Dates the server answered 404 for, so re-runs do not ask again."""

    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.dates = set()
        if path.exists():
            self.dates = {l.strip() for l in path.read_text().split() if l.strip()}

    def __contains__(self, d: dt.date):
        return d.isoformat() in self.dates

    def add(self, d: dt.date):
        with self.lock:
            if d.isoformat() not in self.dates:
                self.dates.add(d.isoformat())
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path, "a") as f:
                    f.write(d.isoformat() + "\n")


def _run_pool(fn, items, label, workers=MAX_WORKERS):
    errors, done = [], 0
    if not items:
        return errors
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, it): it for it in items}
        for fut in cf.as_completed(futs):
            done += 1
            try:
                fut.result()
            except Exception as e:
                errors.append((futs[fut], str(e)))
            if done % 500 == 0 or done == len(items):
                log.info("%s: %d/%d (%d errors)", label, done, len(items), len(errors))
    return errors


def daterange(start: dt.date, end: dt.date):
    d = start
    while d <= end:
        yield d
        d += dt.timedelta(days=1)


def download_bhav(start: dt.date, end: dt.date, root=None, workers=MAX_WORKERS):
    """Try every calendar day (special sessions fall on weekends and holidays)."""
    missing = MissingSet(raw_dir(root) / "bhav" / "missing.txt")
    todo = [d for d in daterange(start, end) if not bhav_path(d, root).exists() and d not in missing]

    def one(d):
        data = http_get(bhav_url_path(d))
        if data is None:
            missing.add(d)
        elif data[:2] != b"PK":
            raise FetchError(f"{d}: not a zip")
        else:
            _atomic_write(bhav_path(d, root), data)

    errs = _run_pool(one, todo, "bhavcopy", workers)
    if errs:
        raise FetchError(f"{len(errs)} bhavcopy downloads failed, first: {errs[0]}")


def trading_days(start: dt.date, end: dt.date, root=None) -> list[dt.date]:
    return [d for d in daterange(start, end) if bhav_path(d, root).exists()]


def download_mto(days, root=None, workers=MAX_WORKERS):
    missing = MissingSet(raw_dir(root) / "mto" / "missing.txt")
    todo = [d for d in days if not mto_path(d, root).exists() and d not in missing]

    def one(d):
        data = http_get(mto_url_path(d))
        if data is None:
            missing.add(d)
        else:
            _atomic_write(mto_path(d, root), data)

    errs = _run_pool(one, todo, "delivery", workers)
    if errs:
        log.warning("%d delivery downloads failed (optional data), first: %s", len(errs), errs[0])


def download_pr(days, root=None, workers=MAX_WORKERS):
    """Daily press bundle. Only the corporate-action (Bc*) and ETF (etf*)
    members are kept; the bundle itself (0.3-0.5 MB a day) is not stored."""
    missing = MissingSet(raw_dir(root) / "pr" / "missing.txt")

    def marker(d):
        return pr_dir(d, root) / f"bc{d:%d%m%y}.csv"

    todo = [d for d in days if d >= PR_FIRST_DATE and not marker(d).exists() and d not in missing]

    def one(d):
        data = http_get(pr_url_path(d), timeout=120)
        if data is None:
            missing.add(d)
            return
        z = zipfile.ZipFile(io.BytesIO(data))
        bc = etf = None
        for n in z.namelist():
            low = n.lower().rsplit("/", 1)[-1]
            if low.startswith("bc") and low.endswith(".csv"):
                bc = z.read(n)
            elif low.startswith("etf") and low.endswith(".csv"):
                etf = z.read(n)
        if etf is not None:
            _atomic_write(pr_dir(d, root) / f"etf{d:%d%m%y}.csv", etf)
        # written last: its presence marks the day as done (empty if the bundle had none)
        _atomic_write(marker(d), bc if bc is not None else b"")

    errs = _run_pool(one, todo, "press bundle", workers)
    if errs:
        log.warning("%d press-bundle downloads failed, first: %s", len(errs), errs[0])
    return errs


def download_reference(end: dt.date, root=None, refresh=False):
    ref = raw_dir(root) / "ref"
    for name in ("symbolchange.csv",):
        p = ref / name
        if p.exists() and not refresh:
            continue
        data = http_get(f"/content/equities/{name}")
        if data is None:
            raise FetchError(f"{name} not found")
        _atomic_write(p, data)


def ca_api_path(y: int, half: int, root=None) -> Path:
    return raw_dir(root) / "ca" / f"nse_ca_{y}_H{half}.json"


def download_ca_api(start: dt.date, end: dt.date, root=None):
    """NSE corporate-action feed, by ex-date range (half-years, never past `end`).

    This host sits behind a stricter gateway than the archive hosts and may
    refuse automated clients; a refusal is reported and the build continues
    with whatever is already cached (the press-bundle Bc files cover 2010+).
    """
    out = []
    for y in range(max(start.year, CA_API_FIRST_DATE.year), end.year + 1):
        for half, (a, b) in enumerate(((dt.date(y, 1, 1), dt.date(y, 6, 30)),
                                       (dt.date(y, 7, 1), dt.date(y, 12, 31))), 1):
            a, b = max(a, start), min(b, end)
            if a > b:
                continue
            p = ca_api_path(y, half, root)
            meta = p.with_suffix(".range")
            want = f"{a.isoformat()} {b.isoformat()}"
            if p.exists() and meta.exists() and meta.read_text().strip() == want:
                continue
            url = ("https://www.nseindia.com/api/corporates-corporateActions?index=equities"
                   f"&from_date={a:%d-%m-%Y}&to_date={b:%d-%m-%Y}")
            ok = False
            for i in range(4):
                try:
                    r = _session().get(url, timeout=90, headers={"Accept": "application/json"})
                    if r.status_code == 200:
                        rows = r.json()
                        if isinstance(rows, list):
                            _atomic_write(p, json.dumps(rows).encode())
                            _atomic_write(meta, want.encode())
                            ok = True
                            break
                except Exception as e:
                    log.debug("ca api %s: %s", url, e)
                time.sleep(2.0 * (i + 1))
            if not ok:
                out.append(want)
            time.sleep(0.7)
    if out:
        log.warning("corporate-action feed unavailable for %d ranges (first %s)", len(out), out[0])
    return out


def cmd_download(start, end, root=None, workers=MAX_WORKERS, deliv=True, pr=True, ca=True):
    download_reference(end, root)
    download_bhav(start, end, root, workers)
    days = trading_days(start, end, root)
    log.info("%d trading days with a bhavcopy between %s and %s", len(days), start, end)
    if ca:
        download_ca_api(start, end, root)
    if pr:
        download_pr(days, root, workers)
    if deliv:
        download_mto(days, root, workers)


# --------------------------------------------------------------------------
# parsing raw files
# --------------------------------------------------------------------------

def _unzip_single(data: bytes) -> bytes:
    if data[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(data))
        names = [n for n in z.namelist() if n.lower().endswith(".csv")] or z.namelist()
        return z.read(names[0])
    return data


def parse_bhav(data: bytes, date=None) -> pd.DataFrame:
    """One old-format bhavcopy (csv bytes, or the zip holding it) -> tidy rows.

    Keeps series EQ/BE/BZ only; if a symbol is present in more than one kept
    series the EQ row wins (then BE, then BZ). `isin` is None before the
    exchange added that column (2011).
    """
    raw = pd.read_csv(io.BytesIO(_unzip_single(data)), index_col=False, dtype=str,
                      encoding="latin-1", skipinitialspace=True)
    raw.columns = [c.strip().upper() for c in raw.columns]
    need = ["SYMBOL", "SERIES", "OPEN", "HIGH", "LOW", "CLOSE", "PREVCLOSE", "TOTTRDQTY", "TOTTRDVAL"]
    miss = [c for c in need if c not in raw.columns]
    if miss:
        raise ValueError(f"bhavcopy is missing columns {miss}")
    raw["SYMBOL"] = raw["SYMBOL"].str.strip()
    raw["SERIES"] = raw["SERIES"].str.strip()
    raw = raw[raw["SERIES"].isin(KEEP_SERIES) & raw["SYMBOL"].notna() & (raw["SYMBOL"] != "")]
    out = pd.DataFrame({
        "symbol": raw["SYMBOL"].to_numpy(),
        "series": raw["SERIES"].to_numpy(),
    })
    for dst, src in (("open", "OPEN"), ("high", "HIGH"), ("low", "LOW"), ("close", "CLOSE"),
                     ("prevclose", "PREVCLOSE"), ("volume", "TOTTRDQTY"), ("turnover", "TOTTRDVAL")):
        out[dst] = pd.to_numeric(raw[src], errors="coerce").to_numpy(dtype="float64")
    # 2003 trade-for-trade rows carry 0 for open/high/low: that is "not given", not a price
    for c in ("open", "high", "low", "close", "prevclose"):
        out.loc[~(out[c] > 0), c] = np.nan
    if "ISIN" in raw.columns:
        isin = raw["ISIN"].str.strip()
        out["isin"] = isin.where(isin.str.len() == 12).to_numpy(dtype=object)
    else:
        out["isin"] = None
    if date is None:
        if "TIMESTAMP" not in raw.columns or raw.empty:
            raise ValueError("no date given and no TIMESTAMP column")
        date = pd.to_datetime(raw["TIMESTAMP"].iloc[0].strip(), format="%d-%b-%Y")
    out.insert(0, "date", pd.Timestamp(date))
    out["_r"] = out["series"].map(SERIES_RANK)
    out = (out.sort_values(["symbol", "_r"], kind="stable")
              .drop_duplicates("symbol", keep="first")
              .drop(columns="_r")
              .reset_index(drop=True))
    # a row with no usable close is not a trade record
    return out[out["close"] > 0].reset_index(drop=True)


def parse_mto(data: bytes) -> pd.DataFrame:
    """Security-wise delivery position file -> symbol, series, traded, deliverable, pct."""
    rows = []
    for line in data.decode("latin-1").splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) >= 7 and p[0] == "20":
            try:
                rows.append((p[2], p[3], float(p[4]), float(p[5]), float(p[6])))
            except ValueError:
                continue
    return pd.DataFrame(rows, columns=["symbol", "series", "traded", "deliverable", "pct"])


def parse_bc(data: bytes) -> pd.DataFrame:
    """Corporate-action member (Bc*.csv) of the press bundle."""
    cols = ["series", "symbol", "ex_date", "purpose"]
    if not data.strip():
        return pd.DataFrame(columns=cols)
    raw = pd.read_csv(io.BytesIO(data), dtype=str, encoding="latin-1", index_col=False,
                      on_bad_lines="skip")
    raw.columns = [c.strip().upper() for c in raw.columns]
    if not {"SYMBOL", "EX_DT", "PURPOSE"} <= set(raw.columns):
        return pd.DataFrame(columns=cols)
    out = pd.DataFrame({
        "series": raw.get("SERIES", pd.Series("", index=raw.index)).fillna("").str.strip(),
        "symbol": raw["SYMBOL"].fillna("").str.strip(),
        "ex_date": pd.to_datetime(raw["EX_DT"].str.strip(), format="%d/%m/%Y", errors="coerce"),
        "purpose": raw["PURPOSE"].fillna("").str.strip(),
    })
    return out[(out["symbol"] != "") & out["ex_date"].notna()].reset_index(drop=True)


# --------------------------------------------------------------------------
# corporate-action purpose text
# --------------------------------------------------------------------------

_KEY_RE = re.compile(
    r"DIVIDEND|DIVIDENT|DIVD|DIV|DVD|INTERIM|FINAL|FIN|SPECIAL|SPL(?!I?T)|"          # dividend family
    r"PREMIUM|PREM|SPLIT|SPLT|SUB-?\s?DIVISION|FACE\s?VALUE|FV|RIGHTS?|RGHTS|BUY\s?-?BACK|"
    r"CONSOLIDATION|CONSOL|BONUS|REDEMPTION|REDUCTION|INTEREST|DISTRIBUTION|RETURN OF CAPITAL|"
    r"CAPITAL|WARRANT|CONVERSION|DEBENTURE|NCD|PAR\b")
_DIV_KEYS = ("DIVIDEND", "DIVIDENT", "DIVD", "DIV", "DVD", "INTERIM", "FINAL", "FIN", "SPECIAL", "SPL")
_NUM = r"(\d+(?:\.\d+)?)"
_RATIO = r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)"
_BONUS_RE = re.compile(r"BONUS(?P<mid>[^0-9]{0,24})" + _RATIO + r"(?P<tail>[^/]{0,24})")
_SPLIT_RE = re.compile(
    r"(?:SPLIT|SPLT|SUB-?\s?DIVISION|SUBDIVISION)[^0-9]{0,32}" + _NUM + r"[^0-9]{1,24}?TO[^0-9]{0,12}" + _NUM)
_CONSOL_RE = re.compile(r"CONSOL[A-Z]*[^0-9]{0,32}" + _NUM + r"[^0-9]{1,24}?TO[^0-9]{0,12}" + _NUM)
_RIGHTS_RE = re.compile(r"(?:RIGHTS?|RGHTS)(?P<mid>[^0-9]{0,24})" + _RATIO)
_PREM_RE = re.compile(r"PREM(?:IUM)?[^0-9]{0,12}" + _NUM)
_PAR_RE = re.compile(r"(?:@|AT)\s*PAR\b")
_AMT_RE = re.compile(r"(?P<rs>(?:RS|INR)\s*)?(?P<n>\d+(?:\.\d+)?)(?P<tail>\s*(?:%|PER\s*CENT|"
                     r"(?:PER|PR|P|/)\s*\.?\s*(?:EQ(?:UITY)?\s*)?(?:SHARE|SHR|SH|UNIT)))?")
_NOT_EQUITY = ("DEB", "PREF", "NCD", "NCRPS", "CCPS", "RPS", "WARRANT", "BOND")
_SCHEME_WORDS = ("SCHEME OF ARR", "ARRANGEMENT", "DEMERGER", "DE-MERGER", "SPIN OFF", "SPIN-OFF",
                 "REDUCTION OF CAPITAL", "CAPITAL REDUCTION", "REDUCTION IN CAPITAL", "RESTRUCTUR")


def _norm_purpose(text: str) -> str:
    t = (text or "").upper().replace("/-", " ")
    t = re.sub(r"\bR[SE]\b\.?", "RS ", t)          # RS. / RE. / RS / RE  -> RS
    t = re.sub(r"\bR[SE]\.?(?=\d)", "RS ", t)      # RS10 / RE1          -> RS 10
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def parse_purpose(text: str) -> dict:
    """Read an exchange corporate-action purpose line.

    Returns a dict with any of:
      bonus   (a, b)        a new shares for every b held
      split   (old, new)    face value before and after (sub-division)
      consol  (old, new)    face value before and after (consolidation)
      rights  (a, b, premium or None, at_par)   a new for b held
      div_rs  float         cash dividend, rupees per share (all parts summed)
      div_pct float         cash dividend quoted as a percentage of face value
      scheme  True          scheme of arrangement / demerger / capital reduction
    Purposes are often cut at 25 characters by the exchange; whatever cannot
    be read with certainty is simply left out.
    """
    t = _norm_purpose(text)
    out: dict = {}
    if not t:
        return out

    m = _BONUS_RE.search(t)
    if m and not any(w in m.group("mid") + m.group("tail") for w in _NOT_EQUITY):
        a, b = float(m.group(2)), float(m.group(3))
        if a > 0 and b > 0:
            out["bonus"] = (a, b)

    m = _CONSOL_RE.search(t)
    if m:
        old, new = float(m.group(1)), float(m.group(2))
        if 0 < old < new:
            out["consol"] = (old, new)
    else:
        m = _SPLIT_RE.search(t)
        if m:
            old, new = float(m.group(1)), float(m.group(2))
            if old > new > 0:
                out["split"] = (old, new)
            elif 0 < old < new and "SPLIT" not in t:
                out["consol"] = (old, new)

    m = _RIGHTS_RE.search(t)
    if m and not any(w in m.group("mid") for w in _NOT_EQUITY):
        a, b = float(m.group(2)), float(m.group(3))
        rest = t[m.end():]
        if a > 0 and b > 0 and not any(w in rest[:30] for w in ("DEB", "PREF", "NCD", "WARRANT", "BOND")):
            pm = _PREM_RE.search(rest)
            out["rights"] = (a, b, float(pm.group(1)) if pm else None, bool(_PAR_RE.search(rest)) and not pm)

    if any(w in t for w in _SCHEME_WORDS):
        out["scheme"] = True

    # cash amounts: every number that is marked as rupees / per share / percent,
    # counted as dividend only if the nearest keyword before it is a dividend word
    keys = [(k.start(), k.group(0)) for k in _KEY_RE.finditer(t)]
    rs = pct = 0.0
    got_rs = got_pct = False
    for a in _AMT_RE.finditer(t):
        tail = (a.group("tail") or "").strip()
        is_pct = tail.startswith("%") or tail.startswith("PER C")
        is_rs = bool(a.group("rs")) or (tail != "" and not is_pct)
        if not (is_pct or is_rs):
            continue
        prev = [k for p, k in keys if p < a.start()]
        if not prev or prev[-1] not in _DIV_KEYS:
            continue
        val = float(a.group("n"))
        if is_pct:
            pct += val
            got_pct = True
        else:
            rs += val
            got_rs = True
    if got_rs:
        out["div_rs"] = round(rs, 6)
    if got_pct:
        out["div_pct"] = round(pct, 6)
    return out


def bonus_factor(a: float, b: float) -> float:
    """a new shares for every b held -> price multiplier for earlier dates."""
    return b / (a + b)


def split_factor(old_fv: float, new_fv: float) -> float:
    return new_fv / old_fv


def rights_factor(a: float, b: float, issue_price: float, cum_price: float) -> float | None:
    """Theoretical ex-rights price over the cum-rights close.

    a new shares for every b held at `issue_price`. Returns None when the
    rights are not in the money (no value passes to the holder, so nothing
    to adjust) or the inputs are unusable.
    """
    if not (a > 0 and b > 0 and issue_price > 0 and cum_price > 0) or issue_price >= cum_price:
        return None
    return (b * cum_price + a * issue_price) / ((a + b) * cum_price)


def _year_cache(kind: str, year: int, root=None) -> tuple[Path, Path]:
    d = raw_dir(root) / "parsed"
    return d / f"{kind}_{year}.parquet", d / f"{kind}_{year}.json"


def _cache_fresh(sig_path: Path, pq_path: Path, sig: dict) -> bool:
    if not (sig_path.exists() and pq_path.exists()):
        return False
    try:
        return json.loads(sig_path.read_text()) == sig
    except Exception:
        return False


def parse_bhav_year(year: int, days: list[dt.date], root=None) -> pd.DataFrame:
    """All bhavcopies of one year as a long frame, cached under raw/cm/parsed."""
    pq, sigp = _year_cache("bhav", year, root)
    sig = {"v": 3, "days": [d.isoformat() for d in days]}
    if _cache_fresh(sigp, pq, sig):
        return pd.read_parquet(pq)
    parts = []
    for d in days:
        try:
            parts.append(parse_bhav(bhav_path(d, root).read_bytes(), d))
        except Exception as e:
            raise RuntimeError(f"cannot parse bhavcopy for {d}: {e}") from e
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(
        columns=["date", "symbol", "series", "open", "high", "low", "close", "prevclose",
                 "volume", "turnover", "isin"])
    df["isin"] = df["isin"].astype("string")
    pq.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(pq.with_suffix(".tmp"), index=False)
    os.replace(pq.with_suffix(".tmp"), pq)
    sigp.write_text(json.dumps(sig))
    return df


def parse_mto_year(year: int, days: list[dt.date], root=None) -> pd.DataFrame:
    pq, sigp = _year_cache("mto", year, root)
    have = [d for d in days if mto_path(d, root).exists()]
    sig = {"v": 1, "days": [d.isoformat() for d in have]}
    if _cache_fresh(sigp, pq, sig):
        return pd.read_parquet(pq)
    parts = []
    for d in have:
        m = parse_mto(mto_path(d, root).read_bytes())
        if len(m):
            m.insert(0, "date", pd.Timestamp(d))
            parts.append(m)
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(
        columns=["date", "symbol", "series", "traded", "deliverable", "pct"])
    pq.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(pq.with_suffix(".tmp"), index=False)
    os.replace(pq.with_suffix(".tmp"), pq)
    sigp.write_text(json.dumps(sig))
    return df


def load_long(start: dt.date, end: dt.date, root=None) -> pd.DataFrame:
    """Every kept bhavcopy row between start and end (raw symbols, raw prices)."""
    days = trading_days(start, end, root)
    by_year: dict[int, list[dt.date]] = {}
    for d in days:
        by_year.setdefault(d.year, []).append(d)
    parts = []
    for y in sorted(by_year):
        # the cache always holds every available day of the year; clip afterwards
        all_days = trading_days(dt.date(y, 1, 1), min(dt.date(y, 12, 31), clip_end(dt.date(y, 12, 31), root)), root)
        df = parse_bhav_year(y, all_days, root)
        df = df[(df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))]
        parts.append(df)
        log.info("parsed %d: %d days, %d rows", y, len(by_year[y]), len(df))
    out = pd.concat(parts, ignore_index=True)
    out["symbol"] = out["symbol"].astype(str)
    return out


# --------------------------------------------------------------------------
# corporate-action records (two exchange sources)
# --------------------------------------------------------------------------

CA_COLS = ["symbol", "series", "ex_date", "purpose", "isin", "face_value", "source", "seen_last"]


def parse_ca_api(rows: list) -> pd.DataFrame:
    """Rows of the NSE corporate-action feed -> tidy frame (symbol is the
    company's *present* symbol, not the one it traded under on the ex-date)."""
    out = []
    for x in rows or []:
        try:
            ex = dt.datetime.strptime((x.get("exDate") or "").strip(), "%d-%b-%Y")
        except ValueError:
            continue
        try:
            fv = float(x.get("faceVal"))
        except (TypeError, ValueError):
            fv = np.nan
        isin = (x.get("isin") or "").strip()
        out.append(((x.get("symbol") or "").strip(), (x.get("series") or "").strip(), pd.Timestamp(ex),
                    (x.get("subject") or "").strip(), isin if len(isin) == 12 else None, fv, "api", pd.NaT))
    return pd.DataFrame(out, columns=CA_COLS)


def load_ca_api(start: dt.date, end: dt.date, root=None) -> pd.DataFrame:
    parts = []
    for p in sorted((raw_dir(root) / "ca").glob("nse_ca_*.json")):
        parts.append(parse_ca_api(json.loads(p.read_text())))
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=CA_COLS)
    df = df[(df["ex_date"] >= pd.Timestamp(start)) & (df["ex_date"] <= pd.Timestamp(end))]
    return df[df["series"].isin(KEEP_SERIES)].drop_duplicates(
        ["symbol", "ex_date", "purpose"]).reset_index(drop=True)


def load_bc(start: dt.date, end: dt.date, root=None) -> pd.DataFrame:
    """Every corporate action announced in the daily press bundles.

    A bundle lists actions from about a week back to a few weeks ahead, so an
    action shows up in many bundles; `seen_last` is the last bundle date that
    still carried it (a postponed or cancelled action drops out early).
    """
    days = [d for d in trading_days(max(start, PR_FIRST_DATE), end, root)]
    by_year: dict[int, list[dt.date]] = {}
    for d in days:
        if (pr_dir(d, root) / f"bc{d:%d%m%y}.csv").exists():
            by_year.setdefault(d.year, []).append(d)
    parts = []
    for y, ds in sorted(by_year.items()):
        pq, sigp = _year_cache("bc", y, root)
        sig = {"v": 1, "days": [d.isoformat() for d in ds]}
        if _cache_fresh(sigp, pq, sig):
            parts.append(pd.read_parquet(pq))
            continue
        rows = []
        for d in ds:
            b = parse_bc((pr_dir(d, root) / f"bc{d:%d%m%y}.csv").read_bytes())
            if len(b):
                b["seen"] = pd.Timestamp(d)
                rows.append(b)
        if rows:
            allr = pd.concat(rows, ignore_index=True)
            g = (allr.groupby(["symbol", "series", "ex_date", "purpose"], as_index=False)
                     .agg(seen_last=("seen", "max")))
        else:
            g = pd.DataFrame(columns=["symbol", "series", "ex_date", "purpose", "seen_last"])
        pq.parent.mkdir(parents=True, exist_ok=True)
        g.to_parquet(pq.with_suffix(".tmp"), index=False)
        os.replace(pq.with_suffix(".tmp"), pq)
        sigp.write_text(json.dumps(sig))
        parts.append(g)
    if not parts:
        return pd.DataFrame(columns=CA_COLS)
    df = pd.concat(parts, ignore_index=True)
    df = (df.groupby(["symbol", "series", "ex_date", "purpose"], as_index=False)
            .agg(seen_last=("seen_last", "max")))
    df["isin"] = None
    df["face_value"] = np.nan
    df["source"] = "bc"
    df = df[(df["ex_date"] >= pd.Timestamp(start)) & (df["ex_date"] <= pd.Timestamp(end))]
    return df[df["series"].isin(KEEP_SERIES)][CA_COLS].reset_index(drop=True)


# --------------------------------------------------------------------------
# symbol continuity
# --------------------------------------------------------------------------

def load_symbol_changes(end: dt.date, root=None, path: Path | None = None) -> pd.DataFrame:
    """Exchange symbol-change list, restricted to changes effective on or before `end`."""
    p = path or (raw_dir(root) / "ref" / "symbolchange.csv")
    raw = pd.read_csv(p, encoding="latin-1", dtype=str, header=0, index_col=False)
    raw = raw.iloc[:, :4]
    raw.columns = ["name", "old", "new", "date"]
    for c in raw.columns:
        raw[c] = raw[c].fillna("").str.strip()
    raw["date"] = pd.to_datetime(raw["date"], format="%d-%b-%Y", errors="coerce")
    raw = raw[raw["date"].notna() & (raw["old"] != "") & (raw["new"] != "") & (raw["old"] != raw["new"])]
    raw = raw[raw["date"] <= pd.Timestamp(end)]
    return raw.drop_duplicates(["old", "new", "date"]).sort_values("date").reset_index(drop=True)


def isin_issuer(isin) -> str | None:
    """Issuer part of an Indian ISIN (INE002A01018 -> INE002A). The serial
    that follows changes on a split or consolidation, the issuer part does not."""
    if isinstance(isin, str) and len(isin) == 12:
        return isin[:7]
    return None


class _DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def build_segments(sym_dates: dict, changes: pd.DataFrame, extra_cuts: dict | None = None,
                   max_link_lag_days: int = 730) -> pd.DataFrame:
    """Split every raw symbol's history into segments and join the segments
    that belong to one company.

    sym_dates   raw symbol -> sorted array of trade dates (datetime64)
    changes     exchange symbol changes (old, new, date), already clipped
    extra_cuts  raw symbol -> dates at which a *different* company starts
                using the symbol (evidence from ISIN issuer codes)

    A symbol is cut at the date it was renamed away (rows on or after that
    date are someone else re-using the name) and at the date it was renamed
    to (rows before that date belonged to a previous user of the name).
    A change old->new joins the last segment of `old` before the date with
    the first segment of `new` on or after it.

    Returns one row per segment: symbol, start, end, entity, name. `name` is
    the last symbol the company traded under; when two companies end up with
    the same name the one that traded last keeps it and the earlier one is
    renamed NAME~YYYY (YYYY = its last trading year).
    """
    extra_cuts = extra_cuts or {}
    cuts: dict[str, set] = {}
    for r in changes.itertuples(index=False):
        d = np.datetime64(r.date, "D")
        for s in (r.old, r.new):
            dates = sym_dates.get(s)
            if dates is not None and len(dates) and dates[0] < d <= dates[-1]:
                cuts.setdefault(s, set()).add(d)
    for s, ds in extra_cuts.items():
        dates = sym_dates.get(s)
        if dates is None:
            continue
        for d in ds:
            d = np.datetime64(d, "D")
            if dates[0] < d <= dates[-1]:
                cuts.setdefault(s, set()).add(d)

    seg_sym, seg_start, seg_end = [], [], []
    seg_index: dict[str, list[int]] = {}
    for s, dates in sym_dates.items():
        dates = np.asarray(dates, dtype="datetime64[D]")
        if not len(dates):
            continue
        bounds = [0]
        for c in sorted(cuts.get(s, ())):
            i = int(np.searchsorted(dates, c, side="left"))
            if 0 < i < len(dates) and i != bounds[-1]:
                bounds.append(i)
        bounds.append(len(dates))
        for a, b in zip(bounds[:-1], bounds[1:]):
            seg_index.setdefault(s, []).append(len(seg_sym))
            seg_sym.append(s)
            seg_start.append(dates[a])
            seg_end.append(dates[b - 1])

    dsu = _DSU(len(seg_sym))
    unlinked = []
    for r in changes.itertuples(index=False):
        d = np.datetime64(r.date, "D")
        olds = [i for i in seg_index.get(r.old, ()) if seg_end[i] < d]
        news = [i for i in seg_index.get(r.new, ()) if seg_start[i] >= d]
        if not olds or not news:
            continue                      # the old or the new symbol never traded in the kept series
        o, n = olds[-1], news[0]
        if (seg_start[n] - d).astype(int) > max_link_lag_days:
            unlinked.append((r.old, r.new, str(d)))
            continue
        dsu.union(o, n)

    seg = pd.DataFrame({"symbol": seg_sym,
                        "start": np.array(seg_start, dtype="datetime64[D]"),
                        "end": np.array(seg_end, dtype="datetime64[D]")})
    seg["entity"] = [dsu.find(i) for i in range(len(seg))]
    last = seg.sort_values("end").groupby("entity").tail(1).set_index("entity")
    ent = pd.DataFrame({"name": last["symbol"], "last": last["end"]})
    ent = ent.sort_values(["name", "last"])
    # the company that traded last keeps the plain name
    is_last = ~ent.duplicated("name", keep="last")
    names = ent["name"].where(is_last, ent["name"] + "~" + ent["last"].dt.year.astype(str))
    used, final = set(names[is_last]), {}
    for e, nm in names.items():
        if is_last[e]:
            final[e] = nm
            continue
        k, base = 0, nm
        while nm in used:
            k += 1
            nm = f"{base}{chr(ord('a') + k)}"
        used.add(nm)
        final[e] = nm
    seg["name"] = seg["entity"].map(final)
    seg.attrs["unlinked"] = unlinked
    return seg.sort_values(["symbol", "start"]).reset_index(drop=True)


def assign_names(long: pd.DataFrame, seg: pd.DataFrame) -> pd.Series:
    """Canonical column name for every (raw symbol, date) row of `long`."""
    single = seg.groupby("symbol")["name"].transform("size") == 1
    simple = dict(zip(seg.loc[single, "symbol"], seg.loc[single, "name"]))
    out = long["symbol"].map(simple)
    multi = seg.loc[~single]
    if len(multi):
        todo = out.isna().to_numpy()
        sub = long.loc[todo, ["symbol", "date"]].copy()
        sub["_i"] = np.flatnonzero(todo)
        sub["date"] = sub["date"].astype("datetime64[ns]")
        m = multi[["symbol", "start", "name"]].copy()
        m["start"] = m["start"].astype("datetime64[ns]")
        merged = pd.merge_asof(sub.sort_values("date"), m.sort_values("start"),
                               left_on="date", right_on="start", by="symbol", direction="backward")
        vals = out.to_numpy(dtype=object)
        vals[merged["_i"].to_numpy()] = merged["name"].to_numpy(dtype=object)
        out = pd.Series(vals, index=long.index)
    if out.isna().any():
        raise RuntimeError("rows left without an entity name")
    return out.astype(str)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m quant.data.nse_cm", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "download"):
        p = sub.add_parser(name)
        p.add_argument("--start", default="2003-01-01")
        p.add_argument("--end", default="2021-12-31")
        p.add_argument("--root", default=None, help="data root (default <repo>/data or $QUANT_DATA)")
        p.add_argument("--workers", type=int, default=MAX_WORKERS)
        p.add_argument("--no-deliv", action="store_true", help="skip the delivery files")
        p.add_argument("--no-pr", action="store_true", help="skip the press bundles")
        p.add_argument("--no-ca-api", action="store_true", help="skip the corporate-action feed")
        p.add_argument("--offline", action="store_true", help="build from the raw cache only")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)
    start = pd.Timestamp(a.start).date()
    end = clip_end(a.end, a.root)
    workers = max(1, min(a.workers, MAX_WORKERS))
    if a.cmd == "download":
        cmd_download(start, end, a.root, workers, not a.no_deliv, not a.no_pr, not a.no_ca_api)
        return 0
    raise SystemExit("build stage not implemented yet")


if __name__ == "__main__":
    sys.exit(main())
