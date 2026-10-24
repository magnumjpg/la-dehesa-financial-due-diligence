# La Dehesa del Castrillo S.L.

### Hospitality Feasibility, Senior Debt Underwriting & Computed Due Diligence

**A portfolio-grade financial model built from my own university feasibility study.**
Python 3.11 · 41 automated tests · 12-tab Excel model · 14-step pipeline

> **Read this first.** This is not a "safe deal" pitch. The original promoter case produces €86,275 of Year 1 revenue, €11,297 of EBITDA and negative Year 1 cash. At the official INE Segovia occupancy (21.24%), the project does not cover debt service in Year 1 (DSCR 0.40x). The headline Python case (31.36% mature occupancy, 28.23% in Year 1) is an **upside / management case**, not a market forecast, and it is the only case that clears the 1.25x covenant. The audit is deliberately allowed to fail: **8 of 14 rules pass, 5 material exceptions and 1 warning remain open**, and the verdict is `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`.

---

## 1. What this project is

I started with my own university feasibility study for a 25-hectare rural estate in Segovia (7 double rooms, one full country house, a 21-seat restaurant and a natural swimming biopool). The original Excel is a single-sheet promoter simulator with live formulas; it uses 19.2% occupancy. The Word report documents a more conservative 16.5–17% occupancy, part-time contracts and a LEADER grant application. That gap between the Word and the Excel is the first thing the audit had to reconcile.

I then rebuilt the analysis in Python to answer the questions the original work could not answer:

- What happens at the **official INE occupancy** instead of the promoter's assumption?
- Does the project actually **fund itself at close**, once pre-opening costs, working capital and a debt-service reserve are included?
- Is the payroll **legal per hour** under the Segovia hospitality agreement and the 2026 SMI?
- Does the **VAT bridge** create cash or just move it?
- Can **Phase II** really be self-funded from Phase I cash, or is it a double-spend of the grant and the VAT refund?
- What do the returns look like **with and without an exit**?

The Python layer is not a cosmetic rewrite. It adds a three-case architecture, a sources-and-uses engine, a computed audit, a live formula-driven Excel workbook, and a test suite that locks in the honest numbers.

---

## 2. Three cases, side by side

| Case | Mature occupancy | Revenue Y1 | EBITDA Y1 | DSCR Y1 | Cash Y1 | Project IRR (no exit) | Project IRR (8.5% exit) | Equity IRR (8.5% exit) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Management (upside)** | 31.36% | €154,548 | €66,086 | 1.34x | €10,790 | −20.89% | 15.43% | 29.74% |
| **INE market** | 21.24% | €95,555 | €17,621 | 0.40x | −€29,915 | −27.31% | 9.63% | 17.43% |
| **Promoter (original Excel)** | 19.20% | €86,275 | €11,297 | 0.33x | −€2,553 | −29.48% | 6.84% | 10.95% |

**What each case is:**

- **Promoter** — a faithful replication of the original university Excel: 19.2% occupancy (491 room-nights over 2,555 available), €85 room ADR, €380 house ADR, €20 restaurant ticket, 4.5% / 25-year debt and no grant. The Python model reproduces the original revenue and EBITDA to the euro and the Year 1 cash within €7 (original ≈ −€2,560; model −€2,553.20). This is the case the author actually underwrote.
- **INE market** — the independent benchmark: 21.24% official Segovia room occupancy in 2025 (INE EOTR table 2070), with the original unit economics and the same debt. It is the closest thing to a "market" case in the workbook.
- **Management (upside)** — the headline Python case: 31.36% mature occupancy (1.48x the INE average), one on-site meal per guest per day at a €25 ticket, 5.5% senior debt, and the €163,000 LEADER grant in Month 14. This is an operating upside, not a base case.

The three cases share the same CapEx, tax rate and balance-sheet mechanics. The difference is demand and unit economics, which is exactly where the risk sits.

---

## 3. The findings that matter

1. **The original Excel is the promoter case, not the base case.** It produces €86,275 of revenue and €11,297 of EBITDA. The published Python model's €154,548 / €66,086 is a management upside, not a correction of the original.
2. **The INE market case does not cover debt service in Year 1.** At 21.24% occupancy, EBITDA is €17,621, DSCR is 0.40x and Year 1 cash is −€29,915. The project only works if occupancy is materially above the provincial average.
3. **The management case clears the covenant at 28.23% in Year 1 and 31.36% in Year 2.** DSCR is 1.34x in Year 1, 1.64x in Year 2 and 1.73x in Year 3. That is 1.48x the INE market average at maturity, which is the central commercial assumption to defend. Note that the annual P&L uses a simplified cost stack; with the full unit-economics cost stack (OTA, amenities, breakfast), the covenant break-even is 28.44% and the margin of safety is much thinner.
4. **There is a €70,768 funding gap at close.** Close-day uses are €948,858 (CapEx €729,000 + input VAT €153,090 + pre-opening €25,000 + working capital €20,000 + 6-month DSRA €21,768). Close-day sources are €878,090 (debt €507,500 + equity €217,500 + VAT bridge €153,090). The €163,000 LEADER grant arrives in Month 14 and cannot fund close. After the omitted uses, management Year 1 cash is **−€55,978**, not +€10,790.
5. **The credit line is internally inconsistent.** The model draws a €143,596 VAT bridge in the management case, €147,285 in the market case and €166,752 in the promoter case, while the stated revolving line is €50,000. The bridge must be disclosed as a separate facility or the line must be increased.
6. **Phase II is not self-funded.** Phase II needs €435,564 (€359,970 net CapEx + €75,593.70 VAT). Phase I generates €193,950 of cash by the end of Year 2. The phase-gate gap is **−€241,614**, so the gate returns `DO NOT PROCEED`. The old "100% self-funded" claim was a double-spend of the LEADER grant and the VAT refund.
7. **Returns depend on an exit.** Without an exit, the 5-year project IRR is negative in all three cases (−20.89% management, −27.31% market, −29.48% promoter). With an 8.5% cap-rate exit, the management project IRR is 15.43% and the equity IRR is 29.74%. The exit, not the operating cash flow, is what drives the return.
8. **The audit is computed and can fail.** 8 of 14 rules pass. The five material exceptions are adjusted cash, sources & uses, credit-line limit, Phase II self-funding and market DSCR. The warning is management occupancy vs. INE. This is the point of the audit layer: it reports what the model actually does, not what the narrative wants.
9. **Payroll is part-time and hourly-compliant.** The original Word documents about 1,900 hours for two cooks and 1,792 hours for cleaning. The refined model uses 950 + 950 + 1,792 = 3,692 hours (2.09 FTE). Hourly gross is €14.21 for the cooks and €9.77 for cleaning, above the 2026 SMI (€9.69) and the Segovia convenio floor (€10.12 for a cook, €9.02 for an auxiliary). The earlier "3 FTE / full-time convenio" comparison was wrong; the remaining risk is scheduling and coverage, not the hourly rate.
10. **The "BB+ investment grade" and "BINs shelter" claims were wrong.** BB+ is sub-investment-grade, not investment grade. The management case has positive EBT from Year 1 (€31,041) and pays €7,760 of corporate tax; it does not have a BIN shield. Both claims have been removed from the model narrative.

---

## 4. Original vs refined: the reconciliation

| Category | Original Excel | Refined: mgmt / market / promoter | Notes |
|---|---|---|---|
| Occupancy (mature) | 19.20% | 31.36% / 21.24% / 19.20% | Management is 1.48x INE; promoter is the original. |
| Year 1 revenue | €86,275 | €154,548 / €95,555 / €86,275 | Management adds 1 meal/guest/day at €25. |
| Year 1 EBITDA | €11,297 | €66,086 / €17,621 / €11,297 | Promoter matches the original to the euro. |
| Year 1 ending cash | ≈ −€2,560 | €10,790 / −€29,915 / −€2,553 | Original negative cash is a real funding gap. |
| Year 1 DSCR | n/a | 1.34x / 0.40x / 0.33x | Only management clears 1.25x. |
| CapEx | €725,000 | €729,000 | Includes €4k Kit Digital. |
| Payroll (annual) | €58,740 | €60,075 | Part-time hours; employer SS included. |
| Input VAT on CapEx | Not modeled | €153,090 gross / €143,596 bridge | 21% deductible; bridge is financing. |
| Output VAT | Not modeled (net revenue) | 10.0% statutory | Original sheet did not apply 21% to sales. |
| Balance sheet | Single sheet, no balance sheet | Assets = L + E (€0.00) | Strict double-entry, 5 years, 3 cases. |

### The "VAT paper trap" correction

The old README claimed that applying 21% VAT to hospitality sales created a −€152,250 Year 1 cash deficit, and that correcting it to 10% "confirmed solvency" at +€60,750. **That is not what the original Excel does.** The original sheet works in net revenue and does not apply 21% output VAT to sales. Its negative Year 1 cash is a real funding gap, not a VAT artifact.

The refined model does apply the statutory 10% hospitality rate (Ley 37/1992, Art. 91.Uno.2.2ª) and does recognise the 21% input VAT on CapEx as a deductible asset. But the bridge that funds the input VAT is a **financing source**, not a grant:

- It is drawn at close (€153,090 in the funding engine; €143,596 net of output VAT in the annual model).
- It carries 5.5% interest. The annual model charges one full year of bridge interest in Year 2 (€7,897.80), which is why Year 2 net income is €29,583 rather than €35,506.
- It is repaid from the AEAT refund in Month 18. The refund is not a second inflow.

The honest conclusion is therefore: **the original negative cash is a funding gap, and the management case is solvent only because of the upside occupancy and the bridge.** The VAT correction changes the timing and the financing structure; it does not create €213,000 of value.

---

## 5. Demand calibration: INE vs promoter vs management

The INE *Encuesta de Ocupación en Alojamientos de Turismo Rural* (EOTR), table 2070 for Segovia, reports:

| Period | Room occupancy | Occupied room-nights |
|---|---:|---:|
| 2023 | 21.32% | — |
| 2024 | 21.50% | — |
| 2025 | **21.24%** | 77.5 days |
| August 2025 | 36.78% | — |
| January 2025 | 9.58% | — |

The management case uses a monthly series calibrated to the 2025 annual average of 21.24%, with the January and August anchors preserved. After the 2026 ramp (90% in Year 1, 100% in Year 2, 105% from Year 3), the management case reaches 28.23% in Year 1, 31.36% in Year 2 and 32.93% in Year 3. The monthly engine shows the winter trough in March and the summer peak in August.

The promoter case uses the original Excel's 19.2% (491 room-nights / 2,555 available). The market case uses 21.24% with the original unit economics. The gap between 19.2% and 31.36% is the commercial risk the model is underwriting.

---

## 6. Unit economics (USALI and marginal costing)

| Metric | Value |
|---|---:|
| Capacity | 8 keys (7 double rooms + 1 country house) = 2,920 unit-nights/year |
| Daily gross revenue at 100% occupancy | €1,500 (€975 lodging + €525 F&B) |
| Variable cost per occupied day | €280.25 (18.7%) |
| — F&B COGS (30%) | €157.50 |
| — OTA commissions (60% at 15%) | €87.75 |
| — Amenities and guest supplies | €35.00 |
| Unit contribution margin | €1,219.75 per occupied day (81.32%) |
| Room-night unit margin | €107.97 per room-night (79.98%) |
| Fixed annual overhead | €72,234 (payroll €60,075 + opex €12,159) |
| Senior debt service | €43,536.35 (15-year French amortization at 3.5%) |
| Total annual fixed burden | €115,770.35 |

**Break-even thresholds:**

| Threshold | Occupied days | Occupancy |
|---|---:|---:|
| Operating break-even (EBITDA = 0) | 59.2 | 16.22% |
| Cash debt-service break-even (DSCR = 1.00x) | 94.9 | 26.00% |
| Bank covenant floor (DSCR ≥ 1.25x) | 103.8 | 28.44% |

This is the cleanest way to see the problem: the promoter's 19.2% is above operating break-even but **below** the 26.00% cash debt-service break-even, so the original case cannot service its debt from operations. The management case's 31.36% is above the 28.44% covenant floor, but only by about 2.9 percentage points. The annual three-statement model passes Year 1 at 28.23% because it uses a simplified cost stack; the 28.44% threshold is the stricter unit-economics view, and it is the one a credit committee should use.

---

## 7. Payroll: part-time, not 3 FTE

The original Word report documents part-time contracts: about 1,900 hours across two cooks and 1,792 hours for cleaning. The refined model therefore uses:

| Role | Annual hours | FTE | Hourly gross | 2026 SMI | Segovia convenio floor | Compliant? |
|---|---:|---:|---:|---:|---:|---|
| Cook 1 | 950 | 0.54 | €14.21 | €9.69 | €10.12 | Yes |
| Cook 2 | 950 | 0.54 | €14.21 | €9.69 | €10.12 | Yes |
| Cleaning / auxiliary | 1,792 | 1.01 | €9.77 | €9.69 | €9.02 | Yes |
| **Total** | **3,692** | **2.09** | — | — | — | — |

The 2026 SMI is €17,094 gross per year (14 payments of €1,221, Real Decreto 126/2026). The Segovia hospitality convenio (2026) sets a cook's reference at €17,844.16 and an auxiliary's at €15,916.22; divided by the relevant annual hours, the hourly floors are €10.12 and €9.02. The model's part-time hourly rates are above both floors.

The original Excel's €58,740 is gross payroll (€35,640 cooks + €23,100 cleaning). The refined model's €60,075 includes employer social security and the part-time hour structure. The difference is not a payroll error; it is a different cost basis. The earlier claim that the model employed "3 FTE at full-time convenio rates" was wrong and has been removed.

---

## 8. Three-statement model and promoter replication

The model produces a full P&L, cash-flow statement and balance sheet for five years. The core revenue formula for the management case is:

```
Revenue = 365 × occupancy × (7 rooms × €85 + 1 house × €380 + 21 meals × €25)
```

The market and promoter cases use the original unit economics (€85 / €380 / €20, 859 meals at 19.2%, scaled to 21.24% for the market case). Debt is a 15-year French amortization at 3.5% in the management/market cases and 4.5% / 25 years in the promoter case. Tax is 25% of positive EBT; the management case pays tax from Year 1, so there is no BIN shield.

**Promoter replication check:**

| Line | Original Excel | Python promoter case | Difference |
|---|---:|---:|---:|
| Year 1 revenue | €86,275 | €86,275.00 | €0.00 |
| Year 1 EBITDA | €11,297 | €11,297.00 | €0.00 |
| Year 1 ending cash | ≈ −€2,560 | −€2,553.20 | ≈ €7 |
| Balance sheet discrepancy | n/a | €0.00 | — |

The balance-sheet identity (Assets = Liabilities + Equity) holds to €0.00 in all three cases and all five years. This is checked in the test suite and in the Excel `Live Model`.

---

## 9. Funding: sources & uses, gap and credit line

| Case | Uses at close | Sources at close | Gap at close | Adjusted cash Y1 | DSCR Y1 | Credit line drawn | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Management | €948,858 | €878,090 | **−€70,768** | **−€55,978** | 1.34x | €143,596 | Underfunded |
| Market | €948,858 | €878,090 | **−€70,768** | **−€96,684** | 0.40x | €147,285 | Underfunded |
| Promoter | €939,175 | €897,250 | **−€41,925** | **−€64,478** | 0.33x | €166,752 | Underfunded |

**Close-day uses (management):**

| Use | Amount |
|---|---:|
| CapEx (net of VAT) | €729,000.00 |
| Input VAT (21%) | €153,090.00 |
| Pre-opening costs | €25,000.00 |
| Initial working capital | €20,000.00 |
| DSRA (6 months of debt service) | €21,768.18 |
| **Total uses** | **€948,858.18** |

**Close-day sources:**

| Source | Amount |
|---|---:|
| Senior debt (70%) | €507,500.00 |
| Sponsor equity (30%) | €217,500.00 |
| VAT refund bridge | €153,090.00 |
| Credit line at close | €0.00 |
| **Total sources** | **€878,090.00** |
| LEADER grant (Month 14, post-close) | €163,000.00 |
| **Total including grant** | **€1,041,090.00** |

The grant is real, but it is **post-close**. The close-day gap is €70,768.18; the recommended equity injection is the same amount. If the grant is included, the project has a positive total funding position (€92,231.82), but it is illiquid at close.

**Credit-line inconsistency.** The annual model draws a €143,596 VAT bridge in the management case. The stated revolving line is €50,000. The bridge is a separate facility with 5.5% interest, not the operating line. The model must either disclose it as a separate facility or increase the line to at least €150,000. The audit flags this as a material exception.

**DSRA.** The funding engine uses six months of debt service (€21,768.18). The credit committee's CVaR 99% analysis recommends €47,596.85. If the larger DSRA is used, the close-day gap widens by €25,828.67, to about €96,597. This is a term-sheet item, not a modelling rounding error.

---

## 10. Returns: the exit is doing the work

| Case | Project IRR (no exit) | Project IRR (8.5% exit) | Equity IRR (8.5% exit) | Terminal value | Project MOIC | Equity MOIC |
|---|---:|---:|---:|---:|---:|---:|
| Management | −20.89% | 15.43% | 29.74% | €1,048,704 | 1.90x | 3.73x |
| Market | −27.31% | 9.63% | 17.43% | €898,396 | 1.54x | 2.52x |
| Promoter | −29.48% | 6.84% | 10.95% | €796,462 | 1.36x | 1.82x |

The terminal value is Year 5 EBITDA capitalised at an 8.5% cap rate. Without an exit, the five-year operating cash flow does not recover the €729,000 CapEx in any case. The management project IRR of 15.43% is below a typical 18–20% private-equity hurdle; the 29.74% equity IRR is levered and exit-dependent. The market and promoter cases are below a reasonable equity hurdle even with the exit.

This is a deliberate contrast with the old README, which reported an 18.4% mean sponsor IRR from a Monte Carlo that did not model the exit or the funding gap. The current returns are computed from the cash-flow series, with a Newton/bisection IRR solver and explicit terminal value.

---

## 11. Scenario stress-testing

| Metric | Conservative Y1 | Conservative Y3 | Base Y1 | Base Y3 | Optimistic Y1 | Optimistic Y3 |
|---|---:|---:|---:|---:|---:|---:|
| Revenue | €124,798 | €145,597 | €154,548 | €180,306 | €204,003 | €238,004 |
| EBITDA | €32,236 | €50,852 | €66,086 | €89,140 | €111,794 | €142,224 |
| Net income | −€10,309 | €10,753 | €23,281 | €41,993 | €59,431 | €83,513 |
| Ending cash | −€19,923 | €134,218 | €10,790 | €225,556 | €45,927 | €340,430 |
| DSCR | 0.67x | 1.06x | 1.34x | 1.73x | 2.19x | 2.72x |
| ICR | 1.30x | 2.27x | 3.81x | 5.77x | 7.53x | 10.80x |

The conservative case breaches the covenant in Year 1 (0.67x) and ends with negative cash. The base case is the management upside. The optimistic case is a sensitivity, not a forecast.

---

## 12. Monte Carlo and copula tail risk

**Naive Gaussian Monte Carlo (N = 1,000):**

| Metric | Value |
|---|---:|
| Mean Year 1 DSCR | 1.36x |
| Median Year 1 DSCR | 1.34x |
| VaR 95% (5th percentile) | 0.88x |
| P(covenant breach, DSCR < 1.25x) | 35.4% |
| P(insolvency, DSCR < 1.00x) | 9.6% |

**Multivariate copula (50,000 draws):**

| Model | Mean DSCR | Median DSCR | VaR 95% | VaR 99% | CVaR 99% | P(DSCR < 1.25x) | P(DSCR < 1.00x) | CVaR 99% deficit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gaussian | 1.36x | 1.34x | 0.64x | 0.37x | 0.26x | 42.31% | 21.61% | €33,906 |
| Student-t (ν = 4) | 1.36x | 1.34x | 0.64x | 0.35x | 0.21x | 42.11% | 21.23% | €36,735 |
| Clayton (θ = 1.8) | 1.36x | 1.38x | 0.49x | 0.17x | 0.04x | 40.35% | 23.23% | €47,597 |

The Clayton copula captures asymmetric lower-tail dependence: in a bad year, occupancy, ADR and restaurant spend deteriorate together. The credit committee's recommended DSRA is €47,596.85, which covers the Clayton CVaR 99% shortfall. The naive Gaussian Monte Carlo is kept as a benchmark, not as the risk model.

---

## 13. Phase II: landscape suites and biological pond

Phase II adds two 55 m² landscape suites and a 200 m³ biological pond. The all-in CapEx is €359,970 net, plus €75,593.70 of input VAT, for a cash need of €435,563.70.

| CapEx component | Amount |
|---|---:|
| Construction execution (PEM) | €260,000.00 |
| Execution including fees and taxes (PEC) | €309,400.00 |
| Engineering and architecture fees | €23,400.00 |
| Municipal taxes (ICIO) | €11,700.00 |
| Contingency reserve | €15,470.00 |
| **Total all-in CapEx (net)** | **€359,970.00** |
| Input VAT (21%) | €75,593.70 |
| **Cash need** | **€435,563.70** |

**Operating scenarios (Year 3 stabilized):**

| Scenario | Occupancy | ADR | Incremental EBITDA | 8.5% exit IRR |
|---|---:|---:|---:|---:|
| Base (no incremental FTE) | 50.0% | €290 | €99,620.52 | 40.29% |
| Realistic (1 FTE) | 45.0% | €270 | €51,435.20 | 19.64% |
| Stress (1 FTE) | 36.4% | €250 | €25,185.88 | 2.07% |
| Conservative | 40.0% | €250 | €31,870.20 | 7.50% |
| Optimistic | 58.0% | €330 | €142,432.65 | 53.34% |

The base case is deliberately aggressive: 50% occupancy is more than double the INE provincial average, and it assumes no incremental FTE. The realistic case (45% occupancy, one extra FTE) is the better underwriting anchor. The stress case is barely positive.

**Phase gate:**

| Test | Value |
|---|---:|
| Phase I DSCR Year 3 | 1.73x (floor 1.25x) → pass |
| Phase I cash at end of Year 2 | €193,949.95 |
| Phase II cash need | €435,563.70 |
| Phase II funding gap | **−€241,613.75** |
| Gate recommendation | **DO NOT PROCEED** — additional funding or smaller scope required |

The old README claimed Phase II was 100% self-funded from €421,784 of gross treasury. That figure included the LEADER grant and the VAT refund, both of which are already committed to Phase I. The correct treatment is a phase gate: Phase II can proceed only if Phase I covenants are met and Phase I cash covers the Phase II need. It does not.

If Phase II were funded, consolidated Year 3 revenue would be €326,488.50 and EBITDA €188,760.39, with DSCR expanding from 1.73x to 4.34x (assuming no new senior debt). That is a real upside, but it is conditional on funding, not automatic.

---

## 14. Computed audit: 14 rules, 8 pass, 5 material, 1 warning

The audit is computed from the model, not hand-written. It is allowed to fail.

| Rule | Severity | Status | Actual | Threshold |
|---|---|---|---:|---:|
| RULE_01_BALANCE_SHEET_EQUALITY | Material | **PASS** | €0.00 | ≤ €0.01 |
| RULE_02_HOSPITALITY_VAT_RATE | Material | **PASS** | 10.0% | 10.0% |
| RULE_03_CAPEX_INPUT_VAT | Material | **PASS** | €153,090 | €153,090 |
| RULE_04_PAYROLL_HOURLY_COMPLIANCE | Material | **PASS** | €9.77 min | ≥ €9.02 |
| RULE_05_MANAGEMENT_DSCR | Material | **PASS** | 1.34x | ≥ 1.25x |
| RULE_06_ADJUSTED_CASH_TROUGH | Material | **FAIL** | −€55,978.44 | ≥ €0 |
| RULE_07_DSRA_SIZING | Warning | **PASS** | €21,768.18 | ≥ 6 months |
| RULE_08_SOURCES_USES_CLOSE | Material | **FAIL** | −€70,768.18 | ≥ €0 |
| RULE_09_CREDIT_LINE_LIMIT | Material | **FAIL** | €143,596.37 | ≤ €50,000 |
| RULE_10_OCCUPANCY_VS_INE | Warning | **FAIL** | 1.48x | ≤ 1.25x |
| RULE_11_PHASE2_SELF_FUNDING | Material | **FAIL** | −€241,613.75 | ≥ €0 |
| RULE_12_RETURNS_VS_WACC | Material | **PASS** | 15.43% | ≥ 8.0% |
| RULE_13_PROMOTER_REPLICATION | Info | **PASS** | €86,275 / €11,297 | exact |
| RULE_14_MARKET_DSCR | Material | **FAIL** | 0.40x | ≥ 1.25x |

**Verdict:** `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`.

The five material exceptions are the funding gap, the adjusted cash trough, the credit-line inconsistency, the Phase II double-spend and the market DSCR. The warning is the management occupancy assumption (1.48x the INE average). The audit JSON is exported to `data/model_audit_summary.json` and the same rules are reproduced in the Excel `Funding & Audit` tab.

---

## 15. The Excel model

The workbook has **12 tabs** and **172 formulas**:

| Tab | Purpose |
|---|---|
| `Read Me & Checks` | Model map, three cases, integrity checks and headline findings. |
| `Inputs` | Every hard-coded assumption in one place (blue cells). |
| `Live Model` | Formula-driven 5-year P&L, cash flow, debt and balance sheet; replicates the management case. |
| `Funding & Audit` | Sources & uses, funding gap, credit-line consistency, Phase II gate and the computed audit rules. |
| `Executive Scorecard` | One-page underwriting scorecard. |
| `3-Statement Model` | Full Python output: P&L, cash flow and balance sheet. |
| `Debt Schedule` | 15-year French amortization. |
| `Scenario Stress-Testing` | Conservative / base / optimistic and the 2D DSCR sensitivity. |
| `Monte Carlo Risk` | 1,000-iteration stochastic credit-risk simulation. |
| `Credit Risk & Copula` | Gaussian / Student-t / Clayton tail-risk comparison. |
| `Unit Economics & Runway` | RevPAR, TRevPAR, contribution margin and the monthly liquidity stress. |
| `Phase II Expansion` | Landscape suites and biological pond: CapEx, P&L, scenarios, phase gate and consolidated impact. |

The `Live Model` is intentionally simple and transparent: revenue is a formula linked to `Inputs`, debt comes from `Debt Schedule`, and the checks compare the live output with Python. The 172 formulas are:

- 161 in `Live Model`;
- 8 in `Read Me & Checks`;
- 3 in `Funding & Audit`.

The report tabs are Python snapshots and do not recalculate. The workbook has no calculation engine of its own; open it in Excel or LibreOffice to recalculate. The formulas have been validated by a Python replication: revenue, EBITDA, DSCR and ending cash match the annual model to the cent, and the balance-sheet check is within €1 (rounding).

The `Funding & Audit` tab is allowed to show `FAIL`. That is the audit working as intended.

---

## 16. Repository architecture

```
proyecto-dehesa-del-castrillo/
├── main.py                       # 14-step pipeline
├── README.md / README_ES.md
├── requirements.txt
├── src/
│   ├── config/
│   │   ├── assumptions.py        # CapEx, payroll, debt, opex, cases, funding fields
│   │   └── ine_weights.py        # INE Segovia monthly series (21.24% calibrated)
│   ├── core/
│   │   ├── statements.py         # 3-statement engine, three cases, promoter replication
│   │   ├── debt.py               # French amortization
│   │   ├── tax.py                # VAT and corporate tax
│   │   ├── metrics.py            # DSCR, ICR, IRR (Newton + bisection), exit returns
│   │   ├── funding.py            # Sources & uses, gap, credit line, phase gate
│   │   ├── unit_economics.py     # USALI unit economics and break-evens
│   │   ├── monthly_cash.py       # Monthly liquidity stress (unfunded/funded)
│   │   ├── expansion.py          # Phase II CapEx, scenarios, phase gate
│   │   ├── credit_committee.py   # DSRA and underwriting memo
│   │   └── model_audit.py        # Computed audit, 14 rules, JSON export
│   ├── data/
│   │   ├── extract_raw.py        # Reconciliation with the original Excel
│   │   ├── export_excel.py       # 12-tab workbook
│   │   └── live_excel.py         # Formula-driven live tabs
│   ├── scenarios/
│   │   └── scenario_analysis.py  # Conservative / base / optimistic
│   ├── simulation/
│   │   ├── monte_carlo.py        # Naive Gaussian Monte Carlo
│   │   └── copula_engine.py      # Gaussian / Student-t / Clayton
│   └── visualization/
│       └── charts.py             # Institutional figures
├── tests/
│   ├── test_assumptions.py
│   ├── test_cases.py             # Three-case and returns tests
│   ├── test_funding.py           # Sources & uses, gap, phase gate
│   ├── test_model_audit.py       # Computed audit: 8/14, 5 material, 1 warning
│   ├── test_expansion.py         # Phase II scenarios and phase gate
│   ├── test_financial_engine.py
│   ├── test_unit_economics_monthly.py
│   ├── test_simulation.py
│   └── test_copula.py
├── data/
│   ├── La_Dehesa_del_Castrillo_Financial_Model.xlsx
│   └── model_audit_summary.json
└── assets/
    └── figure_*.png
```

---

## 17. Installation and execution

```bash
git clone https://github.com/magnumjpg/la-dehesa-financial-due-diligence.git
cd la-dehesa-financial-due-diligence
pip install -r requirements.txt

# Full pipeline (14 steps, charts, Excel, audit JSON)
python main.py

# Skip chart generation
python main.py --no-charts

# Test suite (41 tests)
python -m pytest tests/ -q
```

**Outputs:**

- `data/La_Dehesa_del_Castrillo_Financial_Model.xlsx` — 12 tabs, 172 formulas.
- `data/model_audit_summary.json` — computed audit, schema 3.0.0.
- `assets/figure_*.png` — institutional charts.

The pipeline is deterministic by default; the Monte Carlo and copula simulations use a fixed seed (42).

---

## 18. Limitations and next steps

This is a portfolio model, not an investment memorandum. The main limitations are explicit:

1. **The management case is an upside.** 31.36% occupancy is 1.48x the INE provincial average. It should be presented as a management case, not a base case.
2. **The monthly engine is a standalone liquidity stress.** It uses seasonal ADR and includes OTA commissions and amenities; the annual model uses flat ADR and a simpler cost stack. It is not a line-by-line reconciliation of the annual three-statement model.
3. **The Monte Carlo is a naive Gaussian.** The copula engine is the better tail-risk tool; the Gaussian simulation is kept as a benchmark.
4. **The DSRA is inconsistent.** The funding engine uses six months (€21,768); the credit committee recommends €47,597 based on CVaR 99%. The term sheet should use the larger figure, which widens the close gap to about €96,597.
5. **The Phase II CapEx is a pre-tender estimate.** There are no binding construction quotes; the contingency is 5% of PEC.
6. **The tax model is simplified.** It uses a 25% corporate tax rate, no VAT group, no regional deductions and no BIN schedule beyond the current year.
7. **The payroll model is part-time.** The hourly rates are compliant, but scheduling, coverage and turnover risk remain.
8. **The grant is assumed committed.** There is no award letter in the repository; the LEADER timing is modelled at Month 14.
9. **The original raw Excel files are not redistributed.** The promoter case is hard-coded from the audited values and replicated in `statements.py`.
10. **The annual P&L still uses a simplified cost stack.** It includes restaurant COGS (30%) but not the OTA commissions (9% of lodging), amenities (€35/day) or breakfast cost that the unit-economics engine includes. Adding them would reduce management EBITDA by about €23.5k (to ~€42.6k) and push the DSCR below 1.25x. This is the top priority for the next iteration.
11. **OPEX is low for the asset.** The €12,159 fixed opex is thin for a 550 m² hotel with a restaurant and a biopool; a realistic range is €30–40k. The audit's EBITDA bridge shows the effect.
12. **No FF&E reserve, construction period, IDC or grace period.** The refurbishment is assumed to open immediately after close, and the renovation CapEx of €440k (€800/m²) is below the market range of €1,200–1,800/m². Both are material.
13. **The restaurant demand is guests-only.** The model assumes 21 covers/day from hotel guests, with no external covers, events or beverage revenue. The restaurant is 35% of revenue and is not independently underwritten.

**Next steps I would take in a real mandate:**

- Replace the flat ADR with a booking-curve model and a proper competitive set.
- Integrate the monthly engine into the three-statement model with a cash waterfall.
- Model the DSRA, the VAT bridge and the credit line as separate facilities with covenants.
- Run a debt-sizing optimisation and a distribution lock-up test.
- Commission binding construction quotes and a QS report for Phase II.
- Stress the payroll under a full-time staffing scenario and a 10% wage inflation scenario.

---

## 19. References

- **INE**, *Encuesta de Ocupación en Alojamientos de Turismo Rural* (EOTR), table 2070, Segovia, 2023–2025.
- **Ley 37/1992**, *Impuesto sobre el Valor Añadido*, Art. 91.Uno.2.2ª (10% hospitality rate) and Art. 92–114 (deductible input VAT).
- **Ley 27/2014**, *Impuesto sobre Sociedades*, 25% corporate tax rate.
- **Convenio Colectivo Provincial de Hostelería de Segovia** (2026), salary tables for cooks, waiters and auxiliary staff.
- **Real Decreto 126/2026**, 2026 SMI (€17,094 gross/year, 14 payments of €1,221).
- **LEADER / Diputación de Segovia**, rural development grant framework (€163,000 assumed commitment).
- **USALI** (Uniform System of Accounts for the Lodging Industry), 11th edition, for the unit-economics structure.
- **Benchmark set:** Vivood Landscape Hotel (Alicante), Miluna Open Nature Rooms (Toledo), Basoa Suites (Navarra), Cabañitas del Bosque (A Coruña).

---

### A note on authorship and purpose

The original Excel and Word files are my own university work. The Python layer was added to demonstrate AI-assisted financial modelling, not to claim authorship of the original study. The model's value is not that it makes the project look better; it is that it makes the project's weaknesses visible, quantified and testable. The audit's `CONDITIONAL` verdict is the honest output.
