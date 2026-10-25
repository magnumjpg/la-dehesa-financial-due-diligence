# La Dehesa del Castrillo S.L.

### Hospitality Feasibility, Senior Debt Underwriting & Computed Due Diligence

**A portfolio-grade financial model built from my own university feasibility study.**
Python 3.11 · 73 automated tests · 16-rule computed audit · 13-tab Excel model · 8 figures · 15-step pipeline

[![tests](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml/badge.svg)](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## The 60-second version

**The asset.** A 25-hectare rural estate in Segovia: 7 double rooms, one full country house, a 21-cover restaurant and a natural swimming biopool. It started as my university feasibility study.

**What I built.** Three as-is cases (promoter, INE market, management), a full cost stack, sources and uses, a 20-year amortising facility, a computed 16-rule audit, a live-formula Excel workbook, 73 tests and eight figures.

**The answer is no.** The management case fails the 1.25x DSCR covenant in Year 2 at **1.15x**, needs **49.6% cash equity** instead of the planned 30%, and returns a project IRR of **-9.49%** even with an 8.5% exit. The credit recommendation is **DECLINE AS STRUCTURED (RESIZE REQUIRED)**.

**The occupancy question is fair, and the model answers it.** 31.36% is not a flat 48% uplift on the INE's 21.24%. It is a weekend-weighted mix: **72% weekends, 65% holiday bridges and 10.1% midweek**. 68% of the 10.1 pp gap is weekend capture; the midweek is thin in both the plan and the market. That makes the case defensible for a boutique with a restaurant, not certain.

**The reform fixes the credit, not the value.** Six external F&B covers/day, +5% ADR and one extra FTE lift the minimum DSCR to **2.13x**, but the asset is worth €839,075 gross and **€813,903 net of 3% exit costs**, against €1,138,625 of total investment: a **-€324,723 net value gap**. Only the aggressive, unproven R4 corner clears the 8% WACC, and even it fails the net bank test.

**What would change my mind.** A Phase 0 demand test (pop-up or leased restaurant), a lean scope at or below €846k, and debt sized to the DSCR cap rather than to 35% LTV.

---

## How to read this

| Time | Read | What you get |
|---|---|---|
| **5 min** | [The 60-second version](#the-60-second-version) + [Section 3](#3-the-findings-that-matter) | The verdict and the eleven findings that drive it |
| **15 min** | Add [Section 6](#6-demand-calibration-ine-promoter-and-management) and [Section 13](#13-reform--resize-what-would-have-to-be-true) | Why 31.36% occupancy is defensible, and why the reform still fails |
| **30 min** | Add [Section 9](#9-returns-the-exit-does-not-rescue-the-realistic-cases) and [Section 14](#14-red-team-seventeen-attacks-on-my-own-model) | The returns, the net exit test and my own seventeen attacks on the model |
| **Full** | All 20 sections + the Excel workbook | The complete audit trail, formulas and limitations |

> **The one-paragraph version.** The realistic model reaches a harsher conclusion than the original university work. Once the full cost stack, construction interest, debt amortisation, OPEX, FF&E reserve and the equity plug are modelled, the management case fails the covenant, the market case never covers its debt service, and neither earns its cost of capital. The audit is deliberately allowed to fail: **10 of 16 rules pass, 5 material exceptions and 1 warning remain open**, verdict `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`. A separate reform layer is allowed to say no as well, and it does: it fixes the covenant but not the value gap. The last layer (R7) changes the product to six premium cabins and is the only configuration that clears both the WACC and the net total-investment test — by 3.2%, and only at €110k per cabin.

---

## 1. What this project is

I started with my own university feasibility study for a 25-hectare rural estate in Segovia (7 double rooms, one full country house, a 21-seat restaurant and a natural swimming biopool). The original workbook is a two-sheet promoter simulator: a live-formula P&L and a hard-coded summary that was never tied back to it. Its formula sheet implies 18.17% occupancy (66.325 occupied days), its summary hard-codes a different revenue, and the Word report documents a more conservative 16.5-17% occupancy, part-time contracts and a LEADER grant application. Reconciling those sources is the first thing the audit had to do.

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
| **Promoter (re-modelled)** | 19.20% → 28.92% | €86,275 | €11,297 | €11,297 | 0.33x | **0.33x** | -€8,039 | 6.84% | 12.12% |

**What each case is:**

- **Promoter (re-modelled)**: the presentation's headline pair (€86,275 revenue / €11,297 EBITDA) rebuilt from explicit drivers: 19.2% occupancy in Year 1 (491 room-nights + 72 house-nights), €85 room ADR, €380 house ADR, a **€20** restaurant ticket, 859 covers, 4.5% / 25-year debt, no grace, no grant and land purchased rather than contributed in kind. It is the only case with a positive equity IRR on exit, but it is cash-negative in Years 1-2.
- **INE market**: the independent demand anchor: 21.24% official Segovia room occupancy in 2025 (INE EOTR table 2070) in Year 1, with the original unit economics and the original 25%/20% volume ramp, which reaches 32.0% by Year 3 and then grows 5% per year. The F&B attachment stays at the original 950 meals at €20. It is the closest thing to a "market" case in the workbook.
- **Management (upside)**: 31.36% mature occupancy (1.48x the INE average), one on-site meal per guest per day at a €25 ticket, the full variable-cost stack and a 5.5% VAT bridge. It is an operating upside, not a base case. Its "upside" is revenue per occupied day (F&B attachment), not occupancy: the market case actually reaches a similar mature occupancy through the original ramp.

**Why "re-modelled" and not "replicated".** The source does not contain a single Year-1 revenue. It contains four, and the summary sheets were never tied back to the formula sheet:

| Year-1 revenue basis | Figure | Provenance |
|---|---:|---|
| `Plan de Negocio` (live formulas) | €99,487.50 gross | 66.325 occupied days × 7 rooms × €85 + 66.325 × €380 + 1,392.825 covers × €25 |
| `Conclusiones y Viabilidad!B5` | €74,851 net | Hard-coded; equals the €90,570 gross implied by 491 room-nights × €85 + 72 house-nights × €380 + 859 covers × €25, divided by 1.21 |
| Same €90,570 gross at the statutory 10% | €82,336.36 | €90,570 ÷ 1.10 |
| `Presentacion!Tablas para PPT!B11` | €96,628 | Hard-coded, no build-up anywhere in either workbook |
| **Python promoter case** | **€86,275** | 491 × €85 + 72 × €380 + 859 × **€20** |

The EBITDA tells the same story. The source's own formula sheet produces **€26,701.31** (€99,487.50 − €10,446.19 of F&B cost − €62,340 of payroll and maintenance). The presentation hard-codes **€11,297** with no build-up. The Python case lands on €11,297 by construction: €86,275 of revenue − €60,075 of realistic payroll − €14,903 of other operating costs, of which €6,444 is F&B purchases costed at the **€25** ticket while revenue prices the same covers at €20. `RULE_13` is therefore reported as *INFO*, not as a passing reconciliation: it checks that the model hits its stated calibration target, and its note records that the two workbooks disagree with each other and with the model.

The occupancy has the same provenance problem. The 19.2% in the case is **implied by the 491/72 night volumes** (491 ÷ 7 rooms ÷ 365 days = 19.22%), not read from the source: the `Plan de Negocio` formula sheet uses 66.325 occupied days, which is 18.17%, and neither workbook contains the value 19.2% anywhere.

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
11. **The reform fixes the covenant, not the value gap.** A realistic revenue reform (R2: six external covers/day, +5% ADR, experiences and €5k of savings, one extra FTE) lifts mature EBITDA from €37,042 to €71,321 and the minimum DSCR from 1.15x to 2.13x. The asset is then worth €839,075 gross, **€813,903 after 3% exit costs**, still **€236,197 below CapEx** and **€324,723 below total project investment** on a net basis. Value engineering to €900k (R3) and a lean €846k scope (R5) soften the gap but remain below an 8% WACC. Only the aggressive eight-cover / +10% ADR case (R4) produces a positive NPV (+€3,722), and even it fails the net total-investment test at **-€84,147**. The reform conclusion is therefore also a decline, with a conditional Phase 0 demand test.

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

Pre-opening costs of €35,000 are capitalised and amortised over five years (€7,000/year), so total D&A is **€45,943/year**. Input VAT is **€168,021** (21% on the €800,100 non-land base). The promoter case keeps the original €725,000 base, €99,750 of input VAT and no pre-opening capitalisation.

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

### 6.1 The occupancy bridge: 31.36% is not a flat 48% uplift

The fair challenge is this: if the INE average is 21.24%, how can the management case assume 31.36% without assuming that every single night sells 48% better? It does not. The annual average is the sum of three very different segments, and the management case is a weekend-capture story, not a seven-day-demand story.

| Segment | Nights/year | Management | INE Segovia | Gap (pp) | Share of gap |
|---|---:|---:|---:|---:|---:|
| Friday-Saturday weekends | 104 | 72.0% | 48.0% | +6.84 | 68% |
| Holiday bridges | 24 | 65.0% | 45.0% | +1.32 | 13% |
| Midweek | 237 | 10.1% | 7.1% | +1.97 | 19% |
| **Annual average** | **365** | **31.36%** | **21.24%** | **+10.12** | **100%** |

The weekend and holiday occupancies are judgement anchors. The midweek is the residual that makes the three segments reconcile to the 31.36% the model already uses, so the bridge cannot quietly change the P&L. The same arithmetic is applied to the INE average, which is itself weekend-weighted: the official 21.24% is roughly 48% weekends, 45% bridges and 7.1% midweek, not a flat 21% every night.

![Figure 8: occupancy bridge](assets/figure_8_occupancy_bridge.png)

**What this does and does not prove:**

- **It proves the shape is plausible.** A destination boutique with a restaurant can sell most weekends and still be empty on a Tuesday. That is exactly what the local market does, only with weaker weekend capture.
- **It isolates the risk.** 68% of the gap is weekend demand. The plan is not betting on a seven-day market; it is betting on premium weekend pricing and a small midweek base.
- **It exposes the hole.** Midweek is only 3.0 pp above the INE. The reform's external F&B covers are an attempt to fill precisely that hole, which is why the Phase 0 demand test is the gating item.
- **It does not make the case certain.** 72% weekend occupancy is still 1.5x the market's 48%. The anchors are judgement, not a booking curve, and the first year is deliberately weaker: at 0.90x the mature curve the mix is 64.8% / 58.5% / 9.1%, which is 28.23%. That is the "the first years are hard" ramp, and it is already in the model.

The bridge is computed in `src/core/demand_bridge.py` and locked by `tests/test_demand_bridge.py`. It is an annual reconciliation, not a monthly model; monthly seasonality lives in `src/config/ine_weights.py` and Figure 1.

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

**One caveat on this table:** these IRRs are gross of selling costs. A cap-rate exit assumes the asset changes hands for free, which flatters every case. The reform layer below carries the explicit net-of-cost test (3% of value, 4% in the combined downside) and the same logic is the honest way to read the as-is numbers: they are an upper bound, not a net proceeds figure.

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

## 13. Reform / resize: what would have to be true?

This is a separate layer, not a fourth as-is case. The three original projections are untouched. The reform re-runs the same three-statement engine with `case="reform"`, a separately specified CapEx budget, an external F&B / experience revenue overlay, an explicit incremental FTE and a LEADER grant that can be delayed.

The question is deliberately answerable with "no": a reform that fixes the covenant but not the value gap is still a decline.

| Ref | Reform case | CapEx | Total investment | EBITDA Y5 | Min DSCR | EV net of exit | Net gap vs total inv. | Project NPV | Project IRR |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R1 | Capital-only (€900k) | €901,800 | €986,297 | €37,042 | 1.34x | €422,710 | -€563,587 | -€450,359 | -7.18% |
| R2 | Revenue reform (€1.05M) | €1,050,100 | €1,138,625 | €71,321 | 2.13x | €813,903 | -€324,723 | -€220,685 | 2.53% |
| R3 | Revenue + value engineering (€900k) | €901,800 | €986,297 | €71,321 | 2.44x | €813,903 | -€172,394 | -€96,378 | 5.37% |
| R4 | Aggressive demand (€1.05M) | €1,050,100 | €1,138,625 | €92,403 | 2.72x | €1,054,479 | -€84,147 | +€3,722 | 8.08% |
| R5 | Lean scope (€846k) | €846,300 | €929,289 | €71,321 | 2.57x | €813,903 | -€115,387 | -€49,106 | 6.61% |
| R6 | Combined downside | €965,560 | €1,051,789 | -€33,887 | -3.82x | €0 | -€1,051,789 | -€1,021,973 | n/a |

**What the table says:**

- **R1 proves that capital alone does not work.** Cutting the budget to €900k with no demand lever leaves EBITDA at the as-is €37,042 and destroys €563,587 of value versus total investment, net of exit costs.
- **R2 fixes the credit problem.** Six external covers per day at a €28 ticket (€61,320 of mature external F&B revenue), €12,000 of experiences, a 5% ADR uplift and €5,000 of savings lift EBITDA to €71,321. The minimum DSCR rises from 1.15x to 2.13x, so the covenant is no longer the binding constraint.
- **But R2 does not fix the value problem.** At an 8.5% cap rate the asset is worth €839,075 gross and €813,903 net of 3% exit costs. That is €236,197 below the €1,050,100 CapEx and €324,723 below the €1,138,625 total project investment (CapEx + IDC + pre-opening + working capital + DSRA). The reform moves the project from a covenant breach to a negative-NPV asset.
- **Value engineering helps but does not close the gap.** R3 (€900k) and R5 (€846k) reduce the net total-investment gap to -€172,394 and -€115,387, with project IRRs of 5.37% and 6.61%: still below the 8% WACC.
- **Only the aggressive demand corner clears 8%, and it is not bankable.** R4 needs eight external covers per day and a 10% ADR uplift. It produces €3,722 of NPV and a positive gross gap versus CapEx, but the net total-investment gap is still -€84,147 and the demand assumption is well above a defensible base case.
- **R6 confirms how quickly the reform breaks.** It is now genuinely pinned to INE 21.24% occupancy (not the management anchor) and combines half the external covers, a 10% price cut, 1.5 FTE, a 20% CapEx overrun, a 10% exit cap, +200 bp rates and a one-year grant delay. EBITDA turns negative (-€33,887), the DSCR is -3.82x and the asset is worth zero on a cap-rate basis. The downside is carried in the cash flows: a **-€1,021,973 NPV**.

**R2 value bridge (mature year, 8.5% cap rate):**

| Component | EBITDA impact | EV impact |
|---|---:|---:|
| Base management EBITDA | €37,042 | €435,783 |
| + ADR uplift (5%) | €7,182 | €84,496 |
| + External F&B (6 covers/day) | €13,698 | €161,148 |
| + Experiences | €8,400 | €98,824 |
| + Cost savings | €5,000 | €58,824 |
| **Reform EBITDA and EV** | **€71,321** | **€839,075** |

The bridge is computed with the engine itself, lever by lever, so it ties to the reform P&L with a zero residual. It is not a hand-written waterfall.

Figure 7 plots the bridge and the value frontier: the heat map shows EV minus total investment across CapEx and external covers. Almost the entire current budget is value-destroying. The only positive corner is around €700k of CapEx (€450k of non-land spend) with six or more covers. That is not the eight-room refurbishment currently specified; it is a smaller project with a different scope.

### 13.1 Exit costs: the gross cap rate flatters every case

A cap-rate exit assumes the asset changes hands for free. It does not: selling costs, transfer taxes and legal fees are real. The reform charges **3% of value** (4% in R6) and reports the net proceeds next to the gross value.

| Case | EV gross | Exit costs | EV net | Net gap vs CapEx | Net gap vs total inv. |
|---|---:|---:|---:|---:|---:|
| R2 Revenue reform | €839,075 | -€25,172 | €813,903 | -€236,197 | **-€324,723** |
| R3 Value engineering | €839,075 | -€25,172 | €813,903 | -€62,725 | -€172,394 |
| R5 Lean scope | €839,075 | -€25,172 | €813,903 | -€7,225 | -€115,387 |
| R4 Aggressive demand | €1,087,091 | -€32,613 | €1,054,479 | +€4,379 | **-€84,147** |
| R6 Combined downside | €0 | €0 | €0 | -€965,560 | -€1,051,789 |

The important line is R4: it is the only case with a positive gross gap versus CapEx, and it still fails the bank test by €84,147 once total investment and exit costs are included. The net test is the one a lender would apply; the gross test is the one that makes a bad project look marginal.

### 13.2 Rate sensitivity: the covenant survives +300 bp, the value does not

The base reform is priced at a 4.0% fixed rate. The table re-runs R2 at +0 / +100 / +200 / +300 bp.

| Shock | Interest rate | Min DSCR | Project NPV | Net gap vs total inv. |
|---|---:|---:|---:|---:|
| +0 bp | 4.00% | 2.13x | -€220,685 | -€324,723 |
| +100 bp | 5.00% | 1.96x | -€221,863 | -€325,900 |
| +200 bp | 6.00% | 1.65x | -€223,094 | -€327,131 |
| +300 bp | 7.00% | 1.41x | -€224,376 | -€328,413 |

The covenant still passes at +300 bp (1.41x versus 1.25x), so rate risk is not what kills R2. The interesting result is that the **unlevered NPV barely moves**: the project is weak because it does not earn its cost of capital at the operating level, not because the debt is expensive. A floating-rate facility with a shorter tenor would hurt the equity IRR and the cash sweep more than this table shows.

### 13.3 Grant risk: the LEADER grant is load-bearing

The reform assumes a €162,766 LEADER grant disbursed in Year 2. There is no award letter in the repository, so the model tests the downside explicitly.

| R3 scenario | Project NPV | Difference |
|---|---:|---:|
| Grant in Year 2 (base) | -€96,378 | - |
| Grant delayed to Year 3 | -€105,254 | -€8,876 |
| **No grant at all** | **-€216,215** | **-€119,838** |

Without the grant the project loses a further €119,838 of value and needs more equity at close. The grant is not a rounding item; it is part of the funding stack, and it should be treated as conditional until the award letter exists.

### 13.4 What would falsify the reform

The reform is a set of assumptions, not a forecast. The [red team](#14-red-team-seventeen-attacks-on-my-own-model) lists the seventeen attacks I would expect from a credit committee and how each one is answered. The three that would change the conclusion fastest are: external covers below four per day, weekend occupancy materially below 72%, and a construction quote above €1.05M. Any one of them moves R2 from "negative but close" to "clearly unviable".

**Reform recommendation:** `DECLINE AS STRUCTURED - ONLY THE AGGRESSIVE, UNPROVEN DEMAND CASE CLEARS THE WACC`.

The honest continuation is a low-cost **Phase 0 demand test**: prove the external F&B and experience demand with a pop-up or a leased restaurant before committing construction capital. If the family wants to proceed, the first phase should be capped at the lean scope and the second phase should sit behind a demand gate. The land must be charged at its opportunity value throughout; the project does not become viable because the site is already owned.

**Next layer: R7 (cabins and agritourism).** The R2-R6 reform fixes the credit but not the value. The remaining question is whether a different product — five or six two-bedroom cabins plus the main house — could clear it. [BENCHMARKS_R7_ES.md](BENCHMARKS_R7_ES.md) fixes the band: €180-210 ADR, 45-55% stabilised occupancy, €110-150k per cabin all-in and a 9.5% exit cap. R7 is implemented as a separate preset (`CABIN_PRESETS`), not a fourth as-is case. The base case — six cabins at €110k, €200 ADR, 50% occupancy, ten external covers and €45k of experiences — produces €155,713 of mature EBITDA, **+€49,147 of net value gap on €1,540,760 of total investment (3.2%)**, a 1.41x minimum DSCR, +€76,416 NPV and a 9.21% IRR. It clears, but only at the good edge of the corridor: at €120k per cabin the same case fails by -€19,263, and the downside (five cabins, €190, 45%) collapses to a 0.79x DSCR and -€988,767. The recommendation is therefore **proceed to a Phase 0 demand test only**, not to construction.

**Three robustness tests now sit under that margin.** The valuation cross-check shows that the +€49k is a development spread: a 10.11% yield on cost against a 9.50% exit cap. The break-even exit cap is 9.80%, only 30bp higher, and with no cap compression the net gap is -€46,223, which is exactly the exit-cost bill. The cost-inflation stress shows that 2% real cost growth with flat prices turns +€49,147 into -€142,819; at 2.5% it is -€192,609. And the distress playbook on the downside shows the lender is repaid on a sale (143% recovery) while the equity recovers only 17.7% of €1.11M — a demand failure that a cash cure should not be thrown at. The full detail is in the `Reform Case` tab and `data/reform_analysis.json`.

---

## 14. Red team: seventeen attacks on my own model

A model that only survives friendly questions is not a model. These are the ten attacks I would make first if I were paid to break this one, and what the workbook actually says. The long-form memo lists all seventeen in [RED_TEAM.md](RED_TEAM.md).

**1. "31.36% is 48% above the INE average. You invented the demand."**
Fair, and the audit says the same (Rule 10 fails at 1.48x). The bridge is the answer: 72% weekends, 65% bridges and 10.1% midweek, with 68% of the 10.1 pp gap coming from weekend capture. It is a premium weekend story, not a seven-day market, and it remains an upside case. **Verdict: weakens the base case, but it is disclosed and tested; the market case is the downside anchor.**

**2. "Your market case reaches 32% anyway, so the downside is not a downside."**
It reaches 32% only by keeping the promoter's 25%/20% volume ramp and 5% growth after Year 3. That ramp is an assumption, not evidence. At the official 21.24% in Year 1 the case has negative EBITDA (-€18,566) and a -1.46x DSCR; it never clears 1.0x within five years. **Verdict: the ramp is the weak point, and it is labelled as such.**

**3. "You charge €250k for land the family already owns."**
That is the opportunity value of the site, and it is the correct charge. Treating the land as free would turn a family subsidy into a project return and flatter every metric. The model also shows the land separately so the reader can strip it out. **Verdict: strengthens the decline; no change.**

**4. "An 8.5% cap rate is too low for rural Segovia."**
Agreed as a risk. The model uses 8.5% for the base exit and 10% in R6. Each +100 bp removes about €76k of gross value: at a 10% cap, R2 is worth €713k and the net gap versus total investment widens to -€447k. **Verdict: strengthens the decline.**

**5. "Six external F&B covers per day is made up."**
Yes. It is the single most important unproven assumption in the reform, and there is no competitive set, menu engineering or covers-by-daypart build-up in the repository. R6 cuts it to three, and the case collapses to negative EBITDA. **Verdict: genuine weakness; it is exactly why the recommendation is a Phase 0 demand test, not a construction budget.**

**6. "One extra FTE cannot serve six covers and breakfast."**
Plausible. The base uses one FTE at €28k loaded; R6 uses 1.5. The honest base should probably be 1.25-1.5 FTE, which would reduce R2 EBITDA by €7k-€14k and widen the gap. **Verdict: genuine weakness, already flagged as a condition for further work.**

**7. "Your Monte Carlo is a naive Gaussian."**
Correct. It is kept as a benchmark; the copula engine is the real tail tool. The Clayton 99% CVaR implies a €62,786 DSRA against the €13,824 contractual reserve, so the funding stack is under-reserved in the tail. **Verdict: strengthens the decline.**

**8. "Unlevered NPV understates the equity case; leverage can rescue it."**
Leverage does not create value when the asset yield is below the cost of debt, and the DSCR covenant caps the facility at €339k against the €367k requested. R2's equity IRR is 1.96%; R4's is 10.16% but only on the unproven demand corner. **Verdict: no rescue.**

**9. "You double-count the grant and ignore VAT timing."**
The grant is a capital source, not revenue, and the VAT bridge is a separate €175k facility repaid with the AEAT refund in Month 18, with interest. The Phase II gate exists precisely to test whether the grant and the VAT refund are being spent twice; it returns `DO NOT PROCEED`. **Verdict: no double count; the gate is the control.**

**10. "A Year-5 exit at 11.8x EBITDA dominates the result."**
It is a test, not a rescue: without an exit the management project IRR is -35.43%, and the table shows both. The exit multiple is high for a rural asset, which is why the cap rate is stressed to 10% in R6 and why the net-of-cost test is shown separately. **Verdict: the exit does not rescue the case; it makes the failure smaller.**

**Scorecard:** six attacks strengthen the decline, three expose genuine weaknesses (covers, FTE, exit cap) that are all gated by the Phase 0 test, and one is a presentation issue. None of them turns the project into a viable investment.

---

## 15. Computed audit: 16 rules, 10 pass, 5 material, 1 warning

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
| RULE_13_PROMOTER_CALIBRATION | Info | **PASS** | €86,275 / €11,297 | target ± €1 (not source-verified) |
| RULE_14_MARKET_DSCR | Material | **FAIL** | -1.46x | ≥ 1.25x |
| RULE_15_EQUITY_REQUIREMENT | Material | **FAIL** | 49.62% | ≤ 30.0% |
| RULE_16_FFE_RESERVE | Info | **PASS** | €4,636 | 3% of revenue |

**Verdict:** `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`.

The five material exceptions are management DSCR, Phase II self-funding, returns versus WACC, market DSCR and the equity requirement. The warning is the management occupancy assumption (1.48x the INE average). All six are deal findings, not formula errors; the disposition of each is in [MODEL_GOVERNANCE.md](MODEL_GOVERNANCE.md). The audit JSON is exported to `data/model_audit_summary.json` (schema 4.0.0) and the same rules are reproduced in the Excel `Funding & Audit` tab.

---

## 16. The Excel model

The workbook has **13 tabs** and **2,060 live formulas**:

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
| `Reform Case` | R1-R6 presets, R2 value bridge, gross/net exit, CapEx/cover frontier, stress tests, rate sensitivity, R7 premium cabins and the reform recommendation. | 0 |

The `Live Model` is intentionally simple and transparent: revenue is a formula linked to `Inputs`, debt comes from `Debt Schedule`, and the checks compare the live output with Python. The debt tab reproduces the monthly `ROUND` of the Python engine, so the Year-2 service is €27,647.64 and the loan closes at zero in Month 240.

The formulas have been validated with an independent Python calculation engine: revenue €154,548, EBITDA €24,280, Year-2 DSCR 1.1534x, Year-1 cash €20,700.88, Year-2 cash €183,322.64 and balance-sheet discrepancy €0.00 all match within the €1 / 0.01x checks. The `Read Me & Checks` tab correctly shows the covenant check as `FAIL`; the `Funding & Audit` tab is allowed to show `FAIL`. That is the audit working as intended.

The report tabs are Python snapshots and do not recalculate. Open the workbook in Excel or LibreOffice to see the live formulas evaluate.

---

## 17. Repository architecture

```
proyecto-dehesa-del-castrillo/
├── main.py                       # 15-step pipeline
├── README.md / README_ES.md
├── RED_TEAM.md / RED_TEAM_ES.md # seventeen attacks on the model and the responses
├── MODEL_GOVERNANCE.md / MODEL_GOVERNANCE_ES.md # model map, assumptions log, exception disposition
├── BENCHMARKS_R7_ES.md          # evidence note for the R7 cabin / agritourism case (Spanish)
├── requirements.txt
├── .github/workflows/tests.yml   # CI: test suite + pipeline
├── src/
│   ├── config/
│   │   ├── assumptions.py        # CapEx, payroll, debt, opex, cases, funding fields
│   │   ├── reform.py             # ReformConfig, demand anchor and the R1-R6 presets
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
│   │   ├── demand_bridge.py      # Management vs INE occupancy bridge and gap split
│   │   ├── reform.py             # Reform engine, value bridge, frontier, stress, JSON
│   │   └── model_audit.py        # Computed audit, 16 rules, JSON export
│   ├── data/
│   │   ├── extract_raw.py        # Reconciliation with the original Excel
│   │   ├── export_excel.py       # 13-tab workbook
│   │   └── live_excel.py         # Formula-driven live tabs
│   ├── scenarios/
│   │   └── scenario_analysis.py  # Conservative / base / optimistic
│   ├── simulation/
│   │   ├── monte_carlo.py        # Naive Gaussian Monte Carlo
│   │   └── copula_engine.py      # Gaussian / Student-t / Clayton
│   └── visualization/
│       └── charts.py             # Eight institutional figures
├── tests/                        # 12 files, 73 tests
├── raw_data/                     # Source workbooks for the reconciliation
├── data/                         # Excel model, audit JSON and reform JSON
└── assets/                       # figure_*.png
```

---

## 18. Installation and execution

```bash
git clone https://github.com/magnumjpg/la-dehesa-financial-due-diligence.git
cd la-dehesa-financial-due-diligence
pip install -r requirements.txt

# Full pipeline (15 steps, charts, Excel, audit and reform JSON)
python main.py

# Skip chart generation
python main.py --no-charts

# Test suite (73 tests)
python -m pytest tests/ -q
```

**Outputs:**

- `data/La_Dehesa_del_Castrillo_Financial_Model.xlsx`: 13 tabs, 2,060 formulas.
- `data/model_audit_summary.json`: computed audit, schema 4.0.0.
- `MODEL_GOVERNANCE.md` / `MODEL_GOVERNANCE_ES.md`: model map, conventions, assumption log, audit-exception disposition and change control.
- `data/reform_analysis.json`: R1-R6 presets, value bridge, frontier, stress cases, the R7 cabin presets and cost ladder, and both recommendations.
- `assets/figure_*.png`: eight institutional charts.

The pipeline is deterministic by default; the Monte Carlo and copula simulations use a fixed seed (42).

---

## 19. Limitations and next steps

This is a portfolio model, not an investment memorandum. The main limitations are explicit:

1. **The management case is an upside.** 31.36% occupancy is 1.48x the INE provincial average, and it still fails the 1.25x covenant. It should never be presented as a base case.
2. **The market case is not pure INE at maturity.** It starts at 21.24% but keeps the original 25%/20% volume ramp and 5% nominal growth, so it reaches 32% by Year 3. The F&B attachment remains at the original 950 meals.
3. **The Monte Carlo is a naive Gaussian.** The copula engine is the better tail-risk tool; the Gaussian simulation is kept as a benchmark.
4. **The DSRA is contractual, not tail-tested.** The funding engine uses six months (€13,824); the credit committee recommends €62,786 based on Clayton CVaR 99%. The term sheet should use the larger figure, which would widen the equity requirement.
5. **The Phase II CapEx is a pre-tender estimate.** There are no binding construction quotes; the contingency is 5% of PEC.
6. **The tax model is simplified.** It uses a 25% corporate tax rate, no VAT group, no regional deductions and a BIN schedule limited to the projection horizon.
7. **The payroll model is part-time.** The hourly rates are compliant, but scheduling, coverage and turnover risk remain.
8. **The grant is assumed committed.** There is no award letter in the repository; the LEADER timing is modelled at Month 14.
9. **The two source workbooks used for the reconciliation are included in `raw_data/`.** The original Word report and the live OneDrive workbook are not redistributed; the promoter case is calibrated to the presentation's headline figures and rebuilt from explicit drivers in `statements.py`, and §2 documents where it departs from both workbooks.
10. **The restaurant demand is guests-only in the as-is cases.** The management case assumes one meal per guest per day (about 2,163 meals in Year 1), with no external covers, events or beverage revenue. The reform layer adds external covers explicitly, but that demand is an assumption, not evidence.
11. **No booking curve or competitive set.** ADR is flat in the management case; the market and promoter cases use 5% nominal growth from Year 4. A real mandate would model the booking curve and the local competitive set.
12. **The monthly engine is a liquidity stress, not a full monthly three-statement model.** It reconciles to the annual statements (difference €0.00) but does not replace them.
13. **The reform demand is not independently proven.** Six external F&B covers per day is a destination-restaurant assumption; there is no local competitive set, no menu engineering, no covers-by-daypart build-up and no evidence that the 25-hectare estate can attract that traffic outside weekends.
14. **The reform frontier is a sensitivity device, not a budget.** It scales the non-land budget uniformly. The ~€700k positive corner implies €450k of non-land spend for an eight-room refurbishment, which would require a materially smaller scope and a contractor's cost plan.
15. **The incremental FTE is a judgement.** One FTE for six external covers per day is the minimum labour step-up; R6 tests 1.5 FTE and still shows how quickly the reform breaks.
16. **The occupancy bridge anchors are judgement, not a booking curve.** 72% weekend and 65% holiday occupancy are plausible for a destination boutique, but they are not measured. The INE segment split (48% / 45%) is inferred from the official annual average, not published by INE.
17. **Exit costs are a planning assumption.** 3% of value (4% in R6) covers selling costs, transfer taxes and legal fees; the actual Castilla y León bill could be higher. The net test is directionally right, not a quote.
18. **R6 is a genuine INE-demand downside, and its EV is floored at zero.** A loss-making asset is not worth a negative amount, but a real liquidation could still require remediation cash. The NPV carries the operating losses; the value line does not pretend to be a liquidation analysis.
19. **The rate sensitivity is a re-run, not a refinancing model.** It shocks a fixed-rate facility and shows the DSCR and unlevered NPV; it does not model a floating coupon path, break costs or a changed tenor.
20. **R7 is the most fragile case in the book precisely because it passes.** Its margin is 3.2% of total investment, the €110k all-in cabin cost is a benchmark rather than a binding quote (at €120k the case fails), and the €45k of experiences has no signed programme. The correct reading is not "build cabins" but "pay for a €50-80k Phase 0 test before committing €1.54M".

**Next steps I would take in a real mandate:**

- Resize the senior facility to the DSCR cap (€339,145) or re-price to an ADR that clears 1.25x with 10% headroom.
- Raise the cash equity to at least €521,090 and document the land contribution.
- Term-sheet the VAT bridge and the revolver as separate committed facilities.
- Commission binding construction quotes and a QS report for the €550k works package and for Phase II.
- Stress the payroll under a full-time staffing scenario and 10% wage inflation.
- Test a 20% cost overrun and a 12-month delay in the LEADER grant.
- Run a low-cost Phase 0 pop-up or leased-restaurant demand test before committing construction capital.
- If the family proceeds, commission a QS-led lean-scope design at or below the €846k envelope and price the second phase as a separate option.

---

## 20. References

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
