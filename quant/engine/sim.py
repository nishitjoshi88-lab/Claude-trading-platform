"""Daily portfolio simulator for a small Indian cash-market account.

It trades whole shares at the prices actually quoted on the day, pays the
real charge schedule (including flat per-order fees that bite on small
orders), and never lets a decision use information from after it was made.

A strategy hands over a Plan: a table of target weights plus how they are to
be traded. Two modes:

  delivery  positions are carried overnight, long only, no leverage.
  intraday  positions are opened at the open and closed at the same day's
            close, long or short, with leverage up to the broker limit.

Timing of a weights row dated t:

  decide_at="close" (default)  the row was computed after the close of day t
                               and is traded on day t+1 (at the open, or at
                               the close if fill="close").
  decide_at="open"             the row may also use day t's opening price and
                               is traded at that open.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..data.store import Market
from .costs import CostModel


@dataclass
class Plan:
    weights: pd.DataFrame            # index: dates, columns: symbols, values: fraction of equity
    mode: str = "delivery"           # "delivery" or "intraday"
    decide_at: str = "close"         # "close" or "open"
    fill: str = "open"               # for decide_at="close": next day's "open" or "close"
    stop_loss: float | None = None   # exit if price falls this fraction below entry
    take_profit: float | None = None
    trailing_stop: float | None = None   # fraction below the highest close since entry
    max_hold: int | None = None      # trading days, delivery mode
    band: float = 0.0                # skip resizing smaller than this fraction of equity
    note: str = ""

    def __post_init__(self):
        assert self.mode in ("delivery", "intraday"), self.mode
        assert self.decide_at in ("close", "open"), self.decide_at
        assert self.fill in ("open", "close"), self.fill


@dataclass
class SimConfig:
    capital: float = 150_000.0
    costs: CostModel = field(default_factory=CostModel)
    max_participation: float = 0.02      # of the day's traded value, per order
    min_order_value: float = 2_000.0     # rupees; smaller resizes are skipped
    cash_buffer: float = 0.005           # fraction of equity kept back for charges
    intraday_leverage: float = 5.0       # cap on gross exposure / equity
    intraday_max_rank: int = 500         # liquidity rank allowed for intraday trades
    liquid_yield: float = 0.05           # yearly return on idle cash parked in a liquid fund
    park_min_cash: float = 10_000.0      # idle cash below this earns nothing
    delist_days: int = 20                # sessions without a price before a holding is written down
    delist_haircut: float = 0.20


@dataclass
class SimResult:
    equity: pd.Series
    trades: pd.DataFrame                 # one row per closed position
    costs: float                         # rupees of charges plus slippage
    traded_value: float
    orders: int
    exposure: pd.Series                  # invested value / equity at each close
    skipped: dict[str, int]

    @property
    def returns(self) -> pd.Series:
        return self.equity.pct_change().fillna(0.0)


def _ffill(a: np.ndarray) -> np.ndarray:
    """Forward-fill NaNs down each column."""
    mask = np.isfinite(a)
    idx = np.where(mask, np.arange(len(a))[:, None], 0)
    np.maximum.accumulate(idx, axis=0, out=idx)
    out = a[idx, np.arange(a.shape[1])]
    out[~np.maximum.accumulate(mask, axis=0)] = np.nan
    return out


def simulate(plan: Plan, market: Market, cfg: SimConfig | None = None,
             start=None, end=None, liq_rank: pd.DataFrame | None = None) -> SimResult:
    cfg = cfg or SimConfig()
    dates = market.dates
    w = plan.weights
    w = w.loc[:, [c for c in w.columns if c in market.close.columns]]
    used = w.columns[(w.fillna(0.0) != 0.0).any(axis=0).to_numpy()]
    W = w[used].reindex(dates).to_numpy(dtype=float)
    row_active = np.isfinite(w.reindex(dates)).any(axis=1).to_numpy() if w.shape[1] else np.zeros(len(dates), bool)

    def arr(f):
        return getattr(market, f)[used].to_numpy(dtype=float)

    O, H, L, C, F, TO = (arr(f) for f in ("open", "high", "low", "close", "factor", "turnover"))
    EQ = market.eq[used].to_numpy(dtype=bool)
    F = np.where(np.isfinite(F) & (F > 0), F, 1.0)
    Cff = _ffill(C)
    if liq_rank is None:
        liq_rank = market.liquidity_rank()
    # rank known at the previous close
    RK = liq_rank[used].shift(1).to_numpy(dtype=float)

    i0 = int(dates.searchsorted(pd.Timestamp(start))) if start is not None else 0
    i1 = int(dates.searchsorted(pd.Timestamp(end), side="right")) if end is not None else len(dates)
    n = len(used)
    equity = np.full(i1 - i0, np.nan)
    exposure = np.zeros(i1 - i0)
    state = _State(n, cfg, used, dates)

    if plan.mode == "intraday":
        _run_intraday(plan, cfg, state, W, row_active, O, H, L, C, F, TO, EQ, RK, i0, i1, equity, exposure, dates)
    else:
        last_valid = np.array([np.flatnonzero(np.isfinite(C[:, j]))[-1] if np.isfinite(C[:, j]).any() else -1
                               for j in range(n)], dtype=int)
        _run_delivery(plan, cfg, state, W, row_active, O, H, L, C, Cff, F, TO, RK, last_valid,
                      i0, i1, equity, exposure, dates)

    idx = dates[i0:i1]
    trades = pd.DataFrame(state.trades, columns=["symbol", "entry_date", "exit_date", "pnl", "cost_basis", "reason"])
    return SimResult(pd.Series(equity, idx, name="equity"), trades, state.costs, state.traded_value,
                     state.orders, pd.Series(exposure, idx, name="exposure"), dict(state.skipped))


class _State:
    def __init__(self, n: int, cfg: SimConfig, symbols, dates):
        self.cfg, self.symbols, self.dates = cfg, symbols, dates
        self.cash = cfg.capital
        self.shares = np.zeros(n)            # in adjusted-share units
        self.basis = np.zeros(n)             # rupees still tied up in the holding, charges included
        self.invested = np.zeros(n)          # rupees paid in over the life of the holding
        self.realized = np.zeros(n)          # profit booked so far on the holding
        self.entry_px = np.zeros(n)          # average adjusted entry price
        self.peak = np.zeros(n)
        self.entry_i = np.full(n, -1)
        self.blocked = np.zeros(n, bool)     # stopped out; wait for the plan to drop the name
        self.costs = 0.0
        self.traded_value = 0.0
        self.orders = 0
        self.trades: list[tuple] = []
        self.skipped = {"no_price": 0, "unaffordable": 0, "too_small": 0, "circuit": 0,
                        "ineligible": 0, "participation": 0, "no_cash": 0, "written_down": 0}

    def fill(self, j: int, d_raw: int, px: float, factor: float, segment: str, rank: float,
             i: int, reason: str = "") -> None:
        """Execute d_raw whole shares (signed) of symbol j at adjusted price px."""
        value = abs(d_raw) * px / factor
        cost = self.cfg.costs.charges(segment, "buy" if d_raw > 0 else "sell", value) \
            + self.cfg.costs.slippage(value, rank)
        d_adj = d_raw / factor
        self.costs += cost
        self.traded_value += value
        self.orders += 1
        if d_raw > 0:
            if self.shares[j] == 0:
                self.entry_i[j], self.entry_px[j], self.peak[j] = i, px, px
                self.basis[j] = self.invested[j] = self.realized[j] = 0.0
            else:
                self.entry_px[j] = (self.entry_px[j] * self.shares[j] + px * d_adj) / (self.shares[j] + d_adj)
            self.cash -= value + cost
            self.basis[j] += value + cost
            self.invested[j] += value + cost
            self.shares[j] += d_adj
        else:
            frac = min(1.0, -d_adj / self.shares[j])
            self.cash += value - cost
            self.realized[j] += value - cost - self.basis[j] * frac
            self.basis[j] *= (1 - frac)
            self.shares[j] += d_adj
            if frac >= 1.0 - 1e-9:
                self.close_out(j, i, reason)

    def close_out(self, j: int, i: int, reason: str) -> None:
        self.trades.append((self.symbols[j], self.dates[self.entry_i[j]], self.dates[i],
                            self.realized[j], self.invested[j], reason))
        self.shares[j] = self.basis[j] = 0.0


def _run_delivery(plan, cfg, st, W, row_active, O, H, L, C, Cff, F, TO, RK, last_valid,
                  i0, i1, equity, exposure, dates):
    n = W.shape[1]
    sl, tp, ts = plan.stop_loss, plan.take_profit, plan.trailing_stop
    daily_yield = cfg.liquid_yield / 252.0

    def sell_all(j, px, i, reason):
        raw = int(round(st.shares[j] * F[i, j]))
        if raw <= 0:
            st.shares[j] = 0.0
            return
        st.fill(j, -raw, px, F[i, j], "delivery", RK[i, j], i, reason)

    def rebalance(i, px, tgt):
        ref_px = np.where(np.isfinite(px), px, Cff[i - 1] if i > 0 else np.nan)
        eq_ref = st.cash + float(np.nansum(st.shares * ref_px))
        investable = eq_ref * (1 - cfg.cash_buffer)
        prev_c = Cff[i - 1] if i > 0 else np.full(n, np.nan)
        sells, buys = [], []
        for j in np.flatnonzero((tgt != 0) | (st.shares != 0)):
            t = 0.0 if st.blocked[j] else tgt[j]
            if t < 0:
                t = 0.0                                   # no overnight shorting in the cash market
            p = px[j]
            if not np.isfinite(p) or p <= 0:
                if t != 0 or st.shares[j] != 0:
                    st.skipped["no_price"] += 1
                continue
            raw_px = p / F[i, j]
            cur = int(round(st.shares[j] * F[i, j]))
            want = int(math.floor(t * investable / raw_px)) if t > 0 else 0
            d = want - cur
            if d == 0:
                if want == 0 and t > 0:
                    st.skipped["unaffordable"] += 1
                continue
            value = abs(d) * raw_px
            closing = want == 0
            if not closing and value < max(plan.band * eq_ref, cfg.min_order_value):
                st.skipped["too_small"] += 1
                continue
            # a stock locked at its price band cannot be traded against the move
            locked = np.isfinite(H[i, j]) and H[i, j] == L[i, j] and np.isfinite(prev_c[j])
            if locked and ((d > 0 and C[i, j] > prev_c[j] * 1.015) or (d < 0 and C[i, j] < prev_c[j] * 0.985)):
                st.skipped["circuit"] += 1
                continue
            cap = cfg.max_participation * TO[i, j] if np.isfinite(TO[i, j]) else 0.0
            if value > cap:
                d = int(math.copysign(math.floor(cap / raw_px), d))
                st.skipped["participation"] += 1
                if d == 0:
                    continue
            (sells if d < 0 else buys).append((t, j, d, p))
        for t, j, d, p in sells:
            st.fill(j, d, p, F[i, j], "delivery", RK[i, j], i, "rebalance")
        for t, j, d, p in sorted(buys, key=lambda x: -x[0]):
            raw_px = p / F[i, j]
            value = d * raw_px
            cost = cfg.costs.charges("delivery", "buy", value) + cfg.costs.slippage(value, RK[i, j])
            if value + cost > st.cash:
                d = int(math.floor(max(st.cash - 30.0, 0.0) / (raw_px * 1.005)))
                while d > 0 and d * raw_px + cfg.costs.charges("delivery", "buy", d * raw_px) \
                        + cfg.costs.slippage(d * raw_px, RK[i, j]) > st.cash:
                    d -= 1
                if d <= 0 or d * raw_px < cfg.min_order_value:
                    st.skipped["no_cash"] += 1
                    continue
            st.fill(j, d, p, F[i, j], "delivery", RK[i, j], i)

    for k, i in enumerate(range(i0, i1)):
        if plan.decide_at == "open":
            has_tgt, row = row_active[i], W[i]
        else:
            has_tgt, row = (row_active[i - 1], W[i - 1]) if i > 0 else (False, None)
        tgt = np.nan_to_num(row) if has_tgt else None
        if has_tgt:
            st.blocked &= (tgt != 0)

        if has_tgt and (plan.decide_at == "open" or plan.fill == "open"):
            rebalance(i, O[i], tgt)

        if sl or tp or ts:
            for j in np.flatnonzero(st.shares > 0):
                o, h, l = O[i, j], H[i, j], L[i, j]
                if not (np.isfinite(l) and np.isfinite(h)):
                    continue
                ep = st.entry_px[j]
                stop = max(ep * (1 - sl) if sl else -np.inf, st.peak[j] * (1 - ts) if ts else -np.inf)
                target = ep * (1 + tp) if tp else np.inf
                fresh = st.entry_i[j] == i                 # bought at today's open
                exit_px, why = None, ""
                if not fresh and np.isfinite(o) and o <= stop:
                    exit_px, why = o, "stop"               # gapped through the stop
                elif l <= stop:
                    exit_px, why = stop, "stop"
                elif not fresh and np.isfinite(o) and o >= target:
                    exit_px, why = o, "target"
                elif h >= target:
                    exit_px, why = target, "target"
                if exit_px is not None:
                    sell_all(j, exit_px, i, why)
                    st.blocked[j] = True

        if has_tgt and plan.decide_at == "close" and plan.fill == "close":
            rebalance(i, C[i], tgt)

        if plan.max_hold:
            for j in np.flatnonzero(st.shares > 0):
                if i - st.entry_i[j] + 1 >= plan.max_hold and np.isfinite(C[i, j]):
                    sell_all(j, C[i, j], i, "time")
                    st.blocked[j] = True

        for j in np.flatnonzero(st.shares > 0):
            if last_valid[j] >= 0 and i - last_valid[j] >= cfg.delist_days:
                # the symbol stopped trading for good: assume a partial loss
                value = st.shares[j] * Cff[i, j] * (1 - cfg.delist_haircut)
                st.cash += value
                st.realized[j] += value - st.basis[j]
                st.close_out(j, i, "written_down")
                st.skipped["written_down"] += 1

        held = st.shares > 0
        st.peak[held] = np.fmax(st.peak[held], C[i][held])
        invested = float(np.nansum(st.shares * Cff[i]))
        if st.cash > cfg.park_min_cash:
            st.cash += st.cash * daily_yield
        equity[k] = st.cash + invested
        exposure[k] = invested / equity[k] if equity[k] > 0 else 0.0


def _run_intraday(plan, cfg, st, W, row_active, O, H, L, C, F, TO, EQ, RK, i0, i1, equity, exposure, dates):
    sl, tp = plan.stop_loss, plan.take_profit
    costs = cfg.costs
    for k, i in enumerate(range(i0, i1)):
        if plan.decide_at == "open":
            has_tgt, row = row_active[i], W[i]
        else:
            has_tgt, row = (row_active[i - 1], W[i - 1]) if i > 0 else (False, None)
        if not has_tgt:
            equity[k] = st.cash
            continue
        tgt = np.nan_to_num(row)
        gross = np.abs(tgt).sum()
        if gross > cfg.intraday_leverage:
            tgt = tgt * (cfg.intraday_leverage / gross)
        eq_ref, used_gross = st.cash, 0.0
        for j in np.flatnonzero(tgt):
            o, h, l, c = O[i, j], H[i, j], L[i, j], C[i, j]
            if not (np.isfinite(o) and np.isfinite(h) and np.isfinite(l) and np.isfinite(c)) or o <= 0:
                st.skipped["no_price"] += 1
                continue
            if not EQ[i, j] or not (RK[i, j] <= cfg.intraday_max_rank):
                st.skipped["ineligible"] += 1              # not eligible for intraday leverage
                continue
            side = 1.0 if tgt[j] > 0 else -1.0
            raw_o = o / F[i, j]
            qty = int(math.floor(abs(tgt[j]) * eq_ref / raw_o))
            cap = cfg.max_participation * TO[i, j] if np.isfinite(TO[i, j]) else 0.0
            if qty * raw_o > cap:
                qty = int(math.floor(cap / raw_o))
                st.skipped["participation"] += 1
            if qty <= 0 or qty * raw_o < cfg.min_order_value:
                st.skipped["too_small" if qty > 0 else "unaffordable"] += 1
                continue
            exit_px, why = c, "close"
            if sl:
                stop = o * (1 - side * sl)
                if (side > 0 and l <= stop) or (side < 0 and h >= stop):
                    exit_px, why = stop, "stop"
            if tp and why == "close":
                target = o * (1 + side * tp)
                if (side > 0 and h >= target) or (side < 0 and l <= target):
                    exit_px, why = target, "target"
            v_in, v_out = qty * raw_o, qty * exit_px / F[i, j]
            cost = (costs.charges("intraday", "buy" if side > 0 else "sell", v_in)
                    + costs.charges("intraday", "sell" if side > 0 else "buy", v_out)
                    + costs.slippage(v_in, RK[i, j]) + costs.slippage(v_out, RK[i, j]))
            pnl = side * (v_out - v_in) - cost
            st.cash += pnl
            st.costs += cost
            st.traded_value += v_in + v_out
            st.orders += 2
            used_gross += v_in
            st.trades.append((st.symbols[j], dates[i], dates[i], pnl, v_in, why))
        equity[k] = st.cash
        exposure[k] = used_gross / eq_ref if eq_ref > 0 else 0.0
