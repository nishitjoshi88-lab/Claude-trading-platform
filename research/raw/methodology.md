# Backtesting methodology and realistic expectations (India, ₹1.5 lakh, Angel One)

Research date: 2026-11-10. Area: overfitting and multiple testing, post-publication decay, validation schemes, data and execution pitfalls specific to NSE, hard evidence on retail outcomes, and what returns a systematic account can realistically expect after costs.

How this was researched. Ten web searches ran before the shared search budget for this workflow turn was exhausted (four further searches, on the Reality Check and SPA papers, the Harvey-Liu haircut, the closing auction and the 2026 STT rates, were refused). Everything after that came from opening primary documents directly at known URLs with `fetch_text.py`: SEBI study PDFs, NSE and NSE Clearing rule pages, NSE Indices methodology and factsheets, the Angel One and Zerodha charge pages, Zerodha bulletins, and the original papers (author or NBER copies). Every row in the Facts table says whether the source was opened. Items I could not open are marked "(unverified ...)". One search result (a mirror of a Wikipedia page on cavac.at) contained text telling the reader to ignore its instructions and do something unrelated; it was ignored and the page was not used.

All formulas in section 3 were implemented and run (script kept outside the repo); the deflated Sharpe code reproduces the worked example in Bailey and López de Prado (SR0 = 0.1132, DSR = 0.9004) and the multiple-testing code reproduces the Harvey-Liu-Zhu worked example (3, 4 and 6 discoveries under Bonferroni, Holm and BHY).

---

## 1. Headline findings

1. **Nine in ten individual F&O traders in India lose money, every year, and experience does not help.** SEBI's August 2026 study: 87.7% of individual traders lost in FY26 (90.9% in FY25), aggregate net loss ₹91,685 crore, average ₹1.17 lakh per trader. Among traders active in all five years FY22-FY26, 0.5% were profitable every year and 65.6% lost every year. The loss share rises with years of participation (91.0% after one year, 96.5% after four).
2. **An account the size of ours sits in a bucket where 86% lost and the average loss exceeded the capital.** Traders whose peak margin was ₹1-5 lakh: 86.4% loss-makers in FY26, average P&L -₹2.96 lakh (SEBI sample of 4,995 traders).
3. **Automation is not an edge by itself.** Individuals flagged as "algo" (15% of traders in FY26, a flag that also catches broker auto-square-off) had a gross loss of ₹51,728 crore over FY25-FY26, about 30% of all individual gross losses in those two years. Proprietary desks and FPIs made 99% of their profit through algos; the top 10 prop firms took 75% of prop profit.
4. **Option buying is where the losses are; option selling hides tail risk.** "Only option buyers" (93% of traders): 89.9% lose, median return on peak margin -114%. "Majorly option sellers": only 43.8% lose, but the losers average -₹51.7 lakh, and the group's median return on capital is +1%.
5. **Intraday cash trading: 71% lose (FY23); 80% of those making more than 500 trades a year lose.** Trading costs add 57% on top of the trading losses of loss-makers.
6. **A backtest Sharpe of 1.0 is what pure noise produces.** With 10 years of daily data, the best of 100 independent zero-skill trials has an expected annualised Sharpe of 0.80; the best of 1,000 has 1.03. With 5 years the figures are 1.13 and 1.46. Any Sharpe we report must be deflated by the number of things we tried.
7. **Hurdles from the literature.** t-statistic above 3.0 for a new factor (Harvey, Liu, Zhu). That needs an annualised net Sharpe of 0.95 over 10 years or 1.34 over 5 years. Sharpe ratios below 0.4 deserve a haircut above 50%; above 1.0 the haircut is at most 25% (Harvey, Liu).
8. **Published edges shrink.** Returns of 97 published predictors are 26% lower out of sample and 58% lower after publication (McLean, Pontiff). In India the pattern is visible in NSE's own factor indices: Nifty200 Momentum 30 shows 18.05% total-return CAGR since its 2005 base date (mostly back-filled; the index was launched in August 2020) but 7.93% over the last five live years against 6.70% for Nifty 50.
9. **Costs at ₹1.5 lakh are dominated by fixed charges on small tickets.** Using Angel One's November 2026 rates, a delivery round trip costs 0.62% on a ₹15,000 position and 0.93% on ₹5,000 (the ₹20 + GST DP charge on each sell is the main culprit); intraday equity costs 0.13% on ₹50,000; one Nifty option lot costs about ₹50-80 round trip, which is 1-4% of a ₹20-100 premium.
10. **One Nifty future is out of reach.** Lot size 65 (derived from the freeze-quantity table), minimum contract value ₹15 lakh at introduction, no intraday leverage on F&O (1x SPAN + exposure). Notional ≈ ₹15-16 lakh, about ten times the account.
11. **Market mechanics changed in 2026 and change again on 7 December 2026.** A closing auction session now sets the close of F&O stocks (continuous trading in those stocks ends at 15:15); from 7 December 2026 all stocks trade to 15:30, the auction runs 15:30-15:40, and F&O final settlement goes back to the 15:00-15:30 VWAP. Derivatives expire on Tuesday. STT on futures is 0.05% and on option premium 0.15%.

---

## 2. Facts

Confidence: **high** = primary source opened and read; **medium** = reputable secondary source opened, or primary text ambiguous; **low** = from memory or snippet only, not opened. "Derived" means computed by me from verified inputs with the formula given in section 3.

### 2.1 Retail outcomes in India (SEBI)

| claim | value | effective date | source URL | confidence |
|---|---|---|---|---|
| Individual F&O traders with a net loss | FY26 87.7% (82.1% before costs); FY25 90.9%; FY24 91.1%; FY23 91.5%; FY22 90.2% | FY22-FY26 | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf | high |
| Aggregate net loss of individual F&O traders | FY26 ₹91,685 cr; FY25 ₹1,11,788 cr (revised, 15 brokers; ₹1,05,603 cr in the earlier 13-broker sample); FY24 ₹74,812 cr; FY23 ₹65,747 cr; FY22 ₹40,824 cr; five-year total ≈ ₹3.85 lakh cr | FY22-FY26 | same; and https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1751900271726.pdf | high |
| Average net loss per individual F&O trader | FY26 ₹1.17 lakh; FY25 ₹1.14 lakh; FY24 ₹0.87 lakh; FY23 ₹1.13 lakh; FY22 ₹0.96 lakh | FY22-FY26 | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf | high |
| Average loss of a loss-maker vs average profit of a profit-maker | ₹1.47 lakh vs ₹1.22 lakh | FY26 | same | high |
| Two-year outcome FY25-FY26 | 122.6 lakh unique traders; 91.0% net losers; net loss ₹2.03 lakh cr; about 1.1% earned more than ₹1 lakh | FY25-FY26 | same | high |
| Three-year outcome FY22-FY24 | 1.13 crore traders; ₹1.81 lakh cr lost; 92.8% losers; 7.2% profitable; 1% earned more than ₹1 lakh | FY22-FY24 | https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1727085659479.pdf | high |
| Loss-makers by product | FY26: index options 87%, stock options 76%, stock futures 64%, index futures 62%; all futures 66.0% vs all options 87.7% | FY26 | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf | high |
| Traders who used only futures | 0.92 lakh traders, 67.3% losers, average P&L -₹2,94,425 | FY25-FY26 | same | high |
| Loss-makers by capital (peak margin) | under ₹1 lakh: 90.2%, average loss ₹0.44 lakh; ₹1-5 lakh: 86.4%, average P&L -₹2,96,356; ₹5-10 lakh: 76.3%; ₹10 lakh-1 cr: 67.6% | FY26 (random sample, n = 4,995) | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233601328.pdf | high |
| Outcome by style | only option buyers (93% of traders): 89.9% lose, median return on peak margin -114%; majorly option buyers: 75.2%, -15%; majorly futures: 60.9%, -13%; majorly option sellers: 43.8% lose, median +1%, average loss of losers ₹51.7 lakh | FY26 (sample; seller and futures groups are small, 105 and 46 traders) | same | high |
| Experience does not help | loss share 91.0% (1 consecutive year), 94.4% (2), 96.0% (3), 96.5% (4), 95.3% (5); of traders active all of FY22-FY26, 0.5% profitable every year, 65.6% lost every year | FY22-FY26 | same | high |
| Persistence of losses | 90-92% of traders who lost in each of the previous two years lost again the next year | FY22-FY26 | same | high |
| Activity and losses | traders active more than 100 days: 42% of traders, 94% of turnover, 87% of losses | FY26 | same | high |
| Quarterly asymmetry | 15.4% of 4.02 crore trader-quarters profitable; median winning quarter ₹4,366, median losing quarter ₹10,525 | FY25-FY26 | same | high |
| Individuals flagged "algo" | 15% of 84.2 lakh traders in FY26 (flag includes broker auto-square-off); gross P&L over FY25-FY26 -₹51,728 cr vs -₹1,18,396 cr for non-algo individuals | FY25-FY26 | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf (chart 20) | high |
| Who wins | FY26 gross trading profit: proprietary ≈ ₹44,000 cr, FPIs ≈ ₹14,000 cr; 99% of prop and FPI profit from algo entities; top 10 prop entities earn about 75% of prop profit | FY26 | same | high |
| Transaction costs paid by individuals in F&O | ≈ ₹24,859 cr; ₹31,628 per trader; brokerage 44.3%, STT 26.7%, exchange fees 15.8%, GST 11.0%, stamp duty 1.3%, SEBI fee 0.9% | FY26 | same | high |
| Costs relative to results | costs = 35% of gross losses of loss-makers and 21% of gross profits of profit-makers; 4.4 lakh traders with a gross profit became net losers after costs | FY26 | same | high |
| Expiry-day concentration | 59% of index-option turnover on the expiry day itself, 97% within seven days of expiry (70% and 98% in FY25) | FY26 | same | high |
| Intraday equity cash traders with a net loss | 71% (FY23), 69% (FY22), 65% (FY19); 80% for those with more than 500 trades a year; 76% for turnover above ₹1 cr | FY23 | https://www.sebi.gov.in/sebi_data/attachdocs/jul-2024/1721818140715.pdf | high |
| Intraday cash average outcomes | average P/L -₹2,069; loss-makers average -₹5,371; profit-makers +₹5,989; more than 500 trades: average loss ₹61,394; turnover above ₹1 cr: average -₹34,977 | FY23 | same | high |
| Intraday cash cost drag | loss-makers paid costs equal to 57% of their trading losses; profit-makers paid 19% of profits; after 3 years' experience 54% still lose | FY23 | same | high |
| SEBI measures in index derivatives | weekly expiries limited to one index per exchange from 20 Nov 2024; contract size raised from 2 Jan 2025; upfront collection of option premium and no calendar-spread benefit on expiry day from 10 Feb 2025; intraday position-limit monitoring from 1 Apr 2025 | 2024-2025 | https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1751900271726.pdf | high |

### 2.2 Retail outcomes elsewhere

| claim | value | effective date | source URL | confidence |
|---|---|---|---|---|
| Taiwan day traders, 1992-2006 | about 360,000 a year; 13-15% profitable net of fees in a typical year; fewer than 1% (about 1,000) predictably profitable; top 500 earn 28.1 bps a day net, bottom group -34.2 bps | 1992-2006 | https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trading%20Skill%20110523.pdf | high |
| Brazil index-futures day traders | 97% of those who persisted more than 300 days lost; 1.1% earned more than the minimum wage (Chague, De-Losso, Giovannetti 2020) | 2013-2015 | cited in https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf (SSRN copy blocked) | medium |
| Regulator loss-rate disclosures | EU CFDs 74-89% (ESMA 2018); UK CFDs about 82% (FCA 2016); Australia CFDs about 68% (ASIC 2026); US retail forex about 67%; Korea KOSPI 200 futures about 75% | various | same SEBI literature table | medium |

### 2.3 Statistical hurdles

| claim | value | effective date | source URL | confidence |
|---|---|---|---|---|
| t-statistic hurdle for a new factor | above 3.0; BHY benchmark 2.78 at 5% and 3.39 at 1%; Bonferroni 3.78 (2012); 3.18 at 5% once unpublished tests are allowed for | paper 2014/2016 | https://www.nber.org/system/files/working_papers/w20592/w20592.pdf | high |
| Factors catalogued | 316 from 313 papers | to 2012 | same | high |
| Replication failure rate | 286 of 447 anomalies (64%) insignificant at 5% with microcaps controlled; 380 (85%) fail t ≥ 3 | 2017 | https://www.nber.org/papers/w23394 | high (abstract) |
| Counter-evidence | Bayesian replication study: majority of factors replicate, cluster into 13 themes, work in 93 countries | 2021 | https://www.nber.org/papers/w28432 | high (abstract) |
| Counter-evidence | Publication-bias shrinkage only 10-15% of in-sample mean return; false discovery rate below 10%; returns 30-50% weaker in alternative portfolio constructions | 2022-2023 | https://arxiv.org/abs/2209.13623 | high (abstract) |
| Sharpe to t-statistic | t = annualised Sharpe × sqrt(years). Example: Sharpe 0.92 over 10 years gives t = 2.91; with 200 strategies tried, Bonferroni requires t ≥ 3.66 | 2014 | https://people.duke.edu/~charvey/Research/Published_Papers/P116_Evaluating_trading_strategies.pdf | high |
| Sharpe haircut | "common practice" is 50%; correct haircut is nonlinear: above 50% when annualised Sharpe is under 0.4, at most 25% when above 1.0 | 2015 | https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF | high |
| Expected best Sharpe from zero-skill trials | 10 years daily: 0.50 (10 trials), 0.72 (50), 0.80 (100), 0.97 (500), 1.03 (1,000). 5 years: 0.70, 1.02, 1.13, 1.37, 1.46. 3 years: 0.91, 1.31, 1.46, 1.76, 1.88 | n/a | derived from eq. 1 of https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf | high (derived, code checked against paper example) |
| Deflated Sharpe worked example | annual Sharpe 2.5, 5 years daily, 100 trials, trial-Sharpe variance 0.5, skew -3, kurtosis 10 gives DSR 0.9004 (not significant at 95%); passes only if trials ≤ 46 | 2014 | same | high |
| Minimum backtest length | years needed so that the best of N zero-skill trials is not expected to reach Sharpe 1: N=10: 2.5; N=45: 5.0; N=100: 6.4; N=1,000: 10.6 | n/a | derived; matches the "5 years allows at most 45 trials" statement of Bailey, Borwein, López de Prado, Zhu (2014), which I could not open (AMS returned 403) | medium |
| Minimum track record to show Sharpe > 0 at 95% | annual Sharpe 0.5: 10.8 years; 1.0: 2.7 years; 1.5: 1.2 years; 2.0: 0.7 years (normal returns; longer with negative skew) | n/a | derived by inverting the PSR formula | high (derived) |
| PBO via CSCV | split T rows into S even blocks, all C(S, S/2) train/test combinations; S = 16 gives C(16,8) = 12,870 (the paper's text prints 12,780); PBO = share of combinations where the in-sample best ranks below the out-of-sample median; paper's customary rejection level is PBO above 0.05 | 2014 | https://carmamaths.org/jon/backtest2.pdf | high |
| Combinatorial purged CV | N groups, k test groups: C(N,k) splits, k/N × C(N,k) backtest paths (N=6, k=2: 15 splits, 5 paths; skfolio default 10 and 8: 45 splits, 36 paths) | 2018 | https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html | high (library doc; book not opened) |
| Reality Check settings | stationary bootstrap, example smoothing parameter q = 0.1 (mean block 10), 500 or 1,000 resamples | 2000 | https://www.ssc.wisc.edu/~bhansen/718/White2000.pdf | high |
| SPA in software | `arch.bootstrap.SPA(benchmark, models, block_size=None (sqrt(T)), reps=1000, bootstrap='stationary', studentize=True)`; inputs are losses; report the "consistent" p-value | arch 7.2.0 | https://arch.readthedocs.io/en/latest/multiple-comparison/generated/arch.bootstrap.SPA.html | high |

### 2.4 Decay after publication and after launch

| claim | value | effective date | source URL | confidence |
|---|---|---|---|---|
| Decay of published predictors | 97 predictors: long-short return 26% lower out of sample (upper bound on data mining), 58% lower after publication; 32% attributed to informed trading; decay larger for predictors with higher in-sample returns and t-stats, and for those built only from price and volume | 2016 | https://gwern.net/doc/economics/2016-mclean.pdf | high |
| Eight popular factors | 5.8% a year before publication, 2.4% after (Arnott, Beck, Kalesnik 2016) | 2016 | quoted in https://people.duke.edu/~charvey/Research/Published_Papers/P138_A_backtesting_protocol.pdf | medium |
| Costs and turnover | anomalies with one-sided monthly turnover under 50% mostly keep significant net spreads; few with higher turnover do | 2014 | https://www.nber.org/papers/w20721 | high (abstract) |
| NSE factor indices, total return CAGR, 5 years to 30 Oct 2026 vs since base date | Nifty 50: 6.70% vs 12.15% (base 1995). Nifty200 Momentum 30: 7.93% vs 18.05% (base Apr 2005, launched 25 Aug 2020). Nifty Alpha 50: 11.56% vs 19.98% (base Dec 2003, launched 19 Nov 2012). Nifty Low Volatility 50: 9.08% vs 16.47% (base Dec 2003, launched 19 Nov 2012). Nifty200 Quality 30: 6.96% vs 16.58% (base Apr 2005, launched 17 Apr 2018). Nifty100 Alpha 30: 7.08% vs 15.22% (base Apr 2005, launched 28 Jun 2019). Nifty50 Equal Weight: 10.94% vs 13.73% (base 1995, launched 13 Apr 2017) | 30 Oct 2026 | https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf and sibling factsheets (ind_nifty50, Factsheet_Nifty_Alpha50, Factsheet_Nifty_Low_Volatility50, Factsheet_Nifty200_Quality30, Factsheet_Nifty100_Alpha30, Factsheet_Nifty50_Equal_Weight) | high for the figures; the PDF text runs the 5-year and since-inception price-return numbers together, so I relied on the total-return row |
| Time-series momentum | Moskowitz-Ooi-Pedersen results are gross of transaction costs (58 futures) | 2012 | https://quantpedia.com/strategies/time-series-momentum-effect/ | high |
| Live vs backtest Sharpe of bank "alternative beta" products | median deterioration about 73% (Suhonen, Lennkh, Perez 2017) | 2017 | (unverified: from memory, not opened) | low |
| Crowd-sourced algorithms | backtest Sharpe explained under 2.5% of out-of-sample variation across 888 Quantopian strategies (Wiecki et al. 2016) | 2016 | (unverified: from memory; SSRN blocked) | low |

### 2.5 Market rules a simulator needs (NSE)

| claim | value | effective date | source URL | confidence |
|---|---|---|---|---|
| Cash market sessions | pre-open 09:00-09:08; normal 09:15-15:30; post-close ("closing session") 15:40-16:00; block windows 08:45-09:00 and 14:05-14:20 | page as of Nov 2026 | https://www.nseindia.com/market-data/market-timings | high |
| Closing Auction Session (CAS), phase 1 | applies to stocks with derivatives. Continuous trading in those stocks stops at 15:15; reference price = VWAP 15:00-15:15; order entry 15:20-15:30 (market orders only until 15:25, random close in last 2 minutes); matching 15:30-15:35; price band ±3% of reference; no stop-loss or iceberg orders; post-close 15:50-16:00. Non-CAS stocks trade 09:15-15:30. Equity derivatives 09:15-15:40 | NSE page updated 12 Aug 2026; go-live date not confirmed from a document I opened | https://www.nseindia.com/static/products-services/closing-auction-session | high for rules, low for start date |
| CAS and settlement changes | from 7 Dec 2026: all stocks trade to 15:30; CAS 15:30-15:40 (market and limit orders 15:31-15:36, then limit only, random close 15:38-15:40); F&O final settlement price = VWAP 15:00-15:30 instead of CAS price; index and stock F&O trade to 15:45; expiring index contracts stop at 15:30 on expiry day | 7 Dec 2026 | https://zerodha.com/marketintel/bulletin/461085/changes-to-closing-auction-session-cas-from-december-7-2026 | medium (broker bulletin summarising SEBI circular) |
| Stock price bands | 2%, 5% or 10% for specified scrips; 20% for all others; no fixed band for stocks with derivatives, which instead have a 10% operating range | page updated 12 Jan 2023 | https://www.nseindia.com/products-services/equity-market-price-bands | high |
| Market-wide circuit breakers | on Nifty 50 or Sensex moves of 10%, 15%, 20%. 10%: 45-minute halt before 13:00, 15 minutes 13:00-14:30, none after 14:30. 15%: 1 h 45 min before 13:00, 45 min 13:00-14:00, rest of day after 14:00. 20%: rest of day. Reopen with a 15-minute call auction | since 2013 | https://www.nseindia.com/products-services/equity-market-circuit-breakers | high |
| Settlement | T+1 rolling; optional T+0 for eligible securities (trading 09:15-13:30) since 28 Mar 2024 | current | https://www.nseclearing.in/clearing-settlement/capital-market/settlement-cycle and https://www.nseindia.com/products-services/t0-settlement-cycle | high |
| Failure to deliver | buy-in auction on T+1 at 14:30; valuation debit at 120% of settlement price; if not bought in, close-out at the higher of the highest price from trade day to auction day or 20% above the auction-day settlement price | current | https://www.nseclearing.in/clearing-settlement/capital-market/shortages-handling | high |
| Short selling in cash | intraday only; a short not covered by the close becomes a short delivery and goes to auction; overnight shorts only through futures or options (or stock borrowing) | current | https://zerodha.com/varsity/chapter/shorting/ | high |
| Derivatives expiry day | all NSE index and stock derivatives expire on Tuesday (last Tuesday for monthlies; previous trading day if a holiday) | current; circular NSE/FAOP/68747 (date of switch from Thursday not confirmed; SEBI's July 2025 study still showed NSE on Thursday) | https://www.nseindia.com/products-services/equity-derivatives-contract-specifications | high |
| Weekly options | only Nifty 50 has weekly expiries on NSE (4 weekly plus 3 monthly); Bank Nifty, Fin Nifty, Midcap Select, Nifty Next 50 are monthly | current | same | high |
| Minimum contract value | not less than ₹15 lakh at introduction | current | https://www.nseindia.com/products-services/equity-derivatives-nifty50 | high |
| Lot sizes | Nifty 65; Bank Nifty 30; Fin Nifty 60; Midcap Select 120; Nifty Next 50 25 (old freeze quantity ÷ old lot count; the new limits give the same sizes after rounding down to whole lots) | Nov 2026 | derived from https://zerodha.com/marketintel/bulletin/462093/quantity-freeze-limits-for-indices-from-november-02-2026 | medium (derived; confirm against NSE_FO_contract file) |
| Quantity freeze | Nifty 1,800 (27 lots); Bank Nifty 900 (30 lots); Fin Nifty 1,800; Midcap Select 2,800; Nifty Next 50 600 | 2 Nov 2026 | same | medium |
| Tick size | index futures 0.05 up to index level 15,000, 0.10 for 15,000-30,000, 0.20 above 30,000; index options 0.05; stock futures same as the stock | current | https://www.nseindia.com/products-services/equity-derivatives-contract-specifications | medium (table text was flattened) |
| Stock eligibility for F&O | top 500 by market cap and traded value; median quarter-sigma order size ≥ ₹75 lakh; market-wide position limit ≥ ₹1,500 cr; average daily delivery value ≥ ₹35 cr | SEBI circular 30 Aug 2024 | https://www.nseindia.com/products-services/equity-derivatives-selection-criteria | high |
| Index reconstitution | Nifty 50 and broad indices reviewed semi-annually on six months of data ending 31 January and 31 July; changes effective from the last trading day of March and September; four weeks' notice; ad hoc changes on mergers, delisting, suspension, F&O exclusion | methodology Sept 2026 | https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf | high |
| Nifty 50 liquidity screen | average impact cost ≤ 0.50% for a ₹10 crore basket on 90% of observations over six months; must be in F&O | methodology Sept 2026 | same | high |
| Dividend dates | under T+1 the ex-date is normally the record date; price falls by roughly the dividend on ex-date; splits and bonuses rescale price and quantity | current | https://zerodha.com/varsity/chapter/five-corporate-actions-and-its-impact-on-stock-prices/ | high |
| Intraday leverage (broker, not exchange) | equity intraday 5x (20% margin); index and stock F&O 1x (full SPAN + exposure) | 9 Nov 2026, Zerodha | https://zerodha.com/marketintel/bulletin/249809/latest-intraday-leverages-mis-bo-co | high for Zerodha; Angel One's own table not opened |
| Intraday auto square-off (Zerodha) | CAS stocks 15:12; other stocks 15:25; derivatives 15:26 | 9 Nov 2026 | same | high for Zerodha; Angel One times not opened |
| Trading calendar | 10 Nov 2026 (Diwali Balipratipada) is a trading holiday; Muhurat session held for Diwali | Nov 2026 | https://zerodha.com/marketintel/bulletin/ | high |
| Nifty 50 level | 25,044.65 close on 9 Nov 2026 per NSE circuit page; the 30 Oct 2026 factsheet returns imply roughly 23,050 on that date | Nov 2026 | https://www.nseindia.com/products-services/equity-market-circuit-breakers ; https://www.niftyindices.com/Factsheet/ind_nifty50.pdf | medium (the two do not reconcile easily; see Open questions) |
| Close price of non-CAS stocks | VWAP of the last 30 minutes of trading (not the last trade) | long-standing | (unverified: from memory; NSE page not located) | low |
| Stock F&O settlement | physical delivery at expiry | since 2019 | (unverified: from memory) | low |
| Retail algo rules | SEBI framework of Feb 2025: API orders tagged with an exchange algo ID, static IP whitelisting, registration needed above an orders-per-second threshold | 2025-2026 | (unverified: from memory; confirm with the broker-API researcher) | low |

### 2.6 Charges (Angel One, statutory) as displayed on 10 Nov 2026

| claim | value | effective date | source URL | confidence |
|---|---|---|---|---|
| Angel One brokerage, equity delivery | lower of ₹20 or 0.1% per executed order, minimum ₹5 | page as of 10 Nov 2026 | https://www.angelone.in/exchange-transaction-charges | high |
| Angel One brokerage, equity intraday | lower of ₹20 or 0.1% per executed order, minimum ₹5 | same | same | high |
| Angel One brokerage, F&O | ₹20 per executed order (also on expired, exercised and assigned options) | same | same | high |
| STT, equity delivery | 0.1% on buy and on sell | current | same; https://zerodha.com/charges/ | high |
| STT, equity intraday | 0.025% on sell | current | same | high |
| STT, futures | 0.05% on sell | current rate; date of the increase from 0.02% not confirmed (I believe 1 Apr 2026) | same | high for rate, low for date |
| STT, options | 0.15% of premium on sell; 0.15% of intrinsic value on exercise | current rate; date of increase from 0.1% not confirmed | same | high for rate, low for date |
| Earlier STT step | rates were raised from 1 Oct 2024; STT paid by individuals in F&O rose 35% in FY26 | 1 Oct 2024 | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf | high |
| NSE transaction charge | equity 0.0030699%; futures 0.0018299%; options 0.0355299% of premium (each side) | current | https://www.angelone.in/exchange-transaction-charges | high |
| SEBI turnover fee | ₹10 per crore | current | same | high |
| Stamp duty (buy side) | delivery 0.015%; intraday 0.003%; futures 0.002%; options 0.003% of premium | current | same | high |
| GST | 18% on brokerage + transaction + SEBI (+ IPFT) charges | current | same | high |
| NSE IPFT | 0.0000001% (₹0.01 per crore) | current | same | high |
| DP charge on delivery sells | ₹20 + GST per ISIN per day (Angel One); Zerodha ₹15.34 all-in | current | same; https://zerodha.com/charges/ | high |
| Account maintenance | BSDA: nil up to ₹4 lakh of holdings, ₹100 + GST a year for ₹4-10 lakh; non-BSDA ₹60 + GST per quarter; free first year | current | https://www.angelone.in/exchange-transaction-charges | high |
| Interest | MTF 0.041% per day; debit balance 0.049% per day; cash-collateral shortfall above ₹50,000: 0.0342% per day | current | same | high |
| Other | call-and-trade ₹20 per order; auto square-off charged as normal brokerage; margin pledge ₹20 + GST per ISIN | current | same | high |
| Round-trip cost, delivery, Angel One (derived) | ₹5,000: 0.93%; ₹10,000: 0.69%; ₹15,000: 0.62%; ₹30,000: 0.46%; ₹50,000: 0.36%; ₹1,50,000: 0.27% (0.25-0.46% without the DP charge) | Nov 2026 | derived from the rows above | high (derived) |
| Round-trip cost, intraday equity (derived) | ₹10,000: 0.27%; ₹25,000: 0.22%; ₹50,000: 0.13%; ₹1,00,000: 0.08%; ₹7,50,000: 0.04% | Nov 2026 | derived | high (derived) |
| Round-trip cost, one Nifty option lot of 65 (derived) | premium ₹20: ₹50 (3.9% of premium, 0.77 points); ₹50: ₹55 (1.7%); ₹100: ₹63 (0.96%); ₹200: ₹78 (0.60%) | Nov 2026 | derived | high (derived) |
| Round-trip cost, futures (derived) | about 0.06% of notional (₹613 on ₹10 lakh) | Nov 2026 | derived | high (derived) |

### 2.7 Tax treatment

| claim | value | effective date | source URL | confidence |
|---|---|---|---|---|
| Intraday equity | speculative business income, taxed at slab; losses carried forward 4 years and set off only against speculative gains | current | https://zerodha.com/varsity/chapter/taxation-for-traders/ | high |
| F&O | non-speculative business income at slab; losses can offset other income except salary in the same year, carried forward 8 years against non-speculative income | current | same | high |
| Short-term capital gains on delivery equity | flat 20% | since 23 Jul 2024 (date from memory) | same | high for rate |
| Long-term capital gains on equity | 12.5% above ₹1.25 lakh a year | since 23 Jul 2024 | (unverified: from memory) | low |
| Advance tax on business income | 15% by 15 June, 45% by 15 Sept, 75% by 15 Dec, 100% by 15 March | current | https://zerodha.com/varsity/chapter/taxation-for-traders/ | high |
| Tax audit | when business turnover exceeds ₹10 crore, or profit declared below 6% of turnover with income above the exemption limit | FY 2024-25 | same | medium |

---

## 3. Formulas to implement

Notation: r_t is the strategy's net return in period t (after all costs), T the number of periods, P the periods per year (use the actual count of NSE sessions, about 246-250, not a hard-coded 252), rf the per-period risk-free rate.

### 3.1 Sharpe ratio, t-statistic, standard error

- SR = mean(r - rf) / std(r - rf), per period. Annualised SR_a = SR × sqrt(P). This scaling assumes no serial correlation; with autocorrelations ρ_k use SR(q) = η(q) × SR with η(q) = q / sqrt(q + 2 Σ_{k=1}^{q-1} (q-k) ρ_k) (Lo 2002; not opened, standard result). Strategies with positive autocorrelation, such as illiquid or smoothed-price strategies, have overstated annualised Sharpe.
- t-statistic of the mean: t = SR × sqrt(T) = SR_a × sqrt(years). (Harvey-Liu 2014.)
- Standard error with non-normal returns: SE(SR) = sqrt( (1 - γ3·SR + (γ4-1)/4·SR²) / (T-1) ), γ3 skewness, γ4 Pearson kurtosis (3 for a normal). With γ3 = 0, γ4 = 3 this is sqrt((1 + SR²/2)/(T-1)).
- Per-trade version for sparse strategies: t = mean(trade return) / std(trade return) × sqrt(number of trades). Requiring t ≥ 3 with mean 0.3% and std 3% per trade needs 900 trades.

### 3.2 Probabilistic and deflated Sharpe ratio

All Sharpe ratios here are per period, not annualised.

- PSR(SR*) = Φ( (SR - SR*) × sqrt(T-1) / sqrt(1 - γ3·SR + (γ4-1)/4·SR²) ).
- Expected maximum Sharpe among N independent zero-skill trials whose Sharpe estimates have cross-trial variance V:
  SR0 = sqrt(V) × ( (1-γ) Φ⁻¹(1 - 1/N) + γ Φ⁻¹(1 - 1/(N·e)) ), γ = 0.5772156649.
- DSR = PSR(SR0). Accept when DSR ≥ 0.95.
- If the M trials are correlated with average pairwise return correlation ρ, use N = ρ + (1-ρ)·M (DSR paper, appendix A.3), or cluster the trial return series and count clusters.
- If V is not available from our own trial log, the null value is V ≈ 1/(T-1) per period, that is 1/years in annualised units; this is what the "expected best Sharpe" row in the Facts table uses.
- Minimum track record length (observations) to show SR > SR* at confidence 1-α: MinTRL = 1 + (1 - γ3·SR + (γ4-1)/4·SR²) × (Z_{1-α} / (SR - SR*))².
- Minimum backtest length (years) for N trials and target annual Sharpe S: MinBTL = ( ((1-γ) Φ⁻¹(1-1/N) + γ Φ⁻¹(1-1/(N·e))) / S )², always below 2·ln(N)/S².

```python
import math, numpy as np
from scipy import stats as ss
EMC = 0.5772156649

def psr(sr, sr_star, T, skew=0.0, kurt=3.0):          # per-period Sharpe, Pearson kurtosis
    return ss.norm.cdf((sr - sr_star) * math.sqrt(T - 1) /
                       math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2))

def expected_max_sr(var_sr, n_trials, mean_sr=0.0):
    z = (1 - EMC) * ss.norm.ppf(1 - 1.0 / n_trials) + EMC * ss.norm.ppf(1 - 1.0 / (n_trials * math.e))
    return mean_sr + math.sqrt(var_sr) * z

def dsr(sr, T, skew, kurt, var_sr, n_trials):
    return psr(sr, expected_max_sr(var_sr, n_trials), T, skew, kurt)

def effective_trials(corr):                            # corr: M x M correlation of trial returns
    m = corr.shape[0]
    rho = (corr.sum() - np.trace(corr)) / (m * (m - 1))
    return rho + (1 - rho) * m

def min_trl(sr, sr_star=0.0, skew=0.0, kurt=3.0, alpha=0.05):
    return 1 + (1 - skew * sr + (kurt - 1) / 4 * sr ** 2) * (ss.norm.ppf(1 - alpha) / (sr - sr_star)) ** 2

# check: dsr(2.5/250**0.5, 1250, -3, 10, 0.5/250, 100) -> 0.9004 (paper), N=46 -> 0.9505
```

### 3.3 Multiple-testing adjustments and the Sharpe haircut

For M tests with p-values sorted ascending p(1) ≤ ... ≤ p(M):

- Bonferroni (family-wise error): p_adj(i) = min(1, M × p(i)).
- Holm (family-wise, step-down): p_adj(i) = min(1, max_{j ≤ i} (M - j + 1) × p(j)).
- Benjamini-Hochberg-Yekutieli (false discovery rate, valid under dependence): c(M) = Σ_{j=1}^{M} 1/j; p_adj(M) = p(M); p_adj(i) = min(p_adj(i+1), M × c(M) / i × p(i)).

Haircut procedure (Harvey-Liu): t = SR_a × sqrt(years); p = 2(1 - Φ(|t|)); adjust p for the number of tests; t_adj = Φ⁻¹(1 - p_adj/2); SR_haircut = t_adj / sqrt(years); haircut = 1 - SR_haircut/SR_a. With a single-step Bonferroni and 200 tests over 10 years, my code gives a haircut of 88% for Sharpe 0.92 and 26% for Sharpe 1.5, which is the nonlinearity the paper describes.

```python
def adj_pvalues(p, method="bhy"):
    p = np.asarray(p, float); m = len(p); order = np.argsort(p); ps = p[order]
    if method == "bonferroni":
        adj = np.minimum(ps * m, 1.0)
    elif method == "holm":
        adj = np.minimum(np.maximum.accumulate((m - np.arange(m)) * ps), 1.0)
    else:                                              # bhy
        c = np.sum(1.0 / np.arange(1, m + 1))
        raw = ps * m * c / np.arange(1, m + 1)
        adj = np.minimum(np.minimum.accumulate(raw[::-1])[::-1], 1.0)
    out = np.empty(m); out[order] = adj
    return out
```

### 3.4 White's Reality Check and Hansen's SPA

Purpose: test whether the best of K strategies beats a benchmark once the search over K is accounted for. Let d_{k,t} = r_{k,t} - r_{benchmark,t} for t = 1..n and d̄_k its mean. The benchmark for a long-only equity system should be Nifty 50 TRI (or cash for a market-neutral system).

- Reality Check statistic: V = max_k sqrt(n) × d̄_k. Bootstrap: draw B stationary-bootstrap index sets; V*_b = max_k sqrt(n) × (d̄*_{k,b} - d̄_k). p-value = share of V*_b ≥ V.
- Stationary bootstrap (Politis-Romano as described by White): first index uniform on 1..n; thereafter with probability q draw a new uniform index, otherwise take the previous index + 1 (wrapping to the start). Mean block length is 1/q. White's example uses q = 0.1 and B = 500 or 1,000; `arch` defaults to block length sqrt(n).
- SPA (Hansen 2005; paper not opened, formula from memory and consistent with the `arch` documentation): ω_k² = bootstrap variance of sqrt(n) × d̄_k. T = max(0, max_k sqrt(n) d̄_k / ω_k). Recentre each bootstrap mean by g_k = d̄_k if sqrt(n) d̄_k / ω_k ≥ -sqrt(2 ln ln n), else 0 ("consistent" version; g_k = max(d̄_k, 0) gives the lower and g_k = d̄_k the upper p-value). T*_b = max(0, max_k sqrt(n) (d̄*_{k,b} - g_k) / ω_k). p = share of T*_b ≥ T. SPA is less distorted than the Reality Check when the set contains many poor strategies.

```python
def stationary_bootstrap_indices(n, mean_block, rng):
    q = 1.0 / mean_block; idx = np.empty(n, dtype=int); idx[0] = rng.integers(n)
    for t in range(1, n):
        idx[t] = rng.integers(n) if rng.random() < q else (idx[t - 1] + 1) % n
    return idx

def reality_check(d, n_boot=1000, mean_block=10, seed=0, studentize=False):
    """d: n x K differentials vs benchmark. studentize=False: White RC; True: Hansen SPA (consistent)."""
    d = np.asarray(d, float); n, k = d.shape; rng = np.random.default_rng(seed); dbar = d.mean(axis=0)
    bm = np.array([d[stationary_bootstrap_indices(n, mean_block, rng)].mean(axis=0) for _ in range(n_boot)])
    if not studentize:
        return float((math.sqrt(n) * (bm - dbar).max(axis=1) >= math.sqrt(n) * dbar.max()).mean())
    omega = math.sqrt(n) * bm.std(axis=0, ddof=1); omega = np.where(omega > 0, omega, np.inf)
    stat = max(0.0, (math.sqrt(n) * dbar / omega).max())
    g = np.where(math.sqrt(n) * dbar / omega >= -math.sqrt(2 * math.log(math.log(n))), dbar, 0.0)
    boot = np.maximum(0.0, (math.sqrt(n) * (bm - g) / omega).max(axis=1))
    return float((boot >= stat).mean())
```

In production use `arch.bootstrap.SPA(benchmark_losses, model_losses)` with losses = negative returns, and `arch.bootstrap.StepM` to identify which strategies (not just whether any) beat the benchmark.

### 3.5 Probability of backtest overfitting (CSCV)

1. Build M, a T × N matrix of per-period net returns, one column per configuration tried (every one, including the discarded ones), rows aligned in time.
2. Cut the rows into S contiguous blocks of equal length (S even; the paper uses 16).
3. For every combination c of S/2 blocks: in-sample J = those blocks in original order, out-of-sample J̄ = the rest. Compute the performance metric (Sharpe) of every column on J and on J̄. Let n* be the column that is best on J. Let rank be its out-of-sample rank among the N columns (1 = worst, N = best), ω = rank/(N+1), λ_c = ln(ω/(1-ω)).
4. PBO = share of combinations with λ_c ≤ 0.
5. Also report: the regression of out-of-sample on in-sample performance of the selected column across combinations (a negative slope is the signature of overfitting), and the share of combinations in which the selected column loses money out of sample.

```python
import itertools
def pbo_cscv(m, s=16):
    m = np.asarray(m, float); t, n = m.shape
    blocks = np.array_split(np.arange(t - t % s), s); logits = []
    sr = lambda x: x.mean(axis=0) / x.std(axis=0, ddof=1)
    for combo in itertools.combinations(range(s), s // 2):
        is_idx = np.concatenate([blocks[i] for i in combo])
        oos_idx = np.concatenate([blocks[i] for i in range(s) if i not in combo])
        best = int(np.argmax(sr(m[is_idx])))
        w = ss.rankdata(sr(m[oos_idx]))[best] / (n + 1)
        logits.append(math.log(w / (1 - w)))
    return float((np.array(logits) <= 0).mean())
```

On 50 columns of pure noise this returns about 0.5-0.6; with one genuine edge added it returns about 0.02.

### 3.6 Walk-forward analysis

Optimise parameters on an in-sample window, trade the next out-of-sample window with those parameters, roll forward by the out-of-sample length, and judge the system only on the concatenated out-of-sample segments (Pardo; description from the Wikipedia article). The window can be rolling (fixed length) or anchored (growing from the first date). Leave a gap between the windows at least as long as the longest holding period so that a position opened in-sample cannot overlap the test window. Example split from the source: optimise on 1,000 bars, test on the next 200, roll 200.

```python
def walk_forward_windows(n_obs, train, test, gap=0, anchored=False):
    start = 0
    while start + train + gap + test <= n_obs:
        yield (0 if anchored else start, start + train), (start + train + gap, start + train + gap + test)
        start += test
```

Walk-forward gives one path, so its out-of-sample Sharpe has a wide error band, and repeating walk-forward with different window lengths until it looks good is itself a multiple-testing exercise that must be counted in N.

### 3.7 Purging, embargo and combinatorial purged cross-validation

- Purging: remove from the training set every observation whose label (the return it is trying to predict, spanning entry to exit) overlaps in time with a test-set label.
- Embargo: additionally remove the observations immediately after each test block, because features computed just after the test block still contain information from it.
- CPCV: split the sample into N contiguous groups, take every combination of k groups as the test set and the other N-k as the training set (after purging and embargo). There are C(N,k) splits; each group appears in the test set C(N-1,k-1) times, so the test pieces can be recombined into k/N × C(N,k) full-length backtest paths. This yields a distribution of out-of-sample Sharpe ratios instead of one number. Its variance, and the number of distinct configurations, feed V and N in the deflated Sharpe ratio.
- For daily rule-based strategies: purge = maximum holding period in bars; embargo = longest indicator look-back that uses future-adjacent data (if the strategy has no fitted model and parameters are fixed, embargo can be the holding period).

```python
def cpcv_splits(n_obs, n_groups=6, k_test=2, purge=0, embargo=0):
    groups = np.array_split(np.arange(n_obs), n_groups)
    for combo in itertools.combinations(range(n_groups), k_test):
        mask = np.ones(n_obs, bool)
        for g in combo:
            lo, hi = groups[g][0], groups[g][-1]
            mask[max(0, lo - purge): min(n_obs, hi + 1 + purge + embargo)] = False
        yield np.flatnonzero(mask), [groups[g] for g in combo]
```

### 3.8 Expected decay and planning numbers

- Published anomaly: expected live long-short return ≈ backtested × (1 - 0.58); statistical bias alone accounts for 0.26.
- Own discovery: use the haircut Sharpe from 3.3 or the deflated Sharpe from 3.2, whichever is lower. If neither can be computed because trials were not logged, halve the Sharpe.
- Compounding with reinvestment: W_n = W_0 × Π(1 + r_t). Long-run growth rate g ≈ μ - σ²/2 for arithmetic mean μ and volatility σ, so volatility is a direct drag on compounded wealth. The growth-optimal leverage is f* = μ_excess/σ² (Kelly; standard result, no source opened); because μ is estimated with large error, size at half of f* or less.
- Drawdown expectations: resample the net daily return series with the stationary bootstrap (3.4), compute maximum drawdown on each resample, and use the 95th percentile, not the single historical figure, as the planning drawdown.

### 3.9 Cost model

For one executed order of value v (premium value for options), using the rows of table 2.6:

```python
def angel_cost(v, segment, side):           # segment: 'delivery' | 'intraday' | 'futures' | 'options'
    brokerage = max(5.0, min(20.0, 0.001 * v)) if segment in ("delivery", "intraday") else 20.0
    stt = {"delivery": 0.001 * v,
           "intraday": 0.00025 * v if side == "sell" else 0.0,
           "futures": 0.0005 * v if side == "sell" else 0.0,
           "options": 0.0015 * v if side == "sell" else 0.0}[segment]
    exch = {"delivery": 0.000030699, "intraday": 0.000030699, "futures": 0.000018299, "options": 0.000355299}[segment] * v
    sebi = v * 10 / 1e7
    stamp = {"delivery": 0.00015, "intraday": 0.00003, "futures": 0.00002, "options": 0.00003}[segment] * v if side == "buy" else 0.0
    gst = 0.18 * (brokerage + exch + sebi)
    dp = 20 * 1.18 if (segment == "delivery" and side == "sell") else 0.0   # once per ISIN per day
    return brokerage + stt + exch + sebi + stamp + gst + dp
```

Slippage is separate and must be added on top. I found no opened source giving bid-ask spreads by liquidity bucket, so these are **assumptions to be calibrated from our own fills**, not facts: half-spread plus impact of 3-5 bps per side for Nifty 50 names at our order size, 10-15 bps for the rest of Nifty 500, 30 bps or more below that, and at least one tick (₹0.05) per side for index options with a floor of 0.5% of premium. Run every backtest a second time with slippage doubled.

---

## 4. Biases and India-specific pitfalls, with the rule the simulator should apply

| pitfall | what goes wrong | simulator rule |
|---|---|---|
| Survivorship | Testing on today's Nifty 500 list drops companies that were delisted, merged or fell out, and inflates returns, most of all for small-cap, value and mean-reversion strategies | Use point-in-time index membership (reconstitution is semi-annual, effective end of March and September, announced four weeks earlier). Keep delisted and merged symbols in the price file with their last traded price and a terminal event |
| Look-ahead in index membership | Using the constituent list on the announcement date, or a list that includes the future | Membership changes take effect on the effective date; do not trade on them before the announcement date |
| Look-ahead in prices | The official close of a non-CAS stock is a 30-minute VWAP, known only after 15:30; for F&O stocks since 2026 it is the auction price | A signal computed from today's close can be executed at the next session's open, or at today's close only with an explicit slippage penalty and only if the order can be placed before the auction cut-off |
| Look-ahead in fundamentals | Quarterly results appear weeks after the quarter ends | Lag fundamentals to the actual announcement date; if unknown, lag 60 days after quarter end and 75 days after year end (assumption) |
| Corporate actions | Raw bhavcopy prices are not adjusted; splits and bonuses create false -50% days; dividends create false gaps; the ex-date equals the record date under T+1 | Build an adjustment factor series; compute signals on adjusted prices but size orders and check price bands on raw prices; credit dividends as cash on the ex-date |
| Symbol changes and demergers | A renamed or demerged company appears as a new series with no history | Map old to new symbols with ISIN history |
| Circuit limits | A stock locked at the upper band has no sellers, so a backtest that buys it is fictional; a stock locked at the lower band cannot be sold and stop-losses do not fill | If the day's high equals low at the band, or the close is at the band limit, reject buys at the upper band and sells at the lower band; carry the order to the next session. Bands are 2, 5, 10 or 20%; F&O stocks have no fixed band |
| Stop-loss fills | Gaps and locked limits mean the fill is at the open or later, not at the stop price | Fill a triggered stop at the worse of the stop price and the next available traded price |
| Illiquid closes and stale prices | Low-volume stocks show smooth, autocorrelated closes that produce spurious mean reversion or momentum | Liquidity filter: minimum median daily traded value (for a ₹15,000 order, require at least ₹1 crore a day so the order is under 0.15% of volume); exclude stocks in trade-for-trade or surveillance series |
| Auction risk | Selling shares bought the previous day before they are delivered, or failing to cover an intraday short, leads to a buy-in auction and a close-out up to 20% above the price | No sell of undelivered shares; force square-off of intraday shorts before the broker cut-off (Zerodha: 15:12 for CAS stocks, 15:25 others) |
| Short side | Overnight short positions in the cash market are not possible | Long-short equity backtests must model the short leg through stock futures (lot values far above this account) or drop it |
| F&O lot economics | Lot sizes were raised in 2025 (minimum contract value ₹15 lakh) and expiry days moved to Tuesday; history contains several regimes | Store lot size, expiry calendar and contract availability by date; do not apply today's lot size to the past |
| F&O costs | STT rose on 1 Oct 2024 and again by Nov 2026 (futures 0.05%, options 0.15%); a strategy tuned on the old cost schedule may not survive | Apply the charge schedule in force on each trade date; evaluate the final candidate on today's schedule |
| Expiry-day effects | 59% of index-option turnover is on expiry day; final settlement price method changes on 7 Dec 2026 | Tag expiry days; do not assume expiry-day behaviour learned under one settlement rule holds under the next |
| Market-wide halts | 10/15/20% index moves halt all trading | Rare; simulator should refuse fills during a halt day's remainder |
| Calendar | Muhurat sessions, special Saturday sessions and holidays distort day-count features | Use the exchange calendar, not weekday arithmetic |
| Regime in the test window | The last five years to Oct 2026 returned 6.7% a year on Nifty 50 TRI; the year to Oct 2026 was -9.45% | Report results by sub-period; a long-only strategy that only worked in 2020-2021 has shown nothing |
| Tax | Delivery gains under a year are taxed at 20%; intraday and F&O income at slab rates; reinvested capital grows at the after-tax rate | Report pre-tax and an after-tax compounding scenario |

---

## 5. Validation protocol proposed for this project

This is my recommendation built from the sources above; the numeric gates are choices, stated with their origin.

1. **Write the hypothesis first.** Economic reason, universe, signal, parameter ranges and the benchmark, before any run (Arnott-Harvey-Markowitz protocol, items 1 and 2).
2. **Log every run.** Each parameter set that touches data gets a row: return series, Sharpe, date. The log supplies M, the average correlation ρ (hence N), and the cross-trial variance V for the deflated Sharpe ratio. Without the log no result can be deflated.
3. **Split the data once.** Reserve the most recent 20-25% as a holdout that no one looks at until a strategy is frozen. Development uses walk-forward and CPCV on the rest.
4. **Evaluate net of costs** with the dated charge schedule and slippage assumptions, then again with slippage doubled and with execution delayed by one bar.
5. **Gates on the development sample**
   - net annualised Sharpe above the buy-and-hold benchmark over the same dates;
   - t = SR_a × sqrt(years) ≥ 3.0 (Harvey-Liu-Zhu), or DSR ≥ 0.95 using our own N and V;
   - PBO across the configurations of that strategy family ≤ 0.20 (the PBO paper's customary cut is 0.05; that is stricter than a small research programme can usually meet, so anything between 0.05 and 0.20 is flagged rather than rejected);
   - SPA consistent p-value ≤ 0.05 for the family against the benchmark;
   - neighbouring parameter values give similar results (no isolated peak);
   - positive in at least two of three sub-periods;
   - turnover low enough that doubling costs does not turn it negative (Novy-Marx and Velikov: above 50% one-sided monthly turnover, few anomalies survive).
6. **Holdout, once.** Run the frozen rules on the reserved data. Expect the holdout Sharpe to be about half the development Sharpe; a holdout Sharpe below 25% of development, or negative, fails.
7. **Paper trade, then small live.** Track the realised series against the backtest. Minimum track record length tells how long is needed: about 2.7 years of daily returns to confirm a Sharpe of 1.0 at 95%, so early live results can only reject, not confirm.
8. **Kill rules decided in advance.** Stop a strategy when its live drawdown exceeds the 95th-percentile bootstrap drawdown, or when PSR of the live record against half the backtest Sharpe falls below 5%.
9. **Portfolio level.** The same deflation applies to the choice of which strategies go live: selecting the best 3 of 40 tested families is another 40-way selection.

---

## 6. Realistic expectations

- **Base rate for discretionary and semi-systematic retail activity:** about 88-91% of individual F&O traders and 71% of intraday cash traders lose in a year; 0.5% of five-year F&O participants are profitable in every year.
- **Benchmark to beat:** Nifty 50 total return, 12.15% a year since 1995 with 22.4% annualised daily volatility, but 6.70% a year with 13.9% volatility over the five years to 30 Oct 2026 and -9.45% over the last year. A Nifty ETF costs one brokerage ticket and no further effort.
- **Rules-based factor portfolios, zero cost, live record:** 7-11.6% a year over the last five years for NSE's momentum, alpha, quality, low-volatility and equal-weight indices, that is 0.3 to 4.9 percentage points above Nifty 50 before the 0.3-0.9% round-trip costs and the tax on short-term gains that a ₹1.5 lakh replication would pay. Their back-filled histories show 15-20% a year.
- **Academic anomalies:** expect about 40% of the published premium to remain (McLean-Pontiff), and only if monthly turnover is moderate.
- **Statistical ceiling on what we can prove:** with roughly 10-15 years of daily NSE data, a single pre-specified strategy needs a net Sharpe near 0.8-0.95 to reach t = 3; after searching 100 variants, a raw Sharpe of 0.65-0.8 is what chance alone delivers.
- **My judgment, not a sourced figure:** a carefully validated long-only daily or weekly equity system might deliver a net Sharpe of 0.4-0.8 and 0-5 percentage points a year over the index; diversified trend following on futures is usually quoted around 0.3-0.7 net but is not implementable at this account size; any backtest showing Sharpe above 2 on daily bars for a retail-accessible Indian strategy should be treated as a bug or an overfit until proven otherwise.
- **What compounding does at this size:** ₹1.5 lakh grows to ₹2.64 lakh in 5 years and ₹4.66 lakh in 10 at 12% a year; to ₹3.73 lakh and ₹9.29 lakh at 20%; the 20% figure is already above every live index record in the table above.

---

## 7. Strategies in this area

This area is about method, so it contributes only three strategies, all benchmarks that the backtest programme needs: the market, the naive equal-weight portfolio, and one published factor rule with a live record against which to check our own momentum backtests.

### 7.1 Buy and hold Nifty 50 (the null benchmark)

- **Rules.** Universe: one Nifty 50 ETF or index fund. Signal: none. Entry: invest all capital at the first open. Exit: never. Stop: none. Rebalance: reinvest dividends or cash monthly. Positions: 1. Parameters: allocation 100%.
- **Instruments.** Nifty 50 ETF on NSE (cash segment), or the Nifty 50 TRI series for gross comparison.
- **Holding period.** Multi-year.
- **Reported performance.** Nifty 50 TRI 12.15% CAGR since base date 3 Nov 1995 to 30 Oct 2026; 6.70% CAGR over 5 years; -9.45% over 1 year; price index 10.65% and 5.46%; annualised daily standard deviation 22.38% since inception, 13.88% over 5 years (NSE Indices factsheet).
- **India evidence.** Direct.
- **Costs and capacity.** One buy ticket (about 0.13% on ₹1.5 lakh including stamp duty and STT), ETF expense ratio and tracking error not checked here.
- **Failure modes.** Full market drawdown; five-year stretches of single-digit returns, as now.
- **Feasibility at ₹1.5 lakh.** Yes. Units cost a few hundred rupees; no margin, no lot size.
- **Sources.** https://www.niftyindices.com/Factsheet/ind_nifty50.pdf

### 7.2 Replication of Nifty200 Momentum 30 (a published rule with a live record)

- **Rules (NSE Indices methodology, Sept 2026).** Universe: Nifty 200 constituents at review with at least 1 year of listing and available in F&O. For each stock: 12-month return = P(M-1)/P(M-13) - 1 and 6-month return = P(M-1)/P(M-7) - 1, prices at the last trading day of those months, M the rebalance month. σ = annualised standard deviation of daily log returns over 1 year. MR12 = 12-month return/σ, MR6 = 6-month return/σ. Z-score each across the universe. Weighted Z = 0.5 × Z12 + 0.5 × Z6. Normalised score = 1 + Z if Z ≥ 0, else 1/(1 - Z). Select the top 30. Buffer: top 15 always included; existing members dropped only when rank falls beyond 45. Weight ∝ free-float market cap × score, capped at the lower of 5% and 5 times the stock's free-float weight. Rebalance semi-annually in June and December. Stocks leaving Nifty 200 leave the index. No stop.
- **Instruments.** NSE cash equities (or a Momentum 30 ETF or index fund as a one-ticket substitute).
- **Holding period.** Six months between rebalances; individual names often longer because of the buffer.
- **Reported performance.** Total return index: 18.05% CAGR since base date 1 Apr 2005 to 30 Oct 2026; 7.93% over 5 years; -8.48% over 1 year; price return 16.79%, 6.97%, -9.15%. Annualised volatility 22.31% since inception, 19.39% over 5 years; beta to Nifty 50 about 1.15 over the last five years (the factsheet text is ambiguous on column order). The index was launched on 25 Aug 2020, so everything before that is a back-fill; the five-year figure is entirely live and is 1.2 percentage points above Nifty 50 TRI.
- **India evidence.** Direct.
- **Costs and capacity.** Index returns carry no costs. A 30-stock replication at ₹5,000 per name pays about 0.93% per round trip (table 2.6), plus 20% tax on gains realised within a year. Capacity is not a concern.
- **Failure modes.** Momentum crashes at market turns; high beta; large gap between back-filled and live results.
- **Feasibility at ₹1.5 lakh.** Marginal as direct replication: 30 positions of ₹5,000 cannot hold the intended weights in high-priced shares and pay the highest percentage costs. Feasible through an ETF or index fund, or as a concentrated 10-stock variant, which is then a different, untested strategy.
- **Sources.** https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf ; https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf

### 7.3 Equal-weight Nifty 50 (the naive-diversification benchmark)

- **Rules (NSE Indices methodology, Sept 2026).** Universe: the 50 Nifty 50 constituents. Signal: none. Weight 2% each. Reset to equal weight on the last trading day of March, June, September and December using closing prices three trading days earlier. Change constituents only when Nifty 50 changes (semi-annual review, effective end of March and September, plus ad hoc replacements). No stop. Positions: 50.
- **Instruments.** NSE cash equities, or an equal-weight Nifty 50 index fund or ETF.
- **Holding period.** Quarterly rebalance; names held for years.
- **Reported performance.** Total return index 13.73% CAGR since base date 3 Nov 1995 to 30 Oct 2026 against 12.15% for Nifty 50 on the same base date; 10.94% against 6.70% over 5 years; -4.15% against -9.45% over 1 year. Annualised volatility 21.86% since inception, 13.94% over 1 year. The index was launched on 13 Apr 2017; earlier history is back-filled.
- **India evidence.** Direct.
- **Costs and capacity.** Index figures carry no costs. Fifty positions of ₹3,000 pay more than 1% per round trip at Angel One's rates (minimum brokerage ₹5 a side and ₹23.60 DP charge on each sell); quarterly trims are small tickets where the fixed charges dominate.
- **Failure modes.** Underperforms cap-weight when the largest stocks lead; tilts toward the smaller and more volatile members.
- **Feasibility at ₹1.5 lakh.** Marginal as direct replication because of 50 small tickets; yes through a fund. Its use here is as a hurdle: a stock-selection system built on Nifty 50 or Nifty 100 names should beat equal weight, not only the cap-weighted index.
- **Sources.** https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf ; https://www.niftyindices.com/Factsheet/Factsheet_Nifty50_Equal_Weight.pdf

---

## 8. Sources opened

SEBI: https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf ; https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233601328.pdf ; https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1751900271726.pdf ; https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1727085659479.pdf ; https://www.sebi.gov.in/sebi_data/attachdocs/jul-2024/1721818140715.pdf

Commentary on the SEBI studies: https://tradingqna.com/t/win-rate-capital-experience-what-sebi-found-about-f-o-traders/197266 ; https://tradingqna.com/t/key-findings-from-sebis-analysis-of-intraday-trading-by-individuals-in-equity-cash-segment/170633 ; https://www.business-standard.com/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html

Papers: https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf ; https://carmamaths.org/jon/backtest2.pdf ; https://www.nber.org/system/files/working_papers/w20592/w20592.pdf ; https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF ; https://people.duke.edu/~charvey/Research/Published_Papers/P116_Evaluating_trading_strategies.pdf ; https://people.duke.edu/~charvey/Research/Published_Papers/P138_A_backtesting_protocol.pdf ; https://gwern.net/doc/economics/2016-mclean.pdf ; https://www.ssc.wisc.edu/~bhansen/718/White2000.pdf ; https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trading%20Skill%20110523.pdf ; https://www.nber.org/papers/w28432 ; https://www.nber.org/papers/w23394 ; https://www.nber.org/papers/w20721 ; https://arxiv.org/abs/2209.13623

Software and reference: https://arch.readthedocs.io/en/latest/multiple-comparison/generated/arch.bootstrap.SPA.html ; https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparison_examples.html ; https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html ; https://en.wikipedia.org/wiki/Walk_forward_optimization ; https://quantpedia.com/strategies/time-series-momentum-effect/ ; https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing

NSE and NSE Clearing: https://www.nseindia.com/products-services/equity-market-price-bands ; https://www.nseindia.com/products-services/equity-market-circuit-breakers ; https://www.nseindia.com/static/products-services/closing-auction-session ; https://www.nseindia.com/market-data/market-timings ; https://www.nseindia.com/products-services/t0-settlement-cycle ; https://www.nseindia.com/products-services/equity-derivatives-nifty50 ; https://www.nseindia.com/products-services/equity-derivatives-contract-specifications ; https://www.nseindia.com/products-services/equity-derivatives-selection-criteria ; https://www.nseclearing.in/clearing-settlement/capital-market/settlement-cycle ; https://www.nseclearing.in/clearing-settlement/capital-market/shortages-handling

NSE Indices: https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf ; https://www.niftyindices.com/Factsheet/ind_nifty50.pdf ; https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf ; https://www.niftyindices.com/Factsheet/Factsheet_Nifty50_Equal_Weight.pdf ; https://www.niftyindices.com/Factsheet/Factsheet_Nifty_Alpha50.pdf ; https://www.niftyindices.com/Factsheet/Factsheet_Nifty_Low_Volatility50.pdf ; https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Quality30.pdf ; https://www.niftyindices.com/Factsheet/Factsheet_Nifty100_Alpha30.pdf

Brokers: https://www.angelone.in/exchange-transaction-charges ; https://zerodha.com/charges/ ; https://zerodha.com/marketintel/bulletin/ ; https://zerodha.com/marketintel/bulletin/461085/changes-to-closing-auction-session-cas-from-december-7-2026 ; https://zerodha.com/marketintel/bulletin/249809/latest-intraday-leverages-mis-bo-co ; https://zerodha.com/marketintel/bulletin/462093/quantity-freeze-limits-for-indices-from-november-02-2026 ; https://zerodha.com/varsity/chapter/five-corporate-actions-and-its-impact-on-stock-prices/ ; https://zerodha.com/varsity/chapter/shorting/ ; https://zerodha.com/varsity/chapter/taxation-for-traders/

Blocked or not found (claims marked accordingly): SSRN abstract pages (403), AMS Notices PDF (403), S&P SPIVA page (403), Lo (2002) and Hansen (2005) PDFs (404), Angel One SmartAPI documentation (script-rendered), RBI home page (script-rendered), individual NSE circular PDFs (404).

---

## Negative or cautionary evidence

- **The retail base rate is brutal and stable.** Roughly nine in ten individual F&O traders lost in each of FY22-FY26; cumulative net losses were about ₹3.85 lakh crore; the average loser lost ₹1.47 lakh in FY26. Loss shares rise, not fall, with years of experience.
- **The small-account bucket does worst on frequency, and its losses are large relative to capital.** 90% of accounts with under ₹1 lakh of peak margin lost; in the ₹1-5 lakh bucket 86% lost and the average P&L was -₹2.96 lakh.
- **Turnover is the best single predictor of losing.** Traders active more than 100 days produced 87% of losses; 80% of intraday cash traders with more than 500 trades a year lost; large-turnover F&O traders (above ₹1 crore a year) were 20% of traders and 82% of net losses.
- **Retail "algo" users lost too.** The algo flag among individuals is associated with larger, not smaller, losses per head (about 15% of traders in FY26, about 30% of FY25-FY26 gross losses), with the caveat that the flag includes broker auto-square-off and so partly measures heavy intraday activity.
- **The counterparties are a handful of algorithmic firms.** Proprietary desks account for about 60% of derivatives turnover; fewer than ten firms supply about 85% of proprietary options turnover and take most of the profit.
- **Option selling's win rate is a trap.** 56% of predominantly-selling retail traders were profitable in FY26, yet the median return on capital was +1% and the average losing seller lost ₹51.7 lakh.
- **Costs alone flip outcomes.** 4.4 lakh F&O traders who were profitable before costs ended FY26 with a net loss; statutory levies are now about 40% of total costs and rising.
- **Statistical evidence in finance is weak by default.** 64% of 447 anomalies fail a 5% test once microcaps are controlled and 85% fail t ≥ 3; a t of 2 means little after hundreds of tries; five years of data cannot support more than about 45 independent trials at a target Sharpe of 1.
- **Decay is the rule.** 58% lower returns after publication; eight popular factors fell from 5.8% to 2.4% a year; every NSE factor index examined shows a live five-year return far below its back-filled since-inception return.
- **Out-of-sample testing is not a cure.** Harvey and Liu note that a holdout period the researcher has already seen is not out of sample, and that a five-year holdout has little power: a true strategy has a good chance of failing it. Walk-forward repeated until it passes is data mining.
- **Not everyone agrees the literature is mostly false.** Jensen-Kelly-Pedersen and Chen-Zimmermann find that most published factors replicate and that publication-bias shrinkage is only 10-15%. The disagreement is about published academic factors built by careful researchers; it does not rescue a private backtest with an unrecorded number of trials.
- **Sources I could not verify** and therefore did not rely on: the 73% live-versus-backtest Sharpe deterioration for bank alternative-beta products (Suhonen et al.), the Quantopian study of 888 algorithms, Lo's autocorrelation correction, and Hansen's original SPA paper.

## Open questions

1. **Start date of the Closing Auction Session.** The NSE page (updated 12 Aug 2026) gives the rules and the market-timings page already shows derivatives closing at 15:40, but I did not open a document stating the first day. The simulator needs the date to know from when the official close of F&O stocks is an auction price. The 7 Dec 2026 changes come from a broker bulletin, not from the SEBI circular itself.
2. **Dates of the STT increases to 0.05% (futures) and 0.15% (options)** and of the move of NSE expiries from Thursday to Tuesday. The current values are verified; the effective dates are from memory.
3. **Angel One specifics not opened:** intraday leverage table, auto square-off times with the closing auction, API rate limits, the static-IP and algo-registration requirements under SEBI's retail algo framework, and whether the 0.1% intraday brokerage shown on the pricing page applies to API orders.
4. **Nifty 50 level.** NSE's circuit-breaker page gives 25,044.65 for 9 Nov 2026, while the 30 Oct 2026 factsheet returns (-11.77% year to date, 10.65% a year since 1995) imply roughly 23,050. Either the index rose about 8% in six sessions or one of the two pages is stale; lot notional (₹15-16 lakh) and margin estimates depend on it.
5. **Exact lot sizes and margins.** Lot sizes here are inferred from freeze quantities; the authoritative source is the daily NSE_FO_contract file. SPAN plus exposure margin for one Nifty future was not looked up.
6. **Slippage calibration.** No opened source gave bid-ask spreads or impact by liquidity bucket for ₹5,000-50,000 orders. The assumptions in section 3.9 need replacing with measurements from paper trading.
7. **Survivorship-free data.** Whether the project's price files contain delisted and merged companies and point-in-time index membership decides how much of any small-cap or value result is real. Not assessed here.
8. **Risk-free rate for Sharpe ratios.** The current 91-day T-bill or overnight rate was not retrieved (RBI page is script-rendered). Use the Nifty 1D Rate index or T-bill yields by date.
9. **Close price definition for non-CAS stocks and physical settlement of stock derivatives** are stated from memory and should be confirmed against NSE documents.
10. **How many trials will the programme run?** With about 22 research areas and many variants each, M will be in the hundreds or thousands. The deflated Sharpe threshold depends on the effective number after correlation, which can only be computed from the run log.
