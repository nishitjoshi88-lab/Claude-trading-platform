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
