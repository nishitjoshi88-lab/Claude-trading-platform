# What Indian practitioners actually run with small accounts

Research date: 2026-11-10. Scope: publicly documented systematic strategies and track records in India (momentum smallcases, Weekend Investing, Capitalmind, Wright Research, NSE momentum indices, ETF "shop" systems, TradingQnA / Marketcalls / AlgoTest / Streak / Tradetron strategies, PMS and AIF quant funds), and whether each survives a ₹1,50,000 account at Angel One.

## How to read this file

- Every number is attributed to a source I opened with `fetch_text.py`, unless it is marked **(unverified: snippet only)** (seen only in a search-result summary) or **(from memory, unverified)**.
- "Computed" means I derived the figure from sourced inputs; the arithmetic is shown.
- Almost all performance in this area is self-reported by people who sell the product. I say so each time. Live, fee-paid, third-party-visible track records exist only for: the NSE momentum indices (live since Aug 2020), the Capitalmind Adaptive Momentum PMS (live since Mar 2019), the Capitalmind smallcase (Jan 2019 to Sep 2025), the Wright Factor Fund PMS (about 3 years).
- TradingQnA threads were read through the forum's plain-text endpoint (`https://tradingqna.com/raw/<topic id>`); I cite the normal thread URL.
- Search budget note: the shared web-search allowance for this run was exhausted after 19 searches. Everything after that was read from URLs already surfaced. Items I could not chase are listed under "Open questions".

## 0. The cost model that decides everything at ₹1.5 lakh

### 0.1 Angel One charges (official pricing page, opened 2026-11-10)

Source: https://www.angelone.in/pricing

| Item | Equity delivery | Equity intraday | Futures | Options |
|---|---|---|---|---|
| Brokerage | lower of ₹20 or 0.1% per executed order, minimum ₹5 | lower of ₹20 or 0.1%, minimum ₹5 | ₹20 per executed order | ₹20 per executed order |
| STT | 0.1% buy and sell | 0.025% sell | 0.05% sell | 0.15% sell (on premium) |
| NSE transaction charge | 0.0030699% | 0.0030699% | 0.0018299% | 0.0355299% of premium |
| Stamp duty (buy) | 0.015% | 0.003% | 0.002% | 0.003% |
| SEBI fee | ₹10 per crore | same | same | same |
| GST | 18% on brokerage + transaction + SEBI fee | same | same | same |

Other items on the same page: demat debit ("DP") charge ₹20 per ISIN (plus GST) on each sell day; account maintenance nil for a Basic Services Demat Account with holdings up to ₹4 lakh, otherwise ₹60 + GST per quarter; MTF interest 0.041% per day; first-30-day brokerage waiver up to ₹500.

Two things changed since most Indian strategy write-ups were published:
1. Angel One delivery is no longer free. A third-party page still says "brokerage free equity delivery" in its FAQ while its own table says ₹20 or 0.1% (https://www.chittorgarh.com/brokerage_charges/angel-broking/14/). A search summary dates the change to November 2024 (unverified: snippet only). Use the official page.
2. STT on derivatives on the official page is now 0.05% (futures) and 0.15% (options, on premium). The third-party page above still shows 0.01% and 0.05%, which are stale.

### 0.2 Round-trip cost of one delivery position (computed from 0.1)

Formula per round trip of position value P: brokerage 2 x max(5, min(20, 0.1% x P)); GST 18% on brokerage, transaction charge and SEBI fee; STT 0.2% x P; stamp 0.015% x P; transaction 0.00614% x P; DP ₹23.60 per sell. For ETFs I assumed STT of 0.001% on the sell side only (from memory, unverified; confirm before coding).

| Position size | Brokerage per order | Stock round trip | ETF round trip (STT assumption above) |
|---|---|---|---|
| ₹3,000 | ₹5.0 | ₹42 (1.40%) | ₹36 (1.20%) |
| ₹5,000 (30 positions) | ₹5.0 | ₹46 (0.93%) | ₹37 (0.73%) |
| ₹7,500 (20 positions) | ₹7.5 | ₹58 (0.77%) | ₹43 (0.57%) |
| ₹10,000 (15 positions) | ₹10 | ₹69 (0.69%) | ₹50 (0.50%) |
| ₹15,000 (10 positions) | ₹15 | ₹92 (0.62%) | ₹63 (0.42%) |
| ₹20,000 | ₹20 | ₹115 (0.58%) | ₹76 (0.38%) |
| ₹30,000 (5 positions) | ₹20 | ₹138 (0.46%) | ₹78 (0.26%) |
| ₹75,000 (2 positions) | ₹20 | ₹238 (0.32%) | ₹88 (0.12%) |
| ₹1,50,000 (1 position) | ₹20 | ₹405 (0.27%) | ₹106 (0.07%) |

Consequences:
- The DP charge (₹23.60 per sell) is the largest fixed item for positions below about ₹12,000. It is 0.31% of a ₹7,500 position by itself.
- A 20-stock momentum portfolio that replaces 20% of its names each month (Capitalmind's own estimate of its churn, see 3) does about 2.4 full round trips a year: 2.4 x 0.77% = about 1.9% a year in charges, before slippage and tax. The same churn in 10 positions costs about 1.5%.
- Partial "re-weighting" sells are poison at this size: each trim triggers a ₹23.60 DP charge plus a ₹5 minimum brokerage. An automated system should only do full exits and full entries.
- Slippage is extra. Capitalmind says market-order slippage matters above roughly ₹2 to 3 lakh per stock (see 3); at ₹7,500 to ₹15,000 per stock it is small for Nifty 500 names but not for illiquid small caps.

### 0.3 Tax drag

- Short-term capital gains on listed equity 20% (was 15%) and long-term 12.5% (was 10%) after the July 2024 budget; Capitalmind's own sunset note says the bulk of momentum gains are short term and that this "necessitates a change" in how investors hold momentum (https://premium.capitalmind.in/2025/08/whats-next-for-capitalmind-momentum-the-flexi-cap-path/).
- A third-party illustration: at 15% pre-tax, direct-stock momentum nets 11.89% a year after 20% STCG, versus 13.13% to 13.87% when the same return is held inside a mutual fund for 1 to 10 years (https://curiousinvestinginsights.substack.com/p/why-momentum-in-a-mutual-fund-is). The piece mislabels the budget year as 2025; the arithmetic is still right.
- For a reinvesting account this means every backtest must be run after 20% tax on realised short-term gains, paid yearly.

### 0.4 Subscription fees versus a ₹1.5 lakh account (computed)

| Product | Fee (source) | Fee as % of ₹1.5 lakh |
|---|---|---|
| Mi India Top 10 | ₹6,999 a year (weekendinvesting.com) | 4.7% |
| Mi NNF10 | from ₹833 a month (smallcase manager page) | about 6.7% |
| Mi ATH 2 | ₹9,999 a year | 6.7% |
| Mi 20, Mi 25, Mi EverGreen | ₹14,999 a year | 10.0% |
| Mi MT Allcap | ₹19,999 a year | 13.3% |
| Capitalmind Momentum smallcase (closed 30 Sep 2025) | ₹1,125 a month | 9.0% |
| MWM Momentum | ₹12,001 a year | 8.0% |

Capitalmind's own rule of thumb: fees should not exceed 3% of the amount invested, which is why it suggested a ₹5 lakh target for its smallcase (https://premium.capitalmind.in/introduction-to-capitalmind-momentum-model/). Weekend Investing recommends ₹5 to 30 lakh for every strategy. So no paid smallcase makes sense at ₹1.5 lakh. The only way these strategies are usable is to re-implement the public rules ourselves, which is what the backtests are for.

### 0.5 Smallcase minimum amounts (smallcase manager page, Nov 2026)

Source: https://www.smallcase.com/manager/weekend-investing/smallcases. The minimum is the money needed to hold every constituent at the model weights in whole shares, so it is a direct read of whether whole-share equal weighting works at our size.

| Strategy | Positions | Minimum amount | Fits ₹1.5 lakh? |
|---|---|---|---|
| Mi India Top10 | 10 | ₹86,228 | yes |
| Mi ST ATH | 10 | ₹1,04,339 | yes |
| Mi NNF10 | 10 | ₹1,14,341 | yes |
| Mi MT Allcap | 20 | ₹1,96,381 | no |
| Mi25 Smallcap | 25 | ₹1,99,188 | no |
| Mi 20 | 20 | ₹2,04,105 | no |
| Mi 35 | 35 | ₹2,64,383 | no |
| Mi EverGreen | 20 + gold | ₹3,10,771 | no |
| Mi30 | up to 33 | ₹3,24,751 | no |
| Mi Allcap Gold | 4 sleeves | ₹4,59,150 | no |

Rule of thumb from this table: about 10 equal-weight large-cap positions is the practical ceiling for exact equal weighting at ₹1.5 lakh; 20 positions only works with tolerance for uneven weights (one high-priced share can be 2 to 3 times its target weight).

### 0.6 Derivatives at ₹1.5 lakh

- Short ATM Nifty straddle, 1 lot of 75: margin about ₹2.36 lakh; converting it to an iron fly (buy 300-point wings) cut margin to about ₹93,700 (TradingQnA, Feb 2025: https://tradingqna.com/t/reports-of-the-death-of-920-short-straddle-are-greatly-exaggerated/179061).
- One Nifty futures lot: exchange margin about ₹2.2 lakh on about ₹19 lakh notional; one GoldM lot about ₹1.25 lakh margin (Zerodha "The Long and the Short", Nov 2025: https://tradingqna.com/t/trend-following-in-india-part-3-nifty-gold-strategy/188767).
- I did not verify the 2026 Nifty lot size. The sources above use 75. An NSE lot-size revision to 65 for Nifty from the January 2026 series is my recollection only (from memory, unverified); the derivatives researchers should confirm.
- Fixed cost of a daily one-lot intraday option structure (computed from 0.1, ATM straddle premium assumed 250 points): naked short straddle 4 orders a day = about ₹135 a day = about ₹33,000 a year = about 22% of ₹1.5 lakh. Iron fly 8 orders a day = about ₹235 a day = about ₹58,000 a year = about 38% of ₹1.5 lakh. That is before slippage.
- Regulatory context: SEBI found 91% of individual F&O traders lost money in FY25 (net loss ₹1,05,603 crore, average ₹1.1 lakh; https://www.valueresearchonline.com/stories/225398/average-trader-lost-rs-1-1-lakh-fo-fy25/) and 87.7% in FY26 (₹91,685 crore, average about ₹1.17 lakh, transaction costs about ₹25,000 crore, options 92% of losses, algo entities earned 99% of proprietary and FPI profits; https://openthemagazine.com/business/sebi-fo-loss-study-explained-why-9-in-10-retail-traders-lost-91685-crore-in-fy26).

---

## Strategies

Sections 1 to 28 each have a card in `research/cards/small_account_india.json`. Where a manager does not publish a formula, the text says so and labels my replacement rule as a stand-in to be swept in backtests.

### 1. Nifty200 Momentum 30 (and Midcap150 Momentum 50, Nifty500 Momentum 50): index rules, ETF or DIY

What it is: the published NSE factor index that most Indian momentum ETFs and index funds track. It is the only momentum strategy in India with fully public rules, a 2005 back-history and a live record since August 2020.

Exact rules (NSE white papers Sep 2020 and Apr 2026; freefincal's summary of the NSE methodology document; PrimeInvestor):
- Universe: Nifty 200 constituents, listed at least 1 year, available in F&O. (Midcap150 Momentum 50: Nifty Midcap 150, non-F&O stocks that hit a circuit on 20% or more of days excluded. Nifty500 Momentum 50: Nifty 500, same circuit filter, promoter pledge above 20% ineligible, bottom 10% by 6-month average turnover and by turnover ratio ineligible.)
- Momentum ratio: MR6 = 6-month price return / annualised standard deviation of daily returns over the last 1 year; MR12 = 12-month price return / the same standard deviation.
- Z-scores: Z6 and Z12 are each MR standardised across all eligible stocks (subtract cross-sectional mean, divide by cross-sectional standard deviation).
- Weighted average Z = 0.5 x Z12 + 0.5 x Z6.
- Normalised momentum score = 1 + Z if Z >= 0, else 1 / (1 - Z).
- Select the 30 highest scores. A rank buffer is applied to reduce turnover (the exact buffer ranks are in the NSE methodology document, which I did not open).
- Weight = free-float market cap x normalised momentum score, capped at the lower of 5% or 5 times the stock's free-float weight.
- Rebalance semi-annually (June and December); quarterly screen for concentration norms. If a stock leaves the Nifty 200 it leaves the index at the review.
- Instruments: any Nifty200 Momentum 30 ETF or index fund (13 funds, AUM above ₹12,500 crore at 27 Feb 2026), or the 30 stocks directly.
- Holding period: 6 months per rebalance.

Reported performance (NSE white paper, data to 27 Feb 2026, price index, back-tested before Aug 2020):
- Since April 2005: Nifty200 Momentum 30 19.19% a year vs Nifty 200 15.08%; Midcap150 Momentum 50 23.00% vs 17.24%; Nifty500 Momentum 50 21.94% vs 18.85%.
- Momentum 30 trailing: 15 years 18.86%, 10 years 20.16%, 7 years 17.70%, 5 years 18.15%, 3 years 21.50%, 1 year 18.18%, 2026 year to date 0.78%.
- Maximum drawdown: 68% (Momentum 30), 73% (Midcap150 Momentum 50), 70% (Nifty500 Momentum 50) versus 64%, 73%, 64% for the parents.
- Calendar years: beat the parent in 15, 14 and 13 of the last 20 years. Bad years: 2008 (Momentum 30 -60.04%), 2009 (lagged Nifty 200 by 19.47 points in the rebound), 2018 (-1.66%), 2022 (-5.45%, lagged by 10.36 points), 2025 (-4.57%, lagged by 14.13 points; Midcap150 Momentum 50 -3.46%, lagged 9.45; Nifty500 Momentum 50 -7.61%, lagged 15.37).
- Quarterly versus semi-annual rebalancing: quarterly adds roughly 20% to 70% more annual churn and did not improve long-run returns for Momentum 30 (since inception 17.12% quarterly vs 19.19% semi-annual) or Nifty500 Momentum 50; it helped slightly for the midcap index. As I read the churn table, the semi-annual Momentum 30 turned over about 101% to 134% of index weight per year in FY22 to FY26 and the quarterly version 123% to 167%.
- Wright Research's drawdown table for the index since 2010: ten drawdowns above 10%; worst -34.21% (Feb to Mar 2020), -31.79% (27 Sep 2024 to 7 Apr 2025, 192 days, not recovered by Aug 2025), -28.39% (Oct 2021 to Jun 2022, 435 days to recover), -26.34% (2010-11). Average 141 days to trough and 191 days to recover.

India-specific cautions:
- The index launched in August 2020; everything earlier is a backtest, "and an index methodology can always be tweaked to suit an ideal back-tested outcome" (PrimeInvestor).
- Crowding: the December 2025 reconstitution replaced 19 of 30 stocks and was expected to cause about ₹16,130 crore of round-trip trades, with flows in 27 stocks above one day's average volume (Business Standard, 14 Dec 2025). Front-running of a public rebalance is a real cost for ETF holders and an opportunity only for people who trade ahead of it.
- Liquidity illusion: see strategy 12.

Feasibility at ₹1.5 lakh: yes through an ETF (one order, about 0.07% round trip, no stock-level DP charges, and the fund pays no tax on its churn; expense ratio and tracking error apply). DIY replication of 30 names at ₹5,000 each is marginal: about 0.93% per round trip per name and whole-share rounding errors; free-float data is needed for weights.

Sources:
- https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/momentum-strategy-whitepaper_2026.pdf
- https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/nifty200_momentum_30_index_whitepaper_sep_20.pdf
- https://freefincal.com/nifty200-momentum-30-index-a-new-strategy-index-from-the-nse/
- https://primeinvestor.in/reports/pros-and-cons-of-momentum-investing/
- https://www.wrightresearch.in/blog/momentum-strategies-underperforming-2025-data-insights/
- https://www.business-standard.com/amp/markets/news/nifty200-momentum30-a-flip-of-index-switch-jolts-16k-cr-across-the-grid-125121400388_1.html

### 2. Capitalmind "naive momentum": top 30 by 12-month return, monthly

Exact rules (Capitalmind, "Does Momentum Investing work in India?"):
- Universe: all NSE stocks including delisted ones (survivorship-free), with a liquidity floor; the article notes only about 750 securities traded more than ₹1 crore a day.
- On the first trading day of each month rank by absolute return over the last 252 trading days.
- Buy the top 30, equal weight, long only. Rebalance monthly.
- Variant A, Gain-Loss: rank by (percentage of up days in the last 252 days) x (252-day return).
- Variant B, volatility-adjusted: rank by (252-day excess return) / (annualised standard deviation of daily returns), i.e. a Sharpe ratio.
- No stops, no cash rule.

Reported performance (backtest Jan 2007 to 2019, no costs or taxes, no dividends):
- Simple: ₹100 to ₹464, 12.6% a year, versus Nifty 8.9% and Nifty 500 8.7%.
- Gain-Loss: ₹594, 14.7%. Volatility-adjusted: ₹749, 16.8%.
- Beat both indices in only 6 of 13 calendar years; 63% up months versus 54% for the index; "deeper drawdowns" than the index in sharp corrections. The drawdown table is an image; the text's remark "does a 60% drawdown feel significantly better than an 80% drawdown" suggests roughly 80% for simple momentum against roughly 60% for the index in 2008 (my reading, not a quoted figure).
- Control experiment: 30 random stocks rebalanced monthly earned between -7.43% and 5.78% a year in most Monte Carlo runs and under 7% in 99% of them.
- Longer sample quoted by PrimeInvestor from the Capitalmind SSRN paper: Jan 2000 to May 2020, ₹100 to ₹1,038 after taxes versus ₹602 for Nifty 50 buy and hold. (PrimeInvestor describes the universe as Nifty 50, which looks like a slip; I could not open the SSRN paper.)

Cost and capacity: monthly re-ranking of 30 names with no buffer produces very high turnover. At ₹5,000 a position each swap costs about 0.93% round trip. Capitalmind's own disclaimer: transaction costs and short-term tax are not in the numbers.

Failure modes: 2008-style crash (drawdown deeper than the index), sharp reversals (2008 and 2016 are named as spectacular underperformance years), and the 2024-26 momentum slump (see 3).

Feasibility at ₹1.5 lakh: marginal with 30 names; reasonable with 10 to 15 names and a rank buffer (for example exit only when a holding falls out of the top 2N), which is a parameter the backtests should sweep.

Sources:
- https://www.capitalmind.in/insights/momentum-investing-basics-india
- https://primeinvestor.in/reports/pros-and-cons-of-momentum-investing/

### 3. Capitalmind Momentum smallcase and Adaptive Momentum PMS (volatility-adjusted, top decile, weekly review, cash rule)

Public rules (partly proprietary):
- Universe: NSE stocks passing minimum traded value and market cap, roughly the top 500 by market cap, about 90% of market capitalisation.
- Score: a composite of price and volume parameters; "composite return metric adjusted for volatility"; earlier factsheet language says ranking by Sharpe ratio (unverified: snippet only). Entry filters use short-term price and volume criteria to avoid sharp reversals right after entry.
- Entry candidates: 90th percentile and above of the score.
- Exit: a stronger stock displaces it, or it fails a retention criterion.
- Weights: by rank and volatility relative to other candidates.
- Review weekly (changes sent before Friday open); only stocks held at least 1 month can be replaced, except for adverse stock-specific events. About 20% of the portfolio changes each month. Typical holding 2 to 3 months.
- 15 to 25 stocks, long only. "If there aren't enough opportunities, stay in cash." The PMS adds rules that shift partly or fully to cash or other assets in broad market declines, and caps on sector and business-group exposure.

Live performance:
- Adaptive Momentum PMS, net of fees, live since 5 Mar 2019, page updated 6 Nov 2026 (not SEBI-verified): 3 months 2.3% vs Nifty 50 TRI 1.7%; 6 months 8.5% vs 3.8%; 1 year 6.6% vs -0.8%; 2 years -5.9% a year vs 2.3%; 3 years 7.9% vs 10.1%; 4 years 9.1% vs 9.6%; 5 years 7.0% vs 8.3%; 6 years 15.9% vs 13.9%; 7 years 17.8% vs 12.4%.
- PMS AIF World listing (date not shown on page): 1 year 7.31%, 2 years -7.68%, 3 years 7.98%, 5 years 7.24%, since inception 17.14% vs Nifty 50 TRI 11.32%; 15 stocks; 58.6% positive months.
- Reading: all of the 7-year edge was earned in the first two years (2019 to early 2021). An investor who joined any time in the last 5 years has lagged the Nifty 50 TRI after fees.
- The smallcase (launched 27 Jan 2019) showed 14.91% 3-year CAGR at its last factsheet (6 Oct 2025) and was shut on 30 Sep 2025. Fee was ₹1,125 a month; recommended size "up to ₹50 lakh".
- Capitalmind's stated reason for closing it: the tax change, crowding ("many players have jumped on the bandwagon"), and a table of more than 25 momentum definitions showing that "the last 1-year has been poor for any kind of single-factor Momentum-driven strategy". The successor is a flexi-cap mutual fund that switches between momentum and other factors (quality, low volatility, value) using a two-stage rule that is not published; its backtest runs 2007 to June 2025.
- Their backtests show momentum trails the Nifty on a rolling 1-year basis about 30% of the time, and nearly half of all positions exit at a loss.

Feasibility at ₹1.5 lakh: the product no longer exists for retail, and the PMS minimum is ₹50 lakh. A DIY clone (Sharpe-ranked top decile, weekly check, 1-month minimum hold, 10 to 15 names, index trend filter for cash) is implementable on daily data; marginal on costs (about 2% a year in charges at 20 names, see 0.2).

Sources:
- https://premium.capitalmind.in/introduction-to-capitalmind-momentum-model/
- https://capitalmind.in/portfolio-management-service/momentum
- https://premium.capitalmind.in/2025/08/whats-next-for-capitalmind-momentum-the-flexi-cap-path/
- https://assets.smallcase.com/factsheets/CMMO_0001.pdf
- https://www.pmsaifworld.com/portfolio/wizemarkets-capitalmind-momentum-fund

### 4. Weekend Investing Mi India Top 10 (Nifty 50, top 10, monthly)

Rules as published:
- Universe: Nifty 50. Hold 10 stocks at 10% each. Monthly rebalance.
- Rank by "quantitative momentum filters" (formula not disclosed). Winners are allowed to run; a holding is removed at the next rebalance only if it meets the exit criterion (so there is a rank buffer, size not disclosed).
- 2026 smallcase page: "Hybrid Momentum" - in rare systemic stress exposure may reduce and capital may move to cash; a stock showing exceptional deterioration may exit before the scheduled rebalance.
- Described as low churn.

Reported performance (manager's own, backtest plus live): Covid fall -26% vs Nifty -38.4%. CAGR figures are login-gated on smallcase.

Fees and minimum: ₹6,999 a year (₹2,333 for 3 months); smallcase minimum ₹86,228 (Nov 2026); recommended ₹5 to 30 lakh.

Code-ready stand-in for backtesting (my proposal, to be swept): rank Nifty 50 members by 12-month return excluding the last month (alternatives 6-month, 12-month over volatility); buy top 10 equal weight; at each month end sell a holding only if its rank is worse than 20; replace with the best-ranked non-holding.

Feasibility at ₹1.5 lakh: yes if self-implemented. ₹15,000 per position, about 0.62% per round trip, most liquid stocks in India, low churn. Needs historical Nifty 50 membership to avoid survivorship bias.

Sources:
- https://weekendinvesting.com/strategies/mi-india-top-10/
- https://www.smallcase.com/smallcase/mi-india-top10-WKIMO_0020
- https://www.smallcase.com/manager/weekend-investing/smallcases

### 5. Weekend Investing Mi NNF10 (Nifty Next 50, top 10, monthly, always invested)

Rules as published:
- Universe: Nifty Next 50. Always 10 stocks, never cash. Each constituent is reset to 10% at the start of each month.
- Ranking on closing prices of the last trading day of the month; orders on the first trading day of the next month. "Classic momentum way to weed out losers and include winning stocks" (formula not disclosed).

Reported performance (manager's own): Apr 2016 to Nov 2022, ₹100 to ₹353 versus ₹227 for Nifty Next 50; CAGR 21.1% vs 13.3%; maximum drawdown 23.6% vs 42%. Tested on actual historical constituents over 10 years according to the manager. Live since 12 Nov 2020; live numbers are login-gated.

Fees and minimum: from ₹833 a month; minimum ₹1,14,341 (Nov 2026).

Cautions: monthly reset to equal weight means 10 trim or top-up trades a month if followed literally; at our size skip the reset and trade only entries and exits. The Next 50 has had index-method changes and large IPO-driven turnover; the junior index's own drawdown was 42% in the test window.

Feasibility at ₹1.5 lakh: yes if self-implemented (10 positions of ₹15,000). The published minimum already exceeds ₹1.1 lakh because of high-priced shares, so weights will be uneven.

Sources:
- https://www.smallcase.com/blog/the-mi-nnf-10-smallcase-a-passive-money-spinning-strategy/
- https://www.smallcase.com/manager/weekend-investing/smallcases

### 6. Weekend Investing rotational mid and small cap momentum (Mi 20, Mi 35)

Rules as published:
- Mi 20: universe Nifty MidSmallcap 400 (stocks ranked 101 to 500); 20 stocks at 5% each; weekly rebalance; always invested ("regardless of market conditions"); momentum rank; losers removed at the next rebalance if they meet the exit criterion.
- Mi 35: up to 35 stocks from Nifty Smallcap 250; weekly; rotational.

Reported performance (manager's own):
- Mi 20, 1 Apr 2016 to 25 Nov 2022: ₹100 to ₹485.6 versus ₹268.8 for the index; CAGR 26.8% vs 16%; return over maximum drawdown 0.7 vs 0.3 (implies a maximum drawdown near 38%, computed). CAGR from April 2016 fell to about 6% at the Covid low.
- Mi 35: CAGR from Apr 2016 to 31 Mar 2020 was 9.7% versus -9% for Smallcap 250; "almost 50% lower drawdowns".

Fees and minimum: Mi 20 ₹14,999 a year, minimum ₹2,04,105. Mi 35 from ₹833 a month, minimum ₹2,64,383.

Cautions:
- Survivorship bias in small-cap universes is large: an arXiv study of the Nifty Smallcap 250 (1,437 stocks, 2016 to 2025) finds survivor-only backtests overstate returns by 4.94 percentage points a year and that 82.5% of members turned over (https://arxiv.org/abs/2603.19380).
- Weekly small-cap rotation is the most cost-sensitive design at our size.

Feasibility at ₹1.5 lakh: no as specified (20 to 35 positions, weekly). A 10-name, monthly version is marginal.

Sources:
- https://www.smallcase.com/blog/mi-20-your-must-have-affordable-mid-small-cap-strategy/
- https://www.smallcase.com/blog/mi-35-extracting-alpha-from-smallcaps/
- https://weekendinvesting.com/strategies/mi-20/
- https://www.smallcase.com/manager/weekend-investing/smallcases

### 7. Weekend Investing absolute momentum with cash (Mi 25, Mi MT Allcap, Mi30)

Rules as published:
- Mi 25: up to 25 small-cap stocks at 4% each; market cap above ₹1,000 crore; average liquidity checked; "red flag" filter; selection on absolute momentum (each stock judged against its own history, not only against peers); weekly rebalance; if there are no candidates the slot sits in cash (LiquidBees). So the number of holdings falls in weak markets.
- Mi MT Allcap: up to 20 stocks from the most liquid names of any size, 5% each, same absolute-momentum and cash logic, weekly.
- Mi30: up to 33 Nifty 500 stocks, weekly.
- Entry and exit thresholds are not disclosed.

Reported performance (manager's own): Mi 25, Apr 2016 to Jan 2023: +506% vs +134% for Smallcap 250; CAGR 30.2%; Jan 2018 to Mar 2020 fall 29% vs 55%; 3-year return to 31 Mar 2020 +32% vs -42%.

Fees and minimum: Mi 25 ₹14,999 a year, minimum ₹1,99,188; Mi MT Allcap ₹19,999 a year, minimum ₹1,96,381; Mi30 from ₹2,950 a month, minimum ₹3,24,751.

Code-ready stand-in (my proposal): each week, a stock is eligible if close is above its 200-day average and within X% of its 52-week high and its 6-month return is positive; hold up to N eligible stocks ranked by 6-month return; exit when close falls below the 100-day average or the rank falls outside 2N; empty slots stay in a liquid ETF.

Feasibility at ₹1.5 lakh: marginal. The cash rule is attractive for a small account, but 20 to 25 weekly-rotated small caps is too many; test with N = 8 to 12.

Sources:
- https://www.smallcase.com/blog/mi-25-our-flagship-smallcap-strategy/
- https://weekendinvesting.com/strategies/mi-25/
- https://weekendinvesting.com/strategies/mi-mt-allcap/
- https://www.smallcase.com/manager/weekend-investing/smallcases

### 8. Weekend Investing all-time-high momentum (Mi ATH 2, Mi ST ATH)

Rules as published:
- Universe: NSE stocks with market cap above ₹500 crore and "very high turnover".
- Up to 10 stocks, equal weight. Selection by momentum rank and nearness to the all-time (or multi-year) high. Reviewed weekly; stocks that fail the exit criterion are dropped; if no new picks qualify the slot sits in LiquidBees. No manager discretion. "Very high churn."

Reported performance (manager's own): CAGR since 2016 "more than 40%"; Covid fall -16% vs -38.3% for Nifty 500.

Fees and minimum: Mi ATH 2 ₹9,999 a year (₹3,333 for 3 months); Mi ST ATH from ₹1,249 a month, minimum ₹1,04,339.

Related evidence: the 52-week-high effect is reported as "distinct and robust" in Indian equities, Oct 2004 to Aug 2023, more than 4,400 stocks, by Rajan Raju (SSRN 4587697) (unverified: snippet only; SSRN returned HTTP 403). StockViz back-tested a "high-to-price" variant on Indian stocks and noted naive monthly momentum portfolios in India "punished investors with +50% drawdowns every 3-4 years", that some picks fell 30% in a month, and that "the jury is still out" on crash avoidance (https://stockviz.substack.com/p/momentum-without-the-crash).

Code-ready stand-in (my proposal): weekly; eligible if close is at least 95% of the highest close in the available history (or 5 years) and 20-day median traded value is above ₹5 crore; rank by 6-month return; hold up to 10; exit if close falls 15% below the highest close since entry or below the 50-day average.

Feasibility at ₹1.5 lakh: marginal. Position count fits (minimum ₹1.04 lakh) and it holds cash in bad markets, but "very high churn" at 0.62% per round trip is expensive; all gains are short term.

Sources:
- https://weekendinvesting.com/strategies/mi-ath-2/
- https://www.smallcase.com/manager/weekend-investing/smallcases
- https://stockviz.substack.com/p/momentum-without-the-crash

### 9. Weekend Investing Mi EverGreen (75% momentum stocks, 25% gold)

Rules as published: 20 stocks from the Nifty 200 at about 3.75% each chosen by momentum rank, plus a fixed 25% in a gold ETF; monthly rebalance; losers removed at the next rebalance if they meet the exit criterion.

Reported performance (manager's own): Covid fall -18.7% vs -38.2% for Nifty 200; worst fall -41.27% vs -59.00% for Nifty (2008 backtest).

Fees and minimum: ₹14,999 a year; minimum ₹3,10,771.

Feasibility at ₹1.5 lakh: marginal as specified (20 stocks at ₹5,600 each). A scaled version (8 stocks plus gold ETF) is feasible and worth testing because the gold sleeve is a single cheap ETF order.

Sources:
- https://weekendinvesting.com/strategies/mi-evergreen/
- https://www.smallcase.com/manager/weekend-investing/smallcases

### 10. Static equity and gold allocation with rebalancing (NG5050, Mi Allcap Gold)

Rules as published:
- NG5050 (free smallcase): 50% Nifty ETF, 50% gold ETF, rebalanced to equal weight every month. Minimum ₹529. The smallcase is now marked "played out" and is no longer tracked.
- Mi Allcap Gold: 25% each in large caps, mid caps, small caps and gold (paid, minimum ₹4,59,150).

Reported performance: a TradingQnA poster quotes about 15.2% CAGR for NG5050 over roughly 3 years (second-hand). Zerodha's Sandeep Rao gives buy-and-hold over about 11 years to Nov 2025: Nifty +214% with a 38% drawdown, GoldM +161% with a 21% drawdown.

Feasibility at ₹1.5 lakh: yes. Two ETFs, two to four orders per rebalance. Monthly rebalancing is wasteful at our size; test quarterly or 5-point drift bands. This is the natural benchmark every other strategy must beat after costs and tax.

Sources:
- https://www.smallcase.com/smallcase/WKIET_0001
- https://www.smallcase.com/manager/weekend-investing/smallcases
- https://tradingqna.com/t/dual-momentum-strategy-with-niftybees-goldbees/174470
- https://tradingqna.com/t/trend-following-in-india-part-3-nifty-gold-strategy/188767

### 11. Momentum with a market trend overlay (MWM Momentum, Mystic Wealth)

Rules as published: 20 stocks; fully automated; proprietary algorithm ranks stocks on price momentum; "ride the winners and cut the losers"; "a trend following overlay on broader markets to sit out the bad days"; weekly rebalance; recommended size ₹4 to 40 lakh.

Reported performance: 14.7% 3-year CAGR, live data only, factsheet dated 4 Aug 2025; launched 14 Apr 2020. Fee ₹12,001 a year (₹4,720 for 3 months). Factsheet figures are not validated by any SEBI-recognised agency.

Code-ready stand-in (my proposal): strategy 2 or 4 with one switch: hold stocks only while the Nifty 500 (or Nifty 50) closes above its 200-day average (or 10-month average); otherwise liquid ETF.

Feasibility at ₹1.5 lakh: marginal (same as 3). The overlay cuts trades in bear phases but whipsaws in sideways markets.

Source: https://assets.smallcase.com/factsheets/MWMO_0002.pdf

### 12. Low-liquidity momentum (the "liquidity illusion" split)

Rules (T. Desai, BacktestIndia, published on freefincal in 2026):
- Universe: Nifty 200 (the Momentum 30 universe). Rank by 12-month return; take the top 30.
- Compute scaled turnover = daily traded value / market capitalisation. Split the 30 into the 15 with the highest scaled turnover and the 15 with the lowest.
- Equal weight, annual rebalance. Costs included: brokerage, slippage, 12.5% LTCG, 20% STCG. Data includes delisted stocks.

Reported performance (Dec 2006 to Jun 2025, net):
- Low scaled turnover 15: 19.43% CAGR, maximum drawdown -66.41%, 97% of rolling 3-year periods positive.
- All 30: 14.60% CAGR, maximum drawdown -70.61%.
- Nifty 50: 10.41% CAGR, maximum drawdown -55.12%.
- High scaled turnover 15: 8.51% CAGR, maximum drawdown -75.09%, more than 8 years to recover.

Interpretation offered by the author: the Indian momentum premium sits in the less-traded half and looks like an illiquidity premium; funds growing in size are pushed into the half where it vanishes; small accounts keep a structural edge. Caveats: single author with a product to promote, one universe, one rebalance schedule, and the split may proxy for something else (for example retail-driven froth in high-turnover names).

Feasibility at ₹1.5 lakh: yes. 15 positions of ₹10,000, annual rebalance (about 0.69% per round trip once a year), and holding more than 12 months moves gains to the 12.5% LTCG rate (an annual LTCG exemption of ₹1.25 lakh also applies: from memory, unverified). Needs market cap history (shares outstanding) in addition to prices.

Source: https://freefincal.com/is-indian-momentum-investing-just-a-liquidity-illusion/

### 13. Dual momentum between Nifty, gold and debt (three published variants)

Variant A, quarterly 3-month switch (TradingQnA, Oct 2024):
- At each quarter end compare the last 3 months' return of NIFTYBEES and GOLDBEES; hold the winner for the next quarter.
- Claimed (back-tested by ChatGPT on 14 years of end-of-day data): 16.06% CAGR, maximum drawdown -23.51%, Sharpe 0.95, versus NIFTYBEES 11.93% and -55.15%.
- Rebuttal in the same thread: the claim had look-ahead bias (the total equalled the sum of both assets' returns). A member's re-run with the decision made after the quarter and 0.5% cost per switch, Mar 2007 to Dec 2024: 9.11% CAGR, maximum drawdown -29.70%, Sharpe 0.60, total +369.98% versus +625.76% for NIFTYBEES and +570.93% for GOLDBEES held alone. Taxes not included. Daily correlation of the two ETFs' price levels over 17 years was 0.91.

Variant B, Antonacci monthly (Samasthiti Advisors, Feb 2024):
- Each month end: if Nifty 50's 12-month return is above a debt fund's 12-month return, hold whichever of Nifty 50 and gold has the higher 12-month return; otherwise hold the debt fund. One asset at a time.
- Backtest Dec 1996 to Jan 2024, month-end values: 14.0% CAGR vs Nifty 50 12.4%; drawdown about 21% in Nov 2008 (Nifty above 50%) and about 11% in 2020 (Nifty close to 30%). Beat buy and hold for every start year tested but one. No costs or taxes (a reader's comment raises this).

Variant C, 200-day (factorlab, Jul 2024):
- Hold Nifty if its 200-day return exceeds both gold's and a fixed deposit's; hold gold if gold's exceeds both; otherwise fixed deposit.
- Backtest 2014 to 2024: 18.79% CAGR vs Nifty 12.13% and gold 10.86%; maximum drawdown -11.42% vs -34.00% and -21.44%. Rebalance frequency, costs and taxes are not stated.

Variant D (Quant India, Feb 2025): hold NIFTYBEES if either a short (1 to 6 month) or a long (6 to 12 month) lagged return is positive, otherwise GOLDBEES; grid of windows shown only as charts.

Reading: the only variant that was independently re-run with costs lost to buy and hold. B and C show the familiar pattern of lower drawdown with similar or somewhat better return before tax; a full switch realises gains at 20% each time if held under a year.

Feasibility at ₹1.5 lakh: yes. One ETF order each way (about ₹106 per full switch); the liquid leg can be a liquid ETF. Tax is the main drag.

Sources:
- https://tradingqna.com/t/dual-momentum-strategy-with-niftybees-goldbees/174470
- https://samasthiti.substack.com/p/indian-edition-of-the-dual-momentum
- https://momentumlab.substack.com/p/backtesting-dual-momentum-strategy
- https://quantindia.substack.com/p/momentum-in-the-indian-market

### 14. Supertrend or EMA trend following on Nifty, daily bars, long only

Rules (Zerodha "The Long and the Short", Sandeep Rao, Nov 2025):
- Supertrend(10, 3) on Nifty daily closes: go long when the close is above the Supertrend line; exit when the close is below it. Long only.
- Comparison system: 8-period EMA, long when close above, exit when below.
- Stop-and-reverse versions also tested.

Reported performance (Nifty spot, Jan 2015 to Oct 2025, no costs):
- Long only, daily: Supertrend 44 trades averaging 270 points; 8-EMA 256 trades averaging 35 points (totals about 11,900 and 9,000 points, computed). Supertrend had the larger maximum drawdown, about 70% deeper than the EMA version.
- The short side lost on daily bars in both.
- On 4-hour bars (EMA 21 vs Supertrend 10,3): average 48 vs 153 points per long trade; on 1-hour bars (EMA 50): win rate 29% vs 42%; shorts made about 4,700 points with EMA vs 1,400 with Supertrend.
- Exact tables are images; the figures above are those quoted in the text.

Cautions: single instrument, parameters chosen after seeing results, spot index not a tradable series, no costs. A forum member's rule of thumb: if a 15 to 20% change in a parameter changes the result drastically, it is over-fitted.

Feasibility at ₹1.5 lakh: yes with NIFTYBEES (or a Nifty ETF) instead of futures: about 4 round trips a year, about ₹106 each. Not feasible with futures (margin about ₹2.2 lakh, notional about ₹19 lakh).

Sources:
- https://tradingqna.com/t/trend-following-in-india-part-2-building-a-simple-system-that-works/188483

### 15. Hourly Supertrend on Nifty plus gold, 50:50

Rules (same series, part 3): Supertrend(10, 3) on 1-hour bars for Nifty and for MCX GoldM (back-adjusted continuous futures). Long only. Enter at the next bar's open after a close above the Supertrend; exit at the next bar's open after a close below. Run both, half the capital each.

Reported performance (about 11 years to Nov 2025, unlevered, simple sum of percentage returns, no costs, TradingView backtest):
- GoldM +169%, Nifty +205%, 50:50 +187%.
- Maximum drawdown 6.6% for 50:50 vs 18.5% (Nifty) and 11.8% (gold); return over maximum drawdown 28.32; longest drawdown 70 days; correlation of the two return streams 0.04.
- Buy and hold over the same period: Nifty +214% (38% drawdown), GoldM +161% (21% drawdown). So the system matches buy and hold on return and cuts drawdown.
- Capital needed with futures at 2x leverage: about ₹15.75 lakh for one lot of each; exchange margin alone about ₹3.45 lakh.

Feasibility at ₹1.5 lakh: no with futures. Marginal with NIFTYBEES and GOLDBEES: needs hourly data and intraday order placement; the number of trades per year on hourly bars is much higher than on daily bars, so the ₹106 per ETF round trip and 20% STCG matter; gold ETF hours and MCX hours differ.

Source: https://tradingqna.com/t/trend-following-in-india-part-3-nifty-gold-strategy/188767

### 16. Donchian 20-day breakout and 5 x 20 SMA crossover on Nifty (negative result)

Rules: (a) long when the close exceeds the highest high of the last 20 days, stop at the 20-day low; short on the mirror image. (b) Long when the 5-day SMA is above the 20-day SMA, short when below. Tested long and short, long only, short only, on Nifty daily bars.

Reported performance (about 10 years to Oct 2025, no costs): the long-short versions had very poor Sharpe ratios and negative median profit per trade; the long-only Donchian was in drawdown for 5 years; the 5 x 20 long-only made about 7,500 points in 10 years. Author's verdict: "both are to be dumped". A forum member noted the short side shows a reverse edge, i.e. buying dips rather than shorting breakdowns.

Feasibility at ₹1.5 lakh: yes mechanically with an ETF (long only), but the evidence is negative.

Source: https://tradingqna.com/t/trend-following-in-india-part-1-testing-donchian-s-classic-rules/188234

### 17. Nifty 50 inclusion trade (buy on the effective date, hold two weeks)

Rules (Zerodha, June 2026): for each stock added to the Nifty 50 at the March or September review (mergers and demergers excluded), buy on the effective date (first working day after the March or September F&O expiry; announced about four weeks earlier) and sell after two weeks. Split capital equally if there are two inclusions.

Reported performance (33 inclusions, 2015 to 2025, price returns, not benchmark-adjusted, no costs):
- 2 weeks after: win rate 78.8%, mean +2.21%, median +3.07%, standard deviation 5.6%. 1 week: win rate 54.5%.
- 3 months: mean +3.19%, median -0.07%. 6 months: median -2.28%. 12 months: mean +4.81%.
- Compounded: ₹1 lakh became ₹1.22 lakh in 10 years (+22.25% total, about 1.9% a year, computed), maximum drawdown 14.30% (on the second trade, May 2015). Capital is idle most of the year.
- Before inclusion: 12-month mean +58% (median +43%, 93.9% positive); 6-month mean +19.94%; the week before, mean -1.60%. The author warns the pre-inclusion numbers are selection bias; the tradable idea is predicting inclusions from Nifty Next 50 free-float rankings 6 to 12 months ahead (data cut-offs 31 Jan and 31 Jul).
- US comparison in the same piece: the S&P 500 addition effect fell from over 7% in the 1990s to under 1% in the last decade.

Feasibility at ₹1.5 lakh: yes (one or two stocks, twice a year, about 0.3% round trip), but it adds only about 2% a year on the capital and can be layered on a core holding. Needs an event calendar.

Source: https://tradingqna.com/t/the-nifty-50-inclusion-trade-does-it-still-work/195419

### 18. "ETF ki Dukan" (ETF shop) by Mahesh Chander Kaushik: buy the weakest equity ETF daily, sell at a small fixed gain

This is probably the most widely copied small-account system in India (free Hindi YouTube course and Google Sheet by a SEBI-registered research analyst). Rules, 2026 version, from an English walkthrough of his class videos and sheet:

Universe construction (Class 1): download the NSE ETF list after the close; keep ETFs with volume above 100,000 units a day (about 320 falls to about 186); remove gold, silver and other commodity ETFs; remove liquid, gilt and debt ETFs; keep one ETF per index or sector, the highest-volume one (exception: Nifty 50, Nifty 50 equal weight and Nifty 50 Value 20 are all kept). Result: about 75 equity ETFs.

Daily routine (Class 2):
- Compute 14-day RSI (Wilder smoothing, about 150 calendar days of closes) for all 75. Rank the 5 lowest.
- Buy one ETF per day: the lowest-RSI ETF not already held.
- If all five are already held: buy more of a held ETF only if its price is more than 3% below the last purchase price of that ETF (trigger = last buy price x 0.97). Otherwise buy nothing.
- Sell one ETF per day: among holdings showing a gain of 4.57% or more over average cost (target = average cost x 1.0457), sell the most profitable one.
- No stop loss. No market filter: the sheet always shows five buy candidates.

Earlier versions (for parameter ranges): version 1 ranked by distance below the 20-day moving average, top 3, target 3.14%; the 2025 version ranked by nearness to the 52-week low, top 10, with an SIP-style auto-buy; target 6.28% was used for bull phases. Kaushik judged 3.14% too tight (costs and 20% tax eat it) and 6.28% too slow. The 2025 version's failure: a realty ETF at rank 10 was bought repeatedly near the same price by the auto-SIP, then fell 20%.

Evidence: no independent or audited backtest; the creator's experience and a three-month real-money diary. The walkthrough's own findings: on 3 Aug 2026 no ETF had RSI below 30 (lowest 37.56, median 59), yet the sheet still produced five buys; 51 of 75 prices failed to load from Google Finance; the method "has only been stress-tested in an up-and-to-the-right market".

Cost at our size: he sizes purchases at about ₹20,000. One round trip of a ₹20,000 ETF lot costs about ₹76 at Angel One (computed, 0.38%), against a gross target of ₹914 (4.57%); after 20% tax the net is about ₹670. The economics work per trade; the risk is capital getting stuck in falling sector ETFs with no stop.

Feasibility at ₹1.5 lakh: marginal. ₹1.5 lakh funds about 7 lots of ₹20,000, which a falling market exhausts in under two weeks; smaller lots (₹7,500) push cost to 0.57% per round trip. It can be coded exactly on daily data.

Sources:
- https://therationalinvestor.in/blog/etf-ki-dukan-strategy
- https://www.maheshkaushik.com/

### 19. Kaushik's Nifty 50 ETF daily grid (1.57% steps, 15 Nifty ETFs) with the author's 5-year backtest

Published 31 Oct 2026 on his blog (Hindi), with complete rules and a trade-by-trade Excel backtest. Rules:
1. Look once a day at NSE official closing prices. At most one trade a day: one sell, or one buy, or nothing.
2. Use 15 different Nifty 50 ETFs in a fixed rank order: NIFTYBEES, SETFNIF50, HDFCNIFTY, NIFTY1, NIFTYBETA, NIFTYIETF, NETF, QNIFTY, NIFTYAXIS, MOM50, NIFTYETF, NIFTYCASE, GROWWNIFTY, AONENIFTY, ENIFTY. (Different tickers for the same index so each lot has its own cost.)
3. Day 1: buy ₹20,000 of rank 1. Every purchase is ₹20,000, quantity rounded up.
4. Sell rule (checked first): among held ETFs whose close is more than 1.57% above their purchase price, sell the one with the highest percentage gain, the whole lot. Only one per day.
5. No buy on a day with a sell.
6. Buy rule: look only at the most recently bought ETF. If its close is more than 1.57% below its purchase price, buy the highest-ranked ETF not currently held.
7. If the most recently bought ETF has already been sold, the buy gate is open on the next day at any price.
8. Never average: an ETF already held is not bought again. If all listed ETFs are held, do nothing.
9. A sold ETF can be bought again later (not the same day).
10. Only principal recycles; profit is withdrawn as income.

Author's backtest (21 Oct 2021 to 19 Oct 2026, 1,239 trading days, ₹20,000 per lot, no costs, no tax, no interest on idle cash):
- 148 sells, 160 buys, booked profit ₹65,697; profit per sell ₹315 to ₹1,038 (average about ₹444). Half the sells came within 15 days; the longest lot took 401 days.
- Peak capital deployed ₹2,41,536 (12 ETFs held on 8 Oct 2026); recommended fund ₹3,00,000.
- By year: 2021 (from 21 Oct) ₹2,238; 2022 ₹20,227; 2023 ₹9,130; 2024 ₹10,044; 2025 ₹13,106; 2026 (to 19 Oct) ₹10,953. Average ₹1,077 a month; 12 of 61 months had no sale.
- Worst paper loss -₹25,569 on 17 Jun 2022 (11 lots held). On the last day 12 lots were open with a paper loss of -₹13,029, so booked plus open = ₹52,668.

My reading (computed): ₹52,668 over 5.02 years is about ₹10,500 a year, i.e. about 3.5% a year on the recommended ₹3 lakh, or 4.4% a year on peak deployed capital, before charges. Angel One charges on 148 round trips of ₹20,000 would be about ₹11,200 (148 x ₹75.5), and 20% tax applies to booked gains. Net of both, and counting the open loss, it is roughly 2% a year on the ₹3 lakh fund (about 2.5% on peak deployed capital), below a liquid fund, although idle cash would add interest. In a rising market most capital sits idle; in a falling market all lots are stuck. It is a volatility-harvesting scheme whose income equals small realised gains while losses stay unrealised.

Feasibility at ₹1.5 lakh: marginal. With ₹10,000 lots the fixed costs double as a share of profit (about ₹50 on an average gross gain near ₹220). Fully testable on daily ETF closes; the author's trade list makes it a good engine validation case.

Source: https://www.maheshkaushik.com/

### 20. Nifty 50 stock version: buy the stock furthest below its 20-day average, sell at +5%

Rules (TradingQnA user, April 2024, "based on Mahesh Chandra Kaushik strategy"): scan Nifty 50 stocks; compute percentage difference between price and 20-day moving average; buy the one furthest below; sell any holding with profit above 5%; a trailing stop was wished for but not implemented. No stop loss.

Reported performance: the user reports XIRR of 44.91% running it from Sep 2023 to Apr 2024 (7 months of a bull market, self-reported, unaudited) and expects 12 to 24%. Forum replies: "Why buy the stocks which are in downtrend? Implement this strategy in ETFs, not in stocks"; and a warning that using today's Nifty 50 list for old years creates survivorship bias. Streak could not implement the cross-sectional ranking.

Feasibility at ₹1.5 lakh: marginal. It fits mechanically (one buy a day of ₹7,500 to ₹15,000; 0.6 to 0.8% round trip against a 5% target), but single stocks do not always recover and there is no exit for losers, so capital can lock up.

Source: https://tradingqna.com/t/buy-the-stock-has-comparatively-fallen-the-most-from-its-20-dma/164322

### 21. V20 pullback (popular Indian YouTube swing pattern)

Rules (open-source TradingView implementation, July 2026; originator not named on the page):
- Find a run of consecutive green daily candles (at least 2) that gains at least 20% from the lowest low of the run to its highest high.
- Place a limit buy at the base (lowest low) of that run, fixed cash per trade (default ₹10,000). The order never expires.
- Exit with a limit sell at the top (highest high) of the run. No stop loss.
- Optional filter: the base must be below the 200-day SMA, except for a list of large caps that are exempt.
- Multiple setups can be open at once.

Evidence: none found beyond the script; no published statistics. Structurally it is a 20% range mean-reversion bet with unlimited holding time and no stop.

Feasibility at ₹1.5 lakh: yes mechanically (15 slots of ₹10,000, about 0.69% round trip against a 20%+ target), but unfilled and stuck orders tie up capital. Testable on daily OHLC.

Source: https://www.tradingview.com/script/2F8X7p1e-V20-Strategy/

### 22. 9:20 intraday short straddle (the best-known Indian retail algo)

Rules (consistent across TradingQnA, Marketcalls, AlgoTest):
- At 09:20 sell the at-the-money call and put of the current weekly expiry (Nifty; historically Bank Nifty).
- Place a stop on each leg at entry price x (1 + SL), SL = 25% (most common), 35% or 40%. If one leg stops out, the other continues with its stop.
- Square off at 15:10 to 15:15.
- Variants: entry at 09:16, 09:30 or 10:30; combined-premium stop; re-entry; far out-of-the-money wings to cut margin (see 23).

Reported performance and decay:
- KirubaKaran's analysis (May 2022, 25% stop, about 1,300 trades over 5 years): profitable overall, best on Wednesdays, worst on Fridays, profitable in high VIX too; but "if I remove top 10% of the trades ... the overall results turns negative". Returns are lumpy with long drawdowns.
- Marketcalls (Aug 2021): the strategy "can be gamed with stop hunting" because thousands of accounts have stop-market orders at the same percentage levels; Quantman backtests from 2017 (monthly) and April 2019 (weekly) were positive.
- Marketcalls (Dec 2023), Bank Nifty weekly, 35% stops, since 2017 with 0.5% slippage and commissions: the edge diminished in 2023 as sellers crowded in and volatility fell; a 10:30 entry "could have done much better".
- TradingQnA (Feb 2025): a no-stop Nifty straddle in December 2024 made money on 12 of 20 days (sum about +434 points before costs, computed from the table); replies call one month an outlier-prone sample and note the straddle can double intraday. One trader "stopped ... now days its problem with margin requirement".
- Streak's stock "Nifty Income short straddle" showed "more than 30% return in a week" because Streak computed percentage on premium, not margin; Streak staff restated it as 5.44% on about ₹1.4 lakh margin for that week and advised allowing 2 to 3% slippage on option entries.
- AlgoTest (2026) still lists it first among retail options algos and offers a step-by-step 25% stop template, without publishing results.
- SEBI's October 2024 measures raised the minimum contract value for index derivatives, restricted weekly expiries to one benchmark index per exchange and required upfront collection of option premium (Open magazine summary). The Bank Nifty weekly version of this strategy therefore no longer exists (NSE kept Nifty as its weekly: from memory, unverified).

Feasibility at ₹1.5 lakh: no. Margin about ₹2.36 lakh per lot of 75 (Feb 2025). Charges alone would be about 22% of capital a year (0.6).

Sources:
- https://tradingqna.com/t/detailed-analysis-of-920-short-straddle-strategy-is-it-stopped-working/130677
- https://tradingqna.com/t/reports-of-the-death-of-920-short-straddle-are-greatly-exaggerated/179061
- https://www.marketcalls.in/futures-and-options/is-the-920-straddle-no-more-working.html
- https://www.marketcalls.in/futures-and-options/how-the-9-20-intraday-straddlers-are-being-gamed.html
- https://tradingqna.com/t/is-nifty-income-short-straddle-strategy-on-streak-really-profitable-see-details/122634
- https://algotest.in/blog/the-920-straddle-strategy-defined.md

### 23. Hedged versions: intraday iron fly and iron condor

Rules:
- Iron fly: the 9:20 straddle plus long wings, for example buy the put 300 points below and the call 300 points above (TradingQnA example: sell 23600 CE and PE, buy 23300 PE and 23900 CE). Margin fell from ₹2,36,316 to ₹93,741 for one lot; maximum loss and profit are both capped.
- Iron condor (AlgoTest example): sell out-of-the-money call and put (for example 300 points either side of spot), buy further out-of-the-money call and put; profit if the index stays inside the short strikes.
- Exit: stop on each short leg or on combined premium, target, or time exit.

Evidence: no published track record found; a forum trader reports a "modified 9:30 strangle" working in live testing (anecdote). KirubaKaran notes that people who used out-of-the-money hedges for margin benefit "would have suffered more" in drawdowns because the freed margin was used for more lots.

Feasibility at ₹1.5 lakh: marginal on margin (one lot fits), no on economics: 8 orders a day is about ₹235 a day, about 38% of capital a year (0.6), on a structure whose maximum daily profit is the net credit.

Sources:
- https://tradingqna.com/t/reports-of-the-death-of-920-short-straddle-are-greatly-exaggerated/179061
- https://algotest.in/blog/6-popular-algo-trading-strategies-for-retail-traders-in-india.md
- https://tradingqna.com/t/detailed-analysis-of-920-short-straddle-strategy-is-it-stopped-working/130677

### 24. Opening range breakout (15 minutes)

Rules (AlgoTest's list of the six most automated retail strategies, Mar 2026): mark the high and low of the first 15 minutes (09:15 to 09:30); buy when price breaks above the 15-minute high; exit at a target or at the end of the day. The short side on a break of the low, the stop (usually the other side of the range) and the target are left to the user.

Evidence: described as popular; no performance published. Platform-level cautions apply: Streak users report that candle-close signals with market orders enter worse than the backtest and hit stops more often; Tradetron-style marketplace statistics often ignore spread, slippage and commissions.

Feasibility at ₹1.5 lakh: marginal. Intraday equity in a liquid stock or ETF costs about ₹47 brokerage and GST plus 0.025% STT per round trip at full size; index options or futures versions run into the lot and margin limits. Needs intraday data.

Sources:
- https://algotest.in/blog/6-popular-algo-trading-strategies-for-retail-traders-in-india.md
- https://tradingqna.com/t/backtest-vs-papertrading-results-from-streak-pretty-close/116932

### 25. 9 EMA and 20 EMA crossover

Rules (AlgoTest): buy when the 9-period EMA crosses above the 20-period EMA; sell when it crosses below. Timeframe not fixed (commonly 5 or 15 minutes intraday, or daily).

Evidence: none published by the platform; it warns of false signals in sideways markets. The closest Indian test is Zerodha's: an 8-EMA price cross on Nifty daily made only 35 points per trade over 256 long trades in about 11 years before costs, and a 5 x 20 SMA cross was "to be dumped" (strategies 14 and 16).

Feasibility at ₹1.5 lakh: yes mechanically on an ETF; evidence is weak to negative.

Sources:
- https://algotest.in/blog/6-popular-algo-trading-strategies-for-retail-traders-in-india.md
- https://tradingqna.com/t/trend-following-in-india-part-2-building-a-simple-system-that-works/188483

### 26. Intraday mean reversion: VWAP and Bollinger bands

Rules (AlgoTest): VWAP reversion - short when price is "significantly" above the session VWAP, cover at VWAP (and the reverse for longs). Bollinger reversion - short when price touches the upper band, cover at the middle band (and the reverse). The thresholds, timeframe and stops are not specified; said to work in range-bound markets.

Evidence: none published. A long-time TradingQnA systematic trader says both intraday mean reversion and intraday momentum in stocks "are feasible", that intraday shorts work, that scalping probably does not survive costs, and that his edge comes from running several uncorrelated systems (anecdote; no numbers).

Feasibility at ₹1.5 lakh: marginal. Intraday equity allows shorting and leverage, and charges are about 0.13% per round trip at ₹50,000 trade size, 0.08% at ₹1,00,000 and 0.045% at ₹5,00,000 (computed from 0.1), but edges per trade are small. Needs intraday data.

Sources:
- https://algotest.in/blog/6-popular-algo-trading-strategies-for-retail-traders-in-india.md
- https://tradingqna.com/t/trend-following-in-india-part-1-testing-donchian-s-classic-rules/188234

### 27. SIP timing on a Nifty ETF: buy the dip, buy above or below the 200-day average (negative result)

Rules tested by Indian bloggers:
- Dip SIP (freefincal): invest half the monthly amount regularly; park the other half in a liquid fund and move it to equity only when a dip signal built from 6-month and 12-month moving averages is on. Mirror version: deploy only when the momentum signal is on.
- 200-day rule (freefincal): invest only on days the Nifty is below (or only when above) its 200-day average; idle cash earns 8%.
- Threshold dips (The Market Shack): ₹10,000 a month accumulates at 5%; deploy everything the morning after an intraday fall, or at the open on a gap-down, of at least X% (X from 0% to 4% in 0.2% steps), with and without a month-end fallback; 152 combinations.

Reported results:
- freefincal, Sensex TRI plus liquid fund, 122 rolling 15-year periods: "no difference between the two strategies" before tax, and dip buying slightly worse recently; the same for the momentum version; the same for the S&P 500 over 262 rolling 30-year periods. Verdict: "waiting to buy on market dips is a useless strategy ... a loss-making strategy if we factor in taxes".
- freefincal 200-day study: over 3,062 rolling 5-year periods, buying only above the 200-day average produced the higher corpus in many periods; no consistent winner. A search summary of related freefincal posts gives, for 1999 to 2016, XIRR 12.29% for a blind daily SIP, 11.53% for above-200-day only and 13.25% for below-200-day only (unverified: snippet only).
- The Market Shack, Nifty 50 about 1994 to 2024: none of 152 dip rules beat the plain monthly SIP (12.04% XIRR, ₹36.1 lakh contributed became ₹3.11 crore). The most selective rules (3.8 to 4.0% gap-downs, four trades in 30 years) earned 8.65% XIRR. Large gap-downs marked the start of drawdowns, not bargains.

Feasibility at ₹1.5 lakh: yes mechanically, but it is about deploying new savings, not about growing a fixed pot, and the evidence is negative.

Sources:
- https://freefincal.com/stop-waiting-to-buy-on-market-dips-it-is-useless/
- https://freefincal.com/?p=17637
- https://finance-platform-fawn-ten.vercel.app/projects/buying-nifty-after-it-falls-152-tests-across-30-years-show-the-same-thing

### 28. DIY capital-protected structure: liquid or gilt fund plus a long-dated Nifty call

Rules (Zerodha, Dec 2025): on the first trading day of the year, capital = Nifty spot x lot size. Buy one at-the-money December call (strike rounded to the nearest 1,000 for liquidity). Put the rest in a liquid, gilt or conservative hybrid fund. Hold to the December expiry. Repeat yearly.

Reported performance (2019 to 2025 backtest): example for Jan 2025 - 24000 December call cost ₹1,980 x 75 = ₹1.48 lakh on ₹18 lakh capital; maximum potential drawdown equals call premium minus fund yield, at most 6.4% (2022); 2019: gilt plus call 14.40% vs NIFTYBEES 12.9%, liquid plus call 9.99%; underperformed in absolute terms in 2025. Roughly a 9% fund yield would be needed to make the downside zero.

Feasibility at ₹1.5 lakh: no. Needs capital equal to one lot's notional (about ₹18 lakh). A scaled-down spirit (most capital in a liquid ETF, a small fixed budget for long-dated calls) breaks the one-lot ratio.

Source: https://tradingqna.com/t/limited-downside-nifty-strategy/189648

### 29. PMS and AIF quant funds (context, not investable at our size)

No strategy card is written for this section: it is a reality check on live professional results, not a codeable rule set.

- Capitalmind Adaptive Momentum PMS: see 3. Minimum ₹50 lakh (regulatory PMS minimum, as stated on PrimeInvestor's page).
- Wright Factor Fund PMS (Sonam Srivastava; multi-factor quant): AUM ₹214 crore; as on 31 Aug 2026 year to date 14.22%, 1 year 16.93%, 2 years 0.15% a year, since inception 20.33% vs Nifty 500 12.21%; volatility 21.03% vs about 14.86%; fund age 3 years (zfunds listing). Maximum drawdown -27.91%, peak Dec 2024 to trough Apr 2025, vs about -18.6% for the benchmark (unverified: snippet only).
- Wright Momentum smallcase (launched 2020): rules are not public beyond "systematic momentum with risk control, profit target and stop loss ideas"; the performance widgets on the page did not load in text form, so I have no live numbers.
- Industry self-assessment for 2025 (PMS Bazaar fund manager brief, volume 72): "Pure momentum strategies struggled during Jan-Feb and July-Aug selling pressure. The key insight: single-factor quantitative funds are essentially beta plays. True systematic alpha requires factor diversification, regime awareness". Another manager in the same brief: "I over-traded a momentum strategy that showed back tested alpha but generated transaction costs that consumed all excess returns."
- Other quant PMS names surfaced only in search summaries (Dolat Quantum Leap, live from 16 Jan 2026 with back-tested history from 2001; East Green Advisors) (unverified: snippet only).

Feasibility at ₹1.5 lakh: no (₹50 lakh minimum for PMS). Useful only as a reality check on what fee-paid professional momentum earned live: roughly index-like over the last 5 years, with deeper drawdowns.

Sources:
- https://capitalmind.in/portfolio-management-service/momentum
- https://zfunds.in/portfolio-management-services/wright-factor-fund
- https://www.wrightresearch.in/blog/complete-guide-to-momentum-investing-and-the-wright-momentum-portfolio/
- https://resources.pmsbazaar.com/fund-manager-brief/2025/PMSBazaar-Fund-Manager-Brief-Vol-72.pdf
- https://primeinvestor.in/reports/pros-and-cons-of-momentum-investing/

---

## Instruments and holding periods at a glance

| # | Strategy | Instruments | Typical holding period | Data needed |
|---|---|---|---|---|
| 1 | Nifty200 Momentum 30 rules | momentum ETF or index fund; or 30 Nifty 200 stocks | 6 months between rebalances | index series; or daily stock prices, index membership, free float |
| 2 | Naive top-30 12-month momentum | NSE cash equities | 1 month re-rank, names last 2 to 6 months | daily stock prices, delisted names |
| 3 | Capitalmind-style volatility-adjusted momentum with cash | NSE cash equities, liquid ETF | 2 to 3 months per stock | daily stock prices and volume |
| 4 | Mi India Top 10 style | Nifty 50 stocks | monthly check, low churn | daily prices, Nifty 50 membership history |
| 5 | Mi NNF10 style | Nifty Next 50 stocks | monthly | daily prices, Next 50 membership history |
| 6 | Mi 20 and Mi 35 style | mid and small cap stocks | weekly check | daily prices, index membership history |
| 7 | Absolute momentum with cash (Mi 25, MT Allcap) | liquid NSE stocks, LiquidBees | weekly check | daily prices and volume, market cap |
| 8 | All-time-high momentum (Mi ATH) | liquid NSE stocks, LiquidBees | weekly check, very high churn | long daily price history |
| 9 | 75% momentum stocks, 25% gold | Nifty 200 stocks, gold ETF | monthly | daily prices, membership history |
| 10 | Static Nifty and gold | Nifty ETF, gold ETF | permanent, periodic rebalance | daily ETF or index prices |
| 11 | Momentum with market trend overlay | NSE stocks, liquid ETF | weekly check | daily prices |
| 12 | Low-liquidity momentum | 15 Nifty 200 stocks | 12 months | daily prices and traded value, market cap |
| 13 | Dual momentum Nifty, gold, debt | NIFTYBEES, GOLDBEES, liquid ETF | 1 to 3 months between checks | daily ETF or index prices |
| 14 | Daily Supertrend or EMA on Nifty | Nifty ETF (futures need more capital) | weeks to months, about 4 trades a year | daily index OHLC |
| 15 | Hourly Supertrend, Nifty plus gold | futures, or ETFs as a substitute | days to weeks | hourly bars |
| 16 | Donchian 20 and 5 x 20 SMA | Nifty ETF or futures | days to weeks | daily index OHLC |
| 17 | Nifty 50 inclusion trade | the included stock | 2 weeks, twice a year | daily prices, NSE review announcements |
| 18 | ETF ki Dukan | about 75 equity ETFs | days to months, no stop | daily ETF closes and volume |
| 19 | Nifty ETF 1.57% grid | 15 Nifty 50 ETFs | median 15 days, up to 401 days | daily ETF closes |
| 20 | Furthest below 20-day average, +5% target | Nifty 50 stocks | days to months, no stop | daily prices, membership history |
| 21 | V20 pullback | NSE stocks | open-ended | daily OHLC |
| 22 | 9:20 short straddle | Nifty weekly options | intraday | 1-minute option prices |
| 23 | Iron fly, iron condor | Nifty weekly options | intraday to expiry | 1-minute option prices |
| 24 | Opening range breakout | index futures or options, liquid stocks | intraday | 1 to 15-minute bars |
| 25 | 9 and 20 EMA crossover | any | intraday to weeks | bars at the chosen timeframe |
| 26 | VWAP and Bollinger reversion | liquid stocks, index derivatives | intraday | intraday bars with volume |
| 27 | SIP timing | Nifty ETF, liquid fund | accumulation | daily index OHLC |
| 28 | Liquid fund plus long-dated Nifty call | Nifty December call, debt fund | 1 year | daily option settlement prices, fund NAV |
| 29 | PMS and AIF quant funds | not accessible | n/a | n/a |

## Which of these survive ₹1.5 lakh with ₹20 flat brokerage and DP charges

| Group | Verdict | Why |
|---|---|---|
| One or two ETFs, few trades a year (static Nifty and gold; dual momentum; daily Supertrend on a Nifty ETF; momentum index ETF) | Survives | ₹60 to ₹110 per full switch; tax is the only real drag |
| 10 large-cap momentum names, monthly, with a rank buffer (Mi India Top 10 or NNF10 style, self-built) | Survives | ₹15,000 positions, about 0.62% per swap, low churn; published minimums ₹0.86 to 1.14 lakh |
| 15 names, annual rebalance (low-liquidity momentum) | Survives | one round trip a year, long-term tax rate |
| 20 to 35 names, weekly (Mi 20, Mi 25, Mi 35, Capitalmind style) | Marginal to no | ₹4,000 to ₹7,500 positions, 0.8 to 1.2% per swap, about 2% or more a year in charges, uneven weights |
| ETF shop and grid systems | Marginal | economics per trade are fine at ₹20,000 lots, but only 7 lots fit and capital gets stuck; author's own 5-year backtest nets about 3.5% a year before costs |
| Event trade (index inclusion) | Survives as an add-on | 2 to 4 trades a year, about 2% a year on capital |
| Any option selling, futures trend following, structured products | No | margin ₹0.94 to 2.4 lakh per lot, or ₹15 to 18 lakh capital; fixed charges 22 to 38% of capital a year for daily one-lot option structures |
| Paid smallcases, PMS, AIF | No | fees 4.7 to 13% of capital; PMS minimum ₹50 lakh |

## Negative or cautionary evidence

1. Live momentum decayed after it became popular. Capitalmind Adaptive Momentum, net of fees: 5 years 7.0% a year vs Nifty 50 TRI 8.3%; 3 years 7.9% vs 10.1%; 2 years -5.9% vs +2.3% (to 6 Nov 2026). The since-inception lead (17.8% vs 12.4% over 7 years) was earned in 2019-21. The NSE momentum indices lagged their parents by 9 to 15 points in calendar 2025 and the Momentum 30 fell 31.8% from Sep 2024 to Apr 2025.
2. The oldest momentum smallcase closed. Capitalmind shut its smallcase on 30 Sep 2025, citing the tax change, crowding and a poor year for every one of more than 25 momentum definitions it tested.
3. Crowding is measurable. 24 passive funds with over ₹17,000 crore track the Nifty momentum indices; one rebalance (Dec 2025) replaced 19 of 30 stocks with about ₹16,130 crore of forced round-trip trades.
4. The premium may be an illiquidity premium. In a 2006-2025 net-of-cost test the liquid half of the top-30 momentum names earned 8.51% a year (below the Nifty 50's 10.41%) and the illiquid half 19.43%.
5. Maximum drawdowns are equity-like or worse: 68% to 73% for the NSE momentum indices in back-history; deeper than the index for naive momentum in 2008; 66% to 75% for the top-30 momentum variants in the freefincal test; Weekend Investing's own EverGreen backtest shows -41%.
6. Survivorship bias in Indian small-cap backtests is about 5 percentage points a year (arXiv 2603.19380). Most forum backtests use today's index members.
7. A widely shared ChatGPT-made dual momentum backtest (16.06% CAGR) contained look-ahead bias; the corrected run with 0.5% switching cost gave 9.11% and lost to both buy-and-hold legs.
8. Simple daily trend rules on the Nifty fail: Donchian 20 and 5 x 20 SMA "are to be dumped"; an 8-EMA rule made 35 points a trade before costs. Shorting the Nifty on daily signals lost money.
9. The index inclusion effect is small: +2.21% mean over two weeks, about 1.9% a year on capital, and the US version decayed from over 7% to under 1%.
10. Dip-buying and SIP-timing rules do not beat a plain SIP: 0 of 152 rules over 30 years; no difference over 122 rolling 15-year Sensex windows.
11. Kaushik's own 5-year grid backtest nets ₹52,668 on a ₹3 lakh fund (about 3.5% a year) before any charges or tax, with twelve lots under water at the end.
12. The 9:20 straddle's profits depend on the top 10% of trades; removing them turns five years negative. Its edge shrank in 2023, stops are hunted, weekly Bank Nifty expiries are gone and margins rose.
13. Retail F&O outcomes: 91% of individuals lost in FY25 and 87.7% in FY26; about ₹25,000 crore a year goes in transaction costs; among those who lost two years running and continued, about 90% lost again; algorithmic entities earned 99% of proprietary and FPI derivative profits.
14. Platform backtests mislead: Streak showed percentage returns on premium rather than margin; Tradetron marketplace pages showed 1,455% annual return with inconsistent drawdown figures and no slippage or commissions; one analyst's rule of thumb is to deduct about 5 Nifty points per trade and expect 30 to 40% fewer points on futures than on spot, and to demand 7 to 10 years or 1,000 trades of history.
15. Momentum managers themselves say about half of all positions lose and that momentum trails the Nifty in about 30% of rolling one-year periods.

## Open questions

1. Weekend Investing live performance 2023 to 2026. All CAGR figures on smallcase are login-gated ("returns stay locked unless you ask to view them"). The published numbers stop in Nov 2022 to Jan 2023, before the 2024-25 momentum drawdown. Someone with a smallcase login should record 1, 3 and 5-year live CAGR and drawdown for Mi India Top10, Mi NNF10, Mi 20, Mi 25, Mi ST ATH.
2. Weekend Investing ranking formulas, exit ranks and the cash trigger are not public. The stand-ins I propose in 4, 7 and 8 are my own and must be swept, not treated as the managers' rules.
3. Wright Momentum smallcase: rules and live numbers were not retrievable in text form.
4. Nifty and Bank Nifty lot sizes and margins for late 2026 were not verified here (sources use lot 75 and about ₹2.2 to 2.4 lakh margin from 2025).
5. STT on equity ETF delivery sells (I assumed 0.001%) and whether Angel One's ₹5 minimum brokerage applies exactly as "max(5, min(20, 0.1%))" should be checked on a contract note.
6. SEBI's retail algo framework (broker-registered algos, static IP for API orders, order-rate thresholds) and how Angel One SmartAPI implements it in 2026: not verified here; the search budget ran out. It decides whether a self-hosted bot is even permitted to place these orders.
7. The NSE methodology document's rank-buffer numbers for the momentum indices and the exact price-return windows (whether the most recent month is skipped) were not opened.
8. Stockopedia-style rank systems for India and "NiftyBeES SIP timing" threads beyond freefincal and The Market Shack: nothing specific found.
9. Popular Tradetron marketplace strategies with multi-year live subscriber results: no reliable source found; the only material is a 2020 warning post.
10. Marketcalls open-range-breakout and Supertrend system pages with full statistics were not found within the search budget.
11. Raju (SSRN 4587697, 52-week high) and Raju and Teli (SSRN 4163613, conservative formula in India) could not be opened; their decile returns and cost assumptions are needed before coding strategy 8's academic version.
12. Does the low-liquidity momentum split (12) hold with monthly or semi-annual rebalancing, in the Nifty 500, and after 2021? It is the one claim here that says a small account has an edge over funds, so it deserves an independent test first.
13. Momentum ETF plus a simple cash rule (for example hold a Nifty200 Momentum 30 ETF only above its 200-day average): nobody in these sources published it, yet it is the cheapest way to hold momentum at ₹1.5 lakh. Worth testing on the index series from 2005.
