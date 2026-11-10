import numpy as np
import pandas as pd
import pytest

from quant.engine import CostModel, Ctx, Plan, SimConfig, Spec, check_lookahead, simulate
from quant.engine import harness
from quant.engine.harness import evaluate
from quant.engine.metrics import deflated_sharpe, expected_max_sharpe, probabilistic_sharpe, stats
from quant.engine.testing import make_market, synthetic_market

FREE = CostModel(segments={k: type(v)(0, 0, 0, 0, 0, 0, 0, 0) for k, v in CostModel().segments.items()},
                 sebi=0, ipft=0, gst=0, slippage_tiers=((10**9, 0.0),), slippage_unranked=0.0)


def cfg(**kw):
    base = dict(capital=100_000.0, costs=FREE, liquid_yield=0.0, cash_buffer=0.0, min_order_value=0.0)
    base.update(kw)
    return SimConfig(**base)


def frame(values, cols=("A",), start="2020-01-01"):
    idx = pd.bdate_range(start, periods=len(values))
    return pd.DataFrame(np.array(values, dtype=float).reshape(len(values), -1), idx, list(cols))


def flat_market(prices, days=None, **kw):
    """One symbol 'A'; liquidity rank needs history, so pad the front."""
    pad = 70
    close = frame([prices[0]] * pad + list(prices))
    return make_market(close, **kw), close.index[pad:]


# --- costs ----------------------------------------------------------------
def test_delivery_charges_match_hand_calculation():
    c = CostModel()
    v = 10_000.0
    brokerage = 10.0                                   # 0.1% of 10,000, under the Rs 20 cap
    fees = (brokerage + v * 0.0000297 + v * 0.000002) * 1.18
    assert c.charges("delivery", "buy", v) == pytest.approx(fees + v * (0.001 + 0.00015))
    assert c.charges("delivery", "sell", v) == pytest.approx(fees + v * 0.001 + 20 * 1.18)


def test_flat_fees_hurt_small_orders_more():
    c = CostModel()
    assert c.round_trip_rate("delivery", 5_000) > c.round_trip_rate("delivery", 50_000)
    assert c.charges("delivery", "buy", 1_000_000) < 1_000_000 * 0.0013      # brokerage capped at Rs 20
    assert c.charges("intraday", "buy", 100.0) >= 5.0                        # minimum brokerage


def test_slippage_grows_as_liquidity_falls():
    c = CostModel()
    r = [c.slippage(10_000, k) for k in (10, 100, 300, 800, 5000, float("nan"))]
    assert r == sorted(r) and r[-1] == r[-2]


# --- timing: no look-ahead in fills ----------------------------------------
def test_decision_at_close_fills_next_open():
    m, d = flat_market([100, 100, 100, 200, 200])
    open_ = m.close.shift(1).fillna(100.0)
    open_.loc[d[3]] = 150.0                            # gap up on day 3
    m, _ = flat_market([100, 100, 100, 200, 200], open_=open_)
    w = pd.DataFrame({"A": [1.0]}, index=[d[1]])       # decided at the close of day 1
    res = simulate(Plan(w), m, cfg(), start=d[0])
    assert res.equity.loc[d[1]] == pytest.approx(100_000)          # nothing held yet
    assert res.equity.loc[d[2]] == pytest.approx(100_000)          # bought at day-2 open of 100
    assert res.equity.loc[d[3]] == pytest.approx(200_000)


def test_fill_at_next_close_and_decide_at_open():
    m, d = flat_market([100, 110, 120, 130, 140])
    w = pd.DataFrame({"A": [1.0]}, index=[d[0]])
    late = simulate(Plan(w, fill="close"), m, cfg(), start=d[0])
    assert late.equity.loc[d[1]] == pytest.approx(100_000)         # bought at the close of day 1
    assert late.equity.loc[d[2]] == pytest.approx(100_000 + 909 * 10)
    w2 = pd.DataFrame({"A": [1.0]}, index=[d[2]])
    early = simulate(Plan(w2, decide_at="open"), m, cfg(), start=d[0])
    # open of day 2 equals the close of day 1 (110): 909 shares, marked at 120
    assert early.equity.loc[d[2]] == pytest.approx(100_000 + 909 * 10)


# --- whole shares, real prices, corporate actions ---------------------------
def test_whole_shares_and_unaffordable_names():
    m, d = flat_market([3000, 3000, 3300])
    w = pd.DataFrame({"A": [1.0]}, index=[d[0]])
    res = simulate(Plan(w), m, cfg(capital=10_000), start=d[0])
    assert res.equity.loc[d[2]] == pytest.approx(10_000 + 3 * 300)   # 3 shares, not 3.33
    res = simulate(Plan(w), m, cfg(capital=2_000), start=d[0])
    assert res.orders == 0 and res.skipped["unaffordable"] == 1


def test_split_does_not_change_value_and_sizes_use_quoted_price():
    # quoted 1000 before a 2:1 split, 500 after; adjusted price is 500 throughout
    close = frame([500.0] * 75)
    factor = close * 0 + 1.0
    factor.iloc[:72] = 0.5
    m = make_market(close, factor=factor)
    d = close.index[70:]
    w = pd.DataFrame({"A": [1.0]}, index=[d[0]])
    res = simulate(Plan(w), m, cfg(capital=10_500), start=d[0])
    assert res.traded_value == pytest.approx(10_000)      # 10 shares at the quoted 1000
    assert res.equity.iloc[-1] == pytest.approx(10_500)   # value unchanged through the split
    w_exit = pd.DataFrame({"A": [1.0, 0.0]}, index=[d[0], d[3]])
    res = simulate(Plan(w_exit), m, cfg(capital=10_500), start=d[0])
    assert res.traded_value == pytest.approx(20_000)      # sold 20 shares at 500
    assert len(res.trades) == 1 and res.trades.pnl.iloc[0] == pytest.approx(0.0)


def test_costs_reduce_equity_by_exact_charges():
    m, d = flat_market([100, 100, 100, 100])
    w = pd.DataFrame({"A": [0.5, 0.0]}, index=[d[0], d[1]])
    c = SimConfig(capital=100_000, liquid_yield=0.0)
    res = simulate(Plan(w), m, c, start=d[0])
    shares = int(100_000 * (1 - c.cash_buffer) * 0.5 // 100)
    v = shares * 100.0
    expected = (c.costs.charges("delivery", "buy", v) + c.costs.charges("delivery", "sell", v)
                + 2 * c.costs.slippage(v, 1))
    assert res.costs == pytest.approx(expected)
    assert res.equity.iloc[-1] == pytest.approx(100_000 - expected)


def test_no_shorting_and_no_leverage_in_delivery():
    m, d = flat_market([100, 100, 50])
    res = simulate(Plan(pd.DataFrame({"A": [-1.0]}, index=[d[0]])), m, cfg(), start=d[0])
    assert res.orders == 0
    res = simulate(Plan(pd.DataFrame({"A": [3.0]}, index=[d[0]])), m, cfg(), start=d[0])
    assert res.exposure.max() <= 1.0 + 1e-9


# --- exits ------------------------------------------------------------------
def test_stop_loss_fills_at_stop_or_at_gap_open():
    close = frame([100.0] * 72 + [100, 96, 80])
    low = close.copy(); low.iloc[73] = 94.0
    m = make_market(close, low=low)
    d = close.index[70:]
    w = pd.DataFrame({"A": [1.0]}, index=[d[0]])
    res = simulate(Plan(w, stop_loss=0.05), m, cfg(), start=d[0])
    assert res.trades.reason.tolist() == ["stop"]
    assert res.equity.iloc[-1] == pytest.approx(95_000)            # out at 95, not at the low
    # gap: opens far below the stop, so the fill is the open
    open_ = close.shift(1).fillna(100.0); open_.iloc[73] = 90.0
    low2 = close.copy(); low2.iloc[73] = 88.0
    m2 = make_market(close, open_=open_, low=low2)
    res = simulate(Plan(w, stop_loss=0.05), m2, cfg(), start=d[0])
    assert res.equity.iloc[-1] == pytest.approx(90_000)


def test_stopped_position_stays_out_until_plan_resets():
    close = frame([100.0] * 72 + [100, 90, 100, 100, 100, 100])
    m = make_market(close)
    d = close.index[70:]
    w = pd.DataFrame({"A": [1.0] * 6}, index=d[:6])
    res = simulate(Plan(w, stop_loss=0.05), m, cfg(), start=d[0])
    assert len(res.trades) == 1 and res.exposure.iloc[-1] == 0
    w.iloc[4] = 0.0                                                # plan drops the name, then re-adds
    res = simulate(Plan(w, stop_loss=0.05), m, cfg(), start=d[0])
    assert res.exposure.iloc[-1] > 0.9


def test_stop_beats_target_when_both_hit_same_day():
    close = frame([100.0] * 72 + [100, 100])
    high = close.copy(); low = close.copy()
    high.iloc[73], low.iloc[73] = 120.0, 80.0
    m = make_market(close, high=high, low=low)
    d = close.index[70:]
    res = simulate(Plan(pd.DataFrame({"A": [1.0]}, index=[d[0]]), stop_loss=0.1, take_profit=0.1),
                   m, cfg(), start=d[0])
    assert res.trades.reason.tolist() == ["stop"]


def test_max_hold_and_trailing_stop():
    m, d = flat_market([100, 100, 110, 120, 130, 140])
    w = pd.DataFrame({"A": [1.0]}, index=[d[0]])
    res = simulate(Plan(w, max_hold=2), m, cfg(), start=d[0])
    assert res.trades.reason.tolist() == ["time"] and res.trades.exit_date.iloc[0] == d[2]
    m, d = flat_market([100, 100, 150, 120, 120])
    res = simulate(Plan(w, trailing_stop=0.1), m, cfg(), start=d[0])
    assert res.trades.reason.tolist() == ["stop"]
    assert res.equity.iloc[-1] == pytest.approx(100_000 * 1.35)    # out at 135 = 150 less 10%


def test_vanished_stock_is_written_down():
    prices = [100.0] * 75 + [np.nan] * 30
    close = frame(prices + [np.nan], cols=("A",))
    other = frame([50.0] * len(close), cols=("B",))
    m = make_market(pd.concat([close, other], axis=1))
    d = m.dates[70:]
    res = simulate(Plan(pd.DataFrame({"A": [1.0]}, index=[d[0]])), m, cfg(), start=d[0])
    assert res.trades.reason.tolist() == ["written_down"]
    assert res.equity.iloc[-1] == pytest.approx(80_000)


# --- intraday ---------------------------------------------------------------
def test_intraday_long_short_stop_and_flat_overnight():
    close = frame([[100.0, 100.0]] * 72 + [[110, 90], [120, 80]], cols=("A", "B"))
    m = make_market(close)
    d = close.index[70:]
    w = pd.DataFrame({"A": [1.0, 1.0], "B": [-1.0, -1.0]}, index=d[2:4])
    res = simulate(Plan(w, mode="intraday", decide_at="open"), m, cfg(), start=d[0])
    # day 2: A 100 -> 110 long (+10%), B 100 -> 90 short (+10%), each on 100% of equity
    assert res.equity.loc[d[2]] == pytest.approx(120_000)
    assert res.equity.loc[d[3]] > res.equity.loc[d[2]]
    assert (res.trades.entry_date == res.trades.exit_date).all()
    stopped = simulate(Plan(w.assign(A=-1.0), mode="intraday", decide_at="open", stop_loss=0.02),
                       m, cfg(), start=d[0])
    assert "stop" in stopped.trades.reason.tolist()                # short A stopped out 2% above the open


def test_intraday_leverage_is_capped():
    close = frame([100.0] * 72 + [110.0])
    m = make_market(close)
    d = close.index[70:]
    w = pd.DataFrame({"A": [50.0]}, index=[d[2]])
    res = simulate(Plan(w, mode="intraday", decide_at="open"), m, cfg(), start=d[0])
    assert res.exposure.max() <= 5.0 + 1e-9
    assert res.equity.iloc[-1] == pytest.approx(100_000 * 1.5)


# --- look-ahead check and protocol -------------------------------------------
def test_lookahead_check_catches_a_cheat_and_passes_honest_code():
    m = synthetic_market(days=500, symbols=12)
    ctx = Ctx(m)

    def honest(ctx, n=20):
        mom = ctx.market.close.pct_change(n)
        return Plan(mom.rank(axis=1, ascending=False).le(3).astype(float) / 3)

    def cheat(ctx, n=20):
        fut = ctx.market.close.shift(-1) / ctx.market.close - 1      # tomorrow's return
        return Plan(fut.rank(axis=1, ascending=False).le(3).astype(float) / 3)

    def full_sample(ctx, n=20):
        z = (ctx.market.close - ctx.market.close.mean()) / ctx.market.close.std()   # uses the whole history
        return Plan(z.rank(axis=1).le(3).astype(float) / 3)

    def open_gap(ctx):
        gap = ctx.market.open / ctx.market.close.shift(1) - 1
        return Plan(gap.rank(axis=1).le(2).astype(float), mode="intraday", decide_at="open")

    def open_cheat(ctx):
        day = ctx.market.close / ctx.market.open - 1                  # needs today's close at the open
        return Plan(day.rank(axis=1, ascending=False).le(2).astype(float), mode="intraday", decide_at="open")

    assert check_lookahead(Spec("h", "t", honest), ctx) == []
    assert check_lookahead(Spec("c", "t", cheat), ctx)
    assert check_lookahead(Spec("f", "t", full_sample), ctx)
    assert check_lookahead(Spec("g", "t", open_gap), ctx) == []
    assert check_lookahead(Spec("o", "t", open_cheat), ctx)


def test_evaluate_picks_parameters_on_train_only(monkeypatch):
    m = synthetic_market(days=900, symbols=12, start="2012-01-02")
    ctx = Ctx(m)
    monkeypatch.setitem(harness.WINDOWS, "daily",
                        {"train": ("2012-06-01", "2013-12-31"), "valid": ("2014-01-01", "2015-06-01")})

    def mom(ctx, n=20, top=3):
        r = ctx.market.close.pct_change(n)
        return Plan(r.rank(axis=1, ascending=False).le(top).astype(float) / top, band=0.05)

    out = evaluate(Spec("m", "t", mom, {"n": [20, 60], "top": [3, 5]}), ctx, SimConfig(), save=False)
    assert out["n_trials"] == 4 and out["lookahead_problems"] == []
    best_train = max(t["train"]["sharpe"] for t in out["trials"])
    assert out["chosen"]["train"]["sharpe"] == best_train


# --- statistics ---------------------------------------------------------------
def test_stats_basic_numbers():
    m, d = flat_market([100.0] * 300)
    res = simulate(Plan(pd.DataFrame({"A": [0.0]}, index=[d[0]])), m,
                   SimConfig(capital=100_000, liquid_yield=0.05), start=d[0])
    s = stats(res, 100_000)
    assert s["cagr"] == pytest.approx(0.0513, abs=0.002)            # idle cash earns the liquid yield
    assert s["max_drawdown"] == 0 and s["orders"] == 0


def test_deflated_sharpe_penalises_many_trials():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0.0012, 0.01, 1500))
    one = deflated_sharpe(r, 1, 0.05, rf=0.0)
    many = deflated_sharpe(r, 500, 0.05, rf=0.0)
    assert one > many and 0 <= many <= 1
    assert expected_max_sharpe(500, 0.05) > expected_max_sharpe(10, 0.05) > 0
    assert probabilistic_sharpe(0.0, 1000, 0, 3) == pytest.approx(0.5)
