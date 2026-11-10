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
_RE_SYMBOL = r"-RE\d?$"
SERIES_RANK = {"EQ": 0, "BE": 1, "BZ": 2}
MAX_WORKERS = 6
PR_FIRST_DATE = dt.date(2010, 1, 1)      # the PR press bundle does not exist before 2010
CA_API_FIRST_DATE = dt.date(2003, 1, 1)  # the corporate-action feed is almost empty before mid-2005


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
    # rights entitlements trade for a fortnight in the BE series (SYMBOL-RE, ISIN type 20): not shares
    is_re = raw["SYMBOL"].str.contains(_RE_SYMBOL, regex=True)
    if "ISIN" in raw.columns:
        is_re |= raw["ISIN"].fillna("").str.strip().str[7:9].eq("20")
    raw = raw[~is_re]
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
    r"PREMIUM|PREM|PRM|SPLIT|SPLT|SUB-?\s?DIVISION|FACE\s?VALUE|FV|RIGHTS?|RIGTHS|RIGTS|RGTS|RHTS?|"
    r"BUY\s?-?BACK|CONSOLIDATION|CONSOL|BONUS|BON\b|REDEMPTION|REDUCTION|INTEREST|DISTRIBUTION|DIST|"
    r"RETURN OF CAPITAL|CAPITAL|WARRANT|CONVERSION|DEBENTURE|NCD|PAR\b")
_DIV_KEYS = ("DIVIDEND", "DIVIDENT", "DIVD", "DIV", "DVD", "INTERIM", "FINAL", "FIN", "SPECIAL", "SPL")
_NUM = r"(\d+(?:\.\d+)?)"
_RATIO = r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)"
_BONUS_RE = re.compile(r"\bBON(?:US)?(?P<mid>[^0-9]{0,24})" + _RATIO + r"(?P<tail>[^/]{0,24})")
_SPLIT_RE = re.compile(
    r"(?:SPLIT|SPLT|SPTL|SUB-?\s?DIV(?:ISION)?|SUBDIVISION|\bSPL|\bFVS\b)[^0-9%]{0,32}" + _NUM
    + r"[^0-9%]{0,24}?TO[^0-9%]{0,12}" + _NUM)
_SPLIT_DASH_RE = re.compile(r"\bSPL(?:IT)?[^0-9%]{0,6}RS " + _NUM + r"\s*-\s*RS " + _NUM)   # SPL RS10-RS2
_CONSOL_RE = re.compile(r"CONSOL[A-Z]*[^0-9%]{0,32}" + _NUM + r"[^0-9%]{0,24}?TO[^0-9%]{0,12}" + _NUM)
_RIGHTS_RE = re.compile(r"\bR(?:IGHTS?|IGTHS|IGTS|GTS|HTS?)(?P<mid>[^0-9]{0,24})" + _RATIO)
_PREM_RE = re.compile(r"PRE?M(?:IUM)?[^0-9]{0,12}" + _NUM)
_PAR_RE = re.compile(r"(?:@|AT)\s*PAR\b")
_AMT_RE = re.compile(r"(?P<rs>(?:RS|INR)\s*)?(?P<n>\d+(?:\.\d+)?)(?P<tail>\s*(?:%|PER\s*CENT|"
                     r"(?:PER|PR|P|/)\s*\.?\s*(?:EQ(?:UITY)?\s*)?(?:SHARE|SHR|SH|S\b|UNIT)))?")
_NOT_EQUITY = ("DEB", "PREF", "NCD", "NCRPS", "CCPS", "PCCPS", "RPS", "WARRANT", "WRNT", "WAR ", "BOND",
               "DVR", "PCD", "FCD", "CCD", "ZCCB")
_SCHEME_WORDS = ("SCHEME", "SCHM", "SCH OF", "SCH-", "SCH AG", "ARRANGEMENT", "ARANGEMENT", "ARGMT",
                 "ARRNGMT", "DEMERG", "DE-MERGER", "MERGER", "AMALGAMATION", "SPIN OFF", "SPIN-OFF",
                 "REDUCTION", "CAP RED", "RESTRUCTUR")


def _norm_purpose(text: str) -> str:
    t = (text or "").upper().replace("/-", " ")
    t = re.sub(r"\bR[SE]\b\.?", "RS ", t)                 # RS. / RE. / RS / RE  -> RS
    t = re.sub(r"(?<![A-Z])R[SE]\.?(?=\d)", "RS ", t)     # RS10 / RE1          -> RS 10
    t = re.sub(r"(?<=\d)TOR[SE]\.?\s*(?=\d)", " TO RS ", t)   # RS10TORE1 -> RS 10 TO RS 1
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _blank(t: str, m) -> str:
    return t[:m.start()] + " " * (m.end() - m.start()) + t[m.end():]


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
    rest_text = t          # what is left for the cash-amount scan

    m = _BONUS_RE.search(t)
    if m:
        if not any(w in m.group("mid") + m.group("tail") for w in _NOT_EQUITY):
            a, b = float(m.group(2)), float(m.group(3))
            if a > 0 and b > 0:
                out["bonus"] = (a, b)
        rest_text = _blank(rest_text, m)

    m = _CONSOL_RE.search(t)
    if m:
        old, new = float(m.group(1)), float(m.group(2))
        if 0 < old < new:
            out["consol"] = (old, new)
        rest_text = _blank(rest_text, m)
    else:
        m = _SPLIT_RE.search(t) or _SPLIT_DASH_RE.search(t)
        if m:
            old, new = float(m.group(1)), float(m.group(2))
            if old > new > 0:
                out["split"] = (old, new)
            rest_text = _blank(rest_text, m)

    m = _RIGHTS_RE.search(t)
    if m:
        tail = t[m.end():]
        if not any(w in m.group("mid") + tail[:30] for w in _NOT_EQUITY):
            a, b = float(m.group(2)), float(m.group(3))
            if a > 0 and b > 0:
                pm = _PREM_RE.search(tail)
                out["rights"] = (a, b, float(pm.group(1)) if pm else None,
                                 bool(_PAR_RE.search(tail)) and not pm)
        stop = t.find("/", m.end())                 # the rights clause runs to the next "/"
        stop = len(t) if stop < 0 else stop
        rest_text = rest_text[:m.start()] + " " * (stop - m.start()) + rest_text[stop:]

    if any(w in t for w in _SCHEME_WORDS):
        out["scheme"] = True

    # cash amounts: every number that is marked as rupees / per share / percent,
    # counted as dividend only if the nearest keyword before it is a dividend word
    t2 = rest_text
    keys = [(k.start(), k.group(0)) for k in _KEY_RE.finditer(t2)]
    rs = pct = 0.0
    got_rs = got_pct = False
    for a in _AMT_RE.finditer(t2):
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
    sig = {"v": 4, "days": [d.isoformat() for d in days]}
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


def isin_links(long: pd.DataFrame) -> list[tuple]:
    """Pairs (symbol A, A's last date, symbol B, B's first date) where one
    ISIN stopped trading as A and later traded as B: the same security under
    a new symbol. Catches renames that the exchange list misses or misdates."""
    d = long[long["isin"].notna()]
    if d.empty:
        return []
    u = (d.groupby(["isin", "symbol"], observed=True)["date"].agg(["min", "max"]).reset_index()
           .sort_values(["isin", "min"]))
    out = []
    for _, g in u[u.groupby("isin")["symbol"].transform("size") > 1].groupby("isin"):
        rows = list(g.itertuples(index=False))
        for x, y in zip(rows[:-1], rows[1:]):
            if x.max < y.min and x.symbol != y.symbol:
                out.append((x.symbol, np.datetime64(x.max, "D"), y.symbol, np.datetime64(y.min, "D")))
    return out


def build_segments(sym_dates: dict, changes: pd.DataFrame, links: list | None = None,
                   max_link_lag_days: int = 730) -> pd.DataFrame:
    """Split every raw symbol's history into segments and join the segments
    that belong to one company.

    sym_dates   raw symbol -> sorted array of trade dates (datetime64)
    changes     exchange symbol changes (old, new, date), already clipped
    links       extra joins from `isin_links`

    A symbol is cut at the date it was renamed away (rows on or after that
    date are someone else re-using the name) and at the date it was renamed
    to (rows before that date belonged to a previous user of the name).
    A change old->new joins the last segment of `old` before the date with
    the first segment of `new` on or after it.

    Returns one row per segment: symbol, start, end, entity, name. `name` is
    the last symbol of the company (a rename that took effect after its last
    trade is still applied); when two companies end up with the same name
    the one that traded last keeps it and the earlier one becomes NAME~YYYY
    (YYYY = its last trading year).
    """
    sym_dates = {s: np.asarray(d, dtype="datetime64[D]") for s, d in sym_dates.items() if len(d)}
    cuts: dict[str, set] = {}
    for r in changes.itertuples(index=False):
        d = np.datetime64(r.date, "D")
        for s in (r.old, r.new):
            dates = sym_dates.get(s)
            if dates is not None and dates[0] < d <= dates[-1]:
                cuts.setdefault(s, set()).add(d)

    seg_sym, seg_start, seg_end = [], [], []
    seg_index: dict[str, list[int]] = {}
    for s, dates in sym_dates.items():
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

    def seg_at(sym, d):
        for i in seg_index.get(sym, ()):
            if seg_start[i] <= d <= seg_end[i]:
                return i
        return None

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
    n_isin = 0
    for a_sym, a_last, b_sym, b_first in links or ():
        o, n = seg_at(a_sym, a_last), seg_at(b_sym, b_first)
        if o is not None and n is not None and dsu.find(o) != dsu.find(n):
            dsu.union(o, n)
            n_isin += 1

    seg = pd.DataFrame({"symbol": seg_sym,
                        "start": np.array(seg_start, dtype="datetime64[D]"),
                        "end": np.array(seg_end, dtype="datetime64[D]")})
    seg["entity"] = [dsu.find(i) for i in range(len(seg))]
    last = seg.sort_values("end").groupby("entity").tail(1).set_index("entity")
    ent = pd.DataFrame({"name": last["symbol"].astype(object), "last": last["end"]})

    # renames effective after the company's last trade (new symbol never traded yet)
    pending = {}
    for r in changes.itertuples(index=False):
        pending.setdefault(r.old, []).append((np.datetime64(r.date, "D"), r.new))
    for e in ent.index:
        nm, lastd = ent.at[e, "name"], np.datetime64(ent.at[e, "last"], "D")
        for _ in range(8):
            nxt = [(d, n) for d, n in pending.get(nm, ()) if d > lastd]
            if not nxt:
                break
            d, n = min(nxt)
            dates = sym_dates.get(n)
            if dates is not None and (dates >= d).any():
                break                      # that symbol trades as somebody else
            nm, lastd = n, d
        ent.at[e, "name"] = nm

    ent = ent.sort_values(["name", "last"])
    is_last = ~ent.duplicated("name", keep="last")      # the company that traded last keeps the name
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
    seg.attrs["isin_links_used"] = n_isin
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


# --------------------------------------------------------------------------
# adjustment events
# --------------------------------------------------------------------------

# Businesses that carried on under a new symbol without an exchange symbol
# change (the exchange treated the successor as a new listing). old raw
# symbol -> new raw symbol. The join is adjusted like a scheme of arrangement
# (see `resolve_events`).
MANUAL_LINKS = (
    # Larsen & Toubro, 2004: the cement business stayed in the old company
    # (now UltraTech Cement); engineering moved to a new company that took
    # the L&T name and listed as LT on 2004-06-23. Holders of the old share
    # received new LT shares plus UltraTech shares.
    ("L&T", "LT"),
)

# Ratios a plain bonus or face-value split produces most often; an
# undeclared overnight gap is snapped to one of these only when it is within
# SNAP_TOL of it, otherwise the gap itself is used.
COMMON_RATIOS = (1 / 2, 1 / 3, 2 / 3, 1 / 4, 3 / 4, 1 / 5, 2 / 5, 3 / 5, 1 / 10)
SNAP_TOL = 0.03
INFER_DOWN = 0.79          # an undeclared overnight ratio at or below this is a capital change
INFER_UP = 1.27            # ... or at or above this (consolidation, capital reduction)
INFER_MAX_GAP_DAYS = 10    # only inferred when the stock traded within this many days before
SCHEME_DOWN, SCHEME_UP = 0.90, 1.25
REVIEW_MOVE = 0.35         # adjusted overnight moves beyond this are listed for review

# Hand-checked overrides, keyed by (panel name, first trade date on or after the ex-date).
#   MANUAL_EVENTS: factor to apply (replaces whatever the feeds or the gap scan say)
#   MANUAL_REAL:   the move is a real price move (or a data quirk left as is): no adjustment
# Every entry carries the reason it is there.
MANUAL_EVENTS: dict[tuple[str, str], tuple[float, str]] = {}
MANUAL_REAL: dict[tuple[str, str], str] = {}


def _kind_factor(kind: str, a: float, b: float) -> float:
    if kind == "bonus":
        return bonus_factor(a, b)
    return split_factor(a, b)          # split and consol: new face value / old face value


def declared_events(ca: pd.DataFrame) -> pd.DataFrame:
    """Exchange records -> one row per (name, ex_date, kind) candidate.

    `ca` must carry a `name` column (panel name of the company). Kinds:
    bonus, split, consol (with a, b), rights (a, b, premium, at_par), scheme.
    Dividend amounts are returned on the same rows (div_rs, div_pct).
    """
    rows = []
    for r in ca.itertuples(index=False):
        d = parse_purpose(r.purpose)
        base = dict(name=r.name, ex_date=r.ex_date, source=r.source, purpose=r.purpose,
                    face_value=r.face_value, isin=r.isin)
        for kind in ("bonus", "split", "consol"):
            if kind in d:
                rows.append(dict(base, kind=kind, a=d[kind][0], b=d[kind][1]))
        if "rights" in d:
            a, b, prem, par = d["rights"]
            rows.append(dict(base, kind="rights", a=a, b=b, premium=prem, at_par=par))
        if d.get("scheme"):
            rows.append(dict(base, kind="scheme"))
        if "div_rs" in d or "div_pct" in d:
            rows.append(dict(base, kind="div", div_rs=d.get("div_rs", np.nan), div_pct=d.get("div_pct", np.nan)))
    cols = ["name", "ex_date", "kind", "a", "b", "premium", "at_par", "div_rs", "div_pct",
            "face_value", "isin", "source", "purpose"]
    out = pd.DataFrame(rows, columns=cols)
    return out


def map_ca_names(ca: pd.DataFrame, seg: pd.DataFrame, long: pd.DataFrame,
                 max_days: int = 400) -> pd.Series:
    """Panel name of the company each corporate-action record refers to.

    Press-bundle records carry the symbol in use when the bundle was
    published, so the raw-symbol segment nearest to the ex-date decides.
    Feed records carry the company's present symbol: the panel name is tried
    first (and rejected when the record's ISIN issuer contradicts the
    company's), then the raw symbol, then the ISIN issuer on its own.
    Records that cannot be placed get NaN.
    """
    by_sym: dict[str, list] = {}
    for r in seg.itertuples(index=False):
        by_sym.setdefault(r.symbol, []).append((np.datetime64(r.start, "D"), np.datetime64(r.end, "D"), r.name))
    span = seg.groupby("name").agg(first=("start", "min"), last=("end", "max"))
    first = {n: np.datetime64(v, "D") for n, v in span["first"].items()}
    last = {n: np.datetime64(v, "D") for n, v in span["last"].items()}
    iss = long.loc[long["isin"].notna(), ["name", "isin"]].drop_duplicates()
    iss = iss.assign(issuer=iss["isin"].str[:7])
    issuers_of = iss.groupby("name")["issuer"].agg(set).to_dict()
    names_of: dict[str, set] = {}
    for n, ss in issuers_of.items():
        for x in ss:
            names_of.setdefault(x, set()).add(n)
    tol = np.timedelta64(max_days, "D")

    def by_raw(sym, d):
        best, bd = None, None
        for st, en, nm in by_sym.get(sym, ()):
            dist = max(st - d, d - en, np.timedelta64(0, "D"))
            if bd is None or dist < bd:
                best, bd = nm, dist
        return best if bd is not None and bd <= tol else None

    out = []
    for r in ca.itertuples(index=False):
        d = np.datetime64(r.ex_date, "D")
        if r.source != "api":
            out.append(by_raw(r.symbol, d))
            continue
        issuer = isin_issuer(r.isin)
        nm = None
        if r.symbol in first and first[r.symbol] - tol <= d <= last[r.symbol] + tol:
            known = issuers_of.get(r.symbol)
            if not (issuer and known and issuer not in known):
                nm = r.symbol
        if nm is None:
            c = by_raw(r.symbol, d)
            if c is not None:
                known = issuers_of.get(c)
                if not (issuer and known and issuer not in known):
                    nm = c
        if nm is None and issuer:
            c = [n for n in names_of.get(issuer, ()) if first[n] - tol <= d <= last[n] + tol]
            if len(c) == 1:
                nm = c[0]
        out.append(nm)
    return pd.Series(out, index=ca.index, dtype=object)


class Prices:
    """Raw daily rows of every company, sorted by (name, date), with the
    overnight ratio (open over previous close; close over previous close
    where the open is not given)."""

    def __init__(self, long: pd.DataFrame):
        long = long.sort_values(["name", "date"], kind="stable").reset_index(drop=True)
        self.long = long
        self.name = long["name"].to_numpy(dtype=object)
        self.date = long["date"].to_numpy(dtype="datetime64[D]")
        self.open = long["open"].to_numpy(dtype="float64")
        self.close = long["close"].to_numpy(dtype="float64")
        uniq, first = np.unique(self.name, return_index=True)
        self.span = {n: (int(i), int(j)) for n, i, j in zip(uniq, first, np.r_[first[1:], len(self.name)])}
        n = len(long)
        is_first = np.ones(n, dtype=bool)
        is_first[1:] = self.name[1:] != self.name[:-1]
        prev_close = np.r_[np.nan, self.close[:-1]]
        prev_close[is_first] = np.nan
        prev_date = np.r_[self.date[:1], self.date[:-1]]
        self.prev_close = prev_close
        self.gap_days = (self.date - prev_date).astype("int64").astype("float64")
        self.gap_days[is_first] = np.nan
        ref = np.where(self.open > 0, self.open, self.close)
        self.ref = ref
        with np.errstate(divide="ignore", invalid="ignore"):
            self.g = ref / prev_close

    def locate(self, name: str, date) -> int | None:
        """Row index of the first trade on or after `date` that has a trade before it."""
        sp = self.span.get(name)
        if sp is None:
            return None
        a, b = sp
        i = a + int(np.searchsorted(self.date[a:b], np.datetime64(date, "D"), side="left"))
        if i <= a or i >= b:
            return None
        return i


def resolve_events(px: Prices, decl: pd.DataFrame, fv_of: dict | None = None,
                   manual_events: dict | None = None, manual_real: dict | None = None,
                   infer: bool = True):
    """Decide the adjustment factor events.

    Returns (events, notes). `events` has one row per (name, date): the first
    trade date on or after the ex-date, the factor that multiplies every
    earlier price, the method and the evidence. Methods:

      declared            split / bonus / consolidation published by the exchange
                          and matching the overnight price ratio
      declared_shifted    same, but the gap sits up to 5 sessions from the published date
      declared_unverified published, too small to check against prices (|factor-1| <= ~20%)
      rights              published rights issue; factor = theoretical ex-rights price
                          over the cum-rights close
      scheme_gap          published scheme of arrangement / demerger / capital reduction
                          with an overnight ratio <= 0.90 or >= 1.25; factor = that ratio
      price_snap          no usable record; overnight ratio within 3% of a common
                          split/bonus ratio; factor = that ratio
      price_gap           no usable record and no common ratio; factor = the overnight ratio
      link_gap            join of a manual symbol link; factor = the ratio across the join
      manual              hand-checked override

    `notes` lists published records that were not applied and why.
    """
    fv_of = fv_of or {}
    manual_events = MANUAL_EVENTS if manual_events is None else manual_events
    manual_real = MANUAL_REAL if manual_real is None else manual_real
    ev: dict[tuple[str, int], dict] = {}
    notes = []

    adj = decl[decl["kind"].isin(["bonus", "split", "consol", "rights", "scheme"])]
    for (name, ex_date), grp in adj.groupby(["name", "ex_date"], sort=False):
        i = px.locate(name, ex_date)
        if i is None:
            continue
        cum, g, gap = px.prev_close[i], px.g[i], px.gap_days[i]
        if not (cum > 0 and g > 0):
            continue
        sources = sorted(set(grp["source"]))
        purposes = " | ".join(sorted(set(grp["purpose"])))[:200]
        # --- split / bonus / consolidation: product over kinds, alternatives per kind
        alts = [1.0]
        kinds = []
        for kind in ("bonus", "split", "consol"):
            k = grp[grp["kind"] == kind]
            if k.empty:
                continue
            kinds.append(kind)
            vals = sorted({round(_kind_factor(kind, r.a, r.b), 9) for r in k.itertuples(index=False)})
            alts = [x * v for x in alts for v in vals]
        f_rights = 1.0
        rk = grp[grp["kind"] == "rights"]
        if not rk.empty:
            best = None
            for r in rk.itertuples(index=False):
                fv = r.face_value if r.face_value == r.face_value else fv_of.get(name, np.nan)
                if r.premium == r.premium and r.premium is not None:
                    issue = r.premium + (fv if fv == fv else 0.0)
                elif r.at_par and fv == fv:
                    issue = fv
                else:
                    continue
                # cum price on the basis the ratio refers to: undo a same-day split/bonus later
                f = rights_factor(r.a, r.b, issue, cum)
                if f is not None and (best is None or r.source == "api"):
                    best = f
            if best is not None and 0.3 <= best < 1.0:
                f_rights = best
                kinds.append("rights")
            else:
                notes.append(dict(name=name, ex_date=ex_date, why="rights not priced or not in the money",
                                  purpose=purposes, g=g))
        if kinds and kinds != ["rights"]:
            tol = 0.20 if gap <= 5 else 0.40
            f = min(alts, key=lambda x: abs(np.log(g / (x * f_rights)))) * f_rights
            err = abs(np.log(g / f))
            if err <= tol:
                ev[(name, i)] = dict(factor=f, method="declared", kinds="+".join(kinds), g=g,
                                     sources=",".join(sources), purpose=purposes)
                continue
            a, b = px.span[name]
            best_j, best_err = None, 0.12
            for j in range(max(a + 1, i - 5), min(b, i + 6)):
                if j == i or not (px.g[j] > 0):
                    continue
                for x in alts:
                    e = abs(np.log(px.g[j] / (x * f_rights)))
                    if e <= best_err:
                        best_j, best_err, f = j, e, x * f_rights
            if best_j is not None:
                ev[(name, best_j)] = dict(factor=f, method="declared_shifted", kinds="+".join(kinds),
                                          g=px.g[best_j], sources=",".join(sources), purpose=purposes)
                continue
            f = min(alts, key=lambda x: abs(np.log(g / (x * f_rights)))) * f_rights
            if abs(np.log(f)) < 0.224:
                ev[(name, i)] = dict(factor=f, method="declared_unverified", kinds="+".join(kinds), g=g,
                                     sources=",".join(sources), purpose=purposes)
            else:
                notes.append(dict(name=name, ex_date=ex_date, why="published factor %.4f not seen in prices" % f,
                                  purpose=purposes, g=g))
            continue
        if kinds == ["rights"]:
            ev[(name, i)] = dict(factor=f_rights, method="rights", kinds="rights", g=g,
                                 sources=",".join(sources), purpose=purposes)
            continue
        if (grp["kind"] == "scheme").any() and gap <= 200 and (g <= SCHEME_DOWN or g >= SCHEME_UP):
            ev[(name, i)] = dict(factor=g, method="scheme_gap", kinds="scheme", g=g,
                                 sources=",".join(sources), purpose=purposes)

    # --- manual symbol links: the join itself is the event
    for old, new in MANUAL_LINKS:
        pass   # handled by the caller through `link_rows`

    # --- gaps with no usable record
    if infer:
        cand = np.flatnonzero(((px.g <= INFER_DOWN) | (px.g >= INFER_UP)) & (px.gap_days <= INFER_MAX_GAP_DAYS)
                              & (px.prev_close >= 1.0))
        for i in cand:
            name = px.name[i]
            if (name, int(i)) in ev:
                continue
            a, b = px.span[name]
            # a published event within 5 sessions already explains a gap of this size?
            near = [ev[(name, j)] for j in range(max(a, i - 5), min(b, i + 6)) if (name, j) in ev]
            if any(abs(np.log(px.g[i] / e["factor"])) <= 0.25 and e["method"] != "declared_shifted" and False
                   for e in near):
                continue
            g = px.g[i]
            # the new level has to hold: same-day close and the next sessions
            c0 = px.close[i] / (g * px.prev_close[i])
            nxt = px.close[i + 1:min(b, i + 4)]
            lvl = np.median(nxt) / px.ref[i] if len(nxt) else 1.0
            if not (0.75 <= c0 <= 1.33 and 0.70 <= lvl <= 1.43):
                continue
            snap = [c for c in COMMON_RATIOS if abs(np.log(g / c)) <= SNAP_TOL]
            if g < 1 and snap:
                ev[(name, int(i))] = dict(factor=snap[0], method="price_snap", kinds="", g=g, sources="", purpose="")
            else:
                ev[(name, int(i))] = dict(factor=float(g), method="price_gap", kinds="", g=g, sources="", purpose="")

    # --- overrides
    for (name, d), why in manual_real.items():
        i = px.locate(name, d)
        if i is not None and px.date[i] == np.datetime64(d, "D"):
            ev.pop((name, i), None)
    for (name, d), (f, why) in manual_events.items():
        i = px.locate(name, d)
        if i is None or px.date[i] != np.datetime64(d, "D"):
            notes.append(dict(name=name, ex_date=pd.Timestamp(d), why="manual event has no trade on that date",
                              purpose=why, g=np.nan))
            continue
        ev[(name, i)] = dict(factor=float(f), method="manual", kinds="", g=px.g[i], sources="manual", purpose=why)

    rows = [dict(name=k[0], date=px.date[k[1]], row=k[1], **v) for k, v in ev.items()]
    events = pd.DataFrame(rows, columns=["name", "date", "row", "factor", "method", "kinds", "g", "sources", "purpose"])
    events = events.sort_values(["name", "date"]).reset_index(drop=True)
    return events, pd.DataFrame(notes, columns=["name", "ex_date", "why", "purpose", "g"])


def factor_column(px: Prices, events: pd.DataFrame) -> np.ndarray:
    """Per-row factor: product of the factors of all later events of the company."""
    f = np.ones(len(px.name), dtype="float64")
    if events.empty:
        return f
    for name, grp in events.groupby("name", sort=False):
        a, b = px.span[name]
        mult = np.ones(b - a, dtype="float64")
        for r in grp.itertuples(index=False):
            mult[r.row - a] *= r.factor          # applies to rows strictly before r.row
        # factor[t] = product of mult[k] for k > t
        rev = np.cumprod(mult[::-1])[::-1]
        f[a:b - 1] = rev[1:]
    return f


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
