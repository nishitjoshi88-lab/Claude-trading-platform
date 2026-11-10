"""Strategy registry, look-ahead check and the evaluation protocol.

A strategy is a function `fn(ctx, **params) -> Plan`, registered with an id,
a family and a parameter grid. It reads data only through `ctx`, which is
what lets the harness prove it does not look ahead: the harness re-runs the
strategy on data cut off at a date and requires the same decision for that
date.

Protocol: parameters are chosen on the train window only; the validation
window is used to rank strategies against each other; the holdout period is
not on disk until strategy code is frozen.
"""
from __future__ import annotations

import importlib
import itertools
import json
import pkgutil
import time
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from ..data import store
from ..data.store import Market
from .metrics import stats
from .sim import Plan, SimConfig, simulate

# Three kinds of strategy, each with its own data and its own protected period:
#   daily     NSE cash market, daily bars     holdout 2022 onward
#   options   index options, daily bars       holdout 2022 onward
#   intraday  one-minute bars (from 2022)     holdout 2025 onward
WINDOWS = {
    "daily": {"train": ("2005-01-01", "2014-12-31"), "valid": ("2015-01-01", "2021-12-31")},
    "options": {"train": ("2008-01-01", "2014-12-31"), "valid": ("2015-01-01", "2021-12-31")},
    "intraday": {"train": ("2022-01-01", "2023-12-31"), "valid": ("2024-01-01", "2024-12-31")},
}
INTRADAY_MAX_RANK = 120          # intraday strategies are evaluated on the 120 most liquid stocks (end-2021 ranking)
RESULTS = Path(__file__).resolve().parents[2] / "results" / "research"


@lru_cache(maxsize=None)
def _parquet(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)


class Ctx:
    """Everything a strategy may look at, cut off at the market's last date."""

    def __init__(self, market: Market, root=None, open_only: bool = False):
        self.market = market
        self.root = store.data_root(root)
        self.end = market.dates[-1]
        self.open_only = open_only          # last day: only the opening price is known
        self._rank = None

    # --- cash market -----------------------------------------------------
    def liquidity_rank(self) -> pd.DataFrame:
        if self._rank is None:
            self._rank = self.market.liquidity_rank()
        return self._rank

    def universe(self, top: int = 200) -> pd.DataFrame:
        """True where a symbol is among the `top` most traded (point in time)."""
        return self.liquidity_rank() <= top

    # --- other data, clipped to what was known ----------------------------
    def _clip(self, df: pd.DataFrame, col: str | None = None) -> pd.DataFrame:
        key = df.index if col is None else df[col]
        key = pd.DatetimeIndex(key).normalize()
        mask = key < self.end if self.open_only else key <= self.end
        return df[np.asarray(mask)]

    def index(self, field: str = "close") -> pd.DataFrame:
        df = _parquet(str(self.root / "index" / f"{field}.parquet"))
        if self.open_only and field == "open":
            return df[np.asarray(pd.DatetimeIndex(df.index) <= self.end)]
        return self._clip(df)

    def fo(self, symbol: str) -> pd.DataFrame:
        return self._clip(_parquet(str(self.root / "fo" / f"{symbol}.parquet")), "date")

    def table(self, relpath: str, date_col: str | None = "date") -> pd.DataFrame:
        """Any parquet file under the data root, e.g. 'flows/participant_oi.parquet'.
        Pass date_col=None when the dates are the index."""
        return self._clip(_parquet(str(self.root / relpath)), date_col)

    def truncate(self, date, open_only: bool = False) -> "Ctx":
        m = self.market.upto(date)
        if open_only:
            blank = {}
            for f in ("high", "low", "close", "volume", "turnover"):
                df = getattr(m, f).copy()
                df.iloc[-1] = np.nan
                blank[f] = df
            m = replace(m, **blank)
        return Ctx(m, self.root, open_only)


@dataclass
class Spec:
    id: str
    family: str
    fn: Callable[..., Plan]
    grid: dict[str, list] = field(default_factory=dict)
    subset: str = "cm_liquid"
    cards: tuple[str, ...] = ()
    doc: str = ""
    kind: str = "daily"                 # "daily", "options" or "intraday"

    def trials(self, max_trials: int = 60) -> list[dict]:
        keys = list(self.grid)
        combos = [dict(zip(keys, v)) for v in itertools.product(*(self.grid[k] for k in keys))] or [{}]
        if len(combos) > max_trials:
            step = len(combos) / max_trials
            combos = [combos[int(k * step)] for k in range(max_trials)]
        return combos


REGISTRY: dict[str, Spec] = {}


def register(id: str, family: str, grid: dict[str, list] | None = None,
             subset: str = "cm_liquid", cards: tuple[str, ...] = (), kind: str = "daily"):
    """Decorator. `grid` lists the values to try for each parameter; the first
    value of each is the default. `cards` are research card ids this implements.
    `kind` says what the function returns: "daily" a Plan, "options" an
    OptionPlan, "intraday" an IntradayPlan (and it receives an ICtx)."""
    assert kind in WINDOWS, kind
    def deco(fn):
        if id in REGISTRY and REGISTRY[id].fn.__module__ != fn.__module__:
            raise ValueError(f"duplicate strategy id {id}")
        REGISTRY[id] = Spec(id, family, fn, grid or {}, subset, tuple(cards), (fn.__doc__ or "").strip(), kind)
        return fn
    return deco


def discover() -> dict[str, Spec]:
    """Import every module under quant.strategies so that they register."""
    import quant.strategies as pkg
    for m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        importlib.import_module(m.name)
    return REGISTRY


@lru_cache(maxsize=4)
def load_ctx(subset: str = "cm_liquid", root: str | None = None) -> Ctx:
    return Ctx(store.load_market(root=root, subset=subset), root)


def _same(a: pd.Series | None, b: pd.Series | None) -> tuple[bool, float]:
    if a is None and b is None:
        return True, 0.0
    a = pd.Series(dtype=float) if a is None else a
    b = pd.Series(dtype=float) if b is None else b
    cols = a.index.union(b.index)
    x = a.reindex(cols).to_numpy(dtype=float)
    y = b.reindex(cols).to_numpy(dtype=float)
    x, y = np.nan_to_num(x), np.nan_to_num(y)
    diff = float(np.abs(x - y).max()) if len(cols) else 0.0
    return diff < 1e-6, diff


def check_lookahead(spec: Spec, ctx: Ctx, params: dict | None = None, n_dates: int = 4,
                    seed: int = 0) -> list[str]:
    """Re-run the strategy on data cut off at several dates; the decision for
    each cut-off date must match the one made with the full history.
    Returns a list of problems (empty means it passed)."""
    params = params or spec.trials(1)[0]
    full = spec.fn(ctx, **params)
    active = full.weights.dropna(how="all").index
    active = active[active.isin(ctx.market.dates)]
    half = ctx.market.dates[len(ctx.market.dates) // 3]
    pool = active[(active > half) & (active < ctx.market.dates[-2])]
    if len(pool) == 0:
        return ["no decisions in the last two thirds of the sample"]
    rng = np.random.default_rng(seed)
    picks = sorted(rng.choice(len(pool), size=min(n_dates, len(pool)), replace=False))
    problems = []
    for d in pool[picks]:
        part = spec.fn(ctx.truncate(d, open_only=(full.decide_at == "open")), **params)
        if (part.mode, part.decide_at, part.fill) != (full.mode, full.decide_at, full.fill):
            problems.append(f"{d.date()}: plan settings change with the data")
        rows = active[active <= d][-3:]
        for r in rows:
            a = full.weights.loc[r] if r in full.weights.index else None
            b = part.weights.loc[r] if r in part.weights.index else None
            ok, diff = _same(a, b)
            if not ok:
                problems.append(f"decision for {r.date()} changes when data after {d.date()} is hidden "
                                f"(largest weight difference {diff:.4f})")
                break
    return problems


def check_lookahead_options(spec: Spec, ctx: Ctx, params: dict | None = None, n_dates: int = 4,
                            seed: int = 0) -> list[str]:
    """Option plans can only cheat through their entry signal: re-compute it
    on data cut off at several dates and compare."""
    params = params or spec.trials(1)[0]
    full = spec.fn(ctx, **params)
    if full.entry_signal is None:
        return []
    sig = full.entry_signal.dropna()
    half = ctx.market.dates[len(ctx.market.dates) // 3]
    pool = sig.index[(sig.index > half) & (sig.index < ctx.market.dates[-2])]
    if len(pool) == 0:
        return ["entry signal is empty in the last two thirds of the sample"]
    rng = np.random.default_rng(seed)
    problems = []
    for d in pool[sorted(rng.choice(len(pool), size=min(n_dates, len(pool)), replace=False))]:
        part = spec.fn(ctx.truncate(d), **params).entry_signal
        a = sig.loc[:d].iloc[-3:]
        b = part.reindex(a.index) if part is not None else None
        if b is None or not np.allclose(a.to_numpy(dtype=float), b.to_numpy(dtype=float), equal_nan=True):
            problems.append(f"entry signal up to {d.date()} changes when later data is hidden")
    return problems


def _sim_all(spec: Spec, plan, ctx, cfg) -> dict:
    """Simulate one plan on every window of its kind. Returns {window: (result, stats)}."""
    out = {}
    for name, (a, b) in WINDOWS[spec.kind].items():
        if spec.kind == "daily":
            res = simulate(plan, ctx.market, cfg, start=a, end=b, liq_rank=ctx.liquidity_rank())
        elif spec.kind == "options":
            from ..options import simulate_options
            try:
                vix = ctx.index("close")["INDIA VIX"]
            except (KeyError, FileNotFoundError):
                vix = None
            res = simulate_options(plan, ctx.fo(plan.symbol), cfg, start=a, end=b, vix=vix)
        else:
            from ..intraday import simulate_intraday
            res = simulate_intraday(plan, ctx, cfg, start=a, end=b)
        out[name] = (res, stats(res, cfg.capital))
    return out


def default_ctx(spec: Spec):
    if spec.kind == "intraday":
        from ..intraday import load_ictx
        return load_ictx(max_rank=INTRADAY_MAX_RANK)
    return load_ctx(spec.subset)


def default_cfg(spec: Spec):
    if spec.kind == "options":
        from ..options import OptionSimConfig
        return OptionSimConfig()
    if spec.kind == "intraday":
        from ..intraday import IntradaySimConfig
        return IntradaySimConfig()
    return SimConfig()


def run_lookahead(spec: Spec, ctx) -> list[str]:
    if spec.kind == "intraday":
        from ..intraday import check_lookahead_intraday
        return check_lookahead_intraday(spec.fn, ctx, spec.trials(1)[0])
    if spec.kind == "options":
        return check_lookahead_options(spec, ctx)
    return check_lookahead(spec, ctx)


def evaluate(spec: Spec, ctx=None, cfg=None, max_trials: int = 60, save: bool = True,
             check: bool = True) -> dict:
    """Run every parameter set on train and validation; choose on train."""
    ctx = ctx if ctx is not None else default_ctx(spec)
    cfg = cfg or default_cfg(spec)
    t0 = time.time()
    trials, curves = [], {}
    for params in spec.trials(max_trials):
        try:
            plan = spec.fn(ctx, **params)
            w = _sim_all(spec, plan, ctx, cfg)
        except Exception as e:                      # one bad parameter set must not hide the rest
            trials.append({"params": params, "error": f"{type(e).__name__}: {e}"})
            continue
        trials.append({"params": params, "mode": getattr(plan, "mode", spec.kind),
                       "train": w["train"][1], "valid": w["valid"][1]})
        curves[len(trials) - 1] = {k: v[0].equity for k, v in w.items()}
    good = [(k, t) for k, t in enumerate(trials) if "error" not in t and t["train"].get("orders", 0) >= 10]
    out = {"id": spec.id, "family": spec.family, "kind": spec.kind, "cards": list(spec.cards), "doc": spec.doc,
           "n_trials": len(trials), "trials": trials, "seconds": None}
    if good:
        k, best = max(good, key=lambda kt: kt[1]["train"].get("sharpe", -9))
        out["chosen"] = best
        vs = [t["valid"].get("sharpe", np.nan) for _, t in good]
        out["valid_sharpe_median"] = float(np.nanmedian(vs))
        out["valid_sharpe_min"] = float(np.nanmin(vs))
        out["valid_sharpe_max"] = float(np.nanmax(vs))
        if save:
            RESULTS.mkdir(parents=True, exist_ok=True)
            (RESULTS / "curves").mkdir(exist_ok=True)
            pd.concat(curves[k], names=["window", "date"]).to_frame("equity").to_parquet(
                RESULTS / "curves" / f"{spec.id}.parquet")
    else:
        out["chosen"] = None
    out["lookahead_problems"] = run_lookahead(spec, ctx) if check else None
    out["seconds"] = round(time.time() - t0, 1)
    if save:
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / f"{spec.id}.json").write_text(json.dumps(out, indent=1, default=str))
    return out
