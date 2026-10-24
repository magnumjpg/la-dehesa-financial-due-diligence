"""
Credit Committee Underwriting Memorandum Generator.

Produces an institutional credit memo for the Phase I senior facility:
- Facility terms and the actual capital structure (20 years, 12-month grace).
- Primary credit metrics: LTV, CFADS, DSCR by year and debt sizing.
- Full-stack break-even analysis computed by re-running the model.
- Multivariate copula tail risk on the Year-2 DSCR (Gaussian vs. Student-t vs.
  Clayton).
- DSRA sizing against the contractual six-month standard and the 99% CVaR.
- An honest credit committee recommendation: the facility as requested does not
  meet the 1.25x covenant in Year 2, so it is declined as structured and the
  memo sets out the conditions under which it could be re-submitted.
"""

from typing import Optional

from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    SCENARIOS,
)
from src.core.metrics import BreakEvenEngine, CreditMetricsEngine
from src.core.statements import FinancialModelEngine
from src.simulation.copula_engine import (
    ComparativeCopulaResults,
    CopulaSimulationEngine,
)


class CreditCommitteeMemo:
    """Institutional bank credit committee underwriting memorandum."""

    def __init__(
        self,
        capex: Optional[CapExStructure] = None,
        financing: Optional[FinancingStructure] = None,
        copula_results: Optional[ComparativeCopulaResults] = None,
        case: str = "management",
    ):
        self.case = case
        self.model_engine = FinancialModelEngine(
            capex=capex or CapExStructure(),
            financing=financing or FinancingStructure(),
            scenario=SCENARIOS["base"],
            case=case,
        )
        self.capex = self.model_engine.capex
        self.financing = self.model_engine.financing

        if copula_results is None:
            copula_engine = CopulaSimulationEngine(
                n_simulations=50_000, random_seed=42, case=case
            )
            self.copula_results = copula_engine.run_comparative_analysis()
        else:
            self.copula_results = copula_results

        # Deterministic baseline.
        self.df_proj = self.model_engine.run_projection(projection_years=5)
        self.debt_sched = self.model_engine.debt_engine.get_annual_schedule_df()
        self.credit = CreditMetricsEngine(
            target_dscr=self.financing.target_dscr
        )
        self.df_kpis = self.credit.compute_credit_kpis(self.df_proj, self.debt_sched)

        # Break-evens are solved by re-running the full engine, so they carry the
        # cost stack, the tax shield and the funding plug.
        self.breakeven = BreakEvenEngine(case=case).compute()

        # Debt sizing and returns.
        self.debt_sizing = self.model_engine.debt_sizing()
        self.returns = self.credit.compute_returns_summary(
            self.df_proj,
            initial_equity=self.model_engine.total_equity_at_close,
            initial_capex=self.model_engine.total_project_investment,
            exit_cap_rate=0.085,
        )

        self.senior_principal = float(self.financing.senior_debt_principal)
        self.total_capex = float(self.capex.total_capex)
        self.ltv_pct = (
            self.senior_principal / self.total_capex * 100.0 if self.total_capex else 0.0
        )
        self.cash_equity = float(self.model_engine.cash_equity)
        self.total_equity = float(self.model_engine.total_equity_at_close)
        self.total_investment = float(self.model_engine.total_project_investment)
        self.equity_to_capex = (
            self.cash_equity / self.total_capex * 100.0 if self.total_capex else 0.0
        )
        self.dsra_contractual = float(self.model_engine.dsra_amount)
        self.min_dscr = float(
            (self.df_proj["cfads"] / self.df_proj["debt_service"]).min()
        )
        self.recommendation = self._recommendation()

    # ------------------------------------------------------------------
    # Recommendation logic
    # ------------------------------------------------------------------
    def _recommendation(self) -> str:
        min_cash = float(self.df_proj["ending_cash"].min())
        if self.min_dscr >= self.financing.target_dscr and min_cash >= 0:
            return "APPROVE"
        if self.min_dscr >= self.financing.critical_dscr and min_cash >= 0:
            return "DECLINE AS STRUCTURED (RESIZE REQUIRED)"
        return "DECLINE"

    # ------------------------------------------------------------------
    # Markdown memorandum
    # ------------------------------------------------------------------
    def generate_markdown_report(self) -> str:
        """Constructs the credit committee underwriting memorandum in markdown."""
        k = self.df_kpis
        p = self.df_proj
        be = self.breakeven
        gauss = self.copula_results.gaussian
        t_cop = self.copula_results.student_t
        clay = self.copula_results.clayton
        ret = self.returns

        y1, y2, y3 = p.iloc[0], p.iloc[1], p.iloc[2]
        dscr_cap = float(self.debt_sizing["principal_dscr_cap"])
        binding = self.debt_sizing["binding_constraint"]
        dscr_cap_ltv = float(self.debt_sizing["implied_ltv_pct"])

        covenant_be = be["covenant_breakeven_occupancy_mature"]
        base_occ = be["base_occupancy_mature"]
        covenant_gap_pp = (
            (covenant_be - base_occ) * 100.0
            if covenant_be is not None else float("nan")
        )
        adr_covenant = be["covenant_breakeven_adr"]
        adr_irr10 = be["equity_irr_10pct_adr"]

        project_irr = ret["project_irr_exit"]
        equity_irr = ret["equity_irr_exit"]
        project_irr_txt = f"{project_irr * 100:.2f}%" if project_irr is not None else "n/a"
        equity_irr_txt = f"{equity_irr * 100:.2f}%" if equity_irr is not None else "n/a"

        memo = f"""# BANK CREDIT COMMITTEE UNDERWRITING MEMORANDUM

**Facility Reference:** CRE-SME-2026-CASTRILLO-001
**Borrower:** La Dehesa del Castrillo S.L.
**Sponsor:** Private hospitality developers (Segovia, Spain)
**Security:** Senior first-rank mortgage over the 25-hectare rural estate and the
550 m2 refurbished hotel asset
**Date:** October 2026
**Recommendation:** **{self.recommendation}**

---

## 1. Executive summary and facility terms

| Parameter | Specification | Banking assessment |
| :--- | :--- | :--- |
| **Asset** | Boutique rural hotel: 7 double rooms, 1 rural house, restaurant and biopool | 25 ha estate in Segovia |
| **All-in project cost** | {self.total_capex:,.2f} EUR | Audited cost schedule: works, kitchen, FF&E, biopool, digital, fees and 5% contingency |
| **Requested facility** | {self.senior_principal:,.2f} EUR | {self.ltv_pct:.1f}% of all-in cost, within the requested 35% LTV |
| **Cash equity required** | {self.cash_equity:,.2f} EUR | {self.equity_to_capex:.1f}% of CapEx, **not** the 30% assumed in the business plan |
| **Total equity at close** | {self.total_equity:,.2f} EUR | Includes the 250,000 EUR land contributed in kind |
| **Tenure / amortisation** | 20 years (240 months), 12-month interest-only grace | French schedule over the remaining 228 months |
| **Pricing** | 4.00% p.a. fixed | Base case; rate shocks tested in the copula engine |
| **Covenant** | Minimum DSCR >= 1.25x | Default threshold at DSCR < 1.00x |
| **DSRA** | {self.dsra_contractual:,.2f} EUR | Six months of the maximum annual debt service |
| **Grant** | 163,000.00 EUR (LEADER) | Post-completion, Month 14; it cannot fund close-day uses |
| **VAT bridge** | {float(self.capex.total_input_vat):,.2f} EUR | Repaid with the AEAT refund in Month 18 |

The facility is sized at 35% LTV but the binding constraint is the DSCR. At a
1.25x covenant on CFADS the sustainable principal is **{dscr_cap:,.2f} EUR**
({dscr_cap_ltv:.1f}% LTV). The requested {self.senior_principal:,.2f} EUR exceeds
that cap by **{self.senior_principal - dscr_cap:,.2f} EUR**. The binding
constraint reported by the sizing engine is **{binding}**.

---

## 2. Solvency, coverage and break-even profile

| Metric | Year 1 (ramp-up) | Year 2 (first amortising year) | Year 3 (mature) | Threshold |
| :--- | ---: | ---: | ---: | ---: |
| **Total revenue** | {float(y1['total_revenue']):,.2f} EUR | {float(y2['total_revenue']):,.2f} EUR | {float(y3['total_revenue']):,.2f} EUR | Viable scale |
| **EBITDA** | {float(y1['ebitda']):,.2f} EUR | {float(y2['ebitda']):,.2f} EUR | {float(y3['ebitda']):,.2f} EUR | Positive operating cash |
| **FF&E reserve (3%)** | {float(y1['ffe_reserve']):,.2f} EUR | {float(y2['ffe_reserve']):,.2f} EUR | {float(y3['ffe_reserve']):,.2f} EUR | Ranked ahead of debt |
| **Cash tax** | {float(y1['corporate_tax']):,.2f} EUR | {float(y2['corporate_tax']):,.2f} EUR | {float(y3['corporate_tax']):,.2f} EUR | BINs applied |
| **CFADS** | {float(y1['cfads']):,.2f} EUR | {float(y2['cfads']):,.2f} EUR | {float(y3['cfads']):,.2f} EUR | EBITDA - FF&E - tax |
| **Debt service** | {float(y1['debt_service']):,.2f} EUR | {float(y2['debt_service']):,.2f} EUR | {float(y3['debt_service']):,.2f} EUR | Scheduled |
| **DSCR** | **{float(k.iloc[0]['dscr']):.2f}x** | **{float(k.iloc[1]['dscr']):.2f}x** | **{float(k.iloc[2]['dscr']):.2f}x** | **>= 1.25x** |
| **Closing cash** | {float(y1['ending_cash']):,.2f} EUR | {float(y2['ending_cash']):,.2f} EUR | {float(y3['ending_cash']):,.2f} EUR | Positive |

Year 1 is interest-only, so its DSCR of {float(k.iloc[0]['dscr']):.2f}x looks
adequate. The covenant bites in Year 2, the first amortising year, at
**{float(k.iloc[1]['dscr']):.2f}x**: the facility fails the 1.25x test before the
asset reaches stabilisation.

### Break-even analysis (solved on the full model)

- **Operating break-even (EBITDA = 0):** **{be['operating_breakeven_occupancy_mature']:.2%}**
  mature occupancy ({be['operating_breakeven_occupancy_mature'] * 365:.1f} occupied
  days per year).
- **Cash debt-service break-even (DSCR = 1.00x):**
  **{be['debt_service_breakeven_occupancy_mature']:.2%}**
  ({be['debt_service_breakeven_occupancy_mature'] * 365:.1f} days).
- **Covenant break-even (DSCR = 1.25x):** **{covenant_be:.2%}**
  ({covenant_be * 365:.1f} days).
- **Base mature occupancy:** **{base_occ:.2%}**. The covenant break-even sits
  **{covenant_gap_pp:+.2f} percentage points above** the plan: the business case,
  as submitted, is below the level required to service the debt in compliance
  with the covenant.
- **ADR required for the 1.25x covenant at base occupancy:** **{adr_covenant:,.2f} EUR**.
- **ADR required for a 10% equity IRR (8.5% exit):** **{adr_irr10:,.2f} EUR**, about
  {(adr_irr10 / 85.0 - 1.0) * 100:.1f}% above the planned ADR.

The equity case is equally demanding: with the exit at an 8.5% cap rate, the
project IRR is **{project_irr_txt}** and the equity IRR is **{equity_irr_txt}**
against a cost of capital of 8.5%. The asset does not currently earn its cost of
capital at the planned ADR and occupancy.

---

## 3. Copula tail risk on the Year-2 DSCR

The credit test is run on CFADS after the FF&E reserve and cash tax, with the
contractual 20-year / 4.0% debt, the 12-month grace and the full cost stack
(F&B COGS, 9% blended OTA commission, EUR 35 per occupied day of amenities and
EUR 5 per guest-day of breakfast). Each of the 50,000 draws varies occupancy,
ADR, the interest rate and operating costs jointly.

| Metric | Gaussian (benchmark) | Student-t (nu=4) | Clayton (theta=1.8) |
| :--- | ---: | ---: | ---: |
| **Tail dependence (lower / upper)** | 0.00 / 0.00 | 0.18 / 0.18 | **0.68 / 0.00** |
| **Mean Year-2 DSCR** | {gauss.mean_dscr:.2f}x | {t_cop.mean_dscr:.2f}x | {clay.mean_dscr:.2f}x |
| **Median Year-2 DSCR** | {gauss.median_dscr:.2f}x | {t_cop.median_dscr:.2f}x | {clay.median_dscr:.2f}x |
| **VaR 95% (5th percentile)** | {gauss.var_95:.2f}x | {t_cop.var_95:.2f}x | **{clay.var_95:.2f}x** |
| **VaR 99% (1st percentile)** | {gauss.var_99:.2f}x | {t_cop.var_99:.2f}x | **{clay.var_99:.2f}x** |
| **CVaR 99% (expected shortfall)** | {gauss.cvar_99:.2f}x | {t_cop.cvar_99:.2f}x | **{clay.cvar_99:.2f}x** |
| **P(DSCR < 1.25x) covenant breach** | {gauss.prob_covenant_breach:.2%} | {t_cop.prob_covenant_breach:.2%} | **{clay.prob_covenant_breach:.2%}** |
| **P(DSCR < 1.00x) debt-service shortfall** | {gauss.prob_cash_insolvency:.2%} | {t_cop.prob_cash_insolvency:.2%} | **{clay.prob_cash_insolvency:.2%}** |
| **CVaR 99% annual CFADS shortfall** | {gauss.tail_deficit_cvar99_eur:,.2f} EUR | {t_cop.tail_deficit_cvar99_eur:,.2f} EUR | **{clay.tail_deficit_cvar99_eur:,.2f} EUR** |

Even under the Gaussian benchmark the probability of breaching the covenant is
{gauss.prob_covenant_breach:.1%}, because the deterministic Year-2 DSCR is already
{float(k.iloc[1]['dscr']):.2f}x. The Clayton copula adds lower-tail clustering:
the worst 1% of joint scenarios produce an annual CFADS shortfall of
**{clay.tail_deficit_cvar99_eur:,.2f} EUR**, which is
{clay.tail_deficit_cvar99_eur / self.dsra_contractual:.2f}x the contractual
six-month reserve.

---

## 4. DSRA sizing and liquidity structure

1. **Contractual six-month DSRA:** **{self.dsra_contractual:,.2f} EUR** (half of the
   {self.copula_results.annual_debt_service_y2:,.2f} EUR annual service). It covers
   the standard covenant but not the simulated tail: the unprotected gap is
   **{clay.tail_deficit_cvar99_eur - self.dsra_contractual:,.2f} EUR**.
2. **Tail-tested reserve:** **{self.copula_results.dsra_recommended_tail:,.2f} EUR**,
   equal to the Clayton CVaR 99% annual shortfall. That is
   {self.copula_results.dsra_recommended_tail / self.copula_results.annual_debt_service_y2:.2f}
   years of debt service, far above market practice and a further sign that the
   facility is over-levered.
3. **Monthly liquidity:** the monthly engine shows a seasonal trough in April. In
   the management case, cash falls to roughly EUR 12.0k before a EUR 3.0k draw on
   the committed revolver, repaid by Month 7. The annual model assumes no revolver
   usage, so a committed line is a condition precedent, not an optional extra.

---

## 5. Credit committee decision and conditions

### Decision: {self.recommendation}

The requested {self.senior_principal:,.2f} EUR facility is **not bankable as
structured**. It breaches the 1.25x DSCR covenant in Year 2
({float(k.iloc[1]['dscr']):.2f}x), requires {self.equity_to_capex:.1f}% cash equity
instead of the 30% assumed, and its tail shortfall exceeds a full year of debt
service. Approving it would transfer an identified cash-flow deficit to the
lender.

The facility could be re-submitted on the following terms:

1. **Resize the senior loan to at most {dscr_cap:,.2f} EUR** ({dscr_cap_ltv:.1f}% LTV),
   with the difference funded by additional equity so that sources and uses still
   close at zero.
2. **Equity contribution of at least {self.cash_equity:,.2f} EUR in cash**
   ({self.equity_to_capex:.1f}% of CapEx), plus the land in kind, documented before
   first drawdown.
3. **Covenant headroom:** the base case must clear 1.25x in every year with at
   least 10% headroom. That requires either occupancy above
   {covenant_be:.2%} or an ADR of at least {adr_covenant:,.2f} EUR.
4. **DSRA of {self.dsra_contractual:,.2f} EUR** at close, plus a committed
   {self.financing.credit_line_limit:,.2f} EUR revolver for the seasonal trough, and a
   50% cash sweep while DSCR remains below 1.25x.
5. **LEADER grant assignment:** pledge of the 163,000 EUR receivable to the DSRA,
   with disbursement in Month 14 and no double counting against close-day uses.
6. **Phase II carve-out:** Phase II cannot proceed while Phase I DSCR is below
   1.25x. The phase gate is tested in the expansion module and fails.

If the sponsor is not prepared to inject the additional equity or re-price to an
ADR of at least {adr_covenant:,.2f} EUR, the committee's recommendation is to
**decline** the facility.
"""
        return memo.strip()

    # ------------------------------------------------------------------
    # Terminal summary
    # ------------------------------------------------------------------
    def print_terminal_summary(self) -> None:
        """Prints a concise summary of the credit underwriting memorandum."""
        clay = self.copula_results.clayton
        gauss = self.copula_results.gaussian
        k = self.df_kpis
        ret = self.returns
        project_irr = ret["project_irr_exit"]
        equity_irr = ret["equity_irr_exit"]

        print("=" * 88)
        print(" BANK CREDIT COMMITTEE UNDERWRITING MEMORANDUM (SUMMARY)")
        print("=" * 88)
        print(f" Facility requested:            EUR {self.senior_principal:>14,.2f} "
              f"({self.ltv_pct:.1f}% LTV)")
        print(f" DSCR-capped principal (1.25x): EUR {float(self.debt_sizing['principal_dscr_cap']):>14,.2f} "
              f"({float(self.debt_sizing['implied_ltv_pct']):.1f}% LTV)")
        print(f" Binding constraint:            {self.debt_sizing['binding_constraint']}")
        print(f" Cash equity required:          EUR {self.cash_equity:>14,.2f} "
              f"({self.equity_to_capex:.1f}% of CapEx)")
        print(f" DSCR Year 1 / Year 2 / Year 3: {float(k.iloc[0]['dscr']):.2f}x / "
              f"{float(k.iloc[1]['dscr']):.2f}x / {float(k.iloc[2]['dscr']):.2f}x "
              f"(covenant 1.25x)")
        print(f" Break-even occupancy:          EBITDA 0 at "
              f"{self.breakeven['operating_breakeven_occupancy_mature']:.2%} | "
              f"1.00x at {self.breakeven['debt_service_breakeven_occupancy_mature']:.2%} | "
              f"1.25x at {self.breakeven['covenant_breakeven_occupancy_mature']:.2%}")
        print("-" * 88)
        print(" Multivariate copula tail risk (50,000 draws, Year-2 DSCR):")
        print(f"   Gaussian: mean {gauss.mean_dscr:.2f}x | VaR 99% {gauss.var_99:.2f}x | "
              f"CVaR 99% {gauss.cvar_99:.2f}x | P(breach) {gauss.prob_covenant_breach:.1%}")
        print(f"   Clayton:  mean {clay.mean_dscr:.2f}x | VaR 99% {clay.var_99:.2f}x | "
              f"CVaR 99% {clay.cvar_99:.2f}x | P(breach) {clay.prob_covenant_breach:.1%}")
        print(f"   Clayton CVaR 99% annual shortfall: EUR {clay.tail_deficit_cvar99_eur:,.2f}")
        print("-" * 88)
        print(f" Contractual six-month DSRA:    EUR {self.dsra_contractual:>14,.2f}")
        print(f" Tail-tested DSRA:              EUR {self.copula_results.dsra_recommended_tail:>14,.2f}")
        print(f" Project IRR (8.5% exit):       "
              f"{project_irr * 100:>7.2f}%" if project_irr is not None else
              " Project IRR (8.5% exit):       n/a")
        print(f" Equity IRR (8.5% exit):        "
              f"{equity_irr * 100:>7.2f}%" if equity_irr is not None else
              " Equity IRR (8.5% exit):        n/a")
        print("-" * 88)
        print(f" RECOMMENDATION: {self.recommendation}")
        print("=" * 88)
