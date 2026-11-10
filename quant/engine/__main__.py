"""Command line: python -m quant.engine <command>

  run <id> [<id> ...] | --family NAME | --all   evaluate strategies (train + validation)
  check <id>                                    look-ahead check only
  board [--family NAME] [--top N]               leaderboard from saved results
  list                                          registered strategies
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from . import harness


def _run_one(sid: str) -> dict:
    spec = harness.discover()[sid]
    out = harness.evaluate(spec)
    c = out.get("chosen") or {}
    return {"id": sid, "n_trials": out["n_trials"], "seconds": out["seconds"],
            "train_sharpe": (c.get("train") or {}).get("sharpe"),
            "valid_sharpe": (c.get("valid") or {}).get("sharpe"),
            "valid_cagr": (c.get("valid") or {}).get("cagr"),
            "valid_dd": (c.get("valid") or {}).get("max_drawdown"),
            "lookahead_problems": out["lookahead_problems"],
            "errors": [t["error"] for t in out["trials"] if "error" in t][:3]}


def board(family: str | None = None, top: int = 50) -> list[dict]:
    rows, all_valid = [], []
    for f in sorted(harness.RESULTS.glob("*.json")):
        r = json.loads(f.read_text())
        for t in r["trials"]:
            if "error" not in t and t["valid"].get("sharpe") is not None:
                all_valid.append(t["valid"]["sharpe"])
        c = r.get("chosen")
        if not c or (family and r["family"] != family):
            continue
        v, t = c["valid"], c["train"]
        rows.append({"id": r["id"], "family": r["family"], "mode": r.get("kind", c.get("mode")), "trials": r["n_trials"],
                     "train_sharpe": t.get("sharpe"), "valid_sharpe": v.get("sharpe"),
                     "valid_cagr": v.get("cagr"), "valid_dd": v.get("max_drawdown"),
                     "valid_cost": v.get("cost_per_year"), "valid_pos_months": v.get("positive_months"),
                     "median_valid_sharpe": r.get("valid_sharpe_median"),
                     "lookahead_ok": not r.get("lookahead_problems")})
    rows.sort(key=lambda x: -(x["valid_sharpe"] if x["valid_sharpe"] is not None else -9))
    print(f"{len(rows)} strategies, {len(all_valid)} parameter sets tried in total; "
          f"spread of validation Sharpe across all trials: {np.std(all_valid) if all_valid else 0:.2f}")
    hdr = f"{'id':<46}{'family':<18}{'mode':<9}{'n':>3} {'trainSR':>7} {'validSR':>7} {'medSR':>6} {'CAGR':>7} {'maxDD':>7} {'cost/y':>6} {'mon+':>5} ok"
    print(hdr)
    for x in rows[:top]:
        f = lambda v, p: "   n/a" if v is None else format(v, p)
        print(f"{x['id'][:45]:<46}{x['family'][:17]:<18}{str(x['mode']):<9}{x['trials']:>3} "
              f"{f(x['train_sharpe'], '7.2f')} {f(x['valid_sharpe'], '7.2f')} {f(x['median_valid_sharpe'], '6.2f')} "
              f"{f(x['valid_cagr'], '7.1%')} {f(x['valid_dd'], '7.1%')} {f(x['valid_cost'], '6.1%')} "
              f"{f(x['valid_pos_months'], '5.0%')} {'yes' if x['lookahead_ok'] else 'NO'}")
    return rows


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="quant.engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("ids", nargs="*")
    r.add_argument("--family")
    r.add_argument("--all", action="store_true")
    r.add_argument("--jobs", type=int, default=1)
    c = sub.add_parser("check")
    c.add_argument("id")
    b = sub.add_parser("board")
    b.add_argument("--family")
    b.add_argument("--top", type=int, default=50)
    sub.add_parser("list")
    a = ap.parse_args(argv)

    if a.cmd == "board":
        board(a.family, a.top)
        return
    reg = harness.discover()
    if a.cmd == "list":
        for s in sorted(reg.values(), key=lambda s: (s.family, s.id)):
            print(f"{s.family:<20}{s.id:<50}{len(s.trials()):>3} trials")
    elif a.cmd == "check":
        spec = reg[a.id]
        problems = harness.run_lookahead(spec, harness.default_ctx(spec))
        print("PASS" if not problems else "\n".join(problems))
    else:
        ids = a.ids or [s.id for s in reg.values() if a.all or s.family == a.family]
        if a.jobs > 1:
            with ProcessPoolExecutor(a.jobs) as ex:
                for out in ex.map(_run_one, ids):
                    print(json.dumps(out, default=str))
        else:
            for sid in ids:
                print(json.dumps(_run_one(sid), default=str))


if __name__ == "__main__":
    main()
