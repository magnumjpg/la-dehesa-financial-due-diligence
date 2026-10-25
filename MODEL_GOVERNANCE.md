# Model Governance

## 1. Purpose and status

This document records the model's purpose, structure, conventions, controls, exceptions and accountability. It supports a credit and investment decision on a 25-hectare rural estate in Segovia. It is not an investment memorandum or a substitute for an independent model audit; no third-party review has been performed.

Status at 25 October 2026: `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`. All six exceptions are deal findings, not formula errors. The suite has 73 tests (up from 68); the workbook has 13 tabs and 2,060 formulas. The deterministic path is reproducible; simulations use seed 42.

## 2. Model map

| File | Responsibility |
|---|---|
| `main.py` | 15-step pipeline: reconciliation, projections, funding, returns, simulations, reform, audit. |
| `src/config/assumptions.py` | CapEx, payroll, debt, OPEX, scenarios, case calibration. |
| `src/config/reform.py` | `ReformConfig`, R1-R6 and R7 presets. |
| `src/config/ine_weights.py` | INE Segovia monthly occupancy, calibrated to 21.24%. |
| `src/core/statements.py` | Three-statement engine, three cases, equity plug, reform overlay. |
| `src/core/debt.py`, `tax.py` | French amortisation; VAT, 25% CIT, BIN. |
| `src/core/funding.py` | Sources and uses, DSCR/LTV sizing, Phase II gate. |
| `src/core/reform.py` | R1-R7 runs, value bridge, frontier, valuation cross-check, distress playbook. |
| `src/core/model_audit.py` | 16-rule audit and JSON export (schema 4.0.0). |
| `src/data/export_excel.py`, `live_excel.py` | 13-tab workbook and live formulas. |
| `src/simulation/` | Monte Carlo and Gaussian/Student-t/Clayton copula. |
| `tests/` | 12 files, 73 tests. |

## 3. Calculation flow

The chain is fixed: **as-is three cases → funding → debt → returns → reform R1-R6 → R7**.

1. **As-is.** Management revenue €154,548.00, EBITDA €24,279.92, minimum DSCR 1.15x; market €95,555.00, -€18,565.58, -1.46x; promoter (re-modelled) €86,275.00, €11,297.00, 0.33x. CapEx €1,050,100 in the first two.
2. **Funding.** Sources equal uses. Cash equity is a plug: €521,090.22 (49.62% of CapEx) plus €250,000 land in kind.
3. **Debt.** Sized on minimum pre-tax CFADS from Year 2 at 1.25x DSCR and 35% LTV. DSCR binds: €339,144.92 vs €367,535 requested. 20-year French at 4.0% fixed, 12-month grace; Year-2 service €27,647.64. No cash sweep or cure mechanics.
4. **Returns.** Year-5 EBITDA over cap rate, floored at zero, less exit costs. Management project IRR at 8.5% exit: -9.49% vs 8% WACC.
5. **R1-R6.** Same statements, separate budget and revenue overlay. R2: €71,321 mature EBITDA, 2.13x DSCR, but -€324,723 net gap vs total investment.
6. **R7.** Six cabins plus house, €200 ADR, 50% occupancy, €110,000 per cabin. CapEx €1,441,600; total investment €1,540,760.04; Year-5 EBITDA €155,712.50; 1.41x DSCR; net gap +€49,146.54 (3.2%); NPV +€76,416.23; IRR 9.21%. Stretch: €150,000 per cabin, €230 ADR, 55%, CapEx €1,708,000, +€506,865 gap, 3.30x, 14.33% IRR. Downside: five cabins, €190 ADR, 45%, €150,000 per cabin, CapEx €1,541,500, €71,597.62 EBITDA, 0.79x, -€988,767 gap, -9.23% IRR.

## 4. Conventions

| Item | Convention |
|---|---|
| Currency and units | Euros throughout; two decimals. No FX. |
| Price basis | Constant 2026 euros in reform and R7; ADR, OPEX and payroll flat in real terms. |
| Signs and rounding | Inflows positive, costs and debt service negative. Two-decimal rounding; Excel `ROUND`; tolerances €1 and 0.01x. |
| VAT and bridge | 10% output on lodging and restaurant; 21% input on CapEx and taxable OPEX; annual settlement. €168,021 input VAT funded by a €175,000 bridge, repaid with the AEAT refund in Month 18. |
| Time | Five annual periods; debt monthly over 240 months; liquidity monthly over 24 months, reconciled to the annual statements. |
| Tax | 25% flat CIT (15%/20% new-entity regime not used); BIN inside the horizon; deferred tax asset on the balance sheet; grant not amortised to P&L. |
| Depreciation | 3%, 12%, 10%, 10% and 25%; land not depreciable; pre-opening over five years; D&A €45,943. |
| Exit | EBITDA over cap rate, floored at zero; exit costs 3% (4% R6/R7 downside); no appraisal. |

## 5. Controls and reconciliation

- **Tests.** 73 tests in 12 files cover debt, VAT, tax and BIN, three-statement equality, funding, returns, scenarios, unit economics, liquidity, copulas, the audit and R1-R7. Changes require passing tests.
- **Computed audit.** 16 rules; 10 pass, five material failures and one warning failure.
- **Promoter case.** Re-modelled to the presentation's headline pair (€86,275 revenue / €11,297 EBITDA), not replicated from the source workbooks. Both workbooks contain different Year-1 revenues (€74,851 net in `Conclusiones`, €99,487.50 gross in the `Plan de Negocio` formulas, €96,628 hard-coded in the deck), and the €11,297 EBITDA has no build-up in the source. `RULE_13` is therefore an *INFO* check that the model hits its stated target; README §2 carries the full reconciliation.
- **Python-to-Excel.** Revenue €154,548, EBITDA €24,280, Year-2 DSCR 1.1534x, Year-1 cash €20,700.88, Year-2 cash €183,322.64 and balance-sheet discrepancy €0.00 all reconcile.
- **Balance-sheet equality.** Assets equal liabilities plus equity in all three cases; maximum discrepancy €0.00.
- **Value bridge.** R2 is computed lever by lever and ties to reform EBITDA with a zero residual.
- **Determinism.** No random draws in the deterministic path; Monte Carlo and copula runs use seed 42.
- **Recomputation.** DSCR, sources and uses, the Phase II gate and the debt cap are recomputed outside the reporting layer.

## 6. Assumption log

**Measured**: observed, statutory or a model identity. **Triangulated**: benchmark check, no binding quote. **Judgement**: analyst assumption.

| Assumption | Value | Basis | Source or rationale | Where it bites |
|---|---:|---|---|---|
| Land value | €250,000 | Judgement | Opportunity cost, every case | CapEx, equity |
| Works | €550,000 | Triangulated | 550 m² at €1,000/m² | CapEx |
| Fit-out and digital | €172,000 | Triangulated | €55k+€65k+€40k+€12k | CapEx |
| Fees, contingency | 6% and 5% of works | Judgement | Fees, contingency | CapEx |
| Total CapEx | €1,050,100 | Measured | Cost-line identity | Funding, DSCR |
| Pre-opening | €35,000, 5 years | Judgement | Capitalised costs | D&A, cash |
| VAT | 10% output; 21% input | Measured | Ley 37/1992 | Revenue, bridge |
| Corporate tax, BIN | 25%; BIN in horizon | Measured / Judgement | Ley 27/2014 | Tax, net income |
| Senior debt | 35% LTV; €367,535 | Measured | Requested structure | Funding |
| Covenant | 1.25x DSCR | Measured | Bank covenant | Debt sizing |
| DSCR-capped debt | €339,144.92 | Measured | CFADS / 1.25x | Binding constraint |
| Rate and tenor | 4.0%, 20 years, 12m grace | Judgement | Indicative terms | Debt service |
| Liquidity | DSRA €13,823.82; cash €15,000 | Measured / Judgement | Six months; policy | Equity plug |
| INE market occupancy | 21.24% | Measured | INE EOTR 2070, 2025 | Market case |
| Management occupancy | 31.36% mature; 28.23% Year 1 | Judgement | 72%/65%/10.1% mix | Revenue, RULE_10 |
| Management ADR | Flat | Judgement | Constant-price convention | Revenue, value |
| Restaurant demand | €25; one meal per guest-day | Judgement | No external covers | Revenue |
| Payroll and OPEX | €60,075 and €30,500 | Triangulated | Part-time, SMI-compliant | EBITDA |
| Exit cap and WACC | 8.5% as-is; 9.5% R7; 8% WACC | Judgement | Rural hospitality | Value, IRR |
| Exit costs | 3% (4% R6/R7 downside) | Judgement | Selling costs, taxes | Net value gap |
| R7 unit economics | €200, 50%, €110,000/cabin | Triangulated | €180-210, 45-55%, €110-150k | R7 value, DSCR |
| Cost-inflation stress | 0%, 2%, 2.5%, 3% real | Judgement | Margin-squeeze scenario | Margin, net gap |

## 7. Audit exception disposition

A **model defect** is a wrong formula or link; a **deal finding** means the arithmetic is right and the transaction fails. No open model defect.

| Rule | Finding | Model defect or deal finding? | Disposition | Closing condition |
|---|---|---|---|---|
| RULE_05 | Minimum DSCR 1.15x vs 1.25x | Deal finding | Resize debt to €339,144.92 or add equity | DSCR ≥ 1.25x each year |
| RULE_11 | Phase II gap -€252,241.06; DO NOT PROCEED | Deal finding | Do not commit; fund separately | €435,563.70 committed; DSCR ≥ 1.25x |
| RULE_12 | Project IRR -9.49% vs 8% WACC | Deal finding | Decline on value | IRR ≥ 8% net of exit costs |
| RULE_14 | Market minimum DSCR -1.46x | Deal finding | Not financeable at 35% LTV | Market DSCR ≥ 1.25x or all-equity |
| RULE_15 | Cash equity 49.62% vs 30% plan | Deal finding | Re-plan funding; €521,090.22 plus land | Equity ≤ 30% or commitment |
| RULE_10 | Management occupancy 31.36% = 1.48x INE 21.24% | Deal finding (warning) | Keep as upside; Phase 0 test | Booking evidence |

RULE_07 passes at €13,823.82: a contractual six-month reserve, not tail-tested.

## 8. Price basis and inflation

Constant 2026 euros. ADR, payroll and OPEX are flat. Revenue is not indexed: indexing both sides would add nominal EBITDA capitalised at a real cap rate, flattering terminal value.

R7 yields 10.11% on cost against a 9.50% exit cap; break-even cap is 9.80%, 30.3 bp of headroom. At no compression the net gap is -€46,222.80, the exit-cost bill. Break-even EBITDA is €150,899.18, €4,813.32 below base; the implied exit multiple is 10.53x. Multiples: -€181,390 at 9.0x, +€45,172 at 10.5x, +€271,733 at 12.0x.

The cost-inflation stress is asymmetric: costs grow in real terms, prices do not. A margin-squeeze scenario, not a forecast.

| Real cost growth | EBITDA Year 5 | DSCR Year 5 | Net gap vs total investment |
|---:|---:|---:|---:|
| 0.0% | €155,713 | 3.15x | +€49,147 |
| 2.0% | €136,912 | 2.78x | -€142,819 |
| 2.5% | €132,035 | 2.69x | -€192,609 |
| 3.0% | €127,087 | 2.59x | -€243,134 |

At 2% real cost growth the entire 3.2% margin disappears. The covenant still passes on this measure; the net total-investment test does not.

## 9. Change control and reproducibility

Changes are made in source control. A change is complete only when the suite passes, the audit is regenerated and the Python-to-Excel checks reconcile. Generated `data/` and `assets/` files are outputs, not inputs; a number that cannot be regenerated from a commit is not part of the model. Report tabs are Python snapshots; live tabs must be opened in Excel or LibreOffice to evaluate.

**How to run**

```bash
python -m pip install -r requirements.txt
python -m pytest tests/ -q          # 73 tests
python main.py                      # full pipeline
python main.py --no-charts          # skip figures
```

## 10. Limitations and sign-off

This model does not replace an independent audit; none has been commissioned. Limitations: no binding construction quotes; unproven F&B and experience demand; a naive Gaussian Monte Carlo benchmark; a contractual rather than tail-tested DSRA; simplified tax with BIN limited to the horizon; no LEADER award letter; a liquidity stress, not a full monthly model; and planning-assumption exit costs. R7 is fragile: 3.2% margin; €110,000 per cabin is a benchmark, not a contract. Cost ladder: -€19,263 at €120,000, -€87,672 at €130,000, -€224,490 at €150,000 and -€429,718 at €180,000.

Downside: minimum DSCR 0.79x in Year 1; CFADS shortfall €4,577.04, covered by the €20,292.72 six-month DSRA. An equity cure to 1.25x costs €17,455.75. Net exit value €654,606.82 against €457,236.43 debt gives 143% lender recovery; equity receives €197,370.39 against €1,113,342.89 invested, a 17.7% recovery. The lender is repaid; the equity is wiped out.

| Role | Name | Date | Status |
|---|---|---|---|
| Model owner | [Name] | [Date] | Pending |
| Independent model reviewer | [Name] | [Date] | Not performed |
| Credit approver | [Name] | [Date] | Pending |
| Technical / QS reviewer | [Name] | [Date] | Pending |

No third-party review has been performed. This sign-off records internal accountability only.
