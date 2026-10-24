"""
Sources & Uses, funding-gap and phase-gate analysis.

This module makes the funding structure explicit. The original Python engine
booked a VAT bridge equal to the net VAT refund and treated the LEADER grant
as a Year-2 inflow, but it did not show:

1. The close-day cash uses: pre-opening costs, opening working capital and the
   debt service reserve account (DSRA).
2. The difference between the stated €50,000 credit line and the €143,596 VAT
   bridge actually drawn by the model.
3. That the LEADER grant and the VAT refund are already committed in Phase I
   and cannot be spent again on Phase II.

The result is a transparent funding gap and a phase-gate recommendation.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    SCENARIOS,
    ScenarioDrivers,
)
from src.core.metrics import CreditMetricsEngine
from src.core.statements import FinancialModelEngine


@dataclass
class SourcesUsesResult:
    case: str
    # Uses at close
    capex_net: float
    input_vat: float
    pre_opening_costs: float
    initial_working_capital: float
    dsra: float
    total_uses_at_close: float
    # Sources at close
    senior_debt: float
    sponsor_equity: float
    vat_bridge: float
    credit_line_at_close: float
    total_sources_at_close: float
    # Post-close sources
    leader_grant: float
    total_sources_post_close: float
    # Gaps
    funding_gap_at_close: float
    funding_gap_total: float
    recommended_equity_injection: float
    recommended_debt_increase: float
    # Credit consistency
    credit_line_limit: float
    vat_bridge_limit: float
    vat_bridge_excess: float
    credit_line_utilisation_pct: float
    model_credit_line_drawn_y1: float
    # Operating metrics
    dscr_y1: float
    dscr_y3: float
    cash_y1_model: float
    cash_y2_model: float
    cash_y1_adjusted: float
    cash_y2_adjusted: float
    minimum_adjusted_cash: float
    funding_status: str
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SourcesUsesEngine:
    """Computes a transparent sources & uses table for a given calibration case."""

    def __init__(
        self,
        case: str = "management",
        scenario: Optional[ScenarioDrivers] = None,
        capex: Optional[CapExStructure] = None,
        financing: Optional[FinancingStructure] = None,
    ):
        self.case = case
        self.scenario = scenario or SCENARIOS["base"]
        self.engine = FinancialModelEngine(
            case=case,
            scenario=self.scenario,
            capex=capex,
            financing=financing,
        )
        self.capex = self.engine.capex
        self.financing = self.engine.financing
        self.df = self.engine.run_projection(projection_years=5)
        self.debt_sched = self.engine.debt_engine.get_annual_schedule_df()
        self.credit = CreditMetricsEngine(target_dscr=self.financing.target_dscr)
        self.df_kpi = self.credit.compute_credit_kpis(self.df, self.debt_sched)

    def compute(self) -> SourcesUsesResult:
        capex_net = float(self.capex.total_capex)
        input_vat = float(self.capex.total_input_vat)
        pre_opening = float(self.financing.pre_opening_costs)
        initial_wc = float(self.financing.initial_working_capital)

        # Six months of senior debt service as the DSRA.
        annual_debt_service = float(self.debt_sched.iloc[0]["payment"])
        dsra = round(annual_debt_service * self.financing.dsra_months / 12.0, 2)

        total_uses = round(capex_net + input_vat + pre_opening + initial_wc + dsra, 2)

        senior_debt = float(self.financing.senior_debt_principal)
        sponsor_equity = float(self.financing.sponsor_equity)
        # The bridge is sized on the gross input VAT, not on the net refund.
        vat_bridge = round(input_vat, 2)
        credit_line_at_close = float(self.financing.initial_credit_line_draw)
        total_sources_close = round(
            senior_debt + sponsor_equity + vat_bridge + credit_line_at_close, 2
        )

        leader_grant = float(self.financing.leader_subsidy_amount)
        total_sources_post = round(total_sources_close + leader_grant, 2)

        gap_close = round(total_sources_close - total_uses, 2)
        gap_total = round(total_sources_post - total_uses, 2)

        recommended_equity = round(max(0.0, -gap_close), 2)
        recommended_debt = 0.0

        vat_bridge_excess = round(max(0.0, vat_bridge - self.financing.vat_bridge_limit), 2)
        # The model's Y1 credit-line line item includes the VAT bridge.
        model_bridge_y1 = float(self.df.iloc[0]["credit_line_drawn"])
        credit_utilisation = (
            round(model_bridge_y1 / self.financing.credit_line_limit * 100.0, 2)
            if self.financing.credit_line_limit > 0 else 0.0
        )

        y1 = self.df_kpi.iloc[0]
        y3 = self.df_kpi.iloc[2]
        cash_y1 = float(y1["ending_cash"])
        cash_y2 = float(self.df_kpi.iloc[1]["ending_cash"])

        # The model's cash flow does not include the close-day uses. Adjust it.
        cash_y1_adj = round(cash_y1 - pre_opening - initial_wc - dsra, 2)
        cash_y2_adj = round(cash_y2 - pre_opening - initial_wc - dsra, 2)
        min_adj = min(cash_y1_adj, cash_y2_adj)

        if gap_close < 0:
            status = "UNDERFUNDED - additional equity required at close"
        elif cash_y1_adj < 0:
            status = "LIQUIDITY GAP - close-day funding covered but Year 1 cash negative"
        else:
            status = "FUNDED - close-day and Year 1 liquidity covered"

        notes = (
            "The VAT bridge is a real financing source, but it is separate from the "
            "€50,000 revolving credit line. The LEADER grant is a post-close inflow "
            "(Month 14) and cannot fund close-day uses. The DSRA, pre-opening and "
            "working-capital lines were omitted from the original Python cash flow."
        )

        return SourcesUsesResult(
            case=self.case,
            capex_net=capex_net,
            input_vat=input_vat,
            pre_opening_costs=pre_opening,
            initial_working_capital=initial_wc,
            dsra=dsra,
            total_uses_at_close=total_uses,
            senior_debt=senior_debt,
            sponsor_equity=sponsor_equity,
            vat_bridge=vat_bridge,
            credit_line_at_close=credit_line_at_close,
            total_sources_at_close=total_sources_close,
            leader_grant=leader_grant,
            total_sources_post_close=total_sources_post,
            funding_gap_at_close=gap_close,
            funding_gap_total=gap_total,
            recommended_equity_injection=recommended_equity,
            recommended_debt_increase=recommended_debt,
            credit_line_limit=float(self.financing.credit_line_limit),
            vat_bridge_limit=float(self.financing.vat_bridge_limit),
            vat_bridge_excess=vat_bridge_excess,
            credit_line_utilisation_pct=credit_utilisation,
            model_credit_line_drawn_y1=model_bridge_y1,
            dscr_y1=float(y1["dscr"]),
            dscr_y3=float(y3["dscr"]),
            cash_y1_model=cash_y1,
            cash_y2_model=cash_y2,
            cash_y1_adjusted=cash_y1_adj,
            cash_y2_adjusted=cash_y2_adj,
            minimum_adjusted_cash=min_adj,
            funding_status=status,
            notes=notes,
        )

    def phase_gate(self, phase2_capex_net: float, phase2_vat: float = 0.0) -> Dict[str, Any]:
        """
        Phase-gate test for Phase II. Phase II may only proceed if:
        - Phase I Year-3 DSCR >= 1.25x (covenant compliance), and
        - Phase I available cash at the end of Year 2 covers the Phase II cash need.
        """
        cash_available = float(self.df_kpi.iloc[1]["ending_cash"])
        cash_need = round(phase2_capex_net + phase2_vat, 2)
        gap = round(cash_available - cash_need, 2)
        dscr_ok = float(self.df_kpi.iloc[2]["dscr"]) >= self.financing.target_dscr
        cash_ok = gap >= 0
        return {
            "case": self.case,
            "phase1_dscr_y3": float(self.df_kpi.iloc[2]["dscr"]),
            "phase1_cash_end_y2": cash_available,
            "phase2_cash_need": cash_need,
            "phase2_funding_gap": gap,
            "dscr_condition_met": dscr_ok,
            "cash_condition_met": cash_ok,
            "phase2_proceed": bool(dscr_ok and cash_ok),
            "recommendation": (
                "PROCEED - Phase I covenants and cash cover Phase II"
                if dscr_ok and cash_ok
                else "DO NOT PROCEED - Phase II requires additional funding or a smaller scope"
            ),
        }

    def print_terminal_summary(self) -> None:
        r = self.compute()
        print("=" * 88)
        print(f" SOURCES & USES / FUNDING GAP - {r.case.upper()} CASE")
        print("=" * 88)
        print("USES AT CLOSE:")
        print(f"  CapEx (net of VAT)              €{r.capex_net:>14,.2f}")
        print(f"  Input VAT (21%)                 €{r.input_vat:>14,.2f}")
        print(f"  Pre-opening costs               €{r.pre_opening_costs:>14,.2f}")
        print(f"  Initial working capital         €{r.initial_working_capital:>14,.2f}")
        print(f"  DSRA (6 months debt service)    €{r.dsra:>14,.2f}")
        print(f"  TOTAL USES                      €{r.total_uses_at_close:>14,.2f}")
        print("SOURCES AT CLOSE:")
        print(f"  Senior debt                     €{r.senior_debt:>14,.2f}")
        print(f"  Sponsor equity                  €{r.sponsor_equity:>14,.2f}")
        print(f"  VAT refund bridge               €{r.vat_bridge:>14,.2f}")
        print(f"  Credit line drawn at close      €{r.credit_line_at_close:>14,.2f}")
        print(f"  TOTAL SOURCES                   €{r.total_sources_at_close:>14,.2f}")
        print(f"  LEADER grant (Month 14, post-close) €{r.leader_grant:>10,.2f}")
        print(f"  TOTAL SOURCES INCLUDING GRANT   €{r.total_sources_post_close:>14,.2f}")
        print("-" * 88)
        print(f"  FUNDING GAP AT CLOSE            €{r.funding_gap_at_close:>14,.2f}")
        print(f"  FUNDING GAP INCLUDING GRANT     €{r.funding_gap_total:>14,.2f}")
        print(f"  Recommended equity injection    €{r.recommended_equity_injection:>14,.2f}")
        print(f"  Model Year-1 cash               €{r.cash_y1_model:>14,.2f}")
        print(f"  Adjusted Year-1 cash (with omitted uses) €{r.cash_y1_adjusted:>8,.2f}")
        print(f"  Status: {r.funding_status}")
        print("=" * 88)


if __name__ == "__main__":
    for case in ("management", "market", "promoter"):
        SourcesUsesEngine(case=case).print_terminal_summary()
        print()
