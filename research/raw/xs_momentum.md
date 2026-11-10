# Cross-sectional equity momentum: research findings

Researcher area: cross-sectional (relative) stock momentum for an Indian retail account of ₹1,50,000 at Angel One.
Date of work: 2026-11-10. All web pages and PDFs cited under "Sources" were opened and read with `research/tools/fetch_text.py` unless a claim is marked "(unverified: snippet only)" or "(unverified: not opened)".

## 0. How this was produced, and its limits

- 22 web searches ran (academic, practitioner, NSE methodology, Indian news, broker pages). After that the shared search budget for this run was exhausted, so five planned searches (conservative formula in India, Capitalmind lookback and stop-loss posts, Budget 2026 tax text, Indian sector-momentum backtests, Carhart-alpha studies on Nifty 500) did not run. I continued by opening known URLs directly. Gaps that follow from this are listed under "Open questions".
- Sites that blocked the fetcher: SSRN (403), core.ac.uk (403), emerald.com (403), academia.edu (403), hdfcfund.com (403), web.iima.ac.in legacy host (502). Substitutes used: Erasmus repository copy of Blitz-Huij-Martens, NBER copy of Daniel-Moskowitz, University of Houston copies of Jegadeesh-Titman 1993 and George-Hwang 2004, RePEc abstracts, Alpha Architect and CXO Advisory summaries, and the IIMA faculty-site data library.
- Three sets of numbers are **my own computations**, not published results, and are labelled as such: (a) descriptive statistics from the IIM Ahmedabad Fama-French-Momentum data library CSV files (release 2025-12); (b) a bear-state split and a volatility-scaling test on the same IIMA long-short momentum factor; (c) an Angel One delivery cost table built from the charges on angelone.in.
- Nothing here is a backtest of an investable long-only strategy by me. Published index back-histories are hypothetical before each index launch date (launch dates are listed in section 1.2).

## 1. Time-sensitive facts checked against 2026 sources

### 1.1 Costs and taxes for delivery equity at Angel One (checked 2026-11-10)

| Item | Value | Source |
|---|---|---|
| Brokerage, equity delivery | lower of ₹20 or 0.1% per executed order, minimum ₹5 | angelone.in/exchange-transaction-charges |
| STT, delivery | 0.1% on buy and on sell | angelone.in; zerodha.com/charges |
| NSE transaction charge, cash | 0.0030699% (Angel page); 0.00307% (Zerodha page) | same |
| Stamp duty, delivery | 0.015% on buy | same |
| SEBI fee | ₹10 per crore | same |
| GST | 18% on brokerage + transaction + SEBI charges | same |
| DP (demat debit) charge | ₹20 + GST per ISIN per sell; ₹50 per ISIN for BSDA clients | chittorgarh.com Angel One page (the Angel page shows "₹20 per ISIN" without the BSDA split) |
| Demat AMC | ₹60 + GST per quarter for non-BSDA; BSDA nil up to ₹4 lakh holdings | angelone.in |
| STT, futures / options (for reference) | 0.05% sell / 0.15% sell on premium | angelone.in; zerodha.com/charges |
| STCG, listed equity held under 12 months | 20% for sales after 23 July 2024 | Zerodha Varsity taxation chapter |
| LTCG, listed equity held over 12 months | 12.5% on gains above ₹1.25 lakh per year, for sales after 23 July 2024 | Zerodha Varsity taxation chapter |

Consequence for momentum: most gains from a monthly or quarterly rebalanced portfolio are short term and taxed at 20%. Capitalmind's own FAQ says its momentum portfolio "typically holds stocks for two to three months" and tells subscribers to assume the STCG rate on gains plus "another 1% of gains" for brokerage, STT and DP charges (their page still quotes the old 15% rate). A strategy that rebalances once a year can shift most gains to LTCG, and at ₹1.5 lakh the ₹1.25 lakh annual exemption would cover essentially all of it.

### 1.2 NSE strategy index performance as of 30 October 2026 (niftyindices.com factsheets)

Total-return index, CAGR for periods over one year. "SI" is since each index's base date. Launch date is when NSE began publishing the index; everything before it is back-calculated.

| Index | Base date | Launch date | 1Y TR | 5Y TR | SI TR |
|---|---|---|---|---|---|
| Nifty 50 | 3 Nov 1995 | 22 Apr 1996 | -9.45% | 6.70% | 12.15% |
| Nifty 200 | 1 Jan 2004 | 19 Jul 2011 | -7.35% | 8.26% | 13.42% |
| Nifty 500 | 1 Jan 1995 | not shown | -6.83% | 8.81% | 11.83% |
| Nifty Midcap 150 | 1 Apr 2005 | 1 Apr 2016 | -3.90% | 13.84% | 16.47% |
| Nifty Next 50 | 4 Nov 1996 | 24 Dec 1996 | -2.14% | 10.95% | not shown |
| Nifty200 Momentum 30 | 1 Apr 2005 | 25 Aug 2020 | -8.48% | 7.93% | 18.05% |
| Nifty500 Momentum 50 | 1 Apr 2005 | 4 Jun 2024 | -3.00% | 10.71% | 21.12% |
| Nifty Midcap150 Momentum 50 | 1 Apr 2005 | 16 Aug 2022 | -3.40% | 14.33% | 22.01% |
| Nifty Alpha 50 | 31 Dec 2003 | 19 Nov 2012 | +3.66% | 11.56% | 19.98% |
| Nifty200 Alpha 30 | 1 Apr 2005 | 21 Jul 2022 | -1.66% | 13.04% | 17.27% |
| Nifty Alpha Low-Volatility 30 | 1 Apr 2005 | 10 Jul 2017 | -6.07% | 8.98% | 17.58% |
| Nifty500 Multicap Momentum Quality 50 | 1 Apr 2005 | 4 Sep 2024 | -9.01% | 8.59% | 19.85% |

Since-inception figures are not comparable across rows with different base dates; compare the 1-year and 5-year columns, or the same-start figures from the NSE whitepaper below. The factsheet statistics table also gives annualised daily volatility; my reading of the extracted columns is 1-year, since-inception, 5-year, and volatility figures quoted later in this file rely on that reading.

Reading: over the five years to 30 Oct 2026 the flagship Nifty200 Momentum 30 (7.93%) is slightly **behind** its parent Nifty 200 (8.26%), before fund costs. The broader and mid-cap momentum indices are ahead of their parents by 0.5 to 1.9 points a year over the same five years, and the Jensen-alpha indices by 2.8 to 4.8 points. The large since-inception gaps come mostly from 2005 to 2021.

From the NSE whitepaper "The Science of Momentum" (April 2026, data to 27 Feb 2026):
- Since April 2005: Nifty200 Momentum 30 19.19% vs Nifty 200 15.08%; Nifty Midcap150 Momentum 50 23.00% vs Nifty Midcap 150 17.24%; Nifty500 Momentum 50 21.94% vs Nifty 500 18.85%. The 18.85% is what the whitepaper prints in both its summary and its table, but it looks wrong: at every other horizon in the same table the Nifty 500 and Nifty 200 are within 0.5 points of each other (15 years 13.23% vs 12.99%, 10 years 16.04% vs 15.74%). Treat the stated 3-point gap for the Nifty500 Momentum 50 as understated or unreliable.
- Other horizons from the same table (TR, to 27 Feb 2026): 15 years N200M30 18.86% vs 12.99%, Midcap150M50 23.94% vs 17.62%, N500M50 20.76% vs 13.23%; 10 years 20.16% vs 15.74%, 23.38% vs 20.21%, 20.83% vs 16.04%; 5 years 18.15% vs 14.42%, 24.72% vs 20.77%, 20.79% vs 14.88%. Note how much the 5-year comparison changed between February and October 2026 (section 1.2 table): the window dropped the strong 2021 months.
- Maximum drawdown: 67.7% (N200M30), 72.5% (Midcap150M50), 70.2% (N500M50) against 63.7%, 72.9% and 63.7% for the parents. All troughs are in October 2008 to March 2009.
- Calendar years in which the momentum index beat its parent, 2006 to 2025: 15, 14 and 13 out of 20.
- Bad relative years for N200M30: 2009 (-19.47 points vs Nifty 200), 2022 (-10.36), 2025 (-14.13). For N500M50: 2009 (-29.70), 2022 (-11.84), 2025 (-15.37).
- Annual churn (share of index weight replaced, summed over the year's rebalances), semi-annual schedule, FY22 to FY26: N200M30 101%, 112%, 115%, 110%, 134%; Midcap150M50 103%, 90%, 94%, 96%, 93%; N500M50 124%, 131%, 127%, 139%, 145%.
- A quarterly rebalanced version had 20 to 70% more churn and slightly **lower** long-run return for N200M30 (17.12% vs 19.19% since inception) and N500M50 (21.16% vs 21.94%); marginally higher for the mid-cap index (23.26% vs 23.00%).
- 24 passive funds, AUM above ₹17,000 crore, track these three indices (27 Feb 2026).

Business Standard, 14 Dec 2025: the December 2025 review replaced 19 of the 30 Nifty200 Momentum 30 constituents, with estimated round-trip trading of ₹16,130 crore and flows above one day's average volume in 27 stocks.

Value Research, 29 Jan 2025: ₹1 lakh in a Nifty 200 Momentum 30 fund lost about ₹21,000 in the four months after September 2024, against ₹12,600 for the Nifty 200.

### 1.3 Indian momentum factor, IIM Ahmedabad data library (release 2025-12, data October 1993 to December 2025)

Published on the library page: annualised geometric mean since 1 January 1994: market premium 4.93%, SMB -3.71%, HML 6.61%, WML (winners minus losers) 10.65%. WML for calendar 2025: about -5.3% to -5.5%.

The original working paper (Agarwalla, Jacob, Varma 2013) reported an "average annual return of the momentum factor" of 21.9% for January 1994 to December 2014 (legacy series; the revised abstract's wording, and the original version said 21.2%). That is about twice the 10.65% geometric figure the current library shows, so do not use 21.9% as an expectation. The current library excludes micro-caps and penny stocks and covers NSE and BSE.

My own computation from the monthly CSV files (gross, no costs; "WB" is the winner portfolio among big stocks, "WS" among small stocks, as defined by IIMA; market = MF + RF):

| Period | WML geo. ann. | WML vol | WML max DD | Market geo. ann. | WB geo. ann. | WS geo. ann. | WB minus market, mean per month |
|---|---|---|---|---|---|---|---|
| 1994-2025 | 10.5% | 24.5% | -53% | 12.2% | 18.7% | 17.7% | 0.58% |
| 1994-2004 | 6.3% | 32.4% | -53% | 7.6% | 20.9% | 5.4% | 1.12% |
| 2005-2014 | 12.6% | 23.4% | -52% | 15.1% | 17.3% | 26.9% | 0.28% |
| 2015-2025 | 12.8% | 14.5% | -26% | 14.4% | 17.9% | 22.7% | 0.29% |
| 2020-2025 | 8.4% | 15.4% | -26% | 19.9% | 21.4% | 35.9% | 0.16% |

Worst WML months: Nov 2001 -27.6%, May 2009 -25.0% (market +33.8%), Apr 2000 -21.2%, Dec 2008 -20.3%, Apr 2009 -18.3%, Jan 2012 -18.0%, Apr 2020 -13.5% (market +14.2%). In May 2009 the big-stock winners still rose 21.9% while big-stock losers rose 61.0% and small-stock losers 74.6%, so the crash came from the short (loser) leg. A long-only winner portfolio lagged the market in those months but did not lose money.

Reading: large-cap winners have beaten the market by roughly 3 points a year since 2005 before costs, with tracking volatility near 10% a year. The edge since 2020 is smaller (about 2 points a year) and statistically weak.

### 1.4 What a ₹1.5 lakh account can hold (own computation from the Angel One charges above)

Round-trip cost per position (buy plus sell, including DP charge, excluding slippage), capital split equally:

| Positions | Position size | Round trip, ₹ | Round trip, % (DP ₹20) | Round trip, % (DP ₹50, BSDA) |
|---|---|---|---|---|
| 1 (one ETF) | 1,50,000 | 404 | 0.27% | 0.29% |
| 5 | 30,000 | 138 | 0.46% | 0.58% |
| 10 | 15,000 | 92 | 0.62% | 0.85% |
| 15 | 10,000 | 69 | 0.69% | 1.05% |
| 20 | 7,500 | 58 | 0.77% | 1.25% |
| 30 | 5,000 | 47 | 0.93% | 1.64% |

Annual cost drag = one-way turnover x round-trip cost. With DP ₹20: 15 positions at 100% turnover costs 0.69% of capital a year, at 200% 1.39%, at 400% 2.78%. 30 positions at 400% costs 3.7%. Add slippage (BacktestIndia assumes 0.05% per trade for Nifty 200 names; mid and small caps will be worse) and 20% tax on realised short-term gains.

Other small-account constraints:
- Whole shares only. A stock priced above the per-position budget cannot be bought; skip to the next rank. With 20 positions the budget is ₹7,500 per stock, which excludes several high-priced large caps. With 10 positions it is ₹15,000.
- Trimming and topping-up existing positions to restore equal weights costs a minimum ₹5 brokerage per order plus ₹20 to ₹50 DP on every sell. Do not re-weight survivors; only replace names that exit. Zerodha Varsity's author gives the same advice to a reader.
- Evidence on how many names: Capitalmind's test of 5 to 50 stock monthly momentum portfolios (2007 to 2019, no costs) found 5 and 10 stock portfolios did worst and 20 to 30 did best. Its large-cap test (top 100 by market cap, quarterly) found outperformance at every size from 5 to 30 and chose 20. Zerodha Varsity suggests 10 to 12, at most 15, from a universe of 150 to 200.
- Practical compromise at ₹1.5 lakh: 10 to 15 names if rebalanced monthly or quarterly with a buffer, or one momentum ETF. 30 and 50 stock index replicas are not sensible to hold directly at this size.
- No overnight short selling of stocks in the cash market, so every long-short result in the academic literature has to be read through its long leg only.

## 2. Notation used in the rules

- `P[d]`: close on trading day `d`, adjusted for splits, bonuses and rights. `T` is the signal day (a month-end or week-end close). Trades are placed on the next session.
- `MOM(J,S)` at `T` = `P[T - 21*S] / P[T - 21*J] - 1` using 21 trading days per month (or month-end closes). "12-1" is `MOM(12,1)`, "6-1" is `MOM(6,1)`, "12-0" is the plain 12-month return.
- `VOL1Y` = standard deviation of daily log returns over the last 252 trading days x sqrt(252).
- Universe filters that sources leave vague are stated as "our default" and are not from the source.
- Several cards in `research/cards/xs_momentum.json` add "replace a holding only when it ranks beyond 2N" (or a stated exit rank). That exit buffer is our default taken from S24, not from the cited paper, whose portfolios are fully re-formed at each rebalance.

Card ids map to the sections below as follows: S1 `total_return_topn`, S2 `nifty200_momentum30_replica`, S3 `nifty500_momentum50_replica`, S4 `midcap150_momentum50_replica`, S5 `nifty_alpha50_replica`, S6 `nifty200_alpha30_replica`, S7 `momentum_etf_core`, S8 `msci_conditional_rebalance`, S9 `fifty_two_week_high`, S10 `industry_52w_high_band`, S11 `ath_weekly_cash`, S12 `residual_momentum`, S13 `sharpe_ratio_momentum`, S14 `smooth_path_fip`, S15 `clenow_adjusted_slope`, S16 `vol_target_overlay`, S17 `bear_state_overlay`, S18 `index_trend_cash_switch`, S19 `alpha_low_vol30_replica`, S20 `conservative_formula`, S21 `momentum_quality50_replica`, S22 `intermediate_12_7`, S23 `industry_momentum`, S24 `buffered_rank_hold`, S25 `low_scaled_turnover_annual`, S26 `next50_top10_rotation`, S27 `acceleration` (all prefixed `xs_momentum__`).

## 3. Strategies

### S1. Total-return momentum, top-N long-only (12-1, 6-1; Jegadeesh-Titman)

- **Rules (academic).** Universe: all NYSE and AMEX stocks. Each month rank on past J-month return (J = 3, 6, 9 or 12), optionally skipping one week. Buy the top decile, sell the bottom decile, hold K months (K = 3, 6, 9, 12) with overlapping portfolios so that 1/K of the book is replaced each month. Later convention (Carhart, Fama-French, AQR): rank on the return from 12 months ago to 1 month ago ("12-1" or "12_2"), monthly rebalance.
- **Rules (Indian retail versions).**
  - Zerodha Varsity: tracking universe of 150 to 200 stocks (BSE 500 suggested); compute 12-month return with no skip; rank; buy the top 12 (10 to 15) in equal rupee amounts; at each month-end re-rank, sell names no longer in the top 12 and buy the new ones.
  - Capitalmind "naive momentum": on the first trading day of each month rank all sufficiently liquid NSE stocks on 52-week return, buy the top 30 equal weight, rebalance monthly.
- **Code-ready default.** Universe: Nifty 200 or Nifty 500 members with at least 252 days of history and median daily traded value above ₹5 crore (our default). Signal: `MOM(12,1)`; alternative `MOM(6,1)`. At each month-end hold the top N = 15 equal weight. No stop loss. Exit when a name leaves the top N (or the buffer rank in S24).
- **Parameter ranges in sources.** J 3 to 12 months; skip 0, 1 week, 1 month; K 1 to 12 months; N from top 12 (Varsity) through top 30 (Capitalmind) to deciles.
- **Instruments.** NSE cash equities, delivery.
- **Holding period.** 1 to 12 months per name; Capitalmind reports 2 to 3 months typical in live running.
- **Reported performance.**
  - Jegadeesh and Titman (1993), NYSE/AMEX 1965 to 1989: 12-month formation, 3-month holding earns 1.31% a month (1.49% with a one-week skip); 6/6 earns about 1% a month, a compounded excess return of 12.01% a year. Turnover 84.8% semi-annually; after a 0.5% one-way cost the risk-adjusted return is 9.29% a year.
  - Asness, Frazzini, Israel, Moskowitz as summarised by Quantpedia: US UMD gross 8.3% a year 1927 to 2013 (Sharpe 0.50), 8.4% for 1963 to 2013 (0.57), 6.3% for 1991 to 2013 (0.36), i.e. weaker after the original studies.
  - Daniel and Moskowitz: US winner decile excess return 15.3% a year, loser decile -2.5%, market 7.6%, WML Sharpe 0.71, 1927 to 2013, no costs.
- **India evidence.**
  - IIMA factor library: WML 10.65% annualised since 1994; large-cap winner portfolio 18.7% vs market 12.2% (1994 to 2025, my computation, gross).
  - Capitalmind: top-30 monthly 12.6% CAGR vs Nifty 8.9% and Nifty 500 8.7%, January 2007 to 2019, survivorship-free data, no costs, taxes or dividends; outperformed the indices in 6 of 13 calendar years with large shortfalls in 2008 and 2016; 63% up months vs 54% for the index.
  - Joshipura (NSE-funded working paper), NSE monthly data 1995 to 2008: momentum profits at 6 and 12 month horizons, reversal at 3 years, profit mainly from the winner portfolio.
  - Dhankar and Maheshwari, NSE 1997 to 2013: significant short-term momentum and long-term reversal; a companion paper finds no January or April seasonality but notably negative momentum returns in May.
- **Costs and capacity.** Monthly top-N without a buffer turns over several times a year. Capitalmind's live estimate is about 20% of the portfolio changing each month (roughly 240% a year). At 15 positions that is about 1.7% a year in charges at Angel One before slippage and tax.
- **Failure modes.** Sharp market rebounds after bear markets (2009, April 2020); sector reversals (2022, late 2024 to 2025); stocks on upper-circuit streaks entering a weekly or monthly ranking (raised by a Varsity reader); sensitivity to the rebalance date.
- **Feasibility at ₹1.5 lakh.** Yes as a 10 to 15 stock long-only portfolio. The long-short form is not available.
- **Sources.** bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf; zerodha.com/varsity/chapter/momentum-portfolios/; capitalmind.in/insights/momentum-investing-basics-india; quantpedia.com/strategies/momentum-factor-effect-in-stocks; nber.org w20439; faculty.iima.ac.in/~iffm/Indian-Fama-French-Momentum/; nsearchives.nseindia.com/content/research/res_paperfinal223.pdf; publishingindia.com PDFBrochures 2192 and 3029.

### S2. Nifty200 Momentum 30 replica (NSE methodology, September 2026 document)

- **Universe.** Stocks in, or about to enter, the Nifty 200 at review; at least 1 year of listing; available in F&O on the effective date.
- **Signal.** `MR12 = (P[M-1]/P[M-13] - 1) / VOL1Y` and `MR6 = (P[M-1]/P[M-7] - 1) / VOL1Y`, where M is the rebalance month and prices are the last trading day of months M-1, M-7, M-13. `Z12`, `Z6` = cross-sectional z-scores of MR12 and MR6 over the eligible universe. `WZ = 0.5*Z12 + 0.5*Z6`. Normalized Momentum Score `NMS = 1 + WZ` if `WZ >= 0`, else `1/(1 - WZ)`.
- **Selection and buffer.** Top 30 by NMS. At a review, stocks ranked in the top 15 are always included; existing constituents are dropped only if their rank falls beyond 45; stocks leaving the Nifty 200 are dropped.
- **Weights.** Free-float market cap x NMS, each stock capped at the lower of 5% or 5 times its free-float weight in the index.
- **Rebalance.** Semi-annual, June and December, on data to the last trading day of May and November. Changes take effect near month-end (the December 2025 change was effective at the close on 30 December), so there is roughly a one-month gap between the data cut-off and trading.
- **Instruments / holding period.** Nifty 200 F&O stocks; 6 months or more per name.
- **Reported performance.** See section 1.2. Since April 2005 to Feb 2026: 19.19% TR vs 15.08%; max drawdown 67.7%; since-inception Sharpe about 0.50 (my reading of the whitepaper table). Five years to 30 Oct 2026: 7.93% vs 8.26% for the Nifty 200. Index launched 25 August 2020; earlier history is back-calculated.
- **India evidence.** This is Indian evidence. BacktestIndia's independent reconstruction ("Base Momentum 30": top 30 of the top 200 by 12-month return, positive PE, equal weight, annual December rebalance, Dec 2006 to 2025) gives 15.31% gross, 14.60% net CAGR against 10.41% for the Nifty 50, max drawdown -70.6%.
- **Costs and capacity.** Churn 100 to 134% of weight a year. Capacity is an institutional problem (₹12,500 crore tracks it; 19 of 30 names changed in December 2025), not a retail one. A private replica can trade on a different day from the index funds.
- **Failure modes.** As S1, plus slow reaction: a semi-annual schedule held the pre-September-2024 leaders through the following fall.
- **Feasibility at ₹1.5 lakh.** No for a faithful 30 stock tilt-weighted replica (₹5,000 average position, 0.9 to 1.6% round trip, whole-share rounding). Marginal as an equal-weight top-15 variant. Yes through an ETF (S7).
- **Sources.** niftyindices.com Method_NIFTY_Equity_Indices.pdf (section 17); Factsheet_Nifty200_Momentum30.pdf; momentum-strategy-whitepaper_2026.pdf; nifty200_momentum_30_index_whitepaper_sep_20.pdf; business-standard.com (14 Dec 2025); backtestindia.com.

### S3. Nifty500 Momentum 50 replica

- **Universe.** Nifty 500 members with 1 year of listing. Excluded: non-F&O stocks that hit the upper or lower circuit on 20% or more of trading days in the past 6 months (both circuits on one day count as two instances); companies with promoter pledge above 20%; the bottom 10% of the universe by 6-month average daily turnover; the bottom 10% by turnover ratio (6-month average daily turnover divided by 6-month average free-float market cap).
- **Signal.** Same NMS as S2.
- **Selection and buffer.** Top 50 by NMS. Existing constituents ranked within the top 75 stay; non-members ranked in the top 25 are added, replacing the lowest-scoring constituents; constituents ranked beyond 75 are removed.
- **Weights / rebalance.** Free-float market cap x NMS, cap lower of 5% or 5x free-float weight; semi-annual June and December on May and November data, four weeks' notice.
- **Reported performance.** Since April 2005 to 30 Oct 2026: 21.12% TR; five years 10.71% vs 8.81% for the Nifty 500; 2025 calendar year -7.61% (-15.37 points vs Nifty 500); max drawdown 70.2%. Launched 4 June 2024.
- **Costs and capacity.** Churn 124 to 145% a year. Mid and small-cap members have wider spreads.
- **Feasibility at ₹1.5 lakh.** No directly (50 names). Yes through an ETF or index fund (Motilal Oswal and Groww ETFs exist per the NSE whitepaper).
- **Sources.** Method_NIFTY_Equity_Indices.pdf (section 22); FactsheetNifty500Momentum50.pdf; whitepaper 2026.

### S4. Nifty Midcap150 Momentum 50 replica

- **Universe.** Nifty Midcap 150 members, 1 year listing, excluding non-F&O stocks that hit a circuit on 20% or more of trading days in the past 6 months.
- **Signal, weights.** As S2 and S3.
- **Selection and buffer.** Top 50 by NMS; constituents ranked within 75 stay; non-members in the top 25 enter; beyond 75 exit. Semi-annual June and December.
- **Reported performance.** Since April 2005 to 30 Oct 2026: 22.01% TR vs 16.47% for the Nifty Midcap 150; five years 14.33% vs 13.84%; max drawdown 72.5%; since-inception Sharpe about 0.71 (my reading). Launched 16 August 2022.
- **Note.** The index holds one third of its parent, so it is a mild tilt. Churn 90 to 103% a year.
- **Feasibility at ₹1.5 lakh.** No directly. Yes through index funds; one ETF (Motilal Oswal, ₹27 crore AUM in Feb 2026) is small.
- **Sources.** Method_NIFTY_Equity_Indices.pdf (section 18); Factsheet_NiftyMidcap150Momentum50.pdf; nifty-midcap150-momentum-50-whitepaper_2023.pdf; whitepaper 2026.

### S5. Nifty Alpha 50 replica (Jensen's alpha ranking, quarterly)

- **Universe.** NSE stocks ranking in the top 300 by both average free-float market cap and average daily turnover over the last six months; 1 year listing; 100% trading frequency over the last year.
- **Signal.** Jensen's alpha from 1-year trailing daily prices. NSE's formula (stated in the multi-factor section of the methodology): `alpha = rs - [rf + beta*(rm - rf)]` with `rs` the average daily stock return over the previous 12 months, `rm` the average daily Nifty 50 return, `rf` the average daily 3-month MIBOR rate, and `beta` estimated over the same 12 months.
- **Selection and buffer.** Top 50 by alpha; negative-alpha stocks are not selected. A 100% buffer: an existing constituent is retained if it ranks within the top 100.
- **Weights.** Proportional to alpha (highest alpha gets the highest weight).
- **Rebalance.** Quarterly, on data to the last trading day of February, May, August, November; effective the first working day after F&O expiry of March, June, September, December; weights set on closing prices 5 working days before.
- **Reported performance.** Since 31 Dec 2003 to 30 Oct 2026: 19.98% TR; five years 11.56% (Nifty 500: 8.81%); one year +3.66% when the Nifty 50 was -9.45%. Launched 19 November 2012. Annualised volatility since inception about 24.7% against 22.4% for the Nifty 50 (factsheet).
- **Costs and capacity.** No published churn figure found. Alpha weighting concentrates in volatile small and mid caps: the top holding on 30 Oct 2026 was 7.88% in one small cap.
- **Failure modes.** High beta to speculative phases; alpha weighting has no free-float anchor; quarterly turnover.
- **Feasibility at ₹1.5 lakh.** No directly (50 names). Marginal as a top-10 to 15 equal-weight variant. An ETF exists (ticker not verified in this session).
- **Sources.** Method_Nifty_Alpha_50.pdf; Method_NIFTY_Equity_Indices.pdf (sections 11 and 29); Factsheet_Nifty_Alpha50.pdf.

### S6. Nifty200 Alpha 30 replica

- **Universe.** Nifty 200 members, 1 year listing, available in F&O.
- **Signal.** Jensen's alpha on 1-year trailing prices; only positive-alpha stocks are eligible.
- **Selection and buffer.** Top 30 by alpha. Constituents ranked beyond 45 are removed; non-members ranked in the top 15 are added, replacing the lowest-alpha constituents. If fewer than 30 are eligible the gap is filled from existing constituents with the least negative alpha.
- **Weights.** Alpha score = `1 + Z` if `Z > 0` else `1/(1 - Z)` where Z is the z-score of alpha; cap at the lower of 5% or 5x free-float weight.
- **Rebalance.** Quarterly (March, June, September, December) on data to end February, May, August, November.
- **Reported performance.** Since April 2005 to 30 Oct 2026: 17.27% TR; five years 13.04% vs 8.26% for the Nifty 200; one year -1.66% vs -7.35%. Launched 21 July 2022.
- **Feasibility at ₹1.5 lakh.** Marginal directly (30 liquid names; 15 equal-weight is workable). 
- **Sources.** Method_NIFTY_Equity_Indices.pdf (section 15); Factsheet_Nifty200Alpha30.pdf; ind_nifty_200.pdf.

### S7. Momentum index ETF as the whole position (buy and hold, optional top-ups)

- **Rules.** Buy one ETF tracking the Nifty200 Momentum 30 (or Nifty500 Momentum 50) with the full allocation; reinvest; no stock selection. Optional: monthly additions. A timing overlay is S19.
- **Instruments.** Per the NSE whitepaper (27 Feb 2026) Nifty200 Momentum 30 ETFs are run by ICICI Prudential (₹583 crore), Motilal Oswal (₹125 crore), HDFC (₹96 crore), Aditya Birla Sun Life (₹44 crore) and Kotak (₹6 crore), with one-year tracking errors of roughly 0.2 to 0.5%; Nifty500 Momentum 50 ETFs by Motilal Oswal (₹276 crore) and Groww (₹22 crore); a Nifty Midcap150 Momentum 50 ETF by Motilal Oswal (₹27 crore). Tickertape shows MOM30IETF (ICICI) at ₹30.74 with "high liquidity" and MOMOMENTUM (Motilal) at ₹61.04 with "medium liquidity" on 2026-11-10. Other tickers and all expense ratios: (unverified: snippet only; search snippets disagreed, 0.2% to 1.1%).
- **Holding period.** Years.
- **Reported performance.** The index figures in section 1.2 less expense ratio and tracking error.
- **Costs.** About 0.27% round trip on ₹1.5 lakh once; no STCG until sold; the fund pays no capital gains tax on its internal rebalancing.
- **Failure modes.** All of S2's, plus index funds trading the same names on the same day (December 2025: flows above a day's volume in 27 of 30 stocks), plus thin ETF order books for the smaller funds.
- **Feasibility at ₹1.5 lakh.** Yes. This is the cheapest way to hold a 30 or 50 stock momentum portfolio at this size.
- **Sources.** momentum-strategy-whitepaper_2026.pdf; tickertape.in ETF pages; valueresearchonline.com; business-standard.com.

### S8. MSCI-style risk-adjusted momentum with conditional (volatility-triggered) rebalancing

- **Signal.** `M6 = P[T-1m]/P[T-7m] - 1 - rf`, `M12 = P[T-1m]/P[T-13m] - 1 - rf` (most recent month excluded). Risk-adjusted value = M / sigma, sigma = annualised standard deviation of weekly returns over 3 years. Z-score each horizon, `C = 0.5*Z6 + 0.5*Z12`, standardise C again to Z and winsorise at +/-3. Score = `1 + Z` if `Z > 0` else `1/(1 - Z)`. If the 12-month value is missing use the 6-month only.
- **Selection and buffer.** Fixed number of names by unwinsorised Z. Buffer at 50% of the target count: for a 500 stock index, ranks up to 250 are added first, then existing constituents ranked 251 to 750, then the best remaining.
- **Weights.** Score x parent market-cap weight, normalised, with an issuer cap.
- **Rebalance.** Semi-annual (end May, end November). **Conditional rebalance:** each month compute `V = sqrt(250) * stdev(daily parent-index returns over the trailing 3 months)`; if `V_t / V_(t-1) - 1` exceeds the 95th percentile of its own history, rebalance that month and rank on the 6-month value only.
- **Reported performance.** None taken from this document; it is a methodology. Use: a published, precise rule for speeding up the portfolio when market volatility jumps, which is when 12-month winners are most at risk.
- **India evidence.** None found. The NSE indices have no such trigger.
- **Feasibility at ₹1.5 lakh.** Yes as an overlay on a 10 to 15 stock portfolio (it only adds an occasional extra rebalance).
- **Sources.** msci.com MSCI_Momentum_Indexes_Methodology_June2017.pdf.

### S9. 52-week-high momentum (George and Hwang)

- **Rules.** At each month-end compute `PTH = P[T] / max(P over the past 12 months)`. Rank the universe. Long the 30% of stocks with the highest ratio, short the 30% with the lowest, equal weight, hold 6 months with overlapping monthly cohorts (the paper skips a month between ranking and holding in its regressions).
- **Retail default.** Long only: top N = 15 by PTH within a liquid universe, monthly, ties broken by `MOM(12,1)`, holdings replaced only when they fall out of the top 2N (tie-break and exit buffer are our defaults).
- **Reported performance.** US, CRSP, July 1963 to December 2001, (6,6) strategies: winner minus loser 0.45% a month for the 52-week-high strategy against 0.48% for Jegadeesh-Titman and 0.45% for industry momentum; excluding January 1.23% vs 1.07% and 0.50%. In pairwise tests the 52-week-high measure dominates: 0.65% a month vs 0.38% for JT in raw returns, 0.86% vs 0.38% risk-adjusted. Returns do not reverse in the long run.
- **India evidence.** Raju (SSRN 4587697, 2023): data October 2004 to August 2023; the document description states stocks near the 52-week high had higher returns and risk-adjusted returns than momentum, more stable alpha and weaker long-term reversal (unverified: snippet only; SSRN blocked, only the Scribd description opened). A 2006 to 2010 student study of 25 high and 25 low stocks was mixed (unverified: snippet only).
- **Costs and capacity.** PTH is bounded at 1, so many stocks tie near the top in strong markets and ranks change little from month to month; turnover should be lower than S1 (not measured in a source I opened).
- **Failure modes.** In a broad rally almost everything is near its high and the signal stops discriminating; a low-volatility bias (stable stocks sit near highs); Quantpedia notes weak out-of-sample results for the related industry version.
- **Feasibility at ₹1.5 lakh.** Yes, long only, 10 to 15 names.
- **Sources.** bauer.uh.edu/tgeorge/papers/gh4-paper.pdf; scribd.com/document/694152012 (description only).

### S10. Industry 52-week-high rotation (Hong, Jordan, Liu) and the Indian band test

- **Rules (paper, via Quantpedia).** For each stock `PRILAG = P[T] / 52-week high`. For each of 20 industries take the market-cap weighted average PRILAG. Long the stocks in the 6 industries with the highest average, short those in the 6 lowest, equal weight, hold 3 months, one third rebalanced monthly.
- **Indian test (QuantInsti, Milind Paradkar).** Long only. At the start of each month buy, equal weight, every stock whose price is between 90% and 95% of its 52-week high, excluding stocks that made the 52-week high within the past 30 days; exit at the start of the next month.
- **Reported performance.** Paper: 0.93% a month for the value-weighted small-stock long-short version, about 11.75% a year, 1963 to 2009 (Quantpedia). Quantpedia flags that its own out-of-sample backtest is slightly negative.
- **India evidence.** QuantInsti test 2014 to 2017: about 17% total over three years, Sharpe about 0.4, described by Quantpedia as "not very stellar".
- **Feasibility at ₹1.5 lakh.** Marginal: the band rule gives an uncontrolled number of names; the industry version can be run with sector index ETFs where they exist, otherwise it needs many stocks.
- **Sources.** quantpedia.com/strategies/52-weeks-high-effect-in-stocks; quantpedia.com/an-analysis-of-52-weeks-high-effect-on-indian-stocks/; quantinsti.com/blog/trading-strategy-52-weeks-high-effect-in-stocks/.

### S11. All-time-high momentum, weekly, with cash when nothing qualifies (WeekendInvesting "Mi ST ATH" type)

- **Rules as published.** Up to 10 stocks, equal weight. Universe: NSE stocks with market cap of ₹1,000 crore or more and "very high turnover". Selection by a momentum ranking and nearness to the all-time high. Reviewed every week; stocks that fail the exit criterion are removed and new ones enter. When no new picks qualify the slot sits in cash (LIQUIDBEES). No discretion. The ranking formula, the turnover cut-off and the exit threshold are **not disclosed**.
- **Testable parameterisation (ours, not the manager's).** Universe: market cap >= ₹1,000 crore and 6-month median traded value in the top third. Candidate if `P[T] >= 0.95 * all-time high`. Rank candidates by `MOM(6,0)`. Hold the top 10. Weekly: exit a holding if `P[T] < 0.85 * all-time high` or it falls out of the top 30 candidates; fill empty slots from candidates, otherwise hold LIQUIDBEES.
- **Reported performance.** Not visible without a subscription. StockViz runs a similar "All Star" all-time-high portfolio and notes that naive monthly momentum in India has had 50%+ drawdowns every 3 to 4 years.
- **Costs and capacity.** Weekly review with 10 names at ₹15,000 each: 0.62 to 0.85% per round trip; turnover unknown. The smallcase minimum was about ₹1.04 lakh and the manager's stated optimal size is ₹5 to 30 lakh.
- **Failure modes.** Whipsaw at the all-time-high line; small-cap gaps; subscription rules can change.
- **Feasibility at ₹1.5 lakh.** Marginal: feasible in rupee terms, but the published rule set is incomplete and weekly turnover is costly.
- **Sources.** smallcase.com/smallcase/WKIMO_0007; freefloat.substack.com/p/the-momentum-factor; stockviz.substack.com/p/momentum-without-the-crash.

### S12. Residual (idiosyncratic) momentum (Blitz, Huij, Martens)

- **Rules.** Each month, for every stock with a full 36-month history, regress monthly excess returns over months t-36 to t-1 on the Fama-French market, size and value factors. Take the residuals for months t-12 to t-2, sum them and divide by their standard deviation over the same months. Long the top decile, short the bottom decile, equal weight, monthly (the paper also tests 3, 6 and 12 month holding).
- **India adaptation.** Factors from the IIMA library (market, SMB, HML monthly returns) or, with daily data only, a one-factor market model against the Nifty 500. Long only top N.
- **Reported performance.** US 1926 to 2009, one-month holding, gross: residual momentum 11.2% a year, volatility 12.5%, Sharpe 0.90, against 10.3%, 22.7% and 0.45 for total-return momentum. Large caps only (top 10% by size): Sharpe 0.60 vs 0.36. January 2000 to December 2009: total-return momentum -8.5% a year, residual momentum +4.7%. Without standardising: 11.88%, 13.28% volatility, Sharpe 0.89.
- **India evidence.** None found in an opened source.
- **Costs and capacity.** The paper argues costs bite less because the portfolio is less concentrated in small, volatile stocks; it gives no net figure.
- **Failure modes.** Needs 36 months of history, which removes recent listings; beta estimates are noisy; the benefit is mostly lower risk of the long-short spread, which a long-only holder captures only in part.
- **Feasibility at ₹1.5 lakh.** Yes, long only, 10 to 15 names; computation is light.
- **Sources.** repub.eur.nl/pub/22252/ResidualMomentum-2011.pdf; cxoadvisory.com (stripping-risks-from-a-stock-momentum-strategy); quantpedia.com/strategies/residual-momentum-factor.

### S13. Volatility-adjusted ("Sharpe") momentum, top-N

- **Rules (Capitalmind).** Score = 52-week excess return divided by the annualised standard deviation of daily price changes. Monthly version: first trading day of each month, top 30 equal weight from all liquid NSE stocks. Large-cap version: universe = top 100 NSE stocks by market cap (refreshed yearly), rank by Sharpe ratio at each calendar quarter-end, hold the top 20, go to cash for slots when too few stocks qualify.
- **Code-ready default.** `SCORE = (MOM(12,0) - rf) / VOL1Y`; top 15; quarterly at March, June, September, December ends.
- **Reported performance.** Monthly top 30, January 2007 to 2019, no costs: 16.8% CAGR against 14.7% for gain-loss momentum, 12.6% for plain 12-month return, 8.9% Nifty. Large-cap quarterly: positive alpha vs the Nifty 50 in 9 of 15 years and 57% of months; drawdown in 2008 of 52.83% against 59.86% for the Nifty 50 and 72.49% for the Next 50; quarterly beat monthly rebalancing on return and drawdown.
- **Cautions from the same source.** Results with non-calendar quarter-ends were worse on both return and drawdown (rebalance-date luck). From 2005 to 2015 the large-cap momentum portfolio was far ahead of a 50:50 Nifty 50 plus Next 50 mix, but "since then, both of them have provided more or less similar returns" (written August 2019).
- **Related.** This is the single-horizon cousin of the NSE score (S2) and the MSCI score (S8). A ValuePickr user reports a gross 38% CAGR, 2018 to February 2026, for (weighted 3/6/12-month return)/volatility on Nifty MidSmallcap 400 plus Next 50 with a gold switch, with no costs or taxes; a replying user says a similar strategy gave 54% over the last 10 years but only 12% over 20 years after taxes, brokerage and slippage. Both are anecdotes.
- **Feasibility at ₹1.5 lakh.** Yes: 10 to 15 large caps, quarterly.
- **Sources.** capitalmind.in/insights/momentum-investing-basics-india; premium.capitalmind.in/2019/08/momentum-how-does-it-look-in-large-cap-stocks/; forum.valuepickr.com thread 218153.

### S14. Momentum quality: gain-loss and "frog in the pan" screens

- **Rules (Capitalmind gain-loss).** Score = (percentage of up days in the last 252 trading days) x (252-day return). Top 30, monthly.
- **Rules (Alpha Architect Quantitative Momentum).** Universe: largest 1,500 liquid US stocks, minus red-flag outliers. Step 1: top 100 by 12-month return ignoring the last month. Step 2: among those, keep the 50 with the smoothest path, measured by `ID = sign(PRET) * (%negative days - %positive days)` over the formation window (Da, Gurun, Warachka); lower ID is better. Equal weight, 20% industry cap, rebalanced quarterly near the start of quarter-ending months.
- **Code-ready default for India.** Universe Nifty 500. Take the top 60 by `MOM(12,1)`; keep the 15 with the lowest ID; quarterly.
- **Reported performance.** Capitalmind, 2007 to 2019, no costs: gain-loss 14.7% CAGR vs 12.6% for plain momentum. Alpha Architect's paper cites a seasonality study in which momentum earned 59 bps in non-quarter-ending months and 310 bps in quarter-ending months (opened). Its QMOM fund factsheet is said to show turnover of about 125% a year (unverified: snippet only).
- **India evidence.** Capitalmind only.
- **Feasibility at ₹1.5 lakh.** Yes, 10 to 15 names.
- **Sources.** capitalmind.in/insights/momentum-investing-basics-india; alphaarchitect.com The_Quantitative_Momentum_Investing_Philosophy.pdf; tradingqna.com thread 154146.

### S15. Clenow "Stocks on the Move" (regression slope x R-squared, volatility-sized, index trend filter)

- **Rules (as summarised by TuringTrader, which says it matches the book closely).** Universe: S&P 500 members. Rank by the annualised slope of a 90-day regression of log price on time, multiplied by the R-squared of that regression. Disqualify stocks below their 100-day moving average and stocks with any single-day move above 15% in the past 90 days. Open new positions only when the index is above its 200-day moving average. Position size is fixed-fractional on the 20-day average true range. Rebalance weekly (Wednesdays); the book adjusts sizes every second week. Typically 10 to 30 holdings.
- **India adaptation.** Universe Nifty 200 or 500; index filter on the Nifty 500; shares = (risk fraction x equity) / ATR20, capped by cash; sell when a stock leaves the top 20% of the ranking, falls below its 100-day average or leaves the universe (the exit ranks are from general descriptions of the book, not verified in a source I opened).
- **Reported performance.** The book's 1994 to 2015 US tests were not opened. No Indian test found.
- **Costs and capacity.** Weekly review is the most expensive schedule here for a small account.
- **Failure modes.** Parameter-heavy; filter whipsaw around the 200-day line; ATR sizing produces odd lots that whole-share rounding distorts at ₹1.5 lakh.
- **Feasibility at ₹1.5 lakh.** Marginal: workable with about 10 positions and a fortnightly cycle, but costs need checking in backtest.
- **Sources.** turingtrader-com.web.app/portfolios/clenow-stocks-on-the-move; quant-investing.com (exponential regression article).

### S16. Constant-volatility scaling of momentum exposure (Barroso and Santa-Clara)

- **Rules (paper, via summaries).** Estimate the momentum portfolio's own realised volatility from its recent daily returns (prior six months in the paper; (unverified: snippet only) for the window) and scale exposure by `target / realised`, with a 12% annual target.
- **Long-only retail form.** Each month compute the realised volatility of the momentum portfolio's daily returns over the last 126 trading days; invest fraction `w = min(1, target / realised)` in the stock portfolio and the rest in a liquid fund ETF. Target is a parameter (12% in the paper for a long-short book; a long-only Indian portfolio runs near 20 to 25%, so a target of 15 to 18% is a sensible starting range; that range is ours). To avoid small costly adjustments the card changes the fraction only when it moves by more than 10 percentage points (also ours).
- **Reported performance.** Barroso and Santa-Clara: managing this risk "virtually eliminates crashes and nearly doubles the Sharpe ratio" (quoted by Quantpedia and Alpha Architect). Dierkes and Krupski: worst month of unmanaged US momentum about -77%, about -28% with constant volatility scaling.
- **India evidence.** Singh, Walia, Panda and Gupta (FIIB Business Review 2022), 450 BSE stocks: a risk-managed approach "doubles the adjusted Sharpe ratio" and improves downside risk (abstract). My computation on the IIMA long-short WML factor, June 1994 to December 2025, 12% target, 126-day window, gross: ratio of mean to volatility 0.56 unscaled, 0.89 scaled, 0.83 with weight capped at 1; worst month -27.6% unscaled, -13.2% scaled; max drawdown -53% vs -28%. For 2015 to 2025 the gain is small (0.91 to 1.06).
- **Caveats.** Bianchi, De Polis and Petrella argue volatility scaling understates risk when returns are skewed (unverified: snippet only). The published evidence is for long-short momentum; for long-only the scaling mostly responds to market volatility.
- **Feasibility at ₹1.5 lakh.** Yes: one extra order pair per month in a liquid ETF.
- **Sources.** alphaarchitect.com/avoiding-momentum-crashes/; quantpedia.com/strategies/momentum-factor-effect-in-stocks; ideas.repec.org/a/sae/fbbsrw/v11y2022i3p347-358.html; IIMA data library.

### S17. Bear-state and rebound overlay (Daniel and Moskowitz; Dierkes and Krupski)

- **Rules (papers).** Bear indicator `IB = 1` if the cumulative market return over the past 24 months is negative. Market variance = variance of daily market returns over the preceding 126 days. Momentum's expected return is lower, and its crash risk higher, when IB = 1 and variance is high; crashes coincide with market rebounds. The dynamic strategy weights WML by forecast mean over forecast variance. Dierkes-Krupski crash indicator: rebound = bear state and a positive one-month market return; crash indicator = rebound and negative momentum beta.
- **Long-only retail form (ours).** If IB = 1 and the last month's index return is positive, replace the momentum stock portfolio with the broad index ETF (or halve it) until IB = 0; otherwise run the momentum portfolio.
- **Reported performance.** Daniel and Moskowitz: the dynamic strategy roughly doubles the alpha and Sharpe ratio of static US momentum and reaches Sharpe 1.18 across markets and asset classes. Dierkes and Krupski (via Alpha Architect): average return -3.63% in indicated crash months vs +1.49% otherwise; Sharpe 1.12 for the crash-indicator strategy vs 0.94 constant-volatility and 1.03 dynamic.
- **India evidence.** My computation on the IIMA WML factor, December 1995 to December 2025: mean 1.40% a month when the prior 24-month market return was non-negative (267 months), 0.75% in bear states (94 months); within bear states, -3.09% a month when the market rose that month (50 months) and +5.11% when it fell (44 months). The split on same-month market direction is not tradable in advance; it shows the mechanism.
- **Important limit.** Daniel and Moskowitz find that most of the up-versus-down beta asymmetry in bear markets "is driven by the past losers"; Alpha Architect's summary draws the conclusion that long-only momentum is not subject to such deep crashes. The Indian data agree: in April and May 2009 large-cap winners rose 10.6% and 21.9%. For a long-only account this overlay addresses relative underperformance in rebounds, not absolute loss.
- **Feasibility at ₹1.5 lakh.** Yes: a rare switch between a stock basket and an index ETF.
- **Sources.** nber.org/system/files/working_papers/w20439/w20439.pdf; alphaarchitect.com/avoiding-momentum-crashes/; IIMA data library.

### S18. Momentum with a market trend or regime filter, switching to cash or gold

- **Rules seen in sources.**
  - Clenow: no new buys while the index is below its 200-day average.
  - WeekendInvesting Mi 25: up to 25 small-cap momentum stocks, "designed to either remain invested in the strongest 25 stocks or go to cash in weak markets" (absolute momentum; exact rule not disclosed).
  - Capitalmind Adaptive Momentum: top-decile composite momentum score, weekly review with a minimum one-month hold, "quantitative filters that shift the portfolio partially or fully out of equities into alternate assets or cash when markets weaken" (not disclosed).
  - ValuePickr user: exit all equity into GOLDBEES when the Nifty 50 breaks its weekly Supertrend.
  - Momentumlab: hold NIFTYBEES only while it is above its 200-day EMA.
- **Code-ready default.** Run S1 or S13. Each week, if Nifty 500 close < its 200-day simple average, make no new buys and move the proceeds of exits to LIQUIDBEES; variant B sells everything; variant C requires each stock to be above its own 200-day average.
- **Reported performance.**
  - Mi 25 (manager's blog, April 2016 to January 2023): +506% vs +134% for the Nifty Smallcap 250, CAGR 30.2%, fall of 29% vs 55% in 2018 to 2020.
  - Capitalmind Adaptive Momentum PMS, live since 5 March 2019, net of fees, page updated 2026-11-06 (return window end-date not stated): 1Y 6.6% vs -0.8% for Nifty 50 TRI; 2Y -5.9% vs 2.3%; 3Y 7.9% vs 10.1%; 4Y 9.1% vs 9.6%; 5Y 7.0% vs 8.3%; 6Y 15.9% vs 13.9%; 7Y 17.8% vs 12.4%.
  - Momentumlab NIFTYBEES test, 10 years to 2024: the filtered version ended lower (NAV about 250 vs about 300) with max drawdown -20.19% vs -36.34%.
- **India evidence.** All of the above is Indian. Capitalmind's live record is the most informative: ahead since inception, behind the Nifty 50 TRI over the last 2 to 5 years even with a cash rule.
- **Failure modes.** Whipsaw; being in cash through V-shaped recoveries (April 2020); extra round trips and STCG.
- **Feasibility at ₹1.5 lakh.** Yes.
- **Sources.** smallcase.com/blog/mi-25-our-flagship-smallcap-strategy/; capitalmind.in/portfolio-management-service/momentum; premium.capitalmind.in/introduction-to-capitalmind-momentum-model/; forum.valuepickr.com thread 218153; momentumlab.substack.com; turingtrader page.

### S19. Nifty Alpha Low-Volatility 30 replica (momentum plus low volatility, NSE)

- **Universe.** Nifty 100 and Nifty Midcap 50 members.
- **Signal.** Alpha Z-score from Jensen's alpha (formula in S5, Nifty 50 as market, 1 year of daily data). Low-volatility Z-score from the inverse of the standard deviation of daily returns over 1 year. Each Z is converted to a factor score (`1 + Z` if positive, else `1/(1 - Z)`) and then to a percentile. Average percentile = 50% alpha + 50% low volatility.
- **Selection and buffer.** Top 30 by average percentile. The top 10 are always included; an existing constituent is removed if its rank drops below 50.
- **Weights.** Based on the weighted-average factor Z-score, capped at the lower of 5% or 5x free-float weight. Semi-annual, June and December.
- **Reported performance.** Since April 2005 to 30 Oct 2026: 17.58% TR; five years 8.98%; one year -6.07%. Volatility since inception about 17.2% against 22.4% for the Nifty 50 (factsheet). Launched 10 July 2017.
- **Feasibility at ₹1.5 lakh.** Marginal directly (30 large and mid caps; 15 equal weight is workable). An ETF exists (ticker not verified).
- **Sources.** Method_NIFTY_Equity_Indices.pdf (multi-factor section); Factsheet_Nifty_Alpha_Low-Volatility_30.pdf.

### S20. Conservative formula (Blitz and van Vliet): low volatility, then momentum plus payout yield

- **Rules.** Universe: the 1,000 largest stocks. Split into two halves on 36-month return volatility; keep the 500 least volatile. Rank those on `MOM(12,1)` and on net payout yield (dividends plus buybacks minus issuance); average the two ranks; hold the best 100 equal weight; rebalance quarterly.
- **India adaptation.** Universe Nifty 500: keep the 250 least volatile, rank on `MOM(12,1)` and dividend yield (or momentum only if no fundamentals), hold the top 15 to 20, quarterly.
- **Reported performance.** US: 15.1% compounded a year since 1929; conservative minus speculative spread about 13% a year; positive in every decade; also strong in Europe, Japan and emerging markets (abstract and Alpha Architect summary).
- **India evidence.** Raju and Teli, "The Conservative Formula: Evidence from India" (SSRN 4163613, 2022): the formula gives exposure to low volatility and momentum in India without accounting data (unverified: snippet only; SSRN blocked).
- **Feasibility at ₹1.5 lakh.** Marginal: needs payout or dividend data; 15 to 20 names quarterly is affordable.
- **Sources.** alphaarchitect.com/the-conservative-formula-quantitative-investing-made-easy/.

### S21. Momentum plus quality (Nifty500 Multicap Momentum Quality 50)

- **Universe.** Nifty 500, split into large (Nifty 100), mid (Midcap 150) and small (Smallcap 250) segments, with the S3 exclusions applied within each segment.
- **Signal.** Percentile of NMS (S2) and percentile of a quality score built from ROE, debt to equity (not for financials) and 5-year EPS growth variability. Aggregate = 50% momentum percentile + 50% quality percentile.
- **Selection and buffer.** Top 10 large, 15 mid, 25 small. Constituents stay if ranked within 15, 23 and 38 in their segment; non-members ranked in the top 5, 8 and 13 enter.
- **Weights.** Free-float market cap x (50% NMS + 50% quality score), 5% cap. Semi-annual.
- **Reported performance.** Since April 2005 to 30 Oct 2026: 19.85% TR; five years 8.59% (Nifty 500: 8.81%); one year -9.01%. Launched 4 September 2024.
- **Feasibility at ₹1.5 lakh.** No directly (50 names, half small caps, fundamentals needed).
- **Sources.** Method_NIFTY_Equity_Indices.pdf (section 31); Factsheet_Nifty500MulticapMQ50.pdf.

### S22. Intermediate-horizon momentum, 12-7 ("echo", Novy-Marx)

- **Rules.** Rank on the return from 12 months ago to 7 months ago, `P[T-126]/P[T-252] - 1`, instead of the recent 6 months; otherwise as S1.
- **Reported performance.** Novy-Marx (2012) finds US momentum is driven mainly by months 12 to 7 (unverified: snippet only).
- **Negative evidence.** Goyal and Wahal, "Is Momentum an Echo?": in 36 non-US markets, 1991 to 2009, intermediate momentum does not generally beat recent momentum; where spreads are large, recent momentum matters more (CXO Advisory summary). Alpha Architect found 12_2 and 12_7 "very similar" for long-only use.
- **India evidence.** None found.
- **Feasibility at ₹1.5 lakh.** Yes, but there is no reason to prefer it; include as a robustness variant only.
- **Sources.** cxoadvisory.com/momentum-investing/momentum-echo-outside-the-u-s; alphaarchitect.com/when-academics-disagree-on-momentum-investing/.

### S23. Industry (sector) momentum (Moskowitz and Grinblatt)

- **Rules (as restated by George and Hwang).** Each month rank industries on their value-weighted return over the past 6 months. Long the stocks in the top 30% of industries, short the bottom 30%, hold 6 months.
- **India adaptation.** Rank NSE sector indices on `MOM(6,0)`; hold the top 3 through sector ETFs where liquid, or the 3 to 4 largest stocks of each chosen sector; monthly.
- **Reported performance.** US 1963 to 2001: 0.45% a month winner minus loser; 0.50% excluding January; dominated by the 52-week-high measure in pairwise tests (0.25% vs 0.65%).
- **India evidence.** None opened (a planned search did not run).
- **Feasibility at ₹1.5 lakh.** Marginal: few liquid sector ETFs; with stocks it becomes a concentrated 9 to 12 name portfolio.
- **Sources.** bauer.uh.edu/tgeorge/papers/gh4-paper.pdf.

### S24. Buffered-rank holding (hysteresis, minimum hold, slower schedule) as a turnover control

- **Rules.** Applies to any ranking above. Enter when rank <= N_in. Exit only when rank > N_out, with N_out well above N_in. Optionally require a minimum holding time before a name can be replaced. Optionally review often but trade rarely. Do not re-weight survivors.
- **Values in sources.** NSE: 30 names, compulsory entry at rank 15, exit beyond 45; 50 names, entry 25, exit beyond 75; Alpha 50: retained within rank 100. MSCI: buffer at 50% of the target count. Capitalmind: weekly review, but only stocks held at least one month are candidates for replacement. Zerodha Varsity: replace only the stocks that dropped out; consider a full equal-weight reset only when 6 or 7 names change.
- **Code-ready default.** N = 15; enter at rank <= 10 when a slot is free; exit at rank > 30; minimum hold 21 trading days; monthly check.
- **Evidence.** NSE's quarterly-versus-semi-annual study: 20 to 70% more churn for no return gain in two of three indices. Jegadeesh-Titman: turnover 84.8% semi-annually for the 6/6 strategy. Capitalmind large caps: quarterly beat monthly. Alpha Architect: the premium decays as rebalancing slows but costs rise with frequency, and they chose quarterly as the compromise.
- **Feasibility at ₹1.5 lakh.** Yes; this is what makes direct stock momentum affordable at this size.
- **Sources.** Method_NIFTY_Equity_Indices.pdf; whitepaper 2026; MSCI methodology; premium.capitalmind.in/introduction-to-capitalmind-momentum-model/; zerodha.com/varsity/chapter/momentum-portfolios/; Alpha Architect QMOM paper.

### S25. Momentum restricted to low "scaled turnover" stocks, annual rebalance (BacktestIndia)

- **Rules.** Universe: top 200 NSE stocks by market cap, PE > 0. Take the top 30 by 12-month return. Of those keep the 15 with the **lowest** scaled turnover (daily traded value divided by market cap). Equal weight. Rebalance once a year in December.
- **Reported performance.** December 2006 to June/December 2025, net of 0.11% transaction cost, 0.05% slippage, 12.5% LTCG and 20% STCG: low scaled turnover 19.43% net CAGR (21.07% gross), max drawdown -66.4%; all 30 names 14.60% (15.31% gross), -70.6%; the 15 with the highest scaled turnover 8.51% (9.02% gross), -75.1%, 100 months to recover; Nifty 50 10.41%, -55.1%.
- **Status of the evidence.** One self-published backtest by the operator of a backtesting site, also posted on Freefincal; not peer reviewed and not replicated. Fifteen stocks, one rebalance date a year, so results will be sensitive to the month chosen. The 0.11% cost is below what a ₹1.5 lakh account pays (section 1.4).
- **Why it matters here.** It is the one claim in this area that favours a small account: the names it selects are tradable for ₹10,000 tickets but not for large funds. It also implies the liquid, F&O-only Nifty200 Momentum 30 universe is where the premium is weakest.
- **Feasibility at ₹1.5 lakh.** Yes: 15 names, about 100% turnover a year or less, mostly long-term gains.
- **Sources.** backtestindia.com/blog/momentum-factor-india-liquidity-premium-scaled-turnover; freefincal.com/is-indian-momentum-investing-just-a-liquidity-illusion/.

### S26. Narrow-universe rotation: top 10 of the Nifty Next 50, monthly (WeekendInvesting "Mi NNF 10" type)

- **Rules as published.** Universe: Nifty Next 50 constituents. Always hold 10 stocks, never cash. Weights reset to 10% each at the start of every month. Ranking uses closing prices on the last trading day of the month; orders go out on the first trading day of the next month. The ranking formula is not disclosed.
- **Testable parameterisation (ours).** Rank on `MOM(12,1)` or the S13 score; hold the top 10; exit beyond rank 15; monthly.
- **Reported performance (manager's blog, includes back-tested period before the 12 Nov 2020 launch).** April 2016 to October 2022: CAGR 21.1% vs 13.3% for the Nifty Next 50; max drawdown 23.6% vs 42%.
- **Costs.** Ten positions of ₹15,000: 0.62% round trip. The published rule resets all ten weights monthly, which at this size adds small sell orders with DP charges; skip the re-weighting.
- **Failure modes.** Only 50 candidates, so the top 10 is the top quintile and the tilt is mild; the Next 50 changes composition every six months.
- **Feasibility at ₹1.5 lakh.** Yes.
- **Sources.** smallcase.com/blog/mi-nnf-10-the-passive-money-spinning-strategy/.

### S27. Momentum acceleration (practitioner definition)

- **Rules.** Score = return over the last 6 months minus return over the 6 months before that: `MOM(6,0) - (P[T-126]/P[T-252] - 1)`. Top N, monthly.
- **Evidence.** Listed by FreeFloat/StockViz as one of the common momentum measures; no performance figures in an opened source.
- **Feasibility at ₹1.5 lakh.** Yes mechanically; treat as an untested idea.
- **Sources.** freefloat.substack.com/p/the-momentum-factor.

## 4. Implementation notes that apply to every stock-level variant

- **Point-in-time universe.** Use the index constituents as they were on each date, including delisted and merged companies. Capitalmind and BacktestIndia both stress survivorship-free data. A ValuePickr reviewer also asks whether constituents were refreshed on announcement or effective dates.
- **Adjusted prices.** Splits, bonuses, rights and demergers must be adjusted; an unadjusted split looks like a -50% return and removes a winner from the ranking.
- **Total versus price return.** NSE scores use price return; index results quoted are total return.
- **Signal and trade timing.** Rank on a close, trade the next session. The NSE indices have about a month between data cut-off and effective date, which acts as a skip month.
- **Circuit filters.** NSE excludes non-F&O stocks that hit a circuit on 20% or more of days in six months. A backtest that buys at the close of an upper-circuit day assumes a fill that was not available.
- **Do not re-weight.** See section 1.4.
- **Tax lots.** Realised short-term gains are taxed at 20%; realised short-term losses offset them. Selling losers before year-end and letting winners pass 12 months is a legitimate rule variant to test.

### Data needs beyond daily prices

- Daily adjusted OHLCV for stocks, ETFs and indices is enough for: S1, S7, S8, S9, S10 (band form), S12 (market-model form), S13, S14, S15, S16, S17, S18, S22, S23 (sector indices), S24, S27.
- These also need point-in-time index membership for a faithful test, but can be approximated with a universe ranked by traded value and with equal weights instead of free-float tilt weights: S2, S4, S5, S6, S19, S26. S11 needs a market-cap floor, which a traded-value floor can stand in for.
- These need data that prices cannot supply: S3 (promoter pledge, free-float market cap for the turnover ratio), S20 (payout or dividend yield), S21 (ROE, debt to equity, EPS history), S25 (market capitalisation and PE history). S12 in its three-factor form needs the IIMA factor file, which is public.

## Negative or cautionary evidence

1. **Recent Indian results are weak.** Nifty200 Momentum 30: 7.93% a year for the five years to 30 Oct 2026 against 8.26% for the Nifty 200; calendar 2025 was 14 points behind the parent, 2022 was 10 points behind. Nifty500 Momentum 50 lost 15 points to its parent in 2025.
2. **A long live record shows the same.** Capitalmind Adaptive Momentum (live since March 2019, net of fees, with a cash rule): ahead of the Nifty 50 TRI over 6 and 7 years, behind over 2, 3, 4 and 5 years.
3. **Most index history is back-calculated.** Launch dates: N200M30 August 2020, Midcap150M50 August 2022, N200 Alpha 30 July 2022, N500M50 June 2024, N500 Multicap MQ50 September 2024. Only Nifty Alpha 50 (2012) and Alpha Low-Vol 30 (2017) have long live histories.
4. **Drawdowns are as deep as the market's or deeper.** 68 to 73% in 2008-09 for the NSE momentum indices; -70.6% for BacktestIndia's base momentum; Capitalmind describes its naive backtest drawdown as scary; StockViz: 50%+ drawdowns every 3 to 4 years for naive monthly momentum.
5. **Momentum crashes exist in India.** IIMA WML lost 18.3% and 25.0% in April and May 2009 and 13.5% in April 2020, all in market rebounds. The long-only leg kept rising, so the long-only damage is relative.
6. **The premium may be an illiquidity premium.** BacktestIndia: within the top-200 momentum set, the liquid half earned 8.51% net (below the Nifty 50) and the illiquid half 19.43%. Single source, not replicated.
7. **Large-cap edge faded after 2015.** Capitalmind's large-cap momentum was similar to a Nifty plus Next 50 mix from about 2015 to 2019. IIMA big-stock winners beat the market by 1.12% a month in 1994 to 2004 and 0.28 to 0.29% a month after 2005.
8. **Post-publication decay abroad.** US UMD: 8.3 to 8.4% a year over long samples, 6.3% for 1991 to 2013 with Sharpe 0.36. Blitz et al.: US total-return momentum earned -8.5% a year in 2000 to 2009.
9. **Faster rebalancing did not help.** NSE: quarterly had more churn and lower return than semi-annual for two of three indices. Capitalmind: quarterly beat monthly for large caps.
10. **Rebalance-date luck.** Capitalmind: shifting the quarter-end month changed both return and drawdown materially.
11. **Small portfolios did worst.** Capitalmind: 5 and 10 stock momentum portfolios "never quite recover"; this is the size range a ₹1.5 lakh account is pushed toward.
12. **Costs and taxes at this size are large relative to the edge.** A 2 to 3 point gross edge for large-cap winners is of the same order as 1 to 3% in charges plus 20% tax on gains for a monthly 15 to 20 stock portfolio. A ValuePickr poster reports a strategy that showed 54% CAGR over 10 years but 12% over 20 years after taxes, brokerage and slippage (anecdote).
13. **Variants that failed to replicate.** 12-7 "echo" momentum outside the US; the industry 52-week-high rule on Indian stocks (2014 to 2017, Sharpe about 0.4).
14. **Crowding.** ₹17,000 crore of passive money follows three NSE momentum indices and trades on known dates; 19 of 30 names were replaced at once in December 2025.
15. **Academic Indian studies are mostly gross and long-short.** None of the Indian papers opened reports net long-only returns for a retail-sized portfolio.

## Open questions

1. Net long-only results for a 10 to 15 stock portfolio at Angel One costs, by universe (Nifty 100, Next 50, 200, 500, Midcap 150) and schedule (monthly, quarterly, semi-annual, annual). This is the central test.
2. Does the BacktestIndia low-scaled-turnover result survive other rebalance months, other N, and realistic costs for a small account?
3. Is there any Indian evidence for residual momentum, the conservative formula, sector momentum, or the 52-week-high rank? The Raju papers (SSRN 4587697, 4163613) and the Capitalmind SSRN paper were blocked; their numbers are not in this file.
4. Does volatility scaling or the bear-state switch improve a long-only Indian portfolio? The Indian evidence here is on the long-short factor.
5. Which lookback works best in India (3, 6, 12 months; skip or no skip)? Capitalmind promised a post on this; I did not find it before the search budget ran out. A JT-style J x K grid on Indian data is needed.
6. BSDA status and the DP charge actually applied to this account (₹20 or ₹50 per sell), and whether same-day sale proceeds can fund same-day buys at Angel One.
7. ETF tickers, expense ratios and bid-ask spreads for the momentum and alpha ETFs (search snippets conflicted; only two Tickertape pages were opened).
8. Whether Budget 2026 changed equity capital gains rates. The 20% and 12.5% rates are confirmed from Zerodha Varsity and are used in a March 2026 backtest write-up, but I did not open the Finance Act text.
9. Exact rules of Clenow's exits, Barroso-Santa-Clara's window and Novy-Marx's results were taken from summaries; the primary texts were not opened.
10. Stocks under exchange surveillance (ASM/GSM) or trade-for-trade settlement often rank high on momentum; a rule to exclude them needs a point-in-time list, which I did not locate.
11. The "High-To-Price" momentum variant that StockViz says removes the crash component: the paper was not opened and no rule is recorded here.

## Sources opened

NSE and index providers
- https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf (September 2026)
- https://www.niftyindices.com/Methodology/Method_Nifty_Alpha_50.pdf
- https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/momentum-strategy-whitepaper_2026.pdf
- https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/nifty200_momentum_30_index_whitepaper_sep_20.pdf
- https://niftyindices.com/docs/default-source/indices/nifty-midcap150-momentum-50/nifty-midcap150-momentum-50-whitepaper_2023.pdf
- https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf
- https://www.niftyindices.com/Factsheet/FactsheetNifty500Momentum50.pdf
- https://www.niftyindices.com/Factsheet/Factsheet_NiftyMidcap150Momentum50.pdf
- https://www.niftyindices.com/Factsheet/Factsheet_Nifty_Alpha50.pdf
- https://www.niftyindices.com/Factsheet/Factsheet_Nifty200Alpha30.pdf
- https://www.niftyindices.com/Factsheet/Factsheet_Nifty_Alpha_Low-Volatility_30.pdf
- https://www.niftyindices.com/Factsheet/Factsheet_Nifty500MulticapMQ50.pdf
- https://www.niftyindices.com/Factsheet/ind_nifty50.pdf
- https://www.niftyindices.com/Factsheet/ind_nifty_200.pdf
- https://www.niftyindices.com/Factsheet/ind_nifty_500.pdf
- https://www.niftyindices.com/Factsheet/ind_Nifty_Midcap_150.pdf
- https://www.niftyindices.com/Factsheet/ind_next50.pdf
- https://www.msci.com/eqb/methodology/meth_docs/MSCI_Momentum_Indexes_Methodology_June2017.pdf

Academic
- https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf
- https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf
- https://repub.eur.nl/pub/22252/ResidualMomentum-2011.pdf
- https://www.nber.org/system/files/working_papers/w20439/w20439.pdf
- https://faculty.iima.ac.in/~iffm/Indian-Fama-French-Momentum/ (page and CSV files, release 2025-12)
- https://ideas.repec.org/p/iim/iimawp/12130.html
- https://www.iima.ac.in/publication/four-factor-model-indian-equities-market
- https://www.iima.ac.in/eventswebinar-systematic-long-only-momentum-strategy-financial-markets-evidence-india
- https://nsearchives.nseindia.com/content/research/res_paperfinal223.pdf
- https://www.publishingindia.com/storage/PDFBrochures/2192.pdf
- https://publishingindia.com/storage/PDFBrochures/3029.pdf
- https://ideas.repec.org/a/sae/fbbsrw/v11y2022i3p347-358.html
- https://ideas.repec.org/a/eme/jefasp/jefas-08-2021-0159.html
- https://arxiv.org/abs/2302.13245

Practitioner, global
- https://quantpedia.com/strategies/momentum-factor-effect-in-stocks
- https://quantpedia.com/strategies/residual-momentum-factor
- https://quantpedia.com/strategies/52-weeks-high-effect-in-stocks
- https://quantpedia.com/an-analysis-of-52-weeks-high-effect-on-indian-stocks/
- https://www.quantinsti.com/blog/trading-strategy-52-weeks-high-effect-in-stocks/
- https://alphaarchitect.com/avoiding-momentum-crashes/
- https://alphaarchitect.com/when-academics-disagree-on-momentum-investing/
- https://alphaarchitect.com/wp-content/uploads/2021/08/The_Quantitative_Momentum_Investing_Philosophy.pdf
- https://alphaarchitect.com/the-conservative-formula-quantitative-investing-made-easy/
- https://www.cxoadvisory.com/momentum-investing/stripping-risks-from-a-stock-momentum-strategy/
- https://cxoadvisory.com/momentum-investing/momentum-echo-outside-the-u-s
- https://turingtrader-com.web.app/portfolios/clenow-stocks-on-the-move
- https://quant-investing.com/blog/how-to-find-stocks-on-the-move-with-a-better-momentum-indicator-exponential-regression

Practitioner, India
- https://zerodha.com/varsity/chapter/momentum-portfolios/
- https://www.capitalmind.in/insights/momentum-investing-basics-india
- https://www.capitalmind.in/insights/momentum-strategy-how-many-stocks
- https://premium.capitalmind.in/2019/08/momentum-how-does-it-look-in-large-cap-stocks/
- https://premium.capitalmind.in/introduction-to-capitalmind-momentum-model/
- https://capitalmind.in/portfolio-management-service/momentum
- https://www.capitalmind.in/podcasts/demystifying-momentum
- https://backtestindia.com/blog/momentum-factor-india-liquidity-premium-scaled-turnover
- https://freefincal.com/is-indian-momentum-investing-just-a-liquidity-illusion/
- https://www.smallcase.com/blog/mi-nnf-10-the-passive-money-spinning-strategy/
- https://www.smallcase.com/blog/mi-25-our-flagship-smallcap-strategy/
- https://www.smallcase.com/smallcase/WKIMO_0007
- https://stockviz.substack.com/p/momentum-without-the-crash
- https://freefloat.substack.com/p/the-momentum-factor
- https://curiousinvestinginsights.substack.com/p/momentum-or-mayhem-unpacking-the
- https://momentumlab.substack.com/p/backtesting-momentum-investing-strategies-1eb
- https://forum.valuepickr.com/t/backtesting-volatility-adjusted-momentum-with-a-gold-regime-filter-2018-2026/218153
- https://tradingqna.com/t/best-way-to-do-momentum-trading-in-india/154146
- https://www.scribd.com/document/694152012/SSRN-id4587697 (description only)

News, costs, tax
- https://www.business-standard.com/amp/markets/news/nifty200-momentum30-a-flip-of-index-switch-jolts-16k-cr-across-the-grid-125121400388_1.html
- https://www.valueresearchonline.com/stories/222938/momentum-funds-performance-12-months/
- https://www.angelone.in/exchange-transaction-charges
- https://www.chittorgarh.com/brokerage_charges/angel-broking/14/
- https://zerodha.com/charges/
- https://zerodha.com/varsity/chapter/taxation-for-investors/
- https://www.tickertape.in/etfs/icici-prudential-nifty-200-momentum-30-etf-ICICM
- https://www.tickertape.in/etfs/motilal-oswal-nifty-200-momentum-30-etf-MOMO
