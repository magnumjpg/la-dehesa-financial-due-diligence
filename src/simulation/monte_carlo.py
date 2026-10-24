"""
Monte Carlo stochastic simulation for credit risk and equity returns.

The simulation perturbs the four drivers that matter in a rural hotel:
occupancy, ADR, the senior interest rate and the operating-cost level. Each draw
runs the full three-statement model with the deterministic close-day funding, so
the DSCR, cash balance and equity IRR are internally consistent with the
financial statements.

Outputs:
- Distribution of the minimum DSCR over the three-year projection (VaR 95%).
- Probability of a 1.25x covenant breach and of a sub-1.00x debt-service year.
- Distribution of the levered equity IRR (8.5% exit) and of Year-1 cash.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.config.assumptions import SCENARIOS, ScenarioDrivers
from src.core.metrics import CreditMetricsEngine, calculate_irr
from src.core.statements import FinancialModelEngine


@dataclass
class MonteCarloSummary:
    iterations: int
    mean_min_dscr: float
    median_min_dscr: float
    p5_min_dscr: float          # 5th percentile (VaR 95% worst case)
    p95_min_dscr: float
    prob_covenant_breach: float  # P(min DSCR < 1.25x)
    prob_cash_insolvency: float  # P(min DSCR < 1.00x)
    mean_equity_irr: float
    p5_equity_irr: float
    mean_ending_cash_y1: float
    p5_ending_cash_y1: float
    cash_equity: float
    total_equity_at_close: float
    total_project_investment: float


class MonteCarloSimulator:
    """Stochastic simulator for project financial viability."""

    def __init__(
        self,
        iterations: int = 1000,
        random_seed: int = 42,
        target_dscr: float = 1.25,
        case: str = "management",
        exit_cap_rate: float = 0.085,
    ):
        self.iterations = iterations
        self.random_seed = random_seed
        self.target_dscr = target_dscr
        self.case = case
        self.exit_cap_rate = exit_cap_rate

        # Deterministic funding: the equity plug is a close-day decision, not a
        # random variable. Reusing it avoids a five-year cash probe per draw.
        base = FinancialModelEngine(case=case, scenario=SCENARIOS["base"])
        self.cash_equity = float(base.cash_equity)
        self.total_equity_at_close = float(base.total_equity_at_close)
        self.total_project_investment = float(base.total_project_investment)

    def run_simulation(self) -> Tuple[pd.DataFrame, MonteCarloSummary]:
        """Runs the stochastic iterations and computes the risk distributions."""
        rng = np.random.default_rng(self.random_seed)

        # Occupancy multiplier: normal centred on the management plan, clipped.
        occ_samples = np.clip(rng.normal(1.00, 0.10, self.iterations), 0.65, 1.40)
        # ADR multiplier: tighter dispersion, clipped.
        adr_samples = np.clip(rng.normal(1.00, 0.07, self.iterations), 0.80, 1.25)
        # Interest-rate delta: 75 bp standard deviation, -150/+250 bp bounds.
        rate_samples = np.clip(
            rng.normal(0.00, 0.0075, self.iterations), -0.015, 0.025
        )
        # Operating-cost multiplier.
        opex_samples = np.clip(rng.normal(1.00, 0.05, self.iterations), 0.90, 1.20)

        credit = CreditMetricsEngine(target_dscr=self.target_dscr)
        records: List[Dict[str, float]] = []

        for i in range(self.iterations):
            scenario = ScenarioDrivers(
                name=f"Sim_{i}",
                occupancy_multiplier=float(occ_samples[i]),
                adr_multiplier=float(adr_samples[i]),
                opex_multiplier=float(opex_samples[i]),
                interest_rate_delta=float(rate_samples[i]),
            )
            engine = FinancialModelEngine(
                case=self.case,
                scenario=scenario,
                cash_equity_override=self.cash_equity,
            )
            df = engine.run_projection(projection_years=3)
            debt_sched = engine.debt_engine.get_annual_schedule_df()
            kpi = credit.compute_credit_kpis(df, debt_sched)

            min_dscr = float(kpi["dscr"].min())
            returns = credit.compute_returns_summary(
                kpi,
                initial_equity=engine.total_equity_at_close,
                initial_capex=engine.total_project_investment,
                exit_cap_rate=self.exit_cap_rate,
            )

            records.append(
                {
                    "sim_id": i,
                    "occ_mult": float(occ_samples[i]),
                    "adr_mult": float(adr_samples[i]),
                    "rate_delta": float(rate_samples[i]),
                    "opex_mult": float(opex_samples[i]),
                    "dscr_y1": float(kpi.iloc[0]["dscr"]),
                    "dscr_y2": float(kpi.iloc[1]["dscr"]),
                    "dscr_y3": float(kpi.iloc[2]["dscr"]),
                    "min_dscr": min_dscr,
                    "ending_cash_y1": float(kpi.iloc[0]["ending_cash"]),
                    "ebitda_y3": float(kpi.iloc[2]["ebitda"]),
                    "equity_irr_exit": float(returns["equity_irr_exit"] or 0.0),
                    "project_irr_exit": float(returns["project_irr_exit"] or 0.0),
                    "covenant_breach": bool(min_dscr < self.target_dscr),
                    "default": bool(min_dscr < 1.00),
                }
            )

        df_sim = pd.DataFrame(records)

        summary = MonteCarloSummary(
            iterations=self.iterations,
            mean_min_dscr=round(float(df_sim["min_dscr"].mean()), 2),
            median_min_dscr=round(float(df_sim["min_dscr"].median()), 2),
            p5_min_dscr=round(float(df_sim["min_dscr"].quantile(0.05)), 2),
            p95_min_dscr=round(float(df_sim["min_dscr"].quantile(0.95)), 2),
            prob_covenant_breach=round(float(df_sim["covenant_breach"].mean()), 4),
            prob_cash_insolvency=round(float(df_sim["default"].mean()), 4),
            mean_equity_irr=round(float(df_sim["equity_irr_exit"].mean()), 4),
            p5_equity_irr=round(float(df_sim["equity_irr_exit"].quantile(0.05)), 4),
            mean_ending_cash_y1=round(float(df_sim["ending_cash_y1"].mean()), 2),
            p5_ending_cash_y1=round(float(df_sim["ending_cash_y1"].quantile(0.05)), 2),
            cash_equity=self.cash_equity,
            total_equity_at_close=self.total_equity_at_close,
            total_project_investment=self.total_project_investment,
        )

        return df_sim, summary
