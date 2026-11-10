"""The three strategies. Each returns target quantities, shape (2, N):
row 0 spot, row 1 perp. They see the market only through a MarketView.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .market import PERP, SPOT, MarketView

HOURS_PER_YEAR = 24 * 365


@dataclass
class Context:
    capital: float          # this strategy's share of equity
    equity: float           # whole account
    risk_per_trade: float


class Strategy:
    name = "base"
    directional = True      # flattened when the daily loss limit trips

    def __init__(self):
        self.state: dict = {}

    def target(self, view: MarketView, cur: np.ndarray, ctx: Context) -> np.ndarray:
        raise NotImplementedError


class Carry(Strategy):
    """Long spot, short the same quantity of perp, collect funding.

    Enters when recent funding annualises above `entry_apr`, leaves when it
    falls below `exit_apr`. The gap between the two pays for the round trip.
    """
    name = "carry"
    directional = False

    def __init__(self, lookback=24 * 7, entry_apr=0.12, exit_apr=0.03,
                 max_slots=5, min_slots=3, leg_frac=0.8, resize_band=0.3):
        super().__init__()
        self.lookback, self.entry_apr, self.exit_apr = lookback, entry_apr, exit_apr
        self.max_slots, self.min_slots = max_slots, min_slots
        self.leg_frac, self.resize_band = leg_frac, resize_band

    def target(self, view, cur, ctx):
        out = np.zeros_like(cur)
        f = view.window("funding", self.lookback)
        if len(f) < self.lookback:
            return out
        px = view.prices()
        apr = f.sum(axis=0) / len(f) * HOURS_PER_YEAR
        tradable = np.isfinite(px[SPOT]) & np.isfinite(px[PERP]) & (px[SPOT] > 0)
        held = cur[PERP] < 0
        want = tradable & np.where(held, apr > self.exit_apr, apr > self.entry_apr)
        # keep what we hold first, then the richest new ones
        order = sorted(np.flatnonzero(want), key=lambda j: (not held[j], -apr[j]))[: self.max_slots]
        if not order:
            return out
        leg = ctx.capital * self.leg_frac / max(len(order), self.min_slots)
        for j in order:
            cur_notional = abs(cur[PERP, j]) * px[PERP, j]
            if held[j] and abs(cur_notional - leg) < self.resize_band * leg:
                out[:, j] = cur[:, j]
            else:
                q = leg / px[SPOT, j]
                out[SPOT, j], out[PERP, j] = q, -q
        return out


class Trend(Strategy):
    """Follow the 5-day versus 20-day average on the perp, sized so each
    symbol contributes roughly the same volatility."""
    name = "trend"

    def __init__(self, fast=24 * 5, slow=24 * 20, vol_bars=24 * 10,
                 target_vol=0.40, max_weight=1.0, band=0.3, long_only=False):
        super().__init__()
        self.fast, self.slow, self.vol_bars = fast, slow, vol_bars
        self.target_vol, self.max_weight, self.band = target_vol, max_weight, band
        self.long_only = long_only

    def target(self, view, cur, ctx):
        out = np.zeros_like(cur)
        w = view.window("perp", self.slow)
        if len(w) < self.slow:
            return out
        px = w[-1]
        ok = np.isfinite(w).all(axis=0) & (px > 0)
        if not ok.any():
            return out
        with np.errstate(invalid="ignore", divide="ignore"):
            signal = np.sign(w[-self.fast:].mean(axis=0) - w.mean(axis=0))
            r = np.diff(np.log(w[-self.vol_bars - 1:]), axis=0)
            vol = r.std(axis=0) * np.sqrt(HOURS_PER_YEAR)
            weight = np.minimum(self.target_vol / vol, self.max_weight)
        if self.long_only:
            signal = np.maximum(signal, 0)
        per_symbol = ctx.capital / view.n
        want = np.where(ok & (vol > 0), signal * weight * per_symbol / px, 0.0)
        have = cur[PERP]
        flip = np.sign(want) != np.sign(have)
        drift = np.abs(want - have) > self.band * np.abs(want)
        out[PERP] = np.where(flip | drift, want, have)
        return out


class Reversion(Strategy):
    """Buy the perp after an unusually sharp 24-hour fall, exit on a stop,
    a profit target, or after a fixed holding time."""
    name = "reversion"

    def __init__(self, ret_bars=24, hist_bars=24 * 30, z_entry=-2.5,
                 min_stop=0.03, take_mult=1.5, max_hold=48, max_open=3):
        super().__init__()
        self.ret_bars, self.hist_bars, self.z_entry = ret_bars, hist_bars, z_entry
        self.min_stop, self.take_mult = min_stop, take_mult
        self.max_hold, self.max_open = max_hold, max_open

    def target(self, view, cur, ctx):
        out = np.zeros_like(cur)
        w = view.window("perp", self.hist_bars + self.ret_bars)
        px = w[-1]
        now = view.ts.isoformat()
        # forget entries that never filled (blocked by the risk governor)
        for s in [s for s, e in self.state.items()
                  if e["ts"] != now and cur[PERP, view.symbols.index(s)] == 0]:
            del self.state[s]
        # manage open positions
        for s in list(self.state):
            j, e = view.symbols.index(s), self.state[s]
            e["bars"] += 1
            p = px[j]
            done = (not np.isfinite(p) or p <= e["px"] * (1 - e["stop"])
                    or p >= e["px"] * (1 + self.take_mult * e["stop"])
                    or e["bars"] > self.max_hold)
            if done:
                del self.state[s]
            else:
                out[PERP, j] = cur[PERP, j] if cur[PERP, j] != 0 else e["qty"]
        if len(w) < self.hist_bars + self.ret_bars:
            return out
        with np.errstate(invalid="ignore", divide="ignore"):
            r = w[self.ret_bars:] / w[:-self.ret_bars] - 1
            z = (r[-1] - r.mean(axis=0)) / r.std(axis=0)
            hourly = np.diff(np.log(w[-self.ret_bars * 5:]), axis=0).std(axis=0)
        for j in np.argsort(z):
            if len(self.state) >= self.max_open or not z[j] < self.z_entry:
                break
            s = view.symbols[j]
            if s in self.state or not np.isfinite(px[j]):
                continue
            stop = max(2 * hourly[j] * np.sqrt(self.ret_bars), self.min_stop)
            notional = min(ctx.risk_per_trade * ctx.equity / stop, ctx.capital / self.max_open)
            qty = notional / px[j]
            self.state[s] = {"px": float(px[j]), "stop": float(stop), "qty": float(qty),
                             "bars": 0, "ts": now}
            out[PERP, j] = qty
        return out


def default_strategies() -> list[Strategy]:
    return [Carry(), Trend(), Reversion()]
