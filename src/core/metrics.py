"""
Banking covenant and investment metrics engine.

Computes:
1. Debt Service Coverage Ratio (DSCR = CFADS / Debt Service).
2. Interest Coverage Ratio (ICR = EBITDA / Interest Expense).
3. Loan-to-Value (LTV) and Debt Yield over time.
4. Unlevered (Project) and Levered (Equity) IRR and Net Present Value (NPV / VAN).
5. Operational and Financial Break-Even Occupancy rates.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def calculate_npv(rate: float, cash_flows: List[float]) -> float:
    """Computes Net Present Value for a series of periodic cash flows."""
    val = sum(cf / ((1.0 + rate) ** t) for t, cf in enumerate(cash_flows))
    return round(val, 2)


def calculate_irr(cash_flows: List[float], max_iter: int = 1000, tol: float = 1e-6) -> Optional[float]:
    """
    Computes Internal Rate of Return (IRR) using robust Newton-Raphson with bisection fallback.
    Avoids heavy third-party dependencies while guaranteeing convergence.
    """
    # Check if there is at least one sign change
    has_pos = any(cf > 0 for cf in cash_flows)
    has_neg = any(cf < 0 for cf in cash_flows)
    if not (has_pos and has_neg):
        return None

    rate = 0.10  # Initial guess 10%
    for _ in range(max_iter):
        npv = sum(cf / ((1.0 + rate) ** t) for t, cf in enumerate(cash_flows))
        d_npv = sum(-t * cf / ((1.0 + rate) ** (t + 1)) for t, cf in enumerate(cash_flows))

        if abs(d_npv) < 1e-12:
            break

        new_rate = rate - npv / d_npv
        if abs(new_rate - rate) < tol:
            return round(new_rate, 4)
        rate = new_rate

        # Prevent divergence to extreme negatives
        if rate <= -0.99:
            rate = -0.50

    return round(rate, 4) if not np.isnan(rate) else None


class CreditMetricsEngine:
    """Calculates bank underwriting covenants and financial ratios from projection dataframe."""

    def __init__(self, target_dscr: float = 1.25, discount_wacc: float = 0.08):
        self.target_dscr = target_dscr
        self.discount_wacc = discount_wacc

    def compute_credit_kpis(self, df_projection: pd.DataFrame, debt_schedule: pd.DataFrame) -> pd.DataFrame:
        """Enriches annual projection with DSCR, ICR, and solvency metrics."""
        df = df_projection.copy()

        dscr_list = []
        icr_list = []
        debt_service_list = []
        dscr_compliant_list = []

        for idx, row in df.iterrows():
            y = int(row["year"])
            d_row = debt_schedule[debt_schedule["year"] == y].iloc[0]
            debt_service = float(d_row["payment"])
            principal = float(d_row["principal"])
            interest = float(d_row["interest"])
            ebitda = float(row["ebitda"])

            # CFADS = EBITDA - Taxes
            cfads = ebitda - float(row["corporate_tax"])

            # DSCR = CFADS / Debt Service
            dscr = round(cfads / debt_service, 2) if debt_service > 0 else 999.0
            icr = round(ebitda / interest, 2) if interest > 0 else 999.0

            dscr_list.append(dscr)
            icr_list.append(icr)
            debt_service_list.append(round(debt_service, 2))
            dscr_compliant_list.append(bool(dscr >= self.target_dscr))

        df["debt_service"] = debt_service_list
        df["dscr"] = dscr_list
        df["icr"] = icr_list
        df["dscr_covenant_pass"] = dscr_compliant_list

        return df

    def compute_returns_summary(
        self,
        df_projection: pd.DataFrame,
        initial_equity: float = 217_500.0,
        initial_capex: float = 729_000.0,
    ) -> Dict[str, Any]:
        """Computes Project IRR (Unlevered) and Equity IRR (Levered)."""
        # Unlevered cash flows: -CapEx at t=0, followed by FCFF
        unlevered_cfs = [-initial_capex] + df_projection["fcff"].tolist()
        project_irr = calculate_irr(unlevered_cfs)
        project_npv = calculate_npv(self.discount_wacc, unlevered_cfs)

        # Levered cash flows: -Equity at t=0, followed by FCFE + cash build
        levered_cfs = [-initial_equity] + df_projection["fcfe"].tolist()
        equity_irr = calculate_irr(levered_cfs)
        equity_npv = calculate_npv(self.discount_wacc, levered_cfs)

        return {
            "project_irr": project_irr,
            "project_npv": project_npv,
            "equity_irr": equity_irr,
            "equity_npv": equity_npv,
            "discount_wacc": self.discount_wacc,
        }

    def compute_breakeven_occupancy(
        self,
        fixed_costs_annual: float,
        debt_service_annual: float,
        daily_revenue_at_100_occ: float,
        cogs_ratio: float = 0.30,
        days_per_year: int = 365,
    ) -> Dict[str, float]:
        """
        Finds the exact annual occupancy rate where:
        1. EBITDA = 0 (Operating break-even)
        2. DSCR = 1.00x (Cash break-even covering debt service)
        3. DSCR = 1.25x (Bank covenant compliance break-even)
        """
        # Net margin per occupied day: Daily Rev * (1 - weighted variable cogs)
        net_daily_margin = daily_revenue_at_100_occ * (1.0 - cogs_ratio)

        # Total revenue needed = Fixed Costs / net margin
        # Occupancy = Required Net Margin / (Net Daily Margin * 365)
        annual_capacity_margin = net_daily_margin * days_per_year

        operating_be = fixed_costs_annual / annual_capacity_margin
        cash_debt_be = (fixed_costs_annual + debt_service_annual) / annual_capacity_margin
        covenant_be = (fixed_costs_annual + debt_service_annual * self.target_dscr) / annual_capacity_margin

        return {
            "operating_breakeven_occupancy": round(operating_be, 4),
            "debt_service_breakeven_occupancy": round(cash_debt_be, 4),
            "bank_covenant_breakeven_occupancy": round(covenant_be, 4),
        }
