"""Command line: python -m trader <command>"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .config import Config
from .market import Panel, load_frames, save_frames, synthetic_frames


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="trader")
    ap.add_argument("--config", help="JSON config file")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download", help="download hourly history for backtests")
    d.add_argument("--start", default="2022-01")
    d.add_argument("--end", required=True)
    d.add_argument("--out", default="history")
    b = sub.add_parser("backtest", help="run a backtest")
    b.add_argument("--data", default="history", help="directory of CSVs, or 'synthetic'")
    b.add_argument("--from", dest="start", help="first date, e.g. 2024-01-01")
    b.add_argument("--to", dest="end")
    b.add_argument("--only", help="comma-separated strategy names")
    r = sub.add_parser("run", help="run the automated paper trader")
    r.add_argument("--once", action="store_true", help="one cycle, then exit")
    sub.add_parser("status", help="show current state")
    sub.add_parser("reset", help="clear a risk kill after human review")
    a = ap.parse_args(argv)
    cfg = Config.load(a.config)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    if a.cmd == "download":
        from .data import download_history
        for s in cfg.symbols:
            df = download_history(s, a.start, a.end, cfg.quote)
            if len(df):
                save_frames({s: df}, a.out)
            print(f"{s}: {len(df)} bars")

    elif a.cmd == "backtest":
        from .backtest import format_stats, run
        from .strategies import default_strategies
        frames = synthetic_frames(cfg.symbols) if a.data == "synthetic" \
            else load_frames(a.data, cfg.symbols)
        if not frames:
            raise SystemExit(f"no data in {a.data}; run `download` first")
        frames = {s: f.loc[a.start:a.end] for s, f in frames.items()}
        strategies = default_strategies()
        if a.only:
            strategies = [s for s in strategies if s.name in a.only.split(",")]
        res = run(cfg, Panel.from_frames(frames), strategies)
        print(format_stats(res.stats()))
        for e in res.events[:20]:
            print(" ", e)

    else:
        from .live import Runner
        if a.cmd == "run":
            from .data import ExchangeFeed
            runner = Runner(cfg, ExchangeFeed(cfg.exchange, cfg.quote))
            if a.once:
                print(json.dumps(runner.cycle(), indent=2))
            else:
                runner.run_forever()
        else:
            runner = Runner(cfg, feed=None)
            pf, risk = runner.trader.portfolio, runner.trader.risk
            if a.cmd == "reset":
                risk.reset(pf.equity)
                Path(runner.kill_file).unlink(missing_ok=True)
                runner.save()
                print("risk kill cleared")
            print(json.dumps({"last_bar": str(runner.last_ts), "equity": round(pf.equity, 2),
                              "pnl": pf.pnl, "gross_exposure": round(pf.gross(), 2),
                              "fees": round(pf.fees, 2), "killed": risk.killed,
                              "kill_reason": risk.kill_reason, "halted_today": risk.halted(),
                              "benched": risk.benched_until}, indent=2))


if __name__ == "__main__":
    main()
