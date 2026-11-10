# Event-driven and special situations: India, small account (research date 2026-11-10)

Researcher area: post-earnings drift, results-day moves, analyst revisions, index inclusion/exclusion (Nifty, MSCI), buyback tender offers and the small-shareholder quota, open offers, delisting, mergers and demergers, rights issues, IPO listing-day behaviour and grey-market premium, OFS, bonus/split, bulk/block deals, insider/promoter trades, pledging, credit ratings, FII/DII flows, upper-circuit momentum.

Target user: retail trader, ₹1,50,000 capital, Angel One (SmartAPI), fully automated, profits reinvested.

## 0. How this was produced, and what to distrust

- 36 web searches were run before the shared search budget for the whole workflow ran out. After that, sources were opened directly by URL (papers, regulator documents, broker pages). Topics that were still unsearched at that point are listed under "Open questions"; nothing was filled in from memory without being flagged.
- Tags used below:
  - **[opened]** = I read the page or PDF text myself.
  - **(unverified: snippet only)** = seen only in a search-result summary; the underlying page was paywalled, blocked (HTTP 403 / TLS error) or not reached.
  - **(from memory, not re-verified)** = regulatory detail I believe is right but did not re-open in this session. Treat as a to-check item before coding.
- Most Indian academic evidence here is short-window event studies with small samples, usually gross of costs, often with survivorship and look-ahead problems (announcement timestamps are rarely handled properly). Read "abnormal return" as "before costs, before slippage, versus an index".
- Several of the best-sounding special situations (buyback tender, IPO application, OFS, rights) are not ordinary buy/sell orders. They need a tender/bid/application step that I could not confirm is available through SmartAPI. They may only be semi-automatable (bot decides and alerts, human taps "tender").

## 1. Ground rules for a ₹1.5 lakh Angel One account

### 1.1 Costs (Angel One pricing page, opened 2026-11-10)

| Item | Delivery | Intraday | Futures | Options |
|---|---|---|---|---|
| Brokerage per executed order | lower of ₹20 or 0.1%, min ₹5 | lower of ₹20 or 0.1%, min ₹5 | ₹20 | ₹20 |
| STT | 0.1% buy and sell | 0.025% sell | 0.05% sell | 0.15% sell (premium) |
| NSE transaction charge | 0.0030699% | 0.0030699% | 0.0018299% | 0.0355299% |
| Stamp duty (buy side) | 0.015% | 0.003% | 0.002% | 0.003% |
| SEBI fee | ₹10/crore | ₹10/crore | ₹10/crore | ₹10/crore |
| GST | 18% on brokerage + transaction + SEBI charges | same | same | same |

The delivery minimum went from ₹2 to ₹5 and intraday brokerage from 0.03% to 0.1% (cap ₹20) on 17 November 2025 [opened: Angel One pricing update]. The page also lists "₹20 per ISIN" under other charges, which I read as the depository (DP) charge on delivery sells; the table context was not fully parsed, so confirm.

Round-trip delivery cost implied by those numbers (my arithmetic, DP charge taken as ₹20 + GST per sell):

| Position size | Round-trip cost | As % |
|---|---|---|
| ₹15,000 | about ₹92 | 0.61% |
| ₹30,000 | about ₹138 | 0.46% |
| ₹50,000 | about ₹182 | 0.36% |
| ₹1,50,000 | about ₹405 | 0.27% |

Add slippage (0.1 to 0.5% per side in mid/small caps on event days). **Any event edge below roughly 1.5% gross per trade is not tradable at this account size.** Many of the Indian event studies below report 1 to 3% effects.

### 1.2 Taxes

- Buyback proceeds: taxed as **capital gains in the shareholder's hands from 1 April 2026** (Finance Act 2026, section 69 of the Income-tax Act 2025). Between 1 October 2024 and 31 March 2026 the whole receipt was taxed as dividend at slab rate with the cost becoming a capital loss, which killed the retail buyback trade. Before October 2024 the company paid 20% buyback tax and the shareholder paid nothing. Promoters now pay an effective 22% (corporate) or 30% (others) [opened: SEBI board memorandum of 19 June 2026 reproduced on TaxGuru; SCC Online analysis; TaxGuru explainer].
- Short-term capital gains on listed equity 20%, long-term 12.5% above ₹1.25 lakh a year (from memory, not re-verified; the 12.5% long-term rate is confirmed in the TaxGuru explainer). Whether a tender-offer sale through the exchange window gets the 20% STT-paid rate or slab rate under the 2026 law was not confirmed: see Open questions.
- Frequent event trading is likely to be assessed as short-term gains or business income; every strategy below should be evaluated after 20% tax on net gains.

### 1.3 Structural constraints

- No overnight short selling of shares in the cash market. A short leg needs stock futures or options, and one stock-futures lot needs margin that is a large fraction of ₹1.5 lakh (lot sizes are set for contract values of several lakh rupees; exact 2026 lots are covered by the derivatives researchers). So every long-short result below must be read through its **long leg only**.
- T+1 settlement: to be a shareholder on a record date, buy at least one trading day before it (from memory, not re-verified).
- The small-shareholder cap for buybacks is ₹2,00,000 of holding at record-date close, so a ₹1.5 lakh account is naturally inside the reserved category.
- Stocks locked at a price band cannot be bought or sold at will; SME, T2T/BE series, ASM/GSM stocks should be excluded from any automated event strategy.

### 1.4 Data sources by event type

Reachability was checked on 2026-11-10 with a plain HTTP request (status 200 unless noted). The NSE pages are JavaScript applications; an automated collector needs a session cookie and the JSON endpoints behind them.

| Event | Primary source | Notes |
|---|---|---|
| Quarterly results, board-meeting dates | https://www.nseindia.com/companies-listing/corporate-filings-financial-results , https://www.nseindia.com/companies-listing/corporate-filings-board-meetings , https://www.bseindia.com/corporates/ann.html | Need the broadcast timestamp to know whether results came during or after market hours |
| Corporate actions (bonus, split, dividend, rights, buyback record dates) | https://www.nseindia.com/companies-listing/corporate-filings-actions | Ex-date and record date |
| All announcements (buyback, demerger, delisting, merger, rating) | https://www.nseindia.com/companies-listing/corporate-filings-announcements | Free-text; needs classification |
| Insider trades (PIT Reg 7) | https://www.nseindia.com/companies-listing/corporate-filings-insider-trading | Buyer category, mode (market purchase), value, dates |
| SAST Reg 29 (5% and 2% changes), pledges | https://www.nseindia.com/companies-listing/corporate-filings-regulation-29 , https://www.nseindia.com/companies-listing/corporate-filings-pledged-data | |
| Shareholding pattern | https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern | Quarterly; small-shareholder count for buyback estimates |
| Bulk and block deals | https://nsearchives.nseindia.com/content/equities/bulk.csv , https://nsearchives.nseindia.com/content/equities/block.csv (today's file; columns Date, Symbol, Security Name, Client Name, Buy/Sell, Quantity Traded, Trade Price) [opened]; history at https://www.nseindia.com/report-detail/display-bulk-and-block-deals | Published after market close on the deal day |
| Nifty index changes | Press releases under https://www.niftyindices.com/ (for example https://niftyindices.com/Press_Release/ind_prs23022026.pdf) [opened]; methodology https://nsearchives.nseindia.com/content/indices/Method_NIFTY_Equity_Indices.pdf [opened] | Released after market hours |
| MSCI index reviews | https://www.msci.com/index-review/ | Announced about 3:30 am IST; February, May, August, November |
| Price bands | https://nsearchives.nseindia.com/content/equities/sec_list.csv (Symbol, Series, Band) [opened] | Needed for upper-circuit logic |
| FII/DII flows | https://www.nseindia.com/reports/fii-dii ; https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx | Provisional daily numbers after close |
| IPO calendar and subscription | https://www.nseindia.com/market-data/all-upcoming-issues-ipo | Category-wise subscription updated through the day |
| Buyback list | https://www.chittorgarh.com/report/latest-buyback-issues-in-india/80/tender-offer-buyback/ [opened; table is script-loaded] | Aggregator; letters of offer are on SEBI and exchange sites |

---

## 2. Strategies

Each entry gives: rules; instruments; holding period; reported performance; India evidence; costs and capacity; failure modes; feasibility at ₹1.5 lakh; sources.

### A. Earnings

#### S01. Post-earnings-announcement drift on earnings surprise (SUE), long-only

- **Rules.** Universe: Nifty 500 (or the top 500 by turnover), price above ₹50, 20-day median turnover above ₹5 crore. For each quarterly result compute UE = (EPS_q − EPS_{q−4}) / Price(day −2), day 0 being the first session that can trade on the result. Rank UE against quartile breakpoints taken from the **previous** quarter's cross-section (avoids look-ahead). Long the top quartile. Enter at the open of day +2, hold 63 trading days or until the next result, whichever comes first. Equal weight, maximum 5 to 8 names, new signals replace the oldest. No stop in the source; a 15% stop is a sensible test parameter. Variant: SUE = (EPS_q − EPS_{q−4} − drift) / standard deviation of the last 8 seasonal differences; quintiles or deciles.
- **Instruments.** Cash equities, delivery.
- **Holding period.** About 3 months.
- **Reported performance.** India, 18,269 announcements, 2008 to 2014 (Krishnan and Rangan, NSE-IGIDR): market-adjusted return over days +2 to +64 was −6.6% for the lowest UE quartile, −2.0%, +1.2% and **+0.7%** for the highest; high-minus-low 7.3% (median 6.2%), significant. Sen (2009), cited in that paper: 582 BSE firms 2001 to 2006, top-minus-bottom quintile 10.05% up to the next announcement. US: a Quantpedia review puts the abnormal return at 2.6 to 9.4% per quarter across studies (unverified: snippet only). A SAGE paper on 469 Indian companies 2002 to 2011 reports significant post-event abnormal returns in 35 of 37 quarters (unverified: snippet only).
- **India evidence.** Yes, and it is unfavourable to a long-only version: nearly all of the 2008 to 2014 spread came from losers falling, while the best-surprise quartile beat the Nifty by under 1% in a quarter. Gupta and Dhusia (2021), 100 NSE firms, 1,130 observations, 2014 to 2018, find a negative association between abnormal returns and earnings surprise and conclude the market is efficient to earnings news.
- **Costs and capacity.** Four rotations a year at about 0.5% each is 2% a year, larger than the measured long-leg edge. Capacity is not a constraint.
- **Failure modes.** Edge concentrated in the short leg and in small illiquid names; decay (US drift has declined sharply; Kettell, McInnis and Zhao 2022 tie it to falling persistence of earnings news); EPS data errors, restatements, standalone versus consolidated; announcement timing.
- **Feasibility.** Marginal. Implementable, but the Indian long leg has not been shown to clear costs. Worth one backtest on point-in-time results data, long leg only.
- **Sources.** https://nsearchives.nseindia.com/research/content/NSE-IGIDR-WP4-14-15.pdf ; https://journals.lib.vutbr.cz/index.php/trends/article/view/541 ; https://quantpedia.com/strategies/post-earnings-announcement-effect/ ; https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Events%20Page/PEAD_Declined_over_time.pdf

#### S02. Earnings-announcement-return (EAR) drift, alone or intersected with SUE

- **Rules.** Same universe. EAR = stock return minus index return (Nifty 500) over the three sessions centred on day 0. Sort into quintiles using the previous quarter's breakpoints. Long the top EAR quintile; in the combined version require the top SUE quintile as well. Enter on the second day after the announcement, hold 60 trading days, equal weight. Source excludes stocks under $5, financials and utilities; an Indian version should exclude prices under ₹50 and test with and without financials.
- **Instruments.** Cash equities.
- **Holding period.** 60 trading days.
- **Reported performance.** US, 1987 to 2004 (Brandt, Kishore, Santa-Clara, Venkatachalam, via Quantpedia): EAR long-short abnormal return 7.55% a year, 1.3 points more than SUE; the EAR-and-SUE intersection earned +2.97% (long) versus −0.58% (short) per 60 days, about 15% a year long-short; max drawdown −11.2%; survives among the 1,000 largest firms at a reduced level; most of the return is on the long side in that sample.
- **India evidence.** None found for the EAR sort itself. Indirect: in the Krishnan and Rangan sample the 3-day announcement return was +1.4% for the top UE quartile and −1.9% for the bottom, so price reaction and surprise line up.
- **Costs and capacity.** As S01.
- **Failure modes.** A big results-day jump in India is often a gap that has to be bought next morning at a worse price; crowded "results gap" trading on social media; breakpoints unstable in quarters with few reporters.
- **Feasibility.** Marginal; cheap to test because it only needs prices plus announcement dates.
- **Sources.** https://quantpedia.com/strategies/post-earnings-announcement-effect/ ; https://nsearchives.nseindia.com/research/content/NSE-IGIDR-WP4-14-15.pdf

#### S03. Price-and-volume shock drift (earnings-gap proxy without an event calendar)

- **Rules.** Universe: Nifty 500, price above ₹50. Signal on day t: open at least 4% above the previous close (test 3 to 8%), close in the top 30% of the day's range, volume at least 3 times the 50-day average, and close above the 200-day average. Buy at the open of t+1. Exit after 20 trading days (test 5, 20, 60), or on a close below the low of day t (the "gap low" stop). Maximum 5 positions, equal weight, skip if the index is below its 200-day average (practitioner filter).
- **Instruments.** Cash equities.
- **Holding period.** 5 to 60 trading days.
- **Reported performance.** No source with a sample and costs was found. Indian practitioner pages describe "earnings gap" and "gap and go" setups without statistics; Trendlyne-style screener backtests apply today's index constituents to the past (survivorship bias).
- **India evidence.** None of research quality.
- **Costs and capacity.** About 0.5% a round trip plus the cost of buying after a gap.
- **Failure modes.** Mixes earnings with operator-driven spikes and block deals; exhaustion gaps; cluster risk in results season.
- **Feasibility.** Yes to trade, unproven. Included because it is the only earnings-type rule that can be backtested from daily OHLCV alone.
- **Sources.** https://quantpedia.com/strategies/post-earnings-announcement-effect/ (for the underlying drift only).

#### S04. Triple-sorted momentum: price, earnings surprise and revenue surprise

- **Rules.** Universe: BSE 500 or Nifty 500. Each month rank stocks on (a) prior 6-month return, (b) latest earnings surprise, (c) latest revenue surprise (year-on-year seasonal change, standardised). Long stocks in the top group on all three; hold up to 6 months with monthly cohorts. The abstract does not give breakpoints; test terciles and quintiles. 5 to 10 names.
- **Instruments.** Cash equities.
- **Holding period.** 1 to 6 months.
- **Reported performance.** Sehgal and Jain (2015), 493 BSE 500 companies, January 2002 to June 2010: momentum profits persist up to six months; price-momentum winners earn more than earnings or revenue winners; on a long-short basis earnings momentum is the most profitable and subsumes the other two; the triple-sorted portfolio earns the highest return, **2.28% a month**, unexplained by CAPM or Fama-French; strong reversal after the holding period.
- **India evidence.** Yes, but the sample ends in 2010 and is gross of costs. The paper's literature review notes Griffin et al. found insignificant price and earnings momentum profits for India in an earlier cross-country sample.
- **Costs and capacity.** Monthly turnover could reach 100% a year or more; 2 to 4% a year in costs.
- **Failure modes.** Momentum crashes; 2002 to 2010 was a strong bull phase plus one crash; data-snooped breakpoints.
- **Feasibility.** Yes. Probably overlaps heavily with the momentum researchers' strategies; the event part is the earnings filter.
- **Sources.** https://ejournal.usm.my/aamjaf/article/view/aamjaf_vol11-no1-2015_3

#### S05. Negative earnings surprise: exit rule, or short via futures

- **Rules.** After any result where UE falls in the bottom quartile (previous-quarter breakpoints) or the 3-day announcement return is in the bottom quintile: (a) overlay version: sell the stock if held and block new buys for 63 trading days; (b) short version: short the near-month stock future at the open of day +2, hold 63 trading days, roll once, stop at +12%.
- **Instruments.** Overlay on cash holdings; stock futures for the short.
- **Holding period.** 63 trading days.
- **Reported performance.** India 2008 to 2014: bottom UE quartile −6.6% market-adjusted over days +2 to +64, second quartile −2.0%. A Nottingham dissertation on 665 BSE 500 events (FY2007 to 2012) reports a negative drift lasting over a week after bad news and none after good news (unverified: snippet only).
- **India evidence.** Yes; this is where the Indian drift is.
- **Costs and capacity.** Overlay costs nothing extra. Short version: futures brokerage ₹40 a round trip plus 0.05% STT, but one lot's margin can exceed the whole account.
- **Failure modes.** Short squeezes in a rising market; F&O universe is large-cap where drift is weakest; margin calls.
- **Feasibility.** Overlay yes; short version no at ₹1.5 lakh.
- **Sources.** https://nsearchives.nseindia.com/research/content/NSE-IGIDR-WP4-14-15.pdf

#### S06. Holding through the results announcement (earnings-announcement premium)

- **Rules.** Buy at the close two sessions before a scheduled results date, sell at the close one session after. Optional filter: only stocks whose previous quarter's UE was in the top quartile.
- **Instruments.** Cash equities (or intraday on results day).
- **Holding period.** 3 trading days.
- **Reported performance.** India 2008 to 2014: mean 3-day market-adjusted announcement return over 18,269 announcements was **−0.5%** (median −0.7%), with about 57% negative. By UE quartile the 3-day return ran from −1.9% to +1.4%, but that sort uses the same quarter's surprise, which is unknown beforehand.
- **India evidence.** Yes, negative.
- **Costs and capacity.** 0.5% a round trip on a 3-day trade with negative expectation.
- **Failure modes.** The whole premise.
- **Feasibility.** Tradable, but the evidence says do not. Listed so the backtest can confirm and close the idea.
- **Sources.** https://nsearchives.nseindia.com/research/content/NSE-IGIDR-WP4-14-15.pdf

#### S07. Analyst BUY recommendation drift

- **Rules.** Universe: Nifty 50 (source) or Nifty 100. Event: a new BUY or an upgrade to BUY from a broker. Buy at the next open, hold 20 trading days (test 10 to 60), equal weight, maximum 5 positions, one entry per stock per 20 days. Ignore SELL calls (rare in India, and cannot be shorted).
- **Instruments.** Cash equities.
- **Holding period.** 2 to 12 weeks.
- **Reported performance.** Moulya and Mallikarjunappa (South Asian Journal of Management), Nifty 50 firms 2012 to 2018: no significant price reaction on the announcement day but a delayed response and drift after bullish recommendations, read as under-reaction; magnitudes not extracted. An IIM Bangalore Management Review study of time-to-target concludes that post-recommendation market movement, not analyst insight, drives whether targets are reached.
- **India evidence.** Yes, weak and mixed.
- **Costs and capacity.** Needs a recommendations feed (Trendlyne and similar are paid or need scraping).
- **Failure modes.** Analysts are heavily tilted to BUY, so the signal fires constantly; reports reach paying clients first; no clean timestamp.
- **Feasibility.** Marginal: data is the obstacle, not capital.
- **Sources.** https://www.cukerala.ac.in/cukpdfs/IQAC/3.4.5/3.4.5.DCIB.001.pdf ; https://www.iimb.ac.in/imr/previous-issues/time-june-2020.php

### B. Insiders, large trades and governance flags

#### S08. Promoter and insider open-market buying (PIT disclosures)

- **Rules.** Universe: NSE stocks with market cap ₹500 crore to ₹20,000 crore, turnover above ₹2 crore a day. Event: PIT Regulation 7 disclosure where category is promoter, promoter group, director or KMP, mode is market purchase, and value is at least ₹1 crore or 0.05% of market cap (test thresholds); stronger if two or more insiders buy within 30 days and the stock is down over the prior 3 months (insiders in India buy after declines). Buy at the open after the exchange disclosure. Hold 90 trading days (test 60 to 250). Maximum 6 positions, equal weight, stop 20%.
- **Instruments.** Cash equities.
- **Holding period.** 3 to 12 months.
- **Reported performance.** Krishnan and Rangan, about 32,000 insider trading days, 2008 to 2014: market-adjusted return after buys was −0.20% at one month; buy-minus-sell spread 0.28% at one month, 1.53% at three months, **8.22% at one year**, with most of the profit coming from sells preceding declines; mean 3-month return before buys −3.87% (contrarian buying). A 2026 Springer (Decision) paper on PIT-disclosed purchases reports about +6.67% cumulative abnormal return over 90 days, strongest in smaller firms (unverified: snippet only). An SSRN study of 1,101 BSE insider transactions 2009 to 2013 finds abnormal returns in the first month that fade (unverified: snippet only).
- **India evidence.** Yes, moderately supportive at 3 to 12 months, not at one month.
- **Costs and capacity.** Low turnover; cost drag about 1 to 2% a year.
- **Failure modes.** Creeping acquisitions and price-support buying are not information; inter-se transfers, ESOP, pledge invocations and preferential allotments must be filtered out; disclosure lag (insider to company within two trading days, company to exchange within two more; from memory, not re-verified); small-cap illiquidity.
- **Feasibility.** Yes. One of the better fits: long-only, slow, small positions are fine, data is free on NSE.
- **Sources.** https://nsearchives.nseindia.com/research/content/NSE-IGIDR-WP4-14-15.pdf

#### S09. Red-flag exclusion overlay: insider selling, pledge increases, rating downgrades

- **Rules.** Remove a stock from every long universe for N trading days after any of: (a) net insider/promoter market sales above ₹1 crore in 30 days (N = 250); (b) promoter pledge share of promoter holding rising by 5 points or more quarter on quarter, or pledged above 25% of promoter holding (until it falls); (c) a long-term credit rating downgrade by CRISIL, ICRA or CARE (N = 60). Upgrades are ignored.
- **Instruments.** Filter on other strategies.
- **Holding period.** Not applicable.
- **Reported performance.** Insider sells: the 8.22% one-year buy-minus-sell spread is mostly sells preceding declines (2008 to 2014). Pledging: Kalia (2024), 257 BSE 500 firms 2011 to 2020, pledging is positively related to future crash risk and negatively to future operating performance. Ratings: Dawar, Bhatia and Bindal (2023), top 100 NSE firms 2009 to 2019, most of the price effect is in the pre-event window and downgrades matter more than upgrades; Kushwah and Vigg (2023), Indian banks, returns negative before and on the downgrade day and insignificantly positive afterwards.
- **India evidence.** Yes. For downgrades it says the damage is mostly done before the announcement, so the overlay is a risk control rather than a return source.
- **Costs and capacity.** None.
- **Failure modes.** Filters remove recovery candidates; pledge data is quarterly and late.
- **Feasibility.** Yes.
- **Sources.** https://nsearchives.nseindia.com/research/content/NSE-IGIDR-WP4-14-15.pdf ; https://ideas.repec.org/a/eme/jamrpp/jamr-01-2023-0003.html ; https://som.iitkgp.ac.in/pdf/Working%20Paper/Kousik%20Ganguly_1.pdf ; https://econpapers.repec.org/RePEc:sae:busper:v:11:y:2023:i:2:p:190-209 ; https://econpapers.repec.org/RePEc:ids:afasfa:v:13:y:2023:i:1:p:41-53

#### S10. Following bulk-deal buyers (negative evidence)

- **Rules.** Event: the NSE bulk-deal file shows a client buying more than 0.5% of a company's shares with no bulk sell in the same stock that day ("Only Buy"). Buy at the next open, hold 5 trading days (test 1 to 7).
- **Instruments.** Cash equities.
- **Holding period.** 1 to 7 days.
- **Reported performance.** Rajvanshi (IIM Calcutta WPS 863), NSE bulk deals 2010 to 2019 (81,506 records): for Only-Buy deals by a single investor (N = 1,804) average abnormal return was +2.84% cumulative over days −7 to −1, +3.46% on day 0, +0.71% on day +1, then **negative every day from +2 to +7 (sum about −1.1%)**. Partial-buy days (N = 2,040): +4.19% on day 0, then −0.07% on day +1 and about −2.0% over days +2 to +7. The paper's own framing is that front-runners with advance knowledge earn 5 to 7% in a week. Chaturvedula et al. (2015), 2004 to 2012, same pattern of large returns around the trade.
- **India evidence.** Yes, negative for a follower: the disclosure arrives after the close of day 0, when the move is over, and prices then drift down.
- **Costs and capacity.** 0.5% a round trip on a trade with a negative expected drift after day +1.
- **Failure modes.** You are the exit liquidity; many names are operator-driven.
- **Feasibility.** Tradable but should not be traded.
- **Sources.** https://studentlive.iimcal.ac.in/sites/all/files/pdfs/wp_863.pdf ; https://econpapers.repec.org/RePEc:eee:ememar:v:23:y:2015:i:c:p:26-45 ; https://nsearchives.nseindia.com/content/equities/bulk.csv

#### S11. Rebound after bulk-deal selling

- **Rules.** Event: "Only Sell" bulk deal (a client sells more than 0.5% of equity, no bulk buy that day), stock down on day 0, price above ₹20, turnover above ₹2 crore. Buy at the close of day 0 if the file is available before the close (it is not: published after hours), otherwise at the open of day +1. Hold 5 trading days. Stop 5%.
- **Instruments.** Cash equities.
- **Holding period.** 3 to 7 days.
- **Reported performance.** Same paper: Only-Sell deals by a single investor (N = 2,831): −1.34% cumulative over days −7 to −1, −0.87% on day 0, then +0.38%, +0.26%, +0.16%, +0.08%, +0.05%, +0.06%, +0.04% on days +1 to +7 (**about +1.0% cumulative**). Multi-investor Only-Sell (N = 77): −1.94% on day 0, +1.63% and +1.51% on days +1 and +2.
- **India evidence.** Yes, small.
- **Costs and capacity.** The day +1 return is close-to-close, so an entry at the next open misses part of it; 1.0% gross minus 0.5% costs minus slippage is about zero.
- **Failure modes.** A seller with real information (promoter exit, fund liquidation) keeps selling; few multi-investor events.
- **Feasibility.** Marginal: does not clear costs on the published averages.
- **Sources.** https://studentlive.iimcal.ac.in/sites/all/files/pdfs/wp_863.pdf

#### S12. Block-deal purchases by long-term institutions or insiders

- **Rules.** Event: block-window purchase where the buyer is a mutual fund, insurer, pension or sovereign fund ("pressure-resistant") or a promoter entity, and the seller is not a promoter. Buy at the next open, hold 3 trading days (source window) or test 20 days. Classification by client name against the shareholding pattern.
- **Instruments.** Cash equities, mostly large and mid caps.
- **Holding period.** 3 to 20 days.
- **Reported performance.** Ranganathan and Singh (NSE-IGIDR), 2,547 buy-side and 2,320 sell-side block trades 2005 to 2015: three-day Fama-French-adjusted cumulative abnormal return is positive for purchases by pressure-resistant institutions and by insiders, stronger after the 2010 governance reforms; magnitudes were not legible in the extract.
- **India evidence.** Yes, but the window is centred on the trade date, so part of the return precedes public knowledge.
- **Costs and capacity.** Three-day holds need more than 0.5% net of the gap.
- **Failure modes.** Block price is usually at a discount to market; the block-deal framework and minimum size have changed since the sample (2025 changes: from memory, not re-verified).
- **Feasibility.** Marginal.
- **Sources.** https://nsearchives.nseindia.com/research/content/NSE-IGIDR_CG_RPaper_2015-16_WP4.pdf ; https://nsearchives.nseindia.com/content/equities/block.csv

### C. Index events

#### S13. Index inclusion: announcement to effective date (Nifty 50, Nifty Next 50, MSCI India)

- **Rules.** Event: official announcement of an addition. Nifty: press release from NSE Indices (normally after market hours: from memory, not re-verified), roughly 4 to 5 weeks before the effective date; for example announced 23 February 2026, effective 30 March 2026 (review uses six months of data ending 31 January and 31 July; changes take effect on the last trading day of March and September; four weeks' notice). MSCI: announcement about 3:30 am IST in February, May, August and November, effective about two to three weeks later. Buy at the open of the first session after the announcement (AD+1). Sell at the close of the last session before the effective date (ED−1), where passive funds buy. Do not hold past ED−1. Position 25 to 33% of capital per event. Skip if the stock gaps up more than 5% at the open of AD+1.
- **Instruments.** Cash equities; all Nifty 50 additions and most MSCI additions are liquid.
- **Holding period.** 10 to 25 trading days.
- **Reported performance.** Global MSCI changes, 56 markets, 2006 to 2023 (Chang et al., NTU summary): long additions and short deletions from the AD close to the ED−1 close earns about **5.4%** abnormal after stock-lending fees; 6.1% in Asia-Pacific, 2.8% in North America; ED−1 volume over 10 times normal, nearly half of it in the final minute; index trackers are waiting less than they used to. Nifty: Kumar (NSE research paper), 1996 to 2003, 23 additions: no significant announcement-day effect, effective-day abnormal return +1.47% (deletions −1.60%), reversed by the ninth day. Joshipura and Janakiramanan (2015): no significant positive return around announcement; positive on the effective day, not sustained. Chhatwani (2020), 2000 to 2016: positive abnormal returns after inclusion that reverse within 60 days. Marketcalls (practitioner, unsourced): MSCI India inclusions "typically rally 1 to 7% in the first week". Example of scale: the September 2026 review put BSE into the Nifty 50 in place of Wipro with estimated passive inflow of about $639 million and outflow of $206 million (JM Financial).
- **India evidence.** Mixed. The Indian studies find the effect on the effective day, not at announcement, and it reverses. JM Financial's five-year look: additions are "frequently a sell-the-news event".
- **Costs and capacity.** One to four Nifty 50 changes a year, perhaps 15 to 30 MSCI India additions; 0.4 to 0.5% a round trip.
- **Failure modes.** Additions are widely predicted by brokers weeks ahead, so the run-up happens before the announcement; the US index effect fell from 7.4% in the 1990s to under 1% in the 2010s (Greenwood and Sammon); market direction over a 3-week hold swamps a 1 to 3% effect; long leg only (the published 5.4% includes the short side).
- **Feasibility.** Yes to trade. Few events and long-only make it a small contributor.
- **Sources.** https://nsearchives.nseindia.com/content/indices/Method_NIFTY_Equity_Indices.pdf ; https://niftyindices.com/Press_Release/ind_prs23022026.pdf ; https://www.ntu.edu.sg/business/research/nbs-knowledge-lab/nbs-research-blog/index-tracking-rigidity-and-arbitrage-opportunities-in-msci-index-reconstitutions ; https://nsearchives.nseindia.com/content/research/comppaper90.pdf ; https://ideas.repec.org/a/ids/afasfa/v5y2015i1p21-36.html ; https://www.publishingindia.com/archive/jcar/price-and-volume-effects-of-nifty-50-index-reorganization ; https://www.jmfinancialservices.in/blogs-and-articles/bse-replaces-wipro-in-nifty-50-sept-2026 ; https://alphaarchitect.com/disappearing-index-effect/ ; https://www.marketcalls.in/investment/msci-rebalancing-explained-a-comprehensive-guide-for-indian-investors-and-traders.html

#### S14. Index deletion rebound

- **Rules.** Event: a stock leaves the Nifty 50 (or MSCI India). Buy at the close of ED−1 (the forced-selling session) or on the effective date. Hold 120 trading days (test 60 to 240). Skip deletions caused by merger, delisting, suspension or regulatory orders. Optional filter: positive trailing-twelve-month profit. Up to 25% of capital per name. Stop 20%.
- **Instruments.** Cash equities.
- **Holding period.** 3 to 12 months.
- **Reported performance.** Chhatwani (2020), Nifty 50 changes 2000 to 2016: excluded stocks have negative abnormal returns only in the first ten days, then **+4% to +7% abnormal over 60 to 240 days** after exclusion. DSIJ (2019), MSCI India 2015 to 2019: average one-year-after return 16% for excluded versus 8% for included; excluded stocks had fallen 49% in the prior year. JM Financial (2026), last five years of Nifty 50 changes: 7 of the last 10 removed stocks rose over the next six months and 9 of 10 within a year, versus 7 of 11 and 6 of 11 for added stocks. Kumar (1996 to 2003): −1.60% on the effective day, reversed.
- **India evidence.** Yes, consistent across three independent looks, all small samples and gross of costs.
- **Costs and capacity.** Negligible turnover.
- **Failure modes.** Deleted stocks are losers for a reason (Yes Bank, Vodafone Idea and Indiabulls Housing were 2019 MSCI deletions); two to four Nifty 50 events a year; mean reversion mixed with market beta.
- **Feasibility.** Yes. Long-only, liquid, slow.
- **Sources.** https://www.publishingindia.com/archive/jcar/price-and-volume-effects-of-nifty-50-index-reorganization ; https://insights.dsij.in/dsijarticledetail/msci-india-index-rebalancing-and-returns-10213 ; https://www.jmfinancialservices.in/blogs-and-articles/bse-replaces-wipro-in-nifty-50-sept-2026 ; https://nsearchives.nseindia.com/content/research/comppaper90.pdf

#### S15. Pre-positioning in predicted index additions

- **Rules.** Twice a year, on the first trading day after the cut-off (1 February, 1 August), compute for every Nifty 100 member that trades in F&O and is not in the Nifty 50 its six-month average free-float market cap. A stock qualifies if that figure is at least 1.5 times the six-month average free-float market cap of the smallest Nifty 50 constituent, its trading frequency was 100% and average impact cost at most 0.50% (for a ₹10 crore basket, 90% of observations). At most five additions per calendar year. Buy the top-ranked qualifier, hold to the announcement day close (variant: to ED−1). For MSCI, buy candidates 20 trading days before the announcement using published broker candidate lists. One or two names, 25% of capital each.
- **Instruments.** Cash equities.
- **Holding period.** 3 to 8 weeks.
- **Reported performance.** No tested Indian result. A JM Financial note claims 8 to 15% cumulative excess return in the 20 trading days before MSCI announcements for high-conviction candidates (unverified: snippet only; broker claim). Greenwood and Sammon report that pre-announcement run-ups in the US have become "somewhat stronger" as the announcement effect disappeared.
- **India evidence.** None beyond broker claims.
- **Costs and capacity.** Trivial.
- **Failure modes.** Free-float factors and the committee's discretion make the forecast imperfect; candidates qualify because they have already rallied (BSE was up about 55% year to date before its inclusion), so this is partly a momentum trade; brokers publish the same lists months ahead.
- **Feasibility.** Marginal: needs free-float share data and gives one or two trades a year.
- **Sources.** https://nsearchives.nseindia.com/content/indices/Method_NIFTY_Equity_Indices.pdf ; https://www.jmfinancialservices.in/blogs-and-articles/bse-replaces-wipro-in-nifty-50-sept-2026 ; https://alphaarchitect.com/disappearing-index-effect/

#### S16. F&O list inclusion and exclusion

- **Rules.** Inclusion: buy at the open after the NSE circular announcing new F&O stocks, sell at the close of the first day of F&O trading (variant: hold 20 days). Exclusion: avoid or sell on the circular. Daily-data variant: inclusion date = first day the symbol appears in the F&O bhavcopy; pending exclusion = the symbol has no contract for the newest expiry month while other stocks do.
- **Instruments.** Cash equities.
- **Holding period.** 2 to 6 weeks.
- **Reported performance.** An Indian Economic Journal event study, 2001 to 2020, finds positive price reaction on inclusion and negative on exclusion, driven by liquidity and volatility (unverified: snippet only). DSIJ (2024): of the 11 stocks added in December 2021 and January 2022, six-month returns after inclusion were mostly negative (for example Aditya Birla Capital −27%, Hindustan Copper −30%, Honeywell Automation −18%, IDFC −15%; ABB +22%, GNFC +29%).
- **India evidence.** Mixed: a short-window positive effect, no sustained gain.
- **Costs and capacity.** Infrequent, lumpy (45 stocks were added at once in November 2024).
- **Failure modes.** New shorting capacity arrives with inclusion; eligibility criteria changed in 2024.
- **Feasibility.** Marginal.
- **Sources.** https://insights.dsij.in/dsijarticledetail/the-fo-effect-with-45-stocks-set-to-be-included-in-new-additions-drive-stock-prices-a-look-into-previous-inclusion-performances-id015

### D. Tender-type corporate actions

#### S17. Tender-offer buyback through the small-shareholder quota

- **Rules.**
  1. Event: board approves a buyback by tender offer at price P_b. (SEBI's board memorandum of 19 June 2026 proposed re-introducing open-market buybacks through the exchange from 1 August 2026; implementation was not re-verified. Those have no fixed price and no quota, so they are excluded.)
  2. Eligibility: hold the shares on the record date with total value at most ₹2,00,000 at the record-date close. Fifteen percent of the buyback, or the small shareholders' proportionate entitlement if higher, is reserved for this category. The tender window is five working days.
  3. Estimate the acceptance ratio AR before entry. Floor: AR_min = reserved shares / shares held by small shareholders (use "individuals holding nominal capital up to ₹2 lakh" in the shareholding pattern as a proxy). Realistic: AR_min / expected participation (Capitalmind assumed AR_min 14% and a realistic 25 to 30% for L&T).
  4. Enter only if premium = P_b / P_0 − 1 is at least 10% and AR × premium is at least 3%, and the stock is one you could hold: breakeven price for the unaccepted shares is P_0 − [AR/(1−AR)] × (P_b − P_0).
  5. Size: N = floor(min(capital × 0.6, ₹1.9 lakh) / P_0), checked again so that N × record-date close stays under ₹2 lakh. Buy between announcement and one trading day before the record date.
  6. Tender all N shares. Sell the returned shares at the open after they are credited back, or hold with a stop at the breakeven price.
- **Instruments.** Cash equities plus the tender mechanism (broker's corporate-action window).
- **Holding period.** 3 to 10 weeks.
- **Reported performance.** Case evidence only. HCL Technologies 2017: 148 of every 220 tendered shares accepted (67%), about 10% in three months (Capitalmind). TCS 2022 (₹18,000 crore at ₹4,500, market about ₹3,900 to ₹4,000): retail entitlement 1 in 7, likely acceptance about 25%, well below the 30 to 40% "worst case" commentators had assumed, with over ten lakh tendering shareholders; break-even needed the stock above about ₹3,800 afterwards (PrimeInvestor). L&T 2023 (₹10,000 crore at ₹3,200, record-date close ₹2,948.5, premium 8.5%): expected acceptance 25 to 30% (Capitalmind). Infosys 2025 (₹18,000 crore at ₹1,800, record date 14 November 2025): small-shareholder entitlement 2 for 11 (18.2%), 25.86 lakh small shareholders; the general-category entitlement was 17 for 706 (unverified: snippet only); final acceptance not found. Bharti Infratel 2016 about 8.7% in two months, TCS 2017 about 6%, Jagran 2017 acceptance about 40% against near-full expected (unverified: snippet only).
- **India evidence.** Yes, practitioner. The pattern is a decaying edge: near-full acceptance in 2016, two-thirds in 2017, about a quarter by 2022 to 2023 as the trade became crowded.
- **Costs and capacity.** One buy plus one sell of the unaccepted part; costs under 0.5% of position. Capacity is capped by law at ₹2 lakh per PAN per buyback, which suits this account. Illustration (my arithmetic): premium 12%, AR 25%, leftover sold 2% below cost gives 0.25 × 12% − 0.75 × 2% = +1.5% before costs and tax in about six weeks.
- **Failure modes.** Acceptance ratio lower than assumed; stock falls after the buyback closes when arbitrage holders dump leftovers; market drawdown over the holding period (this is an unhedged single-stock position of up to the whole account); the board can withdraw or delay; PAN-level clubbing of holdings across demat accounts; **tax regime risk** (three regimes in three years). Under the October 2024 to March 2026 dividend treatment the trade was loss-making after tax; it is viable again only since 1 April 2026.
- **Feasibility.** Yes, and structurally the best-matched special situation for this account size. Automation is partial unless tendering can be done by API.
- **Sources.** https://taxguru.in/sebi/sebi-reintroduces-open-market-buy-back-due-tax-neutrality-shareholders.html ; https://www.scconline.com/blog/post/2026/07/16/finance-act-2026-share-buyback-taxation-analysis/ ; https://taxguru.in/income-tax/buyback-tax-reset-finance-act-2026-game-shareholders.html ; https://primeinvestor.in/reports/the-share-buyback-game-isnt-worth-it/ ; https://premium.capitalmind.in/2023/09/larsen-and-toubro-buyback-analysis/ ; https://capitalmind.in/2017/07/bond-baba-unlocked-hcl-tech-accepts-23rd-of-buyback-a-10-return-in-3-months/ ; https://www.icicidirect.com/research/equity/finace/infosys-buyback-2025-complete-guide-for-shareholders ; https://www.ipoji.com/buyback/infosys-buyback-2025 ; https://www.chittorgarh.com/report/latest-buyback-issues-in-india/80/tender-offer-buyback/

#### S18. Buyback announcement drift (no tendering)

- **Rules.** Event: board-meeting intimation "to consider buyback", or the approval itself. Buy at the next open; sell at the close two sessions before the record date (variant: 10 trading days). Tender-offer buybacks only, premium at least 10%, buyback size at least 2% of equity. Maximum 3 positions.
- **Instruments.** Cash equities.
- **Holding period.** 1 to 6 weeks.
- **Reported performance.** IIM Ahmedabad working paper: significant positive abnormal returns around the announcement of both tender and open-market repurchases in India; open-market repurchasers later underperform peers on operating measures and most such programmes follow sharp price declines (price support), so the market over-reacts to them. A 2025 Finance Research Letters paper on 2006 to 2024 buybacks reports significant pre-announcement abnormal returns attributed to leakage, 5.9% after 2015 (unverified: snippet only).
- **India evidence.** Yes for the announcement window; much of it arrives before the public announcement.
- **Costs and capacity.** 0.5% a round trip against an unquantified post-announcement drift.
- **Failure modes.** Leakage means the public buyer is late; price converges to a blend of P_b and fair value, not to P_b.
- **Feasibility.** Marginal.
- **Sources.** https://www.iima.ac.in/publication/market-overreaction-poor-long-run-performance-case-repurchase-firms-india

#### S19. Open-offer (takeover) tender arbitrage

- **Rules.** Event: public announcement of an open offer under the takeover regulations at price P_o for X% of shares (normally 26%: from memory, not re-verified). Enter only if the market price is at least 5% below P_o after costs and the expected acceptance (offer size / expected tendered public float) is at least 50%. Tender all shares; sell leftovers after the offer closes. Alternative that usually dominates: sell in the market whenever the price trades at or above P_o.
- **Instruments.** Cash equities plus the tender window.
- **Holding period.** 2 to 4 months (regulatory approvals).
- **Reported performance.** Verma and Mittal: 31 open offers above ₹100 crore, 2015 to 2017, higher cumulative abnormal returns in days 0 to +30 than in the 30 days before. Nangia et al.: 187 offers 2007 to 2010, significantly negative returns after the announcement. Business Standard (2014): 133 open offers since 2013, "only a handful" obtained the proposed stake; in United Spirits the market expected 70% acceptance and got 55%, leaving arbitrageurs holding leftover stock; professional arbitrageurs hedge the expected unaccepted part by shorting futures.
- **India evidence.** Mixed to negative for unhedged retail participation.
- **Costs and capacity.** The 2014 article says tendered shares were treated as off-market sales (no STT), so short-term gains were taxed at slab rate; whether that still holds for exchange-window tenders in 2026 was not checked.
- **Failure modes.** Partial acceptance, long approval delays, price collapse after the offer, offer withdrawal, no hedge available to a small account.
- **Feasibility.** Marginal.
- **Sources.** https://rd.springer.com/chapter/10.1007/978-981-10-8926-8_14 ; https://ideas.repec.org/p/pra/mprapa/60432.html ; https://www.business-standard.com/article/pf/why-open-offers-aren-t-attractive-for-many-investors-114101300002_1.html

#### S20. Voluntary delisting: reverse book-building and fixed-price offers

- **Rules.** Event: promoter announces intent to delist. Reverse book-building (RBB) version: buy after the announcement if price is within 15% of the floor price; tender in the RBB at a bid of 1.3 to 1.6 times floor; if the discovered price is rejected and no counter-offer succeeds, exit at market. Fixed-price version (allowed since the 2024 amendments, only for frequently traded shares, price at least 15% above the floor): treat as a merger-arbitrage spread: buy only if the market price is at least 4% below the fixed price and promoter-plus-committed holders plausibly reach 90%. Hard stop 12% below entry; position at most 20% of capital.
- **Instruments.** Cash equities plus the tender window.
- **Holding period.** 2 to 6 months.
- **Reported performance.** No systematic study found. Law-firm and press descriptions: success needs the acquirer to reach 90%; RBB discovered prices have "at times" been more than double the floor price; a holder of 1 to 2% can block the offer; a counter-offer is allowed if post-offer holding would be at least 75% and at least half the public float was tendered (2024 amendment); "one can never have statistics of failed delisting deals".
- **India evidence.** Anecdotal.
- **Costs and capacity.** Normal.
- **Failure modes.** Failed delistings fall back toward or below the pre-announcement price; long timelines; illiquid names.
- **Feasibility.** Marginal: binary outcomes, a handful of events a year, cannot be backtested from price data.
- **Sources.** https://www.azbpartners.com/bank/amendments-to-sebi-delisting-of-equity-shares-regulations-2021/ ; https://trilegal.com/knowledge-repository/trilegal-update-sebi-allows-delisting-through-a-fixed-price-offer/ ; https://www.business-standard.com/article/opinion/stepping-forward-with-delisting-reform-118091901151_1.html

#### S21. Share-swap merger arbitrage, long target only

- **Rules.** Event: scheme of amalgamation with swap ratio r (acquirer shares per target share). Spread = r × P_acquirer / P_target − 1. Enter the target when the spread is at least 6% and the record date is expected within 6 months; exit when the spread is below 1% or on the record date. A hedged version shorts the acquirer's futures in ratio and needs both to be in F&O.
- **Instruments.** Cash equities; futures for the hedge.
- **Holding period.** 1 to 18 months.
- **Reported performance.** Examples only. Harita Seating into Minda Industries (2019): 152 Minda shares per 100 Harita; implied gain 8.13% gross, 6.92% after the then 15% short-term tax, with a loss if Minda fell more than 7% and no hedge because Minda was not in F&O (Capitalmind). HDFC into HDFC Bank (25:42, about 15 months to complete): spread 1 to 3% (unverified: snippet only).
- **India evidence.** Anecdotal.
- **Costs and capacity.** Capital tied up for many months for a single-digit gross spread.
- **Failure modes.** Unhedged, the position is simply long the acquirer through a proxy; NCLT and regulator delays; deal break; ratio revision.
- **Feasibility.** Marginal unhedged, no hedged.
- **Sources.** https://premium.capitalmind.in/2019/02/the-uno-minda-and-harita-merger-is-there-an-arbitrage-opp/

#### S22. Demerger announcement drift

- **Rules.** Event: board approves a demerger (spin-off) scheme. Buy the parent at the next open; hold 5 trading days (source window +1 to +5), variant 10 days. Prefer low-priced stocks (source split). Maximum 3 positions.
- **Instruments.** Cash equities.
- **Holding period.** 1 to 2 weeks.
- **Reported performance.** Gupta, Kumar and Chattopadhyay (2022), 221 BSE firms 2003 to 2020: highest average abnormal return +1.35% on day +1; cumulative average abnormal return **2.64% over days +1 to +5**; over days −10 to +10, 3.90% for high-priced and 7.16% for low-priced stocks. Vyas, Pathak and Saraf (2015), 51 demergers 2012 to 2014: +1.74% on announcement falling to +0.16% ten days later. A 2024 Managerial Finance study of 160 announcements 2010 to 2023 reports −1.06% for pure spin-offs versus +8.27% for composite schemes over a 41-day window (unverified: snippet only).
- **India evidence.** Yes, supportive but small; day +1 is partly the opening gap.
- **Costs and capacity.** 2.6% gross minus about 0.5% costs minus whatever part of day +1 is in the opening gap.
- **Failure modes.** Announcement time-stamps; low-priced names are illiquid; pure demergers may show no effect.
- **Feasibility.** Marginal.
- **Sources.** https://econpapers.repec.org/RePEc:taf:oaefxx:v:10:y:2022:i:1:p:2109277 ; https://indianjournals.com/article/jmpp1-7-1-002

#### S23. Newly listed demerged entity (post-listing spin-off)

- **Rules.** Event: the demerged company lists (it often opens with several sessions at the price band as holders who cannot or do not want to own it sell). Wait for the first session that does not close at the lower band, then buy at the next open; hold 250 trading days; stop 25%. Skip entities with losses in the last reported year.
- **Instruments.** Cash equities.
- **Holding period.** 6 to 12 months.
- **Reported performance.** No Indian study with a sample found. Outlook Business (2015): "almost 50%" of listed spin-offs gave negative returns, with wide dispersion (Gulf Oil Lubricants about +90% after listing versus +5% for the parent; Future Retail −45% in six months after separating Future Lifestyle) (figures unverified: snippet only; I opened the article but did not reach these lines).
- **India evidence.** Anecdotal, mixed.
- **Costs and capacity.** Low turnover.
- **Failure modes.** No price history, limited disclosure, lower-circuit lock at the start, high dispersion with few events.
- **Feasibility.** Marginal.
- **Sources.** https://www.outlookbusiness.com/markets-5/feature-20/looks-good-but-far-from-scrumptious-1908

#### S24. Rights-entitlement (RE) discount arbitrage

- **Rules.** During a rights issue the entitlement trades as a separate security. Signal: P_share − (P_RE + issue price) is at least 3% of P_share after costs, with the share liquid. Buy the RE, apply for the rights shares, sell the shares when credited. A holder can do the reverse switch: sell shares, buy RE, subscribe. An RE that is neither sold nor subscribed lapses worthless (from memory, not re-verified).
- **Instruments.** RE, cash equities, rights application.
- **Holding period.** 2 to 4 weeks.
- **Reported performance.** No study found. Timeline since 7 April 2025: the whole issue completes in 23 working days from board approval (previous average 317 days), record date within about four working days, entitlements credited within nine, subscription window 7 to 30 days.
- **India evidence.** None on the arbitrage. On the issuers: Deb and Kamisetty (NSE working paper), 177 rights issues and FPOs, 2000 to 2014: buying at the first-day close and holding five years returned 17% less (about 3% a year) than matched firms.
- **Costs and capacity.** RE liquidity is thin; the hedge (shorting the share until allotment) is not available overnight in cash.
- **Failure modes.** Share price falls below the issue price before allotment; RE trading closes before the issue does; application cannot be automated.
- **Feasibility.** Marginal.
- **Sources.** https://moneylife.in/article/rights-issues-sebi-reduces-timeline-to-23-working-days-from-average-of-317-days/76623.html ; https://nsearchives.nseindia.com/research/content/res_WorkingPaper15.pdf

#### S25. Equity-issuer avoidance: QIP, rights issue, FPO

- **Rules.** Exclude a stock from long universes for 126 trading days after a QIP opens (source horizons 3 and 6 months) and 250 days after a rights issue or FPO.
- **Instruments.** Filter.
- **Holding period.** Not applicable.
- **Reported performance.** A 2018 practitioner article republished on the npbang blog, 84 QIPs 2010 to 2016: average 3-month and 6-month holding returns for QIP buyers negative in every year and below the BSE 500, despite an issue discount of up to 5% to the two-week average floor price. Rights/FPO: −17% over five years versus matched firms (2000 to 2014). Banerjee and Guha Deb (2015): the market reacts positively to QIP announcements only when promoter holding is low.
- **India evidence.** Yes.
- **Costs and capacity.** None.
- **Failure modes.** Excludes growth companies raising capital for good reasons.
- **Feasibility.** Yes.
- **Sources.** https://npbang.blogspot.com/2018/06 ; https://nsearchives.nseindia.com/research/content/res_WorkingPaper15.pdf ; https://ideas.repec.org/a/sae/globus/v16y2015i5_supplp155s-174s.html

#### S26. OFS retail-discount capture

- **Rules.** Event: offer for sale through the exchange with a retail reservation and a retail discount d to the cut-off price. Retail investors bid on the second day (from memory, not re-verified). Bid at cut-off for up to 30% of capital only if (previous close − floor price × (1 − d)) / previous close is at least 4% and the first-day non-retail book is at least 2 times subscribed. Sell at the open on the day shares are credited.
- **Instruments.** OFS bid, then cash sale.
- **Holding period.** 1 to 3 days.
- **Reported performance.** No return study found. Maheshwari and Chatnani (2025), 39 OFS on NSE, March 2012 to July 2023: significant price declines in the cash and derivatives segments **before** PSU OFS announcements (floor-price leakage), cash-segment declines before non-PSU ones. Examples: Mazagon Dock April 2025 floor about 8% below the prior close; IRFC February 2026 floor ₹104 with no retail discount and the stock at ₹104.56 (both unverified: snippet only).
- **India evidence.** Indirect, cautionary.
- **Costs and capacity.** Bid amounts are blocked for a day or two.
- **Failure modes.** The stock falls to or through the floor on OFS day, erasing the discount; no hedge; bids not placeable via API.
- **Feasibility.** Marginal.
- **Sources.** https://ideas.repec.org/a/eme/rbfpps/rbf-07-2024-0208.html

### E. Primary market and listings

#### S27. Mainboard IPO retail application with a subscription filter

- **Rules.** Universe: mainboard book-built IPOs (not SME). On the last day, after 14:00, apply for one retail lot at the cut-off price if QIB subscription (excluding anchors) is at least 20 times (test 10 to 50) and total subscription at least 10 times. Ignore grey-market premium, or use it only as a veto when negative. If allotted, sell on listing day: at the open, or with a stop at the issue price. One application per PAN.
- **Instruments.** IPO application (UPI/ASBA block), then cash sale.
- **Holding period.** About a week of blocked funds; minutes to a day of market exposure.
- **Reported performance.** SEBI study of 144 mainboard IPOs, April 2021 to December 2023: 75% (108) had positive listing returns, 26 gained more than 50%, 92 were oversubscribed more than 10 times and 2 were undersubscribed; individuals sold 50.2% of allotted value within a week (retail 42.7%), and 67.6% when the gain exceeded 20%. 2025: 108 mainboard IPOs, median listing gain **3.8% versus 15.2% in 2024**, 65% opened in profit; average listing gain about 8% in early 2026, the lowest since 2019 (ipomarket.in, secondary). Grey-market premium: in late 2025 NSDL, Orkla India and Tata Capital listed far below their GMP, Lenskart and Studds listed below issue price despite positive GMP, while Groww (GMP ₹3) listed 12% up and LG Electronics India (54 times subscribed) listed about 50% up (PL Capital, Upstox).
- **India evidence.** Yes. Listing gains are real on average but cyclical and shrinking, and the binding constraint is allotment, not selection.
- **Costs and capacity.** No brokerage on application; one sell order. In an oversubscribed retail book allotment is by lottery of one lot per successful applicant (from memory, not re-verified), so the chance is roughly 1 / (retail subscription multiple). Illustration (my arithmetic): lot ₹15,000, 30 times subscribed, 30% listing gain gives an expected ₹150 per application. Capital use is small, so several applications can overlap.
- **Failure modes.** Allotment mostly comes in the weak issues (winner's curse); listing below issue price; blocked funds; hot-market dependence.
- **Feasibility.** Yes, with small expected rupee value; application automation not confirmed.
- **Sources.** https://taxguru.in/sebi/sebi-report-54-percent-ipo-shares-sold-week.html ; https://www.ipomarket.in/news/build-long-term-portfolio-only-ipos-2025-26-data-risks ; https://www.plindia.com/news/gmp-misleading-investors-why-grey-market-premium-no-longer-predicts-ipo-listings-pl-capital/ ; https://upstox.com/news/market-news/ipo/groww-to-lenskart-here-s-how-misleading-grey-market-signals-confuse-investors/article-184620

#### S28. Buying IPOs in the secondary market on or after listing day

- **Rules.** Listing date = first day a symbol appears in the bhavcopy (exclude demerger listings and relistings). Variant A: buy at the listing-day close, hold 20, 60 or 250 trading days. Variant B (practitioner "IPO base"): after at least 15 sessions, buy the first close above the highest close since listing, stop at the lowest low of the last 10 sessions, exit on a close below the 50-day average or after 120 days.
- **Instruments.** Cash equities.
- **Holding period.** 1 to 12 months.
- **Reported performance.** Of the 108 mainboard IPOs of 2025, only 41% were above their **listing** price on 31 December 2025; in FY26 to date 26 of 107 traded above listing price (unverified: snippet only). A study of 377 IPOs from 2005 to 2015 reports 36-month buy-and-hold abnormal return of −57.33%, with about 10% beating the index; a 2012 to 2025 study reports average returns of 12.33% at six months, 20.29% at one year, 10.03% at two years and 8.72% at three years; a 2023 five-factor study argues long-run underperformance is sample-specific and concentrated in high-volume years (all three as reported by ipomarket.in, secondary).
- **India evidence.** Yes, negative for variant A. Nothing found for variant B.
- **Costs and capacity.** Normal.
- **Failure modes.** No history for indicators; lock-in expiries add supply at 30 and 90 days and at six months; hot-issue cohorts fare worst.
- **Feasibility.** Tradable; variant A is expected to lose relative to the index. Testable from daily prices.
- **Sources.** https://www.ipomarket.in/news/build-long-term-portfolio-only-ipos-2025-26-data-risks ; https://taxguru.in/sebi/sebi-report-54-percent-ipo-shares-sold-week.html

#### S29. Anchor lock-in expiry

- **Rules.** Dates: 30 days and 90 days after the allotment date (allotment is a few days before listing). Since April 2022 half the anchor shares unlock at 30 days and the rest at 90. Overlay version: do not hold a recent IPO from 3 sessions before to 2 sessions after the 30-day unlock. Contrarian version: if the stock closes down 5% or more on the first unlocked session with volume at least 3 times average, buy at that close and hold 5 trading days. Higher risk when the issue was under ₹250 crore or the anchor book was FPI-heavy.
- **Instruments.** Cash equities (new listings are not in F&O, so no short).
- **Holding period.** 1 to 5 days.
- **Reported performance.** SEBI staff study (13 August 2026), 242 mainboard IPOs listed April 2022 to October 2025: aggregate anchor exit only 3.2% just after the 30-day unlock, about 8% by day 60, 17.3% after the 90-day unlock, 34% by day 180 and 51% by day 365 (167 IPOs); issues under ₹250 crore saw 9.1%, 20.3% and 32.4%; mean price impact in the 30-day window ran from about **−0.4% where exits were up to 2.5% of the anchor book to −3.5% where exits exceeded 10%**; the 90-day window was more muted. Single cases: Zomato −8% and SBI Cards −15% on unlock day, Sanathan Textiles −9%, IKS −11.8% (unverified: snippet only).
- **India evidence.** Yes, for the avoid version. The rebound version is untested.
- **Costs and capacity.** Normal.
- **Failure modes.** Exit intensity is known only afterwards; average effect is small because most anchors do not sell at the first unlock.
- **Feasibility.** Overlay yes; contrarian marginal. Testable from daily prices using listing date minus about three days as allotment date.
- **Sources.** https://taxguru.in/sebi/sebi-study-finds-gradual-anchor-investor-exit-mainboard-ipos.html

### F. Other announcements and flows

#### S30. Bonus and stock-split announcements

- **Rules.** Event: board approves a bonus issue or forward split. Buy at the next open, hold 10 trading days (test 1, 10, 30). Variant: buy 5 sessions before the ex-date and sell at the ex-date close. Price above ₹50, turnover above ₹2 crore, maximum 3 positions.
- **Instruments.** Cash equities.
- **Holding period.** 1 to 30 days.
- **Reported performance.** Chakrabarti et al. (IIM Calcutta WPS 798), 23 forward splits 2010 to 2015: abnormal return +1.61% around the announcement day (significant), +1.28% on the split day (not significant at 10%). Other Indian studies report a positive bonus-announcement and ex-bonus effect and conflicting split results (unverified: snippet only).
- **India evidence.** Yes, small samples, effect about 1 to 2% and concentrated on the announcement day itself.
- **Costs and capacity.** Edge is about the size of costs plus the opening gap.
- **Failure modes.** Small and micro caps use bonuses and splits for promotion; announcement-day return is not capturable after the fact.
- **Feasibility.** Marginal.
- **Sources.** https://studentlive.iimcal.ac.in/sites/all/files/pdfs/wps_798.pdf

#### S31. Daily FII/DII flow as a next-day index signal

- **Rules.** After the close, read provisional FII and DII net cash-market figures. Go long Nifty (ETF or futures) for the next session if FII net is positive (variants: FII net above its 20-day mean; FII-to-DII ratio), flat otherwise.
- **Instruments.** Nifty ETF, index futures.
- **Holding period.** 1 day (monthly variant: 1 month).
- **Reported performance.** Groww Digest (March 2026), 4,402 trading days from 12 November 2007: on days FIIs bought the market rose about 56% of the time the same day; **yesterday's FII flow gave about a 50% chance of an up day either way**; the reverse holds better (after an up day FIIs buy next day about 63% of the time); monthly, FII net-buy months ended higher about 70% of the time and net-sell months lower about 72%, which is contemporaneous; DIIs bought on about 80% of FII sell days.
- **India evidence.** Yes, negative for prediction: flows follow prices.
- **Costs and capacity.** Daily switching costs dominate a zero edge.
- **Failure modes.** No lead-lag; provisional data revised.
- **Feasibility.** Tradable, no edge shown.
- **Sources.** https://digest.groww.in/p/what-if-the-story-we-tell-about-fiis

#### S32. Upper-circuit momentum

- **Rules.** Universe: NSE EQ-series stocks with a 5%, 10% or 20% band (from sec_list.csv), excluding the 2% band, BE/T2T series, SME, ASM/GSM lists; price above ₹20; 20-day median turnover above ₹1 crore. Signal: close at the upper band (close ≥ previous close × (1 + band) − one tick) with volume at least 2 times the 20-day average and not already up more than 40% in 10 sessions. Buy at the next open only if the open is below that day's upper band (otherwise the order will not fill). Exit at the first close that is not at the upper band, or on a close below the previous day's low, or after 5 sessions. Position at most 10% of capital and at most 1% of the stock's average daily turnover.
- **Instruments.** Cash equities, small and micro caps.
- **Holding period.** 1 to 5 days.
- **Reported performance.** No study or credible backtest found. Mechanics [opened]: at the upper circuit there are queued buyers and no sellers; a new buyer may not be filled; an intraday short may be impossible to close and goes to auction; the next day's band is drawn from a new reference price.
- **India evidence.** None.
- **Costs and capacity.** Fill uncertainty is the main cost: the trades that would work are the ones that do not fill.
- **Failure modes.** Adverse selection on fills; consecutive lower circuits with no exit; operator-driven stocks; surveillance actions (band cuts, T2T) mid-trade.
- **Feasibility.** Marginal. Approximate backtest possible from daily OHLCV plus band data, but it will overstate results unless unfilled opens are modelled.
- **Sources.** https://onetradejournal.com/glossary/upper-circuit ; https://nsearchives.nseindia.com/content/equities/sec_list.csv

---

## 3. Summary table

| # | Strategy | Evidence | India evidence | Feasible at ₹1.5 lakh | Backtest from daily prices only |
|---|---|---|---|---|---|
| S01 | PEAD on SUE, long-only | strong academic globally | yes (long leg about +0.7% a quarter) | marginal | no (needs results) |
| S02 | EAR drift, with or without SUE | strong academic (US) | no | marginal | no (needs dates) |
| S03 | Price-and-volume shock proxy | practitioner | no | yes | yes |
| S04 | Triple-sorted momentum | some academic | yes (2002 to 2010) | yes | no |
| S05 | Negative surprise exit/short | some academic | yes | overlay yes, short no | no |
| S06 | Hold through results day | negative | yes | yes, but no edge | no |
| S07 | Analyst BUY drift | some academic | yes | marginal | no |
| S08 | Insider and promoter buying | some academic | yes | yes | no |
| S09 | Red-flag exclusion overlay | some academic | yes | yes | no |
| S10 | Follow bulk-deal buyers | negative | yes | yes, but loses | no |
| S11 | Rebound after bulk selling | some academic | yes (about +1% gross) | marginal | no |
| S12 | Block-deal informed buyers | some academic | yes | marginal | no |
| S13 | Index inclusion AD to ED−1 | strong academic globally | mixed | yes | no (needs dates) |
| S14 | Index deletion rebound | some academic | yes | yes | no (needs dates) |
| S15 | Predicted index additions | practitioner | no | marginal | no |
| S16 | F&O inclusion/exclusion | some academic | mixed | marginal | yes (F&O bhavcopy) |
| S17 | Buyback tender, small-shareholder quota | practitioner | yes | yes | no |
| S18 | Buyback announcement drift | some academic | yes | marginal | no |
| S19 | Open-offer tender | some academic, mixed | yes | marginal | no |
| S20 | Delisting | anecdotal | yes | marginal | no |
| S21 | Share-swap merger arbitrage | anecdotal | yes | marginal | no |
| S22 | Demerger announcement drift | some academic | yes | marginal | no |
| S23 | Post-listing spin-off | anecdotal | mixed | marginal | no |
| S24 | Rights-entitlement arbitrage | anecdotal | no | marginal | no |
| S25 | Equity-issuer avoidance | some academic | yes | yes | no |
| S26 | OFS retail discount | practitioner | indirect | marginal | no |
| S27 | IPO application with filter | some academic (regulator data) | yes | yes | no |
| S28 | Post-listing IPO buying | negative | yes | yes, but loses | yes |
| S29 | Anchor lock-in expiry | some academic (regulator data) | yes | yes as overlay | yes (approximate) |
| S30 | Bonus/split announcement | some academic | yes | marginal | no |
| S31 | FII/DII flow signal | negative | yes | yes, no edge | no |
| S32 | Upper-circuit momentum | anecdotal | no | marginal | yes (approximate) |

---

## Negative or cautionary evidence

1. **Indian post-earnings drift lives on the short side.** In the largest Indian sample opened (18,269 announcements, 2008 to 2014) the top earnings-surprise quartile beat the Nifty by 0.7% over the following quarter while the bottom quartile lost 6.6%. A long-only retail account captures almost none of the 7.3% spread, and a later study (2014 to 2018, 100 NSE firms) finds no exploitable drift at all.
2. **Results day itself is a losing hold on average**: mean 3-day market-adjusted return −0.5%, median −0.7%, in the same sample.
3. **Bulk-deal buying is followed by reversal**: after the +3.5 to +4.2% deal-day move, abnormal returns are negative on each of days +2 to +7. The disclosed information is stale by the time it is public; the paper frames the profit as front-running by people who knew beforehand.
4. **Insider purchases do not pay at one month** (−0.20% market-adjusted); the insider signal is long-horizon and mostly about sales.
5. **Index inclusion is a fading and crowded effect**: US S&P 500 addition returns fell from 7.4% in the 1990s to under 1% in the 2010s; Indian studies find no announcement-day effect, a 1.5% effective-day effect that reverses within nine days, and reversal of inclusion gains within 60 days; over the last five years Nifty 50 deletions did better than additions over the following 6 and 12 months.
6. **Buyback tender arbitrage decays as it becomes popular**: acceptance fell from near 100% (2016) to about two-thirds (2017) to about a quarter (2022 to 2023). Tax treatment has changed three times in three years; between October 2024 and March 2026 it made the trade uneconomic.
7. **Open offers rarely deliver the full stake and leave leftover shares**; of 133 offers after 2013 only a handful were fully subscribed, and professional arbitrageurs hedge with futures that a small account cannot use.
8. **Grey-market premium is not a forecast**: late-2025 listings repeatedly diverged from GMP in both directions.
9. **IPO listing gains have collapsed and do not persist**: median listing gain 3.8% in 2025 against 15.2% in 2024; 59% of 2025 IPOs were below their listing price by year-end; one 2005 to 2015 sample shows −57% three-year abnormal return.
10. **Equity issuers underperform**: QIP buyers lost money on average over 3 and 6 months in every year from 2010 to 2016; rights/FPO issuers lagged matched firms by 17% over five years.
11. **Rating downgrades are priced before the announcement**; upgrades have no significant effect.
12. **FII flows do not predict the next day**: about 50/50 over 4,402 days. Flows react to prices.
13. **Demerger, split and bonus announcement effects are 1 to 3%** and concentrated on the announcement day or the next open, the same size as costs plus the entry gap for this account.
14. **Upper-circuit and F&O-inclusion trades have no supporting evidence of persistence**, and circuit-locked stocks have a fill problem that makes naive backtests optimistic.
15. **Publication and crowding**: most of these effects are well known to Indian brokers, who publish candidate lists (index changes, buyback calculators, IPO subscription trackers) in real time. Treat every pre-2020 result as an upper bound.
16. **Cost drag at this size**: about 0.46% a round trip on a ₹30,000 position before slippage, plus 20% short-term tax, removes roughly the first 1.5% of any gross event edge.

## Open questions

1. **Tax on tendered shares under the 2026 law**: is a buyback or open-offer tender through the exchange window an STT-paid transfer taxed at the 20% short-term rate, or at slab rate? This changes the after-tax return of S17 and S19 materially for a higher-bracket investor.
2. **Automation path**: does SmartAPI expose buyback tender, OFS bid, rights application or IPO application calls, or are these app-only? If app-only, S17, S24, S26 and S27 are alert-driven, not automated.
3. **Realised small-shareholder acceptance ratios for every tender buyback since 2016** (and especially the first buybacks after 1 April 2026, including Infosys 2025's final ratio). A table of premium, entitlement, final acceptance and 30-day post-closure return is the missing dataset for S17; it has to be built from letters of offer and post-offer public announcements.
4. **Point-in-time results data**: announcement timestamps (before, during or after market hours), consolidated versus standalone EPS, and restatements. Without these, S01, S02, S05 and S06 backtests will have look-ahead bias.
5. **Has Indian PEAD survived after 2018** in the long leg, in mid caps, net of costs? No study after the 2014 to 2018 sample was opened.
6. **Passive assets tracking Nifty 50, Nifty Next 50 and MSCI India in 2026** relative to free float, and whether the announcement-to-effective run-up for Indian additions is still positive in 2022 to 2026 (no measured study found; only broker flow estimates).
7. **Not researched because the search budget ran out**: dividend announcement and ex-dividend effects; "superstar investor" shareholding disclosures; quarterly changes in mutual-fund and FPI holdings; ASM/GSM surveillance-list entry and exit; pre-IPO shareholder (six-month) lock-in expiry; SME IPO rules and listing behaviour; preferential allotments and warrants to promoters; Budget, RBI-policy and election-day event trades (likely covered by the calendar researcher); results-day option strategies (covered by the options researchers).
8. **Block-deal framework and price-band rules in force in 2026** (minimum block size, permitted price range, dynamic bands for F&O stocks) were not re-verified.
9. **Delisting outcomes**: a hand-built list of announced delistings since 2015 with floor price, discovered price, success or failure, and price path would be needed before S20 can be judged.
10. **Short leg access**: whether single-stock futures lot sizes in late 2026 leave any room for one hedged position in a ₹1.5 lakh account (affects S05, S19, S21). My working assumption is no.
