"""
Monthly Cash Flow, Runway & Working Capital Engine for La Dehesa del Castrillo S.L.

Standalone operating-liquidity stress:
1. Translates annual projections into month-by-month cash burn and runway.
2. Models Segovia winter trough (Jan-Feb), spring lift, and summer cash surge.
3. Identifies the exact Cash Trough month in Year 1.
4. Tests two funding states: unfunded (adjusted cash at close is negative) and
   funded after the recommended €70,768.18 equity injection.
5. Treats the AEAT VAT refund as a repayment of the VAT bridge, not as a second
   inflow. The LEADER grant (€163,000) is a genuine post-close inflow.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    FixedOpexStructure,
    LaborStructure,
    RevenueModelConfig,
)
from src.config.ine_weights import SEGOVIA_INE_MONTHLY, MonthlySeasonality


@dataclass(frozen=True)
class MonthlyCashRecord:
    month_index: int              # 1 to 24 (Year 1: 1-12, Year 2: 13-24)
    year: int                     # 1 or 2
    month_of_year: int            # 1 to 12
    month_name: str
    days: int
    occupancy_pct: float
    gross_revenue: float
    variable_costs: float
    contribution_margin: float
    fixed_payroll: float
    fixed_opex: float
    senior_debt_service: float
    net_operating_cash_flow: float
    tax_bridge_inflows: float     # AEAT VAT refund, LEADER grant, or equity
    vat_bridge_repayment: float   # Refund used to retire the VAT bridge (negative)
    credit_line_drawn: float      # Utilization of €50k revolving facility
    ending_cash_balance: float
    liquidity_buffer_total: float # Ending cash + undrawn credit line


@dataclass(frozen=True)
class MonthlyRunwaySummary:
    initial_cash_cushion: float
    year1_trough_month: str
    year1_trough_month_index: int
    year1_trough_cash_balance: float
    year1_max_credit_line_draw: float
    year1_ending_cash: float
    year2_ending_cash: float
    liquidity_cushion_never_breached: bool
    lowest_headroom_eur: float


class MonthlyCashEngine:
    """Simulates monthly cash flows, runway, and working capital over 24 months."""

    def __init__(
        self,
        capex: CapExStructure = CapExStructure(),
        financing: FinancingStructure = FinancingStructure(),
        labor: LaborStructure = LaborStructure(),
        opex: FixedOpexStructure = FixedOpexStructure(),
        rev_cfg: RevenueModelConfig = RevenueModelConfig(),
        initial_cash_buffer: float = -55_978.44,
        minimum_cash_policy: float = 10_000.0,
        vat_refund_amount: float = 143_596.37,
    ):
        self.capex = capex
        self.financing = financing
        self.labor = labor
        self.opex = opex
        self.rev_cfg = rev_cfg
        self.initial_cash_buffer = initial_cash_buffer
        self.minimum_cash_policy = minimum_cash_policy
        self.vat_refund_amount = vat_refund_amount

        # Monthly senior debt payment (15Y French amortization @ 3.5%, 507.5k)
        r_m = self.financing.loan_interest_rate / 12.0
        n_m = self.financing.loan_tenure_years * 12
        p = self.financing.senior_debt_principal
        self.monthly_debt_service = p * (r_m * (1 + r_m) ** n_m) / ((1 + r_m) ** n_m - 1)

    def run_monthly_schedule(self, horizon_months: int = 24) -> pd.DataFrame:
        """Executes a 24-month operational cash flow simulation."""
        monthly_payroll = self.labor.total_annual_payroll / 12.0  # €5,006.25
        monthly_opex = self.opex.total_fixed_opex / 12.0          # €1,013.25
        credit_line_limit = self.financing.credit_line_limit      # €50,000.00

        current_cash = self.initial_cash_buffer
        current_credit_draw = 0.0
        records: List[MonthlyCashRecord] = []

        for m_idx in range(1, horizon_months + 1):
            year = 1 if m_idx <= 12 else 2
            m_of_year = ((m_idx - 1) % 12) + 1
            season = SEGOVIA_INE_MONTHLY[m_of_year - 1]

            # Ramp-up calibration
            ramp = 0.90 if year == 1 else 1.00
            eff_occ = season.base_occupancy * ramp
            days = season.days_in_month
            occ_days = eff_occ * days

            # Revenue
            adr_factor = season.adr_seasonal_factor
            lodging_rev = (
                (self.rev_cfg.double_rooms_count * self.rev_cfg.double_room_adr * adr_factor)
                + (self.rev_cfg.full_house_count * self.rev_cfg.full_house_adr * adr_factor)
            ) * occ_days

            diners = (
                self.rev_cfg.double_rooms_count * self.rev_cfg.restaurant_diners_per_double_room
                + self.rev_cfg.full_house_count * self.rev_cfg.restaurant_diners_per_full_house
            ) * occ_days
            dining_rev = diners * self.rev_cfg.restaurant_average_ticket * adr_factor
            gross_rev = lodging_rev + dining_rev

            # Variable costs: F&B COGS (30%) + blended OTA commission (9% on lodging) + amenities (€35/day)
            cogs_fnb = dining_rev * self.rev_cfg.restaurant_cogs_ratio
            ota_comm = lodging_rev * 0.60 * 0.15
            amenities = 35.0 * occ_days
            tot_var = cogs_fnb + ota_comm + amenities
            cm = gross_rev - tot_var

            # Net operational cash before financing/subsidies
            net_op_cf = cm - monthly_payroll - monthly_opex - self.monthly_debt_service

            # One-off liquidity bridge milestones. The AEAT refund is received
            # and immediately used to retire the VAT bridge, so the net cash
            # effect is zero. The LEADER grant is a genuine post-close inflow.
            extra_inflows = 0.0
            bridge_repayment = 0.0
            if m_idx == 14:  # Year 2 Month 2: LEADER rural grant disbursed
                extra_inflows += self.financing.leader_subsidy_amount  # €163,000.0
            elif m_idx == 18:  # Year 2 Month 6: AEAT CapEx VAT refund received
                extra_inflows += self.vat_refund_amount
                bridge_repayment = -self.vat_refund_amount

            # Cash progression
            available_cash = current_cash + net_op_cf + extra_inflows + bridge_repayment

            # Credit line management
            credit_draw_change = 0.0
            if available_cash < self.minimum_cash_policy:
                # Need to draw from credit line
                shortfall = self.minimum_cash_policy - available_cash
                draw_capacity = credit_line_limit - current_credit_draw
                actual_draw = min(shortfall, draw_capacity)
                current_credit_draw += actual_draw
                credit_draw_change = actual_draw
                available_cash += actual_draw
            elif available_cash > (self.minimum_cash_policy + 15_000.0) and current_credit_draw > 0:
                # Excess cash repays credit line
                surplus = available_cash - (self.minimum_cash_policy + 15_000.0)
                repay = min(surplus, current_credit_draw)
                current_credit_draw -= repay
                credit_draw_change = -repay
                available_cash -= repay

            current_cash = available_cash
            total_liquidity = current_cash + (credit_line_limit - current_credit_draw)

            record = MonthlyCashRecord(
                month_index=m_idx,
                year=year,
                month_of_year=m_of_year,
                month_name=season.month_name,
                days=days,
                occupancy_pct=round(eff_occ * 100, 2),
                gross_revenue=round(gross_rev, 2),
                variable_costs=round(tot_var, 2),
                contribution_margin=round(cm, 2),
                fixed_payroll=round(monthly_payroll, 2),
                fixed_opex=round(monthly_opex, 2),
                senior_debt_service=round(self.monthly_debt_service, 2),
                net_operating_cash_flow=round(net_op_cf, 2),
                tax_bridge_inflows=round(extra_inflows, 2),
                vat_bridge_repayment=round(bridge_repayment, 2),
                credit_line_drawn=round(current_credit_draw, 2),
                ending_cash_balance=round(current_cash, 2),
                liquidity_buffer_total=round(total_liquidity, 2),
            )
            records.append(record)

        return pd.DataFrame([r.__dict__ for r in records])

    def get_runway_summary(self, df_monthly: Optional[pd.DataFrame] = None) -> MonthlyRunwaySummary:
        """Computes executive runway summary and cash trough metrics."""
        if df_monthly is None:
            df_monthly = self.run_monthly_schedule(horizon_months=24)

        df_y1 = df_monthly[df_monthly["year"] == 1]
        trough_row = df_y1.loc[df_y1["ending_cash_balance"].idxmin()]
        max_draw_y1 = df_y1["credit_line_drawn"].max()
        end_cash_y1 = df_y1.iloc[-1]["ending_cash_balance"]

        df_y2 = df_monthly[df_monthly["year"] == 2]
        end_cash_y2 = df_y2.iloc[-1]["ending_cash_balance"]

        min_liquidity = df_monthly["liquidity_buffer_total"].min()
        never_breached = bool(min_liquidity >= self.minimum_cash_policy)

        return MonthlyRunwaySummary(
            initial_cash_cushion=self.initial_cash_buffer,
            year1_trough_month=trough_row["month_name"],
            year1_trough_month_index=int(trough_row["month_of_year"]),
            year1_trough_cash_balance=float(trough_row["ending_cash_balance"]),
            year1_max_credit_line_draw=float(max_draw_y1),
            year1_ending_cash=float(end_cash_y1),
            year2_ending_cash=float(end_cash_y2),
            liquidity_cushion_never_breached=never_breached,
            lowest_headroom_eur=float(min_liquidity),
        )

    def print_terminal_summary(self):
        """Prints formatted terminal audit of monthly cash flow and runway."""
        df_monthly = self.run_monthly_schedule(horizon_months=24)
        summary = self.get_runway_summary(df_monthly)

        print("=" * 88)
        print(" YEAR 1 & YEAR 2 MONTHLY OPERATING LIQUIDITY (STANDALONE STRESS)")
        print("=" * 88)
        print(f"Opening cash at close (unfunded):  €{self.initial_cash_buffer:>14,.2f}")
        print(f"Recommended equity injection:      €{70_768.18:>14,.2f}")
        print(f"Opening cash after injection:      €{self.initial_cash_buffer + 70_768.18:>14,.2f}")
        print("-" * 88)
        print("UNFUNDED SCENARIO (default):")
        print(f"  Year 1 Cash Trough:              {summary.year1_trough_month} (Month {summary.year1_trough_month_index})")
        print(f"  Cash Trough Balance:             €{summary.year1_trough_cash_balance:>14,.2f}")
        print(f"  Max Revolving Credit Draw (Y1):  €{summary.year1_max_credit_line_draw:>14,.2f} (limit €{self.financing.credit_line_limit:,.2f})")
        print(f"  Year 1 Closing Cash:             €{summary.year1_ending_cash:>14,.2f}")
        print(f"  Year 2 Closing Cash:             €{summary.year2_ending_cash:>14,.2f}")
        print(f"  Liquidity policy respected:      {summary.liquidity_cushion_never_breached}")
        print("-" * 88)
        funded = MonthlyCashEngine(
            capex=self.capex,
            financing=self.financing,
            labor=self.labor,
            opex=self.opex,
            rev_cfg=self.rev_cfg,
            initial_cash_buffer=self.initial_cash_buffer + 70_768.18,
            minimum_cash_policy=self.minimum_cash_policy,
            vat_refund_amount=self.vat_refund_amount,
        )
        df_funded = funded.run_monthly_schedule(horizon_months=24)
        summary_funded = funded.get_runway_summary(df_funded)
        print("FUNDED SCENARIO (€70,768.18 equity injection):")
        print(f"  Year 1 Cash Trough:              {summary_funded.year1_trough_month} (Month {summary_funded.year1_trough_month_index})")
        print(f"  Cash Trough Balance:             €{summary_funded.year1_trough_cash_balance:>14,.2f}")
        print(f"  Max Revolving Credit Draw (Y1):  €{summary_funded.year1_max_credit_line_draw:>14,.2f} (limit €{self.financing.credit_line_limit:,.2f})")
        print(f"  Year 1 Closing Cash:             €{summary_funded.year1_ending_cash:>14,.2f}")
        print(f"  Year 2 Closing Cash:             €{summary_funded.year2_ending_cash:>14,.2f}")
        print(f"  Liquidity policy respected:      {summary_funded.liquidity_cushion_never_breached}")
        print("-" * 88)
        print("Note: this is a standalone liquidity stress, not a line-by-line")
        print("decomposition of the annual three-statement model. It uses seasonal")
        print("ADR and includes OTA commissions and amenities; the annual model uses")
        print("flat ADR and a simpler cost stack. The VAT refund repays the bridge.")
        print("-" * 88)

        cols_y1 = [
            "month_of_year",
            "month_name",
            "occupancy_pct",
            "gross_revenue",
            "contribution_margin",
            "net_operating_cash_flow",
            "credit_line_drawn",
            "ending_cash_balance",
        ]
        df_display_y1 = df_monthly[df_monthly["year"] == 1][cols_y1].copy()
        df_display_y1.columns = [
            "M#",
            "Month",
            "Occ %",
            "Revenue (€)",
            "Contrib (€)",
            "Net CF (€)",
            "Credit Line (€)",
            "End Cash (€)",
        ]
        print("Year 1 Monthly Trajectory:")
        print(df_display_y1.to_string(index=False))
        print("=" * 88)
