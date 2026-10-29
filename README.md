# La Dehesa del Castrillo S.L.
### Hospitality Feasibility, Senior Debt Underwriting & Computed Due Diligence

Language: [Español](README_ES.md) · [Model Governance](MODEL_GOVERNANCE.md) · [Excel Model](data/La_Dehesa_del_Castrillo_Financial_Model.xlsx)

> **Executive Underwriting Memo**: Independent credit assessment and financial due diligence of a 25-hectare rural hospitality asset in Segovia, Spain. Evaluates debt service coverage under full amortization, identifies structural covenant failure, and models turnaround restructuring scenarios.

**Artifacts & Standards**: Python 3.11 Engine · 121 Automated Tests (`pytest`) · 16-Rule Computed Audit · 22-Tab Live Excel Model · USALI-Compliant Structure.

---

## 1. Executive Summary & Underwriting Verdict

| Metric | Promoter Plan (Deck) | Institutional Audit (Management Case) | Variance / Credit Impact |
| :--- | :--- | :--- | :--- |
| **All-in Project CapEx** | €725,000 | **€1,050,100** | +€325,100 (+44.8% cost overrun) |
| **Required Cash Equity** | €217,500 (30.0%) | **€521,090 (49.6%)** | +€303,590 (+139.6% cash equity) |
| **Senior Debt Facility** | €367,535 (35.0% LTV) | **€367,535 (Requested)** | Debt capacity capped at **€339,145** |
| **Year 2 DSCR (Amortizing)** | Not modeled (stated >2.0x) | **1.15x** | **FAIL** (Breaches 1.25x bank covenant) |
| **Minimum DSCR across term** | 2.10x | **1.15x** | Never recovers above 1.20x in 5 years |
| **Project IRR (8.5% Exit)** | +6.84% | **-9.49%** | Negative economic return vs 8.0% WACC |
| **Credit Recommendation** | Approve facility | **DECLINE AS STRUCTURED** | Facility over-levered; restructuring required |

### The Underwriting Verdict: DECLINE AS STRUCTURED
The credit committee recommendation is **DECLINE AS STRUCTURED**. While the project complies with standard loan-to-value limits (35.0% LTV against an appraised €1.05M asset), it is constrained by cash flow debt service (CFADS):

1. **CapEx Understatement**: The promoter's budget omitted commercial kitchen (€55k), FF&E (€65k), professional fees (€42.6k), pre-opening expenses (€35k), and a 5% contingency reserve (€35.5k). The realistic non-land budget is €800,100 (€1,050,100 including the contributed €250k land).
2. **Equity Deficit**: Closing sources and uses requires **€521,090 in cash equity** (49.6% of CapEx), alongside a separate €168k VAT bridge facility. The promoter's planned 30% equity leaves an immediate €303k funding gap at close.
3. **Covenant Failure**: Year 1 passes under a 12-month interest-only grace period (DSCR 1.34x). However, in Year 2, when 20-year French amortization commences (€27,648/year debt service), CFADS generates only €31,890, driving the **DSCR to 1.15x versus a mandatory 1.25x bank covenant**.
4. **Binding Debt Constraint**: Sizing senior debt against a 1.25x DSCR on mature cash flows caps debt capacity at **€339,145** (32.3% LTV), requiring a minimum €28,390 debt reduction.

---

## 2. Three Cases Side by Side

The model evaluates three distinct operational scenarios: the original promoter deck (re-modeled to explicit drivers), an independent market anchor based on official INE rural tourism data, and a realistic management case.

| Case | Year 1 Occupancy | Mature Occupancy | Year 1 Revenue | Year 1 EBITDA | Min DSCR | Project IRR (8.5% Exit) | Equity IRR (8.5% Exit) | Underwriting Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Promoter (Re-modelled)** | 19.20% | 28.92% | €86,275 | €11,297 | 0.33x | +6.84% | +12.12% | **Illiquid** (Cash negative Y1–Y2) |
| **INE Market Benchmark** | 21.24% | 32.00% | €95,555 | -€18,566 | -1.46x | -15.18% | -50.22% | **Default** (Unserviceable debt) |
| **Management Case** | 28.23% | 31.36% | €154,548 | €24,280 | **1.15x** | **-9.49%** | **-23.16%** | **Decline** (Breaches 1.25x covenant) |

### Key Scenario Takeaways:
* **Promoter Case**: Appears viable on exit return only because it ignores construction interest, VAT timing, and working capital, resulting in negative cash positions in Years 1 and 2.
* **INE Market Benchmark**: Uses the official Segovia provincial rural tourism occupancy (21.24% in 2025, INE EOTR Table 2070). At market demand and standard pricing (€85 room ADR, €20 restaurant ticket), Year 1 EBITDA is negative (-€18,566), resulting in complete default without sponsor capital injections.
* **Management Case**: Models a premium weekend-weighted capture (31.36% mature occupancy) and on-site guest F&B spend (€25 ticket). Even under this operating upside, debt service leaves insufficient cushion to clear institutional underwriting criteria.

---

## 3. Capital Stack & Sources and Uses at Financial Close

The underwriting engine solves for cash equity as a balancing plug to ensure sources equal uses at financial close:

| Uses at Close | Amount | Sources at Close | Amount | Capital Stack (%) |
| :--- | ---: | :--- | ---: | :---: |
| **Land Contributed in Kind** | €250,000.00 | **Senior Debt Facility (35% LTV)** | €367,535.00 | 28.1% |
| **Hard & Soft Construction CapEx** | €800,100.00 | **VAT Bridge Facility** | €168,021.00 | 12.9% |
| **Interest During Construction (IDC)** | €14,701.40 | **Cash Equity (Sponsor Plug)** | €521,090.22 | 39.9% |
| **CapEx Input VAT (21% on non-land)**| €168,021.00 | **Land Equity (in kind)** | €250,000.00 | 19.1% |
| **Pre-Opening Expenses** | €35,000.00 | | | |
| **Initial Working Capital** | €25,000.00 | | | |
| **Debt Service Reserve (DSRA, 6 mo)** | €13,823.82 | | | |
| **Total Uses** | **€1,306,646.22** | **Total Sources** | **€1,306,646.22** | **100.0%** |

### Structural Financing Notes:
* **VAT Bridge Mechanism**: The €168,021 input VAT on construction is funded via a dedicated bridge facility carrying 5.5% interest, fully repaid in Month 18 upon receipt of the tax refund from the Spanish Tax Agency (AEAT).
* **LEADER Rural Grant**: The €163,000 grant from regional development funds is modeled as disbursed in Month 14 post-completion. Because grant disbursement is contingent on certified completion, it cannot serve as closing liquidity.
* **DSRA Sizing**: Contractual 6-month reserve requires €13,824. However, stochastic tail-risk testing (Clayton copula at 99% CVaR) indicates that an adverse demand shock would require **€62,786 in liquidity reserves** to prevent debt service interruption.

---

## 4. Key Underwriting Findings

```
                              CAPEX & DEBT GAP
  Promoter Plan:  €725k CapEx  |  Debt: €367.5k  |  Equity: €217.5k (30%)
  Audited Base:   €1,050k CapEx |  Debt: €339.1k* |  Equity: €521.1k (49.6%)
                                (*DSCR binding cap vs €367.5k requested)

                             YEAR 2 DSCR CLIFF
  Year 1 (Interest-only):  [=========================] 1.34x (PASS)
  Year 2 (Amortizing):     [===================] 1.15x (FAIL - Covenant: 1.25x)
```

### Finding 1: Debt Sizing is Constrained by Cash Flow, Not Asset Value
The promoter sized senior debt to a standard 35.0% LTV against the completed property value. However, the cash-flow available for debt service (CFADS) in Year 2 (€31,890) can only support an annual service of €25,512 at the 1.25x covenant. The maximum bankable loan is **€339,145** (32.3% LTV). Proceeding with €367,535 creates an immediate technical covenant default.

### Finding 2: Demand relies on Weekend Concentration (The Occupancy Bridge)
The management occupancy of 31.36% (114.5 days) is 10.1 percentage points above the provincial average of 21.24%. The model builds a defensible demand bridge:
* **Friday-Saturday Weekends (104 nights)**: 72.0% occupancy (vs 48.0% provincial average). Accounts for 68% of the total occupancy premium.
* **Holiday Bridges (24 nights)**: 65.0% occupancy (vs 45.0% provincial average).
* **Midweek Days (237 nights)**: 10.1% occupancy (vs 7.1% provincial average).
This proves the asset is viable as a weekend destination, but confirms that midweek demand remains thin.

### Finding 3: Phase II Expansion Fails Phase-Gate Test
The promoter proposed funding a Phase II expansion (€359,970 net CapEx for two landscape suites and biological pool) from Phase I operating cash flows. The model demonstrates that Year 2 ending cash is €183,323, leaving an immediate **€252,241 funding deficit**. Combined with the Year 2 covenant breach, the phase gate triggers a mandatory **DO NOT PROCEED** flag.

---

## 5. Turnaround Analysis & Restructuring Options

The model implements a separate restructuring layer (`case="reform"`) testing operational enhancements, value engineering, and product redesigns to determine what would be required to achieve bankability.

| Case | Strategy | All-in CapEx | Total Investment | Mature EBITDA | Min DSCR | Net Asset Value (8.5% cap) | Net Gap vs Investment | Project IRR | Recommendation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **R1** | CapEx Cut Only (€900k) | €901,800 | €986,297 | €37,042 | 1.34x | €422,710 | -€563,587 | -7.18% | Decline (Negative value) |
| **R2** | Commercial Reform (€1.05M) | €1,050,100 | €1,138,625 | €71,321 | **2.13x** | €813,903 | -€324,723 | +2.53% | **Covenant cleared, Value fails** |
| **R3** | Reform + Value Engineering | €901,800 | €986,297 | €71,321 | 2.44x | €813,903 | -€172,394 | +5.37% | Sub-WACC return |
| **R5** | Lean Scope (€846k) | €846,300 | €929,289 | €71,321 | 2.57x | €813,903 | -€115,387 | +6.61% | Sub-WACC return |
| **R7** | **Product Pivot (6 Cabins)** | **€910,000** | **€1,540,760** | **€155,713** | **1.41x** | **€1,589,907** | **+€49,147** | **+9.21%** | **VIABLE (Phase 0 test first)** |

### Restructuring Takeaways:
* **The Operational Fix (R2)**: Opening the restaurant to external diners (6 covers/day at €28 ticket), adding agro-experiences (€12k/year), and lifting lodging ADR by 5% increases mature EBITDA to €71,321. This lifts minimum DSCR to **2.13x**, completely resolving the credit constraint. However, capitalized at an 8.5% exit cap rate net of 3% selling costs, the asset is worth €813,903, leaving a **€324,723 net loss** against total capital invested.
* **The Product Pivot (R7)**: Repositioning the project toward 6 premium modular cabins (€110k/unit, €200 ADR, 50% occupancy) delivers sufficient revenue density to generate €155,713 EBITDA, clearing the 8.0% WACC with a **9.21% project IRR and 1.41x DSCR**.
* **Next Action**: Execute a low-cost **Phase 0 demand test** (€50k–€80k pop-up restaurant and cabin pre-booking campaign) before committing €1M+ to physical construction.

---

## 6. Sensitivity & Tail-Risk Stress Testing

### 1. Interest Rate Shock (+0 bp to +300 bp)
Senior debt sensitivity under Reform Case R2:
* **Base (4.00%)**: DSCR 2.13x | Project NPV: -€220,685
* **+100 bp (5.00%)**: DSCR 1.96x | Project NPV: -€221,863
* **+200 bp (6.00%)**: DSCR 1.65x | Project NPV: -€223,094
* **+300 bp (7.00%)**: DSCR 1.41x | Project NPV: -€224,376
* *Finding*: The credit structure is resilient to rate hikes; the project's weakness stems from fundamental operating margin relative to CapEx, not debt expense.

### 2. Stochastic Tail-Risk Simulation (Clayton Copula, N=50,000)
Captures asymmetric lower-tail dependence where occupancy, ADR, and restaurant spending drop simultaneously during a downturn:
* **Probability of Covenant Breach (DSCR < 1.25x)**: 50.71%
* **Probability of Default (DSCR < 1.00x)**: 41.07%
* **CVaR 99% Tail Deficit**: €62,786 (identifies true liquidity reserve requirement).

---

## 7. Model Architecture & Deliverables

```
proyecto-dehesa-del-castrillo/
├── main.py                         # 15-step execution pipeline
├── README.md / README_ES.md        # Institutional deal memos (EN / ES)
├── MODEL_GOVERNANCE.md             # Assumptions log, audit exception tracking
├── data/
│   ├── La_Dehesa_del_Castrillo_Financial_Model.xlsx   # 13 tabs, 2,060 formulas
│   ├── model_audit_summary.json    # Machine-readable computed audit output
│   └── reform_analysis.json        # Restructuring and sensitivity datasets
├── src/
│   ├── config/                     # CapEx, debt terms, tax rates, INE weights
│   ├── core/                       # 3-statement engine, debt schedule, tax, DSCR
│   ├── simulation/                 # Monte Carlo and Clayton copula engines
│   └── data/                       # Dynamic Excel exporter with live formulas
└── tests/                          # 12 test modules, 74 automated unit tests
```

### Computed Audit Engine (16 Institutional Rules)
The model includes an automated audit verification layer (`model_audit.py`):
* **Balance Sheet Integrity**: Verified assets equal liabilities + equity across all 5 years (variance €0.00).
* **Tax Compliance**: Verifies 10.0% hospitality VAT and 21.0% deductible CapEx VAT.
* **Labor Compliance**: Checks payroll hourly rates against the 2026 Spanish Minimum Wage (SMI, RD 126/2026) and the Segovia Hospitality Collective Bargaining Agreement (Convenio de Hostelería 2026).
* **Audit Verdict**: `CONDITIONAL - 5 MATERIAL EXCEPTIONS` (flags management DSCR covenant breach, negative NPV, and equity plug size as formal underwriting deal exceptions).

---

## 8. Quickstart & Verification

Ensure you have **Python 3.11+** installed:

```bash
# 1. Clone repository
git clone https://github.com/magnumjpg/la-dehesa-financial-due-diligence.git
cd la-dehesa-financial-due-diligence

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run full financial pipeline (generates Excel model, audit JSON, and charts)
python main.py

# 4. Run automated test suite (121 tests)
pytest -q
```

---

## 9. Author & Underwriting Attribution

* **Author**: Jaime Pérez ([LinkedIn](https://linkedin.com) · [GitHub](https://github.com/magnumjpg))
* **Background**: Business Administration (ADE), Universidad de Alcalá (Madrid). Focus on financial modeling, credit risk underwriting, and automated financial systems.
* **Repository**: [github.com/magnumjpg/la-dehesa-financial-due-diligence](https://github.com/magnumjpg/la-dehesa-financial-due-diligence)
