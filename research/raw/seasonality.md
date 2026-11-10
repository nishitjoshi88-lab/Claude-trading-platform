# Calendar and seasonal effects: research findings

Researcher area: calendar and seasonal effects (turn-of-month, day-of-week, month-of-year, pre-holiday, expiry week and expiry day, Budget day, Muhurat trading, election cycles, monsoon, Sell-in-May, quarter-end window dressing, RBI policy and FOMC days, overnight versus intraday returns, first-trading-day SIP flows).

Written 2026-11-10 for a ₹1,50,000 Angel One (SmartAPI) account with profits reinvested.

## How to read this file

- Every number is tagged by how it was obtained. Unmarked numbers come from a page or PDF that was opened and read with `fetch_text.py`. "(unverified: snippet only)" means the number was seen only in a search-result summary and the page could not be opened (HTTP 403/404/409, paywall, SSL error or JavaScript-rendered values). "(my arithmetic)" means a figure computed here from numbers in an opened source. "(estimate)" means an assumption with no source.
- Search limitation: the shared web-search budget for this run ran out after about 30 searches. Everything after that was done by opening URLs already found. Topics that therefore stayed thin are listed under "Open questions".
- Twenty-seven strategies are described. Parameter variants are folded into one strategy with a range.

## Facts that apply to every strategy (checked against 2025-2026 sources)

### Contract calendar and lot sizes

| Fact | Value | Effective | Source |
|---|---|---|---|
| Nifty weekly expiry day | Tuesday (was Thursday) | Contracts expiring on or after 1 Sep 2025; first Tuesday weekly was 2 Sep 2025 | NSE circular NSE/FAOP/68747 dated 25 Jun 2025 |
| Nifty, Bank Nifty, FinNifty, Midcap Select, Next 50 and all stock monthly expiry | Last Tuesday of the month (was last Thursday) | Same circular; annexure shows stock and FinNifty monthlies and the realigned Nifty quarterly on 30 Sep 2025, and the first newly generated Nifty Tuesday monthly on 28 Oct 2025 | NSE circular NSE/FAOP/68747 |
| Weekly index options | One benchmark per exchange: Nifty 50 on NSE, Sensex on BSE (Thursday). Bank Nifty, FinNifty, Midcap Select have monthly contracts only | 20 Nov 2024 (SEBI circular of Oct 2024) | PhonePe Invest explainer dated 30 Jun 2026 |
| Holiday rule | If expiry day is a trading holiday, expiry moves to the previous trading day | Current | PhonePe Invest explainer |
| Nifty lot size | 65 (was 75) | Weekly expiry 6 Jan 2026 and monthly expiry 27 Jan 2026 onward | Angel One news, 28 Nov 2025 |
| Bank Nifty lot size | 30 (was 35); FinNifty 60 (was 65); Midcap Select 120 (was 140) | Same | Angel One news, 28 Nov 2025 |
| Nifty spot level used for sizing | About 25,000 (24,986 on a 2026 broker page snapshot, date not shown; India VIX 18.4 on the same snapshot) | 2026 | nubra.io expiry guide |

Consequence for every "expiry" study below: almost all Indian expiry-day and expiry-week evidence was measured when expiry was the last Thursday (and Thursday weeklies from 2019). Since September 2025 the anchor day is Tuesday. Any backtest must take the actual expiry date from the contract file, not assume a weekday.

One Nifty futures lot is about 65 x 25,000 = ₹16.25 lakh notional (my arithmetic). The margin for that is larger than the whole account (typical SPAN plus exposure is above 10% of notional; exact figure not verified). So index futures are not usable at ₹1.5 lakh; the long-only instrument is an index ETF (NIFTYBEES and similar).

### Charges (Angel One official pricing page, opened 2026-11-10)

| Item | Equity delivery | Equity intraday | Futures | Options |
|---|---|---|---|---|
| Brokerage | Lower of ₹20 or 0.1% per executed order, minimum ₹5 | Lower of ₹20 or 0.1%, minimum ₹5 | ₹20 per executed order | ₹20 per executed order |
| NSE transaction charge | 0.0030699% | 0.0030699% | 0.0018299% | 0.0355299% of premium |
| STT | 0.1% buy and sell | 0.025% sell | 0.05% sell | 0.15% of premium on sell |
| Stamp duty (buy side) | 0.015% | 0.003% | 0.002% | 0.003% |
| SEBI fee | ₹10 per crore | ₹10 per crore | ₹10 per crore | ₹10 per crore |
| GST | 18% on brokerage and transaction charges | same | same | same |

- The futures STT of 0.05% and options STT of 0.15% are the Budget 2026 rates, effective 1 April 2026 (ClearTax STT page; the Angel One page shows the same rates). Before that, futures were 0.02% and options 0.10% (unverified: snippet only). Any backtest that spans April 2026 needs a cost break.
- ETF units: STT on a delivery sale of equity-oriented fund units is 0.001% (ClearTax STT table), not 0.1%. This is what makes index ETFs the cheap vehicle for calendar trades.
- Demat debit (DP) charge on each delivery sell: ₹20 per ISIN per day plus GST (Chittorgarh broker page; not shown on the Angel One page that was opened, so treat as approximately right).
- Short-term capital gains on STT-paid equity and equity ETF units are taxed at 20%; long-term at 12.5% (ClearTax). Seasonal in-and-out trading converts what would be long-term gains for a buy-and-hold investor into short-term gains.

Worked round-trip costs (my arithmetic from the rates above):

| Trade | Size | Round-trip cost | As % of trade |
|---|---|---|---|
| NIFTYBEES delivery (overnight or longer) | ₹1,50,000 | about ₹106 (brokerage 40, txn 9.2, GST 8.9, stamp 22.5, STT 1.5, DP 23.6) | 0.07%, plus spread (estimate 0.02 to 0.05%) |
| NIFTYBEES intraday | ₹1,50,000 | about ₹100 (STT 37.5 replaces DP and delivery stamp) | 0.07% |
| Single stock delivery | ₹1,50,000 | about ₹405 (adds STT 0.1% each side) | 0.27% |
| Single stock delivery, small ticket | ₹15,000 | about ₹92 (brokerage 15 x 2, STT 30, DP 23.6, rest small) | 0.61% |
| Nifty futures, 1 lot | ₹16.25 lakh notional | about ₹966, of which STT ₹812 | 0.06% of notional, 0.64% of a ₹1.5 lakh account |

Two conclusions follow before any strategy is looked at:
1. A calendar edge traded through an index ETF needs to be well above 0.10% per round trip to matter. Daily-frequency effects (overnight, day-of-week) do not clear this bar; monthly-frequency effects (turn-of-month at 0.5 to 0.8% per trade) do.
2. Multi-stock monthly rotation with ₹15,000 tickets costs about 0.6% per position per month, about 7% a year (my arithmetic). Cross-sectional seasonal strategies are therefore not viable at this capital even where the academic evidence is strong.

---

## A. Within-month effects

### 1. Turn-of-month long, index (TOM)

- Family: monthly cycle.
- Rules. Universe: one broad index ETF (NIFTYBEES; alternatives JUNIORBEES, a Nifty 500 ETF). Signal: calendar only. Let L(k) be the k-th last trading day of month m and F(j) the j-th trading day of month m+1. Enter long with all capital at the close of L(n_in). Exit at the close of F(n_out). No stop in any source. One position, one round trip a month. In cash (liquid ETF) otherwise.
- Parameter values used by sources:
  - Classic "tight" window: return days -1 to +3, that is buy at the close of L(2), sell at close of F(3) (Lakonishok and Smidt 1988; McConnell and Xu 2008 via Quantpedia).
  - Quantpedia simplification: buy at close of last trading day L(1), sell at close of F(1) (Quantpedia composite case study) or F(3) (Quantpedia strategy page).
  - "Extended" window: buy at close of L(5), sell at close of F(3) (QuantifiedStrategies general rule; Zerodha "Extended TOTM").
  - Nifty-optimised: buy at close of L(5) or L(6), sell at close of F(2) (QuantifiedStrategies Nifty article).
  - Recommended test grid: n_in in {1,...,7}, n_out in {1,2,3,4}; anchor in {calendar month end, monthly F&O expiry date}.
- Instruments: index ETF, delivery. Holding period: 2 to 8 trading days.
- Reported performance:
  - US, CRSP 1926-2005 (McConnell and Xu via Quantpedia): large caps earned 0.15% a day on days -1 to +3 against 0.01% on other days (t = 7.81); Quantpedia's indicative figures are 7.2% a year, volatility 6.9%, Sharpe 1.04, before costs and before interest on idle cash. The effect persisted in the 1987-2005 hold-out after Lakonishok and Smidt's 1897-1986 sample, and appeared in 30 markets.
  - US, SPY 1993-2019 (Quantpedia case study, buy last-day close, sell first-day close): 3.01% a year, maximum drawdown 11.97%.
  - US, S&P 500 1960 to about 2021 (QuantifiedStrategies, L(5) to F(3)): 7.11% a year against 6.95% buy-and-hold price index, maximum drawdown 27% against 56%.
  - The paper Quantpedia lists as Carchano and Tornero, "Calendar Anomalies in Stock Index Futures" (S&P 500, DAX, Nikkei futures 1991-2008, 188 calendar effects, bootstrap tests): TOM in S&P 500 futures was the only effect that stayed statistically and economically significant (abstract via Quantpedia).
- India-specific evidence:
  - Mangala and Sharma (2007), S&P CNX Nifty, Jan 1994 to Apr 2005: significantly high mean daily returns just before and in the first few trading days of the month; second half indistinguishable from zero or negative (abstract).
  - Satish and Bheemanagouda (2023), Nifty 50, Sensex, Nifty Smallcap 50, BSE SmallCap, Apr 2007 to Feb 2023: TOM significant by t-test and Mann-Whitney; stronger in small-cap indices; domestic institutions trade significantly more at month end, individuals do not (abstract).
  - QuantifiedStrategies, Nifty 50 from Yahoo data 2007/08 to about 2021: L(5) to F(2), CAGR 10.5%, maximum drawdown 26%, invested about 30% of the time; a second article with L(5) to F(3) reports CAGR 10.4% against 9.5% buy-and-hold and drawdown 34% against 59%. Price index, no costs, parameters optimised in sample (the authors say so).
  - Zerodha "In The Money" (2 Jan 2026), ten years of closes to 2025, pre-cost, no leverage: Nifty Extended (L(5) to F(3)) beat Tight (L(1) to F(3)) on win rate, median, drawdown; expectancy about 0.82% per trade; return-to-max-drawdown 15.1 (Bank Nifty 10.28, Reliance 9.98, HDFC Bank 12.10, SPY 7.40). Exposure about 96 of 250 days. Year by year: 2015-2019 only 2017 was good, 2020-2023 strong, 2024-2025 flat. The author concludes the late-month days carry the effect in India rather than the first days of the new month.
  - Gavhale (2025, arXiv, Nifty 2003-2024): investing on the monthly expiry day instead of the first trading day of the next month gave higher SIP returns at 1 to 5 year horizons. That is the same fact seen another way: the index is on average lower on the last Thursday than on the first trading day.
- Costs and capacity: about 0.10% per round trip in NIFTYBEES at ₹1.5 lakh against a gross edge of roughly 0.5 to 0.8% per trade. Twelve trades a year cost about 1.2% a year. Capacity is not a constraint.
- Failure modes: multi-year flat patches (2018-2019, 2024-2025 in the Zerodha test); full equity beta inside the window, so a crash that lands in the window is taken in full (QuantifiedStrategies drawdown 26 to 34%); window choice is fitted on about 15 years of data; Quantpedia warns calendar effects "tend to vanish or rotate to different days"; the last trading day itself is the weakest of the last seven in the US since about 1990 (QuantifiedStrategies); the monthly expiry moved from last Thursday to last Tuesday in September 2025, which may move the Indian late-month window.
- Feasibility at ₹1.5 lakh: yes. One ETF order each way, twelve times a year, no margin, no shorting.
- Sources: https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes ; https://quantpedia.com/quantpedias-composite-seasonalcalendar-strategy-case-study/ ; https://www.quantifiedstrategies.com/turn-of-the-month-trading-strategy/ ; https://www.quantifiedstrategies.com/end-of-month-effect-in-nifty-50-does-it-exist-turn-of-the-month/ ; https://inthemoneybyzerodha.substack.com/p/turn-of-the-month-tomtotm-strategy ; https://ideas.repec.org/a/sae/padigm/v11y2007i2p9-15.html ; https://rfb.ase.ro/Vol15-2023/dec2a.asp ; https://quantpedia.com/a-turn-of-the-month-strategy-in-asset-allocation/

### 2. Turn-of-month long, small and mid caps

- Family: monthly cycle.
- Rules: same as strategy 1 with the universe changed to a small-cap or mid-cap index ETF (Nifty Smallcap 250, Nifty Midcap 150 trackers) or, for testing, the index itself. Default window L(5) to F(3). Stop: none in sources.
- Reported performance: Satish and Bheemanagouda (2023) report the TOM effect "more pronounced in smaller indices compared to larger ones" for Apr 2007 to Feb 2023 (abstract only; magnitudes not seen). McConnell and Xu found the US effect in small and large caps alike. Dzhabarov and Ziemba (futures 1993-2009) found seasonal effects stronger in small caps (abstract via Quantpedia).
- Costs and capacity: small-cap ETFs trade with wider spreads than NIFTYBEES (estimate; not measured here), which can take a meaningful share of a 0.5 to 1% edge. Index-level backtests overstate what an ETF buyer gets because the ETF price can deviate from NAV at the close.
- Failure modes: small-cap drawdowns are deeper; liquidity at the close; the SEBI and AMFI "froth" interventions of 2024 show flows into this segment can be regulated abruptly (Trendlyne).
- Feasibility: marginal. Tradable in size, but the spread and tracking gap are unknown until measured on real quotes.
- Sources: https://rfb.ase.ro/Vol15-2023/dec2a.asp ; https://ideas.repec.org/a/rfb/journl/v15y2023i2p101-118.html ; https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes ; https://trendlyne.com/posts/4478718/which-are-the-best-and-worst-months-for-indian-stocks-screener-stocks-outperforming-their-sectors

### 3. Mid-month payday effect

- Family: monthly cycle.
- Rules: buy the index ETF at the close of the 15th calendar day (or the last trading day before the 16th) and sell at the close of the 16th (next trading day if the 16th is a holiday). One position. No stop. Parameter: day in {15, 16}; hold 1 day.
- Reported performance: US S&P 500 1980-2010 (Ma and Pratt via Quantpedia): the 16th outperformed every calendar day except the 1st and 2nd; annualised contribution 2.57%, volatility 4.31%, Sharpe 0.6. SPY 1993-2019 (Quantpedia case study): 2.08% a year, drawdown 8.62%. The source paper says the effect weakens as US employers move to bi-weekly pay.
- India-specific evidence: none found. Indian salaries are paid monthly, mostly at month end or in the first week, so the US mechanism (semi-monthly payroll into retirement accounts) does not transfer. Zerodha's segment test found the mid-month segment (10th trading day to 6th-last) had a lower median than the turn-of-month segment.
- Costs: a one-day hold must clear about 0.10% round trip; the US edge was about 0.2% a day.
- Feasibility: yes mechanically; low prior for India.
- Sources: https://quantpedia.com/strategies/payday-anomaly ; https://quantpedia.com/quantpedias-composite-seasonalcalendar-strategy-case-study/ ; https://inthemoneybyzerodha.substack.com/p/turn-of-the-month-tomtotm-strategy

### 4. Expiry-day accumulation instead of first-trading-day buying (SIP-flow timing)

- Family: monthly cycle, flow timing. This is a rule for when to deploy fresh or reinvested capital, not a round-trip trade.
- Rules: whenever capital is to be added to a long-term index holding, buy at the close of the monthly F&O expiry day (last Tuesday since September 2025; last Thursday before) instead of the first trading day of the following month. Parameter: buy day in {monthly expiry, 25th, L(5)}.
- Reported performance: Gavhale (2025), Nifty 50 closes 2003-2024, equal monthly instalments. Expiry-day SIP minus first-trading-day SIP: mean +0.77 percentage points a year over 1-year windows (22 windows, bootstrap 95% interval 0.30 to 1.20), +0.27 over 3-year windows, +0.125 over 5-year windows, and only 3 to 7 basis points over 10 and 20 years (6.83 against 6.76, 7.04 against 6.99, 6.68 against 6.65).
- Caveats on that paper: it is a preprint, not peer reviewed. Its "CAGR" divides final value by total invested and annualises over the full period, which is not an IRR and understates SIP returns; its headline that Nifty SIPs earned 6.7% is an artefact of that formula. The expiry-day instalment is also simply made several days earlier each month, so part of the gain is ordinary drift.
- Contrary practitioner evidence: PrimeInvestor (Nifty 100 and Nifty 500, 2008-2022, SIP on 5th, 15th, 25th) found the 25th slightly ahead in every window but by a negligible amount (₹22,08,778 against ₹22,05,085 on ₹12 lakh invested over 2011-2020). WhiteOak Capital (index data Aug 1996 to Aug 2025, reported by Business Today) found no meaningful difference by SIP date.
- Mechanism claimed: SIP inflows (₹28,265 crore a month in Aug 2025, AMFI figure in Business Today) cluster in the first days of the month.
- Feasibility: yes; costless to adopt. Expected gain is a few basis points a year at long horizons.
- Sources: https://arxiv.org/html/2507.04859v2 ; https://primeinvestor.in/which-date-is-the-best-for-sips/ ; https://www.businesstoday.in/mutual-funds/story/mid-cap-sip-returns-lead-best-sip-date-salary-day-494443-2025-09-17

---

## B. Within-week effects

### 5. Day-of-week long in the index

- Family: weekly cycle.
- Rules: hold the index ETF only from the close of the trading day before weekday W to the close of weekday W. Parameter W in {Mon, Tue, Wed, Thu, Fri}; a weekend variant holds Friday close to Monday close. No stop.
- Reported performance (India):
  - Kumar and Jawa (SRCC Business Analyst), Nifty 50 daily, Jan 1995 to Dec 2015, 5,222 observations: Wednesday coefficient +0.31% a day over the Monday base in OLS (t = 4.6); Wednesday mean +0.16% a day in the EGARCH model (z = 4.7); Monday about -0.06% in OLS (not significant); other days not significant.
  - Siddiqui and Narula (2013), Nifty 2000-2011, GARCH: negative mean Tuesday return; no positive-Friday, negative-Monday pattern; "on dividing the entire period into three-year lags, anomalies instantaneously disappear".
  - Saxena, Purohit and Malhotra (2021, "Diminishing calendar anomalies"), Jan 2011 to Jan 2018: no day-of-week effect in Nifty 50, Nifty Bank, Nifty Auto or Nifty Financial Services.
  - Yadav and Kadian, 11 Mar 2020 to 30 Sep 2021: Monday negative (significant only for Sensex); Tuesday and Friday significantly positive, Tuesday highest. An 18-month sample inside one bull run.
  - Older literature summarised in search results: the Wednesday effect belonged to the pre-2002 weekly account-period settlement and faded after rolling settlement; later studies disagree on which day, if any, is special (unverified: snippet only).
- Interpretation: the significant day changes with every sample (Wednesday, then none, then Tuesday and Friday). That is what noise looks like. The 1995-2015 Wednesday result is driven by the weekly-settlement era.
- Costs: about 50 round trips a year at 0.10% each is 5% a year of drag, larger than any surviving effect.
- Feasibility: yes mechanically; not worth trading. Keep as a control test.
- Sources: https://www.srcc.edu/system/files/Article-No8-Efficient-Market-Hypothesis-and-Calendar-Effects-Updates.pdf ; https://ideas.repec.org/a/sae/vision/v17y2013i3p233-245.html ; https://ideas.repec.org/a/ids/gbusec/v24y2021i1p43-58.html ; https://publishingindia.com/storage/PDFBrochures/8019.pdf

### 6. Weekday pattern in implied volatility: sell premium early in the week

- Family: weekly cycle, volatility.
- Rules (hypothesis built from the cited pattern; no source publishes these exact rules): at Monday's close sell one lot of an at-the-money Nifty iron butterfly (short ATM call and put, long wings at about 2% out) in the nearest weekly expiry that has at least 5 trading days left; close at Wednesday's close or at a loss equal to the credit received, whichever comes first. One position a week. Parameters: entry day Mon, exit day Wed to Fri, wing width 1.5 to 3%, stop 1x credit.
- Evidence: Shaikh and Padhi (2015), India VIX, ARCH/GARCH: significant positive Monday effect (VIX rises at the start of the week), significant negative Wednesday effect (expected volatility falls Wednesday to Friday), a significant fall on option expiry day, and negative March and December effects (abstract; sample period not shown). Agarwalla and Pandey (IIMA, high-frequency data) find higher volatility in the first hour after weekends and the last hour before weekends.
- Caveats: the VIX pattern was measured when expiry was Thursday; the mid-week fall may have been an expiry effect, and expiry is now Tuesday. A fall in VIX is not the same as a profit on a short option position after costs. No Indian backtest of this trade was found.
- Costs: four option legs each way, about ₹160 in charges plus slippage of roughly ₹400 for one lot (estimate), against a credit of the order of ₹15,000 to ₹25,000.
- Feasibility: marginal. A hedged iron butterfly fits the account in margin terms (exact margin not verified), but one lot is the only possible size, so there is no way to scale risk down.
- Sources: https://ceeol.com/search/article-detail?id=285053 ; https://iima.ac.in/sites/default/files/rnpfiles/19191060542012-11-03.pdf

---

## C. Overnight versus intraday

### 7. Overnight long in the index (buy the close, sell the open)

- Family: overnight versus intraday.
- Rules: each day buy the index instrument at or just before the close (ETF 15:25 to 15:29; Marketcalls used Nifty futures at 15:15) and sell at or just after the next open (09:15 to 09:30). No stop. Parameters: entry time 15:15 to 15:29, exit time 09:15 to 09:30, optional filter "only when close is above the 200-day average".
- Reported performance (India):
  - Capitalmind (Oct 2019): of the Nifty's roughly 11,200 points since 1995, "more than 10,900 were lost in intraday movements"; all the gain came close-to-open. They warn the Nifty "open" before the pre-open auction started in 2010 is unreliable (it was often set near the prior close), so only post-2010 index data is meaningful.
  - Capitalmind (Aug 2020): over about 3,000 trading days (12 years), 46% of days closed above the open and 64% of days opened above the prior close.
  - Marketcalls (Sep 2018), Nifty futures, 1-minute data Jan 2011 to Jun 2018, buy 15:15, sell 09:30, one lot of 75: with zero costs +595% on ₹1 lakh; with 0.02% cost per trade the account lost 67% within 185 trades on ₹1 lakh starting capital, and on ₹2 lakh starting capital made +94.65% in total, 9.3% a year.
  - Viral figures such as "overnight-only about 20% a year, intraday-only about -7.6% a year" (unverified: snippet only).
- Global evidence: Knuteson (arXiv 2010.01727) documents strongly positive overnight and negative intraday returns across major world indices. Lou, Polk and Skouras show the split differs by strategy type in US stocks.
- Costs: this is the decisive item. ETF route: about 0.10% per round trip, about 245 trips a year, about 25% a year of drag (my arithmetic), more than the gross edge. Futures route: after April 2026 the 0.05% sell-side STT alone is 2.5 times the 0.02% cost figure Marketcalls used; all-in about 0.06% of notional per round trip, about 15% of notional a year (my arithmetic), and one lot cannot be margined on ₹1.5 lakh anyway.
- Failure modes: gap-down nights carry the whole tail risk (overnight is when global shocks land); the edge is in the opening auction print, which a market order after 09:15 does not get; index "open" values overstate what was tradable.
- Feasibility: no as a daily strategy. The useful residue is a design rule for other strategies: hold index longs overnight and avoid intraday-only long exposure.
- Sources: https://premium.capitalmind.in/2019/10/while-you-were-sleeping-what-stocks-do-overnight-versus-in-trading-hours/ ; https://premium.capitalmind.in/2020/08/capitalmind-chase-roaring-day-and-night/ ; https://www.marketcalls.in/amibroker/buy-at-todays-close-and-sell-at-next-day-open-do-simple-trading-strategies-really-work-part2.html ; https://arxiv.org/abs/2010.01727 ; https://conference.nber.org/conf_papers/f78239/f78239.pdf

### 8. Intraday short in the index (sell the open, cover the close)

- Family: overnight versus intraday.
- Rules: each day short the index at the open (Nifty futures, or an intraday short in the ETF) and cover at the close. Parameter: skip days when the opening gap exceeds x%.
- Evidence: the mirror image of strategy 7. Only 46% of days close above the open (Capitalmind 2020), but the mean intraday loss per day is small. Asked for this test, the Marketcalls author replied "results are not worth playing". Capitalmind's own trend system found that in up-trends long trades gained both intraday and overnight, so the intraday drift is not reliably negative.
- Costs: about 0.07% per round trip intraday in the ETF, 245 trips a year, about 17% a year of drag (my arithmetic).
- Feasibility: no. Listed so it is tested once and closed.
- Sources: https://premium.capitalmind.in/2020/08/capitalmind-chase-roaring-day-and-night/ ; https://www.marketcalls.in/amibroker/buy-at-todays-close-and-sell-at-next-day-open-do-simple-trading-strategies-really-work-part2.html

### 9. Overnight short options (sell at the close, buy back at the open)

- Family: overnight versus intraday, volatility premium.
- Rules as studied: sell Nifty options at the market close and cover at the next day's open, delta-hedged with the future. Practical defined-risk version for a small account: at about 15:25 sell an ATM straddle in the nearest weekly expiry and buy wings 1.5 to 2% away (iron butterfly); buy the whole structure back at 09:20 to 09:30 next day. Skip the night before scheduled events (Budget, RBI, FOMC, election results). Parameters: wing width, moneyness, days to expiry at least 2, whether to hold over weekends.
- Reported performance: Bhat, Pandey and Rao (Journal of Futures Markets 44(8), 2024), Nifty options on NSE, 2017-2020: for short option strategies the daily (open-to-open) and intraday (open-to-close) mean returns are "largely negative and insignificant" while overnight (close-to-open) mean returns are "positive, and highly significant"; robust across calls and puts, moneyness, maturity, sub-samples, after accounting for weekend returns and with alternative prices and trade times; weaker on days with large index jumps. They conclude the variance risk premium "is mainly a reward for overnight risk". Magnitudes were behind the paywall and were not seen. This replicates Muravyev and Ni (2020) for S&P 500 options.
- Costs and capacity: four legs in and four legs out every night. Charges about ₹160 to ₹250 plus slippage of the order of ₹400 to ₹800 per lot per night (estimate). The paper's returns are delta-hedged, pre-margin, and not net of retail slippage. Since April 2026 option STT is 0.15% of sell premium.
- Failure modes: an overnight gap is exactly the risk being sold; wings cap the loss but a capped loss can equal many nights of gains; SEBI removed the calendar-spread margin benefit on expiry day and added extra margin on short options on expiry day in the 2024 measures (unverified: not opened in this session); a 2017-2020 sample has not been confirmed for 2021-2026, a period in which the weekly-option structure changed twice.
- Feasibility: marginal. One hedged lot fits; there is no room to size smaller, and the nightly execution cost is large relative to the expected premium.
- Sources: https://law-journals-books.vlex.com/vid/the-asymmetry-in-day-1115554990

### 10. Momentum held only overnight (stocks)

- Family: overnight versus intraday, cross-sectional.
- Rules: each month rank a liquid universe (Nifty 100) on 12-month return skipping the last month; each day buy the top decile at the close and sell at the next open (the published strategy is long winners and short losers overnight).
- Reported performance: Lou, Polk and Skouras ("A Tug of War", later Journal of Financial Economics 2019), US stocks: essentially all momentum profits accrue overnight; most other anomalies earn their premia intraday; the overnight-intraday spread varies by about 2% a month with institutional activity.
- India-specific evidence: none found.
- Costs: daily delivery round trips in stocks cost 0.27% at ₹1.5 lakh and 0.6% at ₹15,000 tickets; no overnight shorting of stocks. Not implementable.
- Feasibility: no. Recorded for completeness and as a reason to prefer holding momentum positions rather than day-trading them.
- Sources: https://conference.nber.org/conf_papers/f78239/f78239.pdf

---

## D. Month-of-year and annual cycles

### 11. Halloween, "Sell in May"

- Family: annual cycle.
- Rules: hold the index ETF from the close of the last trading day of October to the close of the last trading day of April; hold a liquid or short-duration debt fund for the other six months. Two round trips a year.
- Reported performance (global): Doeswijk via Quantpedia, global equities 1970-2003: 8.8% in the November to April half, close to zero in the other half. Bouman and Jacobsen (2002): higher November to April returns in 36 of 37 countries, 1970-1998 (as summarised by Stable Investor). A 1963-2008 study of five calendar effects jointly (listed by Quantpedia under Grimbracher, Swinkles, Vliet; abstract only): Halloween and turn-of-month are the two that survive; the equity premium was 7.2% in Halloween or turn-of-month periods and -2.8% otherwise.
- India-specific evidence, all against:
  - Stable Investor (2015): Sensex since 2000 averaged 9.35% in May to October against 6.92% in November to April. ₹10,000 from 1 Nov 1995 to Sep 2015 became ₹74,975 with buy-and-hold and ₹40,000 with the Halloween rule, before costs, tax and lost dividends.
  - Samco monthly averages for Nifty 2001-2025 reported by DSIJ: Jan -0.47%, Feb -0.74%, Mar a marginal decline, Apr +1.94%, May +1.04%, Jun +1.25%, Jul +2.19%, Aug +1.12%, Sep +1.60%, Oct +1.10%, Nov +2.50%, Dec +2.61%. Summed, May to October is about +8.3% and November to April about +5.8% before the small March decline (my arithmetic). The Indian pattern is the reverse of the Halloween pattern because January to March is the weak stretch.
  - A study of 11 NSE indices over 1994-2014 found the Halloween effect not significant (unverified: snippet only).
- Feasibility: yes mechanically; evidence says do not trade it in India.
- Sources: https://quantpedia.com/strategies/market-seasonality-effect-in-world-equity-indexes ; https://stableinvestor.com/2015/10/october-effect-stock-markets-financial-nonsense.html ; https://insights.dsij.in/appmindshare/nifty-50-posted-gains-in-18-of-the-last-25-julys-will-the-bull-run-continue-58147 ; https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes

### 12. Month-of-year tilt for India (out in January to March, in from April to December)

- Family: annual cycle.
- Rules: hold the index ETF from the close of the last trading day of March to the close of the last trading day of December; hold a liquid fund in January, February and March. One round trip a year. Parameter: months out, default {1, 2, 3}; alternative "hold only {4, 7, 11, 12}".
- Reported performance:
  - Samco via DSIJ, Nifty 2001-2025: averages as listed under strategy 11; July positive in 18 of 25 years; December strongest (+2.61%), November second (+2.50%); January and February negative on average.
  - Upstox, Nifty December returns over 26 years to 2023: mean 3.19%, median 2.58%, positive 73% of years, best +16.38% (2003), worst -4.30% (2011).
  - Kumar and Jawa, Nifty monthly Jan 1995 to Dec 2015: December is the only month with a significant coefficient (+3.8% a month over the January base, t = 2.45); the regression as a whole is not significant (F-test p = 0.96).
  - Trendlyne, Nifty and sector indices 2006 to Feb 2024: April best for most indices (most indices up in 13 of 18 Aprils, Nifty Auto in 16 of 18); January and February worst; the January to March quarter usually negative.
  - Patel (2008), NSE 500 and BSE 500, 1999-2007, as reported by Wright Research: November +8.55% and December +6.40% average monthly returns; March among the worst.
  - Wright Research: 56% of Marches negative over 23 years; March the lowest-mean and highest-volatility month for BSE 500 and Nifty 500 in 2011-2021.
  - Against: Saxena et al. (2011-2018) found no month-of-year effect in Nifty 50 (sector indices showed scattered effects: April in Auto, February and August in Bank). Siddiqui and Narula (2000-2011) found a November effect, not a March effect, and saw anomalies vanish in three-year sub-periods. A 1994-2014 multi-index study reported April, December and September effects (unverified: snippet only).
- Interpretation: the weak fourth fiscal quarter and strong November to December recur across overlapping samples, but with 25 observations per month and monthly volatility near 6% none of this is statistically firm. The cost of being wrong is missing a strong January to March (which happens).
- Costs: one round trip a year, about 0.1%, plus the tax cost of realising gains every year at the short-term rate if held under 12 months (April to December is 9 months, so every exit is short-term at 20%). That tax drag can exceed the expected benefit of about 1.3% a year (my arithmetic from the Samco averages).
- Feasibility: yes mechanically; after tax the case is weak. Better used as a tilt on position size than as an in-or-out switch.
- Sources: https://insights.dsij.in/appmindshare/nifty-50-posted-gains-in-18-of-the-last-25-julys-will-the-bull-run-continue-58147 ; https://upstox.com/news/market-news/trading/analyzing-nifty-50-s-december-performance-trends-averages-and-historical-patterns-in-the-last-26-years/article-132700 ; https://www.srcc.edu/system/files/Article-No8-Efficient-Market-Hypothesis-and-Calendar-Effects-Updates.pdf ; https://trendlyne.com/posts/4478718/which-are-the-best-and-worst-months-for-indian-stocks-screener-stocks-outperforming-their-sectors ; https://wrightresearch.in/blog/buying-stocks-in-october-november-and-december-seasonal-patterns-in-global-and-indian-stock-markets ; https://wrightresearch.in/blog/decoding-the-march-effect-why-stocks-can-be-volatile-in-march ; https://ideas.repec.org/a/ids/gbusec/v24y2021i1p43-58.html

### 13. Fiscal-year-end weakness and April rebound

- Family: annual cycle, tax-year turn.
- Rules: buy at the close of a day in the last week of March (default L(3) of March) and sell at the close of the last trading day of April. Universe: Nifty 50 ETF by default; variants use a mid-cap or small-cap ETF or the Nifty Auto index, or the 10 worst year-to-date performers in the Nifty 500 (tax-loss-selling candidates). No stop in sources.
- Reported performance: Trendlyne (2006 to Feb 2024): April is the best month for most Nifty indices, most closing higher in 13 of 18 Aprils and Nifty Auto in 16 of 18. Samco via DSIJ: Nifty April average +1.94% over 2001-2025. Wright Research lists the proposed causes: 15 March advance-tax deadline, tax-loss harvesting before 31 March, corporate treasuries raising cash for the year-end balance sheet, institutional rebalancing.
- Evidence quality: practitioner tables only. No Indian paper testing a loser-rebound around 31 March was found. Kumar and Jawa's 1995-2015 regression does not show a significant April coefficient (+1.0% over January, t = 0.6).
- Costs: ETF version 0.1% for one trade a year. The loser-basket version costs about 0.6% per ₹15,000 position.
- Feasibility: yes for the ETF version; marginal for baskets.
- Sources: https://trendlyne.com/posts/4478718/which-are-the-best-and-worst-months-for-indian-stocks-screener-stocks-outperforming-their-sectors ; https://wrightresearch.in/blog/decoding-the-march-effect-why-stocks-can-be-volatile-in-march ; https://insights.dsij.in/appmindshare/nifty-50-posted-gains-in-18-of-the-last-25-julys-will-the-bull-run-continue-58147 ; https://www.srcc.edu/system/files/Article-No8-Efficient-Market-Hypothesis-and-Calendar-Effects-Updates.pdf

### 14. January barometer

- Family: annual cycle.
- Rules: hold the index in January. If the January return is positive stay long for February to December; otherwise hold treasury bills or a liquid fund for those 11 months. An Indian adaptation would use April (first month of the fiscal year) as the barometer month; that variant has no evidence at all.
- Reported performance: US 1857-2008 (Cooper, McConnell and Ovtchinnikov via Quantpedia): 10.38% a year against 9.98% for the index, volatility 16.8% against 19.2%, Sharpe 0.38.
- India-specific evidence: none found. Nifty January averages -0.47% over 2001-2025 (Samco via DSIJ), so the rule would have been out of the market in many years in which April to December was strong.
- Feasibility: yes mechanically; no reason to expect it to work in India.
- Sources: https://quantpedia.com/strategies/january-barometer ; https://insights.dsij.in/appmindshare/nifty-50-posted-gains-in-18-of-the-last-25-julys-will-the-bull-run-continue-58147

### 15. Same-calendar-month seasonality in individual stocks

- Family: annual cycle, cross-sectional.
- Rules (published version): universe is the largest 30% of stocks; each month sort on the stock's return in the same calendar month one year earlier (extensions average the same-month return over lags 12, 24, ..., 60 or up to 240 months); long the top decile, short the bottom decile, equal weight, rebalance monthly. Long-only adaptation: from the Nifty 100, buy the 5 to 10 stocks with the highest average same-calendar-month return over the previous 5 years; hold one month.
- Reported performance: Heston and Sadka (2008), NYSE and AMEX 1965-2002 via Quantpedia: long-short on the 12-month lag in large caps 0.69% a month, about 8.6% a year, volatility 12.2%, Sharpe 0.38 (t = 4.19). Their international paper found the pattern in Canada, Japan and 12 European markets, lasting up to five annual lags (unverified: snippet only). Keloharju, Linnainmaa and Nyberg report about 13% a year for a same-month strategy in the US (unverified: snippet only).
- India-specific evidence: none found. An emerging-markets study exists (Li, Zhang and Zheng) but could not be opened.
- Costs: monthly turnover is close to 100%. At ₹15,000 tickets a full rotation costs about 0.6% a month, about 7% a year (my arithmetic), which is the size of the whole published premium. No short leg is possible in cash equities overnight.
- Feasibility: marginal to no at ₹1.5 lakh. Worth a daily-data backtest for information, since it needs only prices.
- Sources: https://quantpedia.com/strategies/12-month-cycle-in-cross-section-of-stocks-returns

---

## E. Holidays and festivals

### 16. Pre-holiday and post-holiday long

- Family: holiday effects.
- Rules: take the NSE holiday list. Pre-holiday version: buy the index ETF at the close two trading days before a weekday exchange holiday and sell at the close of the last trading day before it. Post-holiday version: buy at the close of the last trading day before the holiday and sell at the close of the first trading day after it. Parameter: side in {pre, post, both}; whether to include holidays adjacent to weekends.
- Reported performance (global): Quantpedia, citing the Dow Jones 1896-2002: pre-holiday days returned 0.239% a day, about ten times a normal day; a strategy long only on about 10 pre-holiday days a year gave 6.39% a year including 4% interest on cash.
- India-specific evidence:
  - Lu and Patel (2016, Economics Bulletin), BSE indices before and during the 2008 crisis: "very strong post-holiday effects for most of the indices"; "the pre-holiday effect was completely missing"; the post-holiday effect strengthened during the crisis.
  - Kalimuthu and Saleem (2023), Nifty 50 and sector indices, 2016-2021: higher returns around Ramadan and Christmas; Christmas the only festival with positive returns in every sector index before Covid; by paired t-test Diwali is the only festival with a significant before-and-after difference, and only for Nifty 50 and Nifty Auto.
  - Siddiqui and Narula (2000-2011) tested a holiday effect within their GARCH study; the abstract does not report it as significant.
  - Agarwalla and Pandey: volatility is higher in the first half-hour after holidays.
- Costs: about 14 to 16 weekday holidays a year; each one-day trade costs about 0.10%.
- Failure modes: a later international study whose title describes "the decline and reversal" of the pre-holiday anomaly is mentioned in search results (unverified: snippet only; authors not confirmed). The Indian post-holiday result comes from a sample centred on 2008.
- Feasibility: yes; small expected contribution.
- Sources: https://quantpedia.com/strategies/pre-holiday-effect ; https://ideas.repec.org/a/ebl/ecbull/eb-16-00286.html ; https://ideas.repec.org/a/aag/wpaper/v27y2023i1p115-142.html ; https://ideas.repec.org/a/sae/vision/v17y2013i3p233-245.html ; https://iima.ac.in/sites/default/files/rnpfiles/19191060542012-11-03.pdf

### 17. Muhurat session

- Family: holiday effects.
- Rules: buy at the close of the last regular session before the Diwali Muhurat session. Version A: sell at the Muhurat open (pre-open auction). Version B: sell at the Muhurat close. Variant: use a small-cap or micro-cap vehicle instead of the Nifty. One trade a year.
- Reported performance (Finnovate table compiled from NSE data, 2006-2025; move measured from the previous close to the Muhurat close): Nifty up in 15 of 20 sessions. Moves by year: 2006 +0.18, 2007 -0.62, 2008 +6.35, 2009 -0.01, 2010 +0.48, 2011 +0.19, 2012 -0.29, 2013 +0.16, 2014 +0.23, 2015 +0.53, 2016 -0.14, 2017 -0.63, 2018 +0.65, 2019 +0.37, 2020 +0.47, 2021 +0.49, 2022 +0.87, 2023 +0.51, 2024 +0.40, 2025 +0.10 (all %). Mean +0.51%, median +0.30%, mean excluding 2008 +0.21% (my arithmetic). Positive in every session from 2018 to 2025.
- The opening pop: in 17 of the 20 sessions in that table the Nifty closed below its own Muhurat opening level (exceptions 2006, 2008, 2024; my count from the open and close columns). So the gain sits in the gap between the previous close and the Muhurat open, and the session itself usually drifts down. Version A captures it only if the ETF also gaps and the auction fill is obtained.
- Market-cap gradient (same source, 2015-2024): small and micro caps moved more than the Nifty in most years, for example 2024 Nifty +0.40, Midcap 150 +0.68, Smallcap 250 +1.11, Microcap 250 +1.09; 2023 +0.51, +0.67, +1.14, +1.33. The Microcap 250 index was launched in 2021, so earlier values are back-calculated.
- No predictive value for the following year (same source).
- Costs: 0.10% round trip in NIFTYBEES against a median 0.30% and an ex-2008 mean of 0.21%. ETF liquidity in a one-hour symbolic session is thin (estimate).
- Feasibility: yes mechanically; expected profit on ₹1.5 lakh is a few hundred rupees a year. The 2026 session (reported as 8 November 2026; unverified: snippet only) has already taken place; its result was not found.
- Sources: https://www.finnovate.in/learn/blog/20-years-muhurat-trading-historical-returns ; https://www.businesstoday.in/markets/stocks/story/nifty-up-7-years-straight-in-muhurat-trading-will-samvat-2082-make-it-eight-498995-2025-10-21

---

## F. Scheduled events

### 18. Union Budget window

- Family: scheduled events.
- Rules: let B be Budget day (1 February since 2017; interim Budgets in election years count). Buy the index ETF at the close of B-2 and sell at the close of B-1 (pre-Budget day). Stay flat through Budget day. Buy at the close of B and sell at the close of B+1 (default) or B+3 or B+5. Conditional variant: take the post-Budget leg only if the Nifty fell more than 3% in the 20 trading days before B.
- Reported performance:
  - Upstox, 2004-2023, 24 Budgets including interim ones, close-to-close: Nifty up on the day before in 16 of 24 (67%), on Budget day in 11 of 24 (46%), on the day after in 15 of 24 (63%). Bank Nifty 17, 12 and 16 of 24. Excluding interim Budgets: Nifty 13, 8 and 13 of 20. Third-quartile Budget-day return 0.81% for Nifty and 1.25% for Bank Nifty. Average 1-day-after and 3-day-after returns were positive over 5, 10 and 20 year windows (values shown only as images).
  - Samco via Business Today: average Budget-day move since 2010 +0.19% for Nifty and +0.42% for Bank Nifty; Nifty between -0.11% and -0.13% on each of the last three to four Budget days (2023 to 2025).
  - Samco: average Nifty return -0.52% in the week before and +1.36% in the week after the Budget, with the week before positive in only 8 of 15 years (unverified: snippet only). Geojit: Nifty rose in 12 of the last 15 post-Budget weeks (unverified: snippet only). SBI Securities: a pre-Budget fall of more than 3% was followed by rebounds over one week, one month and three months (unverified: snippet only).
  - One month after: Swastika, Budgets 2016-2025: about half up and half down, average mildly positive, best 2021, worst 2020.
- Context for 2026: Budget 2026 was presented on Sunday 1 February 2026 with a normal trading session; the Nifty had fallen about 4% in January; it raised STT on derivatives (Business Today; ClearTax).
- Sample-size warning: 24 events. A 67% hit rate on 24 trials is within what chance produces (a 95% interval of roughly 47% to 82%, my arithmetic).
- Costs: two or three one-day ETF trades a year at 0.10% each.
- Feasibility: yes; contribution is small and uncertain.
- Sources: https://upstox.com/news/market-news/trading/how-do-major-indices-react-to-union-budget/article-65567 ; https://www.businesstoday.in/markets/stocks/story/nifty-bank-nifty-budget-day-stock-market-returns-since-2010-full-table-512707-2026-01-23 ; https://www.businesstoday.in/union-budget/story/why-budget-day-returns-are-mostly-muted-should-investors-bet-on-a-post-budget-rally-512931-2026-01-27 ; https://www.swastika.co.in/big-budget-day/nifty-50-performance-one-month-after-union-budget-10-year-reality-check

### 19. Event implied-volatility crush (Budget, election result, RBI policy)

- Family: scheduled events, volatility.
- Rules (hypothesis; no source gives tested rules): at the close on the last session before a scheduled binary event, sell one lot of a Nifty iron butterfly or iron condor in the nearest expiry after the event (short strikes at the money or at about 1 standard deviation, wings 2 to 3% beyond); close at the close of the event day or the next day. Stop at a loss of 1x the credit. The mirror trade (buy a straddle 5 to 10 days before the event, sell the day before) bets on the pre-event rise in implied volatility.
- Evidence: anecdotal. India VIX rose ahead of Budget 2026 and fell about 20% on the Monday after the 2024 exit polls (headlines; unverified: snippet only). Upstox's Budget article notes pre-event drift and volatility in general terms. Shaikh and Padhi find India VIX falls on expiry days, which shows scheduled dates do move it. No Indian study measuring whether event-day realised moves are smaller than the implied move was found.
- Failure modes: the events are exactly when realised moves can exceed implied ones (the Nifty's fall on the June 2024 election-result day is the standard example; figure not checked in this session). With one lot there is no diversification across events.
- Feasibility: marginal. Defined-risk structures fit; sample is a handful of events a year.
- Sources: https://upstox.com/news/market-news/trading/how-do-major-indices-react-to-union-budget/article-65567 ; https://ceeol.com/search/article-detail?id=285053

### 20. RBI policy day

- Family: scheduled events.
- Rules to test: buy the index ETF (or Bank Nifty exposure) at the close five sessions before the Monetary Policy Committee announcement and sell at the close of the day before; alternatively buy the close of announcement day and sell five sessions later. Six scheduled announcements a year.
- Evidence: weak to negative. RBI Working Paper 03/2024 (Sensex; summary seen in search results, PDF did not parse): only the "path" component of policy surprises explains announcement-day equity returns, not the rate decision itself; anticipated actions are already in prices (unverified: snippet only). An IIM Calcutta study of Nifty constituents found the announcement-day impact "may or may not be significant" (unverified: snippet only). A 2009-2020 study found returns largely unaffected by rate changes (unverified: snippet only). An unreviewed dashboard of 26 decisions over 2015-2025 reports about +0.14% in the five days before, about -0.27% on the day and about +1.14% over the following month (unverified: snippet only; the page opened but its numbers are rendered by script and were not visible). No Bank Nifty pre-announcement drift study was found.
- Feasibility: yes mechanically; no evidence of an edge.
- Sources: https://rohanbeingsocial.github.io/repoeffectonmarket/ (opened; values not rendered)

### 21. FOMC next-day long in the Nifty

- Family: scheduled events, global spillover.
- Rules: take the eight scheduled FOMC announcement dates a year. The statement is released at 14:00 US Eastern time, after the NSE close. Buy the index ETF at the NSE close on the announcement date (the Indian session that ends before the statement) and sell at the NSE close of the next Indian session. If that Indian day is a holiday use the last session before the statement. No stop. Parameter: exit at next open instead of next close.
- Reported performance: Lakdawala (NSE-NYU conference slides, Dec 2018), Nifty 50, return "on day after FOMC meeting relative to day of FOMC meeting":
  - Jan 1991 to Jun 2018: mean 0.33% on FOMC days against 0.03% on other days (standard deviation 1.69% for both); regression constant 0.347 (t = 3.47, 234 observations).
  - Jan 1991 to Jan 2000: 0.20% against 0.03%. Feb 2000 to Jun 2018: 0.39% against 0.03%.
  - Sub-period constants: 2000-2008 0.72 (t = 4.65, 77 meetings); 2009-2018 0.215 (t = 1.66, 72 meetings). The effect roughly halved or worse after 2008.
  - The Nifty's response to a hawkish surprise is negative and has grown: -2.24 per 25 basis points of surprise over 2000-2018 (t = -3.28).
- Related evidence: Lucca and Moench (NY Fed Staff Report 512): S&P 500 rose 49 basis points on average in the 24 hours before scheduled announcements since 1994 (annualised Sharpe about 1.1), with similar drifts of 29 to 52 basis points in the DAX, FTSE, CAC, IBEX and SMI and none in the Nikkei. Their 2018 update: after 2011 the drift appeared only at meetings with a press conference. Kurov et al. (2021), "The disappearing pre-FOMC announcement drift", is cited by the BSIC article as showing the unconditional US drift faded after publication (not opened). BSIC (2023, informal): MSCI India drifts up visually around FOMC dates but few regression coefficients are significant. Quantpedia SPY 1993-2019: 2.30% a year for holding one day around meetings, drawdown 7.17%.
- What this trade is: because the NSE is closed during the US pre-announcement window and the announcement, the Indian "next-day" return is the reaction to the statement plus the overnight US move, not the pre-FOMC drift. It is compensation for carrying announcement risk overnight.
- Costs: eight ETF round trips a year at 0.10%: 0.8% a year against a gross 8 x 0.2 to 0.3% = 1.6 to 2.6% a year at post-2008 magnitudes (my arithmetic).
- Failure modes: hawkish surprises (the 19 Jun 2013 taper statement: Nifty -2.94% next day in the slides' table; 21 Sep 2011: -4.26%); decay after 2008; all FOMC meetings have had press conferences since 2019, so the post-2018 behaviour needs fresh testing; the sample ends June 2018.
- Feasibility: yes. Needs a hand-maintained FOMC date list.
- Sources: https://nsearchives.nseindia.com/research/content/nse_nyu/white_paper_2017_18_7.pdf ; https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf ; https://libertystreeteconomics.newyorkfed.org/?p=312 ; https://bsic.it/the-pre-fomc-drift-in-emerging-markets/ ; https://quantpedia.com/strategies/federal-open-market-committee-meeting-effect-in-stocks ; https://quantpedia.com/quantpedias-composite-seasonalcalendar-strategy-case-study/

### 22. Lok Sabha election window

- Family: political cycle.
- Rules: buy the index ETF six months before the first polling day and hold until six months after it; or, more conservatively, buy at the close of result day and hold six months. One trade every five years. A risk rule that follows from the history: hold no short-option or leveraged position over result day.
- Reported performance: IndiaSpend (via The Quint, 2019): for the four elections 1999 to 2014 the Nifty and Sensex were higher six months after the first polling day than six months before; the "average rise of 40.8%" compares those two dates. Ambit (quoted by freefincal): about 33% a year for the Sensex in the three years after three "critical" elections against 16% a year over 30 years; freefincal notes the predicted follow-through after 2014 did not appear in 2015-2016 and concludes "each election year is unique". Franklin Templeton figures (2004 was the one case of declines both before and after; 2009 the strongest) (unverified: snippet only). The 17 May 2004 fall of about 11% after the result (unverified: snippet only).
- Evidence quality: five or six observations, all inside a secular bull market, with one large adverse case. Not testable in any statistical sense.
- Next occurrence: the next general election is due in 2029, so this is not actionable before late 2028.
- Feasibility: yes mechanically; treat as a risk-management note, not a strategy.
- Sources: https://www.thequint.com/elections/why-nifty-sensex-rose-after-every-general-election-since-1999 ; https://freefincal.com/lok-sabha-elections-stock-market-returns/

### 23. Monsoon seasonal and rainfall-conditional sector trade

- Family: weather cycle.
- Rules: seasonal version: hold a monsoon-sensitive sector index (FMCG, Auto, agrochemicals) from 1 June to 30 September and the Nifty otherwise. Conditional version: go long those sectors only when cumulative June to August rainfall is at or above the long-period average (needs India Meteorological Department data).
- Reported performance: Pandey, Obuobi, Singh and Bhattacharyya (Mendeley Data, Feb 2026), five sector indices (agrochemicals, irrigation, FMCG, automobiles, tourism), using OLS, CAPM, seasonal ARIMA, GARCH, rolling regressions and regime switching: "inconsistent and limited direct effects of monsoon on the stock market"; regressions had insignificant explanatory power. Their "Seasonal Long-Only" strategy underperformed buy-and-hold. Three regime-based variants beat both in their backtest and paper trading, but the rules are not given in the abstract and the description is of a student project dataset.
- Other evidence from search summaries: weak negative correlation (about -0.27) between rainfall and Sensex returns; deficient-rain years such as 2014, 2021 and 2023 had strong Nifty returns; brokers argue the FMCG link has weakened with urbanisation (all unverified: snippet only).
- Feasibility: yes mechanically for the seasonal version via a sector ETF where one exists; evidence is negative.
- Sources: https://data.mendeley.com/datasets/tkt4zj38xt/1

---

## G. Derivative expiry effects

### 24. Expiry-week and day-after-expiry long

- Family: expiry effects.
- Rules: US version (Stivers and Sun): hold large caps with active options during the monthly option-expiration week, cash otherwise. Indian adaptation: buy the index ETF at the close of the trading day five sessions before the monthly expiry and sell at the expiry-day close; variant: buy at the expiry-day close and sell at the next close (day-after effect). Use the actual expiry date from the contract master (last Thursday before September 2025, last Tuesday after).
- Reported performance: US S&P 100, 1988-2010 via Quantpedia: 0.528% average weekly return in expiration weeks, 9.3% a year including interest on cash for the other weeks, Sharpe 0.61; the following (fourth-Friday) week underperforms modestly. SPY 1993-2019 (Quantpedia case study): 4.93% a year, drawdown 20.39%.
- India-specific evidence, mostly null on returns:
  - Samineni et al. (2020), Nifty Bank daily closes, 1 Jan 2010 to 31 Mar 2020, ARMA-EGARCH: no expiration-day effect on mean returns, none on volatility, no price reversal after expiry.
  - Their literature review: Narang and Madhu (2013) found returns, turnover and volatility high on expiry day and the day after; Wats (2017) found the effect across the expiry week; Mahalwala (2016) found no effect on returns, volatility or reversal; Bhaumik and Bose (2007) found effects on volume, returns and volatility; Vipul (2005) found a volume surge.
  - Debasish (2010), index futures expiries Jun 2001 to May 2009: higher volume on expiry days and weeks, no significant difference in mean returns (unverified: snippet only).
  - Agarwalla and Pandey (IIMA 2012; Journal of Futures Markets 2013): the expiry effect is a volatility effect confined to the last half-hour, the window over which the settlement price is averaged, and is stronger for stocks with single-stock futures.
  - Gavhale (2025): the Nifty is on average lower at the monthly expiry close than on the next month's first trading day (see strategies 1 and 4), which supports buying at expiry rather than in the days before it.
- Feasibility: yes mechanically; Indian evidence does not support a return edge in the week before expiry.
- Sources: https://quantpedia.com/strategies/option-expiration-week-effect ; https://quantpedia.com/quantpedias-composite-seasonalcalendar-strategy-case-study/ ; https://koreascience.kr/article/JAKO202032462596875.page ; https://iima.ac.in/sites/default/files/rnpfiles/19191060542012-11-03.pdf ; https://www.business-standard.com/article/markets/expiration-day-affectes-spot-market-volatility-on-stock-exchanges-study-113091500770_1.html ; https://arxiv.org/html/2507.04859v2

### 25. Expiry-day short premium (0DTE)

- Family: expiry effects, volatility.
- Rules (the common practitioner template): on Nifty weekly expiry day (Tuesday) at 09:20 sell the at-the-money call and put expiring that day; buy wings 1 to 1.5% away to define risk and reduce margin; per-leg stop at 25 to 40% above the entry premium; exit everything by 15:00 to 15:15 or let it settle. One lot. A daily-data approximation sells at the day's opening option prices and settles at the final settlement price with no stop.
- Evidence: practitioner only. Shaikh and Padhi: India VIX falls significantly on option expiry day. Agarwalla and Pandey: volatility rises in the last half-hour on expiry day, which argues for exiting before 15:00. A trading-education site states the 09:20 straddle is "least profitable on Tuesday (expiry day)" for Bank Nifty and that "expiry day works, but marginally" (unverified: snippet only; no data shown). No reproducible Nifty 0DTE study for 2019-2025 was found.
- Regulatory decay: SEBI cut weekly expiries to one index per exchange from 20 Nov 2024 specifically because expiry-day option activity was hurting retail traders (PhonePe explainer); expiry moved to Tuesday in Sep 2025; option STT rose to 0.15% in Apr 2026; SEBI's 2025 action against Jane Street concerned expiry-day index manipulation (mentioned in Gavhale 2025; order not opened). Any pre-2025 backtest describes a different market.
- Costs: four legs in, two to four legs out; charges about ₹150 to ₹250 plus slippage on fast-decaying options; intraday option data is required for the stop logic.
- Feasibility: marginal. Margin for one hedged lot fits; one lot is all-or-nothing risk for the account on 50 days a year.
- Sources: https://ceeol.com/search/article-detail?id=285053 ; https://iima.ac.in/sites/default/files/rnpfiles/19191060542012-11-03.pdf ; https://www.phonepeinvest.com/buzz/insights/weekly-expiry-days-in-indian-fo-markets/ ; https://nsearchives.nseindia.com/content/circulars/FAOP68747.pdf

---

## H. Quarter-end

### 26. Quarter-end window dressing

- Family: quarter-end flows.
- Rules to test: five trading days before each quarter end (March, June, September, December) buy the 5 to 10 Nifty Midcap 150 or Nifty 500 stocks with the highest 60 to 90 day return (the names funds would want to show); sell at the close of the last trading day of the quarter. Reversal variant: avoid or exit those names on the first two trading days of the new quarter.
- Evidence: Chowdary (IIM Calcutta doctoral thesis, abstract): Indian equity funds do window-dress; risk-based dressing (cutting portfolio risk before the disclosure date) is about three times as common as return-based dressing (buying winners, selling losers); it is done mainly by managers with poor prior performance; retail flows do not respond to it. A glossary page claims recent 90-day outperformers appear more often in reported portfolios, concentrated in March and December (unverified: snippet only). Indian funds disclose portfolios monthly, which removes much of the quarter-end motive (unverified: snippet only).
- No Indian study of price pressure in the last days of a quarter was found.
- Costs: a basket of ten ₹15,000 positions held five days costs about 0.6% per name.
- Feasibility: marginal; evidence anecdotal.
- Sources: https://studentlive.iimcal.ac.in/sites/all/files/pdfs/abstract_bobbur_abhilash_chowdary.pdf

---

## I. Combination

### 27. Composite calendar strategy with a trend filter

- Family: composite.
- Rules (Quantpedia case study, US): be long SPY on any day that belongs to at least one calendar window, flat otherwise, with no leverage when windows overlap. Windows: turn-of-month (buy last-day close, sell first-day close), FOMC (buy the close before the meeting, sell the close after), option-expiration week (buy the Friday before the second Saturday, sell the following Thursday), payday (buy the 15th close, sell the 16th close). Filter: trade only when the price is above its 200-day average.
- Indian adaptation to test: windows = strategy 1 (L(5) to F(3)) + strategy 21 (FOMC next day) + strategy 18 (day before and day after Budget) + strategy 16 (post-holiday day) + strategy 17 (Muhurat); filter = NIFTYBEES close above its 200-day simple average on the entry day; idle cash in a liquid ETF.
- Reported performance (SPY 1993-2019): composite without filter 9.06% a year, maximum drawdown 24.02%, return-to-drawdown 0.38; with the 200-day filter 7.47% a year, drawdown 10.14%, return-to-drawdown 0.74. Components alone: turn-of-month 3.01%, FOMC 2.30%, expiration week 4.93%, payday 2.08% a year.
- India-specific evidence: none for the composite. Zerodha's author observed that Indian turn-of-month results track the broader trend and proposed a trend filter without testing it.
- Costs: about 12 to 25 ETF round trips a year, 1.2 to 2.5% a year.
- Failure modes: each added window adds parameters; windows chosen after seeing the data; the filter removes trades after falls, which is also when turn-of-month rebounds have been largest.
- Feasibility: yes.
- Sources: https://quantpedia.com/quantpedias-composite-seasonalcalendar-strategy-case-study/ ; https://inthemoneybyzerodha.substack.com/p/turn-of-the-month-tomtotm-strategy

---

## Negative or cautionary evidence

1. Costs remove every daily-frequency calendar effect at this account size. The overnight effect is the clearest case: +595% gross on Nifty futures over 2011-2018 became a 67% loss on ₹1 lakh at a 0.02% cost assumption (Marketcalls), and the futures STT alone is now 0.05%.
2. Sell-in-May is inverted in India. May to October has outperformed November to April on Sensex since 2000 (Stable Investor) and on Nifty monthly averages for 2001-2025 (Samco via DSIJ, my arithmetic). A Halloween investor from 1995 to 2015 ended with ₹40,000 against ₹74,975 for buy-and-hold.
3. Day-of-week effects in India do not survive out of sample. Wednesday (1995-2015), nothing (2011-2018), Tuesday and Friday (2020-2021): three samples, three answers. The best-known result belongs to the weekly-settlement era before 2002.
4. Month-of-year effects are not statistically significant in the most recent clean sample (2011-2018, Nifty 50). The December and November strength and January to March weakness are averages over 25 observations each with large dispersion.
5. Expiry-day and expiry-week return effects are mostly absent in Indian studies; what exists is a volume effect and a last-half-hour volatility effect. Bank Nifty 2010-2020 shows no effect on mean returns, volatility or reversal.
6. The pre-FOMC drift faded where it was discovered. After 2011 it appeared only on press-conference meetings (Lucca and Moench 2018) and a 2021 paper is titled "The disappearing pre-FOMC announcement drift". The Indian next-day effect fell from 0.72% (2000-2008) to 0.215% (2009-2018, t = 1.66).
7. Budget, election and Muhurat statistics rest on 20 to 24 annual observations or fewer. Hit rates of 63 to 75% on such samples are not distinguishable from 50% with any confidence. Budget-day returns have been slightly negative in each of the last three or four years.
8. Monsoon timing fails: a seasonal long-only sector strategy underperformed buy-and-hold in the one study that tested it.
9. SIP-date timing is worth a few basis points a year at long horizons according to the one paper that finds an effect, and nothing according to two practitioner studies. The paper's return formula is not an IRR.
10. Publication decay is the norm. Quantpedia's own turn-of-month page warns that calendar effects "tend to vanish or rotate to different days in a month"; the payday effect weakened as pay schedules changed; Siddiqui and Narula found Indian anomalies disappear when the sample is cut into three-year pieces.
11. Data-mining risk is high in this whole area. The futures study listed by Quantpedia (Carchano, Tornero) tested 188 calendar effects in three markets and found one that survived. Hansen and Lunde's point (via Quantpedia's pre-holiday page) is that calendar effects must be tested jointly, otherwise spurious ones pass.
12. Regime breaks in India make old samples a poor guide: rolling settlement (2002), pre-open auction (2010, which changes what "open" means), weekly options (2019 onward), one weekly index per exchange (Nov 2024), Tuesday expiry (Sep 2025), lot-size changes (Jan 2026), STT increase (Apr 2026).
13. Tax asymmetry: a seasonal in-and-out investor pays 20% short-term tax on gains that a buy-and-hold investor would defer and pay at 12.5%. A seasonal rule has to beat buy-and-hold by more than that difference, on top of costs, to be worth switching for. For an account that trades in windows and is otherwise in cash by design this matters less, but it should be in the backtest.
14. Index backtests are not ETF backtests. Published Indian tests use index closes (and for overnight tests, index opens that were not tradable before 2010). The ETF's closing price, its spread and its premium or discount to NAV decide the real result.

## Open questions

1. Is India's late-month strength anchored to the calendar month end or to the monthly F&O expiry? Before September 2025 the fifth-last trading day sat next to the last-Thursday expiry, so the two cannot be told apart in old data without measuring returns relative to each anchor. After the move to last Tuesday they can.
2. Did turn-of-month in the Nifty persist out of sample after the QuantifiedStrategies fit (about 2021) and through the 2024-2025 flat patch that Zerodha reports? A walk-forward test with the window fixed at L(5) to F(3) on data to 2021 and evaluated afterwards answers this.
3. How large is the turn-of-month effect in small and mid caps in numbers, and does it survive the ETF spread? Only the abstract of the 2023 paper was seen.
4. What is the Nifty's FOMC next-day return for July 2018 to 2026, when every meeting has had a press conference and the Fed went through a full hiking and cutting cycle? The only Indian evidence ends June 2018.
5. What were the magnitudes in the Nifty overnight short-option study (2017-2020), and does the result hold for 2021-2026 with Tuesday expiries, a 65 lot and 0.15% STT? Only the first page was readable.
6. Does the Muhurat gap show up in NIFTYBEES prices, and can a retail order get the Muhurat opening auction price? The 20-year table is for the index.
7. Not researched because the search budget ran out: India VIX seasonality by month and around events with numbers; any SEBI or NSE study of expiry-day behaviour after the November 2024 and September 2025 changes; gold seasonality around Akshaya Tritiya and Dhanteras; index-rebalance dates (March and September Nifty reviews) as calendar events; advance-tax dates (15th of June, September, December, March) and liquidity; lunar-cycle claims; Samvat (Diwali-to-Diwali) year patterns; the week before Diwali.
8. Several India-specific papers were seen only as search summaries and should be read before being relied on: the 1994-2014 eleven-index calendar study (Emerald), Patel and Mallikarjun on day-of-week after T+2, Debasish (2010) on expiry, the RBI working paper on policy surprises, and the Li, Zhang and Zheng emerging-market test of same-month seasonality.
9. Exact current margin for one hedged Nifty option structure (iron butterfly, iron condor) at a 65 lot was not verified; it decides whether strategies 6, 9, 19 and 25 are possible at all.
10. NSE holiday list and expiry calendar for each backtest year need to be built from exchange circulars; no machine-readable source was identified in this session.
