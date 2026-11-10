"""Intraday simulator on one-minute bars.

A strategy emits entry events: "at the close of minute m on day d, go long
(or short) this stock, with this stop and this target". The simulator fills
at the next minute's open, walks the following bars to find which exit comes
first (stop, target, an exit signal, or the square-off time), and then runs
all candidate trades of the day through one account in time order, applying
position limits, leverage, a daily loss limit and real intraday charges.

Conventions that keep results honest:
  * a signal at the close of minute m trades at the open of minute m+1;
  * if a bar touches both the stop and the target, the stop is assumed first;
  * a stop that is gapped through fills at the bar's open, not at the stop;
  * market stops and trades in the first minutes pay extra slippage;
  * nothing is held overnight; idle capital earns nothing here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..engine.costs import CostModel
from ..engine.sim import SimResult
from .grid import ICtx, Grid, minute


@dataclass
class Signals:
    """Entry events for one symbol, plus an optional exit grid."""
    day: np.ndarray                    # day index into ctx.days
    col: np.ndarray                    # minute column whose close triggers the entry
    side: np.ndarray                   # +1 long, -1 short
    stop: np.ndarray                   # absolute stop price, NaN = use the plan's stop_pct
    target: np.ndarray                 # absolute target price, NaN = use the plan's target rule
    score: np.ndarray                  # higher = preferred when entries compete
    exit: np.ndarray | None = None     # bool (days, 375): leave at the next minute's open

    def __len__(self) -> int:
        return len(self.day)


def events(entry: np.ndarray, stop=None, target=None, score=None, exit: np.ndarray | None = None) -> Signals:
    """Build Signals from grids. `entry` is (days, 375) with +1/-1 where an
    entry triggers. `stop`, `target` are prices and `score` a ranking value;
    each may be a (days, 375) grid, a per-day (days,) array, or omitted."""
    entry = np.asarray(entry)
    d, c = np.nonzero(entry)

    def pick(x):
        if x is None:
            return np.full(len(d), np.nan)
        x = np.asarray(x, dtype=float)
        return x[d, c] if x.ndim == 2 else x[d]

    sc = pick(score)
    return Signals(d, c, entry[d, c].astype(np.int8), pick(stop), pick(target),
                   np.where(np.isfinite(sc), sc, 0.0), exit)


@dataclass
class IntradayPlan:
    signals: dict[str, Signals]
    stop_pct: float | None = None          # stop distance from the fill, when an event has no stop price
    target_pct: float | None = None        # target distance from the fill
    target_r: float | None = None          # target as a multiple of the stop distance
    exit_col: int = minute("15:15")        # square-off minute (fill at that minute's open)
    entry_from: int = 0                    # ignore signals before this minute column
    entry_until: int = minute("14:30")     # and after this one
    trades_per_symbol: int = 1             # per day
    risk_per_trade: float = 0.005          # share of equity lost if the stop is hit
    max_notional: float = 1.0              # position size cap, multiple of equity
    max_positions: int = 4                 # simultaneous
    max_trades_per_day: int = 8
    daily_loss_limit: float = 0.015        # no new trades after losing this share of equity in a day
    note: str = ""


@dataclass
class IntradaySimConfig:
    capital: float = 150_000.0
    costs: CostModel = field(default_factory=CostModel)
    leverage: float = 5.0                  # broker intraday limit on gross exposure
    min_order_value: float = 3_000.0
    short_max_rank: int = 150              # shorts only in the most liquid names (F&O stocks, no fixed price band)
    stop_extra_slip: float = 0.0003        # market stop orders
    open_slip_mult: float = 2.0            # slippage multiplier in the opening minutes
    open_slip_minutes: int = 5
    max_bar_participation: float = 0.10    # of the entry bar's traded quantity


def _candidates(sym: str, g: Grid, sig: Signals, plan: IntradayPlan, d0: int, d1: int) -> list[tuple]:
    out = []
    if len(sig) == 0:
        return out
    order = np.lexsort((sig.col, sig.day))
    X = plan.exit_col
    cur_day, done, busy_until = -1, 0, -1
    for k in order:
        d, c, side = int(sig.day[k]), int(sig.col[k]), int(sig.side[k])
        if d < d0 or d >= d1:
            continue
        if d != cur_day:
            cur_day, done, busy_until = d, 0, -1
        if done >= plan.trades_per_symbol or c < plan.entry_from or c > plan.entry_until or c < busy_until:
            continue
        e = c + 1
        while e < min(c + 4, X) and not np.isfinite(g.open[d, e]):
            e += 1                                        # no trade that minute: take the next print
        if e >= X or not np.isfinite(g.open[d, e]):
            continue
        px = float(g.open[d, e])
        stop = float(sig.stop[k])
        if not np.isfinite(stop):
            stop = px * (1 - side * plan.stop_pct) if plan.stop_pct else np.nan
        if np.isfinite(stop) and (px - stop) * side <= 0:
            continue                                      # already through the stop at the fill
        risk = abs(px - stop) if np.isfinite(stop) else np.nan
        target = float(sig.target[k])
        if not np.isfinite(target):
            if plan.target_pct:
                target = px * (1 + side * plan.target_pct)
            elif plan.target_r and np.isfinite(risk):
                target = px + side * plan.target_r * risk
        hi, lo, op = g.high[d, e:X], g.low[d, e:X], g.open[d, e:X]
        n = X - e
        if side > 0:
            stop_hit = lo <= stop if np.isfinite(stop) else np.zeros(n, bool)
            tgt_hit = hi >= target if np.isfinite(target) else np.zeros(n, bool)
        else:
            stop_hit = hi >= stop if np.isfinite(stop) else np.zeros(n, bool)
            tgt_hit = lo <= target if np.isfinite(target) else np.zeros(n, bool)
        j_stop = int(np.argmax(stop_hit)) if stop_hit.any() else n
        j_tgt = int(np.argmax(tgt_hit)) if tgt_hit.any() else n
        j_sig = n
        if sig.exit is not None:
            ex = sig.exit[d, e:X - 1]
            if ex.any():
                j_sig = int(np.argmax(ex)) + 1            # act at the next minute's open
        j = min(j_stop, j_tgt, j_sig)
        if j == n:                                        # square-off
            exit_px, why, xcol = g.open[d, X], "time", X
            if not np.isfinite(exit_px):
                closes = g.close[d, e:X]
                ok = np.isfinite(closes)
                exit_px = closes[ok][-1] if ok.any() else px
        elif j == j_stop:
            gapped = j > 0 and np.isfinite(op[j]) and (op[j] - stop) * side < 0
            exit_px, why, xcol = (op[j] if gapped else stop), "stop", e + j
        elif j == j_tgt:
            exit_px, why, xcol = target, "target", e + j
        else:
            exit_px, why, xcol = op[j], "signal", e + j
            if not np.isfinite(exit_px):
                closes = g.close[d, e:e + j]
                ok = np.isfinite(closes)
                exit_px = closes[ok][-1] if ok.any() else px
        vol = g.volume[d, e]
        out.append((d, e, xcol, sym, side, px, float(exit_px), risk, why, float(sig.score[k]),
                    float(vol) if np.isfinite(vol) else 0.0))
        done += 1
        busy_until = xcol
    return out


def simulate_intraday(plan: IntradayPlan, ctx: ICtx, cfg: IntradaySimConfig | None = None,
                      start=None, end=None) -> SimResult:
    cfg = cfg or IntradaySimConfig()
    d0, d1 = ctx.day_slice(start, end)
    cands = []
    for sym, sig in plan.signals.items():
        cands += _candidates(sym, ctx.grid(sym), sig, plan, d0, d1)
    cands.sort(key=lambda t: (t[0], t[1], -t[9]))

    equity = np.empty(d1 - d0)
    exposure = np.zeros(d1 - d0)
    eq, costs_total, traded, orders = cfg.capital, 0.0, 0.0, 0
    skipped = {"loss_limit": 0, "max_trades": 0, "max_positions": 0, "ineligible": 0,
               "too_small": 0, "no_margin": 0, "participation": 0}
    trades = []
    pos = 0
    for k, d in enumerate(range(d0, d1)):
        realized, margin_used, n_trades, peak_gross = 0.0, 0.0, 0, 0.0
        open_pos: list[tuple] = []                       # (exit_col, margin, pnl)
        while pos < len(cands) and cands[pos][0] == d:
            _, e, xcol, sym, side, px, exit_px, risk, why, score, vol = cands[pos]
            pos += 1
            still = []
            for p in open_pos:                           # release positions that have exited by now
                if p[0] <= e:
                    realized += p[2]
                    margin_used -= p[1]
                else:
                    still.append(p)
            open_pos = still
            if realized <= -plan.daily_loss_limit * eq:
                skipped["loss_limit"] += 1
                continue
            if n_trades >= plan.max_trades_per_day:
                skipped["max_trades"] += 1
                continue
            if len(open_pos) >= plan.max_positions:
                skipped["max_positions"] += 1
                continue
            rank = ctx.ranks.get(sym, float("nan"))
            if side < 0 and not rank <= cfg.short_max_rank:
                skipped["ineligible"] += 1
                continue
            cap_value = plan.max_notional * eq
            value = plan.risk_per_trade * eq / risk * px if risk == risk and risk > 0 else cap_value
            value = min(value, cap_value)
            free = (eq + realized - margin_used) * cfg.leverage
            if value > free:
                value = free
                skipped["no_margin"] += 1
            qty = math.floor(value / px) if value > 0 else 0
            max_q = math.floor(cfg.max_bar_participation * vol)
            if qty > max_q:
                qty = max_q
                skipped["participation"] += 1
            if qty <= 0 or qty * px < cfg.min_order_value:
                skipped["too_small"] += 1
                continue
            v_in, v_out = qty * px, qty * exit_px
            slip_in = cfg.costs.slippage(v_in, rank) * (cfg.open_slip_mult if e < cfg.open_slip_minutes else 1.0)
            slip_out = cfg.costs.slippage(v_out, rank) + (v_out * cfg.stop_extra_slip if why == "stop" else 0.0)
            cost = (cfg.costs.charges("intraday", "buy" if side > 0 else "sell", v_in)
                    + cfg.costs.charges("intraday", "sell" if side > 0 else "buy", v_out) + slip_in + slip_out)
            pnl = side * (v_out - v_in) - cost
            margin = v_in / cfg.leverage
            open_pos.append((xcol, margin, pnl))
            margin_used += margin
            peak_gross = max(peak_gross, margin_used * cfg.leverage)
            n_trades += 1
            costs_total += cost
            traded += v_in + v_out
            orders += 2
            trades.append((sym, ctx.days[d], ctx.days[d], pnl, v_in, why, side, e, xcol, px, exit_px, qty))
        realized += sum(p[2] for p in open_pos)
        exposure[k] = peak_gross / eq if eq > 0 else 0.0
        eq += realized
        equity[k] = eq
    idx = ctx.days[d0:d1]
    tr = pd.DataFrame(trades, columns=["symbol", "entry_date", "exit_date", "pnl", "cost_basis", "reason",
                                       "side", "entry_col", "exit_col", "entry_px", "exit_px", "qty"])
    return SimResult(pd.Series(equity, idx, name="equity"), tr, costs_total, traded, orders,
                     pd.Series(exposure, idx, name="exposure"), skipped)


def check_lookahead_intraday(fn, ctx: ICtx, params: dict | None = None, n_cuts: int = 5,
                             n_symbols: int = 6, seed: int = 0) -> list[str]:
    """Re-run the strategy on bars cut off at a few (day, minute) points; every
    event and exit flag up to the cut must be unchanged."""
    params = params or {}
    rng = np.random.default_rng(seed)
    step = max(1, len(ctx.symbols) // n_symbols)
    sub = ctx.subset(ctx.symbols[::step][:n_symbols])
    full = fn(sub, **params)
    problems = []
    # Cut exactly at minutes where the strategy acts: a signal that peeks even
    # one bar ahead then changes, because that bar is hidden.
    first_day = len(ctx.days) // 3
    points = set()
    for sig in full.signals.values():
        keep = sig.day >= first_day
        points.update(zip(sig.day[keep].tolist(), sig.col[keep].tolist()))
        if sig.exit is not None:
            d, c = np.nonzero(sig.exit[first_day:])
            points.update(zip((d[:200] + first_day).tolist(), c[:200].tolist()))
    points = sorted(p for p in points if p[1] < 374)
    if not points:
        return ["no signals in the last two thirds of the sample"]
    picks = rng.choice(len(points), size=min(n_cuts, len(points)), replace=False)
    cuts = [points[k] for k in sorted(picks)]
    cuts.append((int(rng.integers(first_day, len(ctx.days))), int(rng.integers(20, 340))))
    for di, col in cuts:
        part = fn(sub.cut(di, col), **params)
        for sym in sub.symbols:
            a, b = full.signals.get(sym), part.signals.get(sym)

            def known(s):
                if s is None or len(s) == 0:
                    return set()
                keep = (s.day < di) | ((s.day == di) & (s.col <= col))
                keep &= s.day >= di - 2
                return {(int(d), int(c), int(sd), round(float(st), 4) if st == st else None,
                         round(float(tg), 4) if tg == tg else None)
                        for d, c, sd, st, tg in zip(s.day[keep], s.col[keep], s.side[keep], s.stop[keep], s.target[keep])}

            ka, kb = known(a), known(b)
            if ka != kb:
                problems.append(f"{sym}: entries up to {ctx.days[di].date()} minute {col} change when later "
                                f"bars are hidden ({len(ka ^ kb)} differ)")
                continue
            ea = a.exit if a is not None else None
            eb = b.exit if b is not None else None
            if (ea is None) != (eb is None):
                problems.append(f"{sym}: exit grid present in only one run")
            elif ea is not None:
                lo = max(di - 2, 0)
                same = np.array_equal(ea[lo:di], eb[lo:di]) and np.array_equal(ea[di, :col + 1], eb[di, :col + 1])
                if not same:
                    problems.append(f"{sym}: exit flags up to {ctx.days[di].date()} minute {col} change "
                                    f"when later bars are hidden")
    return problems
