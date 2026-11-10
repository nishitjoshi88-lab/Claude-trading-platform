# Short-term mean reversion and swing trading: research findings

Researcher area: short-horizon reversal (RSI(2) and Connors-style systems, IBS, Bollinger reversion, down streaks, pullback-in-uptrend, weekly/monthly reversal, gap fade, panic bounce, index-ETF mean reversion).
Context: India, Rs 1,50,000 capital, Angel One (SmartAPI), fully automated, profits reinvested. Written 2026-11-10.

## 0. How this was produced, and what could not be checked

- About 25 web searches were run (academic, practitioner, Indian broker/news) before the shared search budget for this run was exhausted. After that, sources were read by opening known URLs directly with `fetch_text.py`. No search engine was queried by other means.
- Every number below comes from a page or PDF that was actually opened, unless it is tagged **(unverified: snippet only)** (seen only in a search-result summary) or **(unverified: not opened, general knowledge)**.
- Sources that could not be opened: ScienceDirect "Momentum, reversals and liquidity: Indian evidence" (HTTP 403); Emerald, Parthasarathy (2019) (HTTP 403); EFMA/CORE copies of de Groot, Huij and Zhou (HTTP 503/403; numbers taken from Quantpedia and CXO Advisory summaries, both opened); QuantifiedStrategies Substack posts and several "members only" rule boxes (paywalled); Price Action Lab critique of Turnaround Tuesday (paywalled, title only); IMFI 2023 Nifty 50 technical-rules paper (TLS error).
- Nearly all practitioner backtests are US index ETFs or US stocks, mostly without costs. Direct Indian evidence is thin and is called out strategy by strategy.

## 1. Definitions used in the rules

- `SMA(n)`: simple moving average of closes over n days.
- `RSI(n)`: Wilder RSI on closes. `Cutler RSI(n)`: same but with simple (not Wilder-smoothed) averages of up and down moves (Pagonidis uses Cutler's).
- `IBS = (Close - Low) / (High - Low)` for the day, range 0 to 1 (Pagonidis; QuantifiedStrategies; Alvarez calls it "closing range"). N-day closing range: `(Close - LowestLow_N) / (HighestHigh_N - LowestLow_N)`.
- `%b = (Close - LowerBB) / (UpperBB - LowerBB)`, Bollinger Bands = SMA(n) +/- k standard deviations.
- `Williams %R(n) = -100 * (HighestHigh_n - Close) / (HighestHigh_n - LowestLow_n)`.
- `ConnorsRSI(3,2,100) = [RSI(3) + RSI(Streak,2) + PercentRank(1-day ROC, 100)] / 3`, where Streak is the signed count of consecutive up (+) or down (-) closes, reset to 0 on an unchanged close (QuantifiedStrategies).
- `DV2` (Varadi oscillator, 2-period): rolling percent rank of a 2-day SMA of `Close / ((High+Low)/2)`. The percent-rank lookback is in an image on the source page; 252 days is the usual convention (lookback unverified).
- "Enter at close" means the signal is computed from the day's final bar and filled at (or seconds before) the close. "Enter next open" is the conservative alternative. Several sources show the difference is large (section 28).

## 2. India cost and structure facts that decide feasibility (2026)

Read from Angel One's pricing page (opened 2026-11-10) and Angel One's "Revised Pricing Schedule Effective November 17, 2025" notice:

| Item | Equity delivery | Equity intraday | Index/stock futures |
|---|---|---|---|
| Brokerage | lower of Rs 20 or 0.1% per executed order, minimum Rs 5 | lower of Rs 20 or 0.1%, minimum Rs 5 | Rs 20 per executed order |
| STT | 0.1% buy and sell | 0.025% sell | 0.05% sell (0.02% before 1 Apr 2026) |
| NSE transaction charge | 0.0030699% | 0.0030699% | 0.0018299% |
| Stamp duty (buy) | 0.015% | 0.003% | 0.002% |
| SEBI fee | Rs 10 per crore | same | same |
| GST | 18% on brokerage + transaction + SEBI | same | same |
| DP charge | Rs 20 + GST per ISIN per sell day | none | none |

Other: MTF interest 14.99% p.a. (about 0.041% per day); auto square-off charged as normal brokerage. Options STT is 0.15% of premium on sale from 1 Apr 2026.
ETF units: Groww's STT table (opened) lists "sale of equity-oriented mutual fund units (delivery) 0.001%". Equity ETFs are units of equity-oriented funds, so the delivery sell STT should be 0.001% and no buy-side STT. Confirm on the first contract note (medium confidence).

Round-trip cost at Angel One, computed from those rates (excludes bid-ask spread and slippage):

| Position size | Stock, delivery | Equity ETF, delivery | Stock/ETF, intraday |
|---|---|---|---|
| Rs 15,000 (10 slots) | Rs 92 = 0.62% | Rs 62 = 0.42% | Rs 41 = 0.27% |
| Rs 30,000 (5 slots) | Rs 138 = 0.46% | Rs 78 = 0.26% | Rs 58 = 0.19% |
| Rs 50,000 (3 slots) | Rs 182 = 0.36% | Rs 82 = 0.17% | Rs 65 = 0.13% |
| Rs 75,000 (2 slots) | Rs 238 = 0.32% | Rs 88 = 0.12% | Rs 74 = 0.10% |
| Rs 1,50,000 (1 slot) | Rs 405 = 0.27% | Rs 106 = 0.07% | Rs 100 = 0.07% |

One Nifty futures lot (lot size 65 per one 2026 practitioner page opened; not confirmed against an NSE circular) at index 25,000 is about Rs 16.25 lakh notional; round trip is about Rs 966 = 0.059% of notional = 0.64% of a Rs 1.5 lakh account. The same page puts margin for one Nifty lot at "roughly Rs 1.4 to 1.75 lakh" and Bank Nifty lot size at 30 with margin Rs 1.6 to 1.8 lakh. One lot therefore uses the whole account and a 1% index move is about 11% of capital.

Consequences for this research area:

1. A delivery swing trade in a single stock costs 0.27% to 0.62% round trip before spread. The best-documented US edges for stock-level RSI(2) portfolios are 0.36% to 0.45% average gross per trade (Quantitativo, Concretum). At 5 to 10 positions the Indian cost equals or exceeds the US gross edge. Stock-level short-term reversal is feasible only if the Indian edge per trade is clearly larger than in the US, or with 1 to 3 concentrated positions.
2. The same trade in an equity ETF costs 0.07% to 0.17% round trip at Rs 50,000 to 1,50,000. Index-ETF mean reversion (NIFTYBEES, BANKBEES, JUNIORBEES and other liquid ETFs) is the only version where costs are small relative to reported edges (0.3% to 1.2% per trade on SPY/QQQ).
3. Retail cannot carry a short position in the cash segment overnight (onetradejournal: "most retail traders cannot easily short stocks in the cash segment for multiple days"); shorts must be intraday or via futures. Every long-short academic reversal strategy reduces to its long (loser) leg, which carries full market beta. Share.Market's 25-year Indian RSI study also found short-only and long-short RSI rules lost money across all index universes.
4. Stocks outside F&O have daily price bands; a falling stock can lock at lower circuit with no exit. Capitalmind notes F&O and index stocks have no such limits. Mean-reversion universes should be restricted to F&O stocks or Nifty 100/200 members.
5. NSE's official close is a volume-weighted average of the last 30 minutes and there is a post-close session at the closing price **(unverified: not opened, general knowledge)**. "Buy at the close" backtests on official closes may not match what a market order at 15:25 to 15:29 gets. This needs to be measured, not assumed.
6. Tax treatment (delivery gains as short-term capital gains; intraday as speculative business income; F&O as business income) was not researched here; another area covers it.

## 3. Strategies

### 3.1 RSI(2) pullback in an uptrend, single index or ETF (Connors)

- Rules. Universe: one broad index ETF. Trend filter: Close > SMA(200). Entry: RSI(2) closes below 10 (stricter: below 5); buy at the close (Connors' preference) or next open. Exit: close above SMA(5) (Connors' S&P example), or RSI(2) > 65 to 80, or close > previous day's high (QuantifiedStrategies variant). Stop: none in the original; Connors reports stops hurt. Optional time stop 5 to 10 bars; optional 2 x ATR(10) catastrophic stop (QS suggestion, untested there). One position.
- Parameters in sources: RSI length 2 (StockCharts RSI(5) with 30/70 thresholds is the slower variant); entry 5 or 10; exit SMA5 / RSI2 > 65, 70, 80 / close > yesterday's high; filter SMA200 (optionally also SMA50).
- Instruments: NIFTYBEES, BANKBEES, JUNIORBEES or other liquid index ETFs; Nifty futures only above about Rs 5 lakh capital.
- Holding period: 1 to 7 trading days; QS: "most RSI 2 trades produce quick exits within 3-7 days".
- Reported performance. QuantifiedStrategies, SPY 1993 to about 2025: buy RSI2 < 10, sell RSI2 > 80: 0.9% average gain per trade, about 9% annual return, max drawdown 34%, invested 28% of the time. With SMA200 filter: 0.95% per trade, CAGR 6.8%, max drawdown 31%, invested 18%. Exit on close > yesterday's high, no trend filter: 0.5% per trade, win rate 76%, drawdown 15%. Cost treatment not stated for these three. StockCharts (Arthur Hill) RSI(5) 30/70 on SPY, QQQ, IJR, Dec 2000 to Dec 2016, next-open fills, $10 commission: average win rate 78% across 12 variants, exposure 20% to 35%, IJR best with more than 10% compound annual return. Alvarez, S&P 500 index 1957 to Nov 2023: a low RSI(2) (< 20) was followed by below-average next-day returns from 1957 to 1982, erratic 1983 to 1994, and above-average only from 1995 onward; the 5-day edge "has changed little since the mid-2000s". Backtrex Nasdaq 100, Oct 2016 to Oct 2026, RSI2 < 5: total +26.9% versus buy and hold +528% **(unverified: snippet only)**.
- India evidence. None found with numbers. Marketcalls (2008) reprints Connors' US stock statistics (1995 to mid-2006: stocks with RSI2 < 10 beat the benchmark by 0.06% at 1 day, 0.21% at 2 days, 0.50% at 1 week; RSI2 < 1 by 0.27%, 0.62%, 1.05%). onetradejournal's India page gives only illustrative examples.
- Cost and capacity. About 5 to 15 trades a year per instrument. In an ETF at Rs 75,000 to 1,50,000 the round trip is 0.07% to 0.12% against 0.5% to 0.95% reported gross per trade. Capacity is not a constraint.
- Failure modes. Prolonged bear markets and crashes (QS: win rates below 60% in 2008 and March 2020; "unfiltered RSI(2) trading during the 2022 bear market produced 15% losses"); no stop means occasional large losers; low exposure means low absolute CAGR; daily mean reversion in indices is a post-1995 regime in the US, not a law.
- Feasibility at Rs 1.5 lakh: yes in ETF form (low cost, one position, daily data, simple orders). The edge in Indian ETFs is unproven.
- Sources: https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; https://www.quantifiedstrategies.com/rsi-2-strategy/ ; https://alvarezquanttrading.com/blog/mean-reversion-vs-trend-following-through-the-years/ ; https://articles.stockcharts.com/article/articles-arthurhill-2016-12-systemtrader---testing-and-tweaking-an-rsi-mean-reversion-system-for-spy-qqq-and-ijr/ ; https://www.marketcalls.in/nifty-technicals/2-period-rsi-trading-systems-for-nifty.html ; https://onetradejournal.com/strategies/rsi-2-strategy ; https://www.cxoadvisory.com/?p=2679

### 3.2 RSI(2) stock portfolio with a position cap

- Rules (Concretum canonical version). Universe: index constituents, point-in-time. Entry: RSI(2) < 5 and Close < SMA(5); buy next day's open. Price exit: sell at next open after the first close above SMA(5). Time exit: sell at next open after 5 trading days. No stop.
- Rules (Alvarez portfolio version). Universe: Russell 3000 current and past members; price > $1; 20-day average traded value > $500,000; index (SPX) > SMA(200); stock > SMA(200); RSI(2) below a threshold between 0.5 and 5; rank candidates by 100-day historical volatility, high to low; maximum 10 positions; enter next open; exit next open after RSI(2) > 70.
- Selection when signals exceed slots: highest volatility first (Alvarez HV100, Quantitativo normalized ATR). Useful filters from Alvarez: skip stocks with a gap down of 5% or more in the last 10 days (in his base system: CAR +28%, average trade +25%, trades -6%); require IBS < 25 on the signal day (S&P 500 stocks, RSI2 crossing below 2.5: keeps 63% of trades and raises average trade by 21%; win rate falls from 71% to 57% as IBS rises from 0 to 100).
- Instruments: Nifty 100 / Nifty 200 / F&O-list stocks, delivery.
- Holding period: 1 to 6 days.
- Reported performance. Concretum, all historical S&P 500 constituents, 1996 to Nov 2025: 114,189 trades, mean return 45 bps per trade, hit ratio 64% (no costs stated). Quantitativo, S&P 500 point-in-time, 2004 to 2024, 10 slots, RSI2 version: metrics "pretty similar" to its DV2 version (17.4% annual return, Sharpe 0.87, max drawdown 34%, +0.36% per trade, 64.8% win rate, about 475 trades a year). Alvarez "Mean Reversion Check Up 2022", Russell 3000, RSI2 < 1, exit RSI2 > 70, 2000 to Sep 2022: number of trades and win rate flat, average profit per trade shrinking; the above-200-day version was negative in the 2020 and 2022 bear markets although positive in 2000, 2002, 2008 and 2011.
- India evidence. None found.
- Cost and capacity. Concretum's key result: on signal days the median number of eligible trades was 9, the maximum 250; 3.1% of days produced 50% of all trades; the most profitable 5% of trades occurred when about 65 signals fired at once. With at most 5 trades per day chosen at random, none of 10,000 simulations matched the full-sample mean return. A small account captures less than the headline per-trade average. At Rs 1.5 lakh: 5 slots of Rs 30,000 cost 0.46% per round trip and 10 slots cost 0.62%, against a 0.36% to 0.45% US gross average. At 300 to 475 trades a year the cost is roughly Rs 40,000 a year, more than a quarter of capital.
- Failure modes. Signal clustering in sell-offs (all positions correlated); bear markets; shrinking edge; stock-specific bad news (Capitalmind's "graveyard": Gitanjali Gems, GTL fell further 80% after a 40% one-day fall); survivorship bias if the universe is today's index list.
- Feasibility at Rs 1.5 lakh: marginal. Only worth testing with 3 to 5 slots, strict thresholds (RSI2 < 5 or lower) to cut trade count, F&O stocks, and Indian costs applied.
- Sources: https://concretumgroup.com/opportunity-set-bias-in-mean-reversion-trading-systems/ ; https://alvarezquanttrading.com/blog/mean-reversion-check-up-2022/ ; https://alvarezquanttrading.com/blog/mean-reversion-entry-at-open-vs-intraday-pullback-vs-confirmation/ ; https://alvarezquanttrading.com/blog/internal-bar-strength-for-mean-reversion/ ; https://alvarezquanttrading.com/blog/avoiding-gap-trades/ ; https://www.quantitativo.com/p/a-different-indicator ; https://premium.capitalmind.in/2018/09/when-a-stock-falls-big-is-that-a-opportunity-or-a-forebearer-of-further-bad-news/

### 3.3 Oversold setup with next-day limit entry below the close (Alvarez)

- Rules. Setup at the close: liquid stock; Close > SMA(100) (or SMA(200)); RSI(2) < 10 (tested 2.5 to 10). Next day: place a day-only limit buy x% below the setup close (x tested 1% to 4% in steps of 0.5; 4% and 5% used in other posts). Place only as many orders as free slots (so that all fills still fit, no leverage); rank setups by 100-day historical volatility, high to low; maximum 10 positions (5 at 20% each in another post). Exit at next open after RSI(2) > 50 (or > 70), or after 10 trading days. No stop, no market-timing rule in the base version.
- Instruments: liquid stocks, delivery (the limit order may also be used on ETFs).
- Holding period: 1 to 10 days.
- Reported performance. Alvarez, Russell 3000, 2007 to Jun 2021: versus entering at the open, limit entry raised CAR by 21%, cut exposure by 33%, lowered max drawdown and doubled average profit per trade (relative figures; absolute values are in a spreadsheet not opened). Entering on confirmation (buy stop above the close or above the setup high) was worse than entering at the open, except in 2021. Alvarez, 2007 to Jun 2018, the RSI2 < 10 / SMA100 / 5% limit version: results "really disappointing", best optimisation runs in the low teens CAR, 2016 and 2017 bad; restricting to ex-index stocks roughly doubled CAR and halved drawdown (a universe effect he could not explain beyond index-deletion drift).
- India evidence. None.
- Cost and capacity. Fewer fills than market entry, so lower trade count and cost; unfilled orders mean the best bounces (those that never dip further) are missed. Angel One brokerage applies per executed order, so unfilled limit orders are free.
- Failure modes. Adverse selection: fills occur when the stock keeps falling. Gap-down opens through the limit fill at the open. 2016 to 2017 style low-volatility years leave the system in cash.
- Feasibility at Rs 1.5 lakh: marginal (same stock-delivery cost floor as 3.2, somewhat better edge per fill).
- Sources: https://alvarezquanttrading.com/blog/mean-reversion-entry-at-open-vs-intraday-pullback-vs-confirmation/ ; https://alvarezquanttrading.com/blog/rsi2-strategy-double-returns-with-a-simple-rule-change/ ; https://alvarezquanttrading.com/blog/avoiding-gap-trades/

### 3.4 Connors R3

- Rules (as tested by QuantifiedStrategies). (1) Close > SMA(200). (2) RSI(2) has fallen three days in a row and the first of those falls started from below 60. (3) RSI(2) today < 10. If all true, buy at today's close. Exit at the close when RSI(2) > 70. No stop. Aggressive version (not tested): add a second unit whenever the position closes below the entry price.
- Instruments: index and sector ETFs (Connors used the 20 most liquid US ETFs).
- Holding period: a few days.
- Reported performance. QS, inception to Dec 2020, no commissions or slippage: SPY 1.28% average gain per trade, profit factor 7.17 (Connors' book to end-2008: 1.16%); QQQ 1.04% (Connors 1.24%); DIA 0.65% (0.17%); EEM 0.45% (0.91%); EWH 0.31% (1.18%); EWT 0.31% (0.85%); XLF 0.26% (0.46%); EFA 1.13% (0.85%). QS got fewer fills than Connors and could not replicate exactly. Several non-US and sector ETFs lost half or more of their original per-trade edge after publication.
- India evidence. None.
- Cost and capacity. Rare signals (a handful per year per ETF); cost negligible in ETF form.
- Failure modes. Very few trades, so results are noisy and capital is idle most of the time; correlated signals across ETFs; decay in non-US ETFs.
- Feasibility at Rs 1.5 lakh: yes in ETF form; too few trades to be a standalone system.
- Sources: https://www.quantifiedstrategies.com/larry-connors-r3-strategy/

### 3.5 Connors %b (three days below 0.2)

- Rules. Close > SMA(200); %b < 0.2 on each of the last three days; buy at the close; exit at the close when %b > 0.8. No stop. Band parameters: QS states it lacked Connors' parameters; it reports a 10-day lookback did better than its default; Alvarez typically uses length 5 or 10 with 1.0, 1.5 or 2.0 standard deviations and looks for %b below 0 or -0.1 for one to three days. Treat band length {5, 10, 20} and width {1, 1.5, 2} as the parameter grid.
- Instruments: index/sector ETFs.
- Holding period: days to about two weeks (exit needs a move to the upper part of the band).
- Reported performance. QS, portfolio of Connors' 20 ETFs since inception: 677 trades, win rate 75%, 0.76% average gain per trade, profit factor 1.9, CAGR 4.84%, max drawdown 16%, exposure 17%. With a 10-day lookback: CAGR 8.2% with a larger drawdown. Few fills on SPY and QQQ.
- India evidence. None.
- Cost and capacity: as 3.4.
- Failure modes: low exposure; parameters not replicable from the book; the Bollinger family has weakened since 2018 (see 3.12).
- Feasibility at Rs 1.5 lakh: yes in ETF form.
- Sources: https://www.quantifiedstrategies.com/larry-connors-b-strategy/ ; https://alvarezquanttrading.com/blog/the-abcs-of-creating-a-mean-reversion-strategy-part1/

### 3.6 Connors 3-day high/low method

- Rules. (1) Close > SMA(200). (2) Close < SMA(5). (3) Two days ago both high and low were lower than the day before. (4) Yesterday's high and low were lower than the day before. (5) Today's high and low are lower than yesterday's. Buy at today's close. Exit at the close when Close > SMA(5). No stop. Aggressive version: buy a second unit if the price closes below the initial entry while in the position (not tested).
- Instruments: ETFs.
- Holding period: typically 2 to 6 days.
- Reported performance. QS, 20 ETFs, 2000 to Nov 2020: 1,616 trades, 0.38% average gain per trade, CAGR 5.74%, profit factor 1.53, max drawdown 16.4% (worst in July to August 2011). 13 of the 20 ETFs performed worse than in Connors' original test to end-2008; QS: effectiveness "has somewhat declined over time".
- India evidence. None.
- Cost and capacity: ETF cost 0.07% to 0.17% against 0.38% gross per trade.
- Failure modes: post-publication decay; correlated ETF signals.
- Feasibility at Rs 1.5 lakh: yes in ETF form.
- Sources: https://www.quantifiedstrategies.com/larry-connors-3-day-high-low-method/

### 3.7 N-day down streaks and Connors "multiple days down" (MDD)

- Rules (MDD). Close > SMA(200); Close < SMA(5); the instrument closed down on at least 4 of the last 5 days; buy at the close; exit at the close when Close > SMA(5); no stop. (The "4 of 5" entry is stated on the QS page opened; the remaining conditions are from a search summary of the same article and are **unverified: snippet only**.)
- Rules (plain streak). Buy at the close after N consecutive lower closes (N = 3, 4 or 5; Alvarez: "(3,4,5) days down in a row is a good sign of a pullback"), optionally with Close > SMA(200); exit on close > SMA(5) or first higher close.
- Instruments: ETFs; liquid stocks with a position cap.
- Holding period: 1 to 6 days.
- Reported performance. No opened source gives MDD numbers (QS re-test is paywalled). Alvarez lists days-down as a working pullback measure without statistics.
- India evidence. Indirect and for the opposite streak: Capitalmind, Nifty since 1994 (written 2011): buying after 6 consecutive up closes and selling next day gave 61 instances, 30 wins and 31 losses, expectancy +0.13%; 4-day and 5-day up streaks (178 and 100 instances) had better next-day expectancy (about 0.32% is mentioned). So up streaks in Nifty tended to continue, not reverse; no down-streak test was found.
- Cost and capacity: as other ETF pullback systems.
- Failure modes: streaks cluster in sustained declines; untested in India.
- Feasibility at Rs 1.5 lakh: yes in ETF form.
- Sources: https://quantifiedstrategies.substack.com/p/larry-connors-multiple-days-up-and-d41 ; https://alvarezquanttrading.com/blog/the-abcs-of-creating-a-mean-reversion-strategy-part1/ ; https://premium.capitalmind.in/2011/03/continuous-positive-days/

### 3.8 Double Seven and N-day-low dip buying

- Rules (Double Seven). Close > SMA(200). Buy at the close when the close is a 7-day low. Sell at the close when the close is a 7-day high. No stop. (QS also tested "lowest close" versus "lowest low"; lowest close returned slightly less.)
- Rules (dip variant). Close > SMA(200); today's close is the lowest close of the last 7 days; buy at the close; sell at the close on the first day the close is higher than the previous close.
- Parameters: N in {5, 7, 10} (Alvarez: "closing price is a (5,7,10) day closing low").
- Instruments: index ETFs.
- Holding period: Double Seven up to about 9 or more days; dip variant 1 to 4 days.
- Reported performance. QS, SPY since 1993: Double Seven 154 trades, 1.18% average gain, win rate 82.5%, average loser 2.99% versus average winner 2.06%, max drawdown 33%, exposure 26%, CAGR 6.3% versus 10.1% buy and hold. On a wider ETF list: 1,189 trades, 0.63% per trade, CAGR 6.3%, "almost all gains happened before 2010". Dip variant, SPY: 329 trades, 0.52% per trade, win rate 76%, CAGR 5.7% versus 9.5% buy and hold, invested 16% of the time.
- India evidence. None.
- Cost and capacity: low trade count; ETF costs small.
- Failure modes: gains concentrated before 2010 outside SPY; losers larger than winners; idle capital.
- Feasibility at Rs 1.5 lakh: yes in ETF form.
- Sources: https://www.quantifiedstrategies.com/larry-connors-double-seven-strategy/ ; https://www.quantifiedstrategies.com/buy-the-dip-strategy/ ; https://alvarezquanttrading.com/blog/the-abcs-of-creating-a-mean-reversion-strategy-part1/

### 3.9 Internal bar strength (IBS) on an index ETF

- Rules (QS base). Buy at the close if IBS < 0.2. Sell at the close on any later day when IBS > 0.8. No stop (QS mentions a 10% stop as a safeguard). Variants: trade only when VIX closes above its 100-day average; trade only when the close is at most 5% above SMA(200). Pagonidis threshold test: long when IBS <= 0.2, short when IBS >= 0.8, one-day holds.
- Rules (Marketcalls Nifty futures variant). maIBS = 3-day moving average of IBS. Long: maIBS crosses below 0.3, buy next day's open, exit the same day at the close. Short: maIBS crosses above 0.75, sell next open, cover at the close. One-day (intraday) hold.
- Instruments: index ETFs at the close; Nifty futures intraday in the Marketcalls variant.
- Holding period: 1 to 6 days (QS variant averaged 5.8 trading days); 1 day in threshold form.
- Reported performance. QS, SPY 1993 to about 2025, no slippage or commission: 919 trades, 0.41% average gain, win rate 68%, CAGR 12.5% versus 9.9% buy and hold, profit factor 1.9, max drawdown 26%; losing years 1994, 2002, 2018. QQQ: 742 trades, 0.56% per trade, CAGR 16.6%. Entering at the next open instead of the close cuts SPY's average from 0.41% to 0.31%. VIX filter: 0.41% to 0.53% per trade, profit factor 1.92 to 2.19, but "pretty variable" to the moving-average length. Pagonidis, US-listed equity ETFs, inception to 12 May 2013: average next-day return +0.35% after IBS < 0.2 and -0.13% after IBS > 0.8; probability of an up day differs by 11.2 points between top and bottom buckets; stronger in high volatility, after large-range days, in bear markets and on Mondays; for US index ETFs the effect "completely disappears on low volume days". A simple IBS strategy "delivered an annual return of over 30%, before trading costs, over the last 19 years", but "using IBS alone is difficult due to transaction costs". Pandey and Joshi (arXiv 2306.12434), 2009 to 2019: probability of a positive next day after IBS < 0.2 was 0.58 for PIN (Invesco India ETF) and 0.57 for IVV; single-ETF threshold Sharpe 2.17 for PIN and 0.20 for IVV.
- India evidence. Indirect only. Pagonidis' table for EPI (WisdomTree India, US-listed): +0.394% average next-day return in the lowest IBS bucket, -0.297% in the highest. But Pagonidis also finds locally listed index ETFs in France, Germany, Spain, Switzerland, Taiwan, the UK and Australia show little or no effect, and attributes the US-listed country-ETF effect partly to overreaction to S&P moves while the home market is closed. So EPI/PIN results say little about NIFTYBEES. Marketcalls tested maIBS on Nifty futures May 2007 to Apr 2014 with Rs 200 per trade for two lots, but the results are images and no numbers could be read.
- Cost and capacity. About 29 trades a year on SPY in the QS test; in an Indian ETF at Rs 1.5 lakh that is about 2% a year in costs. Execution must be at or just before the close.
- Failure modes. IBS is widely known ("performed poorly in 2017 and 2018"); weak in commodity-heavy indices (Norway, Australia) and metals; depends on close execution; may be a US market-structure effect.
- Feasibility at Rs 1.5 lakh: yes operationally (ETF, one position). Whether the effect exists on NSE closes is the first thing to test.
- Sources: https://www.quantifiedstrategies.com/internal-bar-strength-ibs-indicator-strategy/ ; https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf ; https://arxiv.org/pdf/2306.12434 ; https://www.marketcalls.in/amibroker/internal-bar-strength-mean-reversion-trading-afl-code.html

### 3.10 RSI(3) pullback with an IBS filter (Pagonidis)

- Rules. Compute Cutler's RSI(3). Go long at the close if RSI(3) < 10. Stay long while RSI(3) <= 40. IBS filter: enter or remain long only on days when IBS <= 0.5 (so the position is closed at the close of any day with IBS > 0.5 and re-entered if conditions hold again). No stop.
- Related QS combination (rules sold separately; a search summary describes one version as IBS < 0.25 and RSI(21) < 45 with exit when the close exceeds the previous close: **unverified: snippet only**).
- Instruments: index ETFs.
- Holding period: 1 to 5 days.
- Reported performance. Pagonidis, US-listed equity ETFs to May 2013: the IBS filter removes about 43% of the days the RSI(3) system spends in the market and increases total returns by 9.6% on average; "when the RSI and IBS strategies align, average close-to-close returns are higher than for either strategy alone". QS "IBS plus second indicator": SPY 278 trades, 0.8% per trade, win rate 78%, 4.8 days per trade, max drawdown 23.75%; QQQ 232 trades, 1.33% per trade, win rate 75%, max drawdown 19.5%.
- India evidence. None.
- Cost and capacity. The filter increases round trips per unit of exposure; still modest in an ETF.
- Failure modes: as 3.9; more parameters.
- Feasibility at Rs 1.5 lakh: yes in ETF form.
- Sources: https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf ; https://www.quantifiedstrategies.com/internal-bar-strength-ibs-indicator-strategy/

### 3.11 Cross-sectional IBS basket (min-max IBS across ETFs)

- Rules (Pandey and Joshi). Each day at the close compute IBS for every ETF in a basket. Go long the ETF with the lowest IBS and short the ETF with the highest IBS; exit both at the next close; repeat daily (always in). Multi-name version: long the N lowest and short the N highest (N = 1 or 2). Long-only version: long the lowest only. Holding longer than one day or using 2-day IBS reduces performance.
- Indian adaptation: basket of liquid NSE ETFs (broad, bank, next-50, sector, gold excluded); long-only; optionally require IBS < 0.2.
- Instruments: ETFs.
- Holding period: 1 day, close to close.
- Reported performance. 15 US-listed country ETFs, 2009 to 2019, no commissions, borrow at 0.01% per day: Sharpe 2.91 for the 15-ETF min-max; best random baskets 3.7 to 3.9; long-only leg Sharpe 1.3 to 2.0, short-only 0.6 to 1.25. Open-to-open execution destroys it (Sharpe between -0.27 and 0.36 for the same baskets).
- India evidence. None for locally listed ETFs; PIN (India ETF listed in the US) appears in most of the best baskets.
- Cost and capacity. About 250 round trips a year. At Rs 1.5 lakh in one ETF that is about 250 x 0.07% = 17.5% a year in charges before spreads; at Rs 75,000 x 2 ETFs about 30% a year. Costs dominate unless the daily edge is very large.
- Failure modes. Execution at the close is mandatory; the effect is largely a US-listed-ETF phenomenon; sample-selected baskets; no costs in the paper.
- Feasibility at Rs 1.5 lakh: marginal (operationally simple, cost drag from daily turnover is severe).
- Sources: https://arxiv.org/pdf/2306.12434

### 3.12 Bollinger band reversion

- Rules (QS simple test). Buy at the close when the close is two standard deviations below the 10-day average. Exit when the close crosses above the 10-day average. Common alternative: BB(20, 2), buy on a close below the lower band, exit at the middle band (or upper band); optional SMA(200) filter; optional stop below the recent swing low.
- Instruments: index ETFs; stocks.
- Holding period: 2 to 10 days.
- Reported performance. QS, S&P 500 since 1993: "failed to beat buy and hold by a wide margin. Since 2018 it has been a losing strategy." A QS study with a 1.5-sigma band reported 561 trades and 0.52% average gain **(unverified: snippet only)**. A Reddit backtest on SPY 2006 to 2025 reported CAGR 3.67% (2.44% with a 200-day filter, 7.22% exiting at the upper band) **(unverified: snippet only)**. A Taiwan study found Bollinger rules could not beat buy and hold after costs **(unverified: snippet only)**.
- India evidence. A 2023 paper in Investment Management and Financial Innovations on 14 Nifty 50 companies with 2022 hourly data found a Bollinger-RSI combination produced net profit for 11 stocks and beat buy and hold for 10; a 2024 Indian study found moving-average envelopes outperformed Bollinger Bands; a 2020 Indian RSI/MACD study doubted profitability after trading costs (all three **unverified: snippet only**). Small samples; costs unclear.
- Cost and capacity: as other pullback systems.
- Failure modes: band touches are common in trends; weakest recent record in the family.
- Feasibility at Rs 1.5 lakh: marginal. Executable in ETFs, but the evidence is the weakest of the oscillator family and negative since 2018 in the US.
- Sources: https://www.quantifiedstrategies.com/bollinger-bands-trading-strategy/ ; https://www.quantifiedstrategies.com/larry-connors-b-strategy/

### 3.13 Stretch below a moving average or ATR band ("rubber band")

- Rules. Percentage stretch (Alvarez): close is 3%, 4% or 5% or more below SMA(5), or 5% or more below SMA(10); combine with a trend filter; buy at the close or next open; exit on close > SMA(5) or RSI(2) > 50 to 70. ATR-band stretch (QS "rubber band", Keltner channel): buy when the close is below a lower band set a multiple of ATR below a moving average; exit at the mean. QS's exact band settings are members-only and were not seen.
- Instruments: ETFs; liquid stocks.
- Holding period: 2 to 7 days.
- Reported performance. QS rubber band, S&P 500 (SPY): 328 trades, 0.45% average gain, CAGR 6.1%, invested 20% of the time, profit factor 2, max drawdown 16%. Alvarez gives parameter ranges, not statistics.
- India evidence. None with data (a Dailymotion video on a Nifty 50 pullback below the 20-day average appeared in search results; results not available).
- Cost and capacity: ETF costs small; for stocks see 3.2.
- Failure modes: fixed-percentage stretches ignore volatility regime; ATR version rules unverified.
- Feasibility at Rs 1.5 lakh: yes in ETF form.
- Sources: https://www.quantifiedstrategies.com/rubber-band-trading-strategy/ ; https://alvarezquanttrading.com/blog/the-abcs-of-creating-a-mean-reversion-strategy-part1/

### 3.14 Williams %R oversold

- Rules (QS). Buy at the close when Williams %R is below -90. Sell at the close when today's close is higher than yesterday's high, or when %R closes above -30. Lookback optimised from 2 to 25 days; short lookbacks were best and every lookback except 25 gave a profit factor of 2 or more. No stop.
- Instruments: index ETFs.
- Holding period: 1 to 5 days.
- Reported performance. QS, SPY since 1993: CAGR 11.9% versus 10.3% buy and hold, exposure 22%, 598 trades, 0.6% average gain, max drawdown 17%, profit factor 2.2. The same exit with RSI as the trigger gave CAGR 7.3%. A further (members-only) variant: 251 trades, 78% winners, CAGR 13.4%, exposure 14%, max drawdown 20.5%.
- India evidence. None.
- Cost and capacity: about 18 trades a year; ETF costs about 1.5% to 2% a year at Rs 1.5 lakh.
- Failure modes: Williams %R(n) with n = 2 is nearly IBS over two bars; expect high correlation with 3.9; optimisation risk.
- Feasibility at Rs 1.5 lakh: yes in ETF form.
- Sources: https://www.quantifiedstrategies.com/williams-r-trading-strategy/

### 3.15 ConnorsRSI pullback

- Rules. Compute ConnorsRSI(3,2,100). Buy at the close when CRSI < 10 (Alvarez: under 10 or 15); exit when the close is higher than yesterday's high (QS test) or when CRSI rises above 50 to 70. QS's best profit factor used a 2-day lookback for all three components with buy < 15 and sell > 85. Trend filter Close > SMA(200) is the usual addition.
- Instruments: ETFs; stocks.
- Holding period: 1 to 6 days.
- Reported performance. QS, S&P 500 since 1993, CRSI with 2-day lookbacks, buy < 10, exit close > yesterday's high: 293 trades, 0.5% average gain, win rate 75%, "a few big losing periods make this strategy hard to trade". The same rules with plain RSI(2): 385 trades, 0.66% average gain. Best CRSI setting: profit factor about 2.08 over 288 trades. QS: "fancy indicators don't guarantee edge".
- India evidence. None.
- Cost and capacity: as 3.1.
- Failure modes: no advantage over RSI(2) in the QS test; more parameters.
- Feasibility at Rs 1.5 lakh: yes in ETF form; low priority.
- Sources: https://www.quantifiedstrategies.com/connors-rsi/ ; https://alvarezquanttrading.com/blog/the-abcs-of-creating-a-mean-reversion-strategy-part1/

### 3.16 DV2 (Varadi oscillator) stock portfolio

- Rules (Quantitativo). Universe: S&P 500 constituents at each date. Each morning: capital split into 10 slots; buy at the open any stock whose DV2 closed below 10 the previous day and whose close was above SMA(200); improved version also requires a positive 6-month return. If more signals than free slots, take the highest normalized ATR first. Maximum 10 positions. Exit at the next open after the stock closes above the previous day's high. No stop.
- Instruments: liquid stocks.
- Holding period: a few days.
- Reported performance. 2004 to 2024, Norgate point-in-time data: 17.4% annual return, Sharpe 0.87, max drawdown 34%, about 475 trades a year, win rate 64.8%, +0.36% per trade, payoff ratio 0.69. With the 6-month filter: 20.9% a year, Sharpe 1.01, similar drawdown; one down year in 21; worst month -12.7% (Mar 2020). Event study on Russell 3000: buying DV2 < 10 above the 200-day average and holding 5 days gave mean +2.0%, median +0.3%, 54% positive; edge rises with volatility decile. Only about 1 in 5 DV2 < 10 events coincide with RSI2 < 10, but daily returns of the two portfolios correlate 80%. Returns fall as assumed trading costs rise (chart only).
- India evidence. None.
- Cost and capacity. 475 trades a year at Rs 15,000 each costs about Rs 44,000 a year at Angel One, about 29% of capital, against a gross of roughly 17% to 21%.
- Failure modes: cost; 34% drawdown; clustering.
- Feasibility at Rs 1.5 lakh: marginal to no in its 10-slot form; only as an alternative trigger inside a low-frequency 3-to-5-slot version.
- Sources: https://www.quantitativo.com/p/a-different-indicator

### 3.17 Turnaround Tuesday (weak Monday)

- Rules (QS, index ETF). V1: today is Monday; close at least 1% below Friday's close; buy at the close; sell at Tuesday's close. V2: Monday; close below the open; IBS < 0.2; buy at the close; sell at Tuesday's close. V3: Monday; close below Friday's close; IBS < 0.5; buy at the close; sell 4 trading days later. V4: as V3 but sell when the close is higher than the previous day's high, or after 4 trading days.
- Rules (StrategyQuant, stocks). Monday; stock closes more than 1% below its open (Close < 0.99 x Open); Close > previous bar's SMA(200); buy Tuesday's open; exit when Close > Close two bars ago or after 10 bars; maximum 10 positions; rank candidates by lowest 5-day rate of change; no stop or target.
- Instruments: index ETFs; stock baskets.
- Holding period: 1 to 4 days (stocks: under 3 days on average, winners about 2, losers about 5).
- Reported performance. QS, SPY from 1993, including 0.03% commission and slippage per trade: V1 212 trades, 0.3% average gain, CAGR 1.8%, exposure 2.5%, win rate 56%. V2 (1993 to Sep 2021) 270 trades, 0.33%, CAGR 2.7%, exposure 3.4%, win rate 57%. V3 495 trades, 0.45%, CAGR 6.5%, exposure 24%, win rate 60%. V4 495 trades, 0.46%, CAGR 7%, exposure 17%, win rate 69%. Buying Monday's close was "twice as good" as Tuesday's; buying strong Mondays did not work. StrategyQuant: Nasdaq 100 stocks, 20 years, 0.1% commission: about 5,900 trades, CAGR almost 10%, profit factor 1.35, win rate 66%, average winner $54 versus average loser $79; S&P 500 stocks: about 8,000 trades, CAGR 15%. Pagonidis independently finds the IBS effect strongest on Mondays and weakest on Fridays.
- India evidence. None found. NSE's weekly expiry calendar differs from the US, so the weekday effect needs its own test.
- Cost and capacity. ETF version: 7 to 17 trades a year, negligible cost. Stock version: 300 to 400 trades a year, same cost problem as 3.2.
- Failure modes. Price Action Lab argues the anomaly disappears once the overnight effect and bear-market short squeezes are accounted for (article paywalled; **unverified: title and snippet only**). Small edge in V1/V2.
- Feasibility at Rs 1.5 lakh: yes in ETF form.
- Sources: https://www.quantifiedstrategies.com/turnaround-tuesday-strategy/ ; https://strategyquant.com/blog/tuesday-reversal-strategy-tested-on-nasdaq-100-and-sp-500-stocks/ ; https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf

### 3.18 Weekly cross-sectional reversal (Lehmann; de Groot, Huij and Zhou) and long-only weekly rotation

- Rules (academic). Universe: the 100 largest stocks by market capitalisation. Each week rank by the previous week's return; long the 10 worst, short the 10 best; hold one week; rebalance weekly (Quantpedia's simple version of de Groot et al.). Cost-reduction rule from the paper: do not sell a loser (cover a winner) until it ranks in the top (bottom) half of past-week returns. Original Lehmann weighting: weights proportional to minus the stock's prior-week excess return over the market.
- Rules (Alvarez long-only rotation). Each weekend: stock is an index member; stock above SMA(200); index above SMA(200). Rank qualifying stocks by a sold-off measure; buy the 5 most sold off; hold one week; replace. Ranking measures tested: RSI(2, 4, 10, 14); return over 1, 3, 5, 10, 21 days; N-day closing range for N in {1, 3, 5, 10, 21}.
- Instruments: large-cap stocks, delivery; long leg only in India.
- Holding period: 1 week.
- Reported performance. Lehmann (1990), via Alpha Architect: prior-week losers earned +0.86% to +1.24% the next week and winners -0.35% to -0.55%; contrarian abnormal returns above 2% a month. De Groot, Huij and Zhou, US 1990 to 2009, via Quantpedia: net long-short return with Nomura cost estimates and five-day rebalancing was -31.4 bp a week for the 1,500 largest stocks, +10.6 bp for the 500 largest and +29.0 bp for the 100 largest (annualised 16.25%, estimated volatility 14.94%); costs assume $1 million trades. Via CXO Advisory: 0.9% gross a week for the top-1,500 decile hedge with daily rebalancing becomes a net loss; the "wait until opposite half" rule lifts net weekly return to about 0.4% (500 largest) and 0.7% (100 largest). Alvarez, S&P 500 stocks, 2007 to Oct 2017, long-only top 5 weekly: RSI ranking and rate-of-change ranking "did poorly" and were no better than random ranking (1,000 random runs: mean CAR 4.30%, standard deviation 2.54); best closing-range ranking CAR 8.26% (1.56 standard deviations above random) with only 0.28% average profit per trade, which "trading slippage would likely eat".
- India evidence. Tripurana and Devulapally (arXiv 2302.13245), NSE 500, 2014 to 2021, no costs: with weekly lookbacks of 2 to 8 weeks all the best portfolios were traditional momentum (winners minus losers 1.3% to 2.5% a month), i.e. continuation, not reversal. An older study (1991 to 2006) reporting weekly contrarian profits in India appeared in search results **(unverified: snippet only, author unclear)**.
- Cost and capacity. Five positions turned over weekly is about 260 round trips a year at Rs 138 each, about Rs 36,000 or 24% of capital a year. The academic net profits exist only for institutions trading the largest 100 stocks; the long leg alone was not reported.
- Failure modes. Long-only version no better than random in the US; Indian weekly data favour momentum; costs.
- Feasibility at Rs 1.5 lakh: no (turnover cost about 24% a year against a long-only edge that failed a random-ranking test).
- Sources: https://quantpedia.com/strategies/short-term-reversal-in-stocks ; https://www.cxoadvisory.com/?p=6251 ; https://alphaarchitect.com/quantitative-momentum-research-short-term-return-reversal/ ; https://alvarezquanttrading.com/blog/weekly-mean-reversion-rotation-strategy-on-sp500-stocks/ ; https://www.arxiv.org/pdf/2302.13245

### 3.19 One-month reversal (Jegadeesh), with turnover conditioning (Medhat and Schmeling)

- Rules. At each month-end rank the universe by the past one-month return. Academic: long the bottom decile, short the top decile, hold one month, rebalance monthly. India long-only: buy the 5 to 10 worst one-month performers among large, liquid stocks, hold one month. Turnover conditioning: Medhat and Schmeling double-sort on one-month return and share turnover (volume / shares outstanding): reversal is significant in the bottom seven turnover deciles and flips to momentum in the top decile, so exclude high-turnover losers (losers that fell on unusually heavy turnover) from the long list.
- Instruments: large-cap stocks, delivery.
- Holding period: 1 month.
- Reported performance. Jegadeesh (1990): about 2% a month for 1934 to 1987 (as cited in Da, Liu and Schaumburg, 2014). Hameed and Mian, US 1968 to 2010: unconditional (market-relative) reversal 0.81% raw and 0.63% risk-adjusted a month equal-weighted; only 0.28% value-weighted and not significant; indistinguishable from zero among large stocks (largest 30% by NYSE breakpoints). Medhat and Schmeling, US July 1963 to Dec 2018 (via Alpha Architect): short-term reversal 0.84% a month among large caps, 1.41% among small caps, 2.04% among microcaps and 0.74% among megacaps; "average monthly transaction cost of 1.94 percent subsumed its average gross return"; winner-minus-loser was -1.41% a month in the lowest turnover decile and +1.37% in the highest; reversal returns "tapered off" after 2011 and are gone after two months. Da, Liu and Schaumburg: reversal profit on the long side comes from liquidity shocks (fire sales), on the short side from sentiment; removing analyst-revision news gives risk-adjusted returns four times the standard strategy (needs analyst data).
- India evidence. Joshipura (NSE-sponsored paper, monthly NSE data 1995 to 2008) finds momentum at 6 and 12 months and contrarian profits at three years; it does not test one month. "Momentum, reversals and liquidity: Indian evidence" (Pacific-Basin Finance Journal, 2023) reports both momentum and short-term reversal exist in India, with reversal "more profound among the most illiquid stocks" and high-turnover stocks showing momentum **(unverified: snippet only; page returned HTTP 403)**. The NSE 500 arXiv study found monthly lookbacks of 3 to 12 months favour momentum.
- Cost and capacity. 5 positions monthly: 60 round trips, about Rs 8,250 or 5.5% of capital a year; 10 positions: about 7.4% a year. Large-cap long-short gross is 0.5% to 0.8% a month in the US; the long-only excess is roughly half of that.
- Failure modes. Concentrated in small, illiquid stocks that a cost-aware trader must avoid; conflicts with one-month momentum in liquid, high-turnover Indian stocks; decayed after 2011.
- Feasibility at Rs 1.5 lakh: marginal (low trade count, but the edge in liquid Indian large caps is doubtful and costs take most of it).
- Sources: https://academicweb.nd.edu/~zda/Reversal.pdf ; https://web2-bschool.nus.edu.sg/wp-content/uploads/media_rp/publications/BwXb81392625636.pdf ; https://alphaarchitect.com/short-term-momentum/ ; https://nsearchives.nseindia.com/content/research/res_paperfinal223.pdf ; https://www.arxiv.org/pdf/2302.13245

### 3.20 Industry-relative (intra-industry) and residual reversal

- Rules (Hameed and Mian). Each month compute each stock's return minus the average return of its industry (17 or 48 industry groups). Go long stocks that underperformed their industry and short those that outperformed, with weights proportional to minus the industry-adjusted return (Lehmann/Nagel weighting), $1 long and $1 short; hold one month. India long-only: buy the N stocks with the most negative industry-adjusted one-month return, at most one or two per sector. Residual reversal (Blitz, Huij, Lansdorp, Verbeek): rank on the last month's residual from a rolling factor regression (36-month Fama-French in the paper, **unverified: detail not opened**) instead of raw return.
- Instruments: large-cap stocks with a sector map.
- Holding period: 1 month.
- Reported performance. Hameed and Mian, US 1968 to 2010: intra-industry reversal 1.14% raw and 0.97% risk-adjusted a month, versus 0.63% for the conventional strategy; 1.28% with 48 industries; significant in every sub-period (0.68% to 1.90%), 0.94% in 2000 to 2010; value-weighted 0.53% a month; 0.47% a month among large stocks, where the conventional strategy is zero; above 1% a month after market declines; 0.70% a month (NYSE 1993 to 2008) when losers had sell-order imbalances, nothing without order imbalance. Blitz et al. (Robeco summary): residual reversal earns risk-adjusted returns twice those of conventional reversal and is profitable net of trading costs even for large caps after 1990; more than 8% a year net **(unverified: snippet only)**.
- India evidence. None found.
- Cost and capacity: as 3.19.
- Failure modes. Needs a stable industry classification; long-only leg keeps market and sector beta; US-only evidence.
- Feasibility at Rs 1.5 lakh: marginal (same cost arithmetic as 3.19, better-supported signal).
- Sources: https://web2-bschool.nus.edu.sg/wp-content/uploads/media_rp/publications/BwXb81392625636.pdf ; https://www.robeco.com/en-za/insights/2011/11/short-term-residual-reversal

### 3.21 Daily cross-sectional contrarian (Lo and MacKinlay; Khandani and Lo; Nagel) and the NSE 500 open-to-close version

- Rules (Lo-MacKinlay / Khandani-Lo). Each day hold every stock with weight `w_i = -(R_i,t-1 - R_m,t-1) / N`, where R_m is the equal-weighted market return: long yesterday's losers, short yesterday's winners, dollar neutral, rebalanced daily. Nagel: average of five such sub-strategies keyed on returns of days t-1 to t-5, scaled to $1 long and $1 short.
- Rules (NSE 500 study). Rank the NSE 500 daily on a volume-adjusted return score over the last J days (J = 1 to 7) into groups of 10 stocks; contrarian portfolio is long the loser group and short the winner group, equal cash, opened at the market open and closed at the close of the last holding day (K = 1 to 7 days). Best combinations: J-K of 3-1, 2-1 and 1-2.
- Indian retail adaptation: intraday only (positions opened at 09:15 and closed by 15:15 to 15:30 under MIS), which allows the short leg.
- Instruments: liquid stocks, intraday product.
- Holding period: 1 day (open to close) to 2 days.
- Reported performance. Khandani and Lo, all US stocks priced $5 to $2,000, gross: average daily return 1.38% in 1995, 0.44% in 2000, 0.13% in 2007 (to August); 3.57% a day in the smallest decile versus 0.04% in the largest in 1995; the leverage needed to match 1998's expected return (0.57% a day) rose from 2:1 to almost 9:1 by 2007 (return multiplier 4.48, their Table 6). Nagel, CRSP 1998 to 2010: 0.30% a day with closing transaction prices but 0.18% with quote midpoints (so a substantial part is bid-ask bounce); annualised Sharpe 8.4 and 4.5 before costs; industry-portfolio reversal only 0.02% a day; returns near 1% a day in the 1998 and 2000/01 crises, below 0.2% by 2007, then "virtually exploded" in 2008. Tripurana and Devulapally, NSE 500, 2014 to 2021, no commissions: best daily contrarian (J-K 3-1, inverse-turnover weighting) loser-minus-winner 6.04% a month with 4.78% monthly standard deviation, final wealth 17.1 times, max drawdown -13.7%; other contrarian variants 2.9% to 4.5% a month; all but one of the best daily portfolios were contrarian. In that table both legs had negative mean returns measured open to close (winners -8.99% a month, losers -2.95%), so the profit came from the short-winner leg and a long-only loser basket lost money.
- India evidence. Yes, the NSE 500 study above (gross, 2014 to 2021, a period ending with the post-Covid rally).
- Cost and capacity. Daily turnover of 100%. Delivery is impossible (0.27% to 0.62% a day). Intraday at Rs 30,000 a name costs 0.19% per round trip; with intraday leverage and Rs 1.5 lakh per name about 0.07%, plus opening-auction slippage on the most volatile names of the day. Reported gross is about 0.2% to 0.4% a day on gross exposure.
- Failure modes. Bid-ask bounce inflates backtests on last-trade prices; the edge decayed for 12 years in the US; August 2007 style liquidations; short-leg dependence in India; intraday short availability and margin rules at the broker; the long-only version is negative.
- Feasibility at Rs 1.5 lakh: marginal (intraday, leveraged, highly cost sensitive); no in delivery form.
- Sources: https://www.newyorkfed.org/medialibrary/media/research/conference/2007/liquidity/Khandani_Lo.pdf ; https://www.nber.org/papers/w17653.pdf ; https://www.arxiv.org/pdf/2302.13245 ; https://www.cxoadvisory.com/?p=6251

### 3.22 Reversal after large price declines in large, liquid Indian stocks (Parthasarathy and Sendilvelu)

- Rules. Universe: large, liquid NSE stocks. Event: a "large" one-month price fall. The threshold is not stated in the abstract; test a grid such as one-month return <= -15%, -20%, -25%, or the worst 5% of the monthly cross-section. Buy at the next session after month-end; hold 1 to 6 months (the paper finds reversals "up to six months" and stronger reversals after stronger shocks). No stop in the paper; a practical version needs a fundamental or event exclusion (results day, fraud, pledge news) because not all falls are overreactions. Daily variant (Parthasarathy 2019, **unverified: snippet only**): after a large one-day fall on low volume, buy for a short horizon; skip large moves on high volume, which tend to continue.
- Instruments: Nifty 100/200 stocks, delivery.
- Holding period: 1 to 6 months (monthly events); days (one-day events).
- Reported performance. Abstract only (Economic Thought Journal 67(3), 2022, sample of large liquid Indian stocks over 2000 to 2019 per the search summary): "significant reversals following both large price declines and increases up to six months"; "stronger initial shocks were followed by stronger reversals"; robust to microstructure effects, extreme events, industry, period and market effects; abnormal returns after large declines "might be economically significant". No magnitudes were available. International background cited by the paper: Bremer and Sweeney (1991), Atkins and Dyl (1990), Benou and Richie (2003).
- India evidence. Yes (the paper itself).
- Cost and capacity. Few trades (a handful a year), long holds, so the 0.3% to 0.5% delivery cost is small relative to a multi-month reversal.
- Failure modes. Value traps and frauds (Capitalmind: Infosys recovered within months of its 26% one-day fall in 2003; Mastek did not for 14 years; Gitanjali and GTL went to near zero); positions held through further drawdowns with no stop; overlaps with long-term value and conflicts with 6-to-12-month momentum, which is strong in India.
- Feasibility at Rs 1.5 lakh: yes operationally (low turnover, 3 to 5 positions); evidence is an abstract without effect sizes.
- Sources: https://etj.iki.bas.bg/en/microeconomics/2022/08/02/on-stock-return-patterns-following-large-monthly-price-movements-empirical-evidence-from-india ; https://premium.capitalmind.in/2018/09/when-a-stock-falls-big-is-that-a-opportunity-or-a-forebearer-of-further-bad-news/

### 3.23 Opening gap fade

- Rules (QS, SPY). If the open is between 0.15% and 0.6% below the previous close, and the previous day's IBS was below 0.25, buy at the opening print. Target: 75% of the gap (open -0.5% means target +0.375% above the fill). If the target is not hit, exit at the close. No stop. Mirror rule for shorts on gap-ups (weaker). Gaps larger than about 1% are treated as continuation, not fade. Other QS observations (2005 to Oct 2012, end-of-day data): fading works better when the previous day left an unfilled gap; after a high-range day (range above its 15-day average) 439 fills averaged 0.078%.
- Instruments: index ETF intraday (MIS) or index futures; needs live open price and intraday data to test targets properly.
- Holding period: intraday.
- Reported performance. QS, Jan 2010 to Aug 2012, end-of-day data: 110 fills, 98 winners, 0.19% average per fill; re-tested on 30-minute data: 89 fills, 0.22% average for longs and 0.08% for shorts. The author warns the end-of-day result is "probably too good to be true" because of bad high/low quotes and that the strategy "didn't perform very well some years ago".
- India evidence. No verified dataset. onetradejournal states "no verified Nifty or Bank Nifty fill-rate dataset is provided". optionx.trade offers "a rough estimate" of same-day fill rates of 40% to 50% for gap-ups and 20% to 30% for gap-downs with no data behind it. Social-media claims of 60% to 82% fill rates are unsourced **(unverified: snippet only)**. A study of 6,902 daily Nifty 50 observations (Inani et al., summarised on the JGU research blog) found next-day opening returns show momentum behaviour and that the prior day's high or low has no effect on them. A secondary summary of Capitalmind Mutual Fund analysis says most of Nifty's long-run gain accrued overnight and open-to-close returns were negative in aggregate (the summary's own index levels are inconsistent; treat as indicative only).
- Cost and capacity. Intraday ETF round trip 0.07% to 0.13% at Rs 50,000 to 1,50,000 against a 0.08% to 0.22% reported average edge: costs take half or more. Futures: 0.059% of notional, but one lot uses the whole account.
- Failure modes. Trend days after gaps; data errors in OHLC backtests; edge of the same order as costs; negative intraday drift in Nifty hurts the long side.
- Feasibility at Rs 1.5 lakh: marginal (needs intraday data and execution; thin edge).
- Sources: https://www.quantifiedstrategies.com/gap-fill-trading-strategies/ ; https://onetradejournal.com/strategies/gap-fill-strategy ; https://optionx.trade/blogs/nifty-bank-nifty-gap-fill-strategy ; https://research.jgu.edu.in/do-daily-price-extremes-influence-short-term-investment-decisions-evidence-from-the-indian-equity-market/ ; https://www.multibagg.ai/market-pulse/articles/nifty-overnight-intraday-returns-study-cmquu8ofy9pn1nz0j1dln1abo

### 3.24 Volatility-conditioned reversal ("buy panic only when fear is high")

- Rules. Overlay on any oscillator entry (IBS < 0.2, RSI(2) < 10, etc.): take the trade only when the volatility index closes above its 100-day moving average (QS), or scale position size up with the volatility index level. India: use India VIX. Alternative triggers from the academic work: after a market decline over the prior month (Hameed and Mian) or when VIX is high (Nagel, VIX lagged five days).
- Instruments: index ETFs (overlay).
- Holding period: as the underlying system.
- Reported performance. QS, SPY IBS system: average trade rises from 0.41% to 0.53% and profit factor from 1.92 to 2.19 with the VIX > 100-day-average filter, but the result is "pretty variable from even small changes" in the average length. Nagel (1998 to 2010): reversal-strategy returns are "highly predictable with the VIX"; conditional Sharpe ratios rise with VIX; even industry-level reversal, unprofitable on average, earns high returns when VIX is high. Hameed and Mian: intra-industry reversal exceeds 1% a month in down markets. Pagonidis: IBS effect stronger in high-volatility regimes and after high-range days. QS notes IBS "performs best in bear markets" because the biggest up days occur there.
- Contrary evidence. Alvarez: his above-200-day RSI(2) stock system lost money in the 2020 and 2022 bear markets. QS on RSI(2): win rates below 60% in 2008 and March 2020 and suggests requiring VIX below 25. So the sign of a volatility filter depends on the system: index-level one-day reversal improves with volatility; multi-day stock pullback systems with a trend filter have been hurt in crashes.
- India evidence. None found.
- Cost and capacity: reduces trade count.
- Failure modes: few independent crisis episodes; parameter fragility; larger losses when a panic continues.
- Feasibility at Rs 1.5 lakh: yes as an overlay (needs India VIX daily history).
- Sources: https://www.quantifiedstrategies.com/internal-bar-strength-ibs-indicator-strategy/ ; https://www.nber.org/papers/w17653.pdf ; https://web2-bschool.nus.edu.sg/wp-content/uploads/media_rp/publications/BwXb81392625636.pdf ; https://alvarezquanttrading.com/blog/mean-reversion-check-up-2022/ ; https://www.quantifiedstrategies.com/rsi-2-strategy/

### 3.25 Reversal around earnings announcements (So and Wang, via Quantpedia)

- Rules. Universe: largest size quintile of listed stocks with a known earnings date t. Sort on the average return over days t-4 to t-2. Long the bottom quintile (pre-announcement losers), short the top quintile; hold over days t-1, t, t+1; equal weights. Rebalanced daily as announcements arrive.
- Instruments: large-cap stocks; needs a reliable forward calendar of board-meeting/results dates.
- Holding period: 3 days.
- Reported performance. US 1996 to 2011: indicative 6.5% a year (arithmetic, assuming 10 rebalances a quarter), estimated volatility 3.76%, Sharpe 1.73 as listed by Quantpedia; the paper documents "a six-fold increase in short-term return reversals during earnings announcements relative to non-announcement periods".
- India evidence. None found.
- Cost and capacity. Roughly 0.16% gross per 3-day window (6.5% over about 40 windows) for the long-short spread; the Indian delivery round trip alone is 0.27% to 0.62%.
- Failure modes. Holding through results is a large single-stock gap risk; Alvarez separately studies avoiding mean-reversion trades before earnings (post not opened in full).
- Feasibility at Rs 1.5 lakh: no (edge smaller than cost; needs event data).
- Sources: https://quantpedia.com/strategies/reversal-during-earnings-announcements

### 3.26 RSI(14 or 21) recovery cross, long-only swing (Share.Market / PhonePe Indian study)

- Rules. Buy when RSI crosses above 30 from below. Exit when RSI crosses above 70. Long-only. RSI length tested 7, 14, 21; 21 gave the best win rate and return per trade. No stop described. (Other rules in the same study: RSI crossing 50 both ways; RSI crossing its own 100- or 200-period EMA.)
- Instruments: Nifty 50, Next 50, Midcap 150, Smallcap 250 and Nifty 500 stocks, delivery.
- Holding period: weeks to months (about one trade per stock per year).
- Reported performance. 25-year backtest on Indian index stocks: RSI 30-70 cross gave the highest return per trade of the three rules; with a 21-period RSI, win rate 79.05% and 15.65% average return per trade; long-only worked while short-only and combined long-short "consistently generated losses across indices". The study states its limits: end-of-day signals; no slippage, spread or brokerage; current index constituents used for the whole period (survivorship bias); missing data and failed trades ignored.
- India evidence. Yes, but with survivorship bias and no costs.
- Cost and capacity. About one round trip per stock per year; 0.3% to 0.6% cost is small against the claimed per-trade return. Capital is tied up for long periods; with 5 to 10 slots many signals will be skipped.
- Failure modes. Survivorship bias inflates dip-buying of today's winners; long holding periods mean much of the return may be market drift; no stop.
- Feasibility at Rs 1.5 lakh: yes (low turnover, delivery, daily data).
- Sources: https://share.market/buzz/insights/the-rsi-myth-is-this-popular-indicator-worth-using-part-2-research-report

### 3.27 Variants noted but not given their own card

- Connors Cumulative RSI, RSI 25/75 and TPS (scale-in) from the 2008 and 2009 books: no opened source gave rules or results (QS pages 404 or paywalled) **(unverified: not opened)**. They are parameter or sizing variants of 3.1.
- Scale-in ("aggressive") versions of R3, 3-day high/low and MDD: add a second unit if the position closes below entry. Not tested by QS; doubles exposure into losers.
- Alvarez "ex-index" universe (stocks that were once in the index but are not now): doubled CAR in one RSI(2) test (3.3). Needs historical membership data.
- Overnight hold (buy the close, sell the next open) on weak closes: QS reports 688 trades and 0.31% average for an S&P 500 overnight rule whose conditions are members-only. In India each one-day ETF round trip costs 0.07% to 0.17%.

## 4. Typical holding periods, stops and exits across the family

- Holding periods: index/ETF oscillator systems 1 to 7 trading days; stock pullback portfolios 1 to 6 days with 5- or 10-day time stops; weekly and monthly reversal 1 week and 1 month; large-decline reversal up to 6 months.
- Exits used in the sources: close above SMA(5); RSI(2) above 50, 65, 70 or 80; close above the previous day's high; first higher close; %b above 0.8; IBS above 0.8; fixed 1-, 4- or 5-day holds.
- Stops: Connors, Alvarez and QS all report that fixed stops reduce returns of short-term mean reversion ("they work better without stops, meaning it is best to wait for the bounce"). Time stops are the standard substitute. The price of this is negative skew: win rates of 65% to 82% with average losers larger than average winners (Double Seven: 2.99% versus 2.06%).
- Exposure: 15% to 35% of days for single-instrument systems, so absolute CAGR is often below buy and hold even when the per-day return is high.

## 5. Negative or cautionary evidence

1. Indian costs versus the size of the edge. Stock-level short-term reversal earns 0.3% to 0.45% gross per trade in the best US studies (Quantitativo 0.36%, Concretum 0.45%, Alvarez weekly rotation 0.28%). An Angel One delivery round trip is 0.46% at Rs 30,000 and 0.62% at Rs 15,000 before spread. Medhat and Schmeling: monthly reversal's average transaction cost of 1.94% a month exceeds its gross return. De Groot et al.: net returns are negative for a 1,500-stock universe and positive only for the largest 100 at institutional scale. Pagonidis: an IBS-only strategy is hard to trade because of costs.
2. Opportunity-set bias (Concretum). Per-trade averages overstate what a capped portfolio earns because the best trades arrive in bursts of dozens to hundreds of signals during sell-offs; 3.1% of days hold half the trades. A 5-slot account cannot capture them.
3. Decay. Daily contrarian returns fell from 1.38% a day (1995) to 0.13% (2007) (Khandani and Lo). Monthly reversal tapered after 2011 (Medhat and Schmeling). Conventional market-relative monthly reversal is indistinguishable from zero among large US stocks over 1968 to 2010 (Hameed and Mian). Alvarez (2022): "edges are continuing to get smaller". QS: Double Seven's multi-ETF gains came before 2010; 13 of 20 ETFs did worse on the 3-day high/low method after publication; Bollinger reversion on the S&P 500 has lost money since 2018; IBS had its first losing year of the century in 2018.
4. Execution at the close is part of the edge. Pandey and Joshi: Sharpe falls from about 3.7 to about 0 when trading open-to-open. QS: IBS average trade drops from 0.41% to 0.31% with next-open entry. Nagel: reversal returns are 0.18% a day on quote midpoints versus 0.30% on last-trade prices, i.e. a large part of the measured effect is bid-ask bounce.
5. Market dependence. Pagonidis finds the IBS effect is essentially a US-listed-ETF phenomenon; locally listed ETFs in seven other markets show little or none. Alvarez shows low RSI(2) readings were followed by below-average returns in the S&P 500 before 1983. In India: weekly horizons show momentum, not reversal (NSE 500, 2014 to 2021); Nifty opening returns show momentum (JGU summary); Nifty up-streaks tended to continue (Capitalmind 2011); RSI short rules lose money (Share.Market). None of this supports assuming US-style index mean reversion carries over.
6. Data-mining and reporting bias. CXO Advisory on Connors' books: no out-of-sample tests, no correction for the number of rules tried, no costs, and trade samples that overlap heavily in time. Alvarez: RSI and rate-of-change rankings were no better than random ranking in a weekly rotation. QS could not replicate Connors' R3 and %b figures exactly. Most practitioner pages sell the rules they report on.
7. Tail risk. No-stop dip buying has negative skew; Alvarez's stock system and QS's RSI(2) both suffered in 2020 and 2022. Single stocks can fall and stay down (Capitalmind's examples). Non-F&O Indian stocks can lock at the lower circuit.
8. Survivorship bias in Indian practitioner studies (Share.Market uses current constituents for 25 years).
9. Turnaround Tuesday is disputed (Price Action Lab), and its plain form earns only 0.3% per trade on about 7 trades a year.
10. Long-only translation. Academic reversal profits are long-short. Da et al. attribute the long-leg profit to liquidity shocks (fire sales), which is encouraging, but in the NSE 500 open-to-close study the long (loser) leg lost money and the profit came from shorting winners.

## 6. Open questions

1. Does one-day index mean reversion (IBS, RSI(2), Williams %R) exist in NIFTY 50, NIFTY Bank and Next 50 daily data and in NIFTYBEES/BANKBEES/JUNIORBEES prices, by sub-period (pre-2010, 2010 to 2019, 2020 onward)? No Indian test with numbers was found.
2. How far is an executable 15:20 to 15:29 price (or the post-close session price) from the official NSE close, and does ETF premium/discount to iNAV at the close create a false IBS/RSI signal in ETF prices that is absent in the index?
3. Is STT on equity-ETF delivery sales really 0.001% on the Angel One contract note, and does the Rs 20 + GST DP charge apply to next-day (BTST) ETF sales?
4. Current Nifty and Bank Nifty lot sizes and margins (65 and 30 were read from one practitioner page, not from NSE), and whether any index future fits a Rs 1.5 lakh account at all.
5. Overnight versus intraday return split for Nifty and for large caps after the October 2010 pre-open auction: the only source was a secondary summary with inconsistent figures. This matters for every "buy the close" rule and for the open-to-close contrarian result.
6. Is the NSE 500 daily contrarian profit (2014 to 2021, gross, short-winner leg) still present in 2022 to 2026, at the open auction price, after intraday costs and with the stocks Angel One allows for intraday shorting?
7. Effect sizes for reversal after large monthly declines in large Indian stocks (the paper's tables were not accessible), and how they interact with 6-to-12-month momentum.
8. A point-in-time constituent history for Nifty 100/200/500 is needed; without it every stock-level dip-buying test is biased upward.
9. Does conditioning on India VIX help or hurt? US evidence points both ways depending on the system.
10. For a 3-to-5-slot stock portfolio, which selection rule (lowest RSI, highest volatility, lowest IBS, no recent gap-down) recovers the most of the full-sample edge under a position cap, measured by Concretum-style random-subsample tests?
11. SEBI's closing-auction proposals for cash equities: status and start date were not checked; a true closing auction would change close-execution assumptions.
