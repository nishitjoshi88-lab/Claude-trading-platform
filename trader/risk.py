"""Risk governor. Its decisions override every strategy.

Three layers:
  * kill   - total drawdown limit or a KILL file: flatten everything and stay
             flat until a human runs `reset`.
  * halt   - daily loss limit: flatten directional books, freeze the rest
             until the next UTC day.
  * bench  - a strategy that loses too much of its own capital is flattened
             and benched for a cooldown period, then allowed back.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import RiskConfig


class RiskGovernor:
    def __init__(self, cfg: RiskConfig, strategies: list[str], kill_file: str | Path | None = None):
        self.cfg = cfg
        self.kill_file = Path(kill_file) if kill_file else None
        self.day: str | None = None
        self.day_start_equity = 0.0
        self.peak_equity = 0.0
        self.halted_day: str | None = None
        self.killed = False
        self.kill_reason = ""
        self.strat_peak = {s: 0.0 for s in strategies}
        self.benched_until: dict[str, str] = {}
        self.events: list[str] = []

    def update(self, ts: pd.Timestamp, equity: float, strat_pnl: dict[str, float],
               strat_capital: dict[str, float]) -> None:
        day = ts.strftime("%Y-%m-%d")
        if day != self.day:
            self.day, self.day_start_equity = day, equity
        self.peak_equity = max(self.peak_equity, equity)

        if not self.killed:
            if self.kill_file and self.kill_file.exists():
                self._kill(ts, "kill file present")
            elif equity < self.peak_equity * (1 - self.cfg.max_drawdown):
                self._kill(ts, f"drawdown limit {self.cfg.max_drawdown:.0%} hit")

        if self.halted_day != day and equity < self.day_start_equity * (1 - self.cfg.daily_loss_limit):
            self.halted_day = day
            self.events.append(f"{ts} HALT daily loss limit hit")

        for s, pnl in strat_pnl.items():
            until = self.benched_until.get(s)
            if until is not None:
                if ts >= pd.Timestamp(until):
                    del self.benched_until[s]
                    self.strat_peak[s] = pnl
                    self.events.append(f"{ts} RESUME {s}")
                continue
            self.strat_peak[s] = max(self.strat_peak[s], pnl)
            cap = strat_capital.get(s, 0.0)
            if cap > 0 and self.strat_peak[s] - pnl > self.cfg.strategy_drawdown * cap:
                until_ts = ts + pd.Timedelta(days=self.cfg.strategy_cooldown_days)
                self.benched_until[s] = until_ts.isoformat()
                self.events.append(f"{ts} BENCH {s} until {until_ts}")

    def _kill(self, ts, reason: str) -> None:
        self.killed, self.kill_reason = True, reason
        self.events.append(f"{ts} KILL {reason}")

    def halted(self) -> bool:
        return self.halted_day == self.day

    def benched(self, strategy: str) -> bool:
        return strategy in self.benched_until

    def reset(self, equity: float) -> None:
        """Human override after a kill."""
        self.killed, self.kill_reason = False, ""
        self.peak_equity = equity
        self.halted_day = None

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "day", "day_start_equity", "peak_equity", "halted_day", "killed",
            "kill_reason", "strat_peak", "benched_until")}

    def load_dict(self, d: dict) -> None:
        for k, v in d.items():
            setattr(self, k, v)
