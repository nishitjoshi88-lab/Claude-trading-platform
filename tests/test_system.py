import json

import numpy as np
import pandas as pd
import pytest

from trader.backtest import run
from trader.config import Config, CostConfig
from trader.core import Trader
from trader.live import Runner
from trader.market import PERP, SPOT, Panel, synthetic_frames
from trader.portfolio import Portfolio
from trader.risk import RiskGovernor
from trader.strategies import Carry, Context, Reversion, Strategy, Trend

SYMS = ["AAA", "BBB", "CCC"]


def flat_panel(bars=400, price=100.0, funding8h=0.0, perp=None):
    idx = pd.date_range("2024-01-01", periods=bars, freq="h")
    f = np.where(idx.hour % 8 == 0, funding8h, 0.0)
    frames = {s: pd.DataFrame({"spot": price, "perp": perp if perp is not None else price,
                               "funding": f}, index=idx) for s in SYMS}
    return Panel.from_frames(frames)


class Hold(Strategy):
    """Test strategy: always wants a fixed perp quantity in the first symbol."""
    name = "trend"

    def __init__(self, qty):
        super().__init__()
        self.q = qty

    def target(self, view, cur, ctx):
        out = np.zeros_like(cur)
        out[PERP, 0] = self.q
        return out


# --- accounting -----------------------------------------------------------
def test_portfolio_pnl_fees_and_funding():
    pf = Portfolio(["s"], 1, 1000.0, CostConfig(spot_fee=0.001, perp_fee=0.0005, slippage=0.0))
    pf.mark(np.array([[100.0], [100.0]]))
    pf.trade("s", np.array([[1.0], [-1.0]]))            # long spot, short perp
    assert pf.pnl["s"] == pytest.approx(-(0.1 + 0.05))
    pf.mark(np.array([[110.0], [110.0]]))               # hedged: no price pnl
    assert pf.pnl["s"] == pytest.approx(-0.15)
    pf.settle_funding(np.array([0.001]))                # short receives 110 * 0.001
    assert pf.pnl["s"] == pytest.approx(-0.15 + 0.11)
    assert pf.gross() == pytest.approx(220.0)


def test_missing_price_does_not_create_pnl():
    pf = Portfolio(["s"], 1, 1000.0, CostConfig(0, 0, 0))
    pf.mark(np.array([[100.0], [100.0]]))
    pf.trade("s", np.array([[0.0], [1.0]]))
    pf.mark(np.array([[np.nan], [np.nan]]))
    assert pf.pnl["s"] == 0
    pf.mark(np.array([[100.0], [105.0]]))
    assert pf.pnl["s"] == pytest.approx(5.0)


# --- no lookahead ---------------------------------------------------------
def test_backtest_fills_on_next_bar():
    idx = pd.date_range("2024-01-01", periods=4, freq="h")
    px = [100.0, 100.0, 200.0, 200.0]
    frames = {"AAA": pd.DataFrame({"spot": px, "perp": px, "funding": 0.0}, index=idx)}
    cfg = Config(symbols=["AAA"], costs=CostConfig(0, 0, 0), allocations={"trend": 1.0})
    res = run(cfg, Panel.from_frames(frames), [Hold(1.0)])
    # decided at bar 0, filled at bar 1 (price 100), so the jump to 200 earns 100
    assert res.equity.iloc[1] == pytest.approx(10_000)
    assert res.equity.iloc[2] == pytest.approx(10_100)


def test_strategies_ignore_future_data():
    frames = synthetic_frames(SYMS, bars=1500, seed=3)
    full = Panel.from_frames(frames)
    cut = Panel.from_frames({s: f.iloc[:1201] for s, f in frames.items()})
    ctx = Context(5000, 10_000, 0.01)
    cur = np.zeros((2, 3))
    for make in (Carry, Trend, Reversion):
        a = make().target(full.view(1200), cur, ctx)
        b = make().target(cut.view(1200), cur, ctx)
        np.testing.assert_allclose(a, b)


# --- strategies -----------------------------------------------------------
def test_carry_enters_hedged_and_earns_funding():
    panel = flat_panel(bars=24 * 40, funding8h=0.0003)        # about 33% a year
    cfg = Config(symbols=SYMS, allocations={"carry": 0.6})
    res = run(cfg, panel, [Carry()])
    assert res.strategy_pnl["carry"].iloc[-1] > 0
    t = Trader(cfg, 3, [Carry()])
    for i in range(24 * 8):
        t.step(panel.view(i))
    q = t.portfolio.qty["carry"]
    assert (q[SPOT] > 0).all()
    np.testing.assert_allclose(q[SPOT], -q[PERP])            # market neutral


def test_carry_stays_out_when_funding_is_low_and_exits_when_it_drops():
    assert run(Config(symbols=SYMS), flat_panel(funding8h=0.00002), [Carry()]).trades == 0
    idx = pd.date_range("2024-01-01", periods=24 * 30, freq="h")
    f = np.where(idx.hour % 8 == 0, 0.0003, 0.0)
    f[24 * 15:] = 0.0
    frames = {s: pd.DataFrame({"spot": 100.0, "perp": 100.0, "funding": f}, index=idx) for s in SYMS}
    cfg = Config(symbols=SYMS)
    t = Trader(cfg, 3, [Carry()])
    panel = Panel.from_frames(frames)
    for i in range(len(panel)):
        t.step(panel.view(i))
    assert not t.portfolio.qty["carry"].any()


def test_trend_goes_long_in_uptrend_short_in_downtrend():
    idx = pd.date_range("2024-01-01", periods=24 * 25, freq="h")
    rng = np.random.default_rng(0)
    noise = np.exp(rng.normal(0, 0.003, len(idx)))
    up = 100 * np.exp(np.arange(len(idx)) * 0.0005) * noise
    down = 100 * np.exp(-np.arange(len(idx)) * 0.0005) * noise
    frames = {"UP": pd.DataFrame({"spot": up, "perp": up, "funding": 0.0}, index=idx),
              "DOWN": pd.DataFrame({"spot": down, "perp": down, "funding": 0.0}, index=idx)}
    panel = Panel.from_frames(frames)
    tgt = Trend().target(panel.view(len(panel) - 1), np.zeros((2, 2)), Context(2500, 10_000, 0.01))
    assert tgt[PERP, 0] > 0 > tgt[PERP, 1]
    assert not tgt[SPOT].any()


def test_reversion_buys_crash_sizes_by_risk_and_times_out():
    idx = pd.date_range("2024-01-01", periods=24 * 40, freq="h")
    rng = np.random.default_rng(1)
    px = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, len(idx))))
    px[-60:] *= 0.85                                          # sudden 15% drop
    frames = {"AAA": pd.DataFrame({"spot": px, "perp": px, "funding": 0.0}, index=idx)}
    panel = Panel.from_frames(frames)
    strat, ctx = Reversion(), Context(1500, 10_000, 0.01)
    i0 = len(panel) - 60
    tgt = strat.target(panel.view(i0), np.zeros((2, 1)), ctx)
    assert tgt[PERP, 0] > 0
    e = strat.state["AAA"]
    assert e["qty"] * e["px"] * e["stop"] <= 0.01 * 10_000 + 1e-6   # at most 1% of equity at risk
    cur = tgt
    for i in range(i0 + 1, len(panel)):
        cur = strat.target(panel.view(i), cur, ctx)
    assert not cur.any() and not strat.state                 # exited by time limit


# --- risk governor --------------------------------------------------------
def test_leverage_and_position_caps():
    panel = flat_panel(bars=5)
    cfg = Config(symbols=SYMS, costs=CostConfig(0, 0, 0), allocations={"trend": 1.0})
    t = Trader(cfg, 3, [Hold(1000.0)])                        # wants 100,000 of exposure
    t.step(panel.view(0)); t.step(panel.view(1))
    assert t.portfolio.gross() <= cfg.risk.max_position_frac * 10_000 + 1e-6


def test_daily_loss_halt_flattens_directional_books():
    idx = pd.date_range("2024-01-01", periods=30, freq="h")
    px = np.full(30, 100.0); px[3:] = 80.0                    # 20% drop on a 30-unit long
    frames = {"AAA": pd.DataFrame({"spot": px, "perp": px, "funding": 0.0}, index=idx)}
    cfg = Config(symbols=["AAA"], costs=CostConfig(0, 0, 0), allocations={"trend": 1.0})
    t = Trader(cfg, 1, [Hold(30.0)])
    panel = Panel.from_frames(frames)
    for i in range(6):
        t.step(panel.view(i))
    assert t.risk.halted() and not t.portfolio.qty["trend"].any()
    for i in range(6, 30):                                    # next UTC day: trading resumes
        t.step(panel.view(i))
    assert t.portfolio.qty["trend"][PERP, 0] > 0


def test_drawdown_kill_is_permanent_until_reset():
    r = RiskGovernor(Config().risk, ["a"])
    ts = pd.Timestamp("2024-01-01")
    r.update(ts, 10_000, {"a": 0.0}, {"a": 10_000})
    r.update(ts + pd.Timedelta(days=1), 8_400, {"a": -1600.0}, {"a": 8_400})
    assert r.killed
    r.update(ts + pd.Timedelta(days=30), 8_400, {"a": -1600.0}, {"a": 8_400})
    assert r.killed
    r.reset(8_400)
    assert not r.killed


def test_kill_file_flattens_everything(tmp_path):
    panel = flat_panel(bars=10)
    cfg = Config(symbols=SYMS, allocations={"trend": 1.0})
    t = Trader(cfg, 3, [Hold(5.0)], kill_file=tmp_path / "KILL")
    for i in range(3):
        t.step(panel.view(i), fill_now=True)
    assert t.portfolio.gross() > 0
    (tmp_path / "KILL").write_text("stop")
    t.step(panel.view(3), fill_now=True)
    assert t.risk.killed and t.portfolio.gross() == 0


def test_losing_strategy_is_benched_then_resumed():
    r = RiskGovernor(Config().risk, ["a"])
    ts = pd.Timestamp("2024-01-01")
    r.update(ts, 10_000, {"a": 0.0}, {"a": 1000})
    r.update(ts + pd.Timedelta(hours=1), 9_890, {"a": -110.0}, {"a": 1000})
    assert r.benched("a") and not r.killed
    r.update(ts + pd.Timedelta(days=15), 9_890, {"a": -110.0}, {"a": 1000})
    assert not r.benched("a")


# --- end to end -----------------------------------------------------------
def test_full_backtest_respects_limits():
    cfg = Config(symbols=SYMS)
    res = run(cfg, Panel.from_frames(synthetic_frames(SYMS, bars=24 * 120, seed=5)))
    assert np.isfinite(res.equity).all()
    assert (res.equity / res.equity.cummax() - 1).min() > -0.20
    assert res.equity.iloc[-1] == pytest.approx(10_000 + res.strategy_pnl.iloc[-1].sum())


class FakeFeed:
    def __init__(self, frames):
        self.frames, self.upto = frames, 0

    def fetch(self, symbol, since):
        f = self.frames[symbol].iloc[: self.upto]
        return f[f.index >= since]


def test_runner_persists_state_and_survives_restart(tmp_path, monkeypatch):
    frames = synthetic_frames(SYMS, bars=24 * 60, seed=7, start="2024-01-01")
    monkeypatch.setattr(pd.Timestamp, "now", classmethod(lambda cls, tz=None: pd.Timestamp("2024-03-10", tz=tz)))
    cfg = Config(symbols=SYMS, data_dir=str(tmp_path / "data"), state_dir=str(tmp_path / "state"))
    feed = FakeFeed(frames)
    feed.upto = 24 * 50
    runner = Runner(cfg, feed)
    assert runner.cycle() is not None
    assert runner.cycle() is None                             # same bar: nothing to do
    for _ in range(100):
        feed.upto += 1
        runner.cycle()
    equity, qty = runner.trader.portfolio.equity, runner.trader.portfolio.qty["trend"].copy()

    restarted = Runner(cfg, feed)                             # fresh process, same state dir
    assert restarted.trader.portfolio.equity == pytest.approx(equity)
    np.testing.assert_allclose(restarted.trader.portfolio.qty["trend"], qty)
    assert restarted.last_ts == runner.last_ts
    feed.upto += 1
    rec = restarted.cycle()
    assert rec["ts"] > runner.last_ts.isoformat()
    lines = (tmp_path / "state" / "journal.jsonl").read_text().splitlines()
    assert len(lines) == 102 and json.loads(lines[-1])["equity"] == rec["equity"]
