# Writing a strategy

A strategy is one function that turns market data into a table of target
weights. The engine does the trading, the charges and the bookkeeping.

```python
from quant.engine import Ctx, Plan, register
from quant.strategies.util import on_rows, period_starts, top_n

@register("xs_momentum__12_1", family="xs_momentum",
          grid={"lookback": [252, 126], "top": [10, 15]},
          cards=("xs_momentum__classic_12_1",))
def momentum_12_1(ctx: Ctx, lookback=252, skip=21, top=10) -> Plan:
    """One-line description of the rule."""
    close = ctx.market.close
    score = close.shift(skip) / close.shift(lookback) - 1
    weights = top_n(score, top, eligible=ctx.universe(200) & score.notna())
    return Plan(on_rows(weights, period_starts(ctx.market.dates, "M")), band=0.02)
```

Working examples: `quant/strategies/reference/examples.py`.

## What you get: `ctx`

| Call | Returns |
|---|---|
| `ctx.market.open/high/low/close` | Prices adjusted for splits and bonuses; table of date by symbol |
| `ctx.market.volume`, `.turnover` | Shares traded (adjusted) and rupees traded |
| `ctx.market.eq` | True where the stock trades in the normal EQ series that day |
| `ctx.market.raw("close")` | Price as quoted on the day (unadjusted) |
| `ctx.universe(200)` | True where a symbol is among the 200 most traded, judged on that day |
| `ctx.liquidity_rank()` | The rank itself (1 = most traded) |
| `ctx.index("close")` | NSE index levels; also `"tri"`, `"pe"`, `"pb"`, `"dy"`, `"open"`, `"high"`, `"low"` |
| `ctx.fo("NIFTY")` | Daily futures and options rows |
| `ctx.table("flows/x.parquet")` | Any other dataset under `data/` |

Read data only through `ctx`. Never call `quant.data.store` loaders or read
files directly inside a strategy: `ctx` is what cuts the data off at the
decision date.

## What you return: `Plan`

`Plan(weights, mode, decide_at, fill, stop_loss, take_profit, trailing_stop, max_hold, band)`

- `weights`: index = dates, columns = symbols, values = fraction of account
  equity. A date with no row (or an all-NaN row) means "leave the portfolio
  alone". A row is a complete instruction: symbols missing from it are sold.
- `mode="delivery"` (default): held overnight, long only, no leverage.
  Negative weights are ignored and total weight above 1 cannot be bought.
- `mode="intraday"`: bought or shorted at the open, closed at the same day's
  close. Weights may be negative. Gross exposure is capped at 5 times equity
  and only the 500 most traded EQ-series stocks are allowed.
- `decide_at="close"` (default): row `t` is computed from data up to the
  close of day `t` and is traded on day `t+1`, at the open (`fill="open"`)
  or at the close (`fill="close"`). Do not shift signals yourself.
- `decide_at="open"`: row `t` may also use day `t`'s opening price (and
  nothing else from day `t`) and is traded at that open.
- `stop_loss`, `take_profit`: fractions of the entry price, checked against
  each day's low and high. `trailing_stop`: fraction below the highest close
  since entry. `max_hold`: trading days. After any of these exits the symbol
  stays out until a later row gives it weight 0.
- `band`: resizes smaller than this fraction of equity are skipped. Use it
  (0.02 to 0.05) for anything rebalanced often; charges are per order.

## Rules that are checked

1. **No look-ahead.** The harness re-runs your function on data cut off at
   several dates and requires the same decision for those dates. It fails if
   you use `shift(-1)`, whole-sample means or ranks, `resample(...).last()`
   month-end rows, `bfill`, or anything else that needs later rows. Use
   `period_starts`/`every_n` for rebalance days.
2. **Small account.** Capital is Rs 1,50,000 and shares are whole. A stock
   priced above its allocation cannot be bought. Orders under Rs 2,000 are
   skipped. Each order costs up to Rs 20 plus taxes, and each delivery sale
   another Rs 23.60, so 20 small positions churned monthly lose several
   percent a year to charges alone.
3. **Grids.** `grid` lists the values to try per parameter; the first value
   is the default and should be what the source uses. Keep the grid to at
   most 24 combinations, chosen before you look at any result.
4. **Parameters are chosen on 2005-2014 only.** Validation (2015-2021) is
   reported for comparison between strategies. Do not redesign a rule because
   its validation number is poor; fix real bugs only. Data after 2021 is not
   on disk.

## Running

```bash
python -m quant.engine check <id>        # look-ahead check
python -m quant.engine run <id>          # train + validation, saved to results/research/<id>.json
python -m quant.engine run --family xs_momentum --jobs 2
python -m quant.engine board --family xs_momentum
```

# Intraday strategies on one-minute bars

Register with `kind="intraday"`. The function receives an `ICtx` and returns
an `IntradayPlan`. Working example: `quant/strategies/reference/intraday_examples.py`.

```python
from quant.engine import register
from quant.intraday import ICtx, IntradayPlan, events, minute
from quant.intraday import features as F

@register("orb__basic", family="opening_range", kind="intraday",
          grid={"or_minutes": [15, 30]}, cards=("intraday_stock_selection__stocks_in_play_rvol_orb",))
def orb(ctx: ICtx, or_minutes=15) -> IntradayPlan:
    signals = {}
    for s in ctx.symbols:
        g = ctx.grid(s)                      # g.open/high/low/close/volume, each (days, 375)
        ...
        signals[s] = events(entry, stop=stop_price, score=score)
    return IntradayPlan(signals, target_r=2.0)
```

## Data

- `ctx.symbols`: the 120 most liquid NSE stocks (ranked at end-2021), most liquid first. `ctx.ranks[s]` is the rank.
- `ctx.days`: 738 full sessions, 2022-01-03 to 2024-12-31. Train is 2022-2023, validation is 2024. Later data is not on disk.
- `ctx.grid(s)`: bars for a stock. Also `ctx.grid("NIFTY")`, `"BANKNIFTY"`, `"INDIAVIX"` (index volume is empty).
- Columns are minutes: column 0 is 09:15, column 374 is 15:29. `minute("10:30")` gives the column.
- NaN means no trade in that minute. Use `F.last_price(g)` for a gap-free price.
- There is no separate daily file. Build daily values from the grid with the helpers below, which only look backward.

## Features (`quant/intraday/features.py`)

`last_price`, `day_open`, `prev_close`, `gap`, `cum_high`, `cum_low`, `opening_range(g, minutes)`,
`cum_volume`, `vwap`, `relative_volume(g, lookback)`, `daily_range_avg(g, lookback)` (average daily
range as a fraction of price over previous sessions), `prev_day(values)`, `returns_since_open`,
`minute_returns`. `day_close(g)` is the session's final price: use it only through `prev_day(...)`.

Anything you compute yourself must use only minutes at or before the signal minute and only earlier
days. Typical mistakes: a day's final high, low, close or total volume used during that day; ranking
stocks at 09:30 with a value that includes later minutes; statistics over the whole sample.

## Signals and the plan

- `events(entry, stop=None, target=None, score=None, exit=None)`: `entry` is a (days, 375) array with
  +1 (long) or -1 (short) at the minute whose close triggers the trade. The fill is the next minute's
  open. `stop` and `target` are prices, as (days, 375) grids or per-day arrays. `score` ranks competing
  entries (higher first). `exit` is a (days, 375) boolean grid: leave at the next minute's open.
- `IntradayPlan(signals, stop_pct, target_pct, target_r, exit_col, entry_from, entry_until,
  trades_per_symbol, risk_per_trade, max_notional, max_positions, max_trades_per_day, daily_loss_limit)`.
  Size is `risk_per_trade` x equity divided by the stop distance, capped at `max_notional` x equity
  and by 5x total leverage. Everything is closed at `exit_col` (default 15:15).
- Shorts are allowed only in stocks ranked 150 or better (all of `ctx.symbols` qualify).

## What the first real test showed

A plain opening-range breakout on all 120 stocks loses about half the account per year: roughly
4 to 5 trades a day, each paying about 0.15-0.2% of its value in charges and slippage, with almost no
edge before costs. So:

- Costs per round trip are about 0.15-0.2% of trade value. A stop 0.5% away means costs alone are
  0.3-0.4 of the amount risked. Prefer wider stops, larger targets, and few trades per day.
- Select hard. A strategy that trades every stock every day cannot win.
- Report what you find even if every variant loses. A clear negative result is useful.

## Rules

1. Fix the parameter grid before running; at most 8 combinations; first value is the default from the source.
2. Do not redesign a rule because validation is poor. Fix real bugs only.
3. `python -m quant.engine check <id>` must pass (it hides later bars and re-runs your function).
4. Run evaluations one at a time (`python -m quant.engine run <id>`); the machine is shared.
5. Do not edit anything under `quant/engine`, `quant/intraday`, `quant/data`. Report problems instead.
