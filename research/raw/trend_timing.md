# Trend following, market timing and tactical allocation: research findings

Researcher area: trend_timing. Compiled 2026-11-10 for a ₹1,50,000 Angel One (SmartAPI) account, India, fully automated, profits reinvested.

## How this was researched, and what the labels mean

- 31 web searches were run (academic, practitioner, Indian blogs/forums, broker and tax pages). The shared search budget for the run was then exhausted, so the remaining verification was done by opening known URLs directly with `fetch_text.py`. No search engine was queried by other means.
- "Opened" means I read the page or PDF text myself. "(unverified: snippet only)" means the claim comes from a search-result summary and I could not open the underlying source. "(researcher's adaptation)" means the rule is my translation of a published rule to Indian ETFs and has no published backtest. "(from memory, not opened)" marks things I know of but did not verify in this session; treat them as leads, not facts.
- Almost every published number below is gross of Indian taxes, and most are gross of costs. Section 0 explains why that matters more for this family than for any other.
- Forum threads on TradingQnA and ValuePickr render only a title to the fetch tool, so I read them through the forums' raw-text endpoints (`https://tradingqna.com/raw/<topic id>`, `https://forum.valuepickr.com/raw/<topic id>`). The thread URLs are given in the text; the raw URLs are the ones listed in the cards file.

## Index of strategies and card ids

| # | Strategy | Card id | Evidence | Feasible at ₹1.5 lakh |
|---|---|---|---|---|
| 1 | Single moving-average price timing | trend_timing__single_ma_price_timing | some academic, India mixed | yes |
| 2 | Dual moving-average crossover | trend_timing__dual_ma_crossover | negative on Indian large caps | yes |
| 3 | Faber GTAA, five sleeves | trend_timing__faber_gtaa5_10m_sma | some academic | yes |
| 4 | Faber GTAA Aggressive, top N | trend_timing__faber_gtaa_aggressive_topn | practitioner | yes |
| 5 | Time-series momentum, 12-month | trend_timing__tsmom_12m_vol_scaled | strong academic (futures) | marginal |
| 6 | Multi-horizon trend blend | trend_timing__multi_horizon_trend_blend | strong academic (futures) | yes |
| 7 | Absolute momentum, equity vs cash | trend_timing__absolute_momentum_equity_vs_cash | some academic | yes |
| 8 | Dual momentum, Indian edition | trend_timing__dual_momentum_gem_india | practitioner, India | yes |
| 9 | Paired switching, Nifty and gold | trend_timing__paired_switching_nifty_gold | practitioner, India | yes |
| 10 | Accelerating Dual Momentum | trend_timing__accelerating_dual_momentum | practitioner | yes |
| 11 | Protective Asset Allocation | trend_timing__protective_asset_allocation | practitioner | marginal |
| 12 | Vigilant Asset Allocation | trend_timing__vigilant_asset_allocation | practitioner | yes |
| 13 | Defensive Asset Allocation (canary) | trend_timing__defensive_asset_allocation_canary | practitioner | yes |
| 14 | Hybrid Asset Allocation | trend_timing__hybrid_asset_allocation | practitioner | marginal |
| 15 | Donchian channel breakout | trend_timing__donchian_channel_breakout | negative on Nifty | yes |
| 16 | Turtle system | trend_timing__turtle_system_atr_units | anecdotal | marginal |
| 17 | Keltner plus Donchian sector timing | trend_timing__keltner_donchian_sector_timing | some academic | marginal |
| 18 | Supertrend long-only | trend_timing__supertrend_long_only | practitioner, India | yes |
| 19 | Volatility targeting overlay | trend_timing__volatility_targeting_overlay | strong academic, contested | yes |
| 20 | Sector momentum rotation | trend_timing__sector_momentum_rotation | some academic | marginal |
| 21 | Asset-class relative-strength rotation | trend_timing__asset_class_relative_strength_rotation | some academic | yes |
| 22 | Risk-on/risk-off switch to gold | trend_timing__risk_on_off_gold_switch | anecdotal, India | yes |
| 23 | Exit on drawdown from the high | trend_timing__drawdown_from_high_exit | negative, India | yes |
| 24 | Long-short trend on index futures | trend_timing__index_futures_long_short_trend | negative, India | no |

---

## 0. India implementation facts that apply to every strategy here

### 0.1 Costs at Angel One (opened: angelone.in pricing page, Nov 2026)

- Equity delivery and intraday brokerage: lower of ₹20 or 0.1% per executed order, minimum ₹5. F&O: ₹20 per executed order.
- NSE transaction charge 0.0030699% (cash), stamp duty 0.015% on buys (delivery), SEBI ₹10 per crore, GST 18% on brokerage + transaction + SEBI charges.
- DP charge on every delivery sell: ₹20 + GST per ISIN per day (about ₹23.60), regardless of size.
- STT shown for delivery equity is 0.1% on buy and sell. Secondary sources say exchange-traded equity ETF units carry only 0.001% on the sell side and gold/debt/liquid ETFs carry none (unverified: snippet only). This single item changes round-trip cost from about 0.07% to about 0.27%, so it must be confirmed from a real contract note before live trading.
- Futures STT is 0.05% of sell value and options STT 0.15% of sell premium (Angel One page; Budget 2026 change effective 1 April 2026 per search summary).
- Account maintenance: ₹60 + GST per quarter for non-BSDA accounts.

Worked example, one ETF, whole account (₹1,50,000), assuming the 0.001% ETF STT:
- Buy: ₹20 brokerage + ₹4.60 exchange + ₹4.46 GST + ₹22.50 stamp ≈ ₹52.
- Sell: ₹20 + ₹4.60 + ₹4.46 + ₹1.50 STT + ₹23.60 DP ≈ ₹54.
- Round trip ≈ ₹106 ≈ 0.07% of capital, plus the bid-ask spread (tight for NIFTYBEES/GOLDBEES, wide for small sector ETFs).

Small orders are where the flat fees bite:
- ₹30,000 order: ₹20 brokerage = 0.067% per side.
- ₹12,500 order (a 1/12 slice): ₹12.50 = 0.10% per side, and a sell adds ₹23.60 DP = 0.19% more.
- ₹2,000 rebalancing sell: ₹5 + GST + ₹23.60 DP ≈ ₹29.50 = 1.5% of the trade.

Design consequences: hold few positions (1 to 5), never do small partial sells, rebalance only on signal change or when drift exceeds a wide band, and prefer monthly decision frequency.

### 0.2 Taxes (opened: Zerodha Fund House ETF tax guide; search summaries of Budget 2024 and 2026)

- Equity ETFs: gains on units held under 12 months taxed at 20%; over 12 months at 12.5%, with the first ₹1.25 lakh of long-term equity gains per year exempt.
- Gold and silver ETFs: long-term after 12 months at 12.5% without indexation; short-term at slab rate.
- Debt ETFs (over 65% debt, bought on or after 1 April 2023), which includes liquid and gilt ETFs: taxed at slab rate regardless of holding period.
- Budget 2026 left the capital-gains framework unchanged and raised F&O STT (unverified: snippet only).
- International ETFs (Nasdaq 100 etc.): treatment not confirmed in a source I opened.

Why this matters: every strategy in this file sells and rebuys. A switch after less than 12 months turns an unrealised gain into a 20% (or slab-rate) tax bill, while buy-and-hold defers tax and eventually pays 12.5% above the exemption. Freefincal's Indian backtests haircut the final tactical corpus by 20% to approximate this (versus 4% for an annually rebalanced portfolio). Any backtest we run must deduct tax as an annual cash outflow, otherwise it will overstate every strategy here relative to buy-and-hold. At ₹1.5 lakh the ₹1.25 lakh exemption is large relative to the account, which favours rules that hold equity ETF winners beyond 12 months.

### 0.3 Instruments (tickers are from my prior knowledge and must be checked against the Angel One instrument master)

- Broad equity: NIFTYBEES (Nifty 50), JUNIORBEES (Nifty Next 50), MID150BEES (Nifty Midcap 150), a Nifty Smallcap 250 ETF.
- Sector: BANKBEES, PSUBNKBEES, ITBEES, PHARMABEES, AUTOBEES, INFRABEES, CONSUMBEES and similar. Several are thinly traded.
- Gold and silver: GOLDBEES (listed March 2007 per a ValuePickr commenter), SILVERBEES.
- Cash proxy: LIQUIDBEES or a growth-NAV liquid ETF. For backtests use a liquid/overnight rate index, because LIQUIDBEES trades near a constant price and pays out its return.
- Government bonds: LTGILTBEES (long gilt), GILT5YBEES (5-year gilt).
- International: MON100 (Nasdaq 100). Opened sources (Finvezto, Agnifolio) report that its premium to NAV averaged about 3.7% from June 2023 to June 2026, with a median day near 0.7%, 17% of days above a 10% premium, and a peak of 27.7% on 5 June 2026, because the industry-wide overseas investment cap (about USD 7 billion, about USD 1 billion for ETFs) repeatedly halts unit creation. A momentum signal on MON100's traded price is partly a signal on the premium. Either exclude it, or trade it only when premium to iNAV is below a threshold.

### 0.4 Derivatives are out of reach for directional trend following at this size

- Nifty 50 lot is 65 from the January 2026 series (opened: Angel One news). Nifty Bank 30, Nifty Financial Services 60, Nifty Midcap Select 120.
- At an index level of about 25,700 (the level cited by Zerodha's Sandeep Rao in November 2025; the current level was not checked), one lot is about ₹16.7 lakh notional, about 11 times the account. He put exchange margin near ₹2.2 lakh for the then 75-unit lot; scaled to 65 units that is roughly ₹1.9 lakh (my arithmetic), more than the whole account.
- Stocks cannot be shorted overnight in the cash market, so every strategy below is long-or-flat unless stated.

---

## 1. Single moving-average price timing (200-day, 100-day, 10-month)

**Rules.** Universe: one equity index ETF plus a cash proxy. Signal: closing price versus a simple moving average of length L. If flat and close > SMA(L), buy at the next open (Faber trades at the signal-day close). If long and close < SMA(L), sell at the next open and hold the liquid ETF. One position. No other stop.

**Parameter values used by sources.**
- L = 10 month-end closes, checked only on the last trading day of the month (Faber; freefincal).
- L = 200 daily closes, checked daily (Freefloat; MoneyWorks4me).
- L = 100 days (Capitalmind headline), 50 days (Freefloat), sweep 10 to 250 days (Capitalmind).
- EMA(k) with k in {10, 20, 50, 100, 200} plus a confirmation rule: buy only after m consecutive closes above the EMA, sell only after n consecutive closes below, m and n in {2, 3, 4, 5} (Slivka, Keswani and Li, 80 algorithms).
- A percentage band around the average to cut whipsaws is a common variant (from memory, not opened).

**Instruments.** NIFTYBEES (also JUNIORBEES, MID150BEES) and a liquid ETF.

**Holding period.** Months. Faber reports less than one round trip per year on the S&P 500 and about 70% of time invested. Capitalmind's 100-day rule on Nifty made 64 trades in 16 years.

**Reported performance.**
- US, Faber: S&P 500 1901 to 2012, timing improved compound return and cut risk while underperforming the index in roughly half of all years. Returns are about 60% lower and volatility about 30% higher when a market is below its 10-month SMA (five asset classes, 1973 to 2012). Excludes taxes, commissions and slippage.
- India, Freefloat (Nifty, 1 March 2004 to June 2020): buy and hold 12.68% a year with a worst drawdown of 58.45%; 200-day rule 14.26% with worst drawdown 28.68%; 50-day rule 14.81% with worst drawdown 26.92%. Exits go to bonds. No costs or taxes.
- India, MoneyWorks4me (Nifty with JM Liquid Fund, 22 years): 200-day rule 13.4% CAGR versus 13.5% buy and hold, before tax and brokerage, which the authors estimate would cost a further 0.2 to 1 percentage point a year.
- India, Capitalmind (Nifty, 2005 to May 2020): the timed strategy lost less than buy and hold in every drawdown except 2014; buy and hold won in 12 of 16 calendar years; all the benefit came in 2008, 2011 and 2020. A 10-day average returned 13.9% a year versus 10.1% for buy and hold but needed 293 trades. Averages longer than about six months were counter-productive on return. Every length from 10 to 250 days reduced maximum drawdown.
- India, Slivka, Keswani and Li (Indian Journal of Finance, 2014; Nifty 2005 to 2012, no costs, no dividends, cash at MIBOR, bootstrap significance): the family of 80 EMA rules worked well in the sharp 2008 decline and far less or not at all in gradually rising, mixed or trendless periods. In the trendless 2011 to 2012 period only EMA(20,5,2) tested significant.
- India, Mitra (Quantitative Finance, 2011; four Indian index series): moving-average rules capture direction and give significant gross returns, but "these returns cannot be exploited fully due to real world transaction costs"; short averages generate many trades.
- India, freefincal (Sensex, 338 rolling ten-year SIP windows, 10-month rule, 20% haircut for tax and loads): higher returns in some windows, but the rule was generally riskier than a 50/50 systematic portfolio on months underwater and maximum drawdown, and needed more equity sell-offs than a PE-based rule.

**Cost and capacity.** One or two round trips a year at about 0.07% each is negligible. Tax is not: each exit within 12 months crystallises gains at 20%.

**Failure modes.** Whipsaw in sideways markets (2010 to 2013, 2015 to 2016). V-shaped crashes: exits near the low, re-entry after the rebound (March 2020). Long stretches of underperformance in steady bull markets. The Indian evidence says the edge is drawdown reduction, not return.

**Feasibility at ₹1.5 lakh.** Yes. One liquid ETF, one order per switch, whole-account orders hit the ₹20 brokerage cap.

**Sources.** https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf ; https://freefloat.substack.com/p/tactical-allocation ; https://www.moneyworks4me.com/investmentshastra/time-the-market-or-asset-allocation/ ; https://premium.capitalmind.in/2020/05/time-the-market-sleep-better/ ; https://www.indianjournalofcapitalmarkets.com/index.php/IJF/article/download/71980/58008/125426 ; https://econpapers.repec.org/RePEc:taf:quantf:v:11:y:2011:i:2:p:287-297 ; https://freefincal.com/market-timing-with-ten-month-moving-average-tactical-asset-allocation-backtest-part-2/

---

## 2. Dual moving-average crossover (5x20, 50x200 golden cross, 150x365 days, 6x12 months)

**Rules.** Long when the fast average is above the slow average, otherwise in cash or debt. Evaluate daily for day-based pairs and at month end for month-based pairs. One position.

**Parameter values used by sources.**
- 5-day and 20-day SMA, daily, Donchian's crossover (Zerodha test).
- 50-day and 200-day SMA, the golden cross (Market Shack study).
- 150-day and 365-day averages, Jim Otar's "hurricane warning" chart (freefincal).
- 6-month and 12-month averages of month-end index values (freefincal "double moving average" series).

**Instruments.** Index ETF and liquid or gilt ETF. Freefincal also applies the 6x12 rule to gold, gilts, Nasdaq 100 and a momentum index (Nifty Midcap 150 Momentum 50 TRI).

**Holding period.** 5x20: days to weeks. Others: many months. Freefincal counts about two switches per five years for 6x12 and eight equity exits in 18.7 years for 150x365.

**Reported performance.**
- India, Zerodha's Sandeep Rao (Nifty spot daily, January 2015 to October 2025, no costs): 5x20 SMA is "a shade better" than the 20-day Donchian breakout "but still not tradable"; median trade P&L negative for long-and-short, long-only and short-only; long-only captured about 7,500 index points in ten years. Verdict: "both are to be dumped".
- India, Market Shack (Nifty 1995-11-03 to 2026-05-05, 50x200 used as a monthly gate for deploying a ₹10,000 SIP, 0.03% cost, 5% on idle cash, nothing ever sold): 11.9803% XIRR versus 11.9907% for a plain SIP; ₹68,863 behind after 30.5 years. No edge as an entry filter.
- India, freefincal 150x365 (Nifty, one 18.7-year window from 2000, 60/40 SIP, debt at an assumed 8%, no tax or exit load): maximum drawdown cut by more than half, XIRR 12.5% versus 11.5%. The author warns it is a single window and expects the edge to shrink with taxes and more windows.
- India, freefincal 6x12: "reasonably works" on Indian gilts, Nasdaq 100, S&P 500 and gold (gold in INR, 341 rolling 15-year windows from 1979: usually lower drawdown and volatility, XIRR not always higher). It "fails badly" on Sensex after March 2020, and also on Nifty Next 50 and Nifty Midcap 150, though not on Nifty Smallcap 250. On the Midcap 150 Momentum 50 index (2005 onward) results were "promising" on return but often with higher drawdown and volatility than a 50/50 systematic portfolio, and the advantage shrank at 70% equity.

**Cost and capacity.** Slow pairs trade rarely, so costs are trivial and tax dominates. The 5x20 pair trades often; costs were not included in the negative result above, so net is worse.

**Failure modes.** Slow pairs lag badly in sharp reversals: freefincal's headline is that the March 2020 path produced a failure "122 years of backtesting failed to reveal". Results are arbitrary across indices.

**Feasibility at ₹1.5 lakh.** Yes mechanically. Evidence is weak to negative for Indian large-cap indices.

**Sources.** https://tradingqna.com/t/trend-following-in-india-part-1-testing-donchian-s-classic-rules/188234 ; https://finance-platform-fawn-ten.vercel.app/projects/the-200-dma-golden-cross-on-nifty-confirmed-too-late-to-matter ; https://freefincal.com/moving-average-crossover/ ; https://freefincal.com/a-risk-in-market-timing-that-122-years-of-backtesting-failed-to-reveal ; https://freefincal.com/testing-a-double-moving-average-market-timing-model-with-gold-part-3/ ; https://freefincal.com/momentum-index-fund-will-tactical-entry-exit-give-better-results/

---

## 3. Faber GTAA: five sleeves, each timed by its 10-month SMA

**Rules (Faber, opened).** Five asset classes at 20% each: US stocks, foreign stocks, bonds, real estate, commodities. On the last trading day of each month, for each sleeve independently: hold the asset if its month-end price is above its 10-month SMA, otherwise hold cash (T-bills) with that 20%. Trades at the signal-day close. Total-return series. Rebalanced monthly to equal weights. Variants: "Conservative" holds 40% bonds and parks cash in 10-year government bonds; a leveraged version doubles every sleeve.

**India adaptation (researcher's adaptation).** Five sleeves of ₹30,000: NIFTYBEES; JUNIORBEES or MID150BEES; GOLDBEES; LTGILTBEES or GILT5YBEES; MON100 (subject to the premium rule in 0.3) or SILVERBEES. Cash sleeve: liquid ETF. To control flat-fee drag, rebalance a sleeve only when its signal flips or its weight drifts outside 15% to 25%.

**Holding period.** Months per sleeve; Faber reports 3 to 4 portfolio round trips a year and an average of 70% invested.

**Reported performance.**
- Faber, 1973 to 2012, five US-centric asset classes: volatility reduced to single digits; "drawdown is reduced from 46% to less than 10%"; one down year of less than 1%. The FAQ gives historical volatility about 7% and maximum drawdown about 10% for GTAA Moderate, and says a 20% drawdown should be expected in future. 2006 to 2012 is described as out of sample. Moving-average lengths of 3 to 12 months all worked similarly. Excludes taxes, commissions and slippage.
- Quantpedia's page on the same paper lists 11.27% a year, 6.87% volatility, maximum drawdown 29.43%, Sharpe 1.06 for 1973 to 2008 "from exhibit 19", and notes the 13-asset version earned 13.41% with cash in 10-year bonds versus 12.04% with T-bills. The 29.43% drawdown does not match Faber's own "less than 10%" for the five-asset model; the exhibit appears to be a different variant. Treat the drawdown figure as unresolved.

**India evidence.** None for the timed version. MoneyWorks4me show a static five-asset portfolio at 20% each, rebalanced once a year (30 years, annual asset returns from Motilal Oswal Research) had only three negative years and lost 5.4% in 2008, which is the diversification half of the idea without the timing half.

**Cost and capacity.** About 0.26% per sleeve round trip at ₹30,000 (two ₹20 brokerages plus GST, DP and stamp). At under one round trip per sleeve per year, under 0.3% a year. Gilt and liquid sleeves are taxed at slab rate.

**Failure modes.** Whipsaws in each sleeve; all sleeves in cash during broad drawdowns means missing V-shaped recoveries; MON100 premium collapses; gilt ETF illiquidity.

**Feasibility at ₹1.5 lakh.** Yes, with five sleeves and band rebalancing.

**Sources.** https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf ; https://quantpedia.com/strategies/asset-class-trend-following ; https://www.moneyworks4me.com/investmentshastra/time-the-market-or-asset-allocation/

---

## 4. Faber GTAA Aggressive: top-N by blended momentum, each gated by its 10-month SMA

**Rules (Faber, opened).** Start from 13 asset classes. Each month rank by the average of 1, 3, 6 and 12-month total returns. Select the top six (or top three). Hold each selected asset at equal weight only if it is above its long-term (10-month) moving average; otherwise that slice goes to cash.

**India adaptation (researcher's adaptation).** Universe of 8 to 10 ETFs (NIFTYBEES, JUNIORBEES, MID150BEES, smallcap ETF, BANKBEES, ITBEES, GOLDBEES, SILVERBEES, LTGILTBEES, MON100). Top 3 at one third each (₹50,000 slices).

**Holding period.** One to several months per holding.

**Reported performance.** Faber shows Aggressive variants with higher returns than GTAA Moderate over 1973 to 2012 (figures are in an image I could not extract). No Indian backtest found.

**Cost and capacity.** Turnover is higher than GTAA 5. Three ₹50,000 positions keep brokerage at the ₹20 cap.

**Failure modes.** Concentration in correlated equity ETFs (Nifty, Next 50, midcap move together); momentum crashes at turning points; premium noise in MON100.

**Feasibility at ₹1.5 lakh.** Yes with top 3.

**Sources.** https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf

---

## 5. Time-series momentum, 12-month sign with volatility scaling (Moskowitz, Ooi and Pedersen)

**Rules (opened).** For each instrument at each month end: signal = sign of the past 12-month excess return. Position size = 40% divided by the instrument's ex-ante annualised volatility, long if the signal is positive and short if negative. Hold one month. The diversified factor is the equal-weighted average across instruments. Ex-ante variance = 261 times the exponentially weighted average of squared daily returns (deviations from the exponentially weighted mean), with decay chosen so the weights' centre of mass is 60 days; the estimate at t-1 is applied to month t.

**India adaptation (researcher's adaptation).** Long-or-flat on ETFs: weight_i = (1/N) x min(1, target_vol / sigma_i) if the 12-month return exceeds the liquid return, else 0; unallocated capital in the liquid ETF. A per-asset target of about 15% is my placeholder, not a published value.

**Instruments.** Original: 58 liquid futures across equity indices, currencies, commodities and bonds. India: 4 to 8 ETFs across equity, gold, silver and gilt.

**Holding period.** One month, positions typically persist for many months.

**Reported performance.**
- Moskowitz, Ooi and Pedersen (January 1985 to December 2009): 12-month time-series momentum profits were positive for every one of the 58 contracts; the diversified portfolio had about 12% annualised volatility and a Sharpe ratio above one, roughly 2.5 times the equity market's; alpha of about 1.58% a month against standard factors; largest gains in the last quarter of 2008. Gross of costs.
- Hurst, Ooi and Pedersen (67 markets, January 1880 to December 2013, equal blend of 1, 3 and 12-month signals, 10% volatility target, after estimated transaction costs): 14.9% a year gross of fees, 11.2% net of a 2-and-20 fee, 9.7% volatility, net Sharpe 0.77, correlation with US equities 0.00. The authors themselves discuss a scenario where the future net Sharpe is only 0.4.
- Baltas and Kosowski (via Quantpedia): strong at monthly frequency, weaker weekly, weak daily, with reversal at very short horizons.

**India evidence.** Singh, Walia, Bekiros, Gupta, Kumar and Mishra (2022), BSE stocks, monthly, January 1996 to December 2020, long-short: "a substantial absolute momentum effect in the Indian equity market", but "exposed to occasional severe losses"; their risk-managed version earned 2.5 times the standard version. That is single stocks, long-short, which a retail account cannot run. I found no peer-reviewed test on Nifty or Bank Nifty futures.

**Cost and capacity.** The published results rely on 58 or more futures, shorting and leverage. A four-to-eight ETF long-only version loses most of the diversification and all of the crisis-period short profits.

**Failure modes.** Sharp reversals (Q3 2008 losses before Q4 gains; 2009 rebound); long flat periods for trend following generally after 2009.

**Feasibility at ₹1.5 lakh.** Marginal: only the long-or-flat ETF version is possible; the futures version is not.

**Sources.** https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf ; https://www.trendfollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf ; https://quantpedia.com/strategies/time-series-momentum-effect ; https://ideas.repec.org/a/eme/jefasp/jefas-08-2021-0159.html

---

## 6. Multi-horizon trend blend with graded exposure (1, 3 and 12 months)

**Rules (Hurst, Ooi and Pedersen, opened).** For each market compute three signals: the sign of the past 1-month, 3-month and 12-month return. Each of the three strategies is always long or short every market, with each position sized to the same volatility. The three are aggregated monthly and the whole portfolio is scaled to a 10% ex-ante annual volatility using a covariance matrix from rolling 3-year monthly returns.

**India adaptation (researcher's adaptation).** Long-only graded exposure per ETF: exposure = (number of the three lookbacks with return above the liquid return) / 3, so 0, one third, two thirds or fully invested. Rebalance at month end only when the exposure step changes.

**Indian real-world analogue.** Edelweiss Balanced Advantage Fund describes a pro-cyclical model (EEHI) whose trend inputs include Nifty's 1-week, 2-week, 1-month and 3-month moving averages alongside volatility, valuation and macro inputs, moving equity between 30% and 80%; the fund house claims it beat counter-cyclical models in 15 of 20 calendar years (unverified: snippet only; a manufacturer's claim, and the exact model is not public).

**Holding period.** Weeks to months; the 1-month leg makes it faster than strategy 5.

**Reported performance.** As for Hurst et al. in strategy 5. No Indian backtest of the graded long-only form.

**Cost and capacity.** Step changes of one third of a sleeve on ₹1.5 lakh are ₹50,000 trades if one ETF is used, so costs are fine with one or two ETFs and poor with many.

**Failure modes.** The 1-month leg whipsaws; partial exposure means partial participation in both directions.

**Feasibility at ₹1.5 lakh.** Yes with one or two ETFs.

**Sources.** https://www.trendfollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf

---

## 7. Absolute momentum: equity versus cash (12-month, 6-month or 200-day lookback)

**Rules.** At each month end compute the asset's total return over the lookback and the return of a cash or debt proxy over the same window. If the asset's return is higher, hold the asset; otherwise hold the debt proxy. One position.

**Parameter values used by sources.**
- 12 months versus Treasury bills: Antonacci defines absolute momentum as "positive past returns in excess of US Treasury bill returns", re-evaluated monthly (opened: Optimal Momentum site). His paper "Absolute Momentum: A Simple Rule-Based Strategy and Universal Trend-Following Overlay" is listed on his research page; I could not open the paper itself.
- 6 months, equity return versus debt return (freefincal "Nifty momentum timing").
- 200 trading days versus a fixed-deposit return (MomentumLab).

**Instruments.** NIFTYBEES (or another index ETF) and a liquid or short gilt ETF.

**Holding period.** Months. Freefincal counts 12 to 13 equity sell-offs per 15 years on average for the 6-month rule.

**Reported performance.**
- India, freefincal (Nifty, all rolling 15-year, 10-year and 5-year SIP windows, 20% haircut for tax and loads): "clearly a higher risk, potentially higher [return] strategy" than a 60/40 or 50/50 systematic portfolio; deeper drawdowns; over 5-year windows the return advantage "practically becomes a coin toss".
- Global evidence for the 12-month sign rule is the time-series momentum literature in strategy 5.

**Cost and capacity.** About one round trip a year. Tax as in 0.2.

**Failure modes.** Same as strategy 1. With a 12-month lookback the exit can come very late in a fast crash.

**Feasibility at ₹1.5 lakh.** Yes.

**Sources.** https://www.optimalmomentum.com/global-equities-momentum/ ; https://www.optimalmomentum.com/research/ ; https://freefincal.com/nifty-momentum/ ; https://momentumlab.substack.com/p/backtesting-dual-momentum-strategy

---

## 8. Dual momentum, Indian edition (Antonacci GEM with Nifty, gold and debt)

**Rules, original (opened: Optimal Momentum; rule order from a secondary summary).** Indexes: S&P 500, MSCI ACWI ex-US, Barclays US Aggregate Bond. Monthly. Relative momentum picks the stronger of the two equity indexes on trailing 12-month total return; absolute momentum requires that return to exceed Treasury bills; otherwise hold aggregate bonds. Antonacci's FAQ warns that checking more often than monthly invites whipsaw and that he prefers bonds or bills to shorting.

**Rules, Indian edition (Samasthiti, opened).** Assets: Nifty 50; gold (Gold BeES price from 30 November 2009, INR gold before that); a debt fund (ABSL Income Fund). At each month end, using 12-month returns: if Nifty's return is below the debt fund's, hold the debt fund; otherwise hold whichever of Nifty and gold has the higher return. Wholly in one asset each month.

**Variant (MomentumLab, opened).** 200-day returns. Hold Nifty if its return beats both gold and a fixed deposit; hold gold if gold beats both; otherwise hold the fixed deposit.

**Instruments.** NIFTYBEES, GOLDBEES, liquid or gilt ETF.

**Holding period.** Months to years.

**Reported performance.**
- Samasthiti (December 1996 to January 2024, month-end data): 14.0% CAGR versus 12.4% for Nifty 50. Drawdown about 21% in November 2008 versus more than 50%; about 11% in 2020 versus close to 30%. Beat Nifty buy and hold in every rolling start year tested (minimum 15 years) except one. No costs or taxes; a reader comment raises exactly that.
- MomentumLab (2014 to 2024): 18.79% CAGR versus 12.13% Nifty and 10.86% gold; maximum drawdown 11.42% versus 34.00% and 21.44%. Ten years, one parameter set, no costs or taxes, promotional source.
- US original: search summaries quote a 43-year CAGR of 17.43% versus 12.34% for the S&P 500 and a maximum drawdown near 22%, and note that lagging the lookback by one month cut excess return from almost 8% to about 6% (unverified: snippet only). Antonacci's own page states the figures exclude transaction costs and taxes.

**Cost and capacity.** Very low turnover. All switches are whole-account orders at the ₹20 cap. Gold gains under 12 months and all debt gains are taxed at slab rate.

**Failure modes.** A ValuePickr commenter who tested gold versus Nifty ETFs said the outperformance came almost entirely from the 2008 crisis and that post-2009 returns were lower than buy and hold (unverified: snippet only). One-asset concentration. Sensitive to the day of the month used.

**Feasibility at ₹1.5 lakh.** Yes. This is the best-documented Indian adaptation in this file, with the caveats above.

**Sources.** https://samasthiti.substack.com/p/indian-edition-of-the-dual-momentum ; https://momentumlab.substack.com/p/backtesting-dual-momentum-strategy ; https://www.optimalmomentum.com/global-equities-momentum/ ; https://optimalmomentum.com/faq/

---

## 9. Paired switching: always invested in the stronger of Nifty and gold

**Rules.** Two assets, no cash leg. At each review date hold whichever had the higher return over the lookback.
- Capitalmind: 12-month return, reviewed monthly.
- TradingQnA post: 3-month return, reviewed at each quarter end.

**Instruments.** NIFTYBEES and GOLDBEES.

**Holding period.** Capitalmind: 23 trades in 17 years.

**Reported performance.**
- Capitalmind (start of 2005 to mid-2022): ₹1 lakh grew to ₹8.4 lakh versus ₹7.7 lakh for Nifty buy and hold, with visibly lower volatility; "comparable returns to the Nifty with lower volatility".
- TradingQnA user post (stated as 14 years of end-of-day data, run through ChatGPT): 16.06% CAGR, maximum drawdown 23.51%, Sharpe 0.95, versus NIFTYBEES 11.93% and 55.15% and GOLDBEES 11.43% and 24.38%. The post describes a 2008 drawdown inside a "14-year" window ending 2024, which cannot both be true; treat as anecdotal. The same post reports that replacing gold with cash cut total return from 1221.5% to 409.15%.

**Cost and capacity.** Trivial trading cost. Gold gains under 12 months at slab rate.

**Failure modes.** Both assets can fall together; no absolute filter. Edge depends on gold's strong 2008 to 2012 and 2019 to 2026 runs.

**Feasibility at ₹1.5 lakh.** Yes.

**Sources.** https://premium.capitalmind.in/2022/06/should-gold-be-in-your-long-term-portfolio/ ; https://tradingqna.com/t/dual-momentum-strategy-with-niftybees-goldbees/174470

---

## 10. Accelerating Dual Momentum (ADM)

**Rules (Engineered Portfolio, and Allocate Smartly's test; both opened).** At the close on the last trading day of the month compute a momentum score for two equity assets, the S&P 500 (SPY) and international small caps (SCZ): the sum (equivalently the average) of the 1, 3 and 6-month total returns. If SPY's score is higher and above zero, hold SPY. If SCZ's is higher and above zero, hold SCZ. Otherwise hold long-term Treasuries (TLT); optional rule: hold TLT or TIPS, whichever has the higher 1-month return. One asset, 100%. Hold until the next month end.

**India adaptation (researcher's adaptation).** Equity pair: NIFTYBEES and one of MID150BEES, JUNIORBEES or MON100. Defensive: LTGILTBEES or GOLDBEES, whichever has the higher 1-month return, or the liquid ETF.

**Holding period.** One to several months.

**Reported performance.**
- Author (mutual fund data, 1998 to February 2018, Portfolio Visualizer, no costs): USD 10,000 grew to USD 426,408 versus just under USD 40,000 in the S&P 500 and USD 80,296 for the 12-month original; maximum drawdown about 20% versus near 60%; no losing calendar year. Each tweak (shorter lookbacks, long Treasuries, small-cap international) was chosen on the same data.
- Allocate Smartly (1990 onward, net of transaction costs): very strong but "the highest portfolio volatility of any strategy that we track (buyer beware)", history limited to 1990, and a "red(ish) flag": results on other trading days of the month were much worse than month-end.

**India evidence.** None.

**Cost and capacity.** Whole-account switches; trading cost trivial; turnover and short-term tax higher than 12-month dual momentum.

**Failure modes.** Overfitting to 1998 to 2018; timing luck; long gilts as the defensive asset fail when rates rise (2022 in the US).

**Feasibility at ₹1.5 lakh.** Yes.

**Sources.** https://engineeredportfolio.com/2018/05/02/accelerating-dual-momentum-investing/ ; https://allocatesmartly.com/taa-strategy-accelerating-dual-momentum/

---

## 11. Protective Asset Allocation (PAA, Keller and Keuning)

**Rules (TrendXplorer, co-author's blog, opened).**
- Risky universe of N assets (12 in the paper: SPY, QQQ, IWM, VGK, EWJ, EEM, IYR, GSG, GLD, HYG, LQD, TLT). Safe universe: SHY and IEF (hold the one with higher momentum).
- Momentum for both timing and ranking: MOM(L) = p0 / SMA(L) - 1 with L = 12 months (the SMA uses 13 month-end prices including the current one).
- n = number of risky assets with MOM > 0. Bond fraction BF = (N - n) / (N - pf x N/4), clipped to 0..1, with protection factor pf = 0 (low), 1 (medium) or 2 (high). With pf = 2 and N = 12 the denominator is 6, so the portfolio is fully in the safe asset once six or more risky assets have non-positive momentum.
- Invest (1 - BF) equally in the top-T risky assets by MOM that have MOM > 0 (T = 6 in the preferred setting). Invest BF in the best safe asset. Monthly.

**India adaptation (researcher's adaptation).** N = 8 ETFs, T = 3, pf = 2, safe asset = better of liquid ETF and GILT5YBEES.

**Holding period.** Monthly review; mixed risky and safe allocations most of the time.

**Reported performance.** Co-author's blog: back-test December 1970 to December 2015 on synthetic monthly total-return data, no trading costs, slippage or taxes; one-year rolling win rates above 95%. A search summary cites the paper's out-of-sample result as 10.4% CAGR versus 8.2% for 60/40 over 1993 to 2015 with 0.1% costs (unverified: snippet only).

**India evidence.** None.

**Cost and capacity.** Fractions of the form k/6 and several holdings give awkward small slices: with ₹1.5 lakh and three risky holdings plus a safe leg, slices of ₹12,500 to ₹50,000. Monthly resizing of the bond fraction creates small trades that pay the ₹5 minimum and the DP fee.

**Failure modes.** Small Indian universe is mostly correlated equity ETFs, so breadth carries less information than in a 12-asset global universe. Safe asset choice matters when rates rise.

**Feasibility at ₹1.5 lakh.** Marginal: workable only with T of 2 or 3 and a no-trade band on the bond fraction.

**Sources.** https://indexswingtrader.blogspot.com/2016/04/introducing-protective-asset-allocation.html

---

## 12. Vigilant Asset Allocation (VAA, Keller and Keuning)

**Rules (TrendXplorer and Allocate Smartly, both opened).**
- Momentum filter 13612W = (12 x r1 + 4 x r3 + 2 x r6 + 1 x r12) / 4, where r_t = p0 / p_t - 1 on month-end prices. The most recent month carries 40% of the weight.
- VAA-G4 offensive universe: US equity, developed ex-US equity, emerging equity, US aggregate bonds (SPY, EFA or VEA, EEM or VWO, AGG or BND). Defensive universe: SHY, IEF, LQD.
- General form: choose top T offensive assets; b = number of offensive assets with non-positive momentum; cash fraction CF = (1/T) x floor(b x T / B), clipped to 0..1; replace the worst CF of the top T with the best defensive asset.
- Recommended T = 1, B = 1: if all four offensive assets have positive 13612W, hold 100% in the one with the highest score; if any one is non-positive, hold 100% in the defensive asset with the highest score. T = 2, B = 1 splits 50/50 between the best two and has the best risk-adjusted result per the authors.

**India adaptation (researcher's adaptation).** Offensive: NIFTYBEES, MID150BEES, MON100 (or GOLDBEES), GILT5YBEES as the "spoiler" bond. Defensive: liquid ETF, GILT5YBEES, LTGILTBEES.

**Holding period.** One month; high turnover.

**Reported performance.** Authors' back-test December 1970 to June 2017 on simulated monthly data, no costs: both VAA-G4 settings beat GEM on raw and risk-adjusted return with lower drawdowns, at the price of "substantial asset re-allocation". Allocate Smartly (1971 onward, net of costs): Sharpe 1.10 and maximum drawdown 16.1% with the aggregate-bond asset in the offensive set, falling to 0.83 and 25.2% without it; the bond asset was held in under 1% of months and acts purely as a kill switch; out-of-market about 60% of the time on average (per the DAA post). Allocate Smartly also shows a "wide disparity" in results when traded on days other than month-end.

**India evidence.** None.

**Cost and capacity.** Whole-account switches most months: trading cost about 0.07% a switch but close to 12 potential switches a year, nearly all gains short-term.

**Failure modes.** Timing luck; whipsaw from the 40% weight on the last month; dependence on one bond series as a spoiler; heavy time in bonds when bond yields are rising.

**Feasibility at ₹1.5 lakh.** Yes mechanically; tax drag high.

**Sources.** https://indexswingtrader.blogspot.com/2017/07/breadth-momentum-and-vigilant-asset.html ; https://allocatesmartly.com/vigilant-asset-allocation-dr-wouter-keller-jw-keuning/

---

## 13. Defensive Asset Allocation with a canary universe (DAA, Keller and Keuning)

**Rules (TrendXplorer, opened).**
- Same 13612W filter as VAA.
- Canary universe: emerging-market equity (VWO) and US aggregate bonds (BND). Breadth threshold B = 2.
- If both canaries have negative 13612W: 100% in the single best asset of the cash universe (SHY, IEF, LQD).
- If exactly one is negative: 50% in the top half of the usual top-T risky assets (equal weight) and 50% in the best cash asset.
- If neither is negative: 100% in the top-T risky assets, equal weight.
- DAA-G12 risky universe: SPY, IWM, QQQ, VGK, EWJ, VWO, VNQ, GSG, GLD, TLT, HYG, LQD, with T = 6 chosen on 1971 to 1993.

**India adaptation (researcher's adaptation).** Canaries: a small or mid-cap equity index (the high-beta "emerging" analogue) and a gilt index. Risky universe of 6 to 8 ETFs with T = 2 or 3.

**Holding period.** Monthly.

**Reported performance.** Authors: across the four VAA universes, 1971 to 2018, DAA's average cash fraction is "often less than half" of VAA's (below 30% instead of nearly 60%) with similar return and risk and lower turnover. Simulated monthly data, no costs. A search summary of a CXO Advisory review says DAA beat VAA on CAGR in three of four universes but with higher maximum drawdowns in 2008 to 2018 (unverified: snippet only). The canary pair was itself selected by optimisation.

**India evidence.** None.

**Cost and capacity.** Three risky holdings of ₹50,000 keep brokerage at the cap. Lower turnover than VAA.

**Failure modes.** The canary choice is a fitted parameter that may not transfer to India at all. Fast filter whipsaws.

**Feasibility at ₹1.5 lakh.** Yes with T of 2 or 3.

**Sources.** https://indexswingtrader.blogspot.com/2018/07/announcing-defensive-asset-allocation.html

---

## 14. Hybrid Asset Allocation (HAA, Keller and Keuning)

**Rules (TrendXplorer, opened).**
- Momentum 13612U = unweighted average of 1, 3, 6 and 12-month total returns, used for all three universes.
- Canary: one asset, US inflation-protected Treasuries (TIP). Defensive: BIL and IEF. Offensive (HAA-Balanced): SPY, IWM, VEA, VWO, VNQ, DBC, IEF, TLT.
- If TIP's momentum is non-positive: 100% in the better of the two defensive assets.
- Otherwise: 25% in each of the top 4 offensive assets by momentum, replacing any of those four whose own momentum is non-positive with the best defensive asset.
- Rebalance fully every month end. HAA-Simple uses SPY alone as the offensive universe.

**India adaptation (researcher's adaptation).** There is no listed Indian inflation-indexed bond ETF that I know of, so the canary must be either the US TIP series (external data) or a substitute such as a gilt index; that substitution is untested. Offensive: 6 to 8 Indian ETFs, top 3.

**Holding period.** Monthly; about seven trading months a year for the balanced version per the authors.

**Reported performance.** Authors: over 50-plus years of simulated data HAA-Balanced had one (limited) losing year and all rolling three-year returns positive, with low cash fractions. Risk-free rates, trading costs, slippage and taxes disregarded. The authors themselves say HAA-Simple "might just be a lucky shot". Designed in 2022 to 2023 after the 2022 stock-and-bond fall, so the canary choice is hindsight-informed.

**India evidence.** None.

**Cost and capacity.** Four slices of ₹37,500 with monthly full rebalancing is the costly part; use bands.

**Failure modes.** Canary not transferable; recent design; four correlated equity ETFs in India.

**Feasibility at ₹1.5 lakh.** Marginal: needs an external canary series and band rebalancing.

**Sources.** https://indexswingtrader.blogspot.com/2023/02/introducing-hybrid-asset-allocation-haa.html

---

## 15. Donchian channel breakout (20-day, 55-day)

**Rules.** Upper channel = highest price of the previous N days; lower channel = lowest price of the previous M days. Long-only form: buy when the close exceeds the upper channel; exit when the close falls below the lower channel. Stop-and-reverse form: go short on a close below the lower channel with the upper channel as the stop. Zerodha's test uses N = M = 20 on daily bars.

**Parameter range.** N in {20, 55, 100}; exit M in {10, 20, 40}.

**Instruments.** Tested on Nifty spot. Tradable long-only via NIFTYBEES and other ETFs.

**Holding period.** Weeks to months.

**Reported performance.** India, Zerodha's Sandeep Rao (Nifty daily, January 2015 to October 2025, long-and-short, long-only and short-only, no transaction costs or slippage): Sharpe ratios for long-and-short "just too bad", negative median P&L in all three variants, and the one that made money (long-only) "was in a drawdown for 5 years". Verdict: "Donchian 20 on a daily timeframe on Nifty fails badly." A forum reply notes the short side shows a reverse edge (buying dips), consistent with mean reversion at this horizon.

**Cost and capacity.** Moderate trade count; costs would worsen an already negative result.

**Failure modes.** Nifty mean-reverts at the 20-day horizon; false breakouts.

**Feasibility at ₹1.5 lakh.** Yes mechanically (long-only ETF). Evidence on Nifty is negative; untested on gold, silver, mid and small-cap ETFs.

**Sources.** https://tradingqna.com/t/trend-following-in-india-part-1-testing-donchian-s-classic-rules/188234 ; https://oxfordstrat.com/coasdfASD32/uploads/2016/01/turtle-rules.pdf

---

## 16. Turtle system (ATR units, pyramiding, 2N stop)

**Rules (Original Turtle Trading Rules, opened).**
- Volatility N = 20-day exponential average of true range: N = (19 x previous N + today's TR) / 20, seeded with a 20-day simple average. TR = max(H - L, H - previous close, previous close - L).
- Unit size = 1% of account equity / (N x value per point), so a 1N move in one unit is 1% of equity.
- System 1: enter on a break of the 20-day high (short on the 20-day low). Skip the signal if the previous 20-day breakout would have been a winner (it is a loser if price moved 2N against it before a profitable 10-day exit); a skipped signal is taken instead at the 55-day breakout. Exit on a 10-day low (long) or 10-day high (short).
- System 2: enter on a break of the 55-day high or low, always taken. Exit on a 20-day low or high.
- Add one unit every half N of favourable movement from the last fill, up to 4 units per market; 6 units in closely correlated markets, 10 in loosely correlated, 12 in one direction overall.
- Stop: 2N from entry (2% of equity per unit); when a unit is added, all stops move to 2N below the latest fill.

**India adaptation (researcher's adaptation).** Long-only on 4 to 6 ETFs. With no leverage, one unit of a low-volatility index ETF is already larger than the account: daily N near 0.8% of price implies a unit notional of about 1.25 times equity. So units must be capped by available cash, which removes pyramiding and turns the system into strategy 15 with an ATR stop.

**Holding period.** Weeks to months.

**Reported performance.** The rules document gives rules, not audited results. No Indian backtest found. See strategy 15 for the Indian breakout evidence.

**Cost and capacity.** Designed for leveraged futures across 20-plus uncorrelated markets.

**Failure modes.** Without leverage and breadth the method loses what made it work; false breakouts.

**Feasibility at ₹1.5 lakh.** Marginal: only a de-levered, single-unit version fits; futures units do not.

**Sources.** https://oxfordstrat.com/coasdfASD32/uploads/2016/01/turtle-rules.pdf

---

## 17. Keltner plus Donchian channel timing on industries (Zarattini and Antonacci, 2025 Dow Award)

**Rules (opened).** Long-only, daily.
- Donchian upper band = highest close of the last 20 days; lower = lowest close of the last 40 days.
- Keltner upper band = EMA(close, 20) + 2 x 1.4 x (20-day average of absolute daily price change); lower = EMA(close, 40) - 2 x 1.4 x (40-day average of absolute daily price change). The factor 1.4 converts average absolute change to an ATR equivalent.
- UpperBand = min(Donchian upper 20, Keltner upper 20, 2). Enter long when the close is at or above the previous day's UpperBand.
- LowerBand = max(Donchian lower 40, Keltner lower 40, 2). Trailing stop = max(previous trailing stop, today's LowerBand); it never moves down. Exit when price hits the trailing stop.
- Sizing: weight_j = (1.5% / N) / sigma_j, where sigma_j is the 14-day standard deviation of daily returns and N the number of tradable assets (a 1.5% daily portfolio volatility target split equally). Total exposure capped at 200%; scale down proportionally if exceeded. Rebalanced daily.

**India adaptation (researcher's adaptation).** 8 to 12 Nifty sector indices for signals, sector ETFs for execution; exposure capped at 100%; rebalance weekly with a no-trade band instead of daily.

**Holding period.** Weeks to months per industry.

**Reported performance.** 48 US industry portfolios, 1926 to 2024, no commissions or slippage: 18.2% a year, 12.6% volatility, Sharpe 1.39, versus the US market's 9.7%, 17.1% and 0.63; annualised alpha 10.9%; drawdown reduced by almost 60% (market maximum drawdown 84%). Uses leverage up to 200%. Replicated on 31 sector ETFs from January 2005 to March 2024 including USD 0.0035 per share commission; the authors say the strategy "remains largely profitable even with high trading costs". An unlevered version would earn materially less than the headline.

**India evidence.** None.

**Cost and capacity.** Daily volatility-target rebalancing across a dozen small positions is exactly what the ₹5 minimum and the per-sell DP fee punish. Indian sector ETFs are thin and several sectors have no ETF.

**Failure modes.** Sector ETF liquidity and tracking; many small positions; published 2024 to 2025, so no post-publication record yet.

**Feasibility at ₹1.5 lakh.** Marginal: needs a cut-down universe, weekly rebalancing and no leverage.

**Sources.** https://cmtassociation.org/wp-content/uploads/2025/10/2025-DowWinner_A-Century-of-Profitable-Trends.pdf ; https://www.optimalmomentum.com/research/

---

## 18. Supertrend, long-only (10, 3)

**Rules (Zerodha's Sandeep Rao, opened; indicator formula is the standard definition and is not restated in the source).** Supertrend with ATR period 10 and multiplier 3: bands at (H + L)/2 plus or minus 3 x ATR(10), with the active band ratcheting in the direction of the trend. Long-only: when a bar closes above the Supertrend line, buy at the next bar's open; when a bar closes below it, exit at the next bar's open and wait. The lower band is the stop.

**Timeframes tested.** Daily, 4-hour and 1-hour bars on Nifty spot (January 2015 to October 2025); 1-hour bars on Nifty and MCX GoldM continuous futures for the two-asset version.

**Instruments.** Tested on Nifty spot and GoldM futures. For this account: NIFTYBEES and GOLDBEES.

**Holding period.** Daily version: 44 long trades in about 10.8 years, so roughly three months per trade. Hourly version: shorter.

**Reported performance (India).**
- Daily Nifty, long-only: Supertrend made 44 trades with average P&L of 270 index points per trade versus 256 trades and 35 points for a price-above-8-EMA rule; smoother equity curve from 2017; higher maximum drawdown than the EMA rule.
- 4-hour: average 153 points per trade for Supertrend versus 48 for a 21-EMA rule; EMA trades nearly four times as often.
- 1-hour, Nifty plus GoldM, 50:50, long-only, no leverage, no compounding (sum of per-trade percentage returns, about 11 years to November 2025): Nifty leg 205%, gold leg 169%, combined 187%; maximum drawdown 6.6% combined versus 18.5% and 11.8%; correlation of the two legs about 0.04; return to maximum drawdown 28.32; longest drawdown 70 days. Buy and hold over the same period: Nifty 214% with a 38% drawdown, GoldM 161% with a 21% drawdown.
- Costs are not stated for these tests. The author says the examples are illustrative and that parameters should not be taken as gospel.

**Cost and capacity.** The futures version needs about ₹15.75 lakh at 2x leverage for one lot each (author's own figure), so it is out of reach. An ETF version works on daily bars; the 1-hour version needs intraday data and more trades.

**Failure modes.** Returns roughly equal buy and hold; the benefit is drawdown. Single test period, single parameter set, tool-default parameters.

**Feasibility at ₹1.5 lakh.** Yes for the daily ETF version; no for the futures version.

**Sources.** https://tradingqna.com/t/trend-following-in-india-part-2-building-a-simple-system-that-works/188483 ; https://tradingqna.com/t/trend-following-in-india-part-3-nifty-gold-strategy/188767

---

## 19. Volatility targeting overlay

**Rules.** Exposure_t = min(cap, target volatility / forecast volatility), applied to a risky asset or portfolio, remainder in cash. Forecast volatility from recent realised volatility.
- Moskowitz, Ooi and Pedersen: exponentially weighted variance with a 60-day centre of mass, annualised with 261 days (opened).
- Zarattini and Antonacci: 14-day standard deviation of daily returns (opened).
- Valuelytica's replication of a Quantpedia paper: 63-day volatility with a 20% annual cap that only reduces exposure and never levers up (opened).
- Moreira and Muir scale exposure by the inverse of the previous month's realised variance (from memory, not opened; the Alpha Architect summary I opened describes it only as conservative when recent volatility is high and levered when it is low).

**India adaptation (researcher's adaptation).** NIFTYBEES (or the output of any strategy above) with cap = 1.0 because there is no cheap leverage: exposure = min(1, 12% to 15% / 20-to-60-day realised volatility), reviewed weekly, traded only when the target changes by more than 10 percentage points.

**Holding period.** Continuous, with partial resizing.

**Reported performance.**
- Harvey, Hoyle, Korgaonkar, Rattray, Sargaison and Van Hemert (Man Group; more than 60 assets, US equities from 1926): volatility scaling raises the Sharpe ratio of equities and credit and of balanced and risk-parity portfolios, has a negligible effect for bonds, currencies and commodities, and reduces the likelihood of extreme returns and maximum drawdowns for all. The mechanism for equities is the leverage effect, which makes volatility scaling a short-term momentum overlay.
- Cederburg, O'Doherty, Wang and Yan (Journal of Financial Economics, 2020; 103 equity strategies), via Alpha Architect: in-sample alphas are real, but real-time versions "generally earn lower certainty equivalent returns and Sharpe ratios" than the unmanaged portfolios because the scaling regression is unstable. A search summary adds that managed versions had higher Sharpe in only 53 of 103 cases, 8 significantly (unverified: snippet only).

**India evidence.** None found.

**Cost and capacity.** Without leverage this can only cut exposure, so it lowers return in calm rising markets by construction and cannot add it back. Frequent small resizes are expensive at this account size.

**Failure modes.** Volatility spikes after the fall has happened (Faber: "this volatility has occurred after the markets already began declining"); de-risking at the bottom of V-shaped crashes.

**Feasibility at ₹1.5 lakh.** Yes as a capped (no-leverage) risk control with wide bands; it is not a return source.

**Sources.** https://www.man.com/maninstitute/the-impact-of-volatility-targeting ; https://alphaarchitect.com/does-portfolio-timing-based-on-volatility-signals-outperform-buy-and-hold/ ; https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf ; https://valuelytica.substack.com/p/golden-dual-momentum-rotation

---

## 20. Sector momentum rotation

**Rules (Faber, "Relative Strength Strategies for Investing", via Quantpedia, opened).** Ten sector funds. Each month rank by trailing 12-month return (tested also with 1, 3, 6, 9 months and a combination). Hold the top 3 at equal weight for one month, then repeat. Optional hedge from the same paper: add a trend-following filter to move to cash.

**India adaptation (researcher's adaptation).** Rank Nifty sector indices (Bank, PSU Bank, IT, Pharma, Auto, FMCG, Metal, Energy, Infra, Realty, Financial Services); trade the top 2 or 3 that have a liquid ETF; require the selected sector (or Nifty) to be above its 10-month SMA, else hold the liquid ETF.

**Holding period.** One month, often longer in practice.

**Reported performance.**
- US, 1928 to 2009, top 3 by 12-month return (French-Fama sectors): 13.94% a year, 18.38% volatility, maximum drawdown 46.29%, Sharpe 0.54, almost 4 points a year above buy and hold; outperformed in roughly 70% of years; worked for all lookbacks from 1 to 12 months. Excludes taxes, commissions and slippage; turnover 100% to 400% a year; the authors estimate a 50 to 150 basis-point tax cost.
- India: a SensexIQ learning page claims that ranking 11 NSE sector indices on 3-month relative strength and tilting 1.5x to the top 3 and 0.5x to the bottom 3 "delivers about 14% CAGR versus Nifty's about 12%" since 2010. No methodology, costs or data are given; treat as an unverified claim. The same page says weekly rebalancing "destroys returns via transaction costs".

**Cost and capacity.** Sector ETF spreads can be tens of basis points; three ₹50,000 positions keep brokerage at the cap; 100% to 400% turnover means almost all gains are short-term.

**Failure modes.** Equity-only: the drawdown is nearly as deep as the market's without a trend filter. Indian sectors are concentrated (Bank and Financial Services overlap heavily). Thin ETFs.

**Feasibility at ₹1.5 lakh.** Marginal: feasible with top 2 or 3 and liquid sector ETFs only; liquidity and tax are the constraints.

**Sources.** https://quantpedia.com/strategies/sector-momentum-rotational-system ; https://sensexiq.vercel.app/learn/sector-rotation-india

---

## 21. Asset-class relative-strength rotation

**Rules (Faber, via Quantpedia, opened).** Universe of about five global asset classes (equities, foreign equities, bonds, REITs, commodities). Each month rank by trailing return (1, 3, 6, 9, 12 months or their combination). Hold the top N (tested 1 to 4; top 3 is the reference) at equal weight for one month. A trend filter can be added.

**India adaptation (researcher's adaptation).** Universe: NIFTYBEES, MID150BEES, GOLDBEES, SILVERBEES, LTGILTBEES, MON100, liquid ETF. Hold top 2 by the average of 1, 3, 6 and 12-month returns; an asset ranked in the top 2 with a negative score is replaced by the liquid ETF.

**Holding period.** One to several months.

**Reported performance.** Faber, 1973 to 2009: the method "works across all measurement periods" and beats buy and hold in roughly 70% of years, by decade as well; no taxes, commissions or slippage; turnover of 70% to 100% a year. The exact return figures did not come through in the page text I could read.

**India evidence.** The Nifty and gold pair results in strategies 8 and 9 are the two-asset special case.

**Cost and capacity.** Two ₹75,000 positions: trading cost negligible.

**Failure modes.** With only six or seven assets, three of them Indian equity, "diversified momentum" is mostly an equity versus gold versus bonds call.

**Feasibility at ₹1.5 lakh.** Yes.

**Sources.** https://quantpedia.com/strategies/asset-class-momentum-rotational-system

---

## 22. Risk-on/risk-off switch to gold on a Nifty trend filter

**Rules (ValuePickr post, opened).** Hold a risk-on equity portfolio (in the post: stocks from Nifty MidSmallcap 400 plus Next 50 ranked by weighted 6, 3 and 12-month returns divided by volatility). Regime filter: if Nifty 50 breaks its weekly Supertrend, exit 100% of equity and hold 100% GOLDBEES; return to equity when Nifty is back above it.

**ETF-only form (researcher's adaptation).** Risk-on asset: MID150BEES, JUNIORBEES or a momentum-index ETF. Risk-off asset: GOLDBEES (or the better of gold and the liquid ETF by 3-month return). Filter: Nifty 50 weekly close versus weekly Supertrend (10, 3), or versus its 200-day SMA.

**Holding period.** Months.

**Reported performance.** ValuePickr poster (2018 to February 2026, end-of-day prices, gross, no taxes or slippage): about 38% CAGR, maximum drawdown 20.9% versus 34% for Nifty, Sharpe 1.51. A reply from another member: a similar strategy he tested "produced 54% CAGR in the last 10 years but only 12% CAGR in the last 20 years after taxes, brokerage and a little slippage", and eight years is too short. The stock-selection part belongs to another research area; only the regime switch is in scope here.

**Cost and capacity.** The ETF form is a whole-account switch a few times in a decade.

**Failure modes.** Period dependence is extreme (the 54% versus 12% comment). Gold is not a guaranteed hedge. Regime filter exits late in fast crashes.

**Feasibility at ₹1.5 lakh.** Yes in ETF form.

**Sources.** https://forum.valuepickr.com/t/backtesting-volatility-adjusted-momentum-with-a-gold-regime-filter-2018-2026/218153

---

## 23. Exit on drawdown from the high (20% below all-time high or 52-week high)

**Rules (MoneyWorks4me, opened).** Hold Nifty while it is less than 20% below its all-time high (variant: 52-week high). If it falls more than 20% below, switch to a liquid fund; return when it is back within 20%.

**Instruments.** NIFTYBEES and liquid ETF.

**Reported performance (India, about 21 to 22 years, before tax and brokerage).** All-time-high rule: ₹100 became ₹656 (8.9% CAGR) versus ₹1,688 (13.7%) for buy and hold. 52-week-high rule: ₹695 (9.6%) versus ₹1,571 (14%).

**Failure modes.** By construction it sells after a 20% fall and buys back higher. This is negative evidence: do not use as a timing rule.

**Feasibility at ₹1.5 lakh.** Yes mechanically; not recommended.

**Sources.** https://www.moneyworks4me.com/investmentshastra/time-the-market-or-asset-allocation/

---

## 24. Long-and-short trend following on index futures (EMA or Supertrend stop-and-reverse)

**Rules (Zerodha's Sandeep Rao, opened).** Always in the market. EMA version: long when price closes above the EMA, short when it closes below. EMA length 8 on daily bars, 21 on 4-hour, 50 on 1-hour. Supertrend (10, 3) version: long on a close above the band, short on a close below.

**Reported performance (India, Nifty spot, January 2015 to October 2025, no costs stated).**
- Daily: the short side loses for both indicators; "it makes little sense to look at the short side, especially on daily timeframes".
- 4-hour: Supertrend shorts lose about 4,000 points; EMA shorts make about 700.
- 1-hour: EMA shorts make about 4,700 points versus 1,400 for Supertrend; EMA win rate 29% versus 42% for Supertrend on longs.
- Gross points rise as the timeframe shortens, with many more trades.

**Cost and capacity.** One Nifty lot (65) is about ₹16.7 lakh notional at the index level cited in section 0.4, with margin above the account size; futures STT is now 0.05% on the sell side; the hourly version trades often.

**Feasibility at ₹1.5 lakh.** No. Lot size and margin rule it out, and the daily short side has negative evidence anyway.

**Sources.** https://tradingqna.com/t/trend-following-in-india-part-2-building-a-simple-system-that-works/188483 ; https://www.angelone.in/news/market-updates/nse-revises-lot-sizes-for-index-derivatives-from-december-2025-nifty-lot-size-to-reduce-to-65 ; https://www.angelone.in/exchange-transaction-charges

---

## Negative or cautionary evidence

1. **On Indian large-cap indices the edge is drawdown reduction, not return.** MoneyWorks4me: 200-day rule 13.4% versus 13.5% buy and hold over 22 years before costs. Capitalmind: buy and hold beat the timed strategy in 12 of 16 years; all the benefit came in 2008, 2011 and 2020. Market Shack: golden cross as an entry gate gave 11.98% versus 11.99% XIRR over 30.5 years.
2. **Taxes and costs remove gross profits.** Mitra (2011): Indian moving-average profits "cannot be exploited fully due to real world transaction costs". Freefincal assumes a 20% haircut on the tactical corpus. A ValuePickr member reports a gold-regime momentum strategy falling from 54% CAGR (10 years, gross) to 12% (20 years, net). Most Indian blog backtests quoted above ignore both.
3. **Trend rules are regime-dependent.** Slivka et al.: 80 EMA rules worked in the 2008 decline and "far less so, or not at all" in rising, mixed or trendless markets. Zakamulin's work (unverified: snippet only) argues reported moving-average timing performance carries substantial data-mining bias, that out-of-sample results are much weaker, that there was no significant outperformance in the second half of his sample, and that 1926 to 2012 outperformance was concentrated in four short episodes.
4. **Classic short-horizon trend rules fail on Nifty daily data.** Zerodha's tests: 20-day Donchian and 5x20 SMA are "to be dumped"; the short side loses on daily bars; an 8-EMA rule made 256 trades for 35 points each before costs.
5. **V-shaped crashes break slow rules.** Freefincal: the 6x12-month rule failed on Sensex, Next 50 and Midcap 150 after March 2020 in a way "122 years" of S&P 500 data never showed, yet did not fail on Smallcap 250. The outcome is arbitrary across indices.
6. **Fast tactical models show timing luck and overfitting flags.** Allocate Smartly: VAA results vary widely by trading day; ADM is the most volatile strategy they track and looks worse on non-month-end days; VAA depends on a bond "spoiler" asset held under 1% of the time. HAA's authors call their own single-asset version a possible "lucky shot". ADM's parameters were all chosen on 1998 to 2018 data.
7. **Volatility management does not reliably help in real time.** Cederburg et al.: out-of-sample volatility-managed portfolios generally underperform their unmanaged versions. Without leverage in India it can only reduce exposure.
8. **Exit-on-drawdown rules destroy value.** MoneyWorks4me: 8.9% versus 13.7% and 9.6% versus 14%.
9. **The strongest global evidence does not transfer to this account.** Time-series momentum results come from 58 to 67 futures markets, long and short, levered and volatility-scaled. Hurst et al. net Sharpe is 0.77 over 134 years and the authors discuss 0.4 going forward. A long-only portfolio of four to eight Indian ETFs captures a small part of that.
10. **Indian dual-momentum results lean on a few episodes.** The Nifty and gold strategies owe much to 2008 and to gold's two strong runs; a forum tester found post-2009 returns below buy and hold (unverified: snippet only). MomentumLab's 18.79% is ten years and one parameter set.
11. **International ETFs are distorted.** MON100's premium to NAV has swung between a discount and 27.7%; a price-momentum signal on it is contaminated.
12. **Derivatives-based trend following is not available at ₹1.5 lakh.** One Nifty lot is about 11 times the account.

## Open questions

1. STT on ETF units at Angel One: is it 0.001% sell-only for equity ETFs and nil for gold, liquid and gilt ETFs, or the 0.1% delivery rate shown on the pricing page? Confirm from a contract note. It changes round-trip cost fourfold.
2. Tax treatment of MON100 and other international ETFs, and of a growth-NAV liquid ETF versus LIQUIDBEES payouts, for FY 2026-27.
3. Which total-return series to use for backtests before each ETF existed (Nifty 50 TRI, Next 50 TRI, Midcap 150 TRI, INR gold, a gilt index, an overnight-rate index), and how much history the dataset team's cut-off allows. GOLDBEES starts March 2007; silver and midcap ETFs are much more recent.
4. After 20% short-term tax and realistic costs, does any timed strategy beat a static, annually rebalanced Nifty, gold and gilt mix on post-tax CAGR, or only on drawdown? This is the central test.
5. Day-of-month sensitivity: every monthly rule should be run on all 20 or so possible rebalance days to measure timing luck before any ranking.
6. Parameter stability: 200-day versus 100-day versus 50-day on Nifty (Capitalmind found shorter better on return, Freefloat likewise); is that robust out of sample or a 2008 and 2020 artefact?
7. Do breakout and trend rules work better on gold, silver, mid-cap and small-cap ETFs than on Nifty 50, as the Zerodha author and forum replies suggest? No published Indian test found.
8. Canary assets for India: is there any Indian series (small-cap index, gilt index, USD/INR, India VIX) with the early-warning property the Keller papers attribute to emerging equities, aggregate bonds and TIPS? Untested. India VIX regime filters are widely discussed but I found no source to cite.
9. Liquidity and spread of sector, gilt and silver ETFs at ₹12,000 to ₹50,000 order sizes during stressed days; whether limit orders at iNAV fill.
10. Whether compounding at this size is helped by using the ₹1.25 lakh long-term exemption deliberately (for example a rule that avoids selling equity ETF lots just short of 12 months).
11. Published strategies I know of but could not open this session, so they are not carded: Adaptive Asset Allocation (momentum plus minimum variance), Keller's Bold Asset Allocation, Generalized Protective Momentum and Flexible Asset Allocation, Clenow's "Following the Trend" core rules, Gayed and Bilello's "Leverage for the Long Run", Antonacci's absolute-momentum paper tables, Zakamulin's papers. All are from memory, not opened.
12. Edelweiss Balanced Advantage Fund and similar funds are a live Indian record of trend-driven allocation; their NAV history could serve as an out-of-sample sanity check for strategy 6.
