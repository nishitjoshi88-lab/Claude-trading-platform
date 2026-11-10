"""Two reference strategies showing the conventions. Copy the shape, not the idea.

1. A monthly stock-momentum portfolio: delivery mode, decisions on the first
   trading day of each month, traded at the next day's open.
2. An intraday gap fade: decided at the open (it may use that day's opening
   price and nothing else from that day), closed the same day.
"""
from __future__ import annotations

import numpy as np

from quant.engine import Ctx, Plan, register
from quant.strategies.util import on_rows, period_starts, top_n


@register("reference__momentum_12_1", family="reference",
          grid={"lookback": [252, 126], "top": [10, 15], "universe": [200]})
def momentum_12_1(ctx: Ctx, lookback: int = 252, skip: int = 21, top: int = 10, universe: int = 200) -> Plan:
    """Buy the `top` stocks with the highest return over `lookback` days,
    skipping the latest `skip` days, among the `universe` most traded."""
    close = ctx.market.close
    score = close.shift(skip) / close.shift(lookback) - 1
    weights = top_n(score, top, eligible=ctx.universe(universe) & score.notna())
    weights = on_rows(weights, period_starts(ctx.market.dates, "M"))
    return Plan(weights, band=0.02)


@register("reference__gap_fade", family="reference",
          grid={"gap": [0.02, 0.03], "names": [3], "stop": [0.02]})
def gap_fade(ctx: Ctx, gap: float = 0.02, names: int = 3, stop: float = 0.02, universe: int = 100) -> Plan:
    """Buy at the open the liquid stocks that opened furthest below the
    previous close (at least `gap`), and sell at the close."""
    m = ctx.market
    opening_gap = m.open / m.close.shift(1) - 1
    # the universe uses yesterday's ranking: today's turnover is not known at the open
    eligible = ctx.universe(universe).shift(1, fill_value=False) & (opening_gap <= -gap)
    weights = top_n(opening_gap, names, eligible=eligible, ascending=True)
    return Plan(weights, mode="intraday", decide_at="open", stop_loss=stop)
