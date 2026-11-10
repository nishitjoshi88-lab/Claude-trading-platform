"""Selection of finalists, the single run on the protected period, and the report.

The selection rule below is fixed before the protected period is opened.
A strategy is a finalist only if all of these hold for the parameter set
chosen on the train window:

  * it passed the automated look-ahead check and an independent code review;
  * train and validation Sharpe ratios clear the thresholds in RULE;
  * the median validation Sharpe across its whole parameter grid is positive
    (the result does not hinge on one lucky setting);
  * it traded often enough in validation for the numbers to mean something;
  * its validation drawdown is within the limit.

Up to three finalists whose daily returns are not highly correlated form the
portfolio, with capital split equally.

  python -m quant.engine.final finalists --kind intraday
  python -m quant.engine.final holdout --kind intraday      # run once, at the end
  python -m quant.engine.final report
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from . import harness
from .metrics import deflated_sharpe, stats
from .sim import SimResult

RULE = {
    "intraday": {"min_train_sharpe": 0.5, "min_valid_sharpe": 1.0, "min_valid_trades": 100,
                 "max_valid_drawdown": -0.25},
    "daily": {"min_train_sharpe": 0.3, "min_valid_sharpe": 0.4, "min_valid_trades": 20,
              "max_valid_drawdown": -0.35},
    "options": {"min_train_sharpe": 0.3, "min_valid_sharpe": 0.4, "min_valid_trades": 30,
                "max_valid_drawdown": -0.30},
}
HOLDOUT = {"intraday": ("2025-01-01", "2026-10-31"), "daily": ("2022-01-01", "2026-10-31"),
           "options": ("2022-01-01", "2026-10-31")}
MAX_PORTFOLIO, MAX_CORR = 3, 0.6
ROOT = Path(__file__).resolve().parents[2]
HOLD_DIR = ROOT / "results" / "holdout"
VERDICTS = ROOT / "results" / "verdicts.json"


def results(kind: str | None = None) -> list[dict]:
    out = []
    for f in sorted(harness.RESULTS.glob("*.json")):
        r = json.loads(f.read_text())
        r.setdefault("kind", "daily")
        if r["family"] != "reference" and (kind is None or r["kind"] == kind):
            out.append(r)
    return out


def verdicts() -> dict:
    return json.loads(VERDICTS.read_text()) if VERDICTS.exists() else {}


def trial_sharpes(kind: str) -> np.ndarray:
    """Validation Sharpe of every parameter set tried (annualised)."""
    return np.array([t["valid"]["sharpe"] for r in results(kind) for t in r["trials"]
                     if "error" not in t and t["valid"].get("sharpe") is not None])


def valid_returns(sid: str) -> pd.Series:
    eq = pd.read_parquet(harness.RESULTS / "curves" / f"{sid}.parquet")["equity"]
    return eq.loc["valid"].pct_change().dropna()


def finalists(kind: str, need_review: bool = True) -> list[dict]:
    rule, ver, out = RULE[kind], verdicts(), []
    for r in results(kind):
        c = r.get("chosen")
        if not c or r.get("lookahead_problems"):
            continue
        v, t = c["valid"], c["train"]
        review = ver.get(r["id"])
        if review == "invalid" or (need_review and review not in ("sound", "fixed_and_rerun")):
            continue
        if (t.get("sharpe", -9) >= rule["min_train_sharpe"] and v.get("sharpe", -9) >= rule["min_valid_sharpe"]
                and v.get("trades", 0) >= rule["min_valid_trades"] and r.get("valid_sharpe_median", -9) > 0
                and v.get("max_drawdown", -1) >= rule["max_valid_drawdown"]):
            out.append({"id": r["id"], "family": r["family"], "kind": kind, "params": c["params"],
                        "train": t, "valid": v, "n_trials": r["n_trials"], "review": review})
    out.sort(key=lambda x: -x["valid"]["sharpe"])
    sharpes = trial_sharpes(kind)
    sr_std = float(np.std(sharpes) / np.sqrt(252)) if len(sharpes) > 1 else 0.0
    for f in out:
        f["deflated_sharpe"] = deflated_sharpe(valid_returns(f["id"]), len(sharpes), sr_std)
    return out


def pick_portfolio(fin: list[dict]) -> list[dict]:
    chosen = []
    for f in fin:
        r = valid_returns(f["id"])
        if all(abs(r.corr(valid_returns(c["id"]))) < MAX_CORR for c in chosen):
            chosen.append(f)
        if len(chosen) == MAX_PORTFOLIO:
            break
    return chosen


def _ctx_cfg(kind: str, holdout: bool):
    spec0 = harness.Spec("x", "x", lambda: None, kind=kind)
    if kind == "intraday" and holdout:
        from ..intraday import load_ictx
        return load_ictx(max_rank=harness.INTRADAY_MAX_RANK, grid="grid_holdout"), harness.default_cfg(spec0)
    return harness.default_ctx(spec0), harness.default_cfg(spec0)


def _simulate(spec, params, ctx, cfg, start, end) -> SimResult:
    plan = spec.fn(ctx, **params)
    if spec.kind == "daily":
        from .sim import simulate
        return simulate(plan, ctx.market, cfg, start=start, end=end, liq_rank=ctx.liquidity_rank())
    if spec.kind == "options":
        from ..options import simulate_options
        try:
            vix = ctx.index("close")["INDIA VIX"]
        except (KeyError, FileNotFoundError):
            vix = None
        return simulate_options(plan, ctx.fo(plan.symbol), cfg, start=start, end=end, vix=vix)
    from ..intraday import simulate_intraday
    return simulate_intraday(plan, ctx, cfg, start=start, end=end)


def combine(parts: list[SimResult]) -> SimResult:
    """Sleeves run side by side, each on its own slice of the capital."""
    eq = sum(p.equity for p in parts)
    expo = sum(p.exposure * p.equity for p in parts) / eq
    skipped: dict[str, int] = {}
    for p in parts:
        for k, v in p.skipped.items():
            skipped[k] = skipped.get(k, 0) + v
    return SimResult(eq, pd.concat([p.trades for p in parts], ignore_index=True), sum(p.costs for p in parts),
                     sum(p.traded_value for p in parts), sum(p.orders for p in parts), expo, skipped)


def run_window(kind: str, window: tuple[str, str], label: str, holdout: bool = False,
               need_review: bool = True) -> dict:
    """Run every finalist and the portfolio on one window and save the outcome."""
    reg = harness.discover()
    fin = finalists(kind, need_review)
    port = pick_portfolio(fin)
    ctx, cfg = _ctx_cfg(kind, holdout)
    out = {"kind": kind, "window": window, "label": label, "rule": RULE[kind],
           "n_strategies": len(results(kind)), "n_trials": int(len(trial_sharpes(kind))), "finalists": []}
    for f in fin:
        res = _simulate(reg[f["id"]], f["params"], ctx, cfg, *window)
        out["finalists"].append({**{k: f[k] for k in ("id", "family", "params", "deflated_sharpe", "review")},
                                 "train_sharpe": f["train"]["sharpe"], "valid_sharpe": f["valid"]["sharpe"],
                                 label: stats(res, cfg.capital)})
    if port:
        sleeve = replace(cfg, capital=cfg.capital / len(port))
        parts = [_simulate(reg[f["id"]], f["params"], ctx, sleeve, *window) for f in port]
        both = combine(parts)
        out["portfolio"] = {"members": [f["id"] for f in port], label: stats(both, cfg.capital)}
        HOLD_DIR.mkdir(parents=True, exist_ok=True)
        both.equity.to_frame("equity").to_parquet(HOLD_DIR / f"{kind}_{label}_portfolio.parquet")
    HOLD_DIR.mkdir(parents=True, exist_ok=True)
    (HOLD_DIR / f"{kind}_{label}.json").write_text(json.dumps(out, indent=1, default=str))
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="quant.engine.final")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("finalists", "holdout", "dryrun"):
        p = sub.add_parser(name)
        p.add_argument("--kind", default="intraday")
        p.add_argument("--unreviewed", action="store_true", help="do not require an independent review verdict")
    a = ap.parse_args(argv)
    if a.cmd == "finalists":
        fin = finalists(a.kind, not a.unreviewed)
        print(f"{len(results(a.kind))} strategies, {len(trial_sharpes(a.kind))} parameter sets tried; "
              f"{len(fin)} finalists")
        for f in fin:
            print(f"  {f['id']:<52} train {f['train']['sharpe']:5.2f}  valid {f['valid']['sharpe']:5.2f}  "
                  f"trades {f['valid']['trades']:>5}  DSR {f['deflated_sharpe']:.2f}  {f['params']}")
        print("portfolio:", [f["id"] for f in pick_portfolio(fin)])
    elif a.cmd == "dryrun":                       # same code path as the final test, on the validation window
        out = run_window(a.kind, harness.WINDOWS[a.kind]["valid"], "dryrun", need_review=not a.unreviewed)
        print(json.dumps(out.get("portfolio", {}), indent=1, default=str)[:1500])
    else:
        if a.kind == "intraday":
            os.environ["QUANT_UNLOCK_INTRADAY"] = "1"
        else:
            os.environ["QUANT_UNLOCK_HOLDOUT"] = "1"
        out = run_window(a.kind, HOLDOUT[a.kind], "holdout", holdout=True, need_review=not a.unreviewed)
        print(json.dumps({"finalists": [(f["id"], round(f["holdout"].get("sharpe", 0), 2)) for f in out["finalists"]],
                          "portfolio": out.get("portfolio", {}).get("members")}, indent=1))


if __name__ == "__main__":
    main()
