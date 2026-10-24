# La Dehesa del Castrillo S.L.

### Hospitality Feasibility, Senior Debt Underwriting & Computed Due Diligence

**A portfolio-grade financial model built from my own university feasibility study.**
Python 3.11 · 42 automated tests · 16-rule computed audit · 12-tab Excel model · 14-step pipeline

[![tests](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml/badge.svg)](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

> **Read this first.** The realistic model reaches a harsher conclusion than the original university work. Once the full cost stack, construction interest, debt amortisation, OPEX, FF&E reserve and the equity plug are modelled, the management case fails the 1.25x DSCR covenant in Year 2 at **1.15x**, requires **49.6% cash equity** instead of the 30% assumed, and produces a project IRR of **-9.49%** even with an 8.5% exit. The audit is deliberately allowed to fail: **10 of 16 rules pass, 5 material exceptions and 1 warning remain open**, and the verdict is `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`. The credit committee recommendation is **DECLINE AS STRUCTURED (RESIZE REQUIRED)**.

---

## 1. What this project is

I started with my own university feasibility study for a 25-hectare rural estate in Segovia (7 double rooms, one full country house, a 21-seat restaurant and a natural swimming biopool). The original Excel is a single-sheet promoter simulator with live formulas; it uses 19.2% occupancy. The Word report documents a more conservative 16.5-17% occupancy, part-time contracts and a LEADER grant application. That gap between the Word and the Excel is the first thing the audit had to reconcile.

I then rebuilt the analysis in Python to answer the questions the original work could not answer:

- What happens at the **official INE occupancy** instead of the promoter's assumption?
- What is the **real all-in cost** of a 550 m² refurbishment, kitchen, FF&E, biopool and digital infrastructure?
- Does the project **fund itself at close** once construction interest, pre-opening costs, working capital and a debt-service reserve are included?
- How much **equity** is actually required, and is it the 30% in the business plan?
- Does the project **service its debt** under a 20-year amortising facility, and in which year does the covenant break?
- Is the **VAT bridge** creating cash or just moving it?
- Can **Phase II** really be self-funded from Phase I cash, or is it a double-spend of the grant and the VAT refund?
- What do the **returns** look like with and without an exit?

The Python layer is not a cosmetic rewrite. It adds a three-case architecture, a sources-and-uses engine, a computed audit, a live formula-driven Excel workbook, and a test suite that locks in the honest numbers.

---

## 2. Three cases, side by side

| Case | Occupancy (Year 1 → mature) | Revenue Y1 | EBITDA Y1 | CFADS Y1 | DSCR Y1 | DSCR min | Cash Y1 | Project IRR (8.5% exit) | Equity IRR (8.5% exit) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Management (upside)** | 28.23% → 31.36% | €154,548 | €24,280 | €19,643 | 1.34x | **1.15x** | €20,701 | -9.49% | -23.16% |
| **INE market** | 21.24% → 32.00% | €95,555 | -€18,566 | -€21,432 | -1.46x | **-1.46x** | €15,000 | -15.18% | -50.22% |
| **Promoter (original Excel)** | 19.20% → 28.92% | €86,275 | €11,297 | €11,297 | 0.33x | **0.33x** | -€8,039 | 6.84% | 12.12% |

**What each case is:**

- **Promoter**: a faithful replication of the original university Excel: 19.2% occupancy in Year 1 (491 room-nights + 72 house-nights), €85 room ADR, €380 house ADR, €20 restaurant ticket, 859 meals, 4.5% / 25-year debt, no grace, no grant and land purchased rather than contributed in kind. The Python model reproduces the original revenue and EBITDA to the euro. This is the case the author actually underwrote, and it is the only case with a positive equity IRR on exit, but it is cash-negative in Years 1-2.
- **INE market**: the independent demand anchor: 21.24% official Segovia room occupancy in 2025 (INE EOTR table 2070) in Year 1, with the original unit economics and the original 25%/20% volume ramp, which reaches 32.0% by Year 3 and then grows 5% per year. The F&B attachment stays at the original 950 meals at €20. It is the closest thing to a "market" case in the workbook.
- **Management (upside)**: 31.36% mature occupancy (1.48x the INE average), one on-site meal per guest per day at a €25 ticket, the full variable-cost stack and a 5.5% VAT bridge. It is an operating upside, not a base case. Its "upside" is revenue per occupied day (F&B attachment), not occupancy: the market case actually reaches a similar mature occupancy through the original ramp.

The three cases share the same CapEx (except the promoter's original €725k base), tax rate and balance-sheet mechanics. The difference is demand, unit economics and financing, which is exactly where the risk sits.

---

## 3. The findings that matter

1. **The real cost stack is €1,050,100, not €725,000.** Land €250,000, 550 m² of structural works at €1,000/m² (€550,000), commercial kitchen €55,000, FF&E €65,000, biopool and landscaping €40,000, digital €12,000, professional fees €42,600 and a 5% contingency €35,500. The original budget omitted the kitchen, FF&E, fees and contingency, and covered only €475,000 of the €800,100 non-land budget.
2. **The equity requirement is 49.6% of CapEx, not 30%.** Sources and uses only close with a cash-equity plug of **€521,090.22**, plus the €250,000 land contributed in kind. Total equity at close is **€771,090.22**.
3. **The covenant fails in Year 2, not Year 1.** Year 1 is interest-only (DSCR 1.34x). The first amortising year produces €27,647.64 of debt service against €31,889.98 of CFADS: **1.15x versus a 1.25x covenant**. It never recovers within five years.
4. **The management case sits 0.69 percentage points below its own covenant break-even.** The 1.25x break-even is **32.05%** mature occupancy; the plan assumes **31.36%**. The operating break-even is 22.26%, but the debt-service break-even is already 30.28%.
5. **The market case never clears 1.00x within five years.** At the official INE occupancy and the original unit economics, Year 1 EBITDA is **-€18,566**, DSCR is **-1.46x**, and the best year reaches only **0.86x**. It is funded only because the equity plug absorbs a €35,375 operating buffer.
6. **Returns are negative in both realistic cases, even with an exit.** Project IRR with an 8.5% cap-rate exit is **-9.49%** (management) and **-15.18%** (market). The promoter case clears the exit at 6.84% project / 12.12% equity, but only after two cash-negative years and with a €20,000 liquidity gap at close.
7. **The €70.8k "funding gap" of the old README is gone, and that is not good news.** It was replaced by a €521k equity plug. Sources equal uses at close by construction, but the sponsor has to fund 49.6% of CapEx in cash. The promoter case keeps its original €20,000 line and its liquidity gap.
8. **The VAT bridge is a financing source, not value creation.** Input VAT on CapEx is €168,021 (21% on the €800,100 non-land base). It is drawn under a separate €175,000 bridge, repaid with the AEAT refund in Month 18, and it carries interest. Operational VAT is a pass-through.
9. **Phase II is not self-funded.** Phase II needs €435,564 (€359,970 net CapEx + €75,593.70 VAT). Phase I cash at the end of Year 2 is €183,322.64, so the phase-gate gap is **-€252,241.06** and the gate returns `DO NOT PROCEED`. It also fails the DSCR condition (1.15x < 1.25x).
10. **The audit is computed and it fails.** 10 of 16 rules pass. The five material exceptions are management DSCR, Phase II self-funding, returns versus WACC, market DSCR and the equity requirement. The warning is management occupancy versus INE. This is the point of the audit layer: it reports what the model actually does, not what the narrative wants.

---

## 4. Cost stack and depreciation

| CapEx item | Amount | Depreciation (Ley 27/2014) |
|---|---:|---:|
| Land (25 ha, contributed in kind) | €250,000 | Not depreciable |
| Structural works (550 m² × €1,000/m²) | €550,000 | 3% = €16,500 |
| Commercial kitchen | €55,000 | 12% = €6,600 |
| FF&E | €65,000 | 10% = €6,500 |
| Biopool and landscaping | €40,000 | 10% = €4,000 |
| Digital infrastructure | €12,000 | 25% = €3,000 |
| Professional fees (6% of works) | €42,600 | 3% = €1,278 |
| Contingency (5%) | €35,500 | 3% = €1,065 |
| **All-in CapEx** | **€1,050,100** | **€38,943/year** |

Pre-opening costs of €35,000 are capitalised and amortised over five years (€7,000/year), so total D&A is **€45,943/year**. Input VAT is **€168,021** (21% on the €800,100 non-land base). The promoter case keeps the original €725,000 base, €99,750 of input VAT and no pre-opening capitalisation, so the replication test remains exact.

The digital line is €12,000 rather than €4,000: a 550 m² property with 8 keys, a restaurant and a biopool needs property-management, POS, Wi-Fi, access control and CCTV, not a single Kit Digital grant.

---

## 5. Funding: sources and uses, equity plug and debt sizing

### Close-day uses and sources (management case)

| Uses at close | Amount |
|---|---:|
| Land contributed in kind | €250,000.00 |
| Cash CapEx (net of VAT) | €800,100.00 |
| Interest during construction (12 months) | €14,701.40 |
| Input VAT (21% on non-land CapEx) | €168,021.00 |
| Pre-opening costs | €35,000.00 |
| Initial working capital | €25,000.00 |
| DSRA (6 months of Year-2 service) | €13,823.82 |
| **Total uses** | **€1,306,646.22** |

| Sources at close | Amount |
|---|---:|
| Senior debt (35% LTV) | €367,535.00 |
| VAT bridge | €168,021.00 |
| Cash equity (plug) | €521,090.22 |
| Land contributed in kind | €250,000.00 |
| **Total sources** | **€1,306,646.22** |
| Funding gap at close | **€0.00** |
| LEADER grant (Month 14, post-close) | €163,000.00 |

The cash equity is a **plug**, calculated so that sources equal uses. It is not an assumption. In the market case the plug is €556,465.05 because it also absorbs a €35,374.83 operating buffer; total equity rises to €806,465.05. The promoter case keeps 30% equity (€217,500), the original €20,000 line and a €20,000 close-day gap.

### Debt sizing: the DSCR is the binding constraint

| Test | Result |
|---|---:|
| Requested facility | €367,535.00 (35.0% LTV) |
| DSCR cap at 1.25x on minimum CFADS | **€339,144.92** (32.3% LTV) |
| Excess over the cap | €28,390.08 |
| Implied maximum annual service at the cap | €25,511.98 |
| Binding constraint | **DSCR** |
| Year-2 DSCR at the requested facility | **1.15x** |
| Year-2 DSCR at the DSCR cap | 1.25x |

The 35% LTV facility complies with the loan-to-value limit but fails the covenant. In the market case, Year-1 CFADS is negative, so the DSCR cap is €0 and the sizing engine returns `NONE (negative CFADS)`: no amount of senior debt can satisfy a 1.25x test.

The debt is a 20-year French amortisation at 4.0% fixed, with 12 months of construction (interest capitalised as IDC) and a 12-month interest-only grace. The annuity is computed over the remaining 228 months: **€2,303.97 per month**, or **€27,647.64 per year** from Year 2. Year 1 pays only interest (€14,701.44). The loan fully amortises in Month 240.

### DSRA and monthly liquidity

The contractual DSRA is six months of the maximum annual service: **€13,823.82**. The copula's Clayton CVaR 99% shortfall is **€62,786.01**, so the tail-tested reserve would be 2.27 years of debt service. That is not a rounding difference: it is a further sign that the facility is over-levered.

The monthly engine (24 months, seasonal revenue, monthly debt service, revolver) finds the trough in **April (Month 4)**: cash falls to **€12,004.01** before a **€2,995.99** draw on the €175,000 revolver, repaid by Month 7. Year 1 closes at **€20,700.88** and Year 2 at **€183,322.64**. The €15,000 minimum balance is never breached, and the monthly-to-annual reconciliation difference is **€0.00**. The LEADER grant arrives in Month 14 (€163,000) and the AEAT VAT refund in Month 18 (€168,021), which repays the bridge.

---

## 6. Demand calibration: INE, promoter and management

The INE *Encuesta de Ocupación en Alojamientos de Turismo Rural* (EOTR), table 2070 for Segovia, reports:

| Period | Room occupancy |
|---|---:|
| 2023 | 21.32% |
| 2024 | 21.50% |
| 2025 | **21.24%** (77.5 occupied days) |
| August 2025 | 36.78% |
| January 2025 | 9.58% |

The monthly series is calibrated to the 2025 annual average of 21.24%, preserving the January and August anchors. Figure 1 compares the INE curve with the management target. The management case runs Year 1 at 0.90x the mature curve (28.23% weighted average) and reaches 31.36% from Year 2; it assumes no nominal ADR growth after stabilisation. The market and promoter cases keep the original 25%/20% volume ramp and 5% annual growth from Year 4.

The gap between 19.2%, 21.24% and 31.36% is the commercial risk the model is underwriting. The management case is 1.48x the provincial average, and the audit flags it as a warning.

---

## 7. Unit economics and break-evens

| Metric | Value |
|---|---:|
| Capacity | 8 keys (7 double rooms + 1 country house) = 2,920 key-nights/year |
| Daily gross revenue at 100% occupancy | €1,500 (€975 lodging + €525 F&B) |
| Variable cost per occupied day | €385.25 (25.68%) |
| - F&B COGS (30%) | €157.50 |
| - OTA commissions (60% at 15%) | €87.75 |
| - Amenities and guest supplies | €35.00 |
| - Breakfast (21 guests at €5) | €105.00 |
| Contribution before FF&E | €1,114.75 (74.32%) |
| FF&E reserve (3% of revenue) | €45.00 |
| Cash contribution after FF&E | €1,069.75 (71.32%) |
| Fixed annual overhead | €90,575 (payroll €60,075 + OPEX €30,500) |
| Maximum annual debt service (Year 2+) | €27,647.64 |
| Total annual fixed burden | €118,222.64 |

**Break-even thresholds by case** (solved on the full model with each case's own ramp; the binding year is Year 2 for management and Year 1 for market and promoter):

| Case | Operating (EBITDA = 0) | Cash debt service (DSCR 1.00x) | Covenant (DSCR 1.25x) | ADR for 1.25x at base occupancy | ADR for 10% equity IRR |
|---|---:|---:|---:|---:|---:|
| Management | 22.26% (81.2 days) | 30.28% (110.5 days) | **32.05%** (117.0 days) | €86.64 | €116.36 |
| Market | 26.83% | 48.73% | **50.43%** | €127.25 | €128.04 |
| Promoter | 16.76% | 36.48% | **39.32%** | €115.56 | €83.60 |

The management case is above its operating and debt-service break-evens but **below its covenant break-even by 0.69 percentage points**. The market case needs roughly 50% mature occupancy to clear 1.25x, which is more than double the INE average. The promoter case clears 1.25x only from Year 3, and its minimum DSCR (Year 1) is 0.33x.

The unit-economics "days" are whole-property occupied days (one day with all 8 keys sold), which is why 22.26% occupancy equals 81.2 days.

---

## 8. Payroll: part-time, not 3 FTE

The original Word report documents part-time contracts: about 1,900 hours across two cooks and 1,792 hours for cleaning. The refined model therefore uses:

| Role | Annual hours | FTE | Hourly gross | 2026 SMI | Segovia convenio floor | Compliant? |
|---|---:|---:|---:|---:|---:|---|
| Cook 1 | 950 | 0.54 | €14.21 | €9.69 | €10.12 | Yes |
| Cook 2 | 950 | 0.54 | €14.21 | €9.69 | €10.12 | Yes |
| Cleaning / auxiliary | 1,792 | 1.01 | €9.77 | €9.69 | €9.02 | Yes |
| **Total** | **3,692** | **2.09** | - | - | - | - |

The 2026 SMI is €17,094 gross per year (14 payments of €1,221, Real Decreto 126/2026). The Segovia hospitality convenio (2026) sets a cook's reference at €17,844.16 and an auxiliary's at €15,916.22; divided by the relevant annual hours, the hourly floors are €10.12 and €9.02. The model's part-time hourly rates are above both floors, and the audit checks the minimum hourly rate (€9.77) against the €9.02 convenio floor and the €9.69 SMI.

The original Excel's €58,740 is gross payroll (€35,640 cooks + €23,100 cleaning). The refined model's €60,075 includes employer social security and the part-time hour structure. The difference is not a payroll error; it is a different cost basis.

---

## 9. Returns: the exit does not rescue the realistic cases

| Case | Project IRR (no exit) | Project IRR (8.5% exit) | Equity IRR (8.5% exit) | Terminal value | Project MOIC | Equity MOIC |
|---|---:|---:|---:|---:|---:|---:|
| Management | -35.43% | **-9.49%** | **-23.16%** | €435,783 | 0.67x | 0.38x |
| Market | -40.50% | -15.18% | -50.22% | €335,419 | 0.50x | 0.10x |
| Promoter | -29.48% | 6.84% | 12.12% | €796,462 | 1.36x | 1.81x |

The terminal value is Year 5 EBITDA capitalised at an 8.5% cap rate. Without an exit, the five-year operating cash flow does not recover the CapEx in any case. The management project NPV at an 8% WACC is **-€574,465** and the equity NPV is **-€541,676**. The promoter case is the only one with a positive exit return, and even it produces a 6.84% project IRR, below the 8% cost of capital.

The reason is structural: at €85 ADR and 31.36% occupancy the asset generates €37,042 of mature EBITDA against €45,943 of D&A and €27,648 of debt service. The business is close to cash break-even but not to an adequate return on €1.05m of CapEx.

---

## 10. Scenario stress-testing

| Metric | Conservative Y1 | Conservative Y3 | Base Y1 | Base Y3 | Optimistic Y1 | Optimistic Y3 |
|---|---:|---:|---:|---:|---:|---:|
| Revenue | €124,798 | €138,664 | €154,548 | €171,720 | €204,003 | €226,670 |
| EBITDA | -€7,500 | €2,737 | €24,280 | €37,042 | €64,576 | €81,614 |
| Net income | -€82,899 | -€62,502 | -€45,606 | -€22,826 | -€3,472 | €17,641 |
| Ending cash | €15,000 | €108,092 | €20,701 | €187,565 | €61,351 | €306,722 |
| DSCR | -0.56x | -0.05x | 1.34x | 1.15x | 4.54x | 2.60x |
| ICR | -0.37x | 0.14x | 1.65x | 2.66x | 5.02x | 6.72x |

The conservative case (85% occupancy, 95% ADR, 110% OPEX, +150 bp) breaches the covenant from Year 1 and never recovers. The base case is the management upside. The optimistic case is a sensitivity, not a forecast.

---

## 11. Monte Carlo and copula tail risk

**Naive Gaussian Monte Carlo (N = 1,000, minimum DSCR of Years 1-3):**

| Metric | Value |
|---|---:|
| Mean minimum DSCR | 1.01x |
| Median minimum DSCR | 1.08x |
| VaR 95% (5th percentile) | -0.29x |
| P(covenant breach, DSCR < 1.25x) | 60.9% |
| P(insolvency, DSCR < 1.00x) | 44.2% |
| Mean Year-1 ending cash | €19,493 |
| P5 Year-1 ending cash | -€5,335 |

**Multivariate copula (50,000 draws, Year-2 DSCR):**

| Model | Mean | Median | VaR 95% | VaR 99% | CVaR 99% | P(< 1.25x) | P(< 1.00x) | CVaR 99% deficit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gaussian | 1.20x | 1.15x | -0.12x | -0.51x | -0.67x | 54.41% | 43.32% | €48,508 |
| Student-t (ν = 4) | 1.19x | 1.15x | -0.11x | -0.54x | -0.76x | 54.59% | 43.19% | €51,350 |
| Clayton (θ = 1.8) | 1.22x | 1.23x | -0.32x | -0.78x | **-0.95x** | 50.71% | 41.07% | **€62,786** |

The credit test is run on CFADS after the FF&E reserve and cash tax, with the contractual 20-year / 4.0% debt, the 12-month grace and the full cost stack. The Clayton copula captures asymmetric lower-tail dependence: in a bad year, occupancy, ADR and restaurant spend deteriorate together. The recommended DSRA is **€62,786.01**, which covers the Clayton CVaR 99% shortfall and is 4.54x the contractual six-month reserve.

---

## 12. Phase II: landscape suites and biological pond

Phase II adds two 55 m² landscape suites and a 200 m³ biological pond. The all-in CapEx is €359,970 net, plus €75,593.70 of input VAT, for a cash need of **€435,563.70**.

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

**Operating scenarios (Year 3 stabilized, all with one incremental FTE):**

| Scenario | Occupancy | ADR | EBITDA | 8.5% exit IRR |
|---|---:|---:|---:|---:|
| Base | 35.0% | €290 | €37,414 | 11.42% |
| Realistic | 30.0% | €270 | €20,157 | -2.75% |
| Stress (official INE) | 21.24% | €240 | -€4,394 | n.m. |

Even the base case is demanding: 35% occupancy for two suites is 1.65x the INE provincial average. The realistic case destroys capital (MOIC 0.88x), and the stress case has a negative exit value. The 5-year schedule ramps at 75% / 90% / 100% and then indexes at 2%.

**Phase gate:**

| Test | Value |
|---|---:|
| Phase I DSCR Year 3 | 1.15x (floor 1.25x) -> FAIL |
| Phase I cash at end of Year 2 | €183,322.64 |
| Phase II cash need | €435,563.70 |
| Phase II funding gap | **-€252,241.06** |
| Gate recommendation | **DO NOT PROCEED** |

If Phase II were funded (which the gate says it is not), consolidated Year 3 revenue would be **€253,188**, EBITDA **€57,198**, CFADS **€49,428** and DSCR **1.79x** on the existing senior debt, with a consolidated valuation of **€672,922**. That is a real upside, but it is conditional on new funding, not automatic.

---

## 13. Computed audit: 16 rules, 10 pass, 5 material, 1 warning

The audit is computed from the model, not hand-written. It is allowed to fail.

| Rule | Severity | Status | Actual | Threshold |
|---|---|---|---:|---:|
| RULE_01_BALANCE_SHEET_EQUALITY | Material | **PASS** | €0.00 | ≤ €0.01 |
| RULE_02_HOSPITALITY_VAT_RATE | Material | **PASS** | 10.0% | 10.0% |
| RULE_03_CAPEX_INPUT_VAT | Material | **PASS** | €168,021 | €168,021 |
| RULE_04_PAYROLL_HOURLY_COMPLIANCE | Material | **PASS** | €9.77 | ≥ €9.02 |
| RULE_05_MANAGEMENT_DSCR | Material | **FAIL** | 1.15x | ≥ 1.25x |
| RULE_06_MINIMUM_CASH | Material | **PASS** | €20,701 | ≥ €0 |
| RULE_07_DSRA_SIZING | Warning | **PASS** | €13,824 | ≥ 6 months |
| RULE_08_SOURCES_USES_CLOSE | Material | **PASS** | €0.00 | ≥ €0 |
| RULE_09_VAT_BRIDGE_LIMIT | Material | **PASS** | €168,021 | ≤ €175,000 |
| RULE_10_OCCUPANCY_VS_INE | Warning | **FAIL** | 1.48x | ≤ 1.10x |
| RULE_11_PHASE2_SELF_FUNDING | Material | **FAIL** | -€252,241 | ≥ €0 |
| RULE_12_RETURNS_VS_WACC | Material | **FAIL** | -9.49% | ≥ 8.0% |
| RULE_13_PROMOTER_REPLICATION | Info | **PASS** | €86,275 / €11,297 | exact |
| RULE_14_MARKET_DSCR | Material | **FAIL** | -1.46x | ≥ 1.25x |
| RULE_15_EQUITY_REQUIREMENT | Material | **FAIL** | 49.62% | ≤ 30.0% |
| RULE_16_FFE_RESERVE | Info | **PASS** | €4,636 | 3% of revenue |

**Verdict:** `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`.

The five material exceptions are management DSCR, Phase II self-funding, returns versus WACC, market DSCR and the equity requirement. The warning is the management occupancy assumption (1.48x the INE average). The audit JSON is exported to `data/model_audit_summary.json` (schema 4.0.0) and the same rules are reproduced in the Excel `Funding & Audit` tab.

---

## 14. The Excel model

The workbook has **12 tabs** and **2,060 live formulas**:

| Tab | Purpose | Formulas |
|---|---|---:|
| `Read Me & Checks` | Model map, three cases, integrity checks and headline findings. | 12 |
| `Inputs` | Every hard-coded assumption in one place (blue cells). | 0 |
| `Live Model` | Formula-driven 5-year P&L, cash flow, debt and balance sheet; replicates the management case. | 316 |
| `Funding & Audit` | Sources & uses, funding gap, credit-line consistency, Phase II gate and the computed audit rules. | 9 |
| `Executive Scorecard` | One-page underwriting scorecard with CFADS, FF&E and returns. | 0 |
| `3-Statement Model` | Full Python output: P&L, cash flow and balance sheet. | 0 |
| `Debt Schedule` | Monthly French amortisation for 240 months plus the annual SUMIF summary. | 1,723 |
| `Scenario Stress-Testing` | Conservative / base / optimistic and the 2D Year-2 DSCR sensitivity. | 0 |
| `Monte Carlo Risk` | 1,000-iteration stochastic credit-risk simulation. | 0 |
| `Credit Risk & Copula` | Gaussian / Student-t / Clayton tail-risk comparison and DSRA sizing. | 0 |
| `Unit Economics & Runway` | RevPAR, TRevPAR, contribution margin and the monthly liquidity stress. | 0 |
| `Phase II Expansion` | Landscape suites and biological pond: CapEx, P&L, scenarios, phase gate and consolidated impact. | 0 |

The `Live Model` is intentionally simple and transparent: revenue is a formula linked to `Inputs`, debt comes from `Debt Schedule`, and the checks compare the live output with Python. The debt tab reproduces the monthly `ROUND` of the Python engine, so the Year-2 service is €27,647.64 and the loan closes at zero in Month 240.

The formulas have been validated with an independent Python calculation engine: revenue €154,548, EBITDA €24,280, Year-2 DSCR 1.1534x, Year-1 cash €20,700.89, Year-2 cash €183,322.65 and balance-sheet discrepancy €0.00 all match within the €1 / 0.01x checks. The `Read Me & Checks` tab correctly shows the covenant check as `FAIL`; the `Funding & Audit` tab is allowed to show `FAIL`. That is the audit working as intended.

The report tabs are Python snapshots and do not recalculate. Open the workbook in Excel or LibreOffice to see the live formulas evaluate.

---

## 15. Repository architecture

```
proyecto-dehesa-del-castrillo/
├── main.py                       # 14-step pipeline
├── README.md / README_ES.md
├── requirements.txt
├── .github/workflows/tests.yml   # CI: test suite + pipeline
├── src/
│   ├── config/
│   │   ├── assumptions.py        # CapEx, payroll, debt, opex, cases, funding fields
│   │   └── ine_weights.py        # INE Segovia monthly series (21.24% calibrated)
│   ├── core/
│   │   ├── statements.py         # 3-statement engine, three cases, equity plug
│   │   ├── debt.py               # French amortisation with grace and IDC
│   │   ├── tax.py                # VAT and corporate tax with BIN carryforward
│   │   ├── metrics.py            # DSCR, ICR, IRR (Newton + bisection), exit returns
│   │   ├── funding.py            # Sources & uses, debt sizing, phase gate
│   │   ├── unit_economics.py     # USALI unit economics and break-evens
│   │   ├── monthly_cash.py       # Monthly liquidity stress and revolver
│   │   ├── expansion.py          # Phase II CapEx, scenarios, phase gate
│   │   ├── credit_committee.py   # DSRA and underwriting memo
│   │   └── model_audit.py        # Computed audit, 16 rules, JSON export
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
│       └── charts.py             # Six institutional figures
├── tests/                        # 9 files, 42 tests
├── raw_data/                     # Source workbooks for the reconciliation
├── data/                         # Excel model and audit JSON
└── assets/                       # figure_*.png
```

---

## 16. Installation and execution

```bash
git clone https://github.com/magnumjpg/la-dehesa-financial-due-diligence.git
cd la-dehesa-financial-due-diligence
pip install -r requirements.txt

# Full pipeline (14 steps, charts, Excel, audit JSON)
python main.py

# Skip chart generation
python main.py --no-charts

# Test suite (42 tests)
python -m pytest tests/ -q
```

**Outputs:**

- `data/La_Dehesa_del_Castrillo_Financial_Model.xlsx`: 12 tabs, 2,060 formulas.
- `data/model_audit_summary.json`: computed audit, schema 4.0.0.
- `assets/figure_*.png`: six institutional charts.

The pipeline is deterministic by default; the Monte Carlo and copula simulations use a fixed seed (42).

---

## 17. Limitations and next steps

This is a portfolio model, not an investment memorandum. The main limitations are explicit:

1. **The management case is an upside.** 31.36% occupancy is 1.48x the INE provincial average, and it still fails the 1.25x covenant. It should never be presented as a base case.
2. **The market case is not pure INE at maturity.** It starts at 21.24% but keeps the original 25%/20% volume ramp and 5% nominal growth, so it reaches 32% by Year 3. The F&B attachment remains at the original 950 meals.
3. **The Monte Carlo is a naive Gaussian.** The copula engine is the better tail-risk tool; the Gaussian simulation is kept as a benchmark.
4. **The DSRA is contractual, not tail-tested.** The funding engine uses six months (€13,824); the credit committee recommends €62,786 based on Clayton CVaR 99%. The term sheet should use the larger figure, which would widen the equity requirement.
5. **The Phase II CapEx is a pre-tender estimate.** There are no binding construction quotes; the contingency is 5% of PEC.
6. **The tax model is simplified.** It uses a 25% corporate tax rate, no VAT group, no regional deductions and a BIN schedule limited to the projection horizon.
7. **The payroll model is part-time.** The hourly rates are compliant, but scheduling, coverage and turnover risk remain.
8. **The grant is assumed committed.** There is no award letter in the repository; the LEADER timing is modelled at Month 14.
9. **The two source workbooks used for the reconciliation are included in `raw_data/`.** The original Word report and the live OneDrive workbook are not redistributed; the promoter case is hard-coded from the audited values and replicated in `statements.py`.
10. **The restaurant demand is guests-only.** The model assumes one meal per guest per day in the management case (about 2,163 meals in Year 1), with no external covers, events or beverage revenue. The restaurant is a large share of revenue and is not independently underwritten.
11. **No booking curve or competitive set.** ADR is flat in the management case; the market and promoter cases use 5% nominal growth from Year 4. A real mandate would model the booking curve and the local competitive set.
12. **The monthly engine is a liquidity stress, not a full monthly three-statement model.** It reconciles to the annual statements (difference €0.00) but does not replace them.

**Next steps I would take in a real mandate:**

- Resize the senior facility to the DSCR cap (€339,145) or re-price to an ADR that clears 1.25x with 10% headroom.
- Raise the cash equity to at least €521,090 and document the land contribution.
- Term-sheet the VAT bridge and the revolver as separate committed facilities.
- Commission binding construction quotes and a QS report for the €550k works package and for Phase II.
- Stress the payroll under a full-time staffing scenario and 10% wage inflation.
- Test a 20% cost overrun and a 12-month delay in the LEADER grant.

---

## 18. References

- **INE**, *Encuesta de Ocupación en Alojamientos de Turismo Rural* (EOTR), table 2070, Segovia, 2023-2025.
- **Ley 37/1992**, *Impuesto sobre el Valor Añadido*, Art. 91.Uno.2.2ª (10% hospitality rate) and Art. 92-114 (deductible input VAT).
- **Ley 27/2014**, *Impuesto sobre Sociedades*, 25% corporate tax rate and the accelerated depreciation tables.
- **Convenio Colectivo Provincial de Hostelería de Segovia** (2026), salary tables for cooks, waiters and auxiliary staff.
- **Real Decreto 126/2026**, 2026 SMI (€17,094 gross/year, 14 payments of €1,221).
- **LEADER / Diputación de Segovia**, rural development grant framework (€163,000 assumed commitment).
- **USALI** (Uniform System of Accounts for the Lodging Industry), 11th edition, for the unit-economics structure.
- **Benchmark set:** Vivood Landscape Hotel (Alicante), Miluna Open Nature Rooms (Toledo), Basoa Suites (Navarra), Cabañitas del Bosque (A Coruña).

---

### A note on authorship and purpose

The original Excel and Word files are my own university work. The Python layer was added to demonstrate AI-assisted financial modelling, not to claim authorship of the original study. The model's value is not that it makes the project look better; it is that it makes the project's weaknesses visible, quantified and testable. The audit's `CONDITIONAL` verdict and the credit committee's `DECLINE AS STRUCTURED` recommendation are the honest outputs.
