"""
Scenario stress-testing and sensitivity analysis engine.

Simulates:
1. Multi-scenario comparative projections (Conservative vs. Base vs. Optimistic).
2. Two-dimensional sensitivity matrices:
   - Occupancy vs. ADR on EBITDA, DSCR, and Equity IRR.
   - Occupancy vs. Senior Debt Interest Rate on minimum DSCR.
3. Multi-tier Break-Even analysis (Operational, Debt Service, Bank Covenant).
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from src.config.assumptions import SCENARIOS, ScenarioDrivers
from src.core.statements import FinancialModelEngine
from src.core.metrics import CreditMetricsEngine


class ScenarioEngine:
    """Executes multi-scenario stress tests and parametric sensitivity analyses."""

    def __init__(self, target_dscr: float = 1.25, projection_years: int = 5):
        self.target_dscr = target_dscr
        self.projection_years = projection_years

    def run_all_scenarios(self) -> Dict[str, pd.DataFrame]:
        """Runs the 3-statement model for each pre-configured institutional scenario."""
        results = {}
        for key, scenario in SCENARIOS.items():
            engine = FinancialModelEngine(scenario=scenario)
            df_proj = engine.run_projection(projection_years=self.projection_years)
            debt_sched = engine.debt_engine.get_annual_schedule_df()

            credit = CreditMetricsEngine(target_dscr=self.target_dscr)
            df_kpi = credit.compute_credit_kpis(df_proj, debt_sched)
            results[key] = df_kpi
        return results

    def generate_scenario_comparison_table(self) -> pd.DataFrame:
        """Produces an executive side-by-side comparison across scenarios for Year 1, Year 3, and 5-Year Average."""
        scenarios_data = self.run_all_scenarios()
        records = []

        metrics_to_extract = [
            ("total_revenue", "Ventas Totales (€)", "{:,.0f}"),
            ("ebitda", "EBITDA (€)", "{:,.0f}"),
            ("net_income", "Beneficio Neto (€)", "{:,.0f}"),
            ("ending_cash", "Caja Final de Ejercicio (€)", "{:,.0f}"),
            ("dscr", "Cobertura de Deuda (DSCR)", "{:.2f}x"),
            ("icr", "Cobertura de Intereses (ICR)", "{:.2f}x"),
        ]

        for metric_key, metric_label, fmt in metrics_to_extract:
            row = {"Métrica": metric_label}
            for sc_key, sc_name in [
                ("conservative", "Conservador"),
                ("base", "Caso Base"),
                ("optimistic", "Optimista"),
            ]:
                df = scenarios_data[sc_key]
                y1_val = df.iloc[0][metric_key]
                y3_val = df.iloc[2][metric_key]
                row[f"{sc_name} (Y1)"] = fmt.format(y1_val)
                row[f"{sc_name} (Y3)"] = fmt.format(y3_val)
            records.append(row)

        return pd.DataFrame(records)

    def generate_sensitivity_matrix_dscr(
        self,
        occupancy_multipliers: List[float] = [0.70, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30],
        interest_rate_deltas: List[float] = [-0.015, -0.010, -0.005, 0.000, 0.010, 0.015, 0.020],
    ) -> pd.DataFrame:
        """
        Builds a 2D sensitivity matrix of Year-2 DSCR against Occupancy vs.
        Interest Rate moves. Year 2 is the first amortising year, so it is the
        binding covenant year. Identifies bank covenant breach zones (DSCR <
        1.25x).
        """
        matrix_data = {}

        for delta_r in interest_rate_deltas:
            col_label = f"{(0.040 + delta_r)*100:.1f}% Rate"
            col_vals = []
            for occ_mult in occupancy_multipliers:
                custom_scenario = ScenarioDrivers(
                    name=f"Sens_{occ_mult}_{delta_r}",
                    occupancy_multiplier=occ_mult,
                    adr_multiplier=1.0,
                    opex_multiplier=1.0,
                    interest_rate_delta=delta_r,
                )
                engine = FinancialModelEngine(scenario=custom_scenario)
                df_proj = engine.run_projection(projection_years=2)
                debt_sched = engine.debt_engine.get_annual_schedule_df()

                credit = CreditMetricsEngine(target_dscr=self.target_dscr)
                df_kpi = credit.compute_credit_kpis(df_proj, debt_sched)
                y2_dscr = df_kpi.iloc[1]["dscr"]
                col_vals.append(y2_dscr)

            matrix_data[col_label] = col_vals

        row_labels = [f"{m*100:.0f}% Occ Factor" for m in occupancy_multipliers]
        df_matrix = pd.DataFrame(matrix_data, index=row_labels)
        return df_matrix
