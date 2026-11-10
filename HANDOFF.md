# Handoff: where the project stands and how to continue

Written 2026-11-10. Read this fully before doing anything.

## Goal and constraints (from the owner)

- Retail trader in India, capital Rs 1,50,000, broker Angel One (SmartAPI).
- Wants a fully automated system, profits reinvested, **intraday trading as the priority**, and a layer that tracks markets and world news.
- **Usage rule: the owner's weekly model allowance must not be exhausted.** Work in small chunks.

## Usage rules (strict)

1. Work solo. Do not use the Workflow tool or multi-agent fan-outs, even if ultracode is on. One sub-agent at a time is allowed only when a chunk below says so.
2. Before starting and every ~30 tool calls, call `get_session` (no arguments). Stop for the day when either:
   - `external_metadata.usage.cost_usd` for this session reaches **25**, or
   - `external_metadata.rate_limit_info.status` is anything other than `allowed`.
3. One chunk per day. Finish by updating "Progress" below, committing and pushing.
4. The first session (10 Nov) spent about $300 in an hour on 70+ parallel agents and put the weekly limit into its warning state. Do not repeat that.

## Protected test periods (never break these)

| Data | Research may use | Protected until strategy code is frozen |
|---|---|---|
| Daily stocks, indices, futures/options | up to 2021-12-31 | 2022-01-01 onward |
| One-minute bars | 2022-01-01 to 2024-12-31 | 2025-01-01 onward |

The loaders enforce this (`quant/data/store.py`, `quant/data/upstox.py`). Do not download, open or analyse protected data, and do not set the unlock variables, until the final test in chunk 7.

## What exists

| Part | Location | State |
|---|---|---|
| Daily simulator, costs, metrics, harness | `quant/engine/` | 20 tests pass. **Not independently reviewed.** |
| Index-options simulator | `quant/options/` | 6 tests pass on synthetic data only. Not reviewed, never run on real data. |
| Minute-bar intraday simulator | `quant/intraday/` | 10 tests pass on synthetic data. Not reviewed, never run on real data. |
| One-minute data downloader | `quant/data/upstox.py` | Works. Data itself is not in git and must be re-downloaded (no model usage, about 40 minutes). |
| Daily / F&O / index / flows data builders | `quant/data/nse_cm.py`, `nse_fo.py`, `indices.py`, `intraday.py` | Written by workers that were stopped mid-task. **Unfinished and unaudited; treat as drafts.** |
| Strategy guide and two examples | `quant/strategies/README.md`, `quant/strategies/reference/` | Examples pass the look-ahead check on synthetic data. |
| Research notes | `research/raw/*.md`, `research/cards/*.json` | 10 of 31 areas written; fact-checking incomplete, so verify any number before relying on it. |
| Old crypto paper trader | `trader/`, `README.md` | Superseded (no edge out of sample; impractical for an Indian resident). README still describes it and needs rewriting. |

Unverified assumptions inside the simulators: Angel One brokerage rates and statutory charges in `quant/engine/costs.py`, slippage tiers, 5x intraday leverage, `lot_notional` in the options simulator.

## Rebuild the intraday data (no model usage)

```bash
pip install -r requirements.txt pyarrow scipy beautifulsoup4 pypdf
python -m quant.data.upstox universe --asof 2021-12-31 --top 200
python -m quant.data.upstox download --start 2022-01 --end 2024-12 --threads 6   # run in the background
python -c "from quant.intraday.grid import build_grids; print(len(build_grids()))"
```

The daily bhavcopy archive needed by `universe` is at archives.nseindia.com (reachable). www.nseindia.com and Yahoo Finance are blocked from the cloud container.

## Staged plan: one chunk per day

1. **Intraday strategies, first batch.** Rebuild the minute data. Implement 5 strategies in `quant/strategies/intraday/` from `research/raw/intraday_evidence.md` and `intraday_stock_selection.md`: opening-range breakout, VWAP trend, gap continuation and gap fade, last-half-hour momentum, relative-volume "stocks in play". Small parameter grids fixed in advance. Run `python -m quant.engine run --family intraday`. Report train (2022-2023) and validation (2024) results after costs, honestly.
2. **Check the intraday simulator against reality.** Compare a sample of minute bars with the day's official prices; check split handling, opening-bar behaviour, missing minutes. Verify Angel One intraday charges, leverage and square-off time from official pages and correct `costs.py`. One research sub-agent allowed.
3. **Daily data.** Finish and verify `quant/data/nse_cm.py` (price adjustment for splits and bonuses is the risky part) and build the 2003-2021 panel. Spot-check 20 known splits/bonuses by hand.
4. **Daily strategies, first batch.** Momentum, short-term mean reversion, trend/ETF rotation from the saved research notes. Train 2005-2014, validation 2015-2021.
5. **Options.** Finish `nse_fo.py`, build NIFTY data 2008-2021, run a few defined-risk structures. Verify lot size and margins first. Expect most structures to be unaffordable at Rs 1.5 lakh; report that plainly.
6. **Market intelligence layer.** Collectors for a pre-market pack (overnight global moves, company announcements, results calendar, headlines). No language-model calls yet.
7. **Selection and the single protected test.** Fix the selection rule in writing first, count every parameter set tried, then unlock the protected periods once, run, and write `research/RESULTS.md`. Only strategies that pass go on to paper trading through Angel One.

Later, not scheduled: Angel One adapter and paper-trading runner; language-model analysis of the intelligence pack (forward-tested only); the 21 unfinished research areas, especially regulation, costs and taxes, and the Angel One API.

## Facts the owner should know (unverified, from broker pages)

- SEBI's retail algo framework became mandatory on 1 April 2026: API orders need a static IP registered with the broker and a fresh two-factor login each trading day. Live automation therefore needs a small server with a fixed IP, not a cloud session.
- Angel One credentials are not needed until paper trading. They must be added as environment secrets, never pasted in chat.

## Progress

- 2026-11-10: engines and downloader written; research and reviews started then stopped early to save usage. Nothing has been backtested on real data yet.
