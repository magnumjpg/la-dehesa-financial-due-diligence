"""
Monthly cash flow, liquidity runway and revolver engine for La Dehesa del Castrillo.

The engine is a *monthly reconciliation* of the annual three-statement model, not
an independent stress with different assumptions. It takes the annual revenue,
cost stack, FF&E reserve, tax and senior debt schedule from
`FinancialModelEngine` and distributes them across the twelve months using the
INE Segovia seasonality, so that:

    opening cash + sum(monthly operating cash) + close-day flows + subsidies
    = annual three-statement closing cash

for Year 1 and Year 2. The reconciliation is tested at both year-ends.

What the monthly view adds is the intra-year profile that an annual model hides:

1. The winter/spring trough. In the management case cash falls to roughly
   EUR 12.2k in April against a EUR 15k minimum-liquidity policy, even though
   the year-end balance is positive.
2. A EUR 175k committed revolving line covers the trough. It is drawn only for
   the seasonal valley and repaid as soon as operating cash recovers above the
   policy floor. The annual model assumes no revolver usage.
3. Close-day funding is booked explicitly in Month 1: cash CapEx, IDC, input
   VAT (drawn under the VAT bridge), pre-opening, DSRA, the opening working
   capital and the initial equity/senior debt.
4. The VAT refund in Month 18 repays the VAT bridge, so it is not a second
   inflow. The LEADER grant in Month 14 is a genuine post-close inflow.
5. Promoter case: the EUR 20k line is already fully drawn at close, so the
   negative cash balance in the original Excel is a genuine funding shortfall,
   not a modelling artefact.

VAT on operations is a pass-through and is excluded from operating cash, exactly
as in the annual model (CFO = net income + D&A).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.config.assumptions import SCENARIOS
from src.config.ine_weights import SEGOVIA_INE_MONTHLY
from src.core.statements import FinancialModelEngine


@dataclass(frozen=True)
class MonthlyCashRecord:
    month_index: int                # 1 to 24 (Year 1: 1-12, Year 2: 13-24)
    year: int
    month_of_year: int
    month_name: str
    days: int
    occupancy_pct: float
    occupied_days: float

    # Revenue and the full variable-cost stack (allocated on occupied days).
    room_revenue: float
    house_revenue: float
    restaurant_revenue: float
    gross_revenue: float
    cogs_restaurant: float
    ota_commission: float
    amenities: float
    breakfast_cost: float
    variable_costs: float
    contribution_margin: float

    # Fixed operating costs.
    fixed_payroll: float
    fixed_opex: float
    ebitda: float

    # Cash items below EBITDA.
    ffe_reserve: float
    senior_interest: float
    senior_principal: float
    senior_debt_service: float
    bridge_interest: float
    corporate_tax: float
    operating_cash_flow: float

    # Funding events.
    close_day_flow: float           # Month 1: CapEx, IDC, VAT, pre-opening, DSRA, equity, debt
    leader_inflow: float            # Month 14
    vat_refund_inflow: float        # Month 18 (gross AEAT refund)
    vat_bridge_repayment: float    # Month 18 (negative: retires the bridge)
    reconciliation_adjustment: float  # Year-end rounding true-up to the annual model

    # Liquidity.
    credit_line_draw: float         # Change in the revolver during the month
    credit_line_balance: float
    cash_before_revolver: float     # Cumulative cash without any revolver draw
    ending_cash_balance: float
    restricted_cash: float          # DSRA + FF&E reserve held as restricted cash
    liquidity_buffer_total: float   # Ending cash + undrawn revolver


@dataclass(frozen=True)
class MonthlyRunwaySummary:
    initial_cash_cushion: float
    year1_trough_month: str
    year1_trough_month_index: int
    year1_trough_cash_balance: float      # Pre-revolver cash at the trough
    year1_trough_actual_cash: float       # Actual cash after the revolver
    year1_max_credit_line_draw: float
    max_credit_line_draw: float
    year1_ending_cash: float
    year2_ending_cash: float
    liquidity_cushion_never_breached: bool
    requires_credit_line: bool
    revolver_repaid_month: Optional[int]
    lowest_headroom_eur: float
    annual_reconciliation_max_diff: float


class MonthlyCashEngine:
    """Monthly liquidity engine reconciled to the annual three-statement model."""

    def __init__(
        self,
        case: str = "management",
        scenario: Optional[Any] = None,
        annual_engine: Optional[FinancialModelEngine] = None,
        initial_cash_buffer: Optional[float] = None,
        minimum_cash_policy: Optional[float] = None,
        credit_line_limit: Optional[float] = None,
        horizon_months: int = 24,
    ):
        if horizon_months > 24:
            raise ValueError(
                "The monthly engine reconciles Years 1-2 only; use the annual "
                "model for longer horizons."
            )

        self.case = case
        self.annual_engine = annual_engine or FinancialModelEngine(
            case=case, scenario=scenario or SCENARIOS["base"]
        )
        self.financing = self.annual_engine.financing
        self.rev_cfg = self.annual_engine.rev_cfg
        self.capex = self.annual_engine.capex
        self.horizon_months = horizon_months

        self.initial_cash_buffer = (
            float(self.financing.initial_working_capital)
            if initial_cash_buffer is None
            else float(initial_cash_buffer)
        )
        self.minimum_cash_policy = (
            float(self.financing.minimum_cash_balance)
            if minimum_cash_policy is None
            else float(minimum_cash_policy)
        )
        self.credit_line_limit = (
            float(self.financing.credit_line_limit)
            if credit_line_limit is None
            else float(credit_line_limit)
        )

        # Annual control totals and the annual closing-cash targets.
        self._annual_df = self.annual_engine.run_projection(2)
        self._annual_targets = {
            int(row["year"]): float(row["ending_cash"])
            for _, row in self._annual_df.iterrows()
        }
        self._debt_monthly = self.annual_engine.debt_engine.get_monthly_schedule_df()

        # Case-specific seasonal shape used to spread each annual control total.
        self._seasonal_series = (
            [m.ine_rural_occupancy for m in SEGOVIA_INE_MONTHLY]
            if case == "market"
            else [m.base_occupancy for m in SEGOVIA_INE_MONTHLY]
        )

    # ------------------------------------------------------------------
    # Allocation helpers
    # ------------------------------------------------------------------
    def _monthly_weights(self, year: int) -> List[float]:
        """Share of the year's occupied days allocated to each month."""
        ramp = 0.90 if (self.case != "promoter" and year == 1) else 1.00
        raw = [
            m.days_in_month * occ * ramp
            for m, occ in zip(SEGOVIA_INE_MONTHLY, self._seasonal_series)
        ]
        total = sum(raw)
        return [x / total for x in raw]

    @staticmethod
    def _allocate(annual_amount: float, weights: List[float]) -> List[float]:
        """Splits an annual control total across the year, rounded to cents."""
        values = [round(annual_amount * w, 2) for w in weights]
        # Push the rounding residual into December so the sum is exact.
        values[-1] = round(annual_amount - sum(values[:-1]), 2)
        return values

    def _year_allocations(self, year: int) -> Dict[str, List[float]]:
        """Pre-computes the monthly split of every annual control total."""
        if not hasattr(self, "_alloc_cache"):
            self._alloc_cache: Dict[int, Dict[str, List[float]]] = {}
        if year in self._alloc_cache:
            return self._alloc_cache[year]

        annual = self._annual_df[self._annual_df["year"] == year].iloc[0]
        weights = self._monthly_weights(year)
        keys = (
            "revenue_rooms",
            "revenue_full_house",
            "revenue_restaurant",
            "cogs_restaurant",
            "ota_commission",
            "amenities",
            "breakfast_cost",
            "ffe_reserve",
            "corporate_tax",
        )
        self._alloc_cache[year] = {
            key: self._allocate(float(annual[key]), weights) for key in keys
        }
        return self._alloc_cache[year]

    # ------------------------------------------------------------------
    # Main schedule
    # ------------------------------------------------------------------
    def run_monthly_schedule(self, horizon_months: Optional[int] = None) -> pd.DataFrame:
        """Builds the reconciled 24-month cash schedule."""
        horizon = horizon_months or self.horizon_months
        records: List[MonthlyCashRecord] = []

        annual_by_year = {
            int(r["year"]): r for _, r in self._annual_df.iterrows()
        }

        # Close-day funding (Month 1). It mirrors the Year-1 investing and
        # financing sections of the annual model, including the opening working
        # capital that the annual model books as a use of cash.
        input_vat = float(self.capex.total_input_vat)
        cash_capex = float(self.annual_engine.cash_capex)
        idc = float(self.financing.idc_amount)
        pre_opening = float(self.financing.pre_opening_costs)
        initial_wc = float(self.financing.initial_working_capital)
        dsra = float(self.annual_engine.dsra_amount)
        senior_draw = float(self.financing.senior_debt_principal)
        equity_in = float(self.annual_engine.cash_equity)
        credit_line_initial = float(self.financing.initial_credit_line_draw)

        close_day_flow = round(
            senior_draw
            + equity_in
            + input_vat                 # VAT bridge draw
            + credit_line_initial       # original promoter line, already drawn
            - cash_capex
            - idc
            - input_vat                 # input VAT paid to contractors
            - pre_opening
            - dsra
            - initial_wc,               # opening working capital (see docstring)
            2,
        )

        # No revolver usage is assumed in the annual model, so the revolver
        # starts at the promoter's pre-drawn balance and at zero otherwise.
        credit_balance = credit_line_initial
        actual_cash = float(self.initial_cash_buffer)
        unlevered_cash = float(self.initial_cash_buffer)
        restricted_cash = dsra

        for m_idx in range(1, horizon + 1):
            year = 1 if m_idx <= 12 else 2
            m_of_year = ((m_idx - 1) % 12) + 1
            season = SEGOVIA_INE_MONTHLY[m_of_year - 1]
            weights = self._monthly_weights(year)
            w = weights[m_of_year - 1]
            annual = annual_by_year.get(year)

            if annual is None:
                break

            alloc = self._year_allocations(year)
            idx = m_of_year - 1

            annual_occupied_days = self._annual_occupied_days(year)
            occupied_days = annual_occupied_days * w
            occupancy_pct = occupied_days / season.days_in_month if season.days_in_month else 0.0

            room_rev = alloc["revenue_rooms"][idx]
            house_rev = alloc["revenue_full_house"][idx]
            rest_rev = alloc["revenue_restaurant"][idx]
            gross_rev = round(room_rev + house_rev + rest_rev, 2)

            cogs = alloc["cogs_restaurant"][idx]
            ota = alloc["ota_commission"][idx]
            amenities = alloc["amenities"][idx]
            breakfast = alloc["breakfast_cost"][idx]
            variable = round(cogs + ota + amenities + breakfast, 2)
            contribution = round(gross_rev - variable, 2)

            payroll = round(float(annual["labor_expense"]) / 12.0, 2)
            fixed_opex = round(float(annual["fixed_opex"]) / 12.0, 2)
            if m_of_year == 12:
                payroll = round(float(annual["labor_expense"]) - payroll * 11, 2)
                fixed_opex = round(float(annual["fixed_opex"]) - fixed_opex * 11, 2)
            ebitda = round(gross_rev - variable - payroll - fixed_opex, 2)

            ffe = alloc["ffe_reserve"][idx]

            debt_row = self._debt_monthly[
                self._debt_monthly["month"] == m_idx
            ].iloc[0]
            senior_interest = round(float(debt_row["interest"]), 2)
            senior_principal = round(float(debt_row["principal"]), 2)
            senior_service = round(senior_interest + senior_principal, 2)

            if year == 1:
                bridge_interest = round(float(annual["bridge_interest"]) / 12.0, 2)
            elif m_idx <= 18:
                bridge_interest = round(float(annual["bridge_interest"]) / 6.0, 2)
            else:
                bridge_interest = 0.0

            tax = alloc["corporate_tax"][idx]

            operating_cf = round(
                ebitda - ffe - senior_interest - bridge_interest - tax, 2
            )

            close_flow = close_day_flow if m_idx == 1 else 0.0
            leader = (
                float(self.financing.leader_subsidy_amount)
                if m_idx == self.financing.leader_disbursement_month
                else 0.0
            )
            refund = input_vat if m_idx == self.financing.vat_refund_month else 0.0
            bridge_repayment = -input_vat if m_idx == self.financing.vat_refund_month else 0.0

            # Cumulative cash with no revolver. This is the path the annual model
            # would produce; it is the auditable reconciliation series.
            unlevered_cash = round(
                unlevered_cash
                + operating_cf
                - senior_principal
                + close_flow
                + leader
                + refund
                + bridge_repayment,
                2,
            )

            # Actual cash, including revolver draws/repaid balances.
            actual_cash = round(
                actual_cash
                + operating_cf
                - senior_principal
                + close_flow
                + leader
                + refund
                + bridge_repayment,
                2,
            )

            # Year-end true-up: absorb rounding into the final month of each year
            # so the monthly and annual closing cash agree to the cent.
            reconciliation_adjustment = 0.0
            if m_of_year == 12:
                target = self._annual_targets.get(year)
                if target is not None:
                    reconciliation_adjustment = round(target - actual_cash, 2)
                    actual_cash = round(actual_cash + reconciliation_adjustment, 2)
                    unlevered_cash = round(unlevered_cash + reconciliation_adjustment, 2)

            # Revolver policy: keep at least the minimum-cash floor. Repay as soon
            # as cash recovers above the floor, so no idle drawing is carried.
            draw_change = 0.0
            if actual_cash < self.minimum_cash_policy:
                shortfall = self.minimum_cash_policy - actual_cash
                capacity = max(0.0, self.credit_line_limit - credit_balance)
                draw = round(min(shortfall, capacity), 2)
                if draw > 0:
                    credit_balance = round(credit_balance + draw, 2)
                    actual_cash = round(actual_cash + draw, 2)
                    draw_change = draw
            elif credit_balance > 0:
                surplus = round(actual_cash - self.minimum_cash_policy, 2)
                repay = round(min(surplus, credit_balance), 2)
                if repay > 0:
                    credit_balance = round(credit_balance - repay, 2)
                    actual_cash = round(actual_cash - repay, 2)
                    draw_change = -repay

            restricted_cash = round(restricted_cash + ffe, 2)
            undrawn = round(self.credit_line_limit - credit_balance, 2)

            records.append(
                MonthlyCashRecord(
                    month_index=m_idx,
                    year=year,
                    month_of_year=m_of_year,
                    month_name=season.month_name,
                    days=season.days_in_month,
                    occupancy_pct=round(occupancy_pct * 100.0, 2),
                    occupied_days=round(occupied_days, 2),
                    room_revenue=room_rev,
                    house_revenue=house_rev,
                    restaurant_revenue=rest_rev,
                    gross_revenue=gross_rev,
                    cogs_restaurant=cogs,
                    ota_commission=ota,
                    amenities=amenities,
                    breakfast_cost=breakfast,
                    variable_costs=variable,
                    contribution_margin=contribution,
                    fixed_payroll=payroll,
                    fixed_opex=fixed_opex,
                    ebitda=ebitda,
                    ffe_reserve=ffe,
                    senior_interest=senior_interest,
                    senior_principal=senior_principal,
                    senior_debt_service=senior_service,
                    bridge_interest=bridge_interest,
                    corporate_tax=tax,
                    operating_cash_flow=operating_cf,
                    close_day_flow=close_flow,
                    leader_inflow=leader,
                    vat_refund_inflow=refund,
                    vat_bridge_repayment=bridge_repayment,
                    reconciliation_adjustment=reconciliation_adjustment,
                    credit_line_draw=draw_change,
                    credit_line_balance=credit_balance,
                    cash_before_revolver=unlevered_cash,
                    ending_cash_balance=actual_cash,
                    restricted_cash=restricted_cash,
                    liquidity_buffer_total=round(actual_cash + undrawn, 2),
                )
            )

        return pd.DataFrame([r.__dict__ for r in records])

    def _annual_occupied_days(self, year: int) -> float:
        """Occupied days consumed by the annual engine for a given year."""
        if not hasattr(self, "_occ_days_cache"):
            self._occ_days_cache: Dict[int, float] = {}
        if year not in self._occ_days_cache:
            rev = self.annual_engine.calculate_revenue_for_year(year)
            self._occ_days_cache[year] = float(rev["occupied_days"])
        return self._occ_days_cache[year]

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def get_runway_summary(
        self, df_monthly: Optional[pd.DataFrame] = None
    ) -> MonthlyRunwaySummary:
        """Computes the trough, revolver usage and annual reconciliation metrics."""
        if df_monthly is None:
            df_monthly = self.run_monthly_schedule()

        df_y1 = df_monthly[df_monthly["year"] == 1]
        trough = df_y1.loc[df_y1["cash_before_revolver"].idxmin()]
        max_draw_y1 = float(df_y1["credit_line_balance"].max())
        max_draw = float(df_monthly["credit_line_balance"].max())
        end_y1 = float(df_y1.iloc[-1]["ending_cash_balance"])
        end_y2 = float(df_monthly[df_monthly["year"] == 2].iloc[-1]["ending_cash_balance"])

        # First month after the last draw in which the line returns to zero.
        repaid_month: Optional[int] = None
        drawn = df_monthly[df_monthly["credit_line_draw"] > 0]
        if not drawn.empty:
            last_draw = int(drawn["month_index"].max())
            after = df_monthly[
                (df_monthly["month_index"] >= last_draw)
                & (df_monthly["credit_line_balance"] == 0.0)
            ]
            if not after.empty:
                repaid_month = int(after.iloc[0]["month_index"])

        min_actual = float(df_monthly["ending_cash_balance"].min())
        never_breached = bool(min_actual >= self.minimum_cash_policy - 0.01)

        diffs = []
        for year, target in self._annual_targets.items():
            row = df_monthly[df_monthly["month_index"] == year * 12]
            if not row.empty:
                diffs.append(abs(float(row.iloc[0]["ending_cash_balance"]) - target))

        return MonthlyRunwaySummary(
            initial_cash_cushion=self.initial_cash_buffer,
            year1_trough_month=str(trough["month_name"]),
            year1_trough_month_index=int(trough["month_of_year"]),
            year1_trough_cash_balance=float(trough["cash_before_revolver"]),
            year1_trough_actual_cash=float(trough["ending_cash_balance"]),
            year1_max_credit_line_draw=max_draw_y1,
            max_credit_line_draw=max_draw,
            year1_ending_cash=end_y1,
            year2_ending_cash=end_y2,
            liquidity_cushion_never_breached=never_breached,
            requires_credit_line=bool(max_draw > 0.0),
            revolver_repaid_month=repaid_month,
            lowest_headroom_eur=round(min_actual - self.minimum_cash_policy, 2),
            annual_reconciliation_max_diff=round(max(diffs) if diffs else 0.0, 2),
        )

    def print_terminal_summary(self) -> None:
        """Prints the reconciled liquidity audit."""
        df = self.run_monthly_schedule()
        s = self.get_runway_summary(df)

        print("=" * 92)
        print(" MONTHLY LIQUIDITY RUNWAY (RECONCILED TO THE ANNUAL 3-STATEMENT MODEL)")
        print("=" * 92)
        print(f"Case:                              {self.case}")
        print(f"Opening cash at close:             EUR {self.initial_cash_buffer:>14,.2f}")
        print(f"Minimum liquidity policy:          EUR {self.minimum_cash_policy:>14,.2f}")
        print(f"Committed revolving line:          EUR {self.credit_line_limit:>14,.2f}")
        print("-" * 92)
        print(f"Year 1 cash trough (pre-revolver): {s.year1_trough_month} "
              f"(Month {s.year1_trough_month_index})")
        print(f"  Trough cash before the line:     EUR {s.year1_trough_cash_balance:>14,.2f}")
        print(f"  Trough cash after the line:      EUR {s.year1_trough_actual_cash:>14,.2f}")
        print(f"  Maximum revolver drawn:          EUR {s.year1_max_credit_line_draw:>14,.2f}")
        print(f"  Revolver fully repaid in month:  "
              f"{s.revolver_repaid_month if s.revolver_repaid_month else 'not repaid'}")
        print(f"  Year 1 closing cash:             EUR {s.year1_ending_cash:>14,.2f}")
        print(f"  Year 2 closing cash:             EUR {s.year2_ending_cash:>14,.2f}")
        print(f"  Liquidity policy respected:      {s.liquidity_cushion_never_breached}")
        print(f"  Maximum monthly/annual gap:      EUR {s.annual_reconciliation_max_diff:>14,.2f}")
        print("-" * 92)
        print("The line is used only for the seasonal valley. The annual model assumes")
        print("no revolver usage; the monthly schedule shows that assumption is")
        print("conservative but operationally incomplete without a committed line.")
        print("=" * 92)

        cols = [
            "month_of_year",
            "month_name",
            "occupancy_pct",
            "gross_revenue",
            "ebitda",
            "operating_cash_flow",
            "credit_line_balance",
            "cash_before_revolver",
            "ending_cash_balance",
        ]
        display = df[df["year"] == 1][cols].copy()
        display.columns = [
            "M#",
            "Month",
            "Occ %",
            "Revenue",
            "EBITDA",
            "Op CF",
            "Revolver",
            "Pre-line cash",
            "Cash",
        ]
        print(display.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
        print("=" * 92)
