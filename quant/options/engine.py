"""Simulator for index option structures on daily futures-and-options data.

A strategy describes a structure (legs chosen relative to the index level),
when to enter relative to expiry, and exit rules. The simulator opens one
position per expiry cycle at the day's closing prices, marks it daily at
settlement prices, and settles at expiry against the index close.

Sizing reflects a small account today. Index lots are large (about Rs 16-17
lakh of index exposure each), so the simulator holds lot exposure constant at
`lot_notional` rupees throughout history: one lot always controls the same
rupee exposure relative to the starting capital as it does now. A structure
the account cannot margin is skipped and counted, not shrunk.

Limits of daily data, stated plainly: entries and exits happen at the close;
stops are checked once a day, so intraday stop strategies (for example the
popular 9:20 straddle) cannot be represented.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..engine.costs import CostModel
from ..engine.sim import SimResult


@dataclass(frozen=True)
class Leg:
    right: str                  # "CE" or "PE"
    side: int                   # +1 buy, -1 sell
    how: str = "pct"            # "atm", "pct" (percent out of the money) or "sigma" (expected-move units)
    amount: float = 0.0         # 0.03 = 3% out of the money; for "sigma", multiples of the expected move to expiry
    ratio: int = 1


@dataclass
class OptionPlan:
    symbol: str
    structures: list[list[Leg]]              # entry_signal value k (1-based) selects structures[k-1]
    series: str = "weekly"                   # "weekly" (nearest expiry) or "monthly"
    dte: int = 4                             # enter at the close this many trading days before expiry
    exit_dte: int = 0                        # 0 = hold to expiry; k = exit at the close k days before
    entry_signal: pd.Series | None = None    # per date, decided at that close, used the next day; None = always structure 1
    stop_mult: float | None = None           # exit when loss reaches this multiple of the credit (or fraction of debit)
    target_frac: float | None = None         # exit when profit reaches this fraction of the maximum profit (credit) or of the debit
    risk_frac: float = 0.05                  # share of equity that may be lost on one trade (defined-risk structures)
    note: str = ""


@dataclass
class OptionSimConfig:
    capital: float = 150_000.0
    costs: CostModel = field(default_factory=CostModel)
    lot_notional: float = 1_650_000.0        # rupees of index exposure per lot today
    naked_margin: float = 0.115              # margin on an unhedged short option, share of notional
    spread_margin_mult: float = 1.25         # margin on a defined-risk structure = this times its maximum loss
    margin_use: float = 0.90                 # share of equity that may be blocked as margin
    slippage: float = 0.0075                 # of premium, per leg per trade
    min_slippage_pts: float = 0.10           # index points
    min_contracts: int = 200                 # contracts traded that day for a strike to be usable at entry
    exercise_stt: float = 0.00125            # on intrinsic value of long options settled in the money
    liquid_yield: float = 0.05               # on funds not blocked as margin
    park_min_cash: float = 10_000.0
    vix_fallback: float = 0.18


def _expiry_table(opt: pd.DataFrame) -> tuple[np.ndarray, set]:
    exp = np.sort(opt["expiry"].unique())
    e = pd.DatetimeIndex(exp)
    monthly = set(pd.Series(e).groupby([e.year, e.month]).max())
    return exp, monthly


def simulate_options(plan: OptionPlan, fo: pd.DataFrame, cfg: OptionSimConfig | None = None,
                     start=None, end=None, vix: pd.Series | None = None) -> SimResult:
    """`fo` is the long table from quant.data.store.load_fo(plan.symbol)."""
    cfg = cfg or OptionSimConfig()
    opt = fo[fo["instrument"] == "OPT"]
    dates = pd.DatetimeIndex(np.sort(fo["date"].unique()))
    spot = fo.groupby("date")["underlying"].first().reindex(dates)
    if spot.isna().any():                       # fall back to the nearest future
        fut = fo[fo["instrument"] == "FUT"].sort_values(["date", "expiry"]).groupby("date")["close"].first()
        spot = spot.fillna(fut.reindex(dates))
    expiries, monthly = _expiry_table(opt)
    by_date = {d: g.set_index(["expiry", "right", "strike"]).sort_index() for d, g in opt.groupby("date")}
    pos_of = {d: k for k, d in enumerate(dates)}
    sig = None
    if plan.entry_signal is not None:
        sig = plan.entry_signal.reindex(dates).shift(1)          # decided yesterday, used today
    vix = (vix.reindex(dates).ffill() / 100.0) if vix is not None else None

    i0 = int(dates.searchsorted(pd.Timestamp(start))) if start is not None else 0
    i1 = int(dates.searchsorted(pd.Timestamp(end), side="right")) if end is not None else len(dates)
    cash, costs_total, traded, orders = cfg.capital, 0.0, 0.0, 0
    equity = np.full(i1 - i0, np.nan)
    exposure = np.zeros(i1 - i0)
    trades, skipped = [], {"unaffordable": 0, "illiquid": 0, "no_strike": 0, "no_signal": 0}
    pos = None                                                   # the single open position
    done_expiries = set()

    def leg_costs(side: str, premium_value: float) -> float:
        return cfg.costs.charges("options", side, premium_value)

    def slip(px: float) -> float:
        return max(px * cfg.slippage, cfg.min_slippage_pts)

    def target_expiry(i: int):
        """The expiry that is exactly plan.dte trading days ahead, if any."""
        j = i + plan.dte
        if j >= len(dates):
            return None
        d = dates[j]
        if np.datetime64(d) not in expiries:
            return None
        if plan.series == "monthly" and d not in monthly:
            return None
        if plan.series == "weekly":
            # nearest expiry only: no earlier expiry between today and d
            nxt = expiries[np.searchsorted(expiries, np.datetime64(dates[i]), side="right")] \
                if np.searchsorted(expiries, np.datetime64(dates[i]), side="right") < len(expiries) else None
            if plan.dte > 0 and nxt is not None and pd.Timestamp(nxt) != d:
                return None
        return d

    for k, i in enumerate(range(i0, i1)):
        d = dates[i]
        S = float(spot.iloc[i])
        chain = by_date.get(d)

        # --- manage the open position ---------------------------------------
        if pos is not None:
            mult, lots = pos["mult"], pos["lots"]
            if d >= pos["expiry"]:
                value = 0.0
                for leg, K in zip(pos["legs"], pos["strikes"]):
                    intrinsic = max(S - K, 0.0) if leg.right == "CE" else max(K - S, 0.0)
                    value += leg.side * leg.ratio * intrinsic
                    if leg.side > 0 and intrinsic > 0:
                        c = intrinsic * mult * lots * leg.ratio * cfg.exercise_stt
                        cash -= c
                        costs_total += c
                cash += value * mult * lots
                trades.append((plan.symbol, pos["entry_date"], d, cash - pos["cash_before"], pos["risk"], "expiry"))
                pos = None
            elif chain is not None:
                marks, ok = [], True
                for leg, K in zip(pos["legs"], pos["strikes"]):
                    try:
                        row = chain.loc[(pos["expiry"], leg.right, K)]
                    except KeyError:
                        ok = False
                        break
                    px = row["close"] if row["contracts"] > 0 and row["close"] > 0 else row["settle"]
                    marks.append(float(px))
                if ok:
                    value = sum(l.side * l.ratio * m for l, m in zip(pos["legs"], marks))
                    pos["value"] = value
                    pnl_pts = value - pos["entry_value"]             # per unit; entry_value is signed the same way
                    exit_now, why = False, ""
                    base = abs(pos["entry_value"])
                    if plan.stop_mult is not None and pnl_pts <= -plan.stop_mult * base:
                        exit_now, why = True, "stop"
                    elif plan.target_frac is not None and pnl_pts >= plan.target_frac * base:
                        exit_now, why = True, "target"
                    elif plan.exit_dte > 0 and pos_of[pos["expiry"]] - i <= plan.exit_dte:
                        exit_now, why = True, "time"
                    if exit_now:
                        for leg, m in zip(pos["legs"], marks):
                            q = mult * lots * leg.ratio
                            fill = m - leg.side * slip(m)            # sell what we own lower, buy back higher
                            fill = max(fill, 0.0)
                            c = leg_costs("sell" if leg.side > 0 else "buy", fill * q)
                            cash += leg.side * fill * q - c
                            costs_total += c + abs(m - fill) * q
                            traded += fill * q
                            orders += 1
                        trades.append((plan.symbol, pos["entry_date"], d, cash - pos["cash_before"], pos["risk"], why))
                        pos = None

        # --- entry -----------------------------------------------------------
        if pos is None and chain is not None and np.isfinite(S):
            exp = target_expiry(i)
            if exp is not None and exp not in done_expiries:
                done_expiries.add(exp)
                which = 1
                if sig is not None:
                    v = sig.iloc[i]
                    which = int(v) if np.isfinite(v) else 0
                if which <= 0 or which > len(plan.structures):
                    skipped["no_signal"] += 1
                else:
                    legs = plan.structures[which - 1]
                    try:
                        sub = chain.loc[exp]
                    except KeyError:
                        sub = None
                    iv = float(vix.iloc[i]) if vix is not None and np.isfinite(vix.iloc[i]) else cfg.vix_fallback
                    move = S * iv * math.sqrt(max((exp - d).days, 1) / 365.0)
                    strikes, prices, ok = [], [], sub is not None
                    for leg in (legs if ok else []):
                        try:
                            ks = sub.loc[leg.right]
                        except KeyError:
                            ok = False
                            skipped["no_strike"] += 1
                            break
                        dist = 0.0 if leg.how == "atm" else leg.amount * S if leg.how == "pct" else leg.amount * move
                        want = S + dist if leg.right == "CE" else S - dist
                        K = float(ks.index[np.abs(ks.index.to_numpy() - want).argmin()])
                        row = ks.loc[K]
                        if row["contracts"] < cfg.min_contracts or not row["close"] > 0:
                            ok = False
                            skipped["illiquid"] += 1
                            break
                        strikes.append(K)
                        prices.append(float(row["close"]))
                    if ok:
                        mult = cfg.lot_notional / S
                        fills = [p + leg.side * slip(p) for leg, p in zip(legs, prices)]
                        entry_value = sum(l.side * l.ratio * f for l, f in zip(legs, fills))   # >0 debit, <0 credit
                        max_loss_pts = _max_loss(legs, strikes, entry_value)
                        if math.isinf(max_loss_pts):
                            margin = cfg.naked_margin * cfg.lot_notional * max(
                                sum(l.ratio for l in legs if l.side < 0 and l.right == "CE"),
                                sum(l.ratio for l in legs if l.side < 0 and l.right == "PE"), 1)
                            risk_per_lot = margin
                        elif entry_value > 0 and all(l.side > 0 for l in legs):
                            margin = risk_per_lot = entry_value * mult                          # long premium only
                        else:
                            risk_per_lot = max_loss_pts * mult
                            margin = cfg.spread_margin_mult * risk_per_lot
                        eq_now = cash
                        lots = int(min(plan.risk_frac * eq_now // max(risk_per_lot, 1e-9),
                                       cfg.margin_use * eq_now // max(margin, 1e-9)))
                        if lots < 1:
                            skipped["unaffordable"] += 1
                        else:
                            cash_before = cash
                            for leg, f, p in zip(legs, fills, prices):
                                q = mult * lots * leg.ratio
                                c = leg_costs("buy" if leg.side > 0 else "sell", f * q)
                                cash -= leg.side * f * q + c
                                costs_total += c + abs(f - p) * q
                                traded += f * q
                                orders += 1
                            pos = {"legs": legs, "strikes": strikes, "expiry": exp, "entry_date": d,
                                   "entry_value": entry_value, "value": entry_value, "mult": mult, "lots": lots,
                                   "margin": margin * lots, "risk": risk_per_lot * lots, "cash_before": cash_before}

        # --- mark ------------------------------------------------------------
        held = pos["value"] * pos["mult"] * pos["lots"] if pos is not None else 0.0
        free = cash + min(held, 0.0) - (pos["margin"] if pos is not None else 0.0)
        if free > cfg.park_min_cash:
            cash += free * cfg.liquid_yield / 252.0
        equity[k] = cash + held
        exposure[k] = pos["margin"] / equity[k] if pos is not None and equity[k] > 0 else 0.0

    idx = dates[i0:i1]
    tr = pd.DataFrame(trades, columns=["symbol", "entry_date", "exit_date", "pnl", "cost_basis", "reason"])
    return SimResult(pd.Series(equity, idx, name="equity"), tr, costs_total, traded, orders,
                     pd.Series(exposure, idx, name="exposure"), skipped)


def _max_loss(legs: list[Leg], strikes: list[float], entry_value: float) -> float:
    """Largest loss per unit at expiry, in index points; inf if unbounded."""
    net_calls = sum(l.side * l.ratio for l in legs if l.right == "CE")
    if net_calls < 0:
        return math.inf                                   # short calls not covered: unlimited upside loss
    points = sorted(set(strikes)) + [0.0]
    worst = 0.0
    for s in points + [max(strikes) * 3]:
        payoff = sum(l.side * l.ratio * (max(s - K, 0.0) if l.right == "CE" else max(K - s, 0.0))
                     for l, K in zip(legs, strikes))
        worst = min(worst, payoff - entry_value)
    net_puts = sum(l.side * l.ratio for l in legs if l.right == "PE")
    if net_puts < 0:
        # uncovered short puts: loss is bounded by the strike but far beyond a small account
        return math.inf
    return -worst
