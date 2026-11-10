import numpy as np
import pandas as pd
import pytest

from quant.engine.costs import CostModel
from quant.intraday import (IntradayPlan, IntradaySimConfig, check_lookahead_intraday, events, minute,
                            simulate_intraday)
from quant.intraday import features as F
from quant.intraday.grid import MINUTES, bars_to_grid, ictx_from_grids, session_days
from quant.intraday.testing import flat_grid, set_bar, synthetic_grids

FREE = CostModel(segments={k: type(v)(0, 0, 0, 0, 0, 0, 0, 0) for k, v in CostModel().segments.items()},
                 sebi=0, ipft=0, gst=0, slippage_tiers=((10**9, 0.0),), slippage_unranked=0.0)


def cfg(**kw):
    base = dict(capital=100_000.0, costs=FREE, stop_extra_slip=0.0, open_slip_mult=1.0, min_order_value=0.0)
    base.update(kw)
    return IntradaySimConfig(**base)


def one_entry(g, day=1, col=10, side=1, stop=np.nan, target=np.nan):
    e = np.zeros(g.close.shape, dtype=np.int8)
    e[day, col] = side
    s = np.full(g.close.shape, np.nan); s[day, col] = stop
    t = np.full(g.close.shape, np.nan); t[day, col] = target
    return events(e, s, t)


def run(g, sig, plan_kw=None, cfg_kw=None, extra=None):
    grids = {"A": g, **(extra or {})}
    ctx = ictx_from_grids(grids)
    kw = dict(risk_per_trade=0.01, max_notional=1.0)
    kw.update(plan_kw or {})
    plan = IntradayPlan(sig if isinstance(sig, dict) else {"A": sig}, **kw)
    return simulate_intraday(plan, ctx, cfg(**(cfg_kw or {})))


def test_minute_helpers_and_grid_building():
    assert minute("09:15") == 0 and minute("09:30") == 15 and minute("15:29") == MINUTES - 1
    ts = pd.date_range("2022-01-03 09:15", periods=375, freq="min").append(
        pd.date_range("2022-01-04 18:15", periods=60, freq="min"))      # an evening special session
    bars = pd.DataFrame({"ts": ts, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10})
    days = session_days(bars)
    assert list(days) == [pd.Timestamp("2022-01-03")]
    g = bars_to_grid(bars, days)
    assert g.close.shape == (1, MINUTES) and np.isfinite(g.close).all()


def test_signal_fills_next_minute_open_and_squares_off():
    g = flat_grid()
    set_bar(g, 1, 11, o=101.0)                       # the fill bar opens at 101, not at the signal bar's 100
    g.open[1, minute("15:15")] = 111.0
    res = run(g, one_entry(g, col=10), {"risk_per_trade": 1.0})
    t = res.trades.iloc[0]
    assert (t.entry_col, t.entry_px, t.reason, t.exit_px) == (11, 101.0, "time", 111.0)
    assert t.qty == 100_000 // 101 and res.equity.iloc[1] == pytest.approx(100_000 + t.qty * 10)
    assert res.equity.iloc[0] == 100_000 and res.equity.iloc[2] == res.equity.iloc[1]


def test_stop_fill_gap_fill_and_stop_before_target():
    g = flat_grid()
    set_bar(g, 1, 50, o=100, l=97.5, c=98)
    res = run(g, one_entry(g, stop=98.0))
    assert res.trades.reason.iloc[0] == "stop" and res.trades.exit_px.iloc[0] == 98.0
    g = flat_grid()
    set_bar(g, 1, 50, o=95.0)                        # opens far through the stop
    res = run(g, one_entry(g, stop=98.0))
    assert res.trades.exit_px.iloc[0] == 95.0
    g = flat_grid()
    set_bar(g, 1, 50, o=100, h=104, l=97, c=100)     # touches both
    res = run(g, one_entry(g, stop=98.0, target=103.0))
    assert res.trades.reason.iloc[0] == "stop"


def test_risk_sizing_target_multiple_and_caps():
    g = flat_grid(volume=1e6)
    set_bar(g, 1, 80, o=100, h=104.5, c=104)
    res = run(g, one_entry(g, stop=98.0), {"target_r": 2.0, "risk_per_trade": 0.01, "max_notional": 5.0})
    t = res.trades.iloc[0]
    assert t.qty == 500                               # 1% of 100,000 = 1,000 at risk; 2 per share
    assert t.reason == "target" and t.exit_px == 104.0 and t.pnl == pytest.approx(2_000)
    res = run(g, one_entry(g, stop=99.9), {"risk_per_trade": 0.01, "max_notional": 1.0})
    assert res.trades.qty.iloc[0] == 1_000            # capped at one times equity
    res = run(g, one_entry(g, stop=99.99), {"risk_per_trade": 0.05, "max_notional": 50.0})
    assert res.trades.qty.iloc[0] == 5_000 and res.exposure.max() == pytest.approx(5.0)   # broker leverage
    thin = flat_grid(volume=2_000.0)
    res = run(thin, one_entry(thin, stop=99.0), {"risk_per_trade": 0.01})
    assert res.trades.qty.iloc[0] == 200              # at most a tenth of the entry bar's volume


def test_short_needs_liquid_name_and_profits_from_fall():
    g = flat_grid()
    g.open[1, minute("15:15")] = 90.0
    sig = one_entry(g, side=-1, stop=102.0)
    ctx = ictx_from_grids({"A": g}, ranks={"A": 400})
    plan = IntradayPlan({"A": sig}, risk_per_trade=0.01)
    assert simulate_intraday(plan, ctx, cfg()).orders == 0
    ctx = ictx_from_grids({"A": g}, ranks={"A": 20})
    res = simulate_intraday(plan, ctx, cfg())
    assert res.trades.pnl.iloc[0] == pytest.approx(500 * 10)


def test_daily_loss_limit_and_position_limit():
    grids = {s: flat_grid() for s in "ABCD"}
    sigs = {}
    for k, s in enumerate("ABCD"):
        set_bar(grids[s], 1, 20 + 10 * k + 2, o=100, l=97, c=98)        # each stops out soon after entry
        sigs[s] = one_entry(grids[s], col=20 + 10 * k, stop=98.0)
    ctx = ictx_from_grids(grids)
    plan = IntradayPlan(sigs, risk_per_trade=0.01, daily_loss_limit=0.015, max_positions=4)
    res = simulate_intraday(plan, ctx, cfg())
    assert len(res.trades) == 2 and res.skipped["loss_limit"] == 2      # two 1% losses breach 1.5%
    # all four enter at once, none exit early: only max_positions are taken
    grids = {s: flat_grid() for s in "ABCD"}
    sigs = {s: one_entry(grids[s], col=20, stop=98.0) for s in "ABCD"}
    plan = IntradayPlan(sigs, risk_per_trade=0.002, max_positions=3)
    res = simulate_intraday(plan, ictx_from_grids(grids), cfg())
    assert len(res.trades) == 3 and res.skipped["max_positions"] == 1


def test_one_trade_per_symbol_and_entry_window():
    g = flat_grid()
    e = np.zeros(g.close.shape, dtype=np.int8)
    e[1, [5, 30, 200, 350]] = 1
    res = run(g, events(e), {"stop_pct": 0.02, "entry_from": 10, "entry_until": 300})
    assert len(res.trades) == 1 and res.trades.entry_col.iloc[0] == 31
    res = run(g, events(e), {"stop_pct": 0.02, "trades_per_symbol": 3, "entry_from": 0, "entry_until": 300})
    assert len(res.trades) == 1                      # still holding the first until square-off


def test_costs_match_schedule():
    g = flat_grid()
    res = run(g, one_entry(g, stop=98.0), cfg_kw={"costs": CostModel(), "stop_extra_slip": 0.0, "open_slip_mult": 1.0})
    v = 500 * 100.0
    c = CostModel()
    expected = c.charges("intraday", "buy", v) + c.charges("intraday", "sell", v) + 2 * c.slippage(v, 1)
    assert res.costs == pytest.approx(expected) and res.trades.pnl.iloc[0] == pytest.approx(-expected)


def test_features_do_not_depend_on_later_bars():
    g = synthetic_grids(days=30, symbols=1)["S00"]
    di, col = 20, 137
    cut = g.cut(di, col)
    for name, fn in [("vwap", F.vwap), ("relative_volume", F.relative_volume), ("cum_high", F.cum_high),
                     ("cum_low", F.cum_low), ("last_price", F.last_price), ("returns_since_open", F.returns_since_open)]:
        a, b = fn(g), fn(cut)
        np.testing.assert_allclose(a[di, :col + 1], b[di, :col + 1], rtol=1e-5, err_msg=name)
        np.testing.assert_allclose(a[:di], b[:di], rtol=1e-5, err_msg=name)
    for name, fn in [("gap", F.gap), ("prev_close", F.prev_close), ("daily_range_avg", F.daily_range_avg),
                     ("day_open", F.day_open)]:
        np.testing.assert_allclose(fn(g)[: di + 1], fn(cut)[: di + 1], rtol=1e-5, err_msg=name)
    hi, lo = F.opening_range(g, 15)
    assert hi[3] == pytest.approx(g.high[3, :15].max()) and lo[3] == pytest.approx(g.low[3, :15].min())


def test_lookahead_check_on_bars():
    ctx = ictx_from_grids(synthetic_grids(days=40, symbols=6))

    def orb(ctx, minutes=15):
        out = {}
        for s in ctx.symbols:
            g = ctx.grid(s)
            hi, lo = F.opening_range(g, minutes)
            px = F.last_price(g)
            brk = (px > hi[:, None]) & (np.arange(MINUTES)[None, :] >= minutes)
            first = brk & (np.cumsum(brk, axis=1) == 1)
            out[s] = events(first.astype(np.int8), stop=lo)
        return IntradayPlan(out, target_r=2.0)

    def cheat_day_high(ctx):
        out = {}
        for s in ctx.symbols:
            g = ctx.grid(s)
            top = np.nanmax(g.high, axis=1)                       # the day's final high
            e = (g.close < top[:, None] * 0.995) & (np.arange(MINUTES)[None, :] == 30)
            out[s] = events(e.astype(np.int8))
        return IntradayPlan(out, stop_pct=0.01)

    def cheat_next_bar(ctx):
        out = {}
        for s in ctx.symbols:
            g = ctx.grid(s)
            nxt = np.roll(g.close, -1, axis=1)
            e = (nxt > g.close * 1.001) & (np.arange(MINUTES)[None, :] % 60 == 7)
            out[s] = events(e.astype(np.int8))
        return IntradayPlan(out, stop_pct=0.01, trades_per_symbol=5)

    assert check_lookahead_intraday(orb, ctx) == []
    assert check_lookahead_intraday(cheat_day_high, ctx)
    assert check_lookahead_intraday(cheat_next_bar, ctx)
