"""Configuration for the trading system. All limits live here."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RiskConfig:
    max_gross_leverage: float = 2.0      # sum of |position notional| / equity
    max_position_frac: float = 0.35      # one leg of one symbol / equity
    risk_per_trade: float = 0.01         # equity lost if a stop is hit
    daily_loss_limit: float = 0.03       # halt for the rest of the UTC day
    max_drawdown: float = 0.15           # flatten everything, wait for a human
    strategy_drawdown: float = 0.10      # of the strategy's allocated capital
    strategy_cooldown_days: int = 14     # bench time for a tripped strategy


@dataclass
class CostConfig:
    spot_fee: float = 0.001
    perp_fee: float = 0.0005
    slippage: float = 0.0002


@dataclass
class Config:
    symbols: list[str] = field(default_factory=lambda: [
        "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "LTC"])
    quote: str = "USDT"
    initial_equity: float = 10_000.0
    allocations: dict[str, float] = field(default_factory=lambda: {
        "carry": 0.60, "trend": 0.25, "reversion": 0.15})
    risk: RiskConfig = field(default_factory=RiskConfig)
    costs: CostConfig = field(default_factory=CostConfig)
    exchange: str = "okx"
    data_dir: str = "data"
    state_dir: str = "state"

    @classmethod
    def load(cls, path: str | Path | None) -> "Config":
        if path is None:
            return cls()
        raw = json.loads(Path(path).read_text())
        risk = RiskConfig(**raw.pop("risk", {}))
        costs = CostConfig(**raw.pop("costs", {}))
        return cls(risk=risk, costs=costs, **raw)

    def to_dict(self) -> dict:
        return asdict(self)
