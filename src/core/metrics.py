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


def _npv_at(rate: float, cash_flows: List[float]) -> float:
    return sum(cf / ((1.0 + rate) ** t) for t, cf in enumerate(cash_flows))


def calculate_irr(cash_flows: List[float], max_iter: int = 1000, tol: float = 1e-7) -> Optional[float]:
    """
    Computes the Internal Rate of Return (IRR).

    Strategy:
    1. Fast Newton-Raphson from 10%.
    2. If Newton fails to converge, scan for sign changes on a dense grid and
       use bisection on each bracket. This avoids the silent hardcoded fallback
       that previously returned 15.57% when NumPy's `np.irr` was unavailable.
    """
    has_pos = any(cf > 0 for cf in cash_flows)
    has_neg = any(cf < 0 for cf in cash_flows)
    if not (has_pos and has_neg):
        return None

    # Newton-Raphson
    rate = 0.10
    for _ in range(max_iter):
        npv = _npv_at(rate, cash_flows)
        d_npv = sum(
            -t * cf / ((1.0 + rate) ** (t + 1))
            for t, cf in enumerate(cash_flows)
        )
        if abs(d_npv) < 1e-12:
            break
        new_rate = rate - npv / d_npv
        if not np.isfinite(new_rate) or new_rate <= -0.9999:
            break
        if abs(new_rate - rate) < tol:
            return round(new_rate, 6)
        rate = new_rate

    # Bisection fallback on a dense grid of brackets.
    grid = [-0.9999 + i * (10.0 + 0.9999) / 2000.0 for i in range(2001)]
    previous_rate = grid[0]
    previous_npv = _npv_at(previous_rate, cash_flows)
    for current_rate in grid[1:]:
        current_npv = _npv_at(current_rate, cash_flows)
        if previous_npv == 0.0:
            return round(previous_rate, 6)
        if previous_npv * current_npv < 0.0:
            low, high = previous_rate, current_rate
            for _ in range(200):
                mid = (low + high) / 2.0
                mid_npv = _npv_at(mid, cash_flows)
                if abs(mid_npv) < 1e-8:
                    return round(mid, 6)
                if _npv_at(low, cash_flows) * mid_npv < 0.0:
                    high = mid
                else:
                    low = mid
            return round((low + high) / 2.0, 6)
        previous_rate, previous_npv = current_rate, current_npv

    return None


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
        exit_cap_rate: float = 0.085,
    ) -> Dict[str, Any]:
        """
        Computes Project IRR (unlevered) and Equity IRR (levered).

        The initial CapEx and the initial equity are placed at t=0; the
        operating FCF series must therefore exclude the Year-1 CapEx (which is
        already in `fcff_ex_capex` / `fcfe_proper`). A terminal value at the end
        of the projection is added using an exit cap rate on final EBITDA.
        """
        if "fcff_ex_capex" in df_projection.columns:
            fcff_ops = df_projection["fcff_ex_capex"].tolist()
        else:
            fcff_ops = df_projection["fcff"].tolist()
        if "fcfe_proper" in df_projection.columns:
            fcfe_ops = df_projection["fcfe_proper"].tolist()
        else:
            fcfe_ops = df_projection["fcfe"].tolist()

        project_cfs = [-initial_capex] + fcff_ops
        equity_cfs = [-initial_equity] + fcfe_ops

        terminal_ebitda = float(df_projection.iloc[-1]["ebitda"])
        terminal_value = terminal_ebitda / exit_cap_rate if exit_cap_rate > 0 else 0.0
        ending_debt = float(df_projection.iloc[-1]["total_debt"])

        project_cfs_exit = list(project_cfs)
        equity_cfs_exit = list(equity_cfs)
        project_cfs_exit[-1] += terminal_value
        equity_cfs_exit[-1] += max(0.0, terminal_value - ending_debt)

        project_irr = calculate_irr(project_cfs)
        equity_irr = calculate_irr(equity_cfs)
        project_irr_exit = calculate_irr(project_cfs_exit)
        equity_irr_exit = calculate_irr(equity_cfs_exit)
        project_npv = calculate_npv(self.discount_wacc, project_cfs_exit)
        equity_npv = calculate_npv(self.discount_wacc, equity_cfs_exit)

        project_moic = (sum(fcff_ops) + terminal_value) / initial_capex if initial_capex else None
        equity_moic = (
            (sum(fcfe_ops) + max(0.0, terminal_value - ending_debt)) / initial_equity
            if initial_equity else None
        )

        return {
            "project_irr": project_irr,
            "project_irr_exit": project_irr_exit,
            "project_npv": project_npv,
            "equity_irr": equity_irr,
            "equity_irr_exit": equity_irr_exit,
            "equity_npv": equity_npv,
            "terminal_value": round(terminal_value, 2),
            "terminal_cap_rate": exit_cap_rate,
            "project_moic": round(project_moic, 4) if project_moic is not None else None,
            "equity_moic": round(equity_moic, 4) if equity_moic is not None else None,
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
