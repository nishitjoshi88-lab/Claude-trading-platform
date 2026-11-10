"""Reference intraday strategy on one-minute bars: opening-range breakout.

Shows the conventions for kind="intraday" strategies: read bars through the
context, build signals per symbol from features that only look backward,
return an IntradayPlan.
"""
from __future__ import annotations

import numpy as np

from quant.engine import register
from quant.intraday import ICtx, IntradayPlan, events, minute
from quant.intraday import features as F
from quant.intraday.grid import MINUTES


@register("reference__orb", family="reference", kind="intraday",
          grid={"or_minutes": [15, 30], "target_r": [2.0, 0.0]})
def opening_range_breakout(ctx: ICtx, or_minutes: int = 15, target_r: float = 2.0,
                           min_range: float = 0.004, max_range: float = 0.03) -> IntradayPlan:
    """Buy the first break above the opening range (short the first break
    below), stop at the other side of the range, exit at a multiple of the
    risk or at the square-off time."""
    cols = np.arange(MINUTES)[None, :]
    signals = {}
    for s in ctx.symbols:
        g = ctx.grid(s)
        hi, lo = F.opening_range(g, or_minutes)                 # known from minute or_minutes-1
        px = F.last_price(g)
        width = (hi - lo) / lo
        ok = ((width >= min_range) & (width <= max_range))[:, None] & (cols >= or_minutes)
        up = ok & (px > hi[:, None])
        down = ok & (px < lo[:, None])
        first = (np.cumsum(up | down, axis=1) == 1) & (up | down)   # the first break of the day only
        entry = np.where(first & up, 1, np.where(first & down, -1, 0)).astype(np.int8)
        stop = np.where(entry > 0, lo[:, None], hi[:, None])        # opposite side of the range
        signals[s] = events(entry, stop=stop, score=width)
    return IntradayPlan(signals, target_r=target_r or None, entry_until=minute("13:00"),
                        risk_per_trade=0.005, max_positions=4, max_trades_per_day=6)
