# Claude Trading Platform

A fully automated, multi-strategy crypto trading system. It fetches market
data, decides, trades, enforces risk limits, benches failing strategies and
saves its state every hour with no human in the loop.

**It trades paper money only.** There is no real-money order execution in
this code yet, and the backtest results below do not justify adding it.

## How it works

Every hour the runner:

1. Fetches the latest closed hourly bars (spot price, perpetual-futures price,
   funding rate) from a public exchange API.
2. Marks positions to market and settles funding.
3. Asks the risk governor whether trading is allowed.
4. Asks each strategy for its target positions.
5. Scales targets down to fit the exposure limits and fills the orders
   (simulated, with fees and slippage).
6. Writes state and a journal line to disk, so a restart loses nothing.

### Strategies

| Name | Capital | Idea |
|---|---|---|
| `carry` | 60% | Long spot, short the same quantity of perp, collect funding when it is high. Market-neutral. |
| `trend` | 25% | Follow the 5-day versus 20-day average on each perp, sized by volatility. Long or short. |
| `reversion` | 15% | Buy after an unusually sharp 24-hour fall; exit on stop, target or time limit. |

### Risk governor

These rules override every strategy (`trader/risk.py`, limits in `trader/config.py`):

| Rule | Limit | Action |
|---|---|---|
| Total exposure | 2x equity | Targets scaled down |
| Single position | 35% of equity | Target scaled down |
| Stop-based trades | 1% of equity at risk | Position sized to fit |
| Daily loss | 3% | Directional books flattened, no new trades until the next UTC day |
| Strategy loss | 10% of its capital | Strategy flattened and benched for 14 days |
| Total drawdown | 15% from peak | Everything flattened; stays flat until a human runs `reset` |
| Kill switch | `state/KILL` file exists | Same as total drawdown |

## Backtest results on real data

Hourly Binance data for 10 large coins, including 0.1% spot fees, 0.05% perp
fees and 0.02% slippage per trade. Parameters were looked at on 2022-01 to
2024-06 only; the later period was run once and not tuned against.

| Period | Annual return | Sharpe | Max drawdown | Positive days |
|---|---|---|---|---|
| 2022-01 to 2024-06 (examined) | +11.4% | 1.54 | -6.6% | 50% |
| 2024-07 to 2026-10 (out of sample) | -0.3% | -0.01 | -11.3% | 47% |
| 2022-01 to 2026-10 (all) | +5.2% | 0.77 | -13.1% | 49% |

What this says:

- **The system is not profitable out of sample.** Nearly all the profit came
  from 2023 (+22.5%); every other year was between -1.6% and +3.6%.
- `carry` is steady (worst drawdown about 1%) but small: funding was only
  high enough to trade part of the time, and it earned almost nothing after 2024.
- `trend` made its money in 2023 and lost slightly afterwards.
- `reversion` shows no reliable edge.
- The risk limits held throughout: the 15% kill never triggered.

The backtest also ignores things that hurt in real trading: exchange outages,
liquidation of the short leg in a sharp rally, borrowing costs, and coins
that were delisted (the 10 symbols were chosen today, which flatters results).

## Usage

```bash
pip install -r requirements.txt
python -m pytest                       # 15 tests

python -m trader download --start 2022-01 --end 2026-10   # history for backtests
python -m trader backtest                                 # full period
python -m trader backtest --from 2024-07-01 --only carry,trend
python -m trader backtest --data synthetic                # no download needed

python -m trader run --once            # one live paper cycle
python -m trader run                   # run forever, one cycle per hour
python -m trader status                # equity, exposure, risk state
touch state/KILL                       # emergency stop: flatten and halt
python -m trader reset                 # clear a kill after review
```

To run it unattended: `docker build -t trader . && docker run -d --restart always -v $PWD/state:/app/state -v $PWD/data:/app/data trader`.

Settings (symbols, allocations, limits, exchange) can be overridden with a
JSON file: `python -m trader --config my.json run`.

## Layout

| File | Purpose |
|---|---|
| `trader/config.py` | All limits and settings |
| `trader/market.py` | Data containers; a view that cannot see the future |
| `trader/data.py` | History download and live exchange feed |
| `trader/portfolio.py` | Positions, fees, funding and profit per strategy |
| `trader/risk.py` | Risk governor |
| `trader/strategies.py` | The three strategies |
| `trader/core.py` | The hourly decision step, shared by backtest and live |
| `trader/backtest.py` | Backtester and statistics |
| `trader/live.py` | Automated runner with persistent state |

## Not built yet

- Real-money order execution.
- Any use of language models or news.
- Automatic strategy research; today the system only benches strategies, it does not invent new ones.
- Alerts and a dashboard.
