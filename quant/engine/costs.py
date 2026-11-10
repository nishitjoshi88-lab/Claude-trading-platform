"""Indian trading charges, as formulas.

Every rate here is a fraction of traded value unless it says rupees. The
defaults are the schedule the simulator applies to the whole history (today's
charges are what matter for a decision about trading tomorrow). Values are
checked against research/INDIA_CONSTRAINTS.md; change them here only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SEGMENTS = ("delivery", "intraday", "futures", "options")


@dataclass(frozen=True)
class SegmentCharges:
    brokerage_rate: float          # fraction of order value
    brokerage_cap: float           # rupees per order (the "flat fee")
    brokerage_min: float           # rupees per order
    stt_buy: float
    stt_sell: float
    exchange: float                # exchange transaction charge, both sides
    stamp_buy: float
    dp_sell: float = 0.0           # rupees per sell order, before GST (demat debit)


@dataclass(frozen=True)
class CostModel:
    segments: dict[str, SegmentCharges] = field(default_factory=lambda: {
        # Angel One: lower of Rs 20 or 0.1% per executed order, minimum Rs 5
        "delivery": SegmentCharges(0.001, 20.0, 5.0, 0.001, 0.001, 0.0000297, 0.00015, dp_sell=20.0),
        # lower of Rs 20 or 0.03% per executed order, minimum Rs 5
        "intraday": SegmentCharges(0.0003, 20.0, 5.0, 0.0, 0.00025, 0.0000297, 0.00003),
        "futures": SegmentCharges(1.0, 20.0, 20.0, 0.0, 0.0002, 0.0000173, 0.00002),
        # value = premium traded
        "options": SegmentCharges(1.0, 20.0, 20.0, 0.0, 0.001, 0.0003503, 0.00003),
    })
    sebi: float = 0.000001         # Rs 10 per crore
    ipft: float = 0.000001         # investor protection fund trust (NSE)
    gst: float = 0.18              # on brokerage + exchange + SEBI + IPFT, and on DP charge
    # slippage as a fraction of value, by liquidity rank (1 = most traded)
    slippage_tiers: tuple[tuple[int, float], ...] = ((50, 0.0003), (200, 0.0006), (500, 0.0012), (1000, 0.0025))
    slippage_unranked: float = 0.004

    def charges(self, segment: str, side: str, value: float) -> float:
        """Rupees of brokerage, taxes and fees for one executed order."""
        s = self.segments[segment]
        value = abs(value)
        if value == 0:
            return 0.0
        brokerage = min(max(value * s.brokerage_rate, s.brokerage_min), s.brokerage_cap)
        exchange = value * s.exchange
        regulatory = value * (self.sebi + self.ipft)
        total = (brokerage + exchange + regulatory) * (1 + self.gst)
        if side == "buy":
            total += value * (s.stt_buy + s.stamp_buy)
        else:
            total += value * s.stt_sell + s.dp_sell * (1 + self.gst)
        return total

    def slippage(self, value: float, rank: float) -> float:
        """Rupees lost to the bid-ask spread and impact for one order."""
        rate = self.slippage_unranked
        if rank == rank:                       # not NaN
            for limit, r in self.slippage_tiers:
                if rank <= limit:
                    rate = r
                    break
        return abs(value) * rate

    def round_trip_rate(self, segment: str, value: float, rank: float = 100) -> float:
        """Total cost of buying then selling `value`, as a fraction of value."""
        c = self.charges(segment, "buy", value) + self.charges(segment, "sell", value)
        return (c + 2 * self.slippage(value, rank)) / value
