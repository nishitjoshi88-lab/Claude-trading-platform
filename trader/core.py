"""The decision loop shared by the backtester and the live runner."""
from __future__ import annotations

import numpy as np

from .config import Config
from .market import MarketView
from .portfolio import Portfolio
from .risk import RiskGovernor
from .strategies import Context, Strategy, default_strategies


class Trader:
    def __init__(self, cfg: Config, n_symbols: int, strategies: list[Strategy] | None = None,
                 kill_file=None):
        self.cfg = cfg
        self.strategies = strategies if strategies is not None else default_strategies()
        names = [s.name for s in self.strategies]
        self.portfolio = Portfolio(names, n_symbols, cfg.initial_equity, cfg.costs)
        self.risk = RiskGovernor(cfg.risk, names, kill_file)
        self.risk.peak_equity = cfg.initial_equity
        self.pending: dict[str, np.ndarray] = {}
        self.min_order_frac = 0.001      # ignore orders below 0.1% of equity

    def step(self, view: MarketView, funding: np.ndarray | None = None,
             fill_now: bool = False) -> dict[str, np.ndarray]:
        """Process one bar.

        Backtest (fill_now=False): orders decided on this bar are filled at
        the next bar's prices. Live (fill_now=True): filled immediately.
        """
        pf, px = self.portfolio, view.prices()
        pf.mark(px)
        pf.settle_funding(view.funding() if funding is None else funding)
        for name, delta in self.pending.items():
            pf.trade(name, delta)
        self.pending = {}

        equity = pf.equity
        capital = {s.name: equity * self.cfg.allocations.get(s.name, 0.0) for s in self.strategies}
        self.risk.update(view.ts, equity, pf.pnl, capital)

        targets = {}
        for s in self.strategies:
            cur = pf.qty[s.name]
            if self.risk.killed or self.risk.benched(s.name) or capital[s.name] <= 0:
                tgt = np.zeros_like(cur)
            elif self.risk.halted():
                tgt = np.zeros_like(cur) if s.directional else cur.copy()
            else:
                ctx = Context(capital[s.name], equity, self.cfg.risk.risk_per_trade)
                tgt = s.target(view, cur, ctx)
            targets[s.name] = np.where(np.isfinite(px), tgt, cur)

        targets = self._apply_limits(targets, px, equity)

        orders = {}
        for name, tgt in targets.items():
            delta = tgt - pf.qty[name]
            notional = np.abs(delta * np.nan_to_num(px))
            closing = (tgt == 0) & (pf.qty[name] != 0)
            delta = np.where((notional >= self.min_order_frac * equity) | closing, delta, 0.0)
            if np.any(delta != 0):
                orders[name] = delta
        if fill_now:
            for name, delta in orders.items():
                pf.trade(name, delta)
        else:
            self.pending = orders
        return orders

    def _apply_limits(self, targets, px, equity):
        """Scale targets down, never up, keeping hedged legs in proportion."""
        p = np.nan_to_num(px)
        cap = self.cfg.risk.max_position_frac * max(equity, 0.0)
        for name, tgt in targets.items():
            worst = np.abs(tgt * p).max(axis=0)                 # per symbol
            scale = np.where(worst > cap, cap / np.where(worst > 0, worst, 1.0), 1.0)
            targets[name] = tgt * scale
        gross = sum(np.abs(t * p).sum() for t in targets.values())
        limit = self.cfg.risk.max_gross_leverage * max(equity, 0.0)
        if gross > limit > 0:
            targets = {n: t * (limit / gross) for n, t in targets.items()}
        return targets

    # --- persistence -----------------------------------------------------
    def to_dict(self) -> dict:
        return {"portfolio": self.portfolio.to_dict(), "risk": self.risk.to_dict(),
                "strategy_state": {s.name: s.state for s in self.strategies}}

    def load_dict(self, d: dict) -> None:
        self.portfolio.load_dict(d["portfolio"])
        self.risk.load_dict(d["risk"])
        for s in self.strategies:
            s.state = d.get("strategy_state", {}).get(s.name, {})
