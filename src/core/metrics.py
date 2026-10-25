"""
Banking covenant, investment-return and break-even metrics.

Computes:
1. Debt Service Coverage Ratio (DSCR = CFADS / senior debt service), where
   CFADS = EBITDA - FF&E reserve - cash tax.
2. Interest Coverage Ratio (ICR = EBITDA / interest).
3. Levered/unlevered IRR and NPV, including the exit at a cap rate.
4. Break-even occupancy and ADR required to reach operating break-even, a
   1.00x debt-service cover, the 1.25x covenant and a 10% equity IRR.

The break-even analysis re-runs the full engine under scaled demand, so it is
consistent with the P&L, the cost stack, the tax shield and the funding plug.
"""

from typing import Any, Dict, List, Optional
from dataclasses import replace

import numpy as np
import pandas as pd

from src.config.assumptions import SCENARIOS, ScenarioDrivers


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
       use bisection on each bracket. This avoids a silent hardcoded fallback.
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
    """Calculates bank underwriting covenants and investment returns."""

    def __init__(self, target_dscr: float = 1.25, discount_wacc: float = 0.08):
        self.target_dscr = target_dscr
        self.discount_wacc = discount_wacc

    def compute_credit_kpis(self, df_projection: pd.DataFrame, debt_schedule: pd.DataFrame) -> pd.DataFrame:
        """
        Enriches the annual projection with DSCR, ICR and debt-service metrics.

        CFADS is taken from the P&L engine (EBITDA - FF&E reserve - cash tax),
        not from EBITDA alone: the FF&E reserve is a contractual cash set-aside
        and the tax is a cash outflow that ranks ahead of debt service.
        """
        df = df_projection.copy()

        dscr_list = []
        icr_list = []
        debt_service_list = []
        dscr_compliant_list = []

        for idx, row in df.iterrows():
            y = int(row["year"])
            d_row = debt_schedule[debt_schedule["year"] == y].iloc[0]
            debt_service = float(d_row["payment"])
            interest = float(d_row["interest"])
            ebitda = float(row["ebitda"])

            cfads = (
                float(row["cfads"]) if "cfads" in df.columns
                else ebitda - float(row["corporate_tax"])
            )

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
        initial_equity: float,
        initial_capex: float,
        exit_cap_rate: float = 0.085,
    ) -> Dict[str, Any]:
        """
        Computes Project IRR (unlevered) and Equity IRR (levered).

        `initial_capex` is the all-in project investment at t=0 (CapEx + IDC +
        pre-opening + working capital + DSRA) and `initial_equity` is the total
        equity at close (cash equity + in-kind land). A terminal value at the
        end of the projection is added using an exit cap rate on final EBITDA.
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
        # Floor the terminal value at zero: a loss-making asset does not have a
        # negative resale value. The operating losses still flow through.
        terminal_value = (
            max(0.0, terminal_ebitda / exit_cap_rate) if exit_cap_rate > 0 else 0.0
        )
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


class BreakEvenEngine:
    """
    Demand-side break-even analysis.

    Solves, by bisection on the scenario multipliers, for:
    1. The occupancy that makes mature EBITDA zero.
    2. The occupancy that makes the minimum DSCR equal 1.00x.
    3. The occupancy that makes the minimum DSCR equal the 1.25x covenant.
    4. The ADR uplift that delivers the 1.25x covenant at base occupancy.
    5. The ADR uplift that delivers a 10% equity IRR with an 8.5% exit.
    """

    def __init__(self, case: str = "management", exit_cap_rate: float = 0.085):
        self.case = case
        self.exit_cap_rate = exit_cap_rate

    def _engine(self, occ_mult: float = 1.0, adr_mult: float = 1.0):
        from src.core.statements import FinancialModelEngine

        scenario = replace(
            SCENARIOS["base"],
            occupancy_multiplier=occ_mult,
            adr_multiplier=adr_mult,
        )
        return FinancialModelEngine(case=self.case, scenario=scenario)

    def _solve(self, metric, target: float, attr: str, lo: float = 0.10, hi: float = 4.0) -> Optional[float]:
        f_lo, f_hi = metric(lo) - target, metric(hi) - target
        if f_lo * f_hi > 0:
            return None
        for _ in range(60):
            mid = (lo + hi) / 2.0
            f_mid = metric(mid) - target
            if abs(f_mid) < 1e-6:
                return round(mid, 4)
            if f_lo * f_mid <= 0:
                hi = mid
            else:
                lo, f_lo = mid, f_mid
        return round((lo + hi) / 2.0, 4)

    def _mature_ebitda(self, occ_mult: float) -> float:
        engine = self._engine(occ_mult=occ_mult)
        return float(engine.run_projection(3).iloc[2]["ebitda"])

    def _min_dscr(self, occ_mult: float) -> float:
        engine = self._engine(occ_mult=occ_mult)
        df = engine.run_projection(5)
        return float((df["cfads"] / df["debt_service"]).min())

    def _equity_irr_exit(self, adr_mult: float) -> float:
        engine = self._engine(adr_mult=adr_mult)
        df = engine.run_projection(5)
        returns = CreditMetricsEngine().compute_returns_summary(
            df,
            initial_equity=engine.total_equity_at_close,
            initial_capex=engine.total_project_investment,
            exit_cap_rate=self.exit_cap_rate,
        )
        return float(returns["equity_irr_exit"] or -0.99)

    def _min_dscr_adr(self, adr_mult: float) -> float:
        engine = self._engine(adr_mult=adr_mult)
        df = engine.run_projection(5)
        return float((df["cfads"] / df["debt_service"]).min())

    @staticmethod
    def _implied_occupancy(engine, year: int = 3) -> float:
        rev = engine.calculate_revenue_for_year(year)
        return round(float(rev["occupied_days"]) / 365.0, 4)

    def compute(self) -> Dict[str, Any]:
        base = self._engine()
        base_rev = base.calculate_revenue_for_year(1)
        base_occ_y1 = round(float(base_rev["occupied_days"]) / 365.0, 4)
        base_occ_mature = self._implied_occupancy(base, 3)

        op_mult = self._solve(self._mature_ebitda, 0.0, "occupancy")
        ds_mult = self._solve(self._min_dscr, 1.00, "occupancy")
        cov_mult = self._solve(self._min_dscr, 1.25, "occupancy")
        adr_cov = self._solve(self._min_dscr_adr, 1.25, "adr")
        adr_irr = self._solve(self._equity_irr_exit, 0.10, "adr")

        def occ(mult: Optional[float], year: int = 3) -> Optional[float]:
            if mult is None:
                return None
            return self._implied_occupancy(self._engine(occ_mult=mult), year)

        result = {
            "case": self.case,
            "base_occupancy_y1": base_occ_y1,
            "base_occupancy_mature": base_occ_mature,
            "operating_breakeven_occupancy_mature": occ(op_mult, 3),
            "debt_service_breakeven_occupancy_mature": occ(ds_mult, 3),
            "covenant_breakeven_occupancy_mature": occ(cov_mult, 3),
            "covenant_breakeven_adr_multiplier": adr_cov,
            "covenant_breakeven_adr": (
                round(85.0 * adr_cov, 2) if adr_cov is not None else None
            ),
            "equity_irr_10pct_adr_multiplier": adr_irr,
            "equity_irr_10pct_adr": (
                round(85.0 * adr_irr, 2) if adr_irr is not None else None
            ),
        }
        return result
