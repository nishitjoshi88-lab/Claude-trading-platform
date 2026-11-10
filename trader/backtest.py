"""Event-driven backtest and performance report."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import Config
from .core import Trader
from .market import Panel


@dataclass
class Result:
    equity: pd.Series
    strategy_pnl: pd.DataFrame
    fees: float
    trades: int
    events: list[str]

    def stats(self) -> dict:
        eq = self.equity
        daily = eq.resample("1D").last().dropna()
        r = daily.pct_change().dropna()
        years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
        total = eq.iloc[-1] / eq.iloc[0] - 1
        dd = (eq / eq.cummax() - 1).min()
        return {
            "start": str(eq.index[0]), "end": str(eq.index[-1]),
            "total_return": total,
            "annual_return": (1 + total) ** (1 / years) - 1 if total > -1 else -1.0,
            "sharpe": float(r.mean() / r.std() * np.sqrt(365)) if r.std() > 0 else 0.0,
            "max_drawdown": float(dd),
            "positive_days": float((r > 0).mean()) if len(r) else 0.0,
            "worst_day": float(r.min()) if len(r) else 0.0,
            "fees": self.fees, "trades": self.trades,
            "strategy_pnl": {k: float(v) for k, v in self.strategy_pnl.iloc[-1].items()},
            "risk_events": len(self.events),
        }


def run(cfg: Config, panel: Panel, strategies=None, start: int = 0, end: int | None = None) -> Result:
    trader = Trader(cfg, len(panel.symbols), strategies)
    end = len(panel) if end is None else end
    eq = np.empty(end - start)
    names = list(trader.portfolio.pnl)
    spnl = np.empty((end - start, len(names)))
    for k, i in enumerate(range(start, end)):
        trader.step(panel.view(i))
        eq[k] = trader.portfolio.equity
        spnl[k] = [trader.portfolio.pnl[n] for n in names]
    idx = panel.index[start:end]
    return Result(pd.Series(eq, idx), pd.DataFrame(spnl, idx, names),
                  trader.portfolio.fees, trader.portfolio.trades, trader.risk.events)


def format_stats(s: dict) -> str:
    lines = [
        f"Period          {s['start'][:10]} to {s['end'][:10]}",
        f"Total return    {s['total_return']:+.1%}",
        f"Annual return   {s['annual_return']:+.1%}",
        f"Sharpe          {s['sharpe']:.2f}",
        f"Max drawdown    {s['max_drawdown']:.1%}",
        f"Positive days   {s['positive_days']:.0%}",
        f"Worst day       {s['worst_day']:.1%}",
        f"Fees paid       {s['fees']:,.0f}",
        f"Trades          {s['trades']}",
        f"Risk events     {s['risk_events']}",
        "Profit by strategy:",
    ]
    lines += [f"  {k:<10} {v:+,.0f}" for k, v in s["strategy_pnl"].items()]
    return "\n".join(lines)
