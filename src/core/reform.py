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
from src.config.reform import (
    REFORM_PRESETS,
    ReformConfig,
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
        ev = terminal_ebitda / config.exit_cap_rate
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
            dscr_min=float(kpi["dscr"].min()),
            ending_cash_y1=float(y1["ending_cash"]),
            ending_cash_y5=float(y5["ending_cash"]),
            exit_cap_rate=float(config.exit_cap_rate),
            discount_rate=float(config.discount_rate),
            terminal_value=float(returns["terminal_value"]),
            ev_cap_rate=round(ev, 2),
            value_gap_capex=round(ev - config.total_capex, 2),
            value_gap_total_investment=round(ev - total_investment, 2),
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
            ("R3 + rate +200 bp", ve, rate_scenario),
            ("R3 + conservative demand", ve, conservative),
            ("R6 combined downside", downside, ine_scenario),
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
                    "project_npv": result.project_npv,
                    "project_irr_exit": result.project_irr_exit,
                    "equity_irr_exit": result.equity_irr_exit,
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
            f"the gap is EUR {r2.value_gap_total_investment:,.0f}. "
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
            "project_npv",
            "project_irr_exit",
            "equity_irr_exit",
        ]
        return df[display_cols].copy()

    def print_terminal_summary(self) -> None:
        print("REFORM / RESIZE CASE - WHAT WOULD HAVE TO BE TRUE?")
        print("-" * 88)
        summary = self.summary_table()
        display = summary.copy()
        for col in ("project_irr_exit", "equity_irr_exit"):
            display[col] = display[col].apply(
                lambda x: f"{x*100:.2f}%" if x is not None and pd.notna(x) else "n/a"
            )
        for col in (
            "capex",
            "total_project_investment",
            "revenue_y5",
            "ebitda_y5",
            "ev_cap_rate",
            "value_gap_capex",
            "value_gap_total_investment",
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
        print(f"  Reform enterprise value:                EUR {bridge['reform_ev']:>12,.2f}")
        print(f"  CapEx:                                  EUR {bridge['capex']:>12,.2f}")
        print(f"  Value gap vs CapEx:                     EUR {bridge['value_gap_capex']:>12,.2f}")
        print(f"  Total project investment:               EUR {bridge['total_project_investment']:>12,.2f}")
        print(f"  Value gap vs total investment:          EUR {bridge['value_gap_total_investment']:>12,.2f}")
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

    def export_json(self, path: Optional[Path] = None) -> Path:
        if path is None:
            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            path = data_dir / "reform_analysis.json"

        presets = self.run_presets()
        bridge = self.value_bridge()
        rec = self.recommendation()
        frontier = self.frontier()
        stress = self.stress_cases()

        payload = {
            "generated_by": "src.core.reform.ReformAnalysisEngine",
            "as_is_base": {
                "note": (
                    "The as-is management, market and promoter cases are "
                    "unchanged; this file is a separate reform overlay."
                )
            },
            "presets": presets.to_dict(orient="records"),
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
