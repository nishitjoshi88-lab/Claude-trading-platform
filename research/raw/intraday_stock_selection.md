# Choosing which stocks to day-trade: selection rules and the evidence for them

Research date: 2026-11-10. Scope: how systematic day traders choose the day's stocks, written as rules that can be coded on our data (1-minute bars for about 200 liquid NSE stocks plus NIFTY 50 and NIFTY BANK from January 2022; daily prices for all NSE stocks from 2003; daily F&O files from 2008; daily participant positioning). Account: ₹1,50,000 at Angel One, fully automated, profits reinvested.

## How to read this file

- A number is attributed to a source I opened with `fetch_text.py` unless it carries one of these labels:
  - **(unverified: snippet only)**: seen only in a search-result summary.
  - **(abstract only)**: I read the abstract through the Consensus research index or a repository page, not the full paper.
  - **(from memory, unverified)**: not checked in this session.
  - **(adaptation)**: my translation of a US or daily rule to NSE hours and our data. Not from the source.
  - **(computed)**: arithmetic on sourced inputs, shown.
- Search effort: 34 web searches and 13 research-index queries (the index returned at most 3 papers per query). For five of the nine topics in the brief (F&O ban, open-interest change, delivery volume, relative strength versus index, results-day intraday behaviour) I found **no** rigorous test of an intraday trading rule on Indian stocks. Those sections say so. They are hypotheses to test, not established edges.
- Almost every positive result below is from US data, gross or lightly costed, and published by people who sell courses, software or newsletters. The one paper that directly shows stock selection changing a day-trading result (Zarattini, Barbon and Aziz 2024) has a co-author who runs a day-trading education business.

## 0. Facts that decide feasibility

### 0.1 Angel One intraday equity charges (official page, opened 2026-11-10)

Source: https://www.angelone.in/pricing

- Brokerage, intraday equity: lower of ₹20 or 0.1% per executed order, minimum ₹5.
- STT, intraday equity: 0.025% on the sell side. Futures: 0.05% on the sell side. Options: 0.15% on the sell side (premium).
- NSE transaction charge, equity: 0.0030699%. Futures: 0.0018299%.
- Stamp duty 0.003% on the buy side for intraday equity and SEBI fee ₹10 per crore: taken from the sibling file `small_account_india.md`, which read the same page; I did not re-read those two lines.
- GST 18% on brokerage, transaction charge and SEBI fee.

Round-trip cost of one intraday cash position of value P (computed from the above):

| Position value | Brokerage (2 orders) | STT | Other + GST | Total | % of position |
|---|---|---|---|---|---|
| ₹5,000 to ₹20,000 | 0.1% each side | 0.025% | | ₹13.6 to ₹54.3 | 0.271% |
| ₹30,000 | ₹40 | ₹7.5 | ₹10.3 | ₹57.8 | 0.193% |
| ₹50,000 | ₹40 | ₹12.5 | ₹12.4 | ₹64.9 | 0.130% |
| ₹75,000 | ₹40 | ₹18.8 | ₹15.0 | ₹73.8 | 0.098% |
| ₹1,00,000 | ₹40 | ₹25.0 | ₹17.7 | ₹82.7 | 0.083% |
| ₹1,50,000 | ₹40 | ₹37.5 | ₹22.9 | ₹100.4 | 0.067% |
| ₹2,50,000 | ₹40 | ₹62.5 | ₹33.4 | ₹135.9 | 0.054% |
| ₹7,50,000 | ₹40 | ₹187.5 | ₹85.8 | ₹313.3 | 0.042% |

Slippage is extra. Nothing I opened measures it for NSE; assume at least 0.02% to 0.05% per side on stop orders in liquid names until our own fills say otherwise (assumption, not sourced).

Consequences for stock selection:
- Below ₹20,000 per position the charge is a flat 0.27% per round trip. A strategy that trades ten small positions pays more than twice the percentage cost of one that trades two large ones. Selection rules that concentrate into the best 1 to 3 names are favoured by the fee schedule, not just by the evidence.
- Leverage: equity intraday (MIS) margin is "5x (up to 20% of trade value)", the exchange VAR+ELM margin, the same at every broker since 1 September 2021 (https://www.chittorgarh.com/broker/angel-broking/margin-exposure/14/). So ₹1.5 lakh controls at most ₹7.5 lakh intraday. Angel One squares off open intraday positions at 3:15 PM (unverified: snippet only), so every rule below exits by 15:10.
- Stock futures are not the vehicle: STT on futures is twice the cash-intraday rate and one lot ties up most of the account (lot sizes and margins are another researcher's area).

### 0.2 What a "tight stop" strategy costs in India

The best-evidenced selection paper sets the stop at 10% of the 14-day ATR and measures profit in units of that stop (R). If a liquid NSE stock has ATR of 2.5% of price (assumption for illustration), R is 0.25% of price. A ₹1.5 lakh position costs 0.067% in charges plus, say, 0.06% slippage both sides: about 0.13% of position, which is about 0.5R per trade (computed). The paper's average edge with the selection filter on was 0.08R per trade, and 0.38R only in the most extreme bucket. The same rules with Indian charges would lose money unless the stop is widened or only extreme cases are traded. This must be tested, not assumed.

### 0.3 Who loses at this

SEBI's July 2024 study of intraday trading by individuals in the equity cash segment, as quoted on TradingQnA (https://tradingqna.com/t/key-findings-from-sebis-analysis-of-intraday-trading-by-individuals-in-equity-cash-segment/170633): 71% of individual intraday traders made a net loss in FY 2022-23; 80% of those with more than 500 trades a year; 76% of those with annual intraday turnover above ₹1 crore (average result −₹34,977). Loss-makers spent a further 57% of their trading losses on costs; profit-makers spent 19% of profits on costs. Even with three years of experience 54% lost. Sample: clients of the top 10 brokers, about 86% of individual clients.

### 0.4 Rules that changed in 2024 to 2026 and affect selection

- **F&O ban.** From 8 December 2025 open interest for the ban test is delta-adjusted "future equivalent" OI, computed at portfolio level; the exchange checks market-wide position limit (MWPL) use at least four random times a day rather than only at day-end; no fresh position or rollover is allowed in a banned stock; a square-off that raises net future-equivalent OI can be cancelled and positions auto-squared after 2 PM (https://www.angelone.in/announcements/market/position-limits-for-stocks-in-ban-period-for-fo-segment-w-e-f-december-8-2025). Kotak Neo's explainer adds: MWPL is now the lower of 15% of free float or 65 times average daily delivery value, with a floor of 10% of free float (it was 20% of free float); entry at 95% of MWPL, exit at 80%; "a stock may enter ban intraday"; futures rollover allowed (https://www.kotakneo.com/bulletins/sebi-new-f-o-rules-explained-delta-based-oi-new-mwpl-what-it-means-for-your-trading/). The two brokers disagree on rollover; check the exchange circular before coding anything in futures. For a cash-only intraday system the disagreement does not matter.
- **Price bands for F&O stocks.** No fixed daily limit. The day starts with a ±10% band. On a hit (50 trades from 10 accounts and 3 members at or beyond 9.90%) the band flexes by 5% after a 15-minute cooling-off (5 minutes in the last half hour), twice; then by 3% after 30 minutes, twice; then by 2% after 60 minutes. Bands slide: when one side flexes, the other side moves by the same amount and resting orders outside the new band are cancelled. Phased in June to October 2024 (https://zerodha.com/z-connect/business-updates/explainer-on-new-price-band-rules-for-stocks-trading-in-the-fo-segment). SEBI was reported in April 2026 to be considering uniform dynamic bands across NSE and BSE (unverified: snippet only).
- **Non-F&O stocks** have fixed bands of 2%, 5%, 10% or 20% (same Zerodha page: "typically range from ±2% to ±20%").

### 0.5 Common definitions used in the rules

- `gap = open_0915 / prev_close − 1`.
- `ATR14` = 14-day average true range from daily bars; `ATRpct = ATR14 / prev_close`.
- `OR_n` = first n one-minute bars from 09:15 (n = 5 means 09:15 to 09:19 inclusive).
- `RVOL_n = volume(OR_n today) / mean(volume(OR_n) over the previous 14 sessions)`.
- "EOD exit" = market order at 15:10 (adaptation; see 0.1).
- Universe U200 = the roughly 200 stocks for which we hold 1-minute bars.

### 0.6 Strategy sheet: instruments, holding period, positions, rebalance

All trades are in NSE cash equities under the intraday (MIS) product unless stated; both directions are possible intraday. "Selection" is how often the candidate list is rebuilt.

| # | Strategy | Selection | Positions | Holding period | Data beyond 1-minute and daily bars |
|---|---|---|---|---|---|
| 1 | Relative-volume ranked 5-minute opening range breakout | daily at 09:20 | 2 to 5 | minutes to 15:10 | none |
| 2 | Opening gap fade | daily at 09:20 | up to 3 | 09:20 to 12:30, else 15:10 | results calendar (filter) |
| 3 | Gap and go | daily at 09:20 | up to 2 | minutes to 15:10 | none |
| 4 | NR4 / NR7 / inside day breakout | previous close | up to 3 | trigger to 15:10 | none |
| 5 | ATR and range-expansion universe filter | daily pre-open | filter only | n/a | none |
| 6 | Intraday relative strength versus NIFTY and sector | 10:00 to 11:00 | 2 or 3 | T to 15:10 | sector map |
| 7 | Index direction gate | 09:45 and 14:40 | gate, or 2 | 14:40 to 15:10 for the late variant | none |
| 8 | Same-time-of-day continuation | every half hour | decile baskets | 30 minutes | none |
| 9 | Intraday-return persistence | daily or monthly | decile lists | open to close | none (daily bars only) |
| 10 | High-volume return premium | previous close | up to 3 | open or trigger to 15:10 | none (daily bars only) |
| 11 | Delivery-volume change | previous close | up to 3 | trigger to 15:10 | deliverable quantity per stock per day |
| 12 | Futures OI and price quadrant | previous close | up to 3 | trigger to 15:10 | daily F&O file |
| 13 | Yesterday's top gainers and losers | previous close | 5 long, 5 short (fewer at our size) | open to 15:10 | none (daily bars only) |
| 14 | Results day and day after | daily | up to 2 | trigger to 15:10 | results dates and times |
| 15 | 52-week high proximity and breakout | previous close, plus live trigger | up to 2 | trigger to 15:10 | none |
| 16 | F&O ban and MWPL state | previous evening | filter, or up to 2 | trigger to 15:10 | daily ban list and MWPL utilisation |
| 17 | Price-band proximity | live | risk rule | n/a | price-band category per stock |
| 18 | Bulk and block deal catalyst | previous evening | up to 2 | trigger to 15:10 | bulk and block deal file |
| 19 | Pre-open auction information | 09:08 | ranking input | n/a | pre-open snapshots (not held) |
| 20 | Intraday top movers at a fixed time | 10:00, 11:00, 13:00, 14:30 | 5 long, 5 short (fewer at our size) | 30 to 60 minutes, or to 15:10 | none |
| 21 | Per-stock strategy fitness | monthly | filter only | n/a | none |

---

## 1. Stocks in play: relative-volume ranked 5-minute opening range breakout

**Source.** Zarattini, Barbon and Aziz, "A Profitable Day Trading Strategy For The U.S. Equity Market", 16 February 2024, SSRN 4729284, full text at https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content

**Exact rules in the paper.**
- Universe: all US-listed stocks 2016 to 2023 (about 7,000, survivorship-free). Daily eligibility: open above $5; 14-day average volume at least 1,000,000 shares; 14-day ATR above $0.50.
- Selection: relative volume of the first 5 minutes versus the mean first-5-minute volume of the previous 14 days must be at least 100%; trade the 20 stocks with the highest relative volume.
- Direction: if the first 5-minute candle closed above its open, long only; below, short only; equal, no trade.
- Entry: stop order at the 5-minute high (long) or low (short).
- Stop: 10% of ATR14 from the entry price. No profit target. Exit at the close if not stopped.
- Size: lose 1% of the capital allocated to the position if stopped; leverage capped at 4x.
- Costs: $0.0035 per share commission; starting capital $25,000. No slippage model is described.

**Reported performance (US, 2016 to 2023, net of commission).**

| Version | Total return | IRR | Vol | Sharpe | Hit ratio | Max DD | Alpha | Beta |
|---|---|---|---|---|---|---|---|---|
| All eligible stocks, no volume filter | 29% | 3.2% | 6.6% | 0.48 | 41.4% | 13% | 3.3% | 0.01 |
| Top 20 by relative volume, 5-min range | 1,637% | 41.6% | 14.8% | 2.81 | 48.4% | 12% | 35.8% | 0.00 |
| Same, 15-min range | 272% | 17.4% | 12.2% | 1.43 | 44.7% | 11% | 16.9% | −0.01 |
| Same, 30-min range | 21% | 2.3% | 11.1% | 0.21 | 42.4% | 35% | 2.8% | 0.01 |
| Same, 60-min range | 39% | 4.1% | 10.2% | 0.40 | 42.3% | 21% | 4.4% | 0.01 |
| S&P 500 buy and hold | 198% | 14.2% | 18.3% | 0.78 | 54.9% | 34% | 0 | 1 |

Average profit per trade by relative volume: −0.02R below 100%; +0.08R above 100%; +0.38R above 3,000%. This is the clearest published evidence that the selection step, not the entry pattern, carries the result: the identical entry on unselected stocks earned 3.2% a year.

**Independent replication.** QuantConnect staff rebuilt it on the 1,000 most liquid US stocks and report Sharpe 2.396 and beta −0.042, but only for 2016, the first year of the paper's sample; 17 of 25 parameter combinations (range 5 to 25 minutes, universe 500 to 1,500) beat buy and hold; replacing the $0.50 ATR floor with "ATR above 1% of price" gave Sharpe 2.237 (https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/). User comments on the same page are less kind: "The backtest doesn't look good for other years. Does it overfit?"; one user complains of trading costs of "25%" while trading only six symbols (the base of the percentage is not stated); another puts the trade-level win rate at 17% (the paper's own best-stock tables show 17% to 24%; its 48.4% "hit ratio" is evidently measured on daily portfolio results); minute-bar backtests place the protective stop a minute late compared with live trading; shortening the range to 1 minute and widening the universe to 2,000 improved backtests (2020 to 2022) but the poster was unsure it would survive live. These comments are anecdotes, not studies.

**NSE version to test (adaptation).**
- Universe U200 with `prev_close ≥ ₹100`, `ATRpct ≥ 1%`.
- At 09:20 compute `RVOL_5`. Keep `RVOL_5 ≥ 1.0`. Rank descending. Take the top N (N = 2 to 5; the paper's 20 names were roughly the top 1% of eligible stocks, so 2 of 200 is the like-for-like figure).
- Direction from the first 5-minute candle; stop-entry at `OR_5` high or low, valid until 12:00.
- Stop distance `k × ATR14`, k in {0.10 (paper), 0.25, 0.50}. EOD exit.
- Risk 1% of equity per trade, position value capped at equity × 5 / N.
- Also test range lengths 1, 5, 15, 30 minutes.

**Costs and capacity.** See 0.2: with k = 0.10 the Indian cost is about half an R per trade. Capacity is irrelevant at ₹1.5 lakh in the top 200 names.

**Failure modes.** Stop orders at the open fill badly; very low win rate means long losing streaks; index-wide gap days fill the list with correlated names; our universe (200 large liquid stocks) is far narrower than the paper's and excludes the small volatile names that produced much of the US result (a QuantConnect user found results fell when the price floor was raised to $50).

**Feasibility at ₹1.5 lakh.** Marginal. Mechanically easy (cash MIS, both directions, 2 to 3 positions of ₹1.5 to 2.5 lakh at 5x). Economically unproven because of 0.2.

---

## 2. Opening gap fade (ordinary gaps, no catalyst)

**Source.** Adam Grimes, "Gap Study (3/3)", SMB Training blog, about October 2010: https://www.smbtraining.com/blog/gap-study-33

**What was measured.** "Closure" means price traded back at least to the previous day's range the same day, so a gap is evidently an open outside the previous day's range (inferred; the definition is in parts 1 and 2 of the series, which I did not open).
- Current S&P 500 members, two years to 1 October 2010, N = 125,811 stock-days: stocks gapped on 28.2% of days (20,261 up, 15,206 down); mean absolute gap 0.69%, median 0.42%; closure on 76% of gap days; on 70.0% after removing gaps smaller than 0.2%; on only 9.6% of gaps beyond ±5% (N = 279).
- Earlier sample in the same series: gaps between 0.2% and 5% gave 5,822 cases with a 72% closure rate; mean gap up 1.03%, mean gap down −1.12%.
- No stop, no cost, no profit figure. A commenter on the page makes the essential objection: an 80% hit rate can still lose money. The author agrees that hit rate alone proves nothing.

**NSE version to test (adaptation).**
- At 09:15: `open > prev_high` (gap up) or `open < prev_low` (gap down), with `0.2% ≤ |gap| ≤ 3%`.
- No-catalyst filter: not a results day (section 14), and `RVOL_5 < 1.5` measured at 09:20.
- Entry at 09:20 against the gap (short gap-ups, long gap-downs) only if the first 5-minute candle closed back toward the previous range.
- Target: previous day's high (for gap-ups) or low (for gap-downs). Stop: `0.5 × ATR14` beyond the opening-range extreme. Time exit 12:30, else EOD.
- Parameters to sweep: lower gap bound 0.2%, 0.5%, 1%; upper bound 2%, 3%, 5%; RVOL ceiling 1.0, 1.5, 2.0.

**India evidence.** Indirect. Tripathi and Aggarwal (2015) report that Indian stock returns reverse "within few minutes" of extreme intraday rises and falls, faster after falls than after rises (abstract only: https://publishingindia.com/archive/ijfm/prior-return-effect-in-indian-stock-market-an-intra-day-analysis). A commercial Nifty index backtest recommends skipping breakout trades on days with an opening gap above 0.8% because "large gaps distort the opening range" (https://intradaylab.com/blog/nifty-orb-breakout-strategy-backtest). Neither is a test of this rule.

**Costs.** The typical target is the gap itself, 0.4% to 1%. A 0.13% to 0.3% round trip takes a third or more of the gross.

**Failure modes.** The gap that does not fill is the one with news; losses there are several times the average win. The 9.6% closure rate for 5% gaps shows how sharply the edge inverts with size.

**Feasibility.** Yes mechanically. Edge unproven after costs.

---

## 3. Gap and go: large gap with abnormal opening volume

**Evidence.** The same SMB data: gaps beyond ±5% closed only 9.6% of the time, so fading them is wrong; that is not the same as proving continuation is profitable. Zarattini et al. show continuation pays when opening volume is abnormal (section 1). Against: Mesfin (2026), a walk-forward falsification study on Micro Nasdaq futures, 947 days of 5-minute data, 2021 to 2025: "gap continuation short" had gross +16.53 points but T = 1.46, failed year-stability and minimum sample; "opening range breakout long" T = 0.88, unstable by year; none of 14 signal families passed all five criteria (https://arxiv.org/abs/2605.04004). That is an index future, not a stock, but it is the most careful negative result I found.

**NSE version to test (adaptation).**
- `|gap| ≥ max(2%, 1.0 × ATRpct)` and `RVOL_5 ≥ 2`.
- Trade only in the gap direction: stop-entry at `OR_5` (or `OR_15`) extreme in the gap direction, valid until 11:00.
- Stop: the opposite end of the opening range, capped at `0.5 × ATR14`. EOD exit.
- Maximum 2 positions; skip if more than 20% of U200 gapped the same way by more than 1% (index-wide day).
- Sweep gap threshold 1%, 2%, 3%, 5%; RVOL threshold 1, 2, 3, 5.

**India evidence.** None found.

**Costs and failure modes.** One or two positions of ₹1.5 to 3 lakh cost 0.05% to 0.07% a round trip. Stop orders just after a gapped open slip; big gaps on index-wide news days are correlated, which is why the breadth skip is in the rule; a gap on results can reverse violently within the first half hour.

**Feasibility at ₹1.5 lakh.** Yes mechanically. Few signals per month in a 200-stock universe. Edge unproven for India.

---

## 4. Narrow range and inside days (NR4, NR7, NR7 plus inside bar)

**Definitions.** NR7: today's high minus low is smaller than each of the previous six days' ranges. NR4: same with three previous days. Inside bar (IB): today's high ≤ yesterday's high and today's low ≥ yesterday's low. The idea is from Toby Crabel (1990): range contraction precedes range expansion.

**Evidence.**
- **India, F&O stocks.** Unofficed's "Backtesting Buddha" course tests NR7 plus inside bar on all F&O stocks from 2015, 2,238 signal days, with separate buy and sell legs. The entry rule is in an earlier lesson that returned a 404; from the function name (`check_high_breakout_and_save`) it is a break of the pattern day's high for buys and low for sells: https://unofficed.com/courses/backtesting-buddha/lessons/backtesting-narrow-range-inside-bar-strategy-using-python/

  | Exit | Buy: wins / losses | Buy: average per signal | Sell: wins / losses | Sell: average per signal |
  |---|---|---|---|---|
  | Same day | 546 / 611 | +124 | 642 / 484 | +473 |
  | Next day | 631 / 724 | +280 | 633 / 718 | +101 |
  | Five days | 703 / 968 | +486 | 686 / 967 | +184 |

  The unit ("pl points") is not defined on the page I read; it looks like rupees per futures lot. No costs. The author's reading: sells do best when exited the same day, buys do best held overnight. Roughly half of the signal days trigger each side.
- **US, Bulkowski.** 1,201 stocks, January 1990 to March 2013, 29,021 trades, $10 commission, entering at the next open after a close beyond the NR7 bar: only upward breakouts in bull markets made money (+$78.79 per trade, 57% wins); bull/down −$55.52 (45%), bear/up −$91.22 (45%), bear/down −$33.63 (47%). The position size behind the dollar figures is not stated in the part I read. "5% failure" rates of 40% to 47% (https://thepatternsite.com/nr7.html).
- **QuantifiedStrategies.** Says the NR7 result on SPY is "solid" with "limited time spent in the market", "the average trade size is modest" and "performance depends heavily on exits and additional filters"; rules and numbers are behind a paywall (https://quantifiedstrategies.substack.com/p/nr7-trading-strategy-explained-for). A search summary gives 924 trades and 0.25% average gain (unverified: snippet only).

**NSE version to test.**
- After the close, flag stocks in U200 (or all F&O stocks from the daily file) with NR7; variants NR4, IB, NR7 and IB, two consecutive inside days.
- Next day: buy stop at pattern-day high, sell stop at pattern-day low, first trigger only, valid until 13:00. Stop: other side of the pattern-day range or `0.5 × ATR14`, whichever is nearer. EOD exit.
- Variant from the Indian backtest: take only the sell side intraday.
- Combine with `RVOL_5 ≥ 1` on the trigger day.

**Costs.** The pattern-day range is narrow by construction, so the stop is tight and cost per R is high, the same problem as 0.2.

**Failure modes.** Whipsaw through both sides; narrow range days cluster in quiet markets when nothing follows.

**Feasibility.** Yes. Selection needs only daily bars.

---

## 5. Volatility and range-expansion filter (trade the movers)

**Rule.** Restrict any trend-following intraday entry to stocks with `ATRpct ≥ x` (x = 1%, 1.5%, 2%) and, optionally, to stocks whose previous day's true range was at least 1.5 × ATR14 (range expansion day) or the widest of the last 7 (WR7). Rank U200 by ATRpct each morning and keep the top third.

**Evidence.**
- Zarattini et al. require ATR above $0.50 and cite Lundström (2017) that opening-range-breakout profit grows with the volatility of the underlying (statement in their literature review; I did not open Lundström).
- QuantConnect's sensitivity test: ATR floors from $0 to $2 all beat buy and hold, Sharpe 1.5 to 2.7, in 2016; so the filter level is not what drives the result (same URL as section 1).
- Indian index: on Nifty, large opening-range sessions (average 144 points) returned +30.3% against +18.6% for tiny-range sessions (average 35 points) in a 30-minute breakout test, July 2017 to March 2026, no costs (https://intradaylab.com/blog/nifty-orb-breakout-strategy-backtest).
- Gao et al. (2018): market intraday momentum is stronger on more volatile and higher-volume days (abstract: https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414).

**Honest reading.** Volatility is a necessary condition for a move large enough to pay Indian charges, not a signal of direction. It belongs in the universe filter of every strategy here, and should be tested as an on/off switch on each.

**Costs and failure modes.** No cost. The filter shrinks the tradable list and concentrates it in the same few high-beta names, so positions become more correlated; high ATR also widens any ATR-based stop, which reduces position size.

**Feasibility at ₹1.5 lakh.** Yes.

---

## 6. Intraday relative strength versus NIFTY and sector

**Rule (practitioner; adaptation for coding).**
- At T (10:00, 10:30 or 11:00) compute `RS = stock return since prev_close − beta × NIFTY return since prev_close` (beta from 60 daily returns; simpler variant uses beta = 1).
- Long candidates: top k by RS, price above session VWAP, and above `OR_30` high. Short candidates: bottom k by RS, below VWAP and below `OR_30` low.
- Take longs only when NIFTY's return since prev_close is positive at T, shorts only when negative.
- Sector confirmation: keep a stock only if the equal-weight RS of its sector peers in U200 is in the top (for longs) or bottom (for shorts) two sectors.
- k = 2 or 3. Stop: VWAP cross or `0.5 × ATR14`. EOD exit.

**Evidence.** I found no rigorous test of intraday relative strength as a stock selector in any market. A search aimed at exactly this returned only SPY timing studies and retail write-ups without results. Related but different:
- Lou, Polk and Skouras (2019): stocks with high intraday returns over the past month keep earning high intraday returns the next month (section 9). That is persistence at a monthly horizon, not same-day strength.
- Heston, Korajczyk and Sadka (2010): same-time-of-day continuation (section 8).
- Gao et al. and Baltussen et al.: index-level momentum into the close (section 7).

**India evidence.** None.

**Costs and failure modes.** Two positions of ₹1.5 to 3 lakh cost 0.05% to 0.07% a round trip. By 10:30 a strong stock has often already made much of its day's move; relative strength built on one news spike reverses; on trend days the strongest stocks are all from one sector, so two positions are really one bet.

**Feasibility at ₹1.5 lakh.** Yes mechanically. Treat as untested.

---

## 7. Index direction gate: market intraday momentum

**Evidence.**
- Gao, Han, Li and Zhou (2018, Journal of Financial Economics): on the S&P 500 ETF, 1993 to 2013, the first half-hour return measured from the previous close predicts the last half-hour return; stronger on volatile, high-volume, recession and macro-news days; also in ten other ETFs (abstract, URL above). An earlier version (1999 to 2012) reported R² of 2% and 6.34% a year for trading the last half hour in the direction of the first (https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/).
- Baltussen, Da, Lammers and Martens (2021, JFE): in more than 60 futures, 1974 to 2020, the return from the previous close to 30 minutes before the close predicts the last 30 minutes; the effect reverts over following days; linked to gamma hedging (https://www3.nd.edu/~zda/intramom.pdf). I read the abstract and did not check whether Indian index futures are in the sample.
- Zhang et al. (2018): same pattern in China (abstract only, via Consensus).
- Against: Rosa (2022, Journal of Futures Markets): the variant using the overnight return "disappears in the out-of-sample period" (abstract only, via Consensus).

**Use for stock selection (adaptation).**
- `r_open = NIFTY(09:45) / NIFTY prev_close − 1`. If `|r_open| ≥ 0.3%`, allow only stock trades in that direction for the day; otherwise allow both.
- Late-day variant: at 14:40 compute NIFTY return from prev_close; go with it in the 2 stocks of U200 with the highest beta-adjusted same-direction return, exit 15:10. The US window is the last 30 minutes; our forced 15:10 exit cuts it to a 14:40 to 15:10 proxy, which may not be the same effect.

**India evidence.** None found for the index pattern on NIFTY. Our 1-minute NIFTY data from 2022 can test it directly.

**Costs and failure modes.** The gate costs nothing but halves the number of trades on directional mornings. The late variant targets a half-hour move that is small relative to a 0.07% to 0.27% round trip. The US mechanism (gamma hedging and end-of-day rebalancing) may not carry over, and the effect weakened out of sample in one variant.

**Feasibility at ₹1.5 lakh.** Yes for the gate; marginal for the late-day trade.

---

## 8. Same-time-of-day continuation (intraday periodicity)

**Source.** Heston, Korajczyk and Sadka, "Intraday Patterns in the Cross-section of Stock Returns", Journal of Finance 2010; abstract at https://arxiv.org/abs/1005.3535

**Finding.** A stock's return in a given half-hour interval predicts its return in the same interval on later days ("exact multiples of a trading day"), for at least 40 trading days. Volume, order imbalance, volatility and spreads show the same pattern but do not explain it. Short-term reversal comes from liquidity imbalances lasting under an hour and bid-ask bounce. The authors' own practical claim is modest: "timing trades can reduce execution costs by the equivalent of the effective spread." I read only the abstract; I do not quote a return figure.

**Rule to test (adaptation).**
- Split 09:15 to 15:15 into 12 half-hour intervals. For each stock and interval j, `score = mean return in interval j over the previous 20 (or 40) sessions`.
- In interval j go long the top decile and short the bottom decile of U200 by score, or
- use the score only as a tie-breaker: when another strategy wants to enter stock s, prefer the interval where its score agrees.

**Costs.** Standalone it needs up to 12 round trips a day per name. Not viable for a retail account. Only the tie-breaker use is realistic.

**India evidence.** None.

**Feasibility.** No as a standalone strategy; marginal as an execution-timing tilt.

---

## 9. Intraday-return persistence and the overnight/intraday tug of war

**Source.** Lou, Polk and Skouras, "A tug of war: Overnight versus intraday expected returns", Journal of Financial Economics 134 (2019): https://personal.lse.ac.uk/polk/research/TugOfWar.pdf

**Findings (US, 1993 to 2013, value-weighted deciles, monthly sorts).**
- Sort on last month's intraday return (product of close/open): winner minus loser decile earns +2.19% a month intraday (t = 6.72), three-factor intraday alpha 2.41% (t = 7.70), and −1.77% a month overnight (t = −7.89).
- Sort on last month's overnight return (product of open/previous close): winner minus loser earns +3.47% a month overnight (t = 16.57) and −3.24% a month intraday (t = −9.34).
- Robust to excluding small caps and to other open and close definitions. Replicated in nine non-US markets (Canada, France, Germany, Italy, UK, Australia, Hong Kong, Japan, South Africa): intraday continuation +2.80% a month (t = 6.23). India is not in the stock sample.
- Related: Akbas, Boehmer, Jiang and Koch (2022, JFE) find that a high frequency of positive overnight returns followed by negative intraday reversals predicts higher future returns (abstract only, via Consensus); a China replication found no such effect (unverified: snippet only).

**Rule to test (daily data only).**
- Every day (or month-end), for each stock compute `ID21 = Π(close/open) − 1` and `ON21 = Π(open/prev_close) − 1` over the last 21 sessions.
- Intraday-long list: top decile by `ID21` (or bottom decile by `ON21`). Intraday-short list: bottom decile by `ID21` (or top decile by `ON21`).
- Direct test: buy at the open, sell at the close every day for the long list; reverse for the short list.
- Practical use: a direction prior. Let other intraday strategies take longs only in stocks from the long list and shorts only from the short list.

**Costs.** The direct version makes about 21 round trips a month per name. At 0.07% to 0.13% each that is 1.5% to 2.7% a month before slippage (computed), which removes the whole 2.2% to 2.8% gross spread, and the spread is long minus short, so each leg earns only part of it. The paper's returns also assume trading at the opening print. Usable only as a filter.

**India evidence.** None at stock level. Blog claims that the Nifty earned its long-run return overnight and lost money intraday exist with mutually inconsistent figures (unverified: snippet only). If true, long-only intraday strategies in India swim against a negative drift; this is cheap to verify on our daily data and should be done first.

**Feasibility.** Marginal: as a filter, yes; as a standalone, no.

---

## 10. High-volume return premium (yesterday's volume shock)

**Source.** Gervais, Kaniel and Mingelgrin, "The High-Volume Return Premium" (Journal of Finance 2001); working paper at https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/9901.pdf

**Exact rule in the paper.** NYSE stocks, August 1963 to December 1996, 161 non-overlapping 50-day intervals. The first 49 days are the reference period, day 50 the formation day. A stock is "high volume" if its day-50 dollar volume is among the top 10% of its own 50 daily volumes (rank 46 to 50), "low volume" if among the bottom 10%. Stocks under $5 in the reference period or with less than a year of listing are dropped. Buy high-volume stocks, sell low-volume stocks, hold 1, 10 or 20 days.

**Reported.** Zero-investment portfolio returns per dollar long: small stocks 0.35% over one day to 0.94% over twenty days; large stocks 0.12% over one day to 0.50% over twenty days. Stronger when the volume shock comes without an extreme return. Not explained by risk or announcements.

**Use for intraday selection.**
- Each evening flag stocks whose volume today ranks in the top 5 of the last 50 days and whose absolute close-to-close return is below 1.5%.
- Next day: long-only watchlist; enter on `OR_15` upside break with `RVOL_5 ≥ 1`; EOD exit. Also test plain open-to-close and close-to-close on the day after the flag.

**Caveat.** The published effect is a multi-day drift measured close to close. How much of the one-day 0.12% (large stocks) falls inside the trading day rather than overnight is unknown, and 0.12% is less than a round trip at ₹50,000. Sample ends in 1996.

**India evidence.** None found. An IIM Calcutta working paper shows volume and delivery percentage rise significantly before NSE bulk deals (section 18), which is a different claim.

**Costs and failure modes.** See the caveat: the expected one-day effect is of the same size as the charges. Volume shocks on results or index-rebalance days are a different animal from the paper's "no extreme return" case; filter them out.

**Feasibility at ₹1.5 lakh.** Marginal as a watchlist input; no as a standalone intraday trade.

---

## 11. Delivery-volume change from the previous day (India-specific)

**Data.** NSE publishes deliverable quantity per security each day ("Security-wise Delivery Position") (unverified: snippet only). Whether our daily price files carry the deliverable column must be checked; if not, this needs a separate download.

**What practitioners claim.** Capitalmind: a strong move with a high delivery percentage means more participants traded with a longer view, so the move "could be a much stronger indicator"; conversely "stocks which rise fast, and see a drop in delivery percentages ... the rise is not sustainable". The same article says: "It's not very useful to use this data to trade per se", and its own January 2016 tables show both the highest and the lowest delivery-percentage large caps falling (19 of 20 fell in a falling month) (https://premium.capitalmind.in/2016/02/delivery-shockers-the-january-2016-edition/).

**Academic evidence.** Thin. Granger-causality studies on a handful of stocks: delivery ratio "caused" returns in Bajaj Auto but not BPCL, 2008 to 2018 (abstract only, via Consensus); in 13 Nifty bank stocks, returns Granger-caused the delivery ratio in two (unverified: snippet only). No out-of-sample trading test found.

**Rules to test.**
- `DQ = deliverable quantity`, `DP = DQ / traded quantity`.
- Accumulation flag: `DQ ≥ 2 × mean(DQ, 20 days)` and `DP ≥ mean(DP, 20) + 10 percentage points` and close-to-close return ≥ +1%. Next day: long-only watchlist, enter on `OR_15` upside break.
- Distribution flag: same volume conditions with return ≤ −1%: short-only watchlist.
- Froth flag: return ≥ +3% with `DP ≤ mean(DP, 20) − 10 points`: fade candidate next day (short on `OR_15` downside break).
- Measure next-day open-to-close, close-to-close and 5-day returns for each flag before building anything on it.

**Costs and failure modes.** Ordinary cash MIS costs (0.1). Delivery percentage is mechanically high on low-volume days and in stocks with little intraday speculation, and jumps on index-rebalance, block-deal and F&O-expiry days (physical settlement of stock derivatives) for reasons unrelated to conviction (my reasoning, not sourced). The flag is known only after the close, so the next morning's gap may already contain the information.

**Feasibility at ₹1.5 lakh.** Yes mechanically. Evidence is anecdotal.

---

## 12. Futures open-interest change with price change (India-specific)

**Data.** Daily F&O file: per contract close, settlement price, open interest, change in OI. Sum stock-futures OI across the three expiries to avoid rollover artefacts.

**The four practitioner labels.** Price up and OI up: long build-up. Price down and OI up: short build-up. Price up and OI down: short covering. Price down and OI down: long unwinding. Broker material reads long build-up as "bullish, strong, fresh buying" and short covering as "bullish but temporary, not conviction-driven", and adds that the framework is "most useful when used alongside volume data and broader price context, not in isolation" (https://www.sahi.com/blogs/open-interest-change-in-oi-nse-guide).

**Evidence.** I found no peer-reviewed or even carefully documented test of next-day stock returns after these four states on NSE. What exists: Srinivasan (2016) relates volatility, volume and OI in NSE stock futures, 2005 to 2012, using expected and unexpected components (abstract only, via Consensus); that is about volatility, not direction. Bura and Ande (IIM Bangalore, 2011) examine whether OI and volume help predict underlying prices (unverified: snippet only; the repository would not load). Scanner sites publish daily counts of each state with no follow-up returns.

**Rules to test.**
- `dOI = total futures OI today / yesterday − 1`; `dP = futures close today / yesterday − 1` (spot close as a variant).
- Thresholds: `|dOI| ≥ 5%` (sweep 3%, 5%, 10%) and `|dP| ≥ 1%`.
- Next day: long-only watchlist after long build-up; short-only after short build-up; test short covering and long unwinding separately as both continuation and reversal.
- Exclude the last three sessions before monthly expiry and the day of any lot-size or contract-cycle change.
- Since 8 December 2025 the regulatory OI measure is delta-based, but the daily file's contract OI is still the raw count (from memory, unverified); keep using the raw count and treat December 2025 as a possible regime break.

**Costs and failure modes.** Ordinary cash MIS costs (0.1). OI changes near expiry are rollover, not new conviction; percentage changes on a small OI base are noise; every OI rise has a buyer and a seller, so the label infers who was aggressive from the price change alone. The labels are published on every broker site each evening, so anything in them is likely in the next open.

**Feasibility at ₹1.5 lakh.** Yes; selection uses free daily data and trades go through cash MIS.

---

## 13. Yesterday's top gainers and losers: continuation or reversal

**Evidence.**
- Kumar, Ruenzi and Ungeheuer, "Daily Winners and Losers" (2017 working paper), as summarised by CXO Advisory (https://www.cxoadvisory.com/technical-trading/short-the-biggest-daily-movers/): each day take the 80 biggest winners and 80 biggest losers among US stocks above $5, July 1963 to December 2015. Next-month value-weighted returns: stocks that were daily winners −0.17%, daily losers +0.39%, both −1.07%, never +0.53%. Never-minus-both earns 1.60% a month gross (4-factor alpha 1.75%). Strongest for close-to-close returns and for retail-heavy, hard-to-short stocks. Mechanism: attention-driven retail buying of whatever is on the day's ranking list. This is a one-month effect, not a next-day one.
- India: Devulapally and Tripurana (2023), NSE 500, 2014 to 2021: among daily, weekly, monthly and yearly formation periods "the high-frequency daily time scale exhibits the strongest reversal", with a reversal portfolio making "a 16-fold profit over the initial investment" (abstract: https://arxiv.org/abs/2302.13245). The abstract does not mention costs; a daily-rebalanced long-short portfolio pays them every day.
- India, intraday: Tripathi and Aggarwal (2015): reversal within minutes after extreme moves (abstract only, URL in section 2).
- India, monthly: Sehgal et al. (2002, Vikalpa) find short-term continuation at the monthly horizon (abstract only, via Consensus). So direction depends on the horizon: reversal at one day, continuation at months.
- Bali et al. (2011, JFE): stocks with the highest maximum daily return in a month underperform the next month by more than 1% (abstract only, via Consensus).

**Rules to test.**
- At the close rank U200 (and separately all NSE stocks above ₹50 with 20-day average traded value above ₹5 crore) by close-to-close return. G = top 5, L = bottom 5.
- Next day, (a) reversal: short G, long L at the open, EOD exit. (b) continuation: the opposite. (c) confirmation variants: enter only on an `OR_15` break in the tested direction.
- Split results by: volume shock or not (section 10); results day or not; gap direction next morning; overnight versus intraday component.

**Costs.** One round trip per name per day; the Indian daily-reversal evidence is gross.

**Failure modes.** Yesterday's biggest movers are mostly news stocks; fading them is fading information. Shorting yesterday's top gainer into an upward-flexing band can be painful. Five longs and five shorts at ₹15,000 each sit on the 0.27% fee floor, so the account-sized version is 2 per side.

**Feasibility at ₹1.5 lakh.** Marginal: mechanically fine (intraday shorts are allowed in cash MIS), but position count must be cut and the Indian evidence is before costs.

---

## 14. Results day and the day after

**What the evidence supports.**
- Earnings are the first catalyst on Zarattini et al.'s list of what puts a stock in play; their relative-volume ranking is a way to detect that a catalyst is actually moving the stock.
- Speed: Patell and Wolfson (1984): the initial price reaction is visible within a few minutes; simple trading-rule profits "dissipate within five to ten minutes", but significant returns appear overnight and at the next open, and variance and serial-correlation disturbances persist for hours and into the next day (abstract only, via Consensus). Old US data; the durable part is that volatility stays elevated the next day.
- India, drift: conflicting. Harshita et al. (2018) report statistically significant post-earnings drift, 2002 to 2017, robust to sub-periods and controls (abstract only). Gupta and Dhusia (2021), 100 NSE firms, 2014 to 2018, 1,130 observations, find a negative association between abnormal returns and earnings surprise and conclude the market "tends to be efficient with respect to earnings announcements" (abstract only). Dsouza et al. (2017), BSE-500, one quarter (September 2012), find slow adjustment (abstract only).
- US, drift decay: a 2022 paper titled "Rest in Peace Post-Earnings Announcement Drift" is reported to find the drift gone in large caps since about 2006 (unverified: snippet only).
- Practitioner back-test: buying every stock on its earnings day with a 20-day moving-average trailing stop, about 50,000 cases, showed "no edge" before extra filters (unverified: snippet only).

**Rules to test (need an events table: result date and time for each company).**
- Day 0 = first session in which the result can be traded (if announced after 15:30, the next session; if announced during the session, Day 0 starts at the announcement minute).
- Pre-market case: on Day 0 apply section 1 rules to the result stocks only (they will usually top the RVOL ranking anyway); record separately.
- Intraday announcement case: trigger when the stock's 5-minute volume exceeds 5 times its 20-day average for that 5-minute slot; enter in the direction of that 5-minute bar on a break of its extreme; stop at the bar's other end; EOD exit.
- Day +1: enter in the direction of Day 0's close-to-close move only if Day 0 closed in the top (bottom) quarter of its range; `OR_15` break entry; EOD exit.
- Exclusion variant: remove result-day stocks from mean-reversion strategies (sections 2 and 13).

**Data gap.** We have no announcement timestamps. Daily board-meeting dates can be collected from exchange filings; exact intraday times are harder. Without time stamps only the pre-market and Day +1 cases can be tested.

**Costs and failure modes.** Ordinary cash MIS costs, but spreads and slippage are widest in the minutes after a result. Direction in the first minutes is often reversed once the commentary or call is digested; results announced during market hours give no warning, so only a volume trigger can catch them.

**Feasibility at ₹1.5 lakh.** Yes for the trade; depends on building the events table.

---

## 15. Stocks near or breaking 52-week highs

**Evidence.**
- George and Hwang (2004) introduced nearness to the 52-week high as a momentum predictor (not opened). Liu et al. (2011, Journal of International Money and Finance): the strategy is profitable in 18 of 20 markets, significantly in 10, but "the profits are no longer significant in most markets once transaction costs are taken into account" (abstract only, via Consensus).
- Huddart, Lang and Yetman (2009), 2,000 US stocks, November 1982 to December 2006, as summarised by CXO Advisory (https://www.cxoadvisory.com/technical-trading/trading-after-52-week-highs-and-lows/): volume spikes when price crosses a 52-week high or low and then subsides; small-investor trades are mostly buys after either event; average abnormal return in the following week is about 0.6% after highs and about 5% after lows for the smallest quarter of stocks; one-month effects are smaller. So the large effect is a bounce after 52-week lows in small stocks, not a surge after highs.
- India: a student project on 250 NSE stocks, 2006 to 2010, found no 52-week-high momentum at 30 days and some at 90 and 180 days (unverified: snippet only).

**Rules to test.**
- `near = close / max(high, 252 days)`. Watchlist: `near ≥ 0.97`.
- Breakout day: when price trades above the prior 252-day high with cumulative volume by that minute at least 1.5 times its 20-day average for the same minute, buy; stop `0.5 × ATR14`; EOD exit. Long only.
- Mirror test for 52-week lows: long on the first `OR_15` upside break the day after a new low (the Huddart bounce), and short on breakdown, reported separately.

**Honest reading.** The documented effects are weekly to monthly and mostly in small stocks. Nothing shows an intraday edge. The volume spike is real, which makes these stocks candidates for section 1, not a strategy by themselves.

**Costs and failure modes.** One or two long positions; ordinary costs. Breakouts above a 52-week high in large caps often retest the level the same day; in a falling market the watchlist is empty for weeks.

**Feasibility at ₹1.5 lakh.** Yes mechanically; evidence for intraday use is weak.

---

## 16. F&O ban entries and exits, and MWPL utilisation (India-specific)

**Rules of the game.** See 0.4. As of October 2024 the limit was the lower of 30 times the average daily shares traded in the previous month or 20% of free float (Panda et al., below). The December 2025 change to delta-based OI and the new limit formula make pre-2025 ban history a different regime.

**Evidence.**
- Panda, Parida, Balakrishnan and Chari (2025), "Do Position Limits in Single Stock Derivatives Benefit Equity Markets?", AABFJ 19(5) (https://www.uowoajournals.org/aabfj/article/id/1750/; I read the PDF). Daily data on stocks under ban, 1 January 2018 to September 2022; 79 companies in all (41, 39 and 30 in the pre-COVID, COVID and post-COVID periods). The table's "days of ban" totals read 1,314, 762 and 1,313 for the three periods, the middle one being the eight months when limits were halved; the table is badly laid out, so treat the counts as approximate. Findings: average holding-period return over the ban was negative in the COVID and post-COVID periods ("stocks display a fall in returns during the ban period"); overnight return on the first ban day was negative in futures before and during COVID; halving the limit cut liquidity and volatility; overnight volatility in futures rose in the ban period; "most of these stocks faced corporate governance or regulatory issues" during repeat bans. No trading rule is tested and significance of the return figures is not the paper's focus.
- Forum observations (2018): "stock price will fire up usually after the stock comes out of the ban"; "ban brings in high volatility, both when the security is put under ban (or about to be) and when it comes out"; "there is no guarantee that price will rise or fall" (https://tradingqna.com/t/what-is-the-effect-of-f-o-ban-on-stock-price/30610). Anecdote.

**Rules to test.**
- `U = aggregate OI / MWPL` from the exchange's daily file. States: approaching (`0.85 ≤ U < 0.95`), ban day 1, in ban, exit day (first day off the list).
- (a) Exclusion: drop stocks in ban or approaching from long-side strategies (negative holding-period return in the only study).
- (b) Ban-entry day: short-only watchlist; enter on `OR_15` downside break in the cash market; EOD exit.
- (c) Ban-exit day: test long on `OR_15` upside break (forum claim) and report honestly.
- (d) Volatility use: admit ban and approaching stocks to section 1 with the wider stop (k = 0.5).

**Data gap.** We need the historical daily ban list and MWPL utilisation file. It is published daily by the exchange (current-day pages confirmed in search results; the archive location is from memory, unverified). It cannot be rebuilt exactly from the F&O price file because the limit depends on free float.

**Costs and failure modes.** Ordinary cash MIS costs. Ban stocks are often in the news for bad reasons and can gap hard; the sample of ban events per year is small (dozens of companies); the regime changed on 8 December 2025, so pre-2025 statistics may not carry over; Kotak's explainer says a stock can now enter or leave the ban during the session.

**Feasibility at ₹1.5 lakh.** Yes for cash intraday. Futures and options in a banned stock are off-limits for new positions anyway.

---

## 17. Price-band proximity (India-specific)

**Evidence.**
- Chari and Inamdar (2017), NSE: price limits delay price discovery; volume stays much higher for five days after a hit; cumulative abnormal returns of stocks hitting the upper band "continue to increase after the event day" (abstract: https://icmai-rnj.in/index.php/rb/article/view/117598). Sample and size of the effect are behind a paywall.
- Magnet effect (prices accelerate toward a limit): mixed. Malaysia: moderate magnet effect for most stocks, stronger near lower limits, and a "repellent" effect near some upper limits; Thailand: significant at stock level, stronger in small firms; China: prices fall further as the market nears its lower breaker (all abstract only, via Consensus). No NSE intraday study found.

**Rules.**
- Risk rule (not a signal): never short a fixed-band stock intraday when it is within 2% of its upper band, and never hold a long within 2% of the lower band; a locked circuit means the position cannot be closed and a short becomes an auction liability. For F&O stocks, a move to 9.9% triggers a 15-minute cooling-off; a stop order priced beyond the current band will be rejected or cancelled when bands slide (0.4).
- Momentum test on fixed-band stocks from daily data: after a close at the upper band, measure next-day open-to-close and close-to-close returns (Chari and Inamdar predict continuation); same for lower band.
- Intraday magnet test on U200 is mostly moot: these are F&O stocks without fixed bands.

**Data gap.** Daily band category per stock (exchange file). It can be approximated from daily data by checking whether the high equals the previous close times 1.05, 1.10 or 1.20.

**Feasibility.** Marginal. Fixed-band stocks are the illiquid end of the market, often barred from intraday leverage (from memory, unverified), and a ₹1.5 lakh account cannot afford one locked position.

---

## 18. Bulk and block deals as a catalyst

**Source.** Rajvanshi, "Impact of Bulk Trades on Price Discovery in Equity Market", IIM Calcutta WPS 863, April 2021: https://studentlive.iimcal.ac.in/sites/all/files/pdfs/wp_863.pdf

**Finding.** NSE bulk deals, 2010 to 2019: "front-runners can achieve around 5-7% returns within a week around the event day"; excess returns before the deal are higher for buy deals; "trading volume and delivery percentage increases significantly before the bulk deals"; lagged abnormal return and changes in volume and delivery explain the event-day abnormal return.

**Use.** The profit is before the deal is public. What a rule-follower can do is detect the signature beforehand: rising volume plus rising delivery percentage plus positive abnormal return over 3 to 5 days in a mid or small cap (this is the accumulation flag of section 11), and treat published bulk buy deals as next-day watchlist entries to be confirmed by `RVOL_5`.

**Costs and failure modes.** The documented profit is earned before disclosure. After disclosure the stock has often already moved, and small-cap bulk-deal names have wide spreads and price bands.

**Feasibility at ₹1.5 lakh.** Marginal: most bulk-deal names are outside U200, so we have no minute data for them.

---

## 19. Pre-open auction information (needs data we lack)

**Idea.** The pre-open call auction sets the 09:15 opening price; indicative price and matched quantity before the open would let the system rank gaps and volume before trading starts. Session times (order entry 09:00 to 09:08, matching to 09:12) are from memory, unverified.

**Evidence.** Acharya and Gaikwad (2014): introducing the pre-open auction on 18 October 2010 had no significant effect on market quality (abstract: https://econpapers.repec.org/RePEc:taf:oaefxx:doi:10.1080/23322039.2014.944668). Another small study finds improved efficiency (unverified: snippet only). Nobody I found tests pre-open volume as a predictor.

**What we can and cannot do.** Our minute bars start at 09:15. The auction result is visible as the 09:15 open, so the gap is available; pre-open quantity is not. Proxy: volume of the first 1-minute bar relative to its 14-day average. To test the real thing we would have to record pre-open snapshots going forward.

**Costs and failure modes.** None in trading terms; the risk is building on data we do not have. Indicative pre-open prices can be moved by orders that are cancelled before matching (my reasoning, not sourced).

**Feasibility at ₹1.5 lakh.** Marginal until the data exists.

---

## 20. Intraday top movers at a fixed time: continuation or reversal

**Rule to test.**
- At T in {10:00, 11:00, 13:00, 14:30} rank U200 by return since prev_close (variant: since open). M+ = top 5, M− = bottom 5.
- (a) continuation to 15:10; (b) reversal over the next 30 and 60 minutes; (c) continuation only for names with cumulative RVOL above 2; (d) reversal only for names with cumulative RVOL below 1.

**Evidence.** Reversal at very short horizon: Tripathi and Aggarwal (India, minutes); Heston et al. (reversal within an hour driven by liquidity imbalance and bid-ask bounce). Continuation into the close at index level: Gao et al., Baltussen et al. Continuation when volume is abnormal: Zarattini et al. So the testable hypothesis is that volume decides the sign. No direct study.

**Costs and failure modes.** Holding periods of 30 to 60 minutes earn moves of the same size as a 0.13% to 0.27% round trip on small positions; the top-mover lists at 10:00 are dominated by gap stocks, so this overlaps sections 2 and 3.

**Feasibility at ₹1.5 lakh.** Marginal: at most 2 names per side.

---

## 21. Per-stock strategy fitness (trade only where the pattern has been working)

**Evidence.**
- Zarattini et al. list the 25 best and worst stocks for each range length. Best for the 5-minute version: DDD +385R, FSLR +370R, NVDA +309R, with win rates of only 17% to 24%; worst: CMC −154R, TRGP −132R, CSX −128R. Popular, heavily traded retail names (TSLA, NVDA, AMD) are among the best; pipelines, railroads and utilities among the worst. This is in-sample description; they do not test whether last year's best names stay best.
- Naga et al. (2024), NIFTY 50 stocks: decision trees build separate intraday rules per stock; the method "does not guarantee success for every stock" and the trader is told to keep only the stocks where the back-test worked (abstract: https://arxiv.org/abs/2405.13959). That is selection on in-sample results unless done walk-forward.
- A QuantConnect user concluded performance "has more to do with the actual selected stock" than with the ATR filter (anecdote, section 1 URL).

**Rule to test (walk-forward only).**
- For a base strategy, keep for each stock the trailing 120-session sum of R (minimum 15 trades).
- Each month trade only stocks in the top third by that score. Compare with the bottom third out of sample. If the spread is not positive out of sample, drop the idea.

**Failure mode.** This is the easiest place in the whole system to fool ourselves. Without the out-of-sample comparison it is curve-fitting by another name.

**Feasibility at ₹1.5 lakh.** Yes; it is a filter and adds no cost.

---

## Source list (opened with fetch_text.py unless marked)

- https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content
- https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/
- https://www.smbtraining.com/blog/gap-study-33
- https://unofficed.com/courses/backtesting-buddha/lessons/backtesting-narrow-range-inside-bar-strategy-using-python/
- https://thepatternsite.com/nr7.html
- https://quantifiedstrategies.substack.com/p/nr7-trading-strategy-explained-for
- https://intradaylab.com/blog/nifty-orb-breakout-strategy-backtest
- https://backtestsnotsignals.substack.com/p/opening-range-breakout-real-edge
- https://arxiv.org/abs/2605.04004
- https://arxiv.org/abs/1005.3535
- https://arxiv.org/abs/2302.13245
- https://arxiv.org/abs/2405.13959
- https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
- https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/9901.pdf
- https://www3.nd.edu/~zda/intramom.pdf
- https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414
- https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/
- https://www.cxoadvisory.com/technical-trading/short-the-biggest-daily-movers/
- https://www.cxoadvisory.com/technical-trading/trading-after-52-week-highs-and-lows/
- https://publishingindia.com/archive/ijfm/prior-return-effect-in-indian-stock-market-an-intra-day-analysis
- https://premium.capitalmind.in/2016/02/delivery-shockers-the-january-2016-edition/
- https://studentlive.iimcal.ac.in/sites/all/files/pdfs/wp_863.pdf
- https://www.uowoajournals.org/aabfj/article/id/1750/ (and its PDF galley)
- https://tradingqna.com/t/what-is-the-effect-of-f-o-ban-on-stock-price/30610
- https://tradingqna.com/t/key-findings-from-sebis-analysis-of-intraday-trading-by-individuals-in-equity-cash-segment/170633
- https://icmai-rnj.in/index.php/rb/article/view/117598
- https://econpapers.repec.org/RePEc:taf:oaefxx:doi:10.1080/23322039.2014.944668
- https://blog.quantinsti.com/epat-project-gap-trading-strategy-based-on-the-markov-rule/ (Indian close-to-open gap project, 10 hand-picked stocks, no costs; read but not used as evidence because it is an overnight trade)
- https://www.angelone.in/pricing
- https://www.angelone.in/announcements/market/position-limits-for-stocks-in-ban-period-for-fo-segment-w-e-f-december-8-2025
- https://www.kotakneo.com/bulletins/sebi-new-f-o-rules-explained-delta-based-oi-new-mwpl-what-it-means-for-your-trading/
- https://zerodha.com/z-connect/business-updates/explainer-on-new-price-band-rules-for-stocks-trading-in-the-fo-segment
- https://www.chittorgarh.com/broker/angel-broking/margin-exposure/14/
- https://www.sahi.com/blogs/open-interest-change-in-oi-nse-guide
- Abstracts read through the Consensus research index, not opened at the publisher (links exactly as the index returned them):
  - Zhang et al. 2018, intraday momentum in China: https://consensus.app/papers/details/307a0a8747b85bddbe7f09248e076e12/?utm_source=claude_code
  - Rosa 2022, Understanding intraday momentum strategies: https://consensus.app/papers/details/83bed7c394255e6c9fae0763898ef141/?utm_source=claude_code
  - Akbas et al. 2022, Overnight returns, daytime reversals: https://consensus.app/papers/details/73a0ef81276d5d7584bea25d61ed7bde/?utm_source=claude_code
  - Bali et al. 2011, Maxing Out: https://consensus.app/papers/details/f47abb5422785c9bb324bdd2bb9dc869/?utm_source=claude_code
  - Srinivasan 2016, NSE stock futures volatility, volume and OI: https://consensus.app/papers/details/3008b987d7ab5e10b842556c3731b827/?utm_source=claude_code
  - Dattatreya et al. 2024, delivery ratio and returns: https://consensus.app/papers/details/00c687b495605998bcf84547f34c56e6/?utm_source=claude_code
  - Sehgal et al. 2002, contrarian and momentum strategies in India: https://consensus.app/papers/details/w:044af74e-0a43-4427-91bb-82dcb388ff25/?utm_source=claude_code
  - Patell and Wolfson 1984, intraday speed of adjustment: https://consensus.app/papers/details/w:cbe73567-b4d5-47ae-935a-6e8f752502ab/?utm_source=claude_code
  - Harshita et al. 2018, PEAD in India: https://consensus.app/papers/details/06a510fba24758c4b6f5e42c6fbadd2d/?utm_source=claude_code
  - Gupta and Dhusia 2021, PEAD in NSE firms: https://consensus.app/papers/details/96d6ef3bc6a85317a7ead3f99c49e821/?utm_source=claude_code
  - Dsouza et al. 2017, earnings reactions on BSE: https://consensus.app/papers/details/w:6f1f46d6-a650-4d5b-8fd8-c795e18d4157/?utm_source=claude_code
  - Liu et al. 2011, 52-week high internationally: https://consensus.app/papers/details/6c909a4ac6095a66a61d713ad0d10c62/?utm_source=claude_code
  - Holmberg et al. 2013, opening range breakout profitability: https://consensus.app/papers/details/w:14824e70-9183-4b87-97db-45e4444dc3f4/?utm_source=claude_code
  - Sifat et al. 2018, magnet effect in Malaysia: https://consensus.app/papers/details/404dc5079a18508d82a23b51ecd78816/?utm_source=claude_code
  - Bogousslavsky 2019, cross-section of intraday and overnight returns: https://consensus.app/papers/details/72b04b07721050debc3bfd850faab281/?utm_source=claude_code
  - Notice returned by the index with every result, reproduced because it explains the three-paper limit: "Create or connect a free Consensus account to return more than 3 results per search in Claude Code.: https://consensus.app/sign-up/?utm_source=claude_code&auth=claude_code"

## Negative or cautionary evidence

1. **Most individuals lose at this, and frequency makes it worse.** 71% of Indian individual intraday traders lost money in FY 2022-23, 80% of those making more than 500 trades a year; costs added 57% to losers' losses (SEBI study via TradingQnA, 0.3). A fully automated intraday system will be in the more-than-500-trades group by design.
2. **The base pattern has almost no edge without selection.** Unselected 5-minute opening range breakouts earned 3.2% a year in the US, Sharpe 0.48 (section 1). On the Nifty index a 30-minute version earned +91.6% over 2,122 trades from July 2017 to March 2026 with profit factor 1.23 before any cost, 2023 was a losing year, three-quarters of profit came from the short side and 65% from Thursdays and Fridays; the author expects 15% to 25% lower returns after costs (https://intradaylab.com/blog/nifty-orb-breakout-strategy-backtest). A paywalled futures test on Micro Nasdaq shows a 30.4% win rate and profit factor 1.43 in-sample, 2020 to 2022 (https://backtestsnotsignals.substack.com/p/opening-range-breakout-real-edge).
3. **A careful falsification study found nothing.** Mesfin (2026): 14 intraday OHLCV signal families on Micro Nasdaq futures, 2021 to 2025, walk-forward, none passed; 11 had gross edge below the cost floor (section 3). Different instrument, same kind of signal.
4. **The headline selection result is fragile outside its sample.** It is one paper, in-sample 2016 to 2023, no slippage model, with a co-author who sells day-trading education. The replication covers one year. Users report poor results in other years, a 17% trade win rate and material slippage on stop orders at the open (section 1).
5. **Indian charges change the arithmetic.** A stop of 0.1 ATR is about 0.25% of price; a round trip costs about 0.13% including assumed slippage; that is half an R against a published average edge of 0.08R (0.2).
6. **High hit rates mislead.** Gaps fill 70% to 76% of the time, yet no profit figure exists for fading them and the losers are the news gaps (section 2).
7. **Published anomalies shrink after costs and after publication.** 52-week-high profits are "no longer significant in most markets once transaction costs are taken into account" (section 15); the overnight-return variant of intraday momentum "disappears in the out-of-sample period" (section 7); post-earnings drift is reported gone in US large caps (unverified: snippet only) and is disputed in India (section 14).
8. **India-specific folklore is untested.** For delivery percentage, OI build-up labels and ban-list effects I found no out-of-sample trading test. Capitalmind, which publishes delivery data, says it is "not very useful to use this data to trade per se" (section 11). The only ban study finds prices fell on average during bans and notes the stocks often had governance or regulatory trouble (section 16).
9. **Daily reversal in India is gross of costs.** The NSE 500 daily-reversal "16-fold profit" (section 13) comes from an abstract that does not mention transaction costs; a daily long-short rebalance pays them every day.
10. **Long-only intraday may fight the drift.** US and international evidence (section 9) and unverified Indian index claims suggest average returns accrue overnight, not intraday. Check on our own data before running any long-biased intraday strategy.
11. **Our universe is not the papers' universe.** The US result draws on about 7,000 stocks including small volatile names; we hold minute data for 200 large liquid ones. Relative-volume extremes of 30 times normal will be rare.
12. **Our intraday sample is short.** January 2022 onward is under five years and contains one market regime change at most. Any split by year, weekday or sector will be thin.

## Open questions

1. Does relative volume in the first 5 minutes rank next-hours profit on NSE's top 200 at all, and at which stop width does the result survive 0.13% round-trip cost? (Testable now on 1-minute data.)
2. What is realistic slippage for stop-market orders between 09:20 and 09:30 in U200 names at ₹1.5 to 2.5 lakh order size? No source; needs paper trading with live quotes.
3. Do Indian stocks earn their return overnight or intraday, by size bucket, 2003 to 2026? (Daily data; decides whether long-only intraday is sensible.)
4. Do the four OI-and-price states predict the next day's open-to-close return in stock futures underlyings, 2008 to 2026, and did anything change after December 2025?
5. Does delivery percentage add anything once volume shock and return are controlled for? Requires confirming that our daily files include deliverable quantity.
6. Can we obtain the historical ban list and MWPL utilisation files back to 2008, and the daily price-band category file?
7. Can we build a results calendar with announcement timestamps? Without times, only next-morning and Day +1 tests are possible.
8. Is NR7 plus inside bar still positive on the sell side intraday after costs, 2022 to 2026, on cash prices rather than futures points?
9. Does per-stock fitness persist out of sample (section 21), or is it noise?
10. Does the NIFTY first-30-minute return predict its last 30 to 45 minutes, 2022 to 2026, given that our exit must be at 15:10?
11. Which stocks does Angel One exclude from intraday (MIS) and from intraday shorting on a given day, and is that list available through SmartAPI before the open? Not researched here.
12. The two broker explainers disagree on whether futures rollover is allowed during a ban; the exchange circular should be read by whoever handles derivatives rules.
13. I could not open: Lundström (2017) on breakout profit versus volatility; George and Hwang (2004); the Bura and Ande IIMB study on OI; the full Tripathi and Aggarwal and Chari and Inamdar papers; QuantifiedStrategies' NR7 numbers; Crabel's original statistics.
