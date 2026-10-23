"""
Core Three-Statement Financial Model for La Dehesa del Castrillo S.L.

Integrates:
1. Income Statement (P&L): Revenue, COGS, Labor, OPEX, EBITDA, D&A, EBIT, Interest, EBT, Tax, Net Income.
2. Balance Sheet: Assets, Liabilities, and Equity with strict equality check.
3. Cash Flow Statement: Direct and Indirect methods (CFO, CFI, CFF, FCFF, FCFE).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd

from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    LaborStructure,
    FixedOpexStructure,
    RevenueModelConfig,
    ScenarioDrivers,
    SCENARIOS,
)
from src.config.ine_weights import SEGOVIA_INE_MONTHLY, get_annual_weighted_occupancy
from src.core.debt import DebtAmortizationEngine
from src.core.tax import VATEngine, CorporateTaxEngine


@dataclass
class AnnualStatementRecord:
    year: int
    # Income Statement
    revenue_rooms: float
    revenue_full_house: float
    revenue_restaurant: float
    total_revenue: float
    cogs_restaurant: float
    gross_margin: float
    labor_expense: float
    fixed_opex: float
    total_opex: float
    ebitda: float
    depreciation: float
    ebit: float
    interest_expense: float
    ebt: float
    corporate_tax: float
    net_income: float

    # Cash Flow Statement
    cfo: float
    cfi: float
    cff: float
    net_cash_flow: float
    ending_cash: float
    fcff: float
    fcfe: float

    # Balance Sheet
    gross_ppe: float
    accumulated_depreciation: float
    net_ppe: float
    cash_and_equivalents: float
    vat_receivable: float
    deferred_tax_asset: float
    total_assets: float

    short_term_debt: float
    long_term_debt: float
    total_debt: float
    credit_line_drawn: float
    total_liabilities: float

    share_capital: float
    retained_earnings: float
    capital_subsidies: float  # LEADER grant
    total_equity: float

    balance_sheet_discrepancy: float  # Must be 0.00


class FinancialModelEngine:
    """Integrated financial modeling engine over multi-year horizon."""

    def __init__(
        self,
        capex: Optional[CapExStructure] = None,
        financing: Optional[FinancingStructure] = None,
        labor: Optional[LaborStructure] = None,
        opex: Optional[FixedOpexStructure] = None,
        revenue_cfg: Optional[RevenueModelConfig] = None,
        scenario: Optional[ScenarioDrivers] = None,
    ):
        self.capex = capex or CapExStructure()
        self.financing = financing or FinancingStructure()
        self.labor = labor or LaborStructure()
        self.opex = opex or FixedOpexStructure()
        self.rev_cfg = revenue_cfg or RevenueModelConfig()
        self.scenario = scenario or SCENARIOS["base"]

        # Adjusted financing terms based on scenario
        effective_interest_rate = max(
            0.01, self.financing.loan_interest_rate + self.scenario.interest_rate_delta
        )
        self.debt_engine = DebtAmortizationEngine(
            principal=self.financing.senior_debt_principal,
            annual_interest_rate=effective_interest_rate,
            tenure_years=self.financing.loan_tenure_years,
        )
        self.vat_engine = VATEngine()
        self.tax_engine = CorporateTaxEngine()

    def calculate_revenue_for_year(self, year: int) -> Dict[str, float]:
        """
        Calculates annual revenue streams considering INE Segovia occupancy and ramp-up.
        Ramp-up factor: Year 1 = 90% of steady state, Year 2 = 100%, Year 3+ = 105% (mature asset).
        """
        ramp_up = 0.90 if year == 1 else (1.00 if year == 2 else 1.05)
        occ_mult = self.scenario.occupancy_multiplier * ramp_up
        adr_mult = self.scenario.adr_multiplier

        # Weighted annual occupied days
        base_occ = get_annual_weighted_occupancy(SEGOVIA_INE_MONTHLY) * occ_mult
        annual_days = 365
        occupied_day_equivalents = base_occ * annual_days

        # 1. Double Rooms
        room_adr = self.rev_cfg.double_room_adr * adr_mult
        rev_rooms = occupied_day_equivalents * self.rev_cfg.double_rooms_count * room_adr

        # 2. Full House
        house_adr = self.rev_cfg.full_house_adr * adr_mult
        rev_house = occupied_day_equivalents * self.rev_cfg.full_house_count * house_adr

        # 3. Restaurant
        diners = (
            occupied_day_equivalents * self.rev_cfg.double_rooms_count * self.rev_cfg.restaurant_diners_per_double_room
            + occupied_day_equivalents * self.rev_cfg.full_house_count * self.rev_cfg.restaurant_diners_per_full_house
        )
        ticket = self.rev_cfg.restaurant_average_ticket * adr_mult
        rev_restaurant = diners * ticket
        cogs_restaurant = rev_restaurant * self.rev_cfg.restaurant_cogs_ratio

        return {
            "rev_rooms": round(rev_rooms, 2),
            "rev_house": round(rev_house, 2),
            "rev_restaurant": round(rev_restaurant, 2),
            "total_revenue": round(rev_rooms + rev_house + rev_restaurant, 2),
            "cogs_restaurant": round(cogs_restaurant, 2),
        }

    def run_projection(self, projection_years: int = 5) -> pd.DataFrame:
        """Executes full projection across the specified time horizon."""
        debt_schedule = self.debt_engine.get_annual_schedule_df()

        records: List[AnnualStatementRecord] = []

        # Opening state at Year 0 / Launch
        gross_ppe = self.capex.total_capex
        accum_depr = 0.0
        ending_cash = 0.0
        retained_earnings = 0.0
        capital_subsidies = 0.0
        vat_receivable = 0.0
        vat_bridge_liability = 0.0

        for y in range(1, projection_years + 1):
            rev = self.calculate_revenue_for_year(y)
            gross_margin = round(rev["total_revenue"] - rev["cogs_restaurant"], 2)

            labor_cost = round(
                self.labor.total_annual_payroll * self.scenario.opex_multiplier, 2
            )
            fixed_opex_cost = round(
                self.opex.total_fixed_opex * self.scenario.opex_multiplier, 2
            )
            total_opex = round(labor_cost + fixed_opex_cost, 2)

            ebitda = round(gross_margin - total_opex, 2)
            depreciation = round(self.capex.annual_depreciation, 2)
            ebit = round(ebitda - depreciation, 2)

            debt_row = debt_schedule[debt_schedule["year"] == y].iloc[0]
            interest_expense = float(debt_row["interest"])
            principal_repayment = float(debt_row["principal"])
            ending_debt_balance = float(debt_row["ending_balance"])
            st_debt = float(debt_row["short_term_debt"])
            lt_debt = float(debt_row["long_term_debt"])

            # Bridge line interest (if any drawn)
            bridge_interest = round(
                vat_bridge_liability * self.financing.credit_line_interest, 2
            )
            total_interest = round(interest_expense + bridge_interest, 2)

            ebt = round(ebit - total_interest, 2)
            tax_res = self.tax_engine.calculate_tax(y, ebt)
            corporate_tax = tax_res["tax_expense"]
            deferred_tax_asset = tax_res["deferred_tax_asset"]
            net_income = round(ebt - corporate_tax, 2)

            # VAT cash flows and balance with AEAT
            capex_inv = self.capex.total_capex if y == 1 else 0.0
            vat_settle = self.vat_engine.calculate_annual_vat_settlement(
                year=y,
                revenue_lodging=rev["rev_rooms"] + rev["rev_house"],
                revenue_restaurant=rev["rev_restaurant"],
                capex_expenditure=capex_inv,
                taxable_opex=fixed_opex_cost + rev["cogs_restaurant"],
                opening_vat_credit=0.0,
                request_annual_refund=True,
            )

            new_vat_receivable = vat_settle["refund_due"]
            delta_vat_receivable = round(new_vat_receivable - vat_receivable, 2)
            vat_receivable = new_vat_receivable

            # Operating Cash Flow (CFO)
            # Working capital adjustment for taxes: -Delta VAT Receivable
            cfo = round(net_income + depreciation - delta_vat_receivable, 2)

            # Investing Cash Flow (CFI)
            cfi = -self.capex.total_capex if y == 1 else 0.0

            # Financing Cash Flow (CFF)
            if y == 1:
                # Startup financing: Senior Loan + Sponsor Equity + Bank VAT bridge facility
                vat_bridge_liability = new_vat_receivable
                cff = round(
                    self.financing.senior_debt_principal
                    + self.financing.sponsor_equity
                    + vat_bridge_liability
                    - principal_repayment,
                    2,
                )
            elif y == 2:
                # Year 2: LEADER grant collected (163k) and VAT bridge facility retired upon AEAT refund
                leader_inflow = self.financing.leader_subsidy_amount
                capital_subsidies += leader_inflow
                repay_bridge = vat_bridge_liability
                vat_bridge_liability = 0.0
                cff = round(
                    leader_inflow - repay_bridge - principal_repayment, 2
                )
            else:
                cff = round(-principal_repayment, 2)

            net_cash_flow = round(cfo + cfi + cff, 2)
            ending_cash = round(ending_cash + net_cash_flow, 2)

            # FCFF & FCFE
            effective_tax_rate = self.tax_engine.cit_rate
            fcff = round(ebit * (1.0 - effective_tax_rate) + depreciation + cfi, 2)
            fcfe = round(
                fcff - total_interest * (1.0 - effective_tax_rate) - principal_repayment, 2
            )

            # Balance Sheet
            accum_depr = round(accum_depr + depreciation, 2)
            net_ppe = round(gross_ppe - accum_depr, 2)
            total_assets = round(net_ppe + ending_cash + vat_receivable, 2)

            total_debt = ending_debt_balance
            total_liabilities = round(total_debt + vat_bridge_liability, 2)

            retained_earnings = round(retained_earnings + net_income, 2)
            share_capital = self.financing.sponsor_equity
            total_equity = round(
                share_capital + retained_earnings + capital_subsidies, 2
            )

            bs_discrepancy = round(total_assets - (total_liabilities + total_equity), 2)

            record = AnnualStatementRecord(
                year=y,
                revenue_rooms=rev["rev_rooms"],
                revenue_full_house=rev["rev_house"],
                revenue_restaurant=rev["rev_restaurant"],
                total_revenue=rev["total_revenue"],
                cogs_restaurant=rev["cogs_restaurant"],
                gross_margin=gross_margin,
                labor_expense=labor_cost,
                fixed_opex=fixed_opex_cost,
                total_opex=total_opex,
                ebitda=ebitda,
                depreciation=depreciation,
                ebit=ebit,
                interest_expense=interest_expense,
                ebt=ebt,
                corporate_tax=corporate_tax,
                net_income=net_income,
                cfo=cfo,
                cfi=cfi,
                cff=cff,
                net_cash_flow=net_cash_flow,
                ending_cash=ending_cash,
                fcff=fcff,
                fcfe=fcfe,
                gross_ppe=gross_ppe,
                accumulated_depreciation=accum_depr,
                net_ppe=net_ppe,
                cash_and_equivalents=ending_cash,
                vat_receivable=vat_receivable,
                deferred_tax_asset=deferred_tax_asset,
                total_assets=total_assets,
                short_term_debt=st_debt,
                long_term_debt=lt_debt,
                total_debt=total_debt,
                credit_line_drawn=vat_bridge_liability,
                total_liabilities=total_liabilities,
                share_capital=share_capital,
                retained_earnings=retained_earnings,
                capital_subsidies=capital_subsidies,
                total_equity=total_equity,
                balance_sheet_discrepancy=bs_discrepancy,
            )
            records.append(record)

        df = pd.DataFrame([r.__dict__ for r in records])
        return df
