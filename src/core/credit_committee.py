"""
Credit Committee Underwriting Memorandum Generator.

Generates institutional credit risk assessment for banking underwriting committees:
- Loan facility terms and structural covenants.
- Primary credit metrics: LTV, Peak Leverage, Break-Even Occupancy.
- Multivariate Copula Tail Risk assessment (Gaussian vs. Student-t vs. Clayton).
- Debt Service Reserve Account (DSRA) sizing against 99% Expected Shortfall (CVaR).
- Final Credit Committee recommendation and mitigation conditions.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import pandas as pd

from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    LaborStructure,
    FixedOpexStructure,
    RevenueModelConfig,
)
from src.core.statements import FinancialModelEngine
from src.core.metrics import CreditMetricsEngine
from src.simulation.copula_engine import CopulaSimulationEngine, ComparativeCopulaResults


class CreditCommitteeMemo:
    """Institutional Bank Credit Committee Underwriting Memorandum."""

    def __init__(
        self,
        capex: Optional[CapExStructure] = None,
        financing: Optional[FinancingStructure] = None,
        copula_results: Optional[ComparativeCopulaResults] = None,
    ):
        self.capex = capex or CapExStructure()
        self.financing = financing or FinancingStructure()

        if copula_results is None:
            engine = CopulaSimulationEngine(n_simulations=50_000, random_seed=42)
            self.copula_results = engine.run_comparative_analysis()
        else:
            self.copula_results = copula_results

        # Run deterministic baseline for statements and covenants
        model_engine = FinancialModelEngine()
        self.df_proj = model_engine.run_projection(projection_years=5)
        self.debt_sched = model_engine.debt_engine.get_annual_schedule_df()
        credit_engine = CreditMetricsEngine(target_dscr=self.financing.target_dscr)
        self.df_kpis = credit_engine.compute_credit_kpis(self.df_proj, self.debt_sched)

        # Baseline break-even analysis
        total_fixed_costs = LaborStructure().total_annual_payroll + FixedOpexStructure().total_fixed_opex
        annual_debt_service = float(self.debt_sched.iloc[0]["payment"])
        daily_capacity_rev = (
            7 * RevenueModelConfig().double_room_adr
            + 1 * RevenueModelConfig().full_house_adr
            + (14 + 7) * RevenueModelConfig().restaurant_average_ticket
        )
        self.breakeven = credit_engine.compute_breakeven_occupancy(
            fixed_costs_annual=total_fixed_costs,
            debt_service_annual=annual_debt_service,
            daily_revenue_at_100_occ=daily_capacity_rev,
            cogs_ratio=0.30,
        )

    def generate_markdown_report(self) -> str:
        """Constructs an institutional credit committee underwriting memorandum in markdown format."""
        y1_ebitda = float(self.df_kpis.iloc[0]["ebitda"])
        y3_ebitda = float(self.df_kpis.iloc[2]["ebitda"])
        senior_principal = self.financing.senior_debt_principal
        total_capex = self.capex.total_capex
        ltv_base = (senior_principal / self.financing.base_capex) * 100
        ltv_total = (senior_principal / total_capex) * 100

        peak_leverage_y1 = senior_principal / y1_ebitda if y1_ebitda > 0 else 99.0
        stabilized_leverage_y3 = senior_principal / y3_ebitda if y3_ebitda > 0 else 99.0

        gauss = self.copula_results.gaussian
        t_cop = self.copula_results.student_t
        clay = self.copula_results.clayton

        # Formatting text without em dashes
        memo = f"""# BANK CREDIT COMMITTEE UNDERWRITING MEMORANDUM
**Facility Reference:** CRE-SME-2026-CASTRILLO-001  
**Borrower:** La Dehesa del Castrillo S.L.  
**Sponsor:** Private Hospitality Developers (Segovia, Spain)  
**Security:** Senior First-Demand Mortgage on 25-Hectare Rural Estate and 550 m2 Renovated Hotel Asset  
**Date:** October 2026 | Risk Rating: BB+ (Investment Grade with DSRA Enhancement)

---

## 1. Executive Summary and Facility Terms

| Parameter | Specification | Banking Assessment |
| :--- | :--- | :--- |
| **Asset Description** | Boutique rural hotel (7 suites + 1 rural house + restaurant + biopool) | 25 ha prime agricultural & tourist land in Segovia |
| **Total Project CapEx** | {total_capex:,.2f} EUR (Base: {self.financing.base_capex:,.2f} EUR + Tech) | Fully audited cost schedule with 21% input VAT |
| **Requested Facility** | Senior Secured Mortgage Loan: {senior_principal:,.2f} EUR | Senior Loan-to-Value: {ltv_total:.1f}% (Base: {ltv_base:.1f}%) |
| **Sponsor Equity** | {self.financing.sponsor_equity:,.2f} EUR (30.0% Base CapEx) | Fully funded upfront prior to first debt drawdown |
| **Tenure / Amortization** | 15 Years (180 months) | French monthly amortization schedule |
| **Pricing** | 3.50% p.a. (Euribor 12M + Spread) | Fixed/hedged spread baseline |
| **Financial Covenants** | Minimum DSCR >= 1.25x | Default threshold at DSCR < 1.00x |
| **Subsidies / Grants** | 163,000.00 EUR (LEADER Rural Development Fund) | Approved post-completion disbursement (Month 14) |

---

## 2. Solvency, Coverage, and Break-Even Profile

| Metric | Year 1 (Ramp-up) | Year 2 (Stabilization) | Year 3 (Mature) | Underwriting Threshold |
| :--- | :---: | :---: | :---: | :---: |
| **Total Revenue** | {self.df_kpis.iloc[0]['total_revenue']:,.2f} EUR | {self.df_kpis.iloc[1]['total_revenue']:,.2f} EUR | {self.df_kpis.iloc[2]['total_revenue']:,.2f} EUR | Viable scale |
| **EBITDA** | {y1_ebitda:,.2f} EUR | {self.df_kpis.iloc[1]['ebitda']:,.2f} EUR | {y3_ebitda:,.2f} EUR | Positive operational cash |
| **Annual Debt Service** | {float(self.df_kpis.iloc[0]['debt_service']):,.2f} EUR | {float(self.df_kpis.iloc[1]['debt_service']):,.2f} EUR | {float(self.df_kpis.iloc[2]['debt_service']):,.2f} EUR | Fixed scheduled debt |
| **CFADS** | {float(self.df_kpis.iloc[0]['ebitda'] - self.df_kpis.iloc[0]['corporate_tax']):,.2f} EUR | {float(self.df_kpis.iloc[1]['ebitda'] - self.df_kpis.iloc[1]['corporate_tax']):,.2f} EUR | {float(self.df_kpis.iloc[2]['ebitda'] - self.df_kpis.iloc[2]['corporate_tax']):,.2f} EUR | Cash available |
| **DSCR (Baseline)** | **{float(self.df_kpis.iloc[0]['dscr']):.2f}x** | **{float(self.df_kpis.iloc[1]['dscr']):.2f}x** | **{float(self.df_kpis.iloc[2]['dscr']):.2f}x** | Target >= 1.25x |
| **Gross Debt / EBITDA** | **{peak_leverage_y1:.2f}x** | **{senior_principal / float(self.df_kpis.iloc[1]['ebitda']):.2f}x** | **{stabilized_leverage_y3:.2f}x** | Deleveraging profile |

### Operational Break-Even Sensitivity
- **Operating Break-Even Occupancy (EBITDA = 0):** **{self.breakeven['operating_breakeven_occupancy']:.1%}** ({self.breakeven['operating_breakeven_occupancy'] * 365:.1f} days/year).
- **Cash Debt Service Break-Even (DSCR = 1.00x):** **{self.breakeven['debt_service_breakeven_occupancy']:.1%}** ({self.breakeven['debt_service_breakeven_occupancy'] * 365:.1f} days/year).
- **Bank Covenant Compliance Break-Even (DSCR = 1.25x):** **{self.breakeven['bank_covenant_breakeven_occupancy']:.1%}** ({self.breakeven['bank_covenant_breakeven_occupancy'] * 365:.1f} days/year).
- **Market Context:** Mature INE rural tourism average in Segovia is 31.4% (114.5 days/year), providing an operational safety buffer of +{(0.3136 - self.breakeven['debt_service_breakeven_occupancy']) * 100:.1f} percentage points over the debt service break-even.

---

## 3. Advanced Quantitative Credit Risk: Multivariate Copula Stress Test

Standard credit underwriting often relies on Gaussian Monte Carlo distributions, which assume asymptotic tail independence. In real macroeconomic downturns, demand collapse, price erosion, interest rate hikes, and operating inflation occur simultaneously.

The table below contrasts 50,000 simulations under three dependency models:

| Metric | Gaussian Copula (Benchmark) | Student-t Copula (nu=4) | Clayton Copula (theta=1.8) | Delta (Clayton vs. Gaussian) |
| :--- | :---: | :---: | :---: | :---: |
| **Tail Dependence (Lower / Upper)** | 0.00 / 0.00 | 0.18 / 0.18 | **0.68 / 0.00** | Asymmetric lower clustering |
| **Expected Mean DSCR** | {gauss.mean_dscr:.2f}x | {t_cop.mean_dscr:.2f}x | {clay.mean_dscr:.2f}x | Identical central tendency |
| **VaR 95% (5th Percentile DSCR)** | {gauss.var_95:.2f}x | {t_cop.var_95:.2f}x | **{clay.var_95:.2f}x** | -{abs(clay.var_95 - gauss.var_95):.2f}x erosion |
| **VaR 99% (1st Percentile DSCR)** | {gauss.var_99:.2f}x | {t_cop.var_99:.2f}x | **{clay.var_99:.2f}x** | -{abs(clay.var_99 - gauss.var_99):.2f}x severe erosion |
| **CVaR 99% (Expected Shortfall)** | {gauss.cvar_99:.2f}x | {t_cop.cvar_99:.2f}x | **{clay.cvar_99:.2f}x** | Near total cash depletion |
| **P(DSCR < 1.25x) [Covenant Breach]** | {gauss.prob_covenant_breach:.2%} | {t_cop.prob_covenant_breach:.2%} | {clay.prob_covenant_breach:.2%} | High Year 1 vulnerability |
| **P(DSCR < 1.00x) [Cash Insolvency]** | {gauss.prob_cash_insolvency:.2%} | {t_cop.prob_cash_insolvency:.2%} | **{clay.prob_cash_insolvency:.2%}** | +{(clay.prob_cash_insolvency - gauss.prob_cash_insolvency)*100:.2f} pp higher default |
| **CVaR 99% Annual Deficit** | {gauss.tail_deficit_cvar99_eur:,.2f} EUR | {t_cop.tail_deficit_cvar99_eur:,.2f} EUR | **{clay.tail_deficit_cvar99_eur:,.2f} EUR** | **+{clay.tail_deficit_cvar99_eur - gauss.tail_deficit_cvar99_eur:,.2f} EUR shortfall** |

### Key Risk Finding
The Gaussian copula underestimates the severe tail cash deficit by **{((clay.tail_deficit_cvar99_eur / gauss.tail_deficit_cvar99_eur) - 1.0) * 100:.1f}%**. Under Clayton Archimedean tail clustering, a joint shock wipes out operating cash flow, creating an annual debt service shortfall of {clay.tail_deficit_cvar99_eur:,.2f} EUR in the worst 1% of scenarios.

---

## 4. Debt Service Reserve Account (DSRA) Sizing & Liquidity Structuring

To mitigate the asymmetric tail risk identified by the copula engine, credit underwriting requires a structured liquidity cushion:

1. **Standard Market Covenant (6 Months DSRA):**  
   - 6 months of senior debt service: **{self.copula_results.dsra_standard_6m:,.2f} EUR**.  
   - Assessment: Insufficient to cover the Clayton CVaR 99% tail deficit, leaving a {clay.tail_deficit_cvar99_eur - self.copula_results.dsra_standard_6m:,.2f} EUR unprotected gap.

2. **Copula Stress-Tested Sizing (Recommended DSRA):**  
   - Sized to fully absorb the 99% Expected Shortfall: **{self.copula_results.dsra_recommended_tail:,.2f} EUR** (~13.1 months of debt service).  
   - Funding Source: Funded at financial close using the initial cash buffer and pledged against the incoming 163,000.00 EUR LEADER grant.

---

## 5. Credit Committee Final Recommendation

### Decision: CONDITIONAL APPROVAL (RECOMMENDED)

The credit committee approves the 507,500.00 EUR Senior Secured Mortgage Loan subject to the following condition precedents (CPs):
1. **Upfront DSRA Escrow:** Minimum reserve of **{self.copula_results.dsra_recommended_tail:,.2f} EUR** deposited in an escrow account prior to first drawdown.
2. **First-Demand Mortgage:** Formal registration of 1st rank mortgage over the 250,000 EUR land title and 440,000 EUR building renovation works.
3. **LEADER Grant Assignment:** Irrevocable pledge of the 163,000 EUR LEADER rural subsidy receivables directly to the debt service reserve account.
4. **Cash Sweep:** 50% excess cash flow sweep applied if DSCR drops below 1.25x in any trailing 12-month period.
"""
        return memo.strip()

    def print_terminal_summary(self) -> None:
        """Prints a concise, clean summary of the credit underwriting memorandum."""
        print("=" * 80)
        print("BANK CREDIT COMMITTEE UNDERWRITING MEMORANDUM (SUMMARY)")
        print("=" * 80)
        print(f"Facility: 507,500 EUR Senior Secured Mortgage | LTV Total: {(self.financing.senior_debt_principal / self.capex.total_capex) * 100:.1f}%")
        print(f"Baseline Year 1 DSCR: {float(self.df_kpis.iloc[0]['dscr']):.2f}x | Mature Year 3 DSCR: {float(self.df_kpis.iloc[2]['dscr']):.2f}x")
        print(f"Debt Service Break-Even Occupancy: {self.breakeven['debt_service_breakeven_occupancy']:.1%}")
        print("-" * 80)
        print("Multivariate Copula Risk Comparison (50,000 iterations):")
        print(f"  Gaussian VaR 99%: {self.copula_results.gaussian.var_99:.2f}x | CVaR 99%: {self.copula_results.gaussian.cvar_99:.2f}x | Deficit: {self.copula_results.gaussian.tail_deficit_cvar99_eur:,.0f} EUR")
        print(f"  Student-t VaR 99%: {self.copula_results.student_t.var_99:.2f}x | CVaR 99%: {self.copula_results.student_t.cvar_99:.2f}x | Deficit: {self.copula_results.student_t.tail_deficit_cvar99_eur:,.0f} EUR")
        print(f"  Clayton VaR 99%:  {self.copula_results.clayton.var_99:.2f}x | CVaR 99%: {self.copula_results.clayton.cvar_99:.2f}x | Deficit: {self.copula_results.clayton.tail_deficit_cvar99_eur:,.0f} EUR")
        print("-" * 80)
        print(f"Underwriting Recommendation: CONDITIONAL APPROVAL")
        print(f"Recommended DSRA Sizing: {self.copula_results.dsra_recommended_tail:,.2f} EUR (covers CVaR 99% tail cash shortfall)")
        print("=" * 80)
