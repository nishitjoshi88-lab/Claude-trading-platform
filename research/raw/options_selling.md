# Index option selling and volatility premium: research findings (India, as of 2026-11-10)

Scope: short straddles and strangles (including the 9:20 straddle), iron condor and iron fly, credit spreads, weekly and monthly systems, expiry-day (0DTE) trades, calendars and diagonals, delta-neutral adjustments, the volatility risk premium (VRP) in India, platform backtests, 2026 margins, what fits in Rs 1.5 lakh, tail episodes, and SEBI rule changes 2024-2026.

Account assumed: Rs 1,50,000 cash, Angel One (SmartAPI), fully automated, profits reinvested.

How to read this file

- "QS 2025-26" means the Quantsapp public strategy library: each strategy written as exact rules and backtested once with default settings on NIFTY, 1 Oct 2025 to 30 Sep 2026, NSE second-level data, 1 lot unless stated. "gross" = before costs. "net*" = after Rs 20 per order and bid-ask slippage as Quantsapp reports it; statutory charges (STT, exchange, GST, stamp) are mostly NOT in that figure, so true net is lower still. One year, default parameters, vendor-published, fills at last traded price, stops filled at the trigger level. Treat as a recent, consistent, single-regime sample, not as proof.
- "(unverified: snippet only)" means I saw the claim in a search result but could not open the source (SSRN, ScienceDirect, Medium, GitHub and blog.openalgo.in returned HTTP 403).
- "(derived)" means my own arithmetic from sourced inputs.
- The web-search tool's shared budget ran out after 28 completed searches, so some planned searches (tastytrade/spintwig US studies, more Indian journal papers, Sensex contract details, more margin examples) were not run. Everything after that point came from opening known URLs directly.

---

## Part A. Facts that every strategy below depends on (2026)

### A1. Contract specifications and expiry calendar

| Item | Value (Nov 2026) | Effective | Source |
|---|---|---|---|
| Nifty 50 lot size | 65 (was 25 until Nov 2024, then 75) | Weekly contracts from the first January 2026 expiry (6 Jan 2026, snippet); quarterly/half-yearly from 30 Dec 2025 EOD | Angel One news; Aliceblue; NSE circular FAOP70616 as cited by both |
| Bank Nifty lot size | 30 (35 before) ; monthly expiry only | Jan 2026 | Angel One news |
| FinNifty / Midcap Select lots | 60 / 120 ; monthly only | Jan 2026 | Angel One news |
| Sensex lot size | 20 (from the Jan 2025 revision; any later revision not checked) | Jan 2025 | Zerodha Z-Connect |
| Weekly index options | One benchmark per exchange: NSE = Nifty 50 only, BSE = Sensex only | 20 Nov 2024 | Zerodha Z-Connect |
| Nifty expiry day | Tuesday (weekly); monthly = last Tuesday | 1 Sep 2025 | Marketinsiders; Quantsapp pages |
| Sensex expiry day | Thursday (weekly); monthly = last Thursday | 1 Sep 2025 | Marketinsiders. (The Aliceblue article says "every Friday": that is wrong or stale.) |
| Minimum contract value | Rs 15-20 lakh at introduction | 20/21 Nov 2024 | Zerodha Z-Connect |
| Notional per Nifty lot | about Rs 16 lakh (Nifty about 24,000-25,000 through mid/late 2026) | | Zerodha "In The Money" (Aug 2026); OpenAlgo (spot 24,056 in late Jun 2026) |

Consequence: the pre-2024 "expiry every day" ecosystem (Bank Nifty Wed, FinNifty Tue, Midcap Mon, Nifty Thu, Sensex Fri) is gone. A 0DTE system now has at most two expiry days a week (Nifty Tuesday, Sensex Thursday). Almost every published Indian backtest before 2025 was run on Bank Nifty weeklies with a 15 or 25 lot; none of that transfers directly.

### A2. Margins (what a short option costs to carry)

Sourced data points:

- Short Nifty ATM straddle, Feb 2025, lot 75, Nifty 23,600: SPAN Rs 1,65,506 + exposure Rs 70,810 = Rs 2,36,316. Same position turned into an iron fly with wings 300 points away: SPAN Rs 22,930 + exposure Rs 70,810 = Rs 93,741 (TradingQnA margin table).
- Short straddle 2026, lot 65: about Rs 1.9-2.1 lakh; Rs 1,92,510 quoted for 24 Sep 2026 (OpenAlgo blog, unverified: snippet only). Zerodha's Aug 2026 article says about Rs 3 lakh is blocked for a 45-DTE monthly straddle on about Rs 16 lakh notional.
- Naked single short Nifty option, 2026: Rs 1.25-1.5 lakh (NiftyWise margin article) or Rs 1.5-2 lakh (NiftyWise capital article). Bank Nifty Rs 1.5-1.9 lakh.
- Iron condor: about Rs 40,000-60,000 per lot; "hedged spread" Rs 15,000-30,000 (NiftyWise; the spread figure looks too low, see below). Quantsapp assumes Rs 60,000 for a weekly double calendar.
- Expiry-day short strangle: a Quantsapp source author notes about Rs 1.4-1.5 lakh per lot on expiry day.
- Expiry day: an additional 2% Extreme Loss Margin on every short index option expiring that day, "regardless of whether your position is intraday or overnight, and even if your position is hedged". Zerodha's example: 2% x 23,500 x 65 = Rs 30,550 per short lot (Zerodha support).
- Calendar-spread margin benefit is withdrawn on expiry day for the expiring leg (from 10 Feb 2025 per Zerodha; Aliceblue dates it 20 Nov 2024).

Margin model for the backtester (derived from the TradingQnA table; check against Angel One's margin calculator before trading):

- Exposure margin = 2% of notional per short leg (35,405 / (23,600 x 75) = 2.0%). It is charged on each short leg even when hedged.
- SPAN for a naked ATM option is about 9.1-9.4% of notional; for a straddle SPAN is the larger leg only.
- Naked straddle is about 13.3% of notional: about Rs 2.1-2.2 lakh at Rs 16-16.25 lakh notional.
- Iron fly / iron condor is about 1-1.5% SPAN + 4% exposure, about 5-5.5% of notional: about Rs 80,000-90,000 on a normal day.
- Single credit spread is about 0.6-1.3% SPAN + 2% exposure: about Rs 42,000-55,000. (This is why I distrust the Rs 15,000-30,000 figure.)
- On expiry day add 2% of notional (about Rs 31,000-32,500) per short leg expiring that day: naked straddle about Rs 2.8 lakh; iron fly or condor about Rs 1.45-1.55 lakh; single credit spread about Rs 75,000-87,000.

So for Rs 1.5 lakh: a naked straddle or strangle never fits. One iron fly or condor fits on non-expiry days with about 40% buffer, but on its own expiry day it needs essentially the whole account. One credit spread fits on any day. Two credit spreads fit only off expiry day.

Other margin rules: full option premium upfront for buyers (1 Feb 2025). At least 50% of margin in cash or cash equivalents from 1 Apr 2026 (Aliceblue; not cross-checked); Angel One charges 0.0342% per day on cash-collateral shortfall above Rs 50,000. Not binding for an all-cash account.

### A3. Costs at Angel One (opened 2026-11-10)

| Charge | Options | Notes |
|---|---|---|
| Brokerage | Rs 20 per executed order, flat | Each leg of each entry and exit is an order |
| STT | 0.15% of premium, sell side (0.10% before 1 Apr 2026; 0.0625% before Oct 2024, the last figure from memory, not re-checked) | Budget 2026. On exercise (ITM at expiry) 0.15% of intrinsic value |
| Exchange transaction | NSE 0.0355299% of premium; BSE Sensex options 0.0325% | Both sides |
| Stamp duty | 0.003% of premium, buy side | |
| SEBI | Rs 10 per crore | |
| GST | 18% on brokerage + transaction + SEBI charges | |

Per-trade cost at 1 lot (derived): a two-leg straddle round trip is 4 orders = Rs 94 brokerage with GST, plus about Rs 35-45 statutory on about Rs 16,000 of premium, about Rs 130-140 before slippage. A four-leg iron fly or condor round trip is 8 orders, about Rs 190 brokerage with GST plus about Rs 40-50 statutory, about Rs 235. Quantsapp's net* figures imply brokerage plus bid-ask slippage of about Rs 215 per daily straddle and about Rs 266 per daily iron fly.

A daily two-leg system therefore costs about Rs 55,000-62,000 a year at 1 lot and a daily four-leg system about Rs 70,000-78,000: 37-52% of a Rs 1.5 lakh account per year. Flat per-order brokerage on a single lot is the dominant drag. This is the single most important number in this file.

### A4. Trading hours and settlement (changes on 7 Dec 2026)

- From 3 Aug 2026 (Closing Auction Session, CAS): CAS stocks stop continuous trading at 15:15, auction to 15:35, index and stock F&O trade until 15:40, and expiring contracts settle on CAS closing prices.
- From 7 Dec 2026: all stocks trade to 15:30; CAS 15:30-15:40 (random close 15:38-15:40); expiring index and stock F&O settle on the VWAP of 15:00-15:30; index F&O trade to 15:45, but expiring index contracts stop at 15:30 on expiry day (Zerodha Z-Connect update, 16 Oct 2026).
- Backtests must not hard-code 15:30. Settlement prices before and after 3 Aug 2026 and after 7 Dec 2026 are not comparable. A SEBI order on the 13 Aug 2026 Sensex expiry found three spikes of 133-405 index points within seconds during the auction and barred two entities (Marketinsiders).

### A5. Algo rules that change how stops must be coded (1 Apr 2026)

Angel One SmartAPI, from 1 Apr 2026: API orders only from a registered static IP; 10 orders per second threshold per exchange/segment (below it a generic exchange algo ID is used); **market orders and IOC orders are prohibited for algorithmic trading**; self-coded "tech-savvy" clients may host their own logic with a registered static IP (Angel One).

Implication: the classic "SL-M on each leg" 9:20 straddle cannot be reproduced. Stops have to be stop-limit or marketable-limit orders with a price buffer, which can go unfilled in a fast market. Every backtest that fills stops "at the trigger level" overstates results; test with a limit buffer and a non-fill model.

### A6. Regulatory risk still open

- SEBI's chairman said in September 2025 that ending weekly expiries would be considered and a consultation paper issued "as and when it is ready" (Outlook Money). As of 31 Aug 2026 the review was still described as open and no decision was found (Marketinsiders). Weekly-expiry strategies carry a real risk of being regulated away. Monthly systems do not.
- SEBI studies: 93% of individual F&O traders lost money over FY22-FY24, aggregate over Rs 1.8 lakh crore (SEBI press release title; Marketinsiders gives Rs 1.81 trillion and 7.2% profitable). FY25: 91% lost (NiftyWise citing SEBI's July 2025 study); net loss Rs 1,05,603 crore (unverified: snippet only).
- Jane Street: SEBI interim order of 3 Jul 2025 alleged Bank Nifty expiry-day manipulation on 18 expiry days (Jan 2023-Mar 2025), Rs 4,843.57 crore impounded (Oxford Business Law Blog). Expiry-day path and settlement were being moved by large players in exactly the window intraday sellers trade.

---

## Part B. Is there a premium to sell? The volatility risk premium in India

Academic

- Sankar, Ramachandran and Lukose (2020), International Review of Economics and Finance 70: 321-334. Tests and rejects the idea that variance risk is unpriced in a retail-heavy market. Model-dependent and model-free methods; robust across sampling frequencies and sub-periods. Only past continuous variance (not jumps) forecasts short-term synthetic variance-swap returns. The search summary adds that market-neutral Nifty straddles and long synthetic variance swaps earn significantly negative returns, that is, sellers are paid (abstract opened; the straddle detail is unverified: snippet only).
- Bhat, Pandey and Rao (2024), Journal of Futures Markets 44(8): 1320-1337. "Positive and significant overnight option returns are accompanied by negative intraday returns" for short Nifty option strategies. "The variance risk premium earned by option sellers is mainly a reward for overnight risk." Robust across option categories and sub-samples, weaker on jump days (abstract opened). Sample reported as 2017-2020 (unverified: snippet only). This is the most important single finding for this area: the popular Indian intraday selling systems sell during the part of the day when the seller's return is negative before costs.
- Pillai (SSRN 6876580, posted 2026), "Trading the Volatility Risk Premium on Nifty 50: Strategy Backtest with Realistic Frictions". Four short-volatility strategies on Nifty monthly options, 119 expiry cycles, Jan 2015-Apr 2025, with STT, brokerage, slippage and daily futures re-hedging. Net of costs every strategy has a negative annualised return; the delta-hedged and straddle variants lose about 44-45% a year on margin; worst month about -13.2% of margin for straddles and -18.3% for a 0.98-moneyness put-write; losses are driven by tails more than by costs; conclusion: the premium exists but is not capturable by a retail trader. Not peer-reviewed. (unverified: snippet only. HTTP 403.)
- NSE Working Paper 9/2013 (Thenmozhi and Chandra): India VIX and Nifty returns are negatively related, asymmetrically; India VIX captures volatility better than ARCH/GARCH measures.

Practitioner measurements

- OpenAlgo quant chapter, year to late June 2026: mean India VIX 13.77 against mean 21-day realised volatility 11.84, an average premium of +1.93 vol points; implied above realised on 82% of days.
- A GitHub study reports India VIX averaging 16.59 against 14.12 next-21-day realised (+2.46 points, positive 79.7% of days, worst day -64.5 on 2020-03-05) (unverified: snippet only).

Global reference

- Coval and Shumway via Quantpedia: zero-beta ATM straddles on S&P indices lose about 3% a week for buyers; a selling strategy (ATM straddle sold at bid, 15% OTM crash put bought at ask, 5% premium exposure) made 1.94% a month over 1986-1995, with a warning that put sellers have had losses up to -800% and large losses cluster.
- Israelov and Tummala, "Which Index Options Should You Sell?" via CXO Advisory: delta-hedged short S&P 500 options, Mar 1996-Dec 2015; shorter maturities beat longer; near-the-money beats deep OTM; puts beat calls. Gross of costs.
- Israelov, Nielsen and Villalon, "Embracing Downside Risk" (AQR, Journal of Alternative Investments 2017): most of the equity premium is compensation for downside exposure; option buyers should expect to underperform.
- Vilkov, "0DTE Trading Rules" via Hull Tactical: S&P 500 0DTE options, Sep 2016-Jan 2024, static daily rules held to expiry. A same-day variance premium exists, but the return distributions are so wide that mean returns of most strategies are not statistically significant; P&L is explained largely by realised intraday skewness.
- Wysocki (arXiv 2608.24786, Aug 2026): learning-to-rank over delta-targeted SPXW 0DTE short puts plus a SKIP option; out-of-time 2025 Sharpe 4.3-5.8 against walk-forward 1.9-3.1 on 2021-2024. One hold-out year, US market, bid-to-mid fills. Shows that conditioning (when not to sell) is where any edge is claimed.

Summary: the premium is real in India in the academic sense, modest in size (about 2 vol points on average), concentrated overnight, and offset by tails. Whether a Rs 1.5 lakh account paying Rs 20 an order can keep any of it is the open question for the backtests.

---

## Part C. Strategies

Each entry: rules, instruments, holding period, reported performance, India evidence, costs and capacity, failure modes, feasibility at Rs 1.5 lakh, sources. Capacity is never binding at this size: Nifty weekly options are the deepest contracts in India; note only that strikes ending in 50 are several times thinner than strikes ending in 00 (Marketcalls 2021).

### C1. Intraday ATM short straddle with a stop on each leg (the "9:20 straddle")

- Rules: every trading day at 09:20 sell 1 lot ATM call and 1 lot ATM put of the nearest Nifty weekly (ATM from spot or that expiry's synthetic forward). Stop on each leg at entry premium x (1 + SL%). When one leg stops, the other continues with its own stop. No re-entry. Square off at 15:10.
- Parameters in sources: entry 09:16, 09:20, 09:30, 10:15, 10:30, 11:00; SL 20%, 25% (AlgoTest's worked example), 30%, 35% (Marketcalls), 40% (Marketcalls 2021), 50% (Stockmock/Squareoff 2020); exit 15:06-15:25.
- Variant "stop to cost": when one leg's stop fills, move the other leg's stop to its own entry price.
- Instruments: Nifty weekly options (historically Bank Nifty weeklies). Holding: about 5.8 hours.
- Reported performance:
  - QS 2025-26 (25% SL): 246 trades, win 56%, gross +Rs 19,405, profit factor 1.07, max drawdown Rs 33,575, worst trade -Rs 7,424; net* -Rs 33,527. Trend days +Rs 1,17,336 (79% win), choppy days -Rs 97,001 (35% win), quiet days about flat. Quantsapp's warning: "five years of results turn negative when the best 10% of days are removed".
  - QS 2025-26 stop-to-cost: gross +Rs 57,025, PF 1.27, max DD Rs 20,495; net* +Rs 8,009.
  - Marketcalls (Dec 2023): Bank Nifty weekly, 35% SL, since 2017, 0.5% slippage and commission included; profitable through 2022, weak in 2023; a 10:30 entry "could have done much better" (results are images; no numbers quoted).
  - Marketcalls (Aug 2021): Quantman backtests of Nifty monthly (from Jan 2017) and weekly (from Apr 2019) intraday straddles looked good; warns market-order slippage plus costs of 1-2.5% of premium turnover and stop hunting on thin 50-multiple strikes.
  - Squareoff/Stockmock (Oct 2020): 50% SL, Bank Nifty and Nifty, "profits almost every month" (images only).
  - TradingQnA (Feb 2025): no-stop 9:20 Nifty straddle for Dec 2024 only: 13 winning days, 7 losing, +434 points gross over 20 sessions (my sum of the poster's table); replies point out the one-month sample and missing costs.
  - Quintalmind (generic claims for 2019-2024, no data shown): expiry-day 9:20 straddle win rate about 65-70% with 25% SL but average loss 2-3x average win; "real-world results are typically 15-30% worse than backtests"; COVID 2020 drawdowns of 30-50% of capital.
- India evidence: yes, extensive but practitioner-grade. Academic counter-evidence: intraday short-option returns on Nifty are negative (Bhat et al. 2024).
- Costs: about Rs 215 per day brokerage plus slippage at 1 lot, plus statutory; the gross edge of Rs 79 per trade is a third of that.
- Failure modes: whipsaw days stop both legs; after one stop the position is a naked directional short; gaps through the stop; crowding (premiums compressed as the trade went viral); stop hunting; market orders now barred for algos; with only one weekly expiry, four days out of five the option has little theta to harvest intraday.
- Feasibility: NO. Margin about Rs 1.9-2.2 lakh per lot (about Rs 2.8 lakh on expiry day) exceeds the account.
- Sources: https://www.quantsapp.com/backtesting/strategies/short-straddle-entry-time-grid-leg-sl ; https://www.quantsapp.com/backtesting/strategies/short-straddle-leg-sl-move-other-to-cost ; https://www.marketcalls.in/futures-and-options/is-the-920-straddle-no-more-working.html ; https://www.marketcalls.in/futures-and-options/how-the-9-20-intraday-straddlers-are-being-gamed.html ; https://algotest.in/blog/the-920-straddle-strategy-defined.md ; https://tradingqna.com/raw/179061 ; https://tradingqna.com/raw/88032 ; https://www.quintalmind.com/blog/time-based-straddle-strategy-nifty-options

### C2. Intraday straddle with trailing leg stops (late-morning entry)

- Rules: 11:00 sell ATM call and put, nearest weekly. Each leg starts with a stop 30% above entry. For every 5 points the leg's premium falls below entry (measured at the lowest price seen), lower that leg's stop by 5 points. A stopped leg closes alone. Exit 14:30. One trade a day.
- Reported: QS 2025-26: 246 trades, win 61%, gross +Rs 1,33,792, PF 2.34, max DD Rs 7,004, worst trade -Rs 5,370; net* +Rs 84,258; 11 of 12 months positive. Quantsapp's own caveat: fills exactly at the stop level flatter a trailing stop on fast moves.
- This was the best-looking intraday result in the library and therefore the one most likely to be an artefact of the fill assumption. Re-test with stop-limit fills and a 1-2 point adverse slip per stop.
- Feasibility: NO as written (naked). A winged version (C6 structure with these stops) is untested.
- Source: https://www.quantsapp.com/backtesting/strategies/straddle-per-leg-trailing-sl

### C3. Intraday straddle with combined-premium stop and target, with re-entry

- Rules: 09:20 sell ATM straddle. Target: call + put cost 20% less than the credit. Stop: call + put cost 1.5x the credit. Both legs close together. After either exit sell a fresh ATM straddle one minute later, at most 3 straddles a day, none after 14:30. Exit 15:15.
- Related variants tested: per-leg re-entry modes; midday re-entry if both legs stopped; combined trailing stop; rupee MTM lock-and-trail; profit ladder (5 lots).
- Reported QS 2025-26: 365 trades, win 69%, gross +Rs 60,284, PF 1.20, max DD Rs 40,329, worst -Rs 12,954; net* +Rs 23,961. Leg re-entry: gross +Rs 51,316, net* -Rs 17,786 (672 leg trades). Midday re-entry: gross +Rs 7,763, net* -Rs 54,413. Profit ladder (5 lots): gross +Rs 1,24,798, net* +Rs 27,654.
- Finding: re-entries add orders faster than they add edge.
- Feasibility: NO (naked).
- Sources: https://www.quantsapp.com/backtesting/strategies/short-straddle-combined-premium-sl-target-reentry ; https://www.quantsapp.com/backtesting/strategies/short-straddle-leg-sl-reentry-modes ; https://www.quantsapp.com/backtesting/strategies/straddle-leg-sl-midday-reentry-if-both-stopped ; https://www.quantsapp.com/backtesting/strategies/atm-straddle-margin-pct-profit-ladder

### C4. Staggered multi-entry straddles (time diversification)

- Rules: sell one ATM straddle at each of 09:40, 09:50, 10:10, 10:30 (each at the ATM of that moment). Each leg of each tranche has its own 30% stop. Exit all at 15:15.
- Reported QS 2025-26 (4 lots a day): 984 trades, win 64%, gross +Rs 3,05,560, PF 1.35, max DD Rs 78,433; net* +Rs 1,02,470 with DD Rs 1,31,629. October and December made Rs 2.09 lakh of the total; June lost Rs 45,037.
- Feasibility: NO (four naked straddles, about Rs 8.5 lakh margin).
- Source: https://www.quantsapp.com/backtesting/strategies/staggered-multi-entry-atm-straddle

### C5. Intraday short strangle with leg stops (OTM by points, delta or premium)

- Rules: 09:20 (or 09:25, 10:00) sell one OTM call and one OTM put, nearest weekly; stop per leg; exit 15:06-15:20. Strike selection in sources: ATM +/- 50 points; 0.15 delta; cheapest option with premium at least Rs 55; option priced nearest 40% of the ATM premium; premium Rs 40-60 or delta 0.15-0.20 (AlgoTest). Stops: 25-30% per leg (1.75x for the 40%-premium version; 40-60% in AlgoTest). Optional MTM stop Rs 2,000 and target Rs 1,500 per lot.
- Reported QS 2025-26: ATM +/- 50: gross +Rs 20,177, net* -Rs 24,538. 0.15 delta with MTM stops: gross +Rs 18,003 (win 62%, worst day -Rs 2,000), net* -Rs 10,321. Premium at least Rs 55: gross +Rs 13,171, net* -Rs 14,295. 40% of ATM premium at 10:00: gross +Rs 28,821 (PF 1.24), net* -Rs 2,257.
- Finding: further OTM means less premium per order, so costs take a bigger share. None survived costs.
- Feasibility: NO (naked; expiry-day margin about Rs 1.4-1.5 lakh+ per the source author).
- Sources: https://www.quantsapp.com/backtesting/strategies/otm-points-offset-strangle-leg-sl ; https://www.quantsapp.com/backtesting/strategies/delta-target-short-strangle-leg-and-mtm-sl ; https://www.quantsapp.com/backtesting/strategies/premium-target-strangle-closest-premium ; https://www.quantsapp.com/backtesting/strategies/short-strangle-40pct-atm-premium-strikes-175x-leg-sl ; https://algotest.in/blog/how-to-backtest-options-trading-strategies-with-examples.md

### C6. Intraday iron fly (hedged 9:20 straddle, wings one straddle-width away)

- Rules: 09:35 read S = ATM call + ATM put premium. Sell ATM call and put; buy call at ATM + S and put at ATM - S (nearest strikes). Stop on each short leg at 30% above sale price (only that leg is bought back; wings stay). Exit 15:15. One a day. Generalised: shorts at ATM +/- m_short x S, wings at ATM +/- m_wing x S.
- Reported QS 2025-26: 246 trades, win 54%, gross +Rs 22,534, PF 1.08, max DD Rs 38,836, worst -Rs 10,391; net* -Rs 43,012 (eight orders a day).
- Other: Quintalmind says wings 200-300 points out cut margin 40-60%. TradingQnA shows the margin drop from Rs 2.36 lakh to Rs 0.94 lakh (lot 75).
- Feasibility: MARGINAL on margin (about Rs 80,000-90,000 on non-expiry days, about Rs 1.5 lakh on expiry Tuesday), but the evidence says costs exceed the gross edge by a factor of three at 1 lot. Not recommended as a daily system.
- Sources: https://www.quantsapp.com/backtesting/strategies/intraday-iron-condor-straddle-width-wings ; https://tradingqna.com/raw/179061 ; https://www.quintalmind.com/blog/time-based-straddle-strategy-nifty-options

### C7. Intraday delta-neutral adjustment: rolling ATM straddle, delta-band strangle

- Rules (rolling straddle): 10:00 sell ATM straddle; reference = index level. Whenever the index is 0.4% or more from the reference, buy back both legs and sell a new ATM straddle; reset the reference. On the trigger for the third straddle, close and stay flat. Exit 15:15.
- Rules (delta-band strangle): 09:22 sell 0.30-delta call and put. Each minute compute net delta; if it exceeds the band, buy back the profitable short and re-sell that side at the strike whose delta matches the other short (cap 0.50, never crossing). Stop: loss of 30% of entry credit. Target: 60% of credit. Exit 15:11.
- Reported QS 2025-26: rolling: 487 straddles, win 52%, gross +Rs 69,322 (PF 1.26), net* +Rs 15,534, DD Rs 29,613. Delta-band: gross +Rs 5,434 (PF 1.03), net* -Rs 48,107. "Delta-breach recentred fly" gross -Rs 8,700; "breakout-rolled straddle ladder" gross +Rs 92,500 (details not opened).
- Failure mode: every adjustment locks in the loss of the move (short gamma) and adds four orders.
- Feasibility: NO (naked).
- Sources: https://www.quantsapp.com/backtesting/strategies/rolling-atm-straddle-spot-move-roll ; https://www.quantsapp.com/backtesting/strategies/delta-neutral-30d-strangle-net-delta-rebalance

### C8. Signal-timed intraday straddles (premium below VWAP, calmer-than-priced, skew filter, wait-and-trade, VIX-routed)

- VWAP cross: on 5-minute bars 09:20-15:00, when the combined ATM straddle premium closes below the VWAP of that combined premium, sell the straddle; exit on a close above VWAP; leg stop 50%, other to cost after one stop; up to 3 trades a day; exit 15:15. QS: 644 trades, win 36%, gross +Rs 69,397 (PF 1.36), net* -Rs 11,074.
- Calmer-than-priced: every 5 minutes compute forecast 1-hour move = 0.8 x sd(last N one-minute log returns) x sqrt(60) x price, and priced 1-hour move = ATM straddle x sqrt(60 / minutes left to expiry); sell when forecast/priced is below 0.9; exit when above 1.1, 40% target, breakeven after 15% gain, 15:15. QS: 325 trades, gross +Rs 50,218 (PF 1.22), net* -Rs 98.
- Skew filter: enter the first minute from 09:20 when ATM call and put premiums differ by 10% or less (relaxing to 20% by 09:30); 50% leg stop; exit 15:20. QS: gross +Rs 20,054, net* -Rs 16,149, DD Rs 60,015.
- Wait-and-trade: sell each 09:20-ATM leg only after it trades 10% below its 09:20 price; 25% stop; exit 15:15. QS: gross +Rs 6,562, net* -Rs 32,710.
- VIX-routed (entry time and point stops chosen by VIX regime): QS gross -Rs 20,635, net* -Rs 51,652.
- Finding: none of the timing filters produced a net-positive daily system.
- Feasibility: NO (naked).
- Sources: https://www.quantsapp.com/backtesting/strategies/straddle-premium-vwap-cross-sell ; https://www.quantsapp.com/backtesting/strategies/straddle-expected-move-vs-priced-move-filter ; https://www.quantsapp.com/backtesting/strategies/atm-straddle-skew-filter-decaying-threshold ; https://www.quantsapp.com/backtesting/strategies/wait-and-trade-momentum-short-straddle ; https://www.quantsapp.com/backtesting/strategies/vix-regime-routed-straddle-entry-time-points-sl

### C9. Afternoon (late-session) short straddle

- Rules: 150 minutes before the close sell ATM call and put, nearest weekly; 30% stop per leg; exit 30 minutes before the close. Expiry-day strangle mode: enter 75 minutes before the close.
- Reported QS 2025-26: 246 trades, win 66%, gross +Rs 38,378 (PF 1.35), DD Rs 30,957; net* +Rs 264. Quintalmind: 13:00 expiry-day straddle has a "75-80%" win rate on thin premium (claim, no data).
- Feasibility: NO (naked).
- Source: https://www.quantsapp.com/backtesting/strategies/afternoon-late-session-short-straddle-strangle

### C10. Expiry-day (0DTE) ATM straddle held from the open to settlement (baseline)

- Rules: on the weekly expiry day sell the ATM straddle at the 09:15 open (strike = open rounded to the grid), hold the fixed strike to settlement, no stop. Payoff = premium - |settlement - strike|.
- Reported (Quintalmind, 148 Nifty weekly expiries, Jul 2023-May 2026, 1-second spot plus minute-level ATM chain, gross of costs): average entry premium 144 points; mean P&L +27 points (median +41); win rate 69%; average win +80, average loss -91; worst -290; 5th percentile -159; only about 19% of premium kept although the rolling ATM straddle "decays 86%". Expiry-day move: mean -12, median -23 points, sd 153 points (0.64%), worst -575, best +450. Strangle survival, settlement versus intraday touch: +/-150 points 72% versus 50%; +/-200 84% versus 66%; +/-300 94% versus 89%. Gaps: 68% of expiry gaps fill, median 12 minutes; gaps above 0.5% fill only 25% (trend-day warning). Rolling straddle as % of open: 82% at 09:30, 58% at 12:00, 40% at 14:00, 19% at 15:00.
- In rupees at lot 65 (derived): +27 points is about Rs 1,755 per expiry gross, less about Rs 135 costs and STT on any ITM leg; worst about -Rs 18,850.
- Failure modes: tail days; pin risk and settlement-window distortions (Jane Street; 13 Aug 2026 Sensex); STT of 0.15% of intrinsic on ITM expiry, so close before settlement.
- Feasibility: NO naked (about Rs 2.8 lakh on expiry day). An iron fly version needs about Rs 1.45-1.55 lakh: effectively the whole account, no buffer.
- Source: https://www.quintalmind.com/blog/nifty-expiry-day-deep-dive

### C11. Expiry-day hedged "stacking" straddle with VIX-sized steps

- Rules: expiry day only, 09:30: sell ATM call and put of the expiring weekly and buy call and put 500 points away. Each time ATM moves a full step (50 points when the previous India VIX close is below a threshold, else 100), sell another ATM straddle with its own +/-500 hedges. Each short leg has a stop at 2.25x its sale price. A stopped leg is re-sold once if it returns to its first sale price and is above Rs 5. At 15:17 close everything except shorts worth Rs 5 or less, which expire.
- Reported QS 2025-26: 52 expiry days, win 69%, gross +Rs 1,70,091, PF 3.04, max DD Rs 14,568, worst -Rs 11,628; net* +Rs 1,17,681. Caveats from Quantsapp: last-traded-price fills on expiry-day options flatter the result; stacking on a trend day multiplies short gamma.
- Feasibility: NO. Each stacked unit adds two short legs carrying 4% exposure plus 4% expiry ELM; three units need about Rs 4-4.5 lakh.
- Source: https://www.quantsapp.com/backtesting/strategies/expiry-day-hedged-straddle-atm-roll-vix-step

### C12. Expiry-day opening-range iron condor

- Rules: expiry day only. Conditions: the day opened inside the previous session's high-low range, and the weekly put/call open-interest ratio at entry is within a neutral band. At 09:45 take the first 30 minutes' high and low. Sell call at (high rounded to strike step) + 50; buy call 100 above it; sell put at (low rounded) - 50; buy put 100 below it. Target: 60% of credit captured. No stop (wings cap loss). Exit 14:30.
- Reported QS 2025-26: 25 trades, win 80%, gross +Rs 14,308, PF 3.4, max DD and worst trade -Rs 2,554; net* +Rs 10,037.
- Related: expiry-day OI-writer-follow single-leg selling: 66 trades, win 71%, gross +Rs 39,928, net* +Rs 35,055 (naked; not feasible). Expiry midday OTM call credit spread (11:00, spot +175, 50 wide): gross -Rs 1,695, net* -Rs 6,348.
- Feasibility: MARGINAL. Two short legs on expiry day carry 8% of notional in exposure plus ELM (about Rs 1.3 lakh) plus small SPAN: about Rs 1.35-1.45 lakh, nearly the whole account for about Rs 10,000 a year. Small sample (25 trades).
- Sources: https://www.quantsapp.com/backtesting/strategies/expiry-day-morning-range-iron-condor ; https://www.quantsapp.com/backtesting/strategies/expiry-day-oi-change-writer-follow-sell ; https://www.quantsapp.com/backtesting/strategies/expiry-day-midday-otm-call-credit-spread

### C13. Expiry-day far-OTM "penny" selling (Rs 1 options, last-30-minute sell)

- Rules A: expiry day 09:30 sell the OTM call and put priced closest to Rs 1; stop when a leg doubles; hold to expiry. Rules B: 30 minutes before the close sell the first call at least 1% above and the first put at least 1% below the forward; stop 2x; hold to the last print.
- Reported QS 2025-26: A: 52 trades, 96% win, gross +Rs 6,299, net* +Rs 1,563 (about Rs 30 per expiry). B: 96% win, gross +Rs 2,143, net* -Rs 2,604, with only 10% of trades profitable after costs.
- Verdict: negative. A near-certain small gain that costs more to collect than it pays, with full naked expiry-day margin and gap risk.
- Feasibility: NO.
- Sources: https://www.quantsapp.com/backtesting/strategies/expiry-day-sell-rs1-far-otm-sl-2x ; https://www.quantsapp.com/backtesting/strategies/expiry-day-last-30min-otm-sell-1pct-band

### C14. Pre-expiry (1 DTE, overnight) strangle beyond the open-interest walls

- Rules: 15:00 on the session before the weekly expiry. Resistance = call strike with the most open interest; support = put strike with the most open interest (that expiry). Sell the call at the resistance strike and the put one strike below the support strike. Skip if the call is not above the forward or the put not below it. Stop: both legs together cost 2x the credit. Otherwise hold to the expiry close.
- Variant: "regime" version sells ATM straddle if neutral, skewed strangle if bullish or bearish.
- Reported QS 2025-26: 45 trades, win 73%, gross +Rs 51,956, PF 1.75, max DD Rs 30,277, worst -Rs 18,232; net* +Rs 46,436; 10 of 12 months positive. Regime version: gross +Rs 35,348, net* +Rs 29,780, but one February trade lost Rs 60,993 and DD was Rs 76,255.
- Why it might work: it holds the overnight interval where the academic evidence says the premium sits, with the fastest theta, and only one trade a week (low cost share).
- Feasibility: NO as written (naked, held through expiry day, about Rs 2.8 lakh). A winged version (buy wings 150-300 points beyond each short; iron-condor margin about Rs 85,000 overnight, about Rs 1.5 lakh on expiry day) is the natural small-account test and is untested.
- Sources: https://www.quantsapp.com/backtesting/strategies/pre-expiry-strangle-beyond-support-resistance-2x-sl ; https://www.quantsapp.com/backtesting/strategies/pre-expiry-regime-straddle-or-skewed-strangle

### C15. Weekly iron condor (the core defined-risk positional structure)

- Rules, version A (1.5 SD): at 15:25 three trading sessions before the weekly expiry, with F = that expiry's put-call-parity forward and IV = mean ATM call/put IV: d = 1.5 x IV x sqrt(3/252). Short put = F x exp(-d) rounded down; short call = F x exp(+d) rounded up; wings 2% of F beyond each short. At 15:25 on each later day before expiry day, close everything if cost-to-close is at least 3x the entry credit. Otherwise hold to expiry.
- Version B (percent OTM): 09:20 on the first session after the previous weekly expiry, on the new nearest weekly (1-7 days out): sell put nearest spot x 0.98 and call nearest spot x 1.02; wings 150 points; skip if net credit is below a minimum. Target 50% of credit; stop when the loss reaches 1.5x credit; else exit 15:15 on expiry day.
- Version C (max-pain centred): 10:00 three sessions before expiry: short strikes at max pain +/- 200, wings 200 further; if spot crosses a short strike close that side; exit 15:15 on expiry day.
- Version D (naive): 15:00 two sessions before expiry: shorts ATM +/- 3 strikes, wings ATM +/- 4 strikes, no stop, exit 15:15 expiry day.
- AlgoTest's generic template: shorts 200-300 points from spot, stop 1.5-2x premium, exit at 70-80% of credit or on expiry afternoon.
- Reported QS 2025-26:
  - A: 50 trades, win 86%, gross +Rs 21,695, PF 1.46, max DD Rs 25,093, worst week -Rs 22,379; net* +Rs 12,836. Average win Rs 1,595 against average loss Rs 6,700. The source itself calls the edge marginal ("best of 3 rules chosen on train"; "the 3x stop's benefit came from 2 of 194 trades").
  - B: 53 trades, win 85%, gross +Rs 26,215, PF 2.28, max DD Rs 6,669, worst -Rs 4,166; net* +Rs 14,223 (PF 1.62). Parameters came from a sweep on the same history.
  - C: 34 trades, win 62%, gross +Rs 24,948, PF 2.65, DD Rs 8,710; net* +Rs 18,150.
  - D: 52 trades, win 38%, gross -Rs 19,152, PF 0.59; net* -Rs 29,648. One-strike wings give a tiny credit against eight orders.
  - 2-DTE condor with "move untested side": gross +Rs 2,010, net* -Rs 21,156.
- Other evidence: a Stockmock-style Bank Nifty test for 2017-2020 found the iron condor lost money after costs while the naked strangle made money (unverified: snippet only). US studies report 60-80% win rates and lower Sharpe for weekly than 30-45 DTE condors (unverified: snippet only).
- Costs: 8 orders a week, about Rs 235 with statutory, about Rs 12,000 a year: manageable relative to the daily systems.
- Failure modes: one bad week costs 4-14 good weeks; weekend gap inside the hold now that expiry is Tuesday; expiry-day margin jump; thin far-OTM wings.
- Feasibility: MARGINAL. One lot only. Margin about Rs 80,000-90,000 until the day before expiry. Holding into expiry Tuesday raises it to about Rs 1.45-1.55 lakh, so either exit on Monday at 15:15 (forgoing the last and fastest decay) or run with zero buffer. Net* of Rs 12,000-18,000 a year is 8-12% on Rs 1.5 lakh before statutory charges and tax, with a possible -15% week.
- Sources: https://www.quantsapp.com/backtesting/strategies/nifty-weekly-iron-condor-1p5sd-3dte-3x-stop ; https://www.quantsapp.com/backtesting/strategies/weekly-iron-condor-pct-otm-tp-sl-credit-multiple ; https://www.quantsapp.com/backtesting/strategies/max-pain-centred-weekly-iron-condor ; https://www.quantsapp.com/backtesting/strategies/time-based-weekly-iron-condor-2dte-1500-to-expiry-1515 ; https://www.quantsapp.com/backtesting/strategies/weekly-iron-condor-2dte-350pt-shorts-move-untested ; https://algotest.in/blog/how-to-backtest-options-trading-strategies-with-examples.md

### C16. Weekly iron condor with "roll the untested side" adjustments (condor to iron fly)

- Rules: 09:20 on the first trading day of each weekly cycle (at least 3 days left): sell about 0.16-delta call and put, buy wings 200 points beyond. Each minute: when a short ("tested") trades at 2x its reference premium, buy back the other short and its wing and re-sell that side at the strike whose premium is closest to the tested short's current premium, never past the tested strike, with a new wing 200 beyond. Reference resets at each roll. When the rolled short reaches the tested strike the position is an iron fly: no more rolls; close everything if the underlying goes more than one strike beyond the fly strike; else exit 15:15 on expiry day.
- Reported QS 2025-26: 53 trades, win 55%, gross +Rs 32,045, PF 1.42, max DD Rs 26,433, worst -Rs 6,438; net* +Rs 12,668. No cost accounting in any original source; each roll is four more fills.
- A site reports a Bank Nifty study in which the raw condor was about breakeven and this adjustment added about Rs 22,400 per lot over 52 "weekly" expiries Mar 2025-Mar 2026 (unverified: snippet only; Bank Nifty has had no weekly expiry since Nov 2024, so the claim is suspect).
- Feasibility: MARGINAL (same margin as C15; needs intraday monitoring).
- Source: https://www.quantsapp.com/backtesting/strategies/iron-condor-roll-untested-at-2x-then-iron-fly

### C17. Weekly naked short strangle (ATR-distance, deep OTM with shift)

- Rules A (ATR): 11:15 on the first session after the previous weekly expiry: sell call at ATM + 1.25 x weekly ATR and put at ATM - 1.25 x weekly ATR (Wilder ATR on completed weekly bars of the near-month future; rounded outward; never inside 0.05 delta). Stop: strangle costs 2.5x the credit (3x if India VIX is above 18). Hold to the expiry-day last print.
- Rules B (deep OTM with shift): 09:30 first session of the weekly cycle sell 0.10-delta call and put; combined stop at 1.8x credit; on a stop, re-sell 0.10-delta strikes ("shift out"); exit 15:15 expiry day.
- Reported QS 2025-26: A: 51 trades, win 82%, gross +Rs 31,608, PF 3.00, DD Rs 3,507; net* +Rs 27,013. B: 83 positions, win 58%, gross -Rs 1,680, net* -Rs 8,995, worst trade -Rs 43,218 (February), DD Rs 69,059.
- Multibagg summary of forum backtests: 45-DTE one-SD strangles were better than shorter ones when held to expiry; exiting 15 days before expiry reduced average and maximum loss (gamma risk); EOD-data backtests understate intraday adverse moves.
- Feasibility: NO (naked; about Rs 2.1 lakh and more on expiry day).
- Sources: https://www.quantsapp.com/backtesting/strategies/weekly-atr-multiple-short-strangle-premium-multiple-sl ; https://www.quantsapp.com/backtesting/strategies/weekly-deep-otm-01delta-strangle-combined-sl-shift-out ; https://www.multibagg.ai/market-pulse/articles/bank-nifty-short-strangle-backtests-cmob7yw87rvgsph0j6sq82xl0

### C18. Monthly 45-DTE short straddle or strangle, managed at 21 DTE (tastytrade rules), with India VIX percentile filter

- Rules (Zerodha test): Nifty monthly expiry only. Enter 45 calendar days before expiry at 15:15: sell ATM call and put, 1 lot each (variants: 30-delta strangle, 16-delta strangle). Exit at the first of: combined premium falls to 50% of credit (target); combined premium reaches 200% of credit (stop); 21 calendar days before expiry (time stop). Target and stop are checked at seven hourly points a day, not continuously. Filter: India VIX percentile rank against the prior 252 sessions at entry; trade only above the 25th, 50th or 75th percentile.
- Reported (Zerodha "In The Money", Jan 2019-Jun 2026, net of brokerage, STT and statutory charges, in points; six trades dropped for unclean data): straddle win rate about 70%; five of seven full years positive (2019 and 2023 negative); best trade the March 2020 cycle; worst the February 2026 cycle, which lost over 1,000 points despite the stop (gapped through) and is the whole of the maximum drawdown. Stops hit 4 times for the straddle against 12 for the 30-delta strangle; average P&L per trade of the straddle about double the 30-delta strangle; 16-delta strangle averaged only 7.3 points a trade ("not worth it"). VIX filter: win rate rises with each percentile level; above the 75th percentile about 86% win, no stop hits, about 20 trades, and years with zero trades; strangles approach 85% win at the 75th percentile. Position-sizing advice: one lot is Rs 16 lakh of notional; margin about Rs 3 lakh; keep leverage to about 1.5x, that is about Rs 11 lakh of capital per lot.
- QS 2025-26: straddle (stop at 100% loss of credit): 13 trades, gross -Rs 29,776, PF 0.81, max DD Rs 1,14,865, worst -Rs 62,813 (March 2026); net* -Rs 40,391. 16-delta strangle with one roll: 13 trades, win 85%, gross +Rs 8,298, DD Rs 55,286, worst -Rs 33,407. 45-DTE iron condor (0.30-delta shorts, 0.16-delta wings, 50% target, 100% stop, exit 15 DTE): gross -Rs 5,318, net* -Rs 10,012.
- Caveat: the 45/21/50% rules come from US research; Nifty second- and third-month options are thinner.
- Feasibility: NO for straddle or strangle (margin about Rs 3 lakh; Zerodha's own sizing implies Rs 11 lakh). The condor version fits on margin (about Rs 85,000, never held on expiry day) but lost money in 2025-26.
- Sources: https://inthemoneybyzerodha.substack.com/p/we-backtested-the-famous-45-dte-strategy ; https://www.quantsapp.com/backtesting/strategies/monthly-short-straddle-45dte-50pt-21dte ; https://www.quantsapp.com/backtesting/strategies/monthly-short-strangle-16d-45dte-manage-21dte-50pct ; https://www.quantsapp.com/backtesting/strategies/monthly-iron-condor-45dte-30d-short-16d-wings-exit-15dte

### C19. Monthly strangle or condor at the India-VIX-implied one-sigma move

- Rules (strangle): at 15:15 on the first session with 15 or fewer (and at least 3) calendar days to the monthly expiry: move = spot x VIX/100 x sqrt(days left/365), VIX = previous close. Sell the first call strike at or above future + move and the first put strike at or below future - move. Hold to 15:15 on expiry day. No stop by default.
- Rules (condor): 09:30 on the first session of each monthly series: move = VIX/100/sqrt(12); sell call nearest spot x (1 + move), put nearest spot x (1 - move); buy wings 300 points beyond; exit 15:15 on monthly expiry day; no stop.
- Reported QS 2025-26: strangle: 12 trades, 11 wins, gross +Rs 74,419, net* +Rs 73,344, worst -Rs 371; "twelve trades in a year with no sharp break through either strike, and no stop". Condor: 13 trades, win 69%, gross -Rs 35,641, net* -Rs 39,299; four losses averaged Rs 16,787 against wins of Rs 3,501.
- A ResearchGate paper (2015-2025) reports monthly Nifty closes staying within the VIX-implied range (unverified: snippet only).
- The contrast between the two is the lesson: same idea, different entry day and a full-month hold, opposite result. Twelve trades prove nothing.
- Feasibility: strangle NO; condor MARGINAL on margin, negative on evidence.
- Sources: https://www.quantsapp.com/backtesting/strategies/monthly-short-strangle-vix-implied-move-strikes ; https://www.quantsapp.com/backtesting/strategies/monthly-iron-condor-vix-sqrt12-bounds

### C20. VRP-gated premium selling (sell only when implied is rich: IV minus realised, IV percentile)

- Rules A (IV-RV gap): each day at 15:15 compute gap = ATM IV of the nearest monthly with at least 5 days left (mean of ATM call and put IV) minus 21-day close-to-close realised volatility of the future, annualised. If flat and gap is at least +5 vol points: sell ATM call and put and buy about 0.10-delta wings. Stop: structure costs 1.5x the net credit. Exit when gap is zero or less (daily check), after 10 trading days, or 2 trading days before expiry. (Mirror: gap at most -5, buy the straddle.)
- Rules B (IV percentile): at 15:15, if ATM IV percentile (share of prior readings below today's, up to a one-year lookback) is at least 80 and flat: sell 0.16-delta call and put on the nearest monthly with at least 5 days left (optionally buy wings). Target 50% of credit; stop at a loss of 2x credit; exit one trading day before expiry.
- Rules C: the Zerodha VIX-percentile filter in C18.
- Reported QS 2025-26: A: 12 trades (all Feb-Sep 2026), win 58%, gross +Rs 47,942, PF 1.81, DD Rs 27,796, worst -Rs 19,152; net* +Rs 45,472; March 2026 alone made Rs 56,449. B: 14 trades, win 86%, gross +Rs 22,497, PF 1.55, worst -Rs 28,291; net* +Rs 24,456.
- Negative related results: selling the "rich side" when put skew is at its 90th percentile (0.25-delta put, 0.10-delta wing): 11 trades, all in Mar-Apr 2026, gross -Rs 31,811; "the expensive puts proved justified". VIX regime playbook switch: gross -Rs 32,500.
- Why it might work: variance-swap returns are forecastable from past continuous variance (Sankar et al. 2020); few trades mean a low cost share; exits before expiry avoid the ELM.
- Failure modes: implied is high for a reason (March 2026); small samples; the percentile lookback changes the signal a lot.
- Feasibility: MARGINAL. With wings the margin is about Rs 80,000-90,000 and positions exit before expiry day. One lot.
- Sources: https://www.quantsapp.com/backtesting/strategies/vrp-atm-iv-minus-realised-vol-gap ; https://www.quantsapp.com/backtesting/strategies/ivp-ivr-gated-short-strangle ; https://www.quantsapp.com/backtesting/strategies/put-skew-extreme-sell-rich-side ; https://www.openalgo.in/quant/vix-and-vrp ; https://inthemoneybyzerodha.substack.com/p/we-backtested-the-famous-45-dte-strategy

### C21. Overnight (close-to-open) short straddle: the day-night asymmetry

- Rules: every trading day, 5 minutes before the close, sell the ATM call and put of the nearest weekly that does not expire today (optionally skip when it expires next session). Buy both back at 09:20 next session. No stop, no target.
- Academic basis: Bhat, Pandey and Rao (2024): overnight short Nifty option returns positive and significant, intraday negative.
- Reported QS 2025-26: 246 nights, win 64%, gross +Rs 24,344, PF 1.10, max DD Rs 56,693, worst night -Rs 37,573; net* -Rs 3,372 (PF 0.99). "The paper itself finds the edge gone after costs." Overnight iron condor (ATM +/-4 and +/-6 strikes, 15:15 to 15:15): gross -Rs 2,629, net* -Rs 40,543. Overnight 0.20-delta credit spread on the richer-IV side (15:20 to 09:20): gross -Rs 9,066, net* -Rs 32,969.
- Failure modes: event nights (Budget, elections, global shocks); wide spreads at the close and open.
- Feasibility: NO naked. Winged version fits on margin but the condor form lost money.
- Sources: https://ideas.repec.org/a/wly/jfutmk/v44y2024i8p1320-1337.html ; https://www.quantsapp.com/backtesting/strategies/overnight-short-options-close-to-open ; https://www.quantsapp.com/backtesting/strategies/btst-overnight-iron-condor-4-6-strikes-1515-to-1515 ; https://www.quantsapp.com/backtesting/strategies/overnight-credit-spread-1520-0920

### C22. Delta-hedged short straddle (futures hedge; the academic way to isolate the premium)

- Rules: 15:00 three sessions before the weekly expiry sell ATM call and put (4 lots each, because a 1-lot straddle's delta never exceeds one futures lot). Every 5 minutes compute net delta (options plus futures held); when it is more than one futures lot from zero, trade near-month futures back to the nearest whole lot. Stop: position down 50% of the credit. Exit 15:15 on expiry day. Academic form: daily re-hedge, hold to expiry.
- Reported QS 2025-26: 52 trades, win 71%, gross +Rs 90,806, PF 1.16, max DD Rs 3,90,930, worst trade -Rs 3,28,932 (February 2026); net* -Rs 9,040. The opposite trade (long straddle gamma scalp) lost Rs 2,66,256 gross and Rs 5,31,751 net*: costs sink both sides.
- Academic: gross delta-hedged short index option returns are positive in the US (Israelov and Tummala 1996-2015); in India variance risk is priced (Sankar et al.) and short-option returns are positive overnight (Bhat et al.). Pillai reports about -44% a year net on margin for Nifty monthlies 2015-2025 (unverified: snippet only).
- Feasibility: NO (futures plus naked options, several lots).
- Sources: https://www.quantsapp.com/backtesting/strategies/short-straddle-futures-delta-hedge-theta-harvest ; https://www.quantsapp.com/backtesting/strategies/long-straddle-gamma-scalp-futures-75-delta-band ; https://www.cxoadvisory.com/equity-options/best-index-options-to-sell ; https://econpapers.repec.org/RePEc:eee:reveco:v:70:y:2020:i:c:p:321-334

### C23. Directional credit spreads by trend regime (bull put / bear call)

- Rules A (daily regime): at 15:15 when flat. Gate: India VIX rank over a lookback above a floor. Regime from the previous close: ADX(14) above 20 means trend, direction from Supertrend(10,3); otherwise range. Uptrend: sell the OTM put nearest 0.175 delta (not on an open-interest wall) and buy the put 4 strikes lower. Downtrend: mirror call spread. Range with a high "range score" (max-pain proximity, PCR balance, OI concentration): both spreads (iron condor). Weekly expiry with 5-9 days left. Target 50% of credit; stop at a loss equal to 100% of credit; exit 15:15 one session before expiry.
- Rules B (intraday flip): Supertrend(80, 3.6) on 5-minute futures bars with ADX at least 30; bullish flip: sell the put one strike in the money and buy the put 50 points lower; bearish: mirror; exit on the opposite flip, at 95% of credit (then roll to the next weekly), or 15:15 on expiry day.
- Rules C (intraday Supertrend selling): from 09:20 on 5-minute bars sell the option at the strike nearest the Supertrend(10,3) line on the trend side, hedge 900 points away; exit on a touch of the line, a 50% premium stop, or 15:15; up to 3 runs a day.
- Rules D (daily Supertrend + Bollinger naked write): the session after a daily Supertrend(10,2) flip sell the first strike beyond the Bollinger band on the trend side, monthly with at least 10 days; stop when premium doubles; exit on the opposite flip or a session before expiry.
- Reported QS 2025-26: A: 60 trades, win 70%, gross +Rs 5 (PF 1.00), net* -Rs 44,361 ("the classic credit-spread trap": 42 targets averaging Rs 1,015 against 18 losers averaging Rs 2,368). B: 86 trades, win 29%, gross +Rs 777, net* -Rs 13,081. C: 586 runs, gross +Rs 45,838 (PF 1.15), net* -Rs 9,341. D: 14 trades, 12 wins, gross +Rs 47,633, net* +Rs 46,615 (naked, tiny sample).
- Feasibility: YES on margin (one spread about Rs 42,000-55,000, exits before expiry day). Evidence for A-C is flat to negative after costs; D is not feasible (naked).
- Sources: https://www.quantsapp.com/backtesting/strategies/regime-driven-credit-spread-supertrend-adx-ivrank ; https://www.quantsapp.com/backtesting/strategies/supertrend-adx-weekly-credit-spread-roll ; https://www.quantsapp.com/backtesting/strategies/directional-option-selling-supertrend-martingale ; https://www.quantsapp.com/backtesting/strategies/daily-supertrend-bb-outside-band-option-write

### C24. Systematic put-write (PUT-index style), as a put credit spread for a small account

- Rules (classic): the session after each monthly expiry sell one ATM (or 2% OTM) Nifty put on the new monthly; hold to expiry; repeat. Cash-secured in the index version. Small-account form: also buy a put 3-5% lower (bull put spread), exit the day before expiry.
- Filtered variant tested: monthly put write on a 5/10 EMA bullish crossover with IV percentile above 50, 80% target, 15-day exit.
- Evidence: strong academic support in the US for selling index puts and straddles (Coval-Shumway; Bondarenko; Israelov-Tummala: puts beat calls, short maturities beat long; AQR "Embracing Downside Risk"). Quantpedia's reference strategy: 1986-1995, 1.94% a month at 5% premium exposure with a 15% OTM crash put, Sharpe about 1.16. India: Pillai finds the 0.98-moneyness put-write net negative over 2015-2025 with a worst month of -18.3% of margin (unverified: snippet only). QS 2025-26 EMA-filtered put write: 5 trades, gross -Rs 5,940, net* -Rs 7,240.
- Related (not feasible): monthly covered call on futures and the futures "wheel" in C28 lost heavily in 2025-26.
- Feasibility: MARGINAL. Naked put about Rs 1.3-2 lakh: no. Spread: yes on margin, but the bought put removes much of the premium.
- Sources: https://quantpedia.com/strategies/volatility-risk-premium-effect ; https://www.aqr.com/-/media/AQR/Documents/Journal-Articles/JoAI-Embracing-Downside-Risk.pdf?sc_lang=en ; https://www.cxoadvisory.com/equity-options/best-index-options-to-sell ; https://www.quantsapp.com/backtesting/strategies/monthly-put-write-ema-cross-ivp50-15day-exit

### C25. Calendar, double calendar and diagonal spreads

- Double calendar (weekly): 09:31 on the session after a weekly expiry, only if the previous India VIX close is between 10 and 13.5. Sell 0.15-delta call and put of the current weekly; buy the next-weekly call and put whose prices are closest to the sold ones. Liquidity screen on each leg (two-sided quote, spread and last-price gap limits). Target: profit of 1.5% of margin used (assumed Rs 60,000, so Rs 900). Stop: loss of 2% of margin (Rs 1,200). Exit 15:15 on the near expiry day.
- IV-inversion calendar: at 15:15 when near-week ATM IV divided by next-week ATM IV is at least 1.10 and the near weekly has at least 2 sessions left: sell the near ATM straddle, buy the same-strike next-week straddle. Stop at 50% of debit; exit when the ratio is 1.00 or lower, or one session before near expiry.
- Double diagonal (monthly, mildly bullish): when the near monthly is 28 or fewer days away, sell the near put 1% below the forward and buy the next-month put 100 points lower; sell the near call 2% above and buy the next-month call at the same strike. Close put legs if the future falls 2.25%; call legs if it rises 3.75%; exit the day before near expiry.
- Reported QS 2025-26: double calendar: 29 trades, win 55%, gross -Rs 1,916, net* -Rs 11,263 (a Rs 900 target leaves no room for 8 orders). IV-inversion calendar: 3 trades, gross +Rs 2,200. Double diagonal: 13 trades, gross -Rs 23,387, net* -Rs 31,459. IV-regime structure selector (calendar when IV low, condor or strangle when high): 12 trades, gross +Rs 26,639.
- India-specific rule: the calendar margin benefit disappears on the expiry day of the near leg, so the short near leg is margined as naked plus ELM that day. Any calendar must be closed by the session before near expiry in a small account. The long far leg carries vega risk: a VIX fall hurts even if the index is still.
- Feasibility: MARGINAL (about Rs 60,000 off expiry day; cannot be held into the near expiry day). Evidence flat to negative.
- Sources: https://www.quantsapp.com/backtesting/strategies/weekly-double-calendar-vix-band-margin-pct-exits ; https://www.quantsapp.com/backtesting/strategies/iv-term-structure-inversion-calendar ; https://www.quantsapp.com/backtesting/strategies/mild-bullish-double-diagonal-call-calendar-put-diagonal ; https://www.quantsapp.com/backtesting/strategies/iv-regime-structure-selector-calendar-condor-strangle ; https://zerodha.com/z-connect/business-updates/sebis-new-rules-for-index-derivatives-heres-whats-changing

### C26. Jade lizard and big lizard

- Jade lizard: 09:30 on the first session 14 or fewer days before the monthly expiry: sell 0.20-delta put and 0.30-delta call; buy the call at the narrowest width (100-300 points) for which total credit is at least the call-spread width (no upside risk at expiry). Target 50% of credit; stop at a loss of 2x credit; exit 2 days before expiry.
- Big lizard: once per monthly series (at least 20 days left) sell ATM call and put; buy a call about 2% higher, stepped in until credit is at least the width; target 25% of credit; else hold to expiry.
- Reported QS 2025-26: jade: 5 trades, all winners, gross +Rs 21,967, net* +Rs 20,418 (the stop was never tested). Big lizard: 13 trades, 11 winners averaging Rs 11,962, two losers averaging Rs 1,22,055 (one -Rs 1,95,410 in March), gross -Rs 1,12,524, net* -Rs 1,74,884.
- Feasibility: NO (naked short put).
- Sources: https://www.quantsapp.com/backtesting/strategies/jade-lizard-nifty-credit-exceeds-call-width ; https://www.quantsapp.com/backtesting/strategies/big-lizard-short-straddle-long-otm-call

### C27. Ratio spreads, "Batman" and broken-wing butterflies

- Batman (intraday): 10:00 buy 1 ATM call and 1 ATM put; sell 3 calls three strikes above and 3 puts three strikes below. Stop: position down Rs 3,000 per base lot. After +Rs 2,000 exit if P&L falls to half its best. Exit 15:15.
- Front ratio call spread: 15:00 three sessions before weekly expiry buy 1 ATM call, sell 2 calls 150 points higher, buy 1 call one strike above them; stop if Nifty is above the upper breakeven; exit 15:15 expiry day.
- Credit broken-wing call butterfly: two sessions before expiry buy 1 call at K, sell 2 at K+200, buy 1 at K+500, shifting K out until there is a net credit; stop at 50% of maximum loss; exit 15:15 expiry day; skip event weeks and low IV.
- Reported QS 2025-26: Batman: 246 trades, win 68%, gross +Rs 51,217 (PF 1.24), net* -Rs 10,531 with DD Rs 42,259. Front ratio: 52 trades, win 33%, gross -Rs 52,004, net* -Rs 78,462 (one -Rs 37,050). BWB: 2 trades, gross -Rs 3,172.
- Feasibility: NO for Batman and ratios (net naked shorts). BWB is defined-risk and fits on margin but almost never qualifies.
- Sources: https://www.quantsapp.com/backtesting/strategies/intraday-batman-double-1x3-ratio-1000 ; https://www.quantsapp.com/backtesting/strategies/front-ratio-call-spread-1x2-convert-on-approach ; https://www.quantsapp.com/backtesting/strategies/weekly-broken-wing-call-butterfly-credit

### C28. Index covered call, futures wheel, poor man's covered call

- Covered call: first session of each monthly series buy 1 near-month Nifty future and sell the call at the first strike at or above future x 1.03; close both at 15:15 on monthly expiry; repeat.
- Wheel: sell puts for about 1% premium; when assigned, hold a long future and sell calls.
- Poor man's covered call: deep ITM long-dated call, sell weekly calls against it, 30% stop on the long call.
- Reported QS 2025-26 (a falling year: March 2026 down about 10.5%): covered call: 13 cycles, gross -Rs 2,87,716 (March alone -Rs 2,15,868). Wheel: gross -Rs 1,58,644 (three losers averaged Rs 1,17,521). PMCC: gross -Rs 90,966, net* -Rs 1,53,187.
- These are long-equity strategies with a thin premium cushion (Israelov and Nielsen make the same point for covered calls); 2025-26 shows the downside.
- Feasibility: NO (Angel One's lot-cut note puts the margin per Nifty contract at about Rs 1,77,000; Rs 16 lakh of delta on a Rs 1.5 lakh account).
- Sources: https://www.quantsapp.com/backtesting/strategies/covered-call-index-monthly-3pct-otm ; https://www.quantsapp.com/backtesting/strategies/index-wheel-1pct-premium-puts-calls-futures ; https://www.quantsapp.com/backtesting/strategies/poor-mans-covered-call-nifty-deep-itm-leap-weekly-short ; https://www.angelone.in/news/market-updates/nse-reduces-lot-sizes-in-nifty-and-bank-nifty-derivatives

### C29. Event IV-crush selling (RBI policy, Union Budget, election counting)

- Event-eve: 5 minutes before the close on the eve of an RBI policy day or Budget day sell the ATM straddle of the nearest expiry after the event and buy wings 3% away; stop at a loss of 50% of net credit; exit 10:45 on RBI day or 15:15 on Budget day.
- Budget-day intraday: 10:15 on Budget day sell ATM straddle, 20% stop per leg, exit 15:25.
- Election: sell the straddle on counting day after the result (the tested default was the opposite: long straddle into the count).
- Reported QS 2025-26: event-eve: 6 events, 2 winners, gross -Rs 19,594 (PF 0.09), net* -Rs 20,806. Budget day 1 Feb 2026: both legs stopped, -Rs 5,140. Long RBI-policy straddle (buy at the prior close, sell next morning) +Rs 15,200: the long side won in this sample. Budget-day Nifty ranges have been 0.8-4.9%.
- Tail reference: 4 June 2024 (election result): Nifty -5.93%, India VIX intraday high 31.71 (unverified: snippet only).
- Feasibility: MARGINAL on margin with wings; evidence negative and samples tiny. Most systems should instead skip event days.
- Sources: https://www.quantsapp.com/backtesting/strategies/event-eve-short-straddle-iv-crush ; https://www.quantsapp.com/backtesting/strategies/budget-day-intraday-short-straddle-leg-sl ; https://www.quantsapp.com/backtesting/strategies/election-result-event-vol-trade ; https://www.quantsapp.com/backtesting/strategies

---

## Part D. What fits in Rs 1.5 lakh

| Structure | Margin, normal day (lot 65, derived) | Margin on its expiry day | Fits? |
|---|---|---|---|
| Naked short straddle or strangle | about Rs 2.1-2.2 lakh | about Rs 2.8 lakh | No |
| Single naked short option | about Rs 1.25-2.0 lakh | + about Rs 32,000 | No (no buffer) |
| Iron fly / iron condor, 1 lot | about Rs 80,000-90,000 (NiftyWise says Rs 40,000-60,000) | about Rs 1.45-1.55 lakh | Marginal: 1 lot; exit before expiry day or run with zero buffer |
| Bull put / bear call spread, 1 lot | about Rs 42,000-55,000 | about Rs 75,000-87,000 | Yes, 1 lot any day; 2 lots off expiry day |
| Calendar / double calendar | about Rs 60,000 (Quantsapp) | benefit withdrawn: naked + ELM | Marginal: must exit before near expiry day |
| Ratio, Batman, jade lizard | naked-leg margin | more | No |
| Futures-based (covered call, wheel, delta hedge) | about Rs 1.77 lakh per contract (Angel One) | | No |

Compounding: size moves in whole lots. A second iron condor lot held to expiry needs about Rs 3 lakh; a second lot closed the day before expiry needs about Rs 1.8 lakh plus buffer. So "profits reinvested" does nothing until capital has grown 20-100%, and then risk doubles in one step. A mix (one condor plus one spread) is the only finer step.

Realistic return range from the evidence: the net-positive defined-risk systems made Rs 10,000-18,000 net* per lot per year in 2025-26, that is 7-12% on Rs 1.5 lakh before statutory charges and business-income tax, with single-week losses of Rs 4,000-22,000 (3-15% of the account).

---

## Part E. Tail-risk episodes

| Date | What happened | Effect on sellers | Verification |
|---|---|---|---|
| Mar 2020 (COVID) | Nifty -23.2% over four weeks after the VIX spike | "Destroyed many short straddle systems, drawdowns of 30-50% of capital" (Quintalmind); the March 2020 cycle was nevertheless the best trade of Zerodha's 45-DTE straddle because it was entered into the spike | Samco; Quintalmind; Zerodha |
| 5 Mar 2020 | VRP -64.5 points (realised far above implied) | Worst single reading of India VIX minus next-21-day realised | unverified: snippet only |
| 4 Jun 2024 (election result) | Nifty -5.93% on the day; India VIX intraday 31.71, below 15 a week later | Stops gapped; IV crush afterwards | unverified: snippet only |
| Apr 2025 (tariff shock) | Sharp VIX spike, then Nifty +12.5% in four weeks | Whipsaw both ways | Samco |
| Jan 2023-Mar 2025 | Alleged Bank Nifty expiry-day manipulation on 18 expiry days | Morning lift, afternoon reversal on expiry days: the exact shape that stops both legs | Oxford Business Law Blog |
| Late Feb-Mar 2026 (Iran-US-Israel conflict, oil above USD 110) | India VIX from 13.70 (27 Feb) to 23.36 (9 Mar) to about 26-27 (23 Mar); Nifty -10.51% in March, -13.76% year to date | QS: monthly 45-DTE straddle -Rs 62,813 in one cycle; breakeven-adjusted 2-lot straddle -Rs 1,85,510; big lizard -Rs 1,95,410; delta-hedged 4-lot straddle -Rs 3,28,932 in one February trade; Zerodha's worst trade (over 1,000 points) was the February 2026 cycle | mStock (opened); VIX path from snippets |
| 13 Aug 2026 (Sensex expiry, first weeks of CAS) | Three index spikes of 133-405 points within seconds in the closing auction; SEBI barred two entities | Settlement-price risk for anything held to expiry | Marketinsiders |

Pattern: losses arrive as gaps (overnight or event) and as trend months. Stops checked intraday or hourly did not contain the February 2026 loss.

---

## Source list (opened unless marked)

Regulation, contracts, costs
- https://zerodha.com/z-connect/business-updates/sebis-new-rules-for-index-derivatives-heres-whats-changing
- https://zerodha.com/z-connect/updates/changes-to-closing-auction-session-cas-from-december-7-2026
- https://support.zerodha.com/category/trading-and-markets/margins/margin-leverage-and-product-and-order-types/articles/additional-elm-for-index-expiry
- https://aliceblueonline.com/blog/sebi-new-fo-rules-2024-to-2026 (contains errors: Sensex expiry day, Bank Nifty and Midcap lot history)
- https://www.angelone.in/news/market-updates/nse-reduces-lot-sizes-in-nifty-and-bank-nifty-derivatives
- https://www.angelone.in/exchange-transaction-charges
- https://oga-prod.angelone.in/news/market-updates/what-s-changing-in-angel-one-s-smartapi-access-from-april-1-2026
- https://marketinsiders.in/2026/08/31/sebi-may-end-weekly-options-expiry-to-curb-risk/
- https://www.outlookmoney.com/news/sebi-to-float-consultation-paper-on-endin-futures-and-options-weekly-expiry-soon-tuhin-kanta-pandey
- https://niftywise.org/blog/how-much-margin-to-sell-nifty-options
- https://niftywise.org/blog/how-much-capital-do-you-need-for-nifty-options-trading
- https://blogs.law.ox.ac.uk/oblb/blog-post/2025/07/jane-street-and-expiry-day-trap-unpacking-sebis-crackdown-algorithmic
- https://www.mstock.com/articles/decoding-stock-market-crash-on-23-march-2026
- https://www.samco.in/knowledge-center/articles/nifty-rebounds-in-75-of-cases-after-extreme-india-vix-spikes-what-history-reveals/

Academic and research
- https://ideas.repec.org/a/wly/jfutmk/v44y2024i8p1320-1337.html (Bhat, Pandey, Rao 2024)
- https://econpapers.repec.org/RePEc:eee:reveco:v:70:y:2020:i:c:p:321-334 and https://researcher.manipal.edu/en/publications/dynamics-of-variance-risk-premium-evidence-from-india/ (Sankar, Ramachandran, Lukose 2020)
- https://nsearchives.nseindia.com/research/content/res_WorkingPaper9.pdf (NSE WP 9/2013)
- https://quantpedia.com/strategies/volatility-risk-premium-effect
- https://www.cxoadvisory.com/equity-options/best-index-options-to-sell
- https://www.aqr.com/-/media/AQR/Documents/Journal-Articles/JoAI-Embracing-Downside-Risk.pdf?sc_lang=en
- https://hulltactical.com/2026/07/08/0dte-options-tiny-edge-huge-distribution/
- https://arxiv.org/abs/2608.24786
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6876580 (NOT opened: HTTP 403; snippet only)
- https://www.sciencedirect.com/science/article/abs/pii/S1059056020301222 (NOT opened: HTTP 403)

Practitioner backtests
- https://www.quantsapp.com/backtesting/strategies and the strategy pages cited in Part C
- https://inthemoneybyzerodha.substack.com/p/we-backtested-the-famous-45-dte-strategy
- https://www.quintalmind.com/blog/nifty-expiry-day-deep-dive
- https://www.quintalmind.com/blog/time-based-straddle-strategy-nifty-options
- https://www.marketcalls.in/futures-and-options/is-the-920-straddle-no-more-working.html
- https://www.marketcalls.in/futures-and-options/how-the-9-20-intraday-straddlers-are-being-gamed.html
- https://algotest.in/blog/the-920-straddle-strategy-defined.md
- https://algotest.in/blog/how-to-backtest-options-trading-strategies-with-examples.md
- https://tradingqna.com/raw/179061 (thread 179061) and https://tradingqna.com/raw/88032 (thread 88032)
- https://www.openalgo.in/quant/vix-and-vrp
- https://www.multibagg.ai/market-pulse/articles/bank-nifty-short-strangle-backtests-cmob7yw87rvgsph0j6sq82xl0
- https://blog.openalgo.in/building-the-09-20-am-intraday-short-straddle-strategy-using-openalgo-gpt-af63c7b309ed (NOT opened: HTTP 403; snippet only)

---

## Negative or cautionary evidence

1. The premium is earned overnight; intraday short-option returns on Nifty are negative (Bhat, Pandey and Rao 2024). The most popular Indian retail systems are intraday.
2. Costs dominate at one lot. In QS 2025-26, of the roughly 30 daily intraday selling systems opened here, almost all were positive before costs and negative or flat after Rs 20 an order and slippage: 9:20 straddle +19,405 to -33,527; iron fly +22,534 to -43,012; OTM strangle +20,177 to -24,538; delta-neutral strangle +5,434 to -48,107; VWAP straddle +69,397 to -11,074; Batman +51,217 to -10,531. Statutory charges (STT at 0.15% since Apr 2026) are extra.
3. Net-of-cost academic backtest for India: every short-volatility strategy on Nifty monthlies 2015-2025 negative, tails rather than costs the main cause (Pillai, SSRN; unverified: snippet only; not peer reviewed).
4. Decay after popularity: Marketcalls documents the 9:20 straddle's edge fading by 2023 as it went viral, and stop-hunting of clustered SL-M orders. Quantsapp: five years of 9:20 results turn negative without the best 10% of days.
5. High win rates hide negative skew. Examples: big lizard 11 of 13 wins and -Rs 1.12 lakh; VIX condor 69% wins and -Rs 35,641; penny selling 96% wins and a loss after costs; regime credit spreads 70% wins and zero gross profit.
6. Stops are not protection against gaps. Zerodha's worst trade lost over 1,000 points "despite a stop"; backtests that fill stops at the trigger are optimistic; market and IOC orders are now barred for API algos, so a stop is a limit order that may not fill.
7. Hedging with wings turns unlimited loss into capped loss but in these tests usually also turned a small gross profit into a net loss, because it doubles the order count (iron fly, overnight condor, 2-DTE condor).
8. 0DTE: US evidence finds a premium but statistically insignificant mean returns for static rules (Vilkov). Indian expiry-day data: 86% "decay" becomes 19% of premium kept, and 34-50% of near strangles are touched intraday even when they expire worthless (Quintalmind).
9. Covered calls and wheels on the index lost Rs 1.6-2.9 lakh per lot in 2025-26; they are leveraged long positions.
10. Regulation is moving against the product: weekly expiries cut from six to two, lot value tripled, expiry-day ELM, STT on option sales raised from 0.10% to 0.15% in Apr 2026 (and, from memory, from 0.0625% to 0.10% in Oct 2024), algo restrictions, a new settlement method on 7 Dec 2026, and an open review of whether weekly expiries should exist.
11. Retail outcomes: 91-93% of individual F&O traders lose money (SEBI FY22-FY25).
12. Platform backtests published before 2025 mostly used Bank Nifty weeklies, lot sizes of 15-25, lower STT and five expiry days a week. Do not carry their numbers forward.
13. Vendor conflicts: AlgoTest, Stockmock, Quantman, Tradetron, Squareoff, NiftyWise and Quintalmind sell tools, bots or brokerage referrals. Several pages give win rates with no data. Quantsapp is the exception in showing after-cost numbers that are mostly unflattering.

## Open questions

1. Exact Angel One margin for a 1-lot Nifty iron condor, iron fly, credit spread and calendar on a normal day and on expiry day at lot 65. Sources disagree (Rs 15,000-30,000 for a spread and Rs 40,000-60,000 for a condor at NiftyWise; about Rs 45,000 and Rs 85,000 by my derivation). Query the SmartAPI margin calculator before fixing position sizes.
2. Does Angel One auto-square-off or reject short options on expiry day for accounts short of the extra ELM, and at what time? Not found.
3. Will SEBI end or thin weekly expiries? No decision found as of late Aug 2026. The consultation paper promised in Sep 2025 was not located.
4. How do results change after 7 Dec 2026 (settlement on 15:00-15:30 VWAP, expiring contracts stop at 15:30)? No data yet.
5. Pillai's SSRN paper: exact strategy definitions and numbers need reading in full; it is the only net-of-cost long-sample Indian study found.
6. Does any winged version of the two best-looking naked ideas survive costs: the pre-expiry OI-wall strangle (C14) and the VRP-gated straddle (C20)? Untested anywhere I could find.
7. Do weekly condor results hold over 2019-2025 with correct historical lot sizes and expiry days, and with exit on the day before expiry (the only version a Rs 1.5 lakh account can margin comfortably)?
8. Stop execution under the market-order ban: what limit buffer and non-fill rate are realistic for Nifty weekly options at 1 lot?
9. Sensex weekly options (Thursday, lot 20): liquidity, spreads and whether any of these results transfer. Not researched (search budget exhausted).
10. Long-run India VIX minus realised series (2008-2026) by regime, and whether the day-night split persists after 2020. Computable from daily index data; not found published.
11. Long-sample Indian platform backtests with numbers (AlgoTest, Stockmock, Opstra, Tradetron marketplace): the pages found were tutorials, images or marketing; none gave an auditable multi-year table.
