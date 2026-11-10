# Evidence on intraday return patterns: research findings

Researcher area: academic and empirical evidence on intraday predictability (first half-hour to last half-hour momentum, rest-of-day momentum, noise-band and VWAP trend following, opening-range breakout including "stocks in play", relative volume, intraday and end-of-day reversal, overnight versus intraday returns, gap continuation versus fade, intraday seasonality of volume and volatility, day-of-week and expiry-day patterns), with Indian (NSE) evidence wherever it exists.

Written 2026-11-10 for a ₹1,50,000 Angel One (SmartAPI) account with profits reinvested.

## How to read this file

- Every number is tagged by how it was obtained. Unmarked numbers come from a page or PDF that was opened and read with `fetch_text.py`. "(unverified: snippet only)" means the number was seen only in a search-result summary and the page could not be opened (HTTP 403, paywall, SSL error or JavaScript page). "(my arithmetic)" means a figure computed here from numbers in an opened source. "(estimate)" means an assumption with no source. "(my adaptation)" means a rule I translated from US clock times or US dollar filters to NSE; the source does not state it.
- 34 web searches were run and about 50 pages or PDFs were opened. Sources that could not be opened: the only India-specific intraday-momentum paper found (ResearchGate, HTTP 403), three GitHub replications of the noise-band strategy (403), one SSRN abstract (403), the Reading University copy of the international intraday-momentum paper (502; the Lancaster conference copy of the same paper was read instead).
- Twenty-four strategies are described. Parameter variants are folded into one strategy with a range.
- The single most important finding is in "Cost hurdle" below: the published intraday edges are 2 to 12 basis points per trade before costs in the most liquid US instruments, and an Indian retail cash-market round trip costs 4 to 20 basis points before slippage. Most of what follows fails that test unless the Indian effect turns out to be several times larger than the US one. Our own backtests have to settle that; the literature cannot.

## Facts that apply to every strategy (checked against 2026 sources)

### Session structure, and the 2026 changes to the close

| Item | Rule | Effective | Source |
|---|---|---|---|
| Continuous trading, cash | 09:15 to 15:30 | long-standing | Singh and Gangwar 2018; SAHI guide |
| Pre-open call auction | Introduced 18 Oct 2010. Before that the Nifty "open" was often just a number near the previous close, so overnight versus intraday splits before late 2010 are unreliable | 18 Oct 2010 | Singh and Gangwar 2018; Capitalmind 2019; Capitalmind 2017 |
| Pre-open phases (restructured) | 09:00 to 09:05 market and limit orders; 09:05 to 09:10 limit only, random close between 09:08 and 09:10; matching 09:10 to 09:12; transition 09:12 to 09:15 | 7 Sep 2026 | SAHI guide (updated 28 Aug 2026) |
| Official close before the auction | Volume-weighted average of trades 15:00 to 15:30 | until 31 Jul 2026 | SAHI guide; Agarwalla and Pandey 2012 |
| Closing Auction Session (CAS), first version | For stocks with F&O contracts: continuous trading stops 15:15; reference price from 15:00 to 15:15 trades; order entry 15:20 to 15:30 (limit only after 15:25, random close 15:28 to 15:30); matching 15:30 to 15:35; band ±3% of reference. Non-F&O stocks unchanged (trade to 15:30, VWAP close). F&O contracts trade to 15:40 | 3 Aug 2026 | SAHI guide |
| CAS, revised | Runs 15:30 to 15:40 for F&O-eligible stocks. Reference price = VWAP 15:15 to 15:30. Orders 15:31 to 15:36 (market and limit), 15:36 to 15:40 limit only with random close in the last two minutes; matching 15:40 to 15:45; post-close 15:50 to 16:00. Stop-loss and disclosed-quantity orders not allowed in CAS. Derivatives trade to 15:45; index contracts expiring that day stop at 15:30 | 7 Dec 2026 (NSE circulars of 6 Nov 2026 after SEBI circular of 15 Oct 2026) | Kotak Neo news 9 Nov 2026; CNBC-TV18 via TradingView 7 Nov 2026 |
| Expiry-day final settlement, revised | Index: index value from constituents' VWAP 15:00 to 15:30 of continuous trading. Stock derivatives: underlying VWAP 15:00 to 15:30 across exchanges | 7 Dec 2026 | same |

Consequences for coding and backtesting:

1. Between 3 Aug 2026 and 4 Dec 2026, F&O stocks (which is nearly all of our 200-stock universe) have no continuous prints from 15:15 to 15:30, and index values shown in that window were indicative only (one broker froze its charts at 15:15 for this reason; PhonePe Share.Market note of 4 Aug 2026). The "last half-hour" in that window is 14:45 to 15:15. Before 3 Aug 2026 and from 7 Dec 2026 it is 15:00 to 15:30. Every rule below that says "last half-hour" or "exit at close" must read the session calendar, not a fixed clock time.
2. Under the first CAS the auction price could differ a lot from the last continuous price. On the 4 Aug 2026 Nifty expiry the index was 24,463.45 (down 1.25%) at 15:15 and closed officially at 24,614.9 (down 0.6%) after the auction, a jump of about 150 points (Multibagg article of 18 Aug 2026; PhonePe Share.Market). A strategy that "exits at the close" through the auction would have carried that risk; one that exits in continuous trading would not.
3. US studies exit at the 16:00 closing print with no forced-exit rule. An Indian leveraged intraday (MIS) position is closed by the broker before the close. Third-party listings give Angel One's auto square-off as 15:15 for equity and 15:20 for F&O (unverified against Angel One's own page; these listings may predate the auction). SAHI moved its auto square-off for CAS stocks to 15:10 from 3 Aug 2026. Brokers typically charge ₹50 plus GST per position squared off by their risk system (InCred Money guide, updated 25 Sep 2026). Working assumption (estimate): a leveraged position must be exited by the strategy itself by about 15:05 to 15:10; an unleveraged same-day position taken with full cash can be held to the last continuous minute. That alone removes or shortens the "last half-hour" for leveraged trades.

### Leverage, shorting and instruments

- Intraday leverage: under SEBI's peak-margin rules the broker must collect the exchange margin (VaR plus ELM) upfront for cash trades (Angel One "leverage trading" page, opened). The practical ceiling is about 5 times on liquid stocks (20% margin; general knowledge, exact per-stock margin not verified). So the account can hold at most about ₹7.5 lakh of intraday stock positions.
- Shorting: stocks can be shorted only intraday in the cash market (given in the task brief). A short in a stock that locks at the upper circuit cannot be covered and goes to auction; F&O stocks have no fixed circuit, so shorts should be limited to F&O stocks (general knowledge, not verified here).
- Index futures: one Nifty lot is 65 units, about ₹16 lakh notional at 24,600 (lot size from the seasonality file in this folder, sourced there to Angel One news; index level from the 4 Aug 2026 close above). Margin exceeds the account. Not usable.
- Index ETFs (NIFTYBEES, BANKBEES) are the only cash instrument for index-level intraday trades. The NIFTY 50 and NIFTY BANK 1-minute index series we hold have no volume, so any VWAP-based rule on the index needs a volume proxy (ETF volume or summed constituent volume). That is a data gap for strategies 3 and 6.
- Index options: affordable (one ATM weekly Nifty lot is roughly ₹6,000 to ₹10,000 of premium) and much cheaper per unit of directional exposure than cash (see below), but we have no intraday option data, so nothing option-based can be backtested by us.

### Charges and the cost hurdle (Angel One pricing page, opened 2026-11-10)

Equity intraday: brokerage lower of ₹20 or 0.1% per executed order, minimum ₹5; NSE transaction charge 0.0030699% each side; STT 0.025% on the sell side; stamp duty 0.003% on the buy side; SEBI fee ₹10 per crore; GST 18% on brokerage, transaction charge and SEBI fee. Futures: ₹20 per order, STT 0.05% on sell, transaction 0.0018299%. Options: ₹20 per order, STT 0.15% of premium on sell, transaction 0.0355299% of premium.

Round-trip statutory plus brokerage cost of one intraday equity trade, before spread and slippage (my arithmetic):

| Position size (notional) | Cost | % of notional |
|---|---|---|
| ₹15,000 | ₹41 | 0.271% |
| ₹30,000 | ₹58 | 0.193% |
| ₹37,500 | ₹61 | 0.161% |
| ₹75,000 | ₹74 | 0.098% |
| ₹1,50,000 | ₹100 | 0.067% |
| ₹3,75,000 | ₹180 | 0.048% |
| ₹7,50,000 | ₹313 | 0.042% |

Daily cost of some ways to use the account, if traded every day (my arithmetic, 250 days):

| Daily activity | Cost per day | % of capital per day | % of capital per year |
|---|---|---|---|
| 1 trade of ₹1.5 lakh (no leverage) | ₹100 | 0.067% | 17% |
| 1 trade of ₹7.5 lakh (5x) | ₹313 | 0.209% | 52% |
| 2 trades of ₹3.75 lakh (5x) | ₹361 | 0.240% | 60% |
| 5 trades of ₹1.5 lakh (5x) | ₹502 | 0.335% | 84% |
| 10 trades of ₹75,000 (5x) | ₹738 | 0.492% | 123% |
| 20 trades of ₹37,500 (5x) | ₹1,210 | 0.807% | 202% |
| 5 trades of ₹30,000 (no leverage) | ₹289 | 0.193% | 48% |

Add spread and slippage: for a market order in a Nifty 100 stock I assume 0.02% to 0.05% per side (estimate; wider in the first five minutes), and under 0.01% per side for NIFTYBEES (estimate). So a realistic all-in round trip is about 0.06% to 0.08% for an index ETF at full leverage and 0.10% to 0.25% for a single stock.

Compare the published gross edges per trade:

| Study | Edge per trade or per day, gross | Instrument |
|---|---|---|
| Gao et al. first to last half-hour | 6.67% a year = 2.6 bp per day (my arithmetic) | SPY |
| Zarattini, Aziz, Barbon noise band, unlevered | 9.7% a year over about 443 trades a year = about 2.2 bp per trade net of US costs (my arithmetic) | SPY |
| Baltussen, Da, Soebhag end-of-day reversal | 3.78 bp per day value-weighted, 6.38 to 6.86 bp equal-weighted, for a long-short pair | US stocks |
| Heston et al. same-time-of-day continuation | 3.01 bp per half-hour, decile spread | NYSE stocks |
| Lou et al. intraday persistence | 2.41% a month = about 11 bp per day for a long-short pair (my arithmetic) | US stocks |
| Zarattini and Aziz 5-minute ORB | +0.13 R per trade, R being the first 5-minute bar's range | QQQ |
| ORB on stocks in play | +0.08 R per trade when relative volume exceeds 100%, +0.38 R above 3,000%; R = 10% of the 14-day ATR | US stocks |

The index-level effects (2 to 3 bp) are smaller than the Indian ETF round trip (6 to 8 bp). The stock-level effects are gross long-short spreads that need two legs (two round trips). The ORB edges are quoted in units of a very tight stop; with a 14-day ATR of 2.5% of price (estimate), R is 0.25% of price and an Indian round trip of 0.10% to 0.25% is 0.4 R to 1.0 R, several times the reported average edge.

Options as the cheaper vehicle (my arithmetic; premium and spread are assumptions): one Nifty lot of an ATM weekly option at ₹120 premium is ₹7,800; the round trip costs about ₹66 (₹1.01 per unit), which at a delta of 0.5 equals about 2 index points or 0.8 bp of index notional; with 5 lots it is ₹0.43 per unit, about 0.35 bp. That is 5 to 15 times cheaper than the ETF per unit of direction, because STT is charged on premium rather than notional. It adds time decay, changing delta and implied-volatility risk, and we cannot test it without intraday option data. This is the main open question for the whole intraday programme.

### What the literature says about the Indian intraday environment

- Volatility shape. Nifty futures 1-minute data, Jan 2011 to Aug 2018 (Singh and Gangwar, MPRA 89689): volatility per hour-equivalent is 0.350% for 09:15 to 10:00, 0.238% for 10 to 11, 0.225% for 11 to 12 (the minimum), 0.246% for 12 to 13, 0.285% for 13 to 14, 0.327% for 14 to 15 and 0.280% for 15:00 to 15:30. Friday has the highest opening volatility (0.424%). Average hourly volatility fell by half between 2011 (0.426%) and Jan to Aug 2018 (0.209%).
- 500 most liquid NSE stocks, 2,230 trading days from 2001 (Agarwalla and Pandey, IIMA W.P. 2012-11-03; the session was then 09:55 to 15:30 with no call auctions): "reverse J" shape; the peak 5-minute volatility is almost four times the intraday low, against about twice for the S&P 500 and Nikkei 225; average 5-minute absolute returns range from 0.3% to 1.2%; the first 15 minutes are 10.2% more volatile on Mondays and 9.8% more volatile after holidays; on derivative expiry days the volatility of F&O stocks rises only in the last 30 minutes (the settlement window), by 38% to 76% in the last two 15-minute intervals for the two middle market-cap groups (42.9% and 76.4% for the third quintile, 37.7% and 53.3% for the fourth).
- Nifty 50 returns (Arora 2017, Asian Journal of Management, abstract only): a significant "open jump" effect in the first 20 minutes on every weekday and a persistent end-of-session effect.
- Overnight versus intraday. Capitalmind (Oct 2019): since 1995, of the Nifty's roughly 11,200 points, more than 10,900 were lost in open-to-close moves; all the gain came close-to-open. Capitalmind (Aug 2020): over about 3,000 days, 46% of days were positive open-to-close against 64% positive close-to-open. A widely shared 2000 to 2023 version (39,084 points overnight, minus 15,620 intraday) reached me only through secondary pages. Implication for every long intraday strategy on the index: the open-to-close drift it trades in has been flat to negative.
- Who loses. SEBI study released 24 Jul 2024 (Business Standard report, opened): 71% of individual intraday traders in the equity cash segment lost money in FY23, average loss ₹5,371; 80% of those making more than 500 trades a year lost; intraday traders at the top 10 brokers rose from 1.5 million in FY19 to 6.9 million in FY23; average trade size fell from ₹76,205 to ₹35,333; loss-makers traded more often than profit-makers. Loss-makers spent a further 57% of their trading losses on costs (unverified: snippet only).

## Summary table

| # | Strategy | Direction | Evidence | India evidence | Needs |
|---|---|---|---|---|---|
| 1 | First half-hour predicts last half-hour | momentum | strong academic, decayed out of sample | none opened | intraday index |
| 2 | Rest-of-day predicts last half-hour | momentum | strong academic | none | intraday index |
| 3 | Noise-band breakout with VWAP trailing stop | momentum | some academic (working paper, in-sample) | none | intraday, volume |
| 4 | 5-minute opening-range breakout on an index | momentum | some academic; net zero in a 2026 replication | practitioner descriptions only | intraday |
| 5 | Opening-range breakout on stocks in play (relative volume) | momentum | some academic (working paper) | none | intraday stocks |
| 6 | VWAP trend following | momentum | negative (failed replications) | none | intraday, volume |
| 7 | Full-gap plus 15-minute range breakout | momentum | practitioner | yes (Bank Nifty) | intraday |
| 8 | 2 PM day-range breakout | momentum | practitioner | yes (Bank Nifty) | intraday |
| 9 | Volatility-stretch breakout from the open (Crabel) | momentum | some academic | none | daily or intraday |
| 10 | End-of-day reversal of intraday losers | reversal | strong academic, gross only | none | intraday stocks |
| 11 | Overnight to intraday reversal (fade overnight moves) | reversal | strong academic, gross only | none | daily open and close |
| 12 | Buy small gap-downs in uptrends | reversal | practitioner, decayed | none | daily OHLC |
| 13 | Short large gap-downs | continuation | practitioner | none | daily OHLC, intraday entry |
| 14 | Index gap fade | reversal | practitioner | yes (Nifty) | daily or intraday |
| 15 | Overnight-only index holding | drift | some academic abroad; practitioner in India | yes (Nifty) | daily |
| 16 | Intraday or overnight return persistence ("tug of war") | persistence | strong academic, gross only | none | daily open and close |
| 17 | Tug-of-war intensity (monthly stock selection) | cross-sectional | some academic; failed in China and Thailand | none | daily open and close |
| 18 | Same-time-of-day continuation | seasonality | strong academic; negative after spread | none | intraday stocks |
| 19 | Narrow-range day (NR4, NR7) filter for intraday momentum | filter | some academic (in-sample table) | none | daily plus intraday |
| 20 | Signal-strength and volatility-regime filter | filter | some academic | anecdote | intraday, India VIX |
| 21 | Time-of-day window filter (U-shape) | filter | strong academic on volatility, none on returns | yes | intraday |
| 22 | Day-of-week conditioning | filter | some academic | partial | intraday |
| 23 | Expiry-day intraday pattern | event | anecdotal, and structurally broken | yes | intraday, expiry dates |
| 24 | Intraday overreaction reversal and next-day follow-through | reversal | some academic (abstracts only) | yes | intraday stocks |

## Strategies

### 1. First half-hour predicts last half-hour (market intraday momentum)

Source: Gao, Han, Li, Zhou, "Market intraday momentum", Journal of Financial Economics 129 (2018); read in the December 2015 working-paper version.

Exact rules in the paper:
- Instrument: SPY, 1993 to 2013, 13 half-hour returns per day.
- r1 = price at 10:00 divided by the previous day's 16:00 close, minus 1. It includes the overnight gap on purpose.
- r12 = return of the second-to-last half-hour (15:00 to 15:30). r13 = last half-hour (15:30 to 16:00).
- Timing rule η(r1): at 15:30 go long if r1 > 0, short if r1 ≤ 0; close at 16:00.
- Combined rule η(r1, r12): long only if r1 > 0 and r12 > 0; short only if both ≤ 0; otherwise flat.
- No stop. One trade a day. Full notional.

NSE translation (my adaptation): r1 = index at 09:45 / previous close − 1; r12 = index 15:00 / index 14:30 − 1; enter 15:00, exit at the last continuous minute (15:29; 15:14 between 3 Aug and 4 Dec 2026). For a leveraged position, shift the whole window 20 to 25 minutes earlier. Parameters to sweep: first-window length 30 minutes (paper) with 15 and 45 as variants; last-window length 30 minutes.

Instruments: signal on the NIFTY 50 or NIFTY BANK 1-minute index; trade NIFTYBEES or BANKBEES intraday (long and short). Holding period: 30 minutes.

Reported performance (SPY, 1993 to 2013): predictive R² 1.6% for r1 alone and 2.6% with r12; out-of-sample R² 1.2% and 1.8%. η(r1): 6.67% a year, standard deviation 6.19%, Sharpe 1.08, skewness 0.90. Always long in the last half-hour: −1.11% a year. Random timing: −0.68%. Buy and hold: 6.04%, Sharpe 0.29. The effect is concentrated on days when r1 is positive (R² 2.3% against 0.5% when r1 is negative; excluding the financial crisis 1.1% against 0.1%), on high-volatility days (R² 3.3% for the combined predictors), on high-volume days (R² rises from 1.1% in the lowest volume tercile to 3.1% in the highest), in the 2007 to 2009 crisis and on some news days. Costs: paying the quoted spread at 15:30 after decimalisation cut η(r1) from about 6.9% to 4.46% a year; after 2005 (spread about 1.2 bp) the figures are 7.96% before and 6.52% after. Commission was ignored.

Replication and decay:
- Li, Sakkas, Urquhart, "Intraday time series momentum: international evidence" (16 developed markets, 2005 to 2017; India is not in the sample): significant in 12 of 16 markets; alphas of 2.66% to 7.45% a year against an always-long benchmark; the US first half-hour also predicts other markets' last half-hour. The text contains no transaction-cost analysis (I searched the PDF for the term).
- Baltussen et al. 2021 (strategy 2): for equity index futures, in a regression that also includes the previous day's last half-hour return, the overnight-plus-first-half-hour signal has an in-sample R² of 1.94% but an out-of-sample R² of −1.40%; the rest-of-day signal is the better predictor (out-of-sample R² 2.77%).
- Rosa, "Understanding intraday momentum strategies", Journal of Futures Markets 2022 (abstract opened): "The predictability disappears in the out-of-sample period"; it depends on signal strength; a strategy with thresholds beats one that is always active.
- Asia-Pacific ETFs (Limkriangkrai, Chai, Zheng 2023): present in China and Japan, weak in Korea, absent in Hong Kong and Singapore, weaker during COVID (unverified: snippet only).

India-specific evidence: one paper, "Hedging demand and intraday momentum within the Indian stock market" (ResearchGate, 2024), is described in search results as finding strong momentum into the last half-hour and a 13% rise in Sharpe ratio (unverified: snippet only; the page returned HTTP 403, and its abstract snippet is partly garbled). Nothing else was found.

Cost and capacity: 2.6 bp a day gross on SPY against 6 to 8 bp per ETF round trip here. Capacity is not an issue at this size.

Failure modes: decayed out of sample in the US; depends on high volatility; the Indian close is now an auction, and the settlement window has moved twice in 2026; negative open-to-close drift in India works against the long side.

Feasibility at ₹1.5 lakh: marginal. One ETF trade a day is mechanically easy (about ₹100 at ₹1.5 lakh, ₹313 at full leverage), but the hurdle is 2 to 3 times the US effect size. Worth testing because it costs nothing to test on the index series; trade only if the Indian per-trade edge exceeds about 10 bp or if an options vehicle is validated.

URLs: https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf ; http://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-092-Zeming-Li.pdf ; https://econpapers.repec.org/RePEc:wly:jfutmk:v:42:y:2022:i:12:p:2218-2234

### 2. Rest-of-day return predicts the last half-hour (hedging-demand momentum)

Source: Baltussen, Da, Lammers, Martens, "Hedging demand and market intraday momentum", Journal of Financial Economics 142 (2021).

Exact rules: r_ROD = return from the previous close to 30 minutes before today's close (overnight + first half-hour + middle + second-to-last half-hour). At 30 minutes before the close take a position with the sign of r_ROD; close at the close. Variants in the paper: sign of the overnight-plus-first-half-hour return (the Gao signal), and a version that trades only when both agree.

NSE translation (my adaptation): r_ROD = index at 15:00 / previous close − 1; hold 15:00 to 15:29 (calendar-aware as in strategy 1).

Reported performance: more than 60 futures (equity, bond, commodity, currency), 1974 to 2020. Equity index futures, pooled, in a regression that also includes the previous day's last half-hour return: slope on r_ROD 4.14 (t = 7.50), R² 2.91%, out-of-sample R² 2.77%. By sub-period for equities: 1974 to 1999 slope 5.96 (t = 4.80), R² 3.41%; 2000 to 2020 slope 3.98 (t = 6.65), R² 2.34%. Annualised Sharpe ratios of the simple timing strategy between 0.87 and 1.73 at asset-class level. The previous day's last-half-hour return predicts today's negatively for equities (slope about −6.7, t about −2.7), and the effect reverts over the following days. The paper states: "we do not consider transaction costs ... the strategy as presented might not be exploitable to many investors after accounting for transaction costs"; it gives a positive net Sharpe for S&P 500 futures at a one-tick cost. Mechanism: dealers who are short gamma (options, leveraged ETFs) must trade with the move late in the day; the effect is present when dealer gamma is negative and stronger the more negative it is, and absent on positive-gamma days (the last clause is from a secondary summary; unverified: snippet only).

India-specific evidence: none opened. India is not in the paper (I searched the text for India and Nifty). India has no leveraged ETFs of size; the option market is very large, but dealer gamma is not observable from our data.

Cost, failure modes, feasibility: as strategy 1. The same paper family (Baltussen, Da, Soebhag 2025) decomposes the effect: the time-series strategy at stock level earns about 2.8 bp a day, the same order as the index effect. Marginal.

URLs: https://www3.nd.edu/~zda/intramom.pdf ; https://www3.nd.edu/~zda/EOD.pdf

### 3. Noise-band breakout with VWAP trailing stop ("Beat the Market")

Source: Zarattini, Aziz, Barbon, Swiss Finance Institute Research Paper 24-97 (first version May 2024, this version 3 Feb 2025). Working paper by a research firm and a proprietary trading educator; not peer reviewed.

Exact rules in the paper (SPY, 1-minute bars):
1. For each minute of the day HH:MM and each of the previous 14 days, move = |Close(HH:MM) / Open(09:30) − 1|. σ(HH:MM) = average of the 14 values.
2. UpperBound(HH:MM) = max(today's open, yesterday's close) × (1 + VM × σ(HH:MM)); LowerBound(HH:MM) = min(today's open, yesterday's close) × (1 − VM × σ(HH:MM)). VM (volatility multiplier) = 1 in the paper; 1.5 gave the best Sharpe in their sensitivity test.
3. Decisions only at HH:00 and HH:30 (first at 10:00, 30 minutes after the open). Long if price is above the upper bound, short if below the lower bound.
4. Exit: base version, when price crosses the opposite bound (and reverse). Improved version, trailing stop: long is closed when price is below max(upper bound, VWAP); short when above min(lower bound, VWAP). VWAP uses regular-hours data only. Stops are also checked only on the half-hour grid. All positions closed at the close.
5. Size: base 100% of equity. Dynamic: shares = equity × min(4, 2% / σ_daily) / open, where σ_daily is the standard deviation of the last 14 daily returns.
6. Costs assumed: commission $0.0035 a share and slippage $0.001 a share.

NSE translation (my adaptation): open 09:15; grid 09:45, 10:15, ... 15:15; flat by the last continuous minute or by 15:05 if leveraged; leverage cap 5 instead of 4; VWAP from 1-minute typical price times volume of the traded instrument. On the index series there is no volume, so either run it on NIFTYBEES bars (not in our data) or drop the VWAP term and use the upper or lower bound alone as the stop (the paper's intermediate variant).

Reported performance (2007 to early 2024, net of the assumed costs):

| Variant | Total return | Annual | Volatility | Sharpe | Hit ratio | Max drawdown |
|---|---|---|---|---|---|---|
| Stop at opposite band, 100% size | 178% | 6.2% | 10.9% | 0.61 | 54% | 21% |
| Stop at current band or VWAP, 100% size | 380% | 9.7% | 7.7% | 1.24 | 43% | 12% |
| Same, volatility-targeted up to 4x | 1,985% | 19.6% | 14.3% | 1.33 | 43% | 25% |
| SPY buy and hold | 227% | 7.2% | 20.2% | 0.45 | 54% | 56% |

Trades: 5,494 (base) and 7,668 (improved), about 1.8 a day; average profit 9 to 10 cents a share. Worst day of the base version −10.33%. Sharpe rises with the VIX at the open (about 1.5 over all days, about 3.5 when VIX exceeds 40). Day of week (average daily profit, levered version): Monday 9 bp (t = 1.84), Tuesday 9 (2.00), Wednesday 18 (3.42), Thursday 12 (2.39), Friday 13 (2.39). Regressing daily strategy return on the prior day's 5-day RSI gives a slope of −3.25 (p = 0.001): the strategy does better after recent market declines.

Replication: the whole sample is in-sample; the parameters (14 days, half-hour grid, VM = 1) were not tuned much but were not held out either. Independent replications on S&P 500 and Nasdaq futures exist on GitHub and one 2026 SSRN paper reports that one index point of slippage on stop fills removes 22% of the edge in Nasdaq futures (unverified: snippet only; pages returned 403). No Indian replication was found.

Cost and capacity: unlevered, 9.7% a year over about 443 trades a year is about 2.2 bp per trade net of roughly half a basis point of US cost (my arithmetic). At 6 to 8 bp per Indian ETF round trip the US-sized edge is negative.

Failure modes: sharp intraday reversals (the paper's example, 20 Jan 2022, lost 2.19% in the base version); tighter stops raise trade count by 40%; an auction close; no volume on the index series.

Feasibility at ₹1.5 lakh: marginal. Mechanically simple (one instrument, at most a few trades a day), but cost per trade is about three times the US net edge per trade. Test on the index series first with the band-only stop.

URL: https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content

### 4. Five-minute opening-range breakout on an index instrument

Source: Zarattini and Aziz, "Can day trading really be profitable?" (SSRN 4416622, April 2023). Rules taken from the CXO Advisory summary and a 2026 replication post, both opened; the authors' own page was opened for the headline numbers.

Exact rules:
- First 5-minute bar of the session. If close > open, buy at the open of the second 5-minute bar; if close < open, sell short; if equal (doji), no trade.
- Stop: low of the first bar for a long, high for a short. R = |entry − stop|.
- Target: 10 R. Otherwise exit at the close.
- Size: lose 1% of capital if the stop is hit; leverage capped at 4.
- Variant for the 3x ETF: stop = 5% of the 14-day ATR, no target, exit at close.
- Costs assumed: $0.0005 a share commission, no spread, no slippage.

NSE translation (my adaptation): first bar 09:15 to 09:20, enter 09:20, exit by 15:05 to 15:10 if leveraged. Parameter range: opening range 5, 15, 30 minutes; target 10 R or none; stop at range extreme or 5% to 25% of ATR.

Reported performance: QQQ, 1 Jan 2016 to 17 Feb 2023, 1,795 trades, 33.2% a year against 14.9% for QQQ (CXO summary); hit rate 24% and +0.13 R per trade (replication post); 3x ETF version 1,484% total against 169% for QQQ, annualised alpha 33% (authors' page).

Replication (MQL5 blog by T.-P. Krueger, 25 Sep 2026; a blog, but it publishes its tables): same rule, unchanged, on five index CFDs, Jan 2015 to Jun 2026, about 2,900 sessions each.

| Market | Gross R per trade (t) | Net R per trade (t) | Rule minus random direction, net (t) |
|---|---|---|---|
| Nasdaq 100 | +0.131 (2.9) | +0.002 (0.0) | +0.124 (2.1) |
| S&P 500 | +0.119 (2.4) | −0.081 (−1.6) | +0.092 (1.2) |
| Dow | +0.048 (1.1) | −0.081 (−1.9) | +0.021 (0.4) |
| DAX | +0.116 (2.4) | −0.038 (−0.8) | +0.128 (2.5) |
| FTSE | +0.050 (1.1) | −0.079 (−1.8) | +0.106 (2.0) |

The author's reading: the paper's gross figure reproduces; net of spread and slippage no market is distinguishable from zero and four of five are negative; 2015 to 2017 is negative in every market; 2021 to 2026 gives +0.06 R on the Nasdaq at best; hit rate near 20% with a 10 R target means losing streaks of ten or more are routine. The first candle does carry about 0.1 R of directional information against a random-direction benchmark.

Related evidence from the same authors (strategy 5 paper): an unconditional 5-minute ORB across all liquid US stocks earned only 3.2% a year (Sharpe 0.48) in 2016 to 2023; with the relative-volume filter the 5-minute range beat 15 minutes (Sharpe 1.43), 30 minutes (0.21) and 60 minutes (0.40).

India-specific evidence: descriptions only. Marketcalls (2008) describes a 15-minute range breakout in the direction of the gap with an exit after two hours and no statistics. Broker education pages describe 15-minute ORB without results. A QuantInsti course project lists ten first-candle patterns on Nifty 50 stocks, "average 4-5 trades per month per script", with no statistics in the text. I found no Indian backtest with costs and a sample period.

Cost and capacity: with R equal to the first 5-minute range (perhaps 0.15% to 0.3% of the index; estimate), 0.13 R is 2 to 4 bp against a 6 to 8 bp ETF round trip.

Failure modes: low-volatility years; costs as a share of a tight stop; forced exit before the close cuts the right tail that pays for everything.

Feasibility: marginal. Same instrument and cost as strategy 1.

URLs: https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy ; https://www.mql5.com/en/blogs/post/776235 ; https://concretumgroup.com/can-day-trading-really-be-profitable/ ; https://www.marketcalls.in/nifty-technicals/15-minute-opening-range-breakout.html ; https://blog.quantinsti.com/intraday-low-frequency-trading-strategy-project-rajtk/

### 5. Opening-range breakout on stocks in play (relative volume)

Source: Zarattini, Barbon, Aziz, "A profitable day trading strategy for the U.S. equity market", Swiss Finance Institute Research Paper 24-98 (16 Feb 2024; SSRN 4729284). Working paper.

Exact rules in the paper:
- Universe each day: all US-listed stocks (about 7,000, survivorship-free) with opening price above $5, average daily volume over the previous 14 days of at least 1,000,000 shares, and 14-day ATR above $0.50.
- Relative volume = volume in the first 5 minutes today / average first-5-minute volume over the previous 14 days. Require at least 100%. Take the 20 stocks with the highest relative volume.
- Direction: first 5-minute candle up means long only, down means short only, doji means no order.
- Entry: stop order at the 5-minute high (long) or low (short), working for the rest of the day.
- Stop loss: 10% of the 14-day ATR from the entry price. No profit target. Exit at the close.
- Size: a stopped trade loses 1% of the capital allocated to that position; total leverage capped at 4.
- Costs: $0.0035 a share commission. I saw no spread or slippage charge in the sections read.
- Variants: 15-, 30- and 60-minute ranges with relative volume measured over the same window.

NSE translation (my adaptation; the thresholds are mine and need testing): universe = our roughly 200 liquid stocks, restricted to F&O stocks for shorts; price above ₹100; 14-day average turnover above a floor; ATR(14) at least 1.5% of price; relative volume from the 09:15 to 09:20 bars; top N with N between 3 and 5 at this capital; entry valid until 14:30; exit by 15:05 to 15:10. The stop width must be a parameter (10%, 25%, 50% of ATR, or the opening-range extreme), because cost in units of R is the binding constraint here.

Reported performance (1 Jan 2016 to 31 Dec 2023, $25,000 start):

| Variant | Total | Annual | Volatility | Sharpe | Hit ratio | Max drawdown | Alpha | Beta |
|---|---|---|---|---|---|---|---|---|
| ORB on all filtered stocks | 29% | 3.2% | 6.6% | 0.48 | 41.4% | 13% | 3.3% | 0.01 |
| ORB, relative volume ≥ 100%, top 20 | 1,637% | 41.6% | 14.8% | 2.81 | 48.4% | 12% | 35.8% | 0.00 |
| 15-minute version | 272% | 17.4% | 12.2% | 1.43 | 44.7% | 11% | | |
| 30-minute version | 21% | 2.3% | 11.1% | 0.21 | 42.4% | 35% | | |
| 60-minute version | 39% | 4.1% | 10.2% | 0.40 | 42.3% | 21% | | |
| S&P 500 | 198% | 14.2% | 18.3% | 0.78 | | 34% | | |

Average profit per trade by relative volume: below 100%, −0.02 R; above 100%, +0.08 R; above 3,000%, +0.38 R. Per-stock win ratios of the best performers are only 17% to 24%. Worst day −1.61%.

Replication: a QuantConnect re-creation covers 2016 only (the first year of the paper's own sample): Sharpe 2.396, beta −0.042; 17 of 25 combinations of range length (5 to 25 minutes) and universe size beat buy and hold; Sharpe between 1.5 and 2.7 across ATR thresholds from $0 to $2. That is a code check, not an out-of-sample test. I found no test on data after 2023 and none outside the US.

India-specific evidence: none.

Cost and capacity: with ATR at 2.5% of price (estimate), R is 0.25% of price. An Indian round trip of 0.07% to 0.16% plus slippage on a stop-entry in the first minutes (estimate 0.05% to 0.10%) is 0.5 R to 1.0 R, against an average edge of +0.08 R. Twenty positions a day at full leverage would cost about 0.8% of capital a day in charges alone (table above). The paper's sizing (1% loss at a stop 0.25% away) implies notional of four times the allocated capital per name, which is the whole leverage limit. A 200-stock universe will rarely contain 20 names with unusual volume; the US result comes from choosing among thousands.

Failure modes: stop-entry slippage in fast openings; gaps through a 10%-of-ATR stop; upper-circuit locks on shorts in non-F&O names; relative volume is mechanically high on expiry, index-rebalance and results days.

Feasibility at ₹1.5 lakh: marginal. It can be run with 2 to 5 names at ₹1.5 lakh to ₹3.75 lakh notional each (charges 0.05% to 0.07% per trade), but only if a wider stop keeps cost below about 0.2 R and the edge survives that change. This is the stock-level strategy most worth testing because the selection variable (relative volume) is observable in our data.

URLs: https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content ; https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/ ; https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/

### 6. VWAP trend following

Source: Zarattini and Aziz, "Volume Weighted Average Price (VWAP): the holy grail for day trading systems" (SSRN 4631351, 2023). Rules from the authors' summary page and a QuantConnect discussion that re-implemented it.

Exact rules: 1-minute bars; session VWAP restarted at the open; wait one minute after the open; long when the 1-minute close is above VWAP, short when below, flip on each cross; flat one minute before the close; full notional (QQQ) or the 3x ETF.

Reported performance (2 Jan 2018 to 28 Sep 2023): $25,000 to $192,656 on QQQ net of commissions (671%), maximum drawdown 9.4%, Sharpe 2.1, against 126%, 37% and 0.7 for buy and hold. The 3x ETF version: 8,242% (unverified: snippet only).

Replication: negative. The QuantConnect thread ("not so fast") could not reproduce it: the first re-implementation performed poorly; QuantConnect's founder noted it "is pretty sensitive to the minimum filter and gets eaten alive by covid"; another user improved it with a 2% dead-band around VWAP "but I am far from approaching the original paper results"; a later configuration-matched version reproduces the in-sample behaviour but "out-of-sample and after realistic spreads it looks a lot less exciting". One public re-run shows a 49% drawdown with turnover around 2,100% (unverified: snippet only).

India-specific evidence: none. VWAP on the index series is not computable from our data.

Cost: the rule flips on every cross, so trade count is high and every flip pays a full Indian round trip.

Feasibility at ₹1.5 lakh: no. Use VWAP only as a trailing stop inside strategy 3.

URLs: https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/ ; https://www.quantconnect.com/forum/discussion/16706/bear-bull-traders-039-paper-on-quot-the-holy-grail-quot-not-so-fast/

### 7. Full-gap plus 15-minute range breakout (Indian practitioner version)

Source: Marketcalls (Dinesh Tarte, 17 Jun 2015), with AmiBroker code.

Exact rules:
- Full gap: today's open above yesterday's high or below yesterday's low.
- Opening range: high and low of the first 15 minutes (to 09:30).
- Buy if the range high breaks, short if the range low breaks, after either kind of gap.
- Long stop: yesterday's low. Short stop: yesterday's high. (Readers noted the code's stop condition does not match this description.)
- Target: range high × (1 + 2.5%) for longs, range low × (1 − 2.5%) for shorts; otherwise exit at 15:15.
- Backtest settings stated: Bank Nifty, 5-minute bars, three years, ₹100 commission per leg. The report is a download I could not read, so no statistics.

Reported performance: none readable. A reader who ran it on 12 to 13 Nifty stocks over seven years of 5-minute data reported a maximum profit of about ₹60,000 on ₹2,50,000 with ₹100 brokerage per trade and called it "not good enough to deploy in practice" (comment on the page).

Cost and feasibility: Bank Nifty must be traded through BANKBEES or options at this capital. Marginal. Included because it is the best-specified Indian ORB variant and directly codeable on our index bars.

URL: https://www.marketcalls.in/amibroker/full-gap-open-range-strategy-amibroker-afl-code.html

### 8. 2 PM day-range breakout (Bank Nifty)

Source: TradingQnA post by the founder of an algo-vendor (28 May 2018). Vendor source.

Exact rules: at 14:00 record the day's high and low of Bank Nifty. Place a buy stop above the high and a sell stop below the low. Stop loss: the opposite order (stop and reverse) or a fixed 0.5%. Exit at 15:20.

Reported performance: 2010 to 2018, more than 2,200 trading days; a trade triggered on about half of them; more than 17,000 index points in total; 48% winners; largest single loss about 130 points; 2017 flat "because of drastic reduction in volatility". No costs or slippage: "I haven't considered transaction cost & slippages".

My reading (my arithmetic): 17,000 points over roughly 1,100 trades is about 15 points a trade, which at an average index level near 20,000 is 7 to 8 bp gross, about the same as an Indian ETF round trip. Break-even at best in cash.

Failure modes: low volatility; since Aug 2026 the square-off and auction changes shorten the window after 14:00; the rationale given (European open) is a story, not a test.

Feasibility: marginal (BANKBEES or options). Codeable on our NIFTY BANK bars from 2022, which is an out-of-sample period for this claim.

URL: https://tradingqna.com/t/orb-opening-range-breakout-2pm-banknifty-intraday-strategy/39756

### 9. Volatility-stretch breakout from the open (Crabel)

Source: Toby Crabel's 1990 book as described in the literature review of the strategy 5 paper (opened), which also summarises the academic tests. The stretch formula itself comes from secondary pages (unverified: snippet only).

Rules: noise = the smaller of (high − open) and (open − low) for each day; stretch = 10-day average of noise, optionally times a multiple (1 to 2). Buy stop at open + stretch, sell stop at open − stretch; exit at the close; optional stop at the opposite level.

Evidence as summarised in the opened paper: Holmberg, Lönnbark and Lundström (2013), US crude oil futures 1983 to 2011: a volatility breakout from the open was significantly profitable, mostly in 2000 to 2011. Lundström (2017): profitability rises with the volatility of the underlying (crude oil and S&P 500 futures). Tsai et al. (2019), Dow, S&P 500 and Nasdaq index futures: most profit when the range is defined within 5 minutes of the open; no stops or targets. Wu et al. (2020), Taiwan index futures 2007 to 2018: profit targets hurt, stop losses help. None of these was opened individually.

India-specific evidence: none.

Feasibility: marginal, same cost logic as strategy 4. It can be approximated on daily open, high, low and close (a trigger is known to have occurred if the high or low passed the level; the order of events is ambiguous when both levels were touched), so it is one of the few breakout rules testable on the long daily history from 2003.

URL: https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content

### 10. End-of-day reversal: buy the day's losers for the last half-hour

Source: Baltussen, Da, Soebhag, "End-of-day reversal" (April 2025 version).

Exact rules: split the day into overnight, first half-hour, middle, second-to-last half-hour and last half-hour. ROD3 = return from the previous close to one hour before today's close (the second-to-last half-hour is skipped to avoid bid-ask bounce). Sort stocks into quintiles on ROD3. Hold for the last half-hour only: long the lowest quintile, short the highest. Value- or equal-weighted, price filter $5 or $1.

NSE translation (my adaptation): ROD3 = price at 14:30 / previous close − 1; enter 15:00, exit at the last continuous minute; with 200 stocks, quintiles of 40 are too many to trade, so test the bottom 3 to 5 losers long only.

Reported performance (US common stocks, Jan 1993 to Dec 2019, gross): value-weighted low-minus-high 3.78 bp a day (t = 10.69; six-factor alpha 3.71 bp); equal-weighted 6.38 bp (t = 17.30) in the main sort and up to 6.86 bp depending on the price filter; about 9.5% and 17.3% a year. Most of it is the losers rising (lowest quintile +3.55 bp value-weighted; highest −0.22 bp). Present in almost every 3-year window and among the largest and most liquid stocks; robust to skipping the last five minutes; the last-half-hour move itself reverts the next day. The authors: "the strategy as presented might not be exploitable by many investors after accounting for transaction costs". Drivers proposed: attention-driven retail buying and short-sellers reducing risk before the close.

Related: Komarov (2017), US stocks 1993 to May 2010, via the CXO summary: both extreme morning winners and extreme morning losers (deciles on the 09:30 to 12:00 return) gain in the last half-hour, 0.077% and 0.062% a day gross; average half-hour returns were negative in the first hour and positive in the last half-hour and overnight.

India-specific evidence: none. India has the ingredients (heavy retail intraday participation, forced closing of intraday shorts before the close), which is a reason to test, not evidence.

Cost: 4 to 7 bp gross for two legs against at least 13 bp for two Indian round trips at ₹1.5 lakh per leg.

Feasibility: no as a long-short portfolio; marginal as a long-only top-few rule if the Indian loser bounce is several times the US one. The forced-exit time matters: leveraged positions cannot be held through the window being measured.

URLs: https://www3.nd.edu/~zda/EOD.pdf ; https://www.cxoadvisory.com/momentum-investing/intraday-stock-price-momentum-and-reversal-trading/

### 11. Overnight-to-intraday reversal (fade the overnight move)

Source: Della Corte, Kosowski, Wang, "Market closure and short-term reversal" (Nov 2015), via the CXO Advisory summary (opened).

Exact rules: each morning compute every asset's close-to-open return. Weight each asset by minus its deviation from the cross-sectional average (long below-average, short above-average; long and short sides equal). Hold from the open to the close. Margin of 50% assumed for return calculations.

Reported performance (gross): US stocks Jan 1993 to Dec 2014, 1.68% a day, annualised Sharpe 24.16, against 0.33% and 5.52 for the conventional close-to-close reversal; open-to-close to open-to-close shows momentum instead (−0.17% a day). Weaker for European, Japanese and UK stocks and much weaker for futures. Concentrated in small illiquid stocks but survives in large ones. For S&P 500 stocks most of the profit arrives immediately after the open; a one-minute delay "dramatically reduces" it. Turnover about 100% a day; nothing is net of costs. Later evidence that it faded among S&P 500 stocks in 2011 to 2017 while persisting in small stocks: (unverified: snippet only).

NSE notes (my adaptation): the official open is the pre-open auction price, known a few minutes before continuous trading starts at 09:15, so the signal can be computed before the first continuous trade; but execution is at 09:15 prices, not at the open used in a daily-data backtest. A daily-OHLC test therefore overstates the result by exactly the part the paper says is earned in the first minute. Test both: daily (upper bound) and 1-minute with entry at 09:16.

India-specific evidence: none found.

Feasibility at ₹1.5 lakh: marginal. A handful of positions (largest gap-downs long, largest gap-ups short among F&O stocks) at ₹1.5 lakh notional each is workable; costs are 0.07% plus opening slippage per name, so the per-name edge needs to exceed roughly 0.15% to 0.2%.

URL: https://www.cxoadvisory.com/technical-trading/overnightintraday-return-reversal-trading/

### 12. Buy small gap-downs in uptrending stocks

Source: E. P. Chan's "buy on gap" rule as quoted and re-tested by A. Pavlov (Financial Noob, 27 Jul 2024), and Brian Stanley (QuantRocket, 2 Sep 2020).

Exact rules (Chan, as quoted):
1. At the open select stocks whose return from the previous day's low to today's open is below minus one standard deviation, the standard deviation being that of daily close-to-close returns over 90 days.
2. Keep only those opening above the 20-day moving average of closes.
3. Buy the 10 with the lowest return from the previous low (all if fewer than 10).
4. Sell at the close.

Reported performance: Pavlov, constituents of a US small-cap value ETF (a survivorship-biased list), rolling 3-year windows starting 2005 to 2018, 0.1% two-way cost: Sharpe 3.58 before costs for 2005 to 2008; Sharpe 1.57 and 70% a year after costs for 2008 to 2011; after the book appeared in 2013 only one window (2014 to 2017) is positive; "a clear downward trend in Sharpe ratios". QuantRocket: without the open-above-moving-average condition (so including large gaps), buying gap-downs in liquid US stocks lost money; with it, the equity curve was positive (no statistics given).

India-specific evidence: none. Capitalmind remarks that stocks that break out on gaps "rarely fall back" while index gaps mean-revert, with no numbers.

Feasibility at ₹1.5 lakh: marginal. Ten positions of ₹75,000 at full leverage cost about 0.10% each plus opening slippage, similar to the assumed cost in the US test under which the edge had already gone by the mid-2010s. Testable on daily OHLC (with the same opening-price caveat as strategy 11).

URLs: https://financialnoob.substack.com/p/buy-on-gap-strategy-and-its-performance ; https://www.quantrocket.com/blog/buy-or-sell-down-gaps/

### 13. Short large gap-downs (gap continuation)

Source: QuantRocket blog (2 Sep 2020).

Exact rules: universe US common stocks in the top 10% by dollar volume that closed above their 20-day moving average; gap-down = today's open below yesterday's low minus one standard deviation (window not stated in the post); short one minute after the open; cover at the close. Entering 5 to 10 minutes after the open worked better than entering immediately, and large caps worked better than small caps.

Reported performance: 2014 to 2020, Sharpe 1.30, annual return 10% (costs not described). The mirror-image long trade "is so bad, it suggests a good strategy". Interpretation in the post: small gaps in an uptrend recover, large gaps that break the trend keep falling.

India-specific evidence: none. Intraday shorting of F&O stocks makes it executable.

Feasibility: marginal; few signals a day in a 200-stock universe, so position size per trade can be large and percentage cost low (0.05% to 0.07%). Needs 1-minute data for the delayed entry; the open-to-close version is testable on daily OHLC.

URL: https://www.quantrocket.com/blog/buy-or-sell-down-gaps/

### 14. Index gap fade

Source: Capitalmind, "Nifty gaps and future returns" (March 2017); Marketcalls gap tutorials (2015).

What the sources say: Capitalmind, after tabulating Nifty performance following gap-ups and gap-downs (tables are images I could not read): "Gaps are generally mean reverting with one seeing a small retracement most of the time"; after gap-downs "we see way more Greens than Reds"; "historical evidence is geared more towards a short term reversal versus a runaway rally". It also explains that gap statistics before 2011 are distorted because the index open was not a real traded price before the pre-open session. Marketcalls describes fading "exhaustion" gaps that occur after a one-directional, overbought or oversold run, with chart examples only. Fill-rate figures circulating on blogs (same-day fill of 40% to 50% of gap-ups; gaps under 70 points filled within 90 minutes 62% of the time in 2020 to 2024) have no stated method (unverified: snippet only).

Rules to test (my specification, since no source gives exact ones): if the Nifty opens more than g away from the previous close (g from 0.3% to 1.0%), take the opposite side at 09:16 in NIFTYBEES; target the previous close; stop at k times the gap beyond the open (k from 0.5 to 1); exit at 15:05 if neither is hit. Daily variant for the long history: gap-down days, buy the open, sell the close.

Feasibility at ₹1.5 lakh: marginal; one ETF trade on perhaps one day in five. Daily version testable from 2011.

URLs: https://premium.capitalmind.in/2017/03/nifty-gaps-and-future-returns/ ; https://www.marketcalls.in/futures-and-options/trading-the-gap-up-and-gap-down-part-2.html

### 15. Overnight-only index holding (buy the close, sell the open)

Sources: Capitalmind (2019, 2020); Marketcalls (1 Sep 2018).

Exact rules (Marketcalls): buy one lot of Nifty futures at 15:15, sell at 09:30 the next day, every day. ETF version (my adaptation): buy NIFTYBEES in the last minutes of continuous trading, sell at 09:16 to 09:30.

Reported performance: Marketcalls, Nifty futures 1-minute data, Jan 2011 to Jun 2018, one lot (75 units then): +595% on ₹1 lakh with zero costs; with a 0.02% cost the ₹1 lakh account lost 67% within 185 trades and could no longer fund the margin; with ₹2 lakh starting capital it made 94.65% in total, 9.3% a year. The author's conclusion: "most of the market performance comes by holding positions overnight. However one cannot capitalize the entire performance returns majorly due to higher number of trades involved and transactional cost." Capitalmind figures are in the environment section above.

International context: the overnight-versus-intraday split is well documented in the US (Lou, Polk, Skouras 2019, strategy 16; Komarov's half-hour averages in strategy 10).

Cost: a NIFTYBEES delivery round trip costs about 0.07% of ₹1.5 lakh plus spread (seasonality file in this folder). The average overnight return is of the same order: one secondary page puts it at just under 2 bp a day in the early 2000s and almost 12 bp in the 2020s (unverified: second-hand). Gains are short-term capital gains.

Failure modes: costs equal to the edge; gap-down nights carry the full market risk; from Aug 2026 the close is an auction, so "buy at the close" has to choose between the last continuous price and the auction.

Feasibility at ₹1.5 lakh: marginal with the ETF (futures are out of reach). The more useful output is the corollary: prefer strategies that are short or flat during the day and long overnight over ones that are long only during the day.

URLs: https://www.marketcalls.in/amibroker/buy-at-todays-close-and-sell-at-next-day-open-do-simple-trading-strategies-really-work-part2.html ; https://premium.capitalmind.in/2019/10/while-you-were-sleeping-what-stocks-do-overnight-versus-in-trading-hours/ ; https://premium.capitalmind.in/2020/08/capitalmind-chase-roaring-day-and-night/

### 16. Intraday and overnight return persistence ("tug of war")

Source: Lou, Polk, Skouras, "A tug of war: overnight versus intraday expected returns", Journal of Financial Economics 134 (2019).

Exact rules: each month sort stocks into deciles on the past month's cumulative intraday (open-to-close) return. Next month, hold the winner decile during the day only (buy at the open, sell at the close) and short the loser decile during the day only. Overnight analogue: sort on the past month's cumulative overnight return and hold winners overnight only. Value-weighted.

Reported performance (US stocks, 1993 to 2013, gross): overnight winners minus losers: three-factor overnight alpha 3.47% a month (t = 16.83) and intraday alpha −3.02% a month (t = −9.74). Intraday winners minus losers: intraday alpha 2.41% a month (t = 7.70), overnight alpha −1.77% (t = −7.89). The patterns persist with signals lagged up to 60 months. Stronger in large-cap and high-priced stocks (unverified: snippet only). The authors: "transaction costs will make the actual profitability of a trading strategy exploiting these overnight/intraday patterns much less attractive".

India-specific evidence: none. An intraday long-short book is legal here through intraday shorting; an overnight short is not possible in cash.

Cost: 2.41% a month is about 11 bp a day for the pair (my arithmetic), so 5 to 6 bp per leg against 7 to 16 bp per leg in charges alone.

Feasibility at ₹1.5 lakh: no as a stand-alone strategy; useful as a filter (prefer intraday longs in stocks with high past-month intraday returns and low past-month overnight returns; avoid buying at the open stocks that habitually gap up and fade). Fully testable on daily open and close from 2011.

URL: https://personal.lse.ac.uk/polk/research/TugOfWar.pdf

### 17. Tug-of-war intensity as a monthly stock signal

Source: Akbas, Boehmer, Jiang, Koch, "Overnight returns, daytime reversals, and future stock returns", Journal of Financial Economics 145 (2022); abstract opened.

Rules: for each stock and month, count the share of days with a positive overnight return followed by a negative open-to-close return ("negative daytime reversal"); divide by the stock's average of that share over the previous 12 months (unverified: the scaling is from a snippet). Buy stocks with abnormally high values for the following month.

Reported performance: "a more intense daily tug of war predicts higher future returns in the cross section" (abstract). Magnitudes were not obtained. Outperformance lasting up to six months, and robustness to an early NYSE sample: (unverified: snippet only). Non-replication: no significant difference in China (Cheema, Chiah, Man 2022) and limited power in Thailand (unverified: snippet only).

India-specific evidence: none.

Feasibility at ₹1.5 lakh: marginal. It is a monthly delivery rotation, so the cost is the 0.3% to 0.6% per position round trip documented in the small-account file, not the intraday cost. Testable on daily open and close for all NSE stocks from 2011.

URL: https://econpapers.repec.org/RePEc:eee:jfinec:v:145:y:2022:i:3:p:850-875

### 18. Same-time-of-day continuation (intraday periodicity)

Source: Heston, Korajczyk, Sadka, "Intraday patterns in the cross-section of stock returns", Journal of Finance 65 (2010); arXiv 1005.3535.

Exact rules: 13 half-hour intervals a day. For interval k today, sort stocks into deciles on their return in the same interval on a previous day (lag of 13, 26, 39 ... half-hours, up to 40 days). Long the top decile and short the bottom decile for that half-hour. Equal-weighted.

Reported performance: NYSE stocks (1,715 firms), Jan 2001 to Dec 2005. Top-minus-bottom decile at a one-day lag: 3.01 bp per half-hour before costs; significant for at least 40 trading days; strongest in the first and last half-hours; not explained by size, S&P 500 membership, volume or volatility patterns. After buying at the ask and selling at the bid, "the average results are negative for all size categories at all times of the day": about −14 bp for large stocks, −20 bp for medium, −25 bp for small. The authors' practical conclusion is about timing trades one already wants to make, saving roughly one effective spread.

India-specific evidence: none.

Feasibility at ₹1.5 lakh: no as a strategy. Use: schedule entries of other strategies in the half-hour where the stock has recently been weak (for buys) or strong (for sells). Testable on our 1-minute stock data.

URL: https://ar5iv.arxiv.org/html/1005.3535

### 19. Narrow-range day filter (NR4, NR7, triangle) for intraday momentum

Source: Table 5 of the strategy 3 paper.

Definitions: NR4 (NR7) = yesterday's high-low range is the smallest of the last 4 (7) days. Inside day = yesterday's high below and low above the day before. Triangle = yesterday's high below the highs of the two previous days and low above their lows. Trend day = open in the bottom 15% and close in the top 15% of the day's range (or the reverse) with a range above the 14-day average.

Rule: run strategy 3 (or 4) only, or with larger size, on days following an NR4, NR7 or triangle day; skip days following a trend day.

Reported performance (average daily profit of the volatility-targeted noise-band strategy on SPY, by the previous day's pattern): unconditional 12 bp (t = 5.34, Sharpe 1.7, 2,620 observations); NR4 22 bp (t = 5.14, Sharpe 3.2, 660 observations); NR7 16 bp (3.07, 2.5, 367); triangle 14 bp (3.19, 2.0, 664); inside day 5 bp (0.85); outside day 7 bp (1.05); after a trend day −2 bp (−0.24); big tail 19 bp (1.17, 85 observations); strong or weak close 14 bp (2.04).

Caveats: eight patterns were tested on the same in-sample data with no correction for multiple tests; SPY only. No Indian evidence.

Feasibility: yes as a filter, in the sense that it lowers trade count and therefore cost; its value depends entirely on the base strategy. Needs daily bars for the filter and intraday bars for the trade.

URL: https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content

### 20. Signal-strength and volatility-regime filter for intraday momentum

Sources: Rosa (2022, abstract); Gao et al.; strategy 3 paper; the TradingQnA post in strategy 8.

Rule: trade strategies 1 to 4 only when the signal is large or volatility is high. Candidate definitions (my specification; the sources give the principle, not thresholds): |r1| or |r_ROD| greater than k times its own 60-day standard deviation (k from 0.5 to 1.5); India VIX above its one-year median; previous-day 5-day RSI below 50.

Evidence: Rosa: predictability "depends on the strength of the signal" and "a strategy with thresholds delivers higher returns than a strategy that is always active". Gao et al.: R² rises from 1.6% to 3.3% on high-volatility days and is higher on high-volume days. Strategy 3 paper: Sharpe rises with the VIX; negative slope on the prior day's RSI. India: the Bank Nifty 2 PM breakout was flat in the low-volatility year 2017 (vendor post).

Why it matters here: with a fixed cost per trade, trading only the largest signals is the one adjustment that raises edge per trade without raising cost per trade.

Feasibility: yes as a filter. Thresholds chosen on 2022 to 2026 data will be overfitted unless fixed in advance; India VIX history is needed (not in the listed data).

URLs: https://econpapers.repec.org/RePEc:wly:jfutmk:v:42:y:2022:i:12:p:2218-2234 ; https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf

### 21. Time-of-day window filter (the U-shape)

Sources: Singh and Gangwar (2018); Agarwalla and Pandey (2012); Arora (2017, abstract).

Rule (my specification from the volatility evidence): allow new breakout or momentum entries only between 09:15 and 10:00 and after 13:00; no new entries between 11:00 and 13:00; scale stop distance and breakout thresholds by a time-of-day volatility curve (20-day average absolute 1-minute return for each minute of the day), which is what the noise band in strategy 3 already does.

Evidence: all of it is about volatility and volume, not returns. Indian volatility is highest in the first 45 minutes, lowest between 11:00 and 12:00, and rises again from 13:00 (numbers in the environment section). The peak-to-trough ratio in Indian stocks is about four, twice that of the US. A U-shape in volatility, volume and trade count on NSE tick data is also reported by Sampath and Gopalaswamy (2020) (unverified: snippet only). Arora reports significant index returns in the first 20 minutes and near the end of the session.

Caveat: higher volatility at the open also means wider spreads and worse fills on stop orders, so the filter concentrates trading where slippage is highest. The published ORB results depend on the first 5 minutes, exactly where our cost estimate is least certain.

Feasibility: yes as a filter. Testable on our 1-minute data.

URLs: https://mpra.ub.uni-muenchen.de/89689/1/MPRA_paper_89689.pdf ; https://iima.ac.in/sites/default/files/rnpfiles/19191060542012-11-03.pdf ; https://indianjournals.com/article/ajm-8-3-082

### 22. Day-of-week conditioning of intraday strategies

Sources: Table 6 of the strategy 3 paper; Singh and Gangwar; Agarwalla and Pandey.

Rule: weight or switch an intraday momentum strategy by weekday. US result for the noise-band strategy: Wednesday 18 bp a day (t = 3.42), Thursday 12 (2.39), Friday 13 (2.39), Tuesday 9 (2.00), Monday 9 (1.84). The authors note that their 5-minute ORB did best on Mondays in their earlier work, which they attribute to the Monday move happening in the first 30 minutes, and that Wednesday includes US central-bank announcement days.

India: Friday has the highest opening volatility in Nifty futures (0.424% against 0.316% to 0.346% on other days, 2011 to 2018); Monday and post-holiday openings are about 10% more volatile in stocks. The weekday of index option expiry has changed (Thursday until Aug 2025, Tuesday since Sep 2025; seasonality file), so any weekday effect in Indian intraday data is confounded with expiry and will have moved.

Evidence quality: one in-sample table for the US; volatility facts only for India. High data-mining risk with under five years of 1-minute data (about 240 observations per weekday).

Feasibility: yes as a filter; low priority.

URLs: https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content ; https://mpra.ub.uni-muenchen.de/89689/1/MPRA_paper_89689.pdf

### 23. Expiry-day intraday pattern

Sources: Agarwalla and Pandey (2012); Oxford Business Law Blog on SEBI's interim order against Jane Street (30 Jul 2025); 2026 pages on the closing auction.

What is documented:
- 2001 to 2009: for F&O stocks the only abnormal expiry-day behaviour is higher volatility in the last 30 minutes, the window that then set the settlement price.
- SEBI interim order of 3 Jul 2025: on 18 Bank Nifty expiry days between Jan 2023 and Mar 2025 one firm bought index constituents and their futures aggressively from 09:15 to 11:46, often more than 20% of market-wide traded value in several bank stocks, while building short option positions, and then sold from 11:49 to the close, pushing the index down into settlement. SEBI impounded ₹4,843.57 crore; the firm deposited it on 14 Jul 2025 and restrictions were lifted on 21 Jul 2025 subject to compliance. The case was still under appeal at last report (unverified: snippet only).
- 2026: with the first closing auction, the index moved about 150 points between the end of continuous trading and the official close on the 4 Aug 2026 expiry; from 7 Dec 2026 expiring contracts settle on the 15:00 to 15:30 VWAP again.
- Practitioner figures: on expiry Thursdays in 2023 to 2024 the Nifty's range was about 180 to 220 points against 140 to 170 on other days, and the first 45 and last 90 minutes held about 60% of the range (Multibagg article summarising social-media posts; no method given).

Rules to test (my specification): on index expiry days only, (a) momentum: position with the sign of the rest-of-day return for the final half-hour of continuous trading (strategy 2 restricted to expiry days, the negative-gamma story); (b) reversal: from 11:50 fade the 09:15 to 11:45 move until 15:00.

Why caution dominates: the best-documented expiry-day pattern in recent Indian data was, according to the regulator, produced by one participant who has been stopped; weekly Bank Nifty options ended in Nov 2024; the expiry weekday changed in Sep 2025; the settlement mechanism changed in Aug 2026 and again in Dec 2026. A backtest over 2022 to 2026 mixes four regimes with about 50 monthly and 240 weekly expiry days in total.

Feasibility: marginal mechanically (index ETF or options), but evidence is anecdotal and the structure has broken several times. Expiry dates must come from the daily F&O files.

URLs: https://iima.ac.in/sites/default/files/rnpfiles/19191060542012-11-03.pdf ; https://blogs.law.ox.ac.uk/oblb/blog-post/2025/07/jane-street-and-expiry-day-trap-unpacking-sebis-crackdown-algorithmic ; https://www.share.market/buzz/insights/cas-expiry-days/ ; https://www.multibagg.ai/market-pulse/articles/nifty-options-expiry-tuesday-sideways-cmsy7ms1f00gw0zmzcepmle1f

### 24. Intraday overreaction reversal and next-day follow-through (Indian studies)

Sources: Tripathi and Aggarwal, "Prior return effect in Indian stock market: an intra-day analysis", International Journal of Financial Management 5(1), 2015 (abstract only; full text is behind a paywall). Siddiqui and Misra, "Intraday overreaction and underreaction: profitability analysis and factor explanations", Journal of Asset Management 26(5), 2025 (abstract only).

What they report: Tripathi and Aggarwal: in Indian stocks, "security returns exhibit a reversal in their direction within few minutes of extreme price rises as well as price falls"; prices recover quickly after unjustified falls and more slowly after unjustified rises. Siddiqui and Misra: using a speed-of-price-adjustment measure on Indian high-frequency data, intraday overreaction is positively related to next-day returns; a factor long overreacting and short underreacting stocks earns a premium not explained by market, size, value, momentum or illiquidity; overreaction legs are always more profitable than underreaction legs. Neither abstract gives thresholds, sample period, or costs.

Rules to test (my specification, because the papers' definitions were not accessible): (a) intraday fade: when a stock's 5-minute return exceeds 3 standard deviations of its own 5-minute returns for that time of day over the last 20 days, and the index has not moved more than a third as much, take the opposite side at the next bar's open; exit after 15 to 30 minutes or at VWAP; stop at the extreme of the event bar plus one event-bar range. (b) next-day: rank stocks at 15:00 by the day's overreaction score, buy the top few near the close, sell at the next day's close.

Consistency check with other evidence: the US end-of-day reversal (strategy 10) is mostly losers bouncing, which matches the faster recovery after falls reported for India.

Cost: version (a) trades often in single stocks at 0.10% to 0.25% all-in per round trip; a typical 3-standard-deviation 5-minute move in a liquid stock is perhaps 0.5% to 1% (estimate), so a partial retracement can exceed cost, but fills at the next bar after a spike are where slippage is worst. Version (b) is a delivery trade (0.27% round trip at ₹1.5 lakh).

Feasibility at ₹1.5 lakh: marginal. It is the only stock-level intraday pattern with Indian academic support, but only at abstract level.

URLs: https://publishingindia.com/archive/ijfm/prior-return-effect-in-indian-stock-market-an-intra-day-analysis ; https://ideas.repec.org/a/pal/assmgt/v26y2025i5d10.1057_s41260-025-00418-y.html

## Negative or cautionary evidence

1. Cost against effect size. Every index-level intraday momentum result that has been published is 2 to 3 bp per trade in the US before or after very small US costs. An Indian intraday ETF round trip is 4 to 7 bp in charges plus spread. Stock-level cross-sectional effects are 3 to 11 bp a day gross for a two-leg portfolio. The authors of the three strongest academic papers (Baltussen et al. 2021; Baltussen, Da, Soebhag 2025; Heston et al. 2010) each say their effect may not be exploitable after transaction costs, and Heston et al. show it is negative after the spread.
2. Daily trading at full leverage costs 50% to 200% of capital a year in charges (table above). STT alone on ₹7.5 lakh of daily sells is about 31% of capital a year (my arithmetic: 0.025% × 7.5 lakh × 250 / 1.5 lakh).
3. Decay after publication. First-half-hour momentum: "the predictability disappears in the out-of-sample period" (Rosa 2022); negative out-of-sample R² for equity futures in Baltussen et al. Buy-on-gap: positive in only one 3-year window after its 2013 publication. Overnight-to-intraday reversal: faded in large US stocks after 2011 (snippet only). Intraday volatility itself halved in Nifty futures between 2011 and 2018.
4. The practitioner papers are in-sample and optimistic on costs. The 5-minute ORB paper assumes no spread or slippage; an independent 2026 replication reproduces the gross +0.13 R and finds +0.002 R net on the paper's own market and negative results on four of five indices. The VWAP "holy grail" paper could not be reproduced by several independent coders and has a large drawdown in at least one public re-run. The stocks-in-play paper has no out-of-sample period, charges commission only, and its only replication covers the first year of its own sample.
5. Low hit rates. The ORB with a 10 R target wins about one trade in four or five; the stocks-in-play version wins under half the days and its best stocks win 17% to 24% of trades. With reinvested profits and a small account, runs of ten or more losses are normal, and a few days a year supply all the profit; missing them through a forced early exit or a platform failure removes the edge.
6. Indian market structure differs from the test markets in ways that all reduce the edge: forced exit of leveraged positions before the close; a closing auction since Aug 2026 and a different one from Dec 2026; no continuous trading at the official open price; no shorting overnight; a 200-stock universe instead of 7,000; index futures out of reach; no volume on the index series.
7. Negative daytime drift. Since the pre-open session began, the Nifty's open-to-close return has been flat to negative while close-to-open carried the gains; only 46% of days were positive open-to-close in Capitalmind's 12-year sample. Long-only intraday strategies start from behind.
8. Outcomes of real intraday traders. SEBI: 71% of individual intraday cash traders lost money in FY23, 80% of the most active. Brazil (Chague, De-Losso, Giovannetti, via Quantpedia, opened): of 1,551 people who day-traded index futures for more than 300 days, 97% lost money, 1.1% earned more than the minimum wage, and there was no evidence of learning. Taiwan (Barber, Lee, Liu, Odean): fewer than 1% of day traders are predictably profitable (unverified: snippet only).
9. Expiry-day patterns in 2023 to 2025 were, on SEBI's account, partly manufactured by one firm. Patterns measured in that window should not be assumed to persist.
10. No rigorous Indian evidence exists for any of the headline strategies. For first-half-hour momentum, noise bands, ORB, relative volume, end-of-day reversal and overnight-to-intraday reversal I found no Indian study with a stated sample, rules and costs. Indian evidence is limited to volatility shape (solid), the overnight-versus-intraday split (solid as a fact, weak as a strategy), two abstracts on intraday overreaction, and vendor or blog backtests without costs.

## Open questions

1. Is the Indian effect larger than the US one? Per-trade gross edge on NIFTY 50 and NIFTY BANK for strategies 1 to 4 over 2022 to 2026, reported in basis points against the 6 to 8 bp ETF hurdle. Higher peak-to-trough intraday volatility in India (four times against two) is a reason to hope, not a result.
2. Can options carry these signals? By my arithmetic the option round trip is 5 to 15 times cheaper per unit of direction than the ETF. Testing it needs intraday option prices, which we do not have. Until then, any index-level intraday signal that fails the ETF hurdle but shows a stable gross edge should be parked, not discarded.
3. What is Angel One's current auto square-off time for CAS stocks, and will it change again on 7 Dec 2026? What is the per-stock intraday margin? Both set how much of the afternoon a leveraged strategy can use. Not verified on Angel One's own pages.
4. Does a same-day buy and sell placed under the delivery product (full cash) avoid the forced square-off while still being charged as intraday? This is common broker practice, but I did not verify it for Angel One.
5. How large is the difference between the official open (pre-open auction price) and the first achievable continuous price at 09:15 to 09:16 in our 1-minute data? It decides whether the gap and overnight-reversal strategies (11 to 14), which look best on daily data, exist at all.
6. Slippage in the first five minutes for stop-entry orders in the top 200 stocks. Every ORB number depends on it and no Indian measurement was found. The US authors measured $0.001 a share on SPY by live experiment; we need the equivalent from paper trading.
7. How many of the 200 stocks have relative volume above 100% and a directional first candle on a typical day, and does the top 3 to 5 behave like the US top 20?
8. The 2026 closing-auction regimes: do the last continuous half-hour and the auction show momentum or reversal relative to the rest of the day? There is no literature yet; our own data from 3 Aug 2026 are the only source.
9. Dealer gamma in Nifty options: can the sign be proxied from the daily F&O files and participant positioning data we hold (for example net option positions of proprietary and client categories), to condition strategy 2 as the US paper does?
10. The India-specific intraday momentum paper on ResearchGate, the full text of the two Indian overreaction papers, and the three GitHub replications of the noise-band strategy could not be opened. They are the first things to read if access becomes available.
11. Tax treatment of intraday equity profits (speculative business income) versus F&O and delivery gains was not researched here and affects the reinvestment rate.

## Sources opened

Academic and working papers:
- Gao, Han, Li, Zhou (working paper, Dec 2015): https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf
- Baltussen, Da, Lammers, Martens (JFE 2021): https://www3.nd.edu/~zda/intramom.pdf
- Baltussen, Da, Soebhag, End-of-day reversal (Apr 2025): https://www3.nd.edu/~zda/EOD.pdf
- Li, Sakkas, Urquhart (international evidence): http://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-092-Zeming-Li.pdf
- Rosa (2022) abstract: https://econpapers.repec.org/RePEc:wly:jfutmk:v:42:y:2022:i:12:p:2218-2234
- Zarattini, Aziz, Barbon, Beat the Market: https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content
- Zarattini, Barbon, Aziz, stocks in play: https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content
- Heston, Korajczyk, Sadka: https://ar5iv.arxiv.org/html/1005.3535
- Lou, Polk, Skouras: https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
- Akbas, Boehmer, Jiang, Koch abstract: https://econpapers.repec.org/RePEc:eee:jfinec:v:145:y:2022:i:3:p:850-875
- Agarwalla and Pandey, IIMA W.P. 2012-11-03: https://iima.ac.in/sites/default/files/rnpfiles/19191060542012-11-03.pdf
- Singh and Gangwar, MPRA 89689: https://mpra.ub.uni-muenchen.de/89689/1/MPRA_paper_89689.pdf
- Arora (2017) abstract: https://indianjournals.com/article/ajm-8-3-082
- Tripathi and Aggarwal (2015) abstract: https://publishingindia.com/archive/ijfm/prior-return-effect-in-indian-stock-market-an-intra-day-analysis
- Siddiqui and Misra (2025) abstract: https://ideas.repec.org/a/pal/assmgt/v26y2025i5d10.1057_s41260-025-00418-y.html

Practitioner, replication and summary pages:
- https://concretumgroup.com/can-day-trading-really-be-profitable/
- https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/
- https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/
- https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy
- https://www.cxoadvisory.com/technical-trading/overnightintraday-return-reversal-trading/
- https://www.cxoadvisory.com/momentum-investing/intraday-stock-price-momentum-and-reversal-trading/
- https://www.mql5.com/en/blogs/post/776235
- https://www.quantconnect.com/forum/discussion/16706/bear-bull-traders-039-paper-on-quot-the-holy-grail-quot-not-so-fast/
- https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/
- https://www.quantrocket.com/blog/buy-or-sell-down-gaps/
- https://financialnoob.substack.com/p/buy-on-gap-strategy-and-its-performance
- https://quantpedia.com/retail-day-trading-is-an-uphill-battle/
- https://harbourfrontquant.substack.com/p/does-intraday-momentum-exist-in-stock

Indian practitioner, broker and news pages:
- https://premium.capitalmind.in/2019/10/while-you-were-sleeping-what-stocks-do-overnight-versus-in-trading-hours/
- https://premium.capitalmind.in/2020/08/capitalmind-chase-roaring-day-and-night/
- https://premium.capitalmind.in/2017/03/nifty-gaps-and-future-returns/
- https://www.marketcalls.in/amibroker/buy-at-todays-close-and-sell-at-next-day-open-do-simple-trading-strategies-really-work-part2.html
- https://www.marketcalls.in/amibroker/full-gap-open-range-strategy-amibroker-afl-code.html
- https://www.marketcalls.in/nifty-technicals/15-minute-opening-range-breakout.html
- https://www.marketcalls.in/futures-and-options/trading-the-gap-up-and-gap-down-part-2.html
- https://tradingqna.com/t/orb-opening-range-breakout-2pm-banknifty-intraday-strategy/39756 (read through the forum's .json endpoint)
- https://blog.quantinsti.com/intraday-low-frequency-trading-strategy-project-rajtk/
- https://www.angelone.in/pricing
- https://www.angelone.in/knowledge-center/share-market/leverage-trading
- https://www.kotakneo.com/news/regulations/nse-new-closing-auction-and-f-and-o-trading-rules-from-7-december/
- https://www.tradingview.com/news/cnbctv:d9dfe3839094b:0/
- https://www.sahi.com/blogs/closing-auction-session-cas-explained-nse-bse-closing-price-rules-2026
- https://www.share.market/buzz/insights/cas-expiry-days/
- https://www.incredmoney.com/knowledge-center/intraday-trading/intraday-auto-square-off-time/
- https://www.business-standard.com/markets/news/over-70-intra-day-traders-incur-losses-during-fy23-reveals-sebi-study-124072401110_1.html
- https://blogs.law.ox.ac.uk/oblb/blog-post/2025/07/jane-street-and-expiry-day-trap-unpacking-sebis-crackdown-algorithmic
- https://www.multibagg.ai/market-pulse/articles/nifty-overnight-intraday-returns-study-cmqxr9lq34t09o20jum5tsveq
- https://www.multibagg.ai/market-pulse/articles/nifty-options-expiry-tuesday-sideways-cmsy7ms1f00gw0zmzcepmle1f
- https://apintelligence.blogspot.com/2025/10/best-time-to-invest-in-stocks-have.html

Could not be opened (claims from these are marked "unverified: snippet only" above): https://www.researchgate.net/publication/383567351_Hedging_Demand_and_Intraday_Momentum_within_the_Indian_Stock_Market ; https://github.com/giovannibrusco/zarattini-2024-momentum-spy ; https://github.com/VigorTas/beat-the-market-replication ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7609644 ; https://reading-9.eprints-hosting.org/95566/1/Accepted-Version.pdf
