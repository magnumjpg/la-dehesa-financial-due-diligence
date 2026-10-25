"""
Reform / resize case analysis.

This module sits *on top of* the as-is model. It does not change the three
original cases; it asks the question a credit committee asks after a decline:

    "What would have to be true for a reform of the asset to create value?"

The answer is deliberately allowed to be "nothing credible". The engine
computes, for each reform configuration:

* the five-year integrated P&L, cash flow and balance sheet (same engine as
  the as-is cases);
* DSCR, ICR, project/equity IRR, NPV and MOIC;
* the cap-rate enterprise value and the value gap versus both CapEx and total
  project investment;
* the incremental-EBITDA value bridge (external F&B, experiences, ADR, cost
  savings);
* a CapEx / external-cover frontier and a set of stress cases.

The two value-gap metrics are shown side by side because they answer different
questions. EV vs CapEx is the asset-value test; EV vs total project investment
also charges the project for IDC, pre-opening, working capital and the DSRA.
The latter is the conservative, bank-facing test.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from src.config.assumptions import SCENARIOS, ScenarioDrivers
from src.config.ine_weights import MANAGEMENT_OCCUPANCY
from src.config.reform import (
    CABIN_PRESETS,
    REFORM_PRESETS,
    ReformConfig,
    get_cabin_preset,
    get_reform_preset,
)
from src.core.metrics import CreditMetricsEngine
from src.core.statements import FinancialModelEngine


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ReformCaseResult:
    key: str
    name: str
    thesis: str

    # Capital structure
    capex: float
    non_land_capex: float
    total_project_investment: float
    senior_debt: float
    cash_equity: float
    total_equity: float
    leader_subsidy: float

    # Operating profile
    revenue_y1: float
    revenue_y5: float
    ebitda_y1: float
    ebitda_y5: float
    ebitda_margin_y5: float
    external_covers_y5: float
    external_fnb_revenue_y5: float
    experiences_revenue_y5: float
    incremental_payroll_y5: float
    cost_savings_y5: float

    # Credit
    dscr_y1: float
    dscr_y2: float
    dscr_y3: float
    dscr_y5: float
    dscr_min: float
    ending_cash_y1: float
    ending_cash_y5: float

    # Value
    exit_cap_rate: float
    discount_rate: float
    terminal_value: float
    ev_cap_rate: float
    value_gap_capex: float
    value_gap_total_investment: float
    exit_cost_rate: float
    exit_costs: float
    net_exit_value: float
    net_value_gap_capex: float
    net_value_gap_total_investment: float
    required_ebitda_capex: float
    required_ebitda_total_investment: float

    # Returns
    project_irr_exit: Optional[float]
    equity_irr_exit: Optional[float]
    project_npv: float
    equity_npv: float
    project_moic: Optional[float]
    equity_moic: Optional[float]

    balance_sheet_discrepancy: float

    @property
    def clears_wacc(self) -> bool:
        return self.project_npv > 0.0

    @property
    def clears_total_investment(self) -> bool:
        return self.value_gap_total_investment > 0.0

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Analysis engine
# ---------------------------------------------------------------------------
class ReformAnalysisEngine:
    """Runs the reform presets, value bridge, frontier and stress cases."""

    def __init__(self, projection_years: int = 5):
        self.projection_years = projection_years
        self._cache: Dict[Tuple[ReformConfig, ScenarioDrivers], ReformCaseResult] = {}

    # ------------------------------------------------------------------
    # Core runner
    # ------------------------------------------------------------------
    def run_config(
        self,
        config: ReformConfig,
        scenario: Optional[ScenarioDrivers] = None,
        key: Optional[str] = None,
    ) -> ReformCaseResult:
        scenario = scenario or SCENARIOS["base"]
        if config.demand_anchor is not None:
            # Pin the reform to its own demand anchor instead of the inherited
            # management occupancy. R6 uses this to be a genuine INE-demand
            # downside; every other preset leaves it as None.
            scenario = replace(
                scenario,
                occupancy_multiplier=config.demand_anchor / MANAGEMENT_OCCUPANCY,
            )
        cache_key = (config, scenario)
        if cache_key in self._cache:
            return self._cache[cache_key]

        engine = FinancialModelEngine(
            case="reform",
            reform=config,
            scenario=scenario,
        )
        df = engine.run_projection(self.projection_years)
        debt_schedule = engine.debt_engine.get_annual_schedule_df()
        credit = CreditMetricsEngine(
            target_dscr=1.25,
            discount_wacc=config.discount_rate,
        )
        kpi = credit.compute_credit_kpis(df, debt_schedule)
        returns = credit.compute_returns_summary(
            kpi,
            initial_equity=engine.total_equity_at_close,
            initial_capex=engine.total_project_investment,
            exit_cap_rate=config.exit_cap_rate,
        )

        y1 = kpi.iloc[0]
        y5 = kpi.iloc[-1]
        terminal_ebitda = float(y5["ebitda"])
        # A negative-EBITDA asset is not worth a negative amount: the cap-rate
        # value is floored at zero and the downside is carried in the cash
        # flows, not in a fictional negative enterprise value.
        ev = max(terminal_ebitda, 0.0) / config.exit_cap_rate
        exit_costs = round(ev * config.exit_cost_rate, 2)
        net_ev = round(ev - exit_costs, 2)
        total_investment = float(engine.total_project_investment)

        result = ReformCaseResult(
            key=key or config.name,
            name=config.name,
            thesis=config.thesis,
            capex=float(config.total_capex),
            non_land_capex=float(config.non_land_capex),
            total_project_investment=total_investment,
            senior_debt=float(engine.financing.senior_debt_principal),
            cash_equity=float(engine.cash_equity),
            total_equity=float(engine.total_equity_at_close),
            leader_subsidy=float(engine.financing.leader_subsidy_amount),
            revenue_y1=float(y1["total_revenue"]),
            revenue_y5=float(y5["total_revenue"]),
            ebitda_y1=float(y1["ebitda"]),
            ebitda_y5=terminal_ebitda,
            ebitda_margin_y5=(
                float(y5["ebitda"]) / float(y5["total_revenue"])
                if float(y5["total_revenue"]) > 0
                else 0.0
            ),
            external_covers_y5=float(y5.get("external_covers", 0.0)),
            external_fnb_revenue_y5=float(y5.get("revenue_external_fnb", 0.0)),
            experiences_revenue_y5=float(y5.get("revenue_experiences", 0.0)),
            incremental_payroll_y5=float(y5.get("incremental_payroll", 0.0)),
            cost_savings_y5=float(y5.get("cost_savings", 0.0)),
            dscr_y1=float(y1["dscr"]),
            dscr_y2=float(kpi.iloc[1]["dscr"]),
            dscr_y3=float(kpi.iloc[2]["dscr"]),
            dscr_y5=float(y5["dscr"]),
            dscr_min=float(kpi["dscr"].min()),
            ending_cash_y1=float(y1["ending_cash"]),
            ending_cash_y5=float(y5["ending_cash"]),
            exit_cap_rate=float(config.exit_cap_rate),
            discount_rate=float(config.discount_rate),
            terminal_value=float(returns["terminal_value"]),
            ev_cap_rate=round(ev, 2),
            value_gap_capex=round(ev - config.total_capex, 2),
            value_gap_total_investment=round(ev - total_investment, 2),
            exit_cost_rate=float(config.exit_cost_rate),
            exit_costs=exit_costs,
            net_exit_value=net_ev,
            net_value_gap_capex=round(net_ev - config.total_capex, 2),
            net_value_gap_total_investment=round(net_ev - total_investment, 2),
            required_ebitda_capex=round(config.total_capex * config.exit_cap_rate, 2),
            required_ebitda_total_investment=round(
                total_investment * config.exit_cap_rate, 2
            ),
            project_irr_exit=returns["project_irr_exit"],
            equity_irr_exit=returns["equity_irr_exit"],
            project_npv=float(returns["project_npv"]),
            equity_npv=float(returns["equity_npv"]),
            project_moic=returns["project_moic"],
            equity_moic=returns["equity_moic"],
            balance_sheet_discrepancy=float(
                df["balance_sheet_discrepancy"].abs().max()
            ),
        )
        self._cache[cache_key] = result
        return result

    def run_presets(self) -> pd.DataFrame:
        rows = []
        for key, config in REFORM_PRESETS.items():
            result = self.run_config(config, key=key)
            row = result.as_dict()
            row["clears_wacc"] = result.clears_wacc
            row["clears_total_investment"] = result.clears_total_investment
            rows.append(row)
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # R7: premium cabins, a different product
    # ------------------------------------------------------------------
    def run_cabin_presets(self) -> pd.DataFrame:
        rows = []
        for key, config in CABIN_PRESETS.items():
            result = self.run_config(config, key=key)
            row = result.as_dict()
            row["clears_wacc"] = result.clears_wacc
            row["clears_total_investment"] = result.clears_total_investment
            row["cabin_count"] = config.cabin_count
            row["cabin_adr"] = config.cabin_adr
            row["cabin_capex_per_unit"] = config.cabin_capex_per_unit
            row["cabin_occupancy_mature"] = config.cabin_occupancy_mature
            rows.append(row)
        return pd.DataFrame(rows)

    def cabin_cost_ladder(
        self,
        costs: Iterable[float] = (110_000, 120_000, 130_000, 150_000, 180_000),
        base_config: Optional[ReformConfig] = None,
    ) -> pd.DataFrame:
        """
        Value gap by all-in cost per cabin, holding demand constant.

        This is the R7 equivalent of the hotel frontier: it isolates the one
        variable that separates a pass from a fail when the demand band is
        already at the top of what Segovia supports.
        """
        base_config = base_config or get_cabin_preset("cabins_base")
        rows = []
        for cost in costs:
            result = self.run_config(
                base_config.with_cabin_cost(float(cost)), key=f"cabin_cost_{cost}"
            )
            rows.append(
                {
                    "cost_per_cabin": float(cost),
                    "capex": result.capex,
                    "total_investment": result.total_project_investment,
                    "ebitda_y5": result.ebitda_y5,
                    "ev_cap_rate": result.ev_cap_rate,
                    "gap_capex": result.value_gap_capex,
                    "gap_total_investment": result.value_gap_total_investment,
                    "net_gap_total_investment": result.net_value_gap_total_investment,
                    "dscr_min": result.dscr_min,
                    "project_npv": result.project_npv,
                    "clears_wacc": result.clears_wacc,
                    "clears_total_investment": result.clears_total_investment,
                    # The bank-facing test is the *net* gap versus total
                    # investment. The gross property above is kept for the
                    # asset-value test, but the ladder verdict uses this one.
                    "passes_net_test": result.net_value_gap_total_investment > 0.0,
                }
            )
        return pd.DataFrame(rows)

    def cabin_recommendation(self) -> Dict[str, Any]:
        results = {
            key: self.run_config(config, key=key)
            for key, config in CABIN_PRESETS.items()
        }
        base = results["cabins_base"]
        stretch = results["cabins_stretch"]
        downside = results["cabins_downside"]
        ladder = self.cabin_cost_ladder()

        passes_net = base.net_value_gap_total_investment > 0.0
        passes_wacc = base.clears_wacc
        if passes_net and passes_wacc:
            verdict = (
                "CONDITIONAL PROCEED TO PHASE 0 - PREMIUM CABINS PASS ON PAPER, "
                "BUT ONLY AT 110K PER CABIN"
            )
            stance = "phase_zero"
        elif passes_net or passes_wacc:
            verdict = (
                "CONDITIONAL - THE CABIN CASE CLEARS ONE TEST BUT NOT THE NET "
                "TOTAL-INVESTMENT TEST"
            )
            stance = "boundary"
        else:
            verdict = "DECLINE - THE PREMIUM CABIN CASE DOES NOT CLEAR THE HURDLE"
            stance = "decline"

        detail = (
            f"The base cabin case (six two-bedroom cabins, 200 EUR ADR, 50% "
            f"occupancy, ten external covers, 45k of experiences) produces "
            f"EUR {base.ebitda_y5:,.0f} of mature EBITDA and "
            f"EUR {base.ev_cap_rate:,.0f} of enterprise value at a "
            f"{base.exit_cap_rate*100:.1f}% cap rate. Against total investment "
            f"of EUR {base.total_project_investment:,.0f} that is a net gap of "
            f"EUR {base.net_value_gap_total_investment:+,.0f} after "
            f"{base.exit_cost_rate*100:.1f}% selling costs: it passes, but by "
            f"roughly {base.net_value_gap_total_investment/base.total_project_investment*100:.1f}% "
            f"of the capital at risk. The project NPV is "
            f"EUR {base.project_npv:+,.0f}, the project IRR "
            f"{(base.project_irr_exit or 0)*100:.2f}% and the minimum DSCR "
            f"{base.dscr_min:.2f}x."
        )
        detail_2 = (
            f"The corridor is narrow. At 120k per cabin the same demand fails "
            f"the net total-investment test, and at 150k it only works if the ADR "
            f"moves to 230 EUR and occupancy to 55% (the stretch case: EBITDA "
            f"EUR {stretch.ebitda_y5:,.0f}, net gap "
            f"EUR {stretch.net_value_gap_total_investment:+,.0f}). The "
            f"180k ultra-luxury unit fails with the demand this market pays. "
            f"The downside (five cabins, 190 EUR, 45% occupancy) produces "
            f"EBITDA EUR {downside.ebitda_y5:,.0f}, a minimum DSCR of "
            f"{downside.dscr_min:.2f}x and a net gap of "
            f"EUR {downside.net_value_gap_total_investment:+,.0f}: it is a "
            f"demand failure, not a construction-cost problem."
        )
        conditions = [
            "Run the Phase 0 demand test before committing construction capital: two cabins plus the house for one season, or a restaurant/experience pop-up. The gates are 45% occupancy, 190 EUR realised ADR, eight external covers a day and 25k of experiences.",
            "Keep the all-in cabin cost at or below 110k. At 120k the same demand band fails the net total-investment test; at 130k or more the gap is negative.",
            "Do not budget the 180k ultra-luxury unit. It only works at 250 EUR ADR or more, which the Segovia comparables do not support.",
            "Treat the 45k of agronomic experiences as an operating programme with a host, a calendar and marketing, not as passive income.",
            "Charge the land at its 250k opportunity value; the case does not pass by treating the site as free.",
        ]
        return {
            "verdict": verdict,
            "stance": stance,
            "detail": detail,
            "detail_2": detail_2,
            "conditions": conditions,
            "results": results,
            "cost_ladder": ladder,
        }

    # ------------------------------------------------------------------
    # R7: robustness, valuation cross-checks and the distress playbook
    # ------------------------------------------------------------------
    def cost_inflation_stress(
        self,
        base_config: Optional[ReformConfig] = None,
        rates: Iterable[float] = (0.0, 0.02, 0.025, 0.03),
    ) -> pd.DataFrame:
        """
        Margin squeeze from real cost inflation with flat real prices.

        The reform layer is modelled in constant 2026 euros. This stress
        breaks the symmetry on purpose: payroll and fixed OPEX grow in real
        terms while ADR and occupancy stay at the base case. It is not a
        forecast; it is the answer to "what if price power is weaker than
        cost inflation?".
        """
        base_config = base_config or get_cabin_preset("cabins_base")
        rows = []
        for rate in rates:
            config = replace(base_config, cost_inflation_rate=float(rate))
            result = self.run_config(
                config, key=f"cabin_cost_inflation_{float(rate):.3f}"
            )
            rows.append(
                {
                    "cost_inflation": float(rate),
                    "revenue_y5": result.revenue_y5,
                    "opex_y5": round(result.revenue_y5 - result.ebitda_y5, 2),
                    "ebitda_y5": result.ebitda_y5,
                    "ebitda_margin_y5": round(result.ebitda_margin_y5, 4),
                    "dscr_min": result.dscr_min,
                    "dscr_y5": result.dscr_y5,
                    "ev_cap_rate": result.ev_cap_rate,
                    "net_gap_total_investment": result.net_value_gap_total_investment,
                    "project_npv": result.project_npv,
                    "project_irr_exit": result.project_irr_exit,
                    "passes_net_test": result.net_value_gap_total_investment > 0.0,
                }
            )
        return pd.DataFrame(rows)

    def valuation_cross_check(
        self,
        config: Optional[ReformConfig] = None,
        multiples: Iterable[float] = (9.0, 10.5, 12.0),
    ) -> Dict[str, Any]:
        """
        Three independent reads of the same asset value.

        1. The exit cap rate used in the base case (EBITDA / cap).
        2. The implied exit multiple (1 / cap) and a multiple table.
        3. The development yield on cost, the break-even exit cap and the
           no-compression case.

        A development profit exists when the yield on cost exceeds the exit
        cap: the asset is built at 10.1% and sold at 9.5%. That spread is the
        value gap, so the case depends on the exit cap staying below the
        yield on cost. At no compression the net gap is just the exit costs.
        """
        config = config or get_cabin_preset("cabins_base")
        base = self.run_config(config, key="valuation_cross_check")
        ebitda = base.ebitda_y5
        net_factor = 1.0 - base.exit_cost_rate
        rows = []
        for multiple in multiples:
            ev = ebitda * float(multiple)
            net = ev * net_factor
            rows.append(
                {
                    "exit_multiple": float(multiple),
                    "ev": round(ev, 2),
                    "net_exit_value": round(net, 2),
                    "net_gap_total_investment": round(
                        net - base.total_project_investment, 2
                    ),
                }
            )
        break_even_cap = (
            ebitda * net_factor / base.total_project_investment
            if base.total_project_investment
            else 0.0
        )
        break_even_ebitda_net = (
            base.total_project_investment * base.exit_cap_rate / net_factor
            if net_factor
            else 0.0
        )
        return {
            "implied_exit_multiple": round(base.ev_cap_rate / ebitda, 2)
            if ebitda
            else None,
            "going_in_yield_on_cost": round(
                ebitda / base.total_project_investment, 4
            )
            if base.total_project_investment
            else None,
            "exit_cap_rate": base.exit_cap_rate,
            "break_even_cap_rate": round(break_even_cap, 4),
            "cap_rate_headroom_bp": round(
                (break_even_cap - base.exit_cap_rate) * 10_000, 1
            ),
            "no_compression_cap_rate": round(
                ebitda / base.total_project_investment, 4
            )
            if base.total_project_investment
            else None,
            "net_gap_at_no_compression": round(
                -base.total_project_investment * base.exit_cost_rate, 2
            ),
            "break_even_ebitda_net": round(break_even_ebitda_net, 2),
            "ebitda_headroom": round(ebitda - break_even_ebitda_net, 2),
            "ev_cap_rate": base.ev_cap_rate,
            "replacement_cost": base.total_project_investment,
            "gross_value_gap_total_investment": base.value_gap_total_investment,
            "net_value_gap_total_investment": base.net_value_gap_total_investment,
            "exit_multiple_table": pd.DataFrame(rows),
        }

    def distress_playbook(
        self, config: Optional[ReformConfig] = None
    ) -> Dict[str, Any]:
        """
        What happens if R7 lands on the downside and the covenant breaks.

        It computes the annual CFADS shortfall, the equity cure needed to hold
        a 1.25x DSCR, the DSRA cover in months, and whether a sale at the
        downside cap repays the outstanding debt. The point is to show the
        lender's loss given default, not to rescue the case.
        """
        config = config or get_cabin_preset("cabins_downside")
        engine = FinancialModelEngine(
            case="reform", reform=config, scenario=SCENARIOS["base"]
        )
        df = engine.run_projection(self.projection_years)
        debt = engine.debt_engine.get_annual_schedule_df()
        credit = CreditMetricsEngine(target_dscr=1.25, discount_wacc=config.discount_rate)
        kpi = credit.compute_credit_kpis(df, debt)

        rows = []
        for _, row in kpi.iterrows():
            cfads = float(row["cfads"])
            debt_service = float(row["debt_service"])
            rows.append(
                {
                    "year": int(row["year"]),
                    "cfads": round(cfads, 2),
                    "debt_service": round(debt_service, 2),
                    "shortfall": round(max(0.0, debt_service - cfads), 2),
                    "dscr": round(float(row["dscr"]), 2),
                    "ending_cash": round(float(row["ending_cash"]), 2),
                }
            )
        play = pd.DataFrame(rows)
        cumulative_shortfall = round(float(play["shortfall"].sum()), 2)
        min_row = play.loc[play["dscr"].idxmin()]
        cure = round(
            sum(
                max(0.0, 1.25 * float(r["debt_service"]) - float(r["cfads"]))
                for _, r in kpi.iterrows()
            ),
            2,
        )

        first_amortising = debt[debt["year"] == 2]
        dsra_six_months = (
            round(0.5 * float(first_amortising.iloc[0]["payment"]), 2)
            if not first_amortising.empty
            else 0.0
        )
        ending_debt_row = debt[debt["year"] == self.projection_years]
        ending_debt = (
            float(ending_debt_row.iloc[-1]["ending_balance"])
            if not ending_debt_row.empty
            else 0.0
        )
        result = self.run_config(config)
        net_exit_value = result.net_exit_value
        lender_recovery = (
            round(net_exit_value / ending_debt, 4) if ending_debt > 0 else 1.0
        )
        sale_shortfall = round(max(0.0, ending_debt - net_exit_value), 2)
        equity_at_exit = round(max(0.0, net_exit_value - ending_debt), 2)
        equity_invested = float(engine.total_equity_at_close)
        equity_recovery = (
            round(equity_at_exit / equity_invested, 4) if equity_invested else 0.0
        )

        if cumulative_shortfall <= 0.0:
            verdict = "NO SHORTFALL - CFADS COVERS DEBT SERVICE IN EVERY YEAR"
            stance = "covered"
        elif lender_recovery >= 1.0:
            verdict = (
                "THE LENDER IS REPAID ON SALE, BUT THE EQUITY IS WIPED OUT - "
                "DO NOT THROW A CURE AT A DEMAND FAILURE"
            )
            stance = "lender_repaid_equity_wiped"
        else:
            verdict = (
                "CURE OR RESTRUCTURE - A SALE AT THE DOWNSIDE CAP DOES NOT "
                "REPAY THE DEBT"
            )
            stance = "cure_or_restructure"

        return {
            "verdict": verdict,
            "stance": stance,
            "min_dscr": round(float(play["dscr"].min()), 2),
            "min_dscr_year": int(min_row["year"]),
            "cumulative_shortfall": cumulative_shortfall,
            "equity_cure_to_125x": cure,
            "dsra_six_months": dsra_six_months,
            "ending_debt": round(ending_debt, 2),
            "net_exit_value": net_exit_value,
            "lender_recovery": lender_recovery,
            "sale_shortfall": sale_shortfall,
            "equity_invested": round(equity_invested, 2),
            "equity_at_exit": equity_at_exit,
            "equity_recovery": equity_recovery,
            "annual": play,
        }

    # ------------------------------------------------------------------
    # Value bridge
    # ------------------------------------------------------------------
    def value_bridge(self, config: Optional[ReformConfig] = None) -> Dict[str, Any]:
        """
        Splits the mature EBITDA uplift into its four economic levers.

        The bridge is computed with the same engine, not with a hand-written
        formula, so the components tie exactly to the reform P&L.
        """
        config = config or get_reform_preset("revenue_reform")
        base_engine = FinancialModelEngine(
            case="management", scenario=SCENARIOS["base"]
        )
        base_df = base_engine.run_projection(self.projection_years)
        base_ebitda = float(base_df.iloc[-1]["ebitda"])

        adr_only = replace(
            config,
            external_covers_per_day=0.0,
            external_ticket=0.0,
            experiences_revenue=0.0,
            cost_savings=0.0,
            incremental_fte=0.0,
        )
        external_only = replace(
            config,
            adr_uplift=0.0,
            experiences_revenue=0.0,
            cost_savings=0.0,
        )
        experiences_only = replace(
            config,
            adr_uplift=0.0,
            external_covers_per_day=0.0,
            external_ticket=0.0,
            cost_savings=0.0,
            incremental_fte=0.0,
        )
        savings_only = replace(
            config,
            adr_uplift=0.0,
            external_covers_per_day=0.0,
            external_ticket=0.0,
            experiences_revenue=0.0,
            incremental_fte=0.0,
        )

        full = self.run_config(config, key="bridge_full")
        adr = self.run_config(adr_only, key="bridge_adr")
        external = self.run_config(external_only, key="bridge_external")
        experiences = self.run_config(experiences_only, key="bridge_experiences")
        savings = self.run_config(savings_only, key="bridge_savings")

        cap = config.exit_cap_rate
        components = {
            "adr_uplift": adr.ebitda_y5 - base_ebitda,
            "external_fnb": external.ebitda_y5 - base_ebitda,
            "experiences": experiences.ebitda_y5 - base_ebitda,
            "cost_savings": savings.ebitda_y5 - base_ebitda,
        }
        total_increment = sum(components.values())
        reform_increment = full.ebitda_y5 - base_ebitda

        return {
            "base_ebitda": round(base_ebitda, 2),
            "base_ev": round(base_ebitda / cap, 2),
            "components_ebitda": {k: round(v, 2) for k, v in components.items()},
            "components_ev": {k: round(v / cap, 2) for k, v in components.items()},
            "total_increment_ebitda": round(total_increment, 2),
            "reform_increment_ebitda": round(reform_increment, 2),
            "bridge_tie": round(total_increment - reform_increment, 2),
            "reform_ebitda": round(full.ebitda_y5, 2),
            "reform_ev": round(full.ev_cap_rate, 2),
            "capex": round(config.total_capex, 2),
            "total_project_investment": round(full.total_project_investment, 2),
            "value_gap_capex": round(full.ev_cap_rate - config.total_capex, 2),
            "value_gap_total_investment": round(
                full.ev_cap_rate - full.total_project_investment, 2
            ),
            "exit_cost_rate": config.exit_cost_rate,
            "exit_costs": full.exit_costs,
            "net_exit_value": full.net_exit_value,
            "net_value_gap_capex": full.net_value_gap_capex,
            "net_value_gap_total_investment": full.net_value_gap_total_investment,
            "cap_rate": cap,
            "full": full,
        }

    # ------------------------------------------------------------------
    # Frontier
    # ------------------------------------------------------------------
    def frontier(
        self,
        capex_levels: Optional[Iterable[float]] = None,
        cover_levels: Optional[Iterable[float]] = None,
        base_config: Optional[ReformConfig] = None,
    ) -> pd.DataFrame:
        """
        Matrix of value gap (EV - total investment) by CapEx and external
        covers. Negative cells destroy value; positive cells are the only
        potentially investable corner.
        """
        base_config = base_config or get_reform_preset("revenue_reform")
        capex_levels = list(
            capex_levels
            or [1_050_100, 1_000_000, 950_000, 900_000, 850_000, 800_000, 770_000, 700_000]
        )
        cover_levels = list(cover_levels or [0, 3, 6, 8, 10])

        rows = {}
        for capex in capex_levels:
            config_at_capex = base_config.with_total_capex(float(capex))
            row = {}
            for covers in cover_levels:
                fte = 0.0 if covers <= 0 else max(1.0, covers / 6.0)
                config = replace(
                    config_at_capex,
                    external_covers_per_day=float(covers),
                    incremental_fte=fte,
                )
                result = self.run_config(config)
                row[float(covers)] = result.value_gap_total_investment
            rows[float(capex)] = row

        df = pd.DataFrame(rows).T
        df.index.name = "Capex"
        df.columns.name = "External covers/day"
        return df

    # ------------------------------------------------------------------
    # Stress table
    # ------------------------------------------------------------------
    def stress_cases(self) -> pd.DataFrame:
        base = get_reform_preset("revenue_reform")
        ve = get_reform_preset("value_engineered")
        lean = get_reform_preset("resize_850")
        downside = get_reform_preset("downside")

        ine_scenario = replace(
            SCENARIOS["base"],
            occupancy_multiplier=0.2124 / 0.3136,
        )
        rate_scenario = replace(
            SCENARIOS["base"],
            interest_rate_delta=0.02,
        )
        conservative = SCENARIOS["conservative"]

        cases = [
            ("As-is reform (R2)", base, SCENARIOS["base"]),
            ("R2 + INE 21.24% demand", base, ine_scenario),
            ("R2 + covers -50%", replace(base, external_covers_per_day=3.0, incremental_fte=1.0), SCENARIOS["base"]),
            ("R3 + CapEx +20%", ve.scale_non_land_capex(1.20), SCENARIOS["base"]),
            ("R3 + LEADER delayed to Y3", replace(ve, leader_disbursement_year=3), SCENARIOS["base"]),
            ("R3 + no LEADER grant", replace(ve, leader_subsidy_rate=0.0), SCENARIOS["base"]),
            ("R3 + rate +200 bp", ve, rate_scenario),
            ("R3 + conservative demand", ve, conservative),
            ("R6 combined downside", downside, SCENARIOS["base"]),
        ]

        rows = []
        for label, config, scenario in cases:
            result = self.run_config(config, scenario=scenario, key=label)
            rows.append(
                {
                    "case": label,
                    "capex": result.capex,
                    "total_investment": result.total_project_investment,
                    "ebitda_y5": result.ebitda_y5,
                    "dscr_min": result.dscr_min,
                    "ev_cap_rate": result.ev_cap_rate,
                    "value_gap_capex": result.value_gap_capex,
                    "value_gap_total_investment": result.value_gap_total_investment,
                    "net_value_gap_total_investment": result.net_value_gap_total_investment,
                    "project_npv": result.project_npv,
                    "project_irr_exit": result.project_irr_exit,
                    "equity_irr_exit": result.equity_irr_exit,
                }
            )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Rate sensitivity
    # ------------------------------------------------------------------
    def rate_sensitivity(
        self,
        base_config: Optional[ReformConfig] = None,
        deltas: Iterable[float] = (0.0, 0.01, 0.02, 0.03),
    ) -> pd.DataFrame:
        """
        Re-runs the chosen reform at a range of rate shocks. The reform uses a
        4.0% fixed rate in the base case; this table shows what a floating or
        re-priced facility would do to the DSCR and the value gap.
        """
        base_config = base_config or get_reform_preset("revenue_reform")
        rows = []
        for delta in deltas:
            scenario = replace(
                SCENARIOS["base"], interest_rate_delta=float(delta)
            )
            result = self.run_config(
                base_config, scenario=scenario, key=f"rate_{delta}"
            )
            rows.append(
                {
                    "rate_delta_bp": int(round(float(delta) * 10_000)),
                    "interest_rate": round(
                        base_config.loan_interest_rate + float(delta), 4
                    ),
                    "dscr_min": result.dscr_min,
                    "project_npv": result.project_npv,
                    "value_gap_total_investment": result.value_gap_total_investment,
                    "net_value_gap_total_investment": result.net_value_gap_total_investment,
                }
            )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Recommendation
    # ------------------------------------------------------------------
    def recommendation(self) -> Dict[str, Any]:
        results = {
            key: self.run_config(config, key=key)
            for key, config in REFORM_PRESETS.items()
        }
        r2 = results["revenue_reform"]
        r3 = results["value_engineered"]
        r5 = results["resize_850"]
        r4 = results["aggressive"]
        r6 = results["downside"]

        clearing = [k for k, v in results.items() if v.clears_wacc]
        if not clearing:
            verdict = "DECLINE - NO REFORM CASE CLEARS THE 8% WACC"
            stance = "decline"
        elif set(clearing) == {"aggressive"}:
            verdict = (
                "DECLINE AS STRUCTURED - ONLY THE AGGRESSIVE, UNPROVEN "
                "DEMAND CASE CLEARS THE WACC"
            )
            stance = "decline_with_boundary"
        elif r5.clears_wacc or r3.clears_wacc:
            verdict = "CONDITIONAL PROCEED TO PHASE 0 - DEMAND TEST REQUIRED"
            stance = "phase_zero"
        else:
            verdict = "CONDITIONAL - ONLY A DEEPER RESIZE MERITS A PHASE 0 TEST"
            stance = "resize_only"

        detail = (
            "The realistic revenue reform (R2: six external covers/day, +5% "
            f"ADR, one FTE) produces EUR {r2.ebitda_y5:,.0f} of mature EBITDA "
            f"and EUR {r2.ev_cap_rate:,.0f} of asset value. Against the "
            f"EUR {r2.capex:,.0f} CapEx that is a gap of EUR {r2.value_gap_capex:,.0f}; "
            f"against total project investment of EUR {r2.total_project_investment:,.0f} "
            f"the gap is EUR {r2.value_gap_total_investment:,.0f}. After "
            f"{r2.exit_cost_rate*100:.1f}% exit costs the net gap is "
            f"EUR {r2.net_value_gap_total_investment:,.0f}. "
            f"R2 still has a project NPV of EUR {r2.project_npv:,.0f} and a "
            f"project IRR of {(r2.project_irr_exit or 0)*100:.2f}%."
        )
        detail_2 = (
            f"The 900k value-engineered case (R3) improves the NPV to "
            f"EUR {r3.project_npv:,.0f} and the IRR to {(r3.project_irr_exit or 0)*100:.2f}%, "
            f"but still does not clear an 8% WACC. The 850k lean case (R5) "
            f"reaches EUR {r5.project_npv:,.0f} of NPV and "
            f"{(r5.project_irr_exit or 0)*100:.2f}% IRR, still below the hurdle. "
            f"The only positive-NPV case is R4 (eight covers/day, +10% ADR, "
            f"one FTE) at EUR {r4.project_npv:,.0f} of NPV and "
            f"{(r4.project_irr_exit or 0)*100:.2f}% IRR - a negligible margin "
            f"and a total-investment value gap of EUR {r4.value_gap_total_investment:,.0f}. "
            f"After {r4.exit_cost_rate*100:.1f}% exit costs the net gap is "
            f"EUR {r4.net_value_gap_total_investment:,.0f}, so even the boundary "
            f"case fails the net test. "
            f"The combined downside (R6) is deeply negative: EBITDA "
            f"EUR {r6.ebitda_y5:,.0f}, NPV EUR {r6.project_npv:,.0f}. "
            "The value frontier does show a positive corner at roughly EUR 700k of CapEx "
            "(land included) with six or more covers, but that is EUR 450k of non-land "
            "spend for an eight-room refurbishment: a scope-reduction thesis, not the "
            "current 1.05M budget."
        )
        conditions = [
            "Do not treat the 1.05M eight-room project as the base case for a reform.",
            "Prove external F&B demand before committing construction capital: a low-cost Phase 0 pop-up/restaurant test, not a full refurbishment.",
            "If the family wants to proceed, cap the initial capital at the lean scope and keep the second phase behind a demand gate.",
            "Treat the ~700k frontier corner as a different, smaller project: it only works by cutting the non-land budget to about 450k, which is not the eight-room refurbishment currently specified.",
            "Charge the land at its opportunity value; do not describe the project as viable only because the site is already owned.",
            "Price the exit net of selling costs. The gross cap-rate value flatters every case; the boundary case fails once 3% exit costs are deducted.",
            "Re-run the model with 1.25-1.5 FTE for the external covers, not one FTE, and with INE 21.24% occupancy in the downside.",
        ]
        return {
            "verdict": verdict,
            "stance": stance,
            "detail": detail,
            "detail_2": detail_2,
            "conditions": conditions,
            "clearing_cases": clearing,
            "results": results,
        }

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def summary_table(self) -> pd.DataFrame:
        df = self.run_presets()
        display_cols = [
            "key",
            "name",
            "capex",
            "total_project_investment",
            "revenue_y5",
            "ebitda_y5",
            "dscr_min",
            "ev_cap_rate",
            "value_gap_capex",
            "value_gap_total_investment",
            "net_value_gap_capex",
            "net_value_gap_total_investment",
            "project_npv",
            "project_irr_exit",
            "equity_irr_exit",
        ]
        return df[display_cols].copy()

    def print_terminal_summary(self) -> None:
        print("REFORM / RESIZE CASE - WHAT WOULD HAVE TO BE TRUE?")
        print("-" * 88)
        summary = self.summary_table()
        terminal_cols = [
            "key",
            "name",
            "capex",
            "total_project_investment",
            "ebitda_y5",
            "dscr_min",
            "ev_cap_rate",
            "value_gap_total_investment",
            "net_value_gap_total_investment",
            "project_npv",
            "project_irr_exit",
        ]
        display = summary[terminal_cols].copy()
        for col in ("project_irr_exit",):
            display[col] = display[col].apply(
                lambda x: f"{x*100:.2f}%" if x is not None and pd.notna(x) else "n/a"
            )
        for col in (
            "capex",
            "total_project_investment",
            "ebitda_y5",
            "ev_cap_rate",
            "value_gap_total_investment",
            "net_value_gap_total_investment",
            "project_npv",
        ):
            display[col] = display[col].apply(lambda x: f"{x:,.0f}")
        print(display.to_string(index=False))
        print()
        bridge = self.value_bridge()
        print("VALUE BRIDGE - R2 REVENUE REFORM (MATURE YEAR, 8.5% CAP RATE)")
        print(f"  Base management EBITDA:                 EUR {bridge['base_ebitda']:>12,.2f}")
        for label, value in bridge["components_ebitda"].items():
            print(f"  + {label:<36} EUR {value:>12,.2f}")
        print(f"  = Reform EBITDA:                        EUR {bridge['reform_ebitda']:>12,.2f}")
        print(f"  Reform enterprise value (gross):        EUR {bridge['reform_ev']:>12,.2f}")
        print(f"  Exit costs ({bridge['exit_cost_rate']*100:.1f}%):                    EUR {-bridge['exit_costs']:>12,.2f}")
        print(f"  Net exit value:                         EUR {bridge['net_exit_value']:>12,.2f}")
        print(f"  CapEx:                                  EUR {bridge['capex']:>12,.2f}")
        print(f"  Net value gap vs CapEx:                 EUR {bridge['net_value_gap_capex']:>12,.2f}")
        print(f"  Total project investment:               EUR {bridge['total_project_investment']:>12,.2f}")
        print(f"  Net value gap vs total investment:      EUR {bridge['net_value_gap_total_investment']:>12,.2f}")
        print(f"  Bridge tie (should be zero):            EUR {bridge['bridge_tie']:>12,.2f}")
        print()
        rec = self.recommendation()
        print(f"REFORM RECOMMENDATION: {rec['verdict']}")
        print(f"  {rec['detail']}")
        print(f"  {rec['detail_2']}")
        print("  Conditions:")
        for condition in rec["conditions"]:
            print(f"   - {condition}")
        print()

        print("R7 PREMIUM CABINS - A DIFFERENT PRODUCT, SAME HURDLE")
        print("-" * 88)
        cabin_rec = self.cabin_recommendation()
        cabin_summary = self.run_cabin_presets()
        for _, row in cabin_summary.iterrows():
            irr = row["project_irr_exit"]
            irr_text = f"{irr*100:.2f}%" if irr is not None and pd.notna(irr) else "n/a"
            print(
                f"  {row['key']:<18} CapEx {row['capex']:>10,.0f}  "
                f"EBITDA {row['ebitda_y5']:>9,.0f}  DSCR {row['dscr_min']:>4.2f}x  "
                f"net gap {row['net_value_gap_total_investment']:>+10,.0f}  "
                f"IRR {irr_text:>7}"
            )
        print()
        ladder = cabin_rec["cost_ladder"]
        print("  Cost corridor (6 cabins, 200 EUR ADR, 50% occupancy, 45k experiences):")
        for _, row in ladder.iterrows():
            print(
                f"    {row['cost_per_cabin']:>7,.0f} EUR/cabin  "
                f"CapEx {row['capex']:>10,.0f}  "
                f"EBITDA {row['ebitda_y5']:>9,.0f}  "
                f"net gap {row['net_gap_total_investment']:>+10,.0f}  "
                f"{'PASS' if row['passes_net_test'] else 'FAIL'}"
            )
        print()
        print(f"R7 RECOMMENDATION: {cabin_rec['verdict']}")
        print(f"  {cabin_rec['detail']}")
        print(f"  {cabin_rec['detail_2']}")
        print("  Conditions:")
        for condition in cabin_rec["conditions"]:
            print(f"   - {condition}")
        print()

        valuation = self.valuation_cross_check()
        print("R7 VALUATION CROSS-CHECK - CAP RATE, EXIT MULTIPLE AND BREAK-EVEN")
        print(
            f"  Going-in yield on cost:      {valuation['going_in_yield_on_cost']*100:>6.2f}%"
        )
        print(f"  Exit cap rate:               {valuation['exit_cap_rate']*100:>6.2f}%")
        print(
            f"  Break-even exit cap (net):  {valuation['break_even_cap_rate']*100:>6.2f}%"
            f"  (headroom {valuation['cap_rate_headroom_bp']:.0f} bp)"
        )
        print(
            f"  Break-even EBITDA (net):    EUR {valuation['break_even_ebitda_net']:>10,.0f}"
            f"  (headroom EUR {valuation['ebitda_headroom']:,.0f})"
        )
        print(
            f"  Implied exit multiple:       {valuation['implied_exit_multiple']:>6.1f}x"
        )
        print(
            f"  No-compression case:        exit at {valuation['no_compression_cap_rate']*100:.2f}%"
            f" -> net gap EUR {valuation['net_gap_at_no_compression']:+,.0f}"
        )
        print()
        for _, row in valuation["exit_multiple_table"].iterrows():
            print(
                f"    {row['exit_multiple']:>4.1f}x  EV {row['ev']:>10,.0f}  "
                f"net {row['net_exit_value']:>10,.0f}  "
                f"gap {row['net_gap_total_investment']:>+10,.0f}"
            )
        print()

        stress = self.cost_inflation_stress()
        print("R7 COST-INFLATION STRESS - REAL COST GROWTH, FLAT REAL PRICES")
        for _, row in stress.iterrows():
            print(
                f"    {row['cost_inflation']*100:>4.1f}%/yr  EBITDA {row['ebitda_y5']:>9,.0f}  "
                f"DSCR Y5 {row['dscr_y5']:>4.2f}x  net gap "
                f"{row['net_gap_total_investment']:>+10,.0f}  "
                f"{'PASS' if row['passes_net_test'] else 'FAIL'}"
            )
        print()

        distress = self.distress_playbook()
        print(f"DISTRESS PLAYBOOK (R7 DOWNSIDE): {distress['verdict']}")
        print(
            f"  Minimum DSCR {distress['min_dscr']:.2f}x in Year "
            f"{distress['min_dscr_year']}; cumulative shortfall "
            f"EUR {distress['cumulative_shortfall']:,.0f}; six-month DSRA "
            f"EUR {distress['dsra_six_months']:,.0f}"
        )
        print(
            f"  Cash cure to 1.25x DSCR: EUR {distress['equity_cure_to_125x']:,.0f}; "
            f"sale at the downside cap: EUR {distress['net_exit_value']:,.0f} vs "
            f"EUR {distress['ending_debt']:,.0f} of debt"
        )
        print(
            f"  Lender recovery {distress['lender_recovery']*100:.0f}%; equity "
            f"EUR {distress['equity_at_exit']:,.0f} vs "
            f"EUR {distress['equity_invested']:,.0f} invested "
            f"({distress['equity_recovery']*100:.0f}% recovery)"
        )
        print()

    def export_json(self, path: Optional[Path] = None) -> Path:
        if path is None:
            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            path = data_dir / "reform_analysis.json"

        presets = self.run_presets()
        cabins = self.run_cabin_presets()
        bridge = self.value_bridge()
        rec = self.recommendation()
        cabin_rec = self.cabin_recommendation()
        frontier = self.frontier()
        stress = self.stress_cases()
        rate_sensitivity = self.rate_sensitivity()
        cost_inflation = self.cost_inflation_stress()
        valuation = self.valuation_cross_check()
        distress = self.distress_playbook()

        payload = {
            "generated_by": "src.core.reform.ReformAnalysisEngine",
            "as_is_base": {
                "note": (
                    "The as-is management, market and promoter cases are "
                    "unchanged; this file is a separate reform overlay."
                )
            },
            "presets": presets.to_dict(orient="records"),
            "cabins": cabins.to_dict(orient="records"),
            "cabin_cost_ladder": cabin_rec["cost_ladder"].to_dict(orient="records"),
            "cabin_recommendation": {
                "verdict": cabin_rec["verdict"],
                "stance": cabin_rec["stance"],
                "detail": cabin_rec["detail"],
                "detail_2": cabin_rec["detail_2"],
                "conditions": cabin_rec["conditions"],
            },
            "cabin_valuation_cross_check": {
                **{
                    k: v
                    for k, v in valuation.items()
                    if k != "exit_multiple_table"
                },
                "exit_multiple_table": valuation[
                    "exit_multiple_table"
                ].to_dict(orient="records"),
            },
            "cabin_cost_inflation_stress": cost_inflation.to_dict(orient="records"),
            "distress_playbook": {
                **{
                    k: v
                    for k, v in distress.items()
                    if k != "annual"
                },
                "annual": distress["annual"].to_dict(orient="records"),
            },
            "value_bridge": {
                k: v
                for k, v in bridge.items()
                if k != "full"
            },
            "frontier_gap_total_investment": {
                str(round(float(idx), 2)): {
                    str(round(float(col), 2)): round(float(frontier.loc[idx, col]), 2)
                    for col in frontier.columns
                }
                for idx in frontier.index
            },
            "stress_cases": stress.to_dict(orient="records"),
            "rate_sensitivity": rate_sensitivity.to_dict(orient="records"),
            "recommendation": {
                "verdict": rec["verdict"],
                "stance": rec["stance"],
                "detail": rec["detail"],
                "detail_2": rec["detail_2"],
                "conditions": rec["conditions"],
                "clearing_cases": rec["clearing_cases"],
            },
        }
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        return path


if __name__ == "__main__":
    engine = ReformAnalysisEngine()
    engine.print_terminal_summary()
    out = engine.export_json()
    print(f"Exported reform analysis: {out}")
