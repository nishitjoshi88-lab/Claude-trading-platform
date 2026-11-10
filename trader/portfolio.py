"""Position and profit accounting, kept separately for each strategy."""
from __future__ import annotations

import numpy as np

from .config import CostConfig
from .market import PERP, SPOT


class Portfolio:
    """Equity = initial equity + profit of every strategy book.

    Each book holds quantities with shape (2, N): row 0 spot, row 1 perp.
    Slippage is charged as a cost on the traded notional.
    """

    def __init__(self, strategies: list[str], n: int, initial_equity: float, costs: CostConfig):
        self.initial_equity = initial_equity
        self.costs = costs
        self.qty = {s: np.zeros((2, n)) for s in strategies}
        self.pnl = {s: 0.0 for s in strategies}
        self.last_px = np.full((2, n), np.nan)
        self.fees = 0.0
        self.trades = 0

    @property
    def equity(self) -> float:
        return self.initial_equity + sum(self.pnl.values())

    def gross(self) -> float:
        px = np.nan_to_num(self.last_px)
        return float(sum(np.abs(q * px).sum() for q in self.qty.values()))

    def mark(self, px: np.ndarray) -> None:
        """Book price changes since the last mark; missing prices carry over."""
        ok = np.isfinite(px) & np.isfinite(self.last_px)
        change = np.where(ok, px - self.last_px, 0.0)
        for s, q in self.qty.items():
            self.pnl[s] += float((q * change).sum())
        self.last_px = np.where(np.isfinite(px), px, self.last_px)

    def settle_funding(self, rate: np.ndarray) -> None:
        """Longs pay shorts when the rate is positive."""
        px = np.nan_to_num(self.last_px[PERP])
        for s, q in self.qty.items():
            self.pnl[s] -= float((q[PERP] * px * rate).sum())

    def trade(self, strategy: str, delta: np.ndarray) -> None:
        """Apply quantity changes (2, N) at the last marked prices."""
        px = self.last_px
        ok = np.isfinite(px) & (delta != 0)
        delta = np.where(ok, delta, 0.0)
        notional = np.abs(delta * np.nan_to_num(px))
        fee = np.array([[self.costs.spot_fee], [self.costs.perp_fee]]) + self.costs.slippage
        cost = float((notional * fee).sum())
        self.qty[strategy] = self.qty[strategy] + delta
        self.pnl[strategy] -= cost
        self.fees += cost
        self.trades += int(np.count_nonzero(delta))

    def to_dict(self) -> dict:
        return {"qty": {s: q.tolist() for s, q in self.qty.items()},
                "pnl": self.pnl, "last_px": np.where(np.isfinite(self.last_px), self.last_px, 0).tolist(),
                "fees": self.fees, "trades": self.trades}

    def load_dict(self, d: dict) -> None:
        for s in self.qty:
            if s in d["qty"]:
                self.qty[s] = np.array(d["qty"][s], dtype=float)
                self.pnl[s] = float(d["pnl"][s])
        px = np.array(d["last_px"], dtype=float)
        self.last_px = np.where(px > 0, px, np.nan)
        self.fees, self.trades = float(d["fees"]), int(d["trades"])


__all__ = ["Portfolio", "SPOT", "PERP"]
