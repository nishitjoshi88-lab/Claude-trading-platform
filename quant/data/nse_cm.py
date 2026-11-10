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
