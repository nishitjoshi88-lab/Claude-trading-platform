import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from quant.engine.costs import CostModel
from quant.options import Leg, OptionPlan, OptionSimConfig, simulate_options
from quant.options.engine import _max_loss


def bs(S, K, T, vol, right):
    if T <= 0:
        return max(S - K, 0.0) if right == "CE" else max(K - S, 0.0)
    d1 = (math.log(S / K) + 0.5 * vol * vol * T) / (vol * math.sqrt(T))
    d2 = d1 - vol * math.sqrt(T)
    call = S * norm.cdf(d1) - K * norm.cdf(d2)
    return call if right == "CE" else call - S + K


def chain(spots, start="2020-01-01", vol=0.2, step=50.0, contracts=5000):
    """Weekly Thursday expiries; every strike within 12% of spot."""
    dates = pd.bdate_range(start, periods=len(spots))
    expiries = [d for d in pd.bdate_range(start, dates[-1] + pd.Timedelta(days=21)) if d.weekday() == 3]
    rows = []
    for d, S in zip(dates, spots):
        for e in [e for e in expiries if e >= d][:3]:
            T = (e - d).days / 365.0
            lo, hi = math.floor(S * 0.88 / step) * step, math.ceil(S * 1.12 / step) * step
            for K in np.arange(lo, hi + step, step):
                for right in ("CE", "PE"):
                    p = bs(S, K, T, vol, right)
                    rows.append((d, "OPT", e, K, right, p, p, p, p, p, contracts, 1000, 50, S))
    cols = ["date", "instrument", "expiry", "strike", "right", "open", "high", "low", "close",
            "settle", "contracts", "oi", "lot", "underlying"]
    return pd.DataFrame(rows, columns=cols)


FREE = CostModel(segments={k: type(v)(0, 0, 0, 0, 0, 0, 0, 0) for k, v in CostModel().segments.items()},
                 sebi=0, ipft=0, gst=0)


def cfg(**kw):
    base = dict(capital=150_000.0, costs=FREE, slippage=0.0, min_slippage_pts=0.0, exercise_stt=0.0,
                liquid_yield=0.0, lot_notional=1_000_000.0)
    base.update(kw)
    return OptionSimConfig(**base)


def test_max_loss_of_common_structures():
    spread = [Leg("PE", -1), Leg("PE", +1)]
    assert _max_loss(spread, [10000, 9800], -60.0) == pytest.approx(140.0)       # width 200 less credit 60
    assert _max_loss([Leg("CE", +1)], [10000], 80.0) == pytest.approx(80.0)      # long call: the premium
    assert math.isinf(_max_loss([Leg("CE", -1), Leg("PE", -1)], [10200, 9800], -150.0))
    condor = [Leg("CE", -1), Leg("CE", +1), Leg("PE", -1), Leg("PE", +1)]
    assert _max_loss(condor, [10200, 10400, 9800, 9600], -90.0) == pytest.approx(110.0)


def test_long_call_held_to_expiry_pays_intrinsic_less_premium():
    spots = [10000.0] * 6 + [10400.0] * 6                 # Wed 1 Jan 2020 start; Thursdays are expiries
    fo = chain(spots)
    plan = OptionPlan("NIFTY", [[Leg("CE", +1, "atm")]], dte=4, risk_frac=1.0)
    res = simulate_options(plan, fo, cfg())
    t = res.trades.iloc[0]
    entry = pd.Timestamp("2020-01-03")                    # four sessions before Thursday 9 Jan
    assert t.entry_date == entry and t.exit_date == pd.Timestamp("2020-01-09") and t.reason == "expiry"
    premium = bs(10000, 10000, 6 / 365, 0.2, "CE")
    mult = 1_000_000 / 10000
    lots = int(0.9 * 150_000 // (premium * mult))
    assert t.pnl == pytest.approx((400.0 - premium) * mult * lots)


def test_credit_spread_sizing_and_loss_is_capped():
    spots = [10000.0] * 3 + [9000.0] * 9                  # crash through both strikes
    fo = chain(spots)
    legs = [Leg("PE", -1, "pct", 0.02), Leg("PE", +1, "pct", 0.04)]
    plan = OptionPlan("NIFTY", [legs], dte=4, risk_frac=0.10)
    res = simulate_options(plan, fo, cfg(lot_notional=300_000.0))
    t = res.trades.iloc[0]
    credit = bs(10000, 9800, 6 / 365, 0.2, "PE") - bs(10000, 9600, 6 / 365, 0.2, "PE")
    risk_per_lot = (200 - credit) * 30
    lots = int(0.10 * 150_000 // risk_per_lot)
    assert lots >= 1
    assert t.pnl == pytest.approx(-risk_per_lot * lots)
    assert res.equity.min() >= 150_000 * (1 - 0.10) - 1


def test_naked_strangle_is_unaffordable_at_small_capital():
    fo = chain([10000.0] * 12)
    legs = [Leg("CE", -1, "pct", 0.03), Leg("PE", -1, "pct", 0.03)]
    res = simulate_options(OptionPlan("NIFTY", [legs], dte=4, risk_frac=1.0), fo,
                           cfg(lot_notional=1_650_000.0))
    assert res.orders == 0 and res.skipped["unaffordable"] >= 1
    rich = simulate_options(OptionPlan("NIFTY", [legs], dte=4, risk_frac=1.0), fo,
                            cfg(lot_notional=1_650_000.0, capital=1_000_000.0))
    assert rich.orders > 0 and (rich.trades.pnl > 0).all()        # flat market: premium kept


def test_stop_exits_on_daily_mark_and_signal_is_lagged():
    spots = [10000.0] * 3 + [10000.0, 9700.0, 9700.0] + [9700.0] * 6
    fo = chain(spots)
    legs = [Leg("PE", -1, "pct", 0.02), Leg("PE", +1, "pct", 0.06)]
    small = cfg(lot_notional=300_000.0)
    res = simulate_options(OptionPlan("NIFTY", [legs], dte=4, stop_mult=1.0, risk_frac=0.2), fo, small)
    assert res.trades.reason.iloc[0] == "stop" and res.trades.exit_date.iloc[0] == pd.Timestamp("2020-01-07")
    dates = pd.DatetimeIndex(sorted(fo.date.unique()))
    sig = pd.Series(0.0, index=dates)
    sig.loc["2020-01-03"] = 1.0                           # same-day signal must not trigger the 3 Jan entry
    none = simulate_options(OptionPlan("NIFTY", [legs], dte=4, entry_signal=sig, risk_frac=0.2),
                            fo, small, end="2020-01-09")
    assert none.orders == 0
    sig.loc["2020-01-02"] = 1.0
    some = simulate_options(OptionPlan("NIFTY", [legs], dte=4, entry_signal=sig, risk_frac=0.2),
                            fo, small, end="2020-01-09")
    assert some.orders == 2


def test_costs_and_slippage_reduce_profit():
    fo = chain([10000.0] * 12)
    legs = [Leg("PE", -1, "pct", 0.02), Leg("PE", +1, "pct", 0.04)]
    plan = OptionPlan("NIFTY", [legs], dte=4, risk_frac=0.2)
    free = simulate_options(plan, fo, cfg(lot_notional=300_000.0))
    real = simulate_options(plan, fo, OptionSimConfig(lot_notional=300_000.0, liquid_yield=0.0))
    assert real.costs > 0 and real.equity.iloc[-1] < free.equity.iloc[-1]
    assert free.equity.iloc[-1] - real.equity.iloc[-1] == pytest.approx(real.costs, rel=0.05)
