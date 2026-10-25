"""
Sources & Uses, funding-gap and phase-gate analysis.

The engine now books the close-day uses directly in the three-statement model
(IDC, pre-opening costs, opening working capital, DSRA and the VAT bridge), so
this module reconciles the *funded* capital structure rather than adding an
off-model adjustment:

1. Total uses at close = CapEx (land in kind + cash works) + IDC + input VAT +
   pre-opening + working capital + DSRA + operating cash buffer.
2. Total sources at close = senior debt (35% LTV) + VAT bridge + land in kind +
   cash equity. The cash equity is the plug that closes the structure; it is
   reported, not assumed, so the 30% equity assumption is tested rather than
   asserted.
3. The DSRA is sized on six months of the maximum annual senior debt service.
4. The phase gate tests whether Phase I cash can fund Phase II without
   double-counting the LEADER grant or the VAT refund.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    SCENARIOS,
    ScenarioDrivers,
)
from src.core.metrics import CreditMetricsEngine
from src.core.statements import FinancialModelEngine

PROJECTION_YEARS = 5


@dataclass
class SourcesUsesResult:
    case: str

    # Uses at close
    total_capex: float
    land_in_kind: float
    cash_capex: float
    input_vat: float
    idc: float
    pre_opening_costs: float
    initial_working_capital: float
    dsra: float
    operating_cash_buffer: float
    total_uses_at_close: float

    # Sources at close
    senior_debt: float
    vat_bridge: float
    credit_line_at_close: float
    base_cash_equity: float
    cash_equity_required: float
    cash_equity_buffer: float
    total_sources_at_close: float

    # Post-close sources
    leader_grant: float
    total_sources_post_close: float

    # Reconciliation
    funding_gap_at_close: float
    funding_gap_total: float
    recommended_equity_injection: float
    equity_to_capex_pct: float
    ltv_pct: float
    total_equity_at_close: float
    total_project_investment: float

    # Debt sizing
    dscr_cap_principal: float
    binding_constraint: str
    dscr_cap_ltv_pct: float

    # Credit consistency
    credit_line_limit: float
    vat_bridge_limit: float
    vat_bridge_excess: float
    credit_line_utilisation_pct: float
    vat_bridge_drawn_y1: float
    model_credit_line_drawn_y1: float

    # Operating metrics
    dscr_y1: float
    dscr_min: float
    dscr_by_year: List[float]
    cfads_by_year: List[float]
    cash_by_year: List[float]
    min_cash: float
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
        self.df = self.engine.run_projection(projection_years=PROJECTION_YEARS)
        self.debt_sched = self.engine.debt_engine.get_annual_schedule_df()
        self.credit = CreditMetricsEngine(target_dscr=self.financing.target_dscr)
        self.df_kpi = self.credit.compute_credit_kpis(self.df, self.debt_sched)

    def compute(self) -> SourcesUsesResult:
        su = self.engine.sources_uses_at_close()
        uses = su["uses"]
        sources = su["sources"]

        total_uses = float(uses["total_uses"])
        total_sources = float(sources["total_sources"])
        gap = round(total_sources - total_uses, 2)

        input_vat = float(self.capex.total_input_vat)
        vat_bridge = float(sources["vat_bridge"])
        vat_bridge_excess = round(
            max(0.0, vat_bridge - self.financing.vat_bridge_limit), 2
        )

        # The model's Year-1 bridge line is the VAT bridge (the revolving line
        # is undrawn at close in the management and market cases).
        model_bridge_y1 = float(self.df.iloc[0]["credit_line_drawn"])
        credit_utilisation = (
            round(model_bridge_y1 / self.financing.credit_line_limit * 100.0, 2)
            if self.financing.credit_line_limit > 0 else 0.0
        )

        dscr_by_year = [
            round(float(cfads) / float(ds), 2) if ds else 999.0
            for cfads, ds in zip(self.df["cfads"], self.df["debt_service"])
        ]
        cash_by_year = [round(float(c), 2) for c in self.df["ending_cash"]]

        if gap < -0.01:
            status = "UNDERFUNDED - additional equity required at close"
        elif min(cash_by_year) < 0:
            status = "LIQUIDITY GAP - cash turns negative during the projection"
        elif min(dscr_by_year) < self.financing.critical_dscr:
            status = "FUNDED BUT BELOW 1.00x DSCR - sponsor support required"
        else:
            status = "FUNDED - sources & uses close and cash stays positive"

        if self.case == "promoter":
            notes = (
                "The promoter case is a re-modelling, not a replication: 86,275 is its own "
                "revenue construct and 11,297 is the deck literal, on the original "
                "financing structure: EUR 507,500 of senior debt (70% LTV) at 4.5% over 25 years, "
                "no grace period, no LEADER grant and land purchased rather than contributed in "
                "kind. It is not a replication of the source workbooks (README section 2). The "
                "EUR 99,750 input VAT exceeds the EUR 20,000 line, so the close-day structure "
                "shows a EUR 20,000 gap and Year 1 cash turns negative."
            )
        elif self.case == "market":
            notes = (
                "The requested EUR 367,535 facility is 35% of the all-in asset cost, but Year 1 "
                "CFADS is negative at the official INE 21.24% occupancy, so no amount of debt can "
                "satisfy a 1.25x DSCR. The cash equity plug also absorbs a EUR 35,374.83 operating "
                "buffer. The land is contributed in kind and the VAT bridge is repaid with the AEAT "
                "refund in Month 18; the LEADER grant is a post-close inflow (Month 14)."
            )
        else:
            notes = (
                "The requested EUR 367,535 facility is 35% of the all-in asset cost, but the binding "
                "DSCR constraint caps debt at EUR 339,144.92 (32.3% LTV) at 1.25x CFADS. The senior "
                "facility as requested breaches the covenant in Year 2 (1.15x). The land is "
                "contributed in kind and the cash equity line is the plug that closes the structure. "
                "The VAT bridge is repaid with the AEAT refund in Month 18; the LEADER grant is a "
                "post-close inflow (Month 14) that cannot fund close-day uses."
            )
        sizing = self.engine.debt_sizing()

        return SourcesUsesResult(
            case=self.case,
            total_capex=float(self.capex.total_capex),
            land_in_kind=float(uses["land_in_kind"]),
            cash_capex=float(uses["cash_capex"]),
            input_vat=input_vat,
            idc=float(uses["idc"]),
            pre_opening_costs=float(uses["pre_opening_costs"]),
            initial_working_capital=float(uses["initial_working_capital"]),
            dsra=float(uses["dsra"]),
            operating_cash_buffer=float(uses["operating_cash_buffer"]),
            total_uses_at_close=total_uses,
            senior_debt=float(sources["senior_debt"]),
            vat_bridge=vat_bridge,
            credit_line_at_close=float(sources["credit_line"]),
            base_cash_equity=float(self.engine.base_cash_equity),
            cash_equity_required=round(float(sources["cash_equity"]), 2),
            cash_equity_buffer=round(self.engine.cash_equity_buffer, 2),
            total_sources_at_close=total_sources,
            leader_grant=float(self.financing.leader_subsidy_amount),
            total_sources_post_close=round(
                total_sources + float(self.financing.leader_subsidy_amount), 2
            ),
            funding_gap_at_close=gap,
            funding_gap_total=round(
                total_sources
                + float(self.financing.leader_subsidy_amount)
                - total_uses,
                2,
            ),
            recommended_equity_injection=round(max(0.0, -gap), 2),
            equity_to_capex_pct=(
                round(self.engine.cash_equity / self.capex.total_capex * 100.0, 2)
                if self.capex.total_capex else 0.0
            ),
            ltv_pct=(
                round(self.financing.senior_debt_principal / self.capex.total_capex * 100.0, 2)
                if self.capex.total_capex else 0.0
            ),
            total_equity_at_close=float(self.engine.total_equity_at_close),
            total_project_investment=float(self.engine.total_project_investment),
            dscr_cap_principal=float(sizing["principal_dscr_cap"]),
            binding_constraint=str(sizing["binding_constraint"]),
            dscr_cap_ltv_pct=float(sizing["implied_ltv_pct"]),
            credit_line_limit=float(self.financing.credit_line_limit),
            vat_bridge_limit=float(self.financing.vat_bridge_limit),
            vat_bridge_excess=vat_bridge_excess,
            credit_line_utilisation_pct=credit_utilisation,
            vat_bridge_drawn_y1=model_bridge_y1,
            model_credit_line_drawn_y1=model_bridge_y1,
            dscr_y1=dscr_by_year[0],
            dscr_min=min(dscr_by_year),
            dscr_by_year=dscr_by_year,
            cfads_by_year=[round(float(c), 2) for c in self.df["cfads"]],
            cash_by_year=cash_by_year,
            min_cash=min(cash_by_year),
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
        print(f" SOURCES & USES / FUNDING TEST - {r.case.upper()} CASE")
        print("=" * 88)
        print("USES AT CLOSE:")
        print(f"  Land contributed in kind       €{r.land_in_kind:>14,.2f}")
        print(f"  Cash CapEx (works, FF&E, fees) €{r.cash_capex:>14,.2f}")
        print(f"  Interest during construction   €{r.idc:>14,.2f}")
        print(f"  Input VAT (21%, bridge-funded) €{r.input_vat:>14,.2f}")
        print(f"  Pre-opening costs              €{r.pre_opening_costs:>14,.2f}")
        print(f"  Initial working capital        €{r.initial_working_capital:>14,.2f}")
        print(f"  DSRA (6 months debt service)   €{r.dsra:>14,.2f}")
        print(f"  Operating cash buffer          €{r.operating_cash_buffer:>14,.2f}")
        print(f"  TOTAL USES                     €{r.total_uses_at_close:>14,.2f}")
        print("SOURCES AT CLOSE:")
        print(f"  Senior debt (35% LTV)          €{r.senior_debt:>14,.2f}")
        print(f"  VAT refund bridge              €{r.vat_bridge:>14,.2f}")
        print(f"  Credit line drawn              €{r.credit_line_at_close:>14,.2f}")
        print(f"  Land in kind                   €{r.land_in_kind:>14,.2f}")
        print(f"  Cash equity (required)         €{r.cash_equity_required:>14,.2f}")
        print(f"  TOTAL SOURCES                  €{r.total_sources_at_close:>14,.2f}")
        print(f"  LEADER grant (Month 14, post-close) €{r.leader_grant:>10,.2f}")
        print("-" * 88)
        print(f"  RECONCILIATION GAP             €{r.funding_gap_at_close:>14,.2f}")
        print(f"  Cash equity / total CapEx      {r.equity_to_capex_pct:>13.2f}%")
        print(f"  Senior debt / total CapEx      {r.ltv_pct:>13.2f}%")
        print(f"  Minimum DSCR (Years 1-5)       {r.dscr_min:>13.2f}x")
        print(f"  Minimum cash (Years 1-5)       €{r.min_cash:>14,.2f}")
        print(f"  DSCR-capped principal (1.25x)  €{r.dscr_cap_principal:>14,.2f} ({r.dscr_cap_ltv_pct:.1f}% LTV)")
        print(f"  Binding constraint:            {r.binding_constraint}")
        print(f"  Status: {r.funding_status}")
        print("=" * 88)


if __name__ == "__main__":
    for case in ("management", "market", "promoter"):
        SourcesUsesEngine(case=case).print_terminal_summary()
        print()
