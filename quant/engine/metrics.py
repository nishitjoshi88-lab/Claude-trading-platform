"""Performance statistics, including corrections for testing many strategies."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import norm

from .sim import SimResult

DAYS = 252
EULER = 0.5772156649015329


def stats(res: SimResult, capital: float, rf: float = 0.065, tax_rate: float = 0.20) -> dict:
    """Summary of one simulation. `rf` is the yearly risk-free rate used for
    Sharpe and Sortino; Indian treasury bills have paid roughly 6-7%."""
    eq = res.equity.dropna()
    if len(eq) < 30:
        return {"days": int(len(eq))}
    r = eq.pct_change()
    r.iloc[0] = eq.iloc[0] / capital - 1
    years = len(eq) / DAYS
    total = eq.iloc[-1] / capital - 1
    cagr = (1 + total) ** (1 / years) - 1 if total > -1 else -1.0
    vol = float(r.std() * math.sqrt(DAYS))
    excess = r - rf / DAYS
    sharpe = float(excess.mean() / r.std() * math.sqrt(DAYS)) if r.std() > 0 else 0.0
    downside = float(np.sqrt((np.minimum(excess, 0) ** 2).mean()) * math.sqrt(DAYS))
    dd = eq / np.maximum(eq.cummax(), capital) - 1
    max_dd = float(dd.min())
    monthly = eq.resample("ME").last()
    m = monthly.pct_change()
    m.iloc[0] = monthly.iloc[0] / capital - 1
    yearly = eq.resample("YE").last()
    y = yearly.pct_change()
    y.iloc[0] = yearly.iloc[0] / capital - 1
    tr = res.trades
    wins = tr[tr.pnl > 0].pnl.sum() if len(tr) else 0.0
    losses = -tr[tr.pnl <= 0].pnl.sum() if len(tr) else 0.0
    avg_eq = float(eq.mean())
    return {
        "start": str(eq.index[0].date()), "end": str(eq.index[-1].date()), "days": int(len(eq)),
        "final_equity": float(eq.iloc[-1]),
        "total_return": float(total), "cagr": float(cagr), "vol": vol,
        "sharpe": sharpe, "sortino": float(excess.mean() * DAYS / downside) if downside > 0 else 0.0,
        "max_drawdown": max_dd, "calmar": float(cagr / -max_dd) if max_dd < 0 else 0.0,
        "positive_days": float((r > 0).mean()), "positive_months": float((m > 0).mean()),
        "worst_day": float(r.min()), "worst_month": float(m.min()), "best_month": float(m.max()),
        "worst_year": float(y.min()), "positive_years": float((y > 0).mean()),
        "avg_exposure": float(res.exposure.mean()),
        "turnover_per_year": float(res.traded_value / avg_eq / years / 2),
        "cost_per_year": float(res.costs / avg_eq / years),
        "orders": int(res.orders), "trades": int(len(tr)),
        "win_rate": float((tr.pnl > 0).mean()) if len(tr) else 0.0,
        "profit_factor": float(wins / losses) if losses > 0 else float("inf") if wins > 0 else 0.0,
        "avg_trade_return": float((tr.pnl / tr.cost_basis.replace(0, np.nan)).mean()) if len(tr) else 0.0,
        "after_tax_cagr": after_tax_cagr(eq, capital, tax_rate),
        "skew": float(r.skew()), "kurtosis": float(r.kurtosis() + 3),
        "skipped": res.skipped,
    }


def after_tax_cagr(eq: pd.Series, capital: float, rate: float) -> float:
    """Rough: tax every financial year's net gain (April to March) at `rate`,
    carrying losses forward. Overstates tax for long holdings, which are
    taxed only when sold and at a lower rate after a year."""
    fy = (eq.index + pd.offsets.MonthBegin(-3)).year          # April-March label
    start, value, pool = capital, capital, 0.0
    for _, part in eq.groupby(fy):
        growth = part.iloc[-1] / start
        gain = value * (growth - 1)
        taxable = gain - pool
        tax = rate * taxable if taxable > 0 else 0.0
        pool = max(-taxable, 0.0)
        value += gain - tax
        start = part.iloc[-1]
    years = len(eq) / DAYS
    return float((value / capital) ** (1 / years) - 1) if value > 0 else -1.0


def probabilistic_sharpe(sr: float, n: int, skew: float, kurt: float, benchmark: float = 0.0) -> float:
    """Probability that the true per-period Sharpe exceeds `benchmark`
    (Bailey and Lopez de Prado). `sr` and `benchmark` are per period."""
    denom = math.sqrt(max(1 - skew * sr + (kurt - 1) / 4 * sr * sr, 1e-12))
    return float(norm.cdf((sr - benchmark) * math.sqrt(max(n - 1, 1)) / denom))


def expected_max_sharpe(n_trials: int, sr_std: float) -> float:
    """Best per-period Sharpe expected from `n_trials` strategies with no
    edge, when trial Sharpes have standard deviation `sr_std`."""
    if n_trials <= 1:
        return 0.0
    return sr_std * ((1 - EULER) * norm.ppf(1 - 1 / n_trials) + EULER * norm.ppf(1 - 1 / (n_trials * math.e)))


def deflated_sharpe(returns: pd.Series, n_trials: int, sr_std: float, rf: float = 0.065) -> float:
    """Probability the strategy has a real edge after allowing for the number
    of strategies tried. `sr_std` is the standard deviation of per-period
    Sharpe ratios across all trials."""
    r = returns.dropna() - rf / DAYS
    if len(r) < 30 or r.std() == 0:
        return 0.0
    sr = r.mean() / r.std()
    return probabilistic_sharpe(sr, len(r), float(r.skew()), float(r.kurtosis() + 3),
                                expected_max_sharpe(n_trials, sr_std))
