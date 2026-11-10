"""Automated runner: fetch data, decide, trade (paper), save state, repeat.

State is written after every cycle, so the process can be stopped and
restarted at any time without losing positions or risk limits.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import pandas as pd

from .config import Config
from .core import Trader
from .market import Panel, load_frames, save_frames

log = logging.getLogger("trader")
HISTORY_BARS = 24 * 45          # enough for the longest strategy lookback


class Runner:
    def __init__(self, cfg: Config, feed):
        self.cfg, self.feed = cfg, feed
        self.state_dir = Path(cfg.state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "state.json"
        self.journal = self.state_dir / "journal.jsonl"
        self.kill_file = self.state_dir / "KILL"
        self.trader = Trader(cfg, len(cfg.symbols), kill_file=self.kill_file)
        self.last_ts: pd.Timestamp | None = None
        if self.state_file.exists():
            d = json.loads(self.state_file.read_text())
            if d["symbols"] != cfg.symbols:
                raise RuntimeError("symbol list changed; close positions and clear state first")
            self.trader.load_dict(d)
            self.last_ts = pd.Timestamp(d["last_ts"]) if d["last_ts"] else None

    def refresh_data(self) -> Panel:
        frames = load_frames(self.cfg.data_dir, self.cfg.symbols)
        now = pd.Timestamp.now("UTC").tz_localize(None)
        for s in self.cfg.symbols:
            old = frames.get(s)
            since = old.index[-1] - pd.Timedelta(hours=2) if old is not None and len(old) \
                else now - pd.Timedelta(hours=HISTORY_BARS)
            new = self.feed.fetch(s, since)
            both = new if old is None else pd.concat([old, new])
            frames[s] = both[~both.index.duplicated(keep="last")].sort_index().iloc[-HISTORY_BARS * 2:]
        save_frames(frames, self.cfg.data_dir)
        return Panel.from_frames({s: frames[s] for s in self.cfg.symbols})

    def cycle(self) -> dict | None:
        """One decision. Returns a journal record, or None if no new bar."""
        panel = self.refresh_data()
        i = len(panel) - 1
        ts = panel.index[i]
        if self.last_ts is not None and ts <= self.last_ts:
            return None
        # funding settled since the last processed bar (covers downtime)
        if self.last_ts is None:
            funding = panel.funding[i] * 0
        else:
            funding = panel.funding[panel.index > self.last_ts].sum(axis=0)
        n_events = len(self.trader.risk.events)
        orders = self.trader.step(panel.view(i), funding=funding, fill_now=True)
        self.last_ts = ts
        pf = self.trader.portfolio
        record = {
            "ts": ts.isoformat(), "equity": round(pf.equity, 2),
            "pnl": {k: round(v, 2) for k, v in pf.pnl.items()},
            "gross": round(pf.gross(), 2),
            "orders": {name: {panel.symbols[j]: [round(float(d[0, j]), 8), round(float(d[1, j]), 8)]
                              for j in range(len(panel.symbols)) if d[:, j].any()}
                       for name, d in orders.items()},
            "risk": self.trader.risk.events[n_events:],
            "killed": self.trader.risk.killed,
        }
        self.save()
        with self.journal.open("a") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def save(self) -> None:
        d = self.trader.to_dict()
        d["symbols"] = self.cfg.symbols
        d["last_ts"] = self.last_ts.isoformat() if self.last_ts is not None else None
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(d))
        tmp.replace(self.state_file)

    def run_forever(self) -> None:
        while True:
            try:
                rec = self.cycle()
                if rec:
                    log.info("%s equity=%.2f orders=%d %s", rec["ts"], rec["equity"],
                             sum(len(o) for o in rec["orders"].values()), " ".join(rec["risk"]))
            except Exception:                       # keep running through outages
                log.exception("cycle failed; retrying next bar")
            now = time.time()
            time.sleep(3600 - now % 3600 + 20)      # just after the next hourly close
