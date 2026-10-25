"""
Core Three-Statement Financial Model for La Dehesa del Castrillo S.L.

Integrates:
1. Income Statement (P&L): revenue, the full variable-cost stack (F&B COGS,
   OTA commissions, amenities, breakfast), payroll, fixed OPEX, EBITDA, FF&E
   reserve, D&A (PP&E depreciation + capitalised pre-opening amortisation),
   EBIT, interest, EBT, tax and net income.
2. Balance Sheet: PP&E, capitalised pre-opening costs, working capital, cash,
   DSRA + FF&E reserve (restricted cash), VAT receivable, senior debt, VAT
   bridge and equity, with a strict equality check.
3. Cash Flow: CFO (indirect), CFI (CapEx, IDC, pre-opening, DSRA, FF&E
   reserve, VAT refund) and CFF (senior debt, cash equity, VAT bridge, LEADER
   grant, amortisation). FCFF and FCFE for the returns analysis.

Two modelling conventions are made explicit:

* **Operating VAT is a pass-through.** Revenue is net of VAT; the output VAT
  collected from guests is remitted to AEAT net of the recoverable VAT paid on
  operating costs. The net cash effect is zero, so CFO is simply
  ``net income + D&A``. Only the CapEx input VAT is a financing item: it is
  funded by a dedicated bridge and repaid with the AEAT refund in Year 2.

* **The cash equity is a plug, not a 30% assumption.** In the management and
  market cases the engine solves for the cash equity that keeps the minimum
  cash balance positive over the projection, given 35% LTV senior debt, the
  in-kind land contribution, the VAT bridge and the close-day uses. The
  resulting equity requirement is reported, not assumed. The promoter case
  keeps the original 30% equity so that it reproduces the author's Excel.
"""

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple
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
from src.config.reform import ReformConfig
from src.config.ine_weights import SEGOVIA_INE_MONTHLY, get_annual_weighted_occupancy
from src.core.debt import DebtAmortizationEngine
from src.core.tax import VATEngine, CorporateTaxEngine

PREOPENING_AMORTIZATION_YEARS = 5


@dataclass
class AnnualStatementRecord:
    year: int

    # Income Statement
    revenue_rooms: float
    revenue_full_house: float
    revenue_restaurant: float
    total_revenue: float
    cogs_restaurant: float
    ota_commission: float
    amenities: float
    breakfast_cost: float
    total_variable_costs: float
    gross_margin: float
    labor_expense: float
    fixed_opex: float
    total_opex: float
    ebitda: float
    ffe_reserve: float
    cfads: float
    ppe_depreciation: float
    preopening_amortization: float
    depreciation: float
    ebit: float
    senior_interest: float
    bridge_interest: float
    interest_expense: float
    debt_service: float
    ebt: float
    corporate_tax: float
    net_income: float

    # Memo: operating VAT is a pass-through and does not affect cash.
    operating_vat_settlement: float

    # Cash Flow Statement
    cfo: float
    cfi: float
    cff: float
    net_cash_flow: float
    ending_cash: float
    fcff: float
    fcfe: float
    fcff_ex_capex: float
    fcfe_proper: float

    # Balance Sheet - Assets
    gross_ppe: float
    accumulated_depreciation: float
    net_ppe: float
    gross_intangibles: float
    accumulated_amortization: float
    net_intangibles: float
    working_capital_assets: float
    cash_and_equivalents: float
    restricted_cash: float
    vat_receivable: float
    deferred_tax_asset: float
    total_assets: float

    # Balance Sheet - Liabilities
    short_term_debt: float
    long_term_debt: float
    total_debt: float
    credit_line_drawn: float
    vat_bridge: float
    total_liabilities: float

    # Balance Sheet - Equity
    share_capital: float
    retained_earnings: float
    capital_subsidies: float
    total_equity: float

    balance_sheet_discrepancy: float

    # Reform overlay (zero in the three as-is cases). These are memo lines so
    # the reform tab can show what drives the incremental EBITDA without
    # polluting the original management/market/promoter statements.
    revenue_external_fnb: float = 0.0
    revenue_experiences: float = 0.0
    cogs_external_fnb: float = 0.0
    cogs_experiences: float = 0.0
    external_covers: float = 0.0
    incremental_payroll: float = 0.0
    cost_savings: float = 0.0


class FinancialModelEngine:
    """Integrated financial modelling engine over a multi-year horizon."""

    def __init__(
        self,
        capex: Optional[CapExStructure] = None,
        financing: Optional[FinancingStructure] = None,
        labor: Optional[LaborStructure] = None,
        opex: Optional[FixedOpexStructure] = None,
        revenue_cfg: Optional[RevenueModelConfig] = None,
        scenario: Optional[ScenarioDrivers] = None,
        case: str = "management",
        cash_equity_override: Optional[float] = None,
        reform: Optional[ReformConfig] = None,
    ):
        if reform is not None and case != "reform":
            raise ValueError("A ReformConfig requires case='reform'")
        self.case = case
        self.reform = reform if case == "reform" else None
        self.capex = capex or CapExStructure()
        self.financing = financing or FinancingStructure()
        self.labor = labor or LaborStructure()
        self.opex = opex or FixedOpexStructure()
        self.rev_cfg = revenue_cfg or RevenueModelConfig()
        self.scenario = scenario or SCENARIOS["base"]

        # Case-specific calibration.
        # - management: upside demand (31.36% mature occupancy) with the full
        #   realistic cost stack and the re-sized 35% LTV structure.
        # - market: official INE Segovia occupancy (21.24%) with the original
        #   unit economics and the same realistic cost stack and structure.
        # - promoter: the exact original university simulator (19.2%, 4.5%/25Y
        #   debt, no grant, original 729k cost basis) for the replication test.
        if case == "promoter":
            self.rev_cfg = replace(
                self.rev_cfg,
                calibration_mode="promoter",
                apply_full_cost_stack=False,
            )
            self.capex = CapExStructure.original_promoter()
            self.financing = replace(
                self.financing,
                base_capex=725_000.0,
                debt_share=0.70,
                equity_share=0.30,
                land_in_kind=False,
                loan_interest_rate=0.045,
                loan_tenure_years=25,
                construction_months=0,
                grace_months=0,
                leader_subsidy_amount=0.0,
                credit_line_limit=20_000.0,
                vat_bridge_limit=20_000.0,
                initial_credit_line_draw=20_000.0,
                pre_opening_costs=0.0,
                initial_working_capital=0.0,
                dsra_months=0,
            )
            self.opex = FixedOpexStructure(
                maintenance=3_600.0,
                insurance=1_200.0,
                utilities=3_659.0,
                marketing_seo=0.0,
                pms_software=0.0,
                admin_accounting=0.0,
                property_tax_waste=0.0,
                other=0.0,
                purchases=6_444.0,
            )
        elif case == "market":
            self.rev_cfg = replace(
                self.rev_cfg,
                calibration_mode="market",
                apply_full_cost_stack=True,
            )
            self.capex = CapExStructure()
            self.financing = replace(
                self.financing,
                base_capex=self.capex.total_capex,
            )
        elif case == "reform":
            self.reform = reform or ReformConfig()
            self.rev_cfg = replace(
                self.rev_cfg,
                calibration_mode="ine_market",
                apply_full_cost_stack=True,
            )
            self.capex = self.reform.build_capex()
            self.financing = replace(
                self.financing,
                base_capex=self.capex.total_capex,
                debt_share=self.reform.debt_share,
                loan_interest_rate=self.reform.loan_interest_rate,
                loan_tenure_years=self.reform.loan_tenure_years,
                construction_months=self.reform.construction_months,
                grace_months=self.reform.grace_months,
                leader_subsidy_amount=self.reform.leader_subsidy,
                leader_disbursement_year=self.reform.leader_disbursement_year,
                pre_opening_costs=self.reform.pre_opening_costs,
                initial_working_capital=self.reform.initial_working_capital,
                dsra_months=self.reform.dsra_months,
            )
            # The reform's ADR/price uplift is layered on top of the chosen
            # scenario multiplier, so a downside scenario can still cut prices.
            self.scenario = replace(
                self.scenario,
                adr_multiplier=self.scenario.adr_multiplier
                * (1.0 + self.reform.adr_uplift),
            )
        else:
            self.rev_cfg = replace(
                self.rev_cfg,
                calibration_mode="ine_market",
                apply_full_cost_stack=True,
            )
            self.capex = CapExStructure()
            self.financing = replace(
                self.financing,
                base_capex=self.capex.total_capex,
            )

        effective_interest_rate = max(
            0.01, self.financing.loan_interest_rate + self.scenario.interest_rate_delta
        )
        self.debt_engine = DebtAmortizationEngine(
            principal=self.financing.senior_debt_principal,
            annual_interest_rate=effective_interest_rate,
            tenure_years=self.financing.loan_tenure_years,
            grace_months=self.financing.grace_months,
        )
        self.vat_engine = VATEngine()
        self.tax_engine = CorporateTaxEngine()

        # Cash equity: fixed in the promoter case (original 30%); in the
        # management and market cases it is the funding plug that closes the
        # sources & uses at close, plus any operating-cash buffer needed to
        # keep the minimum cash balance over the projection.
        self.base_cash_equity = float(self.financing.sponsor_equity)
        self.cash_equity_buffer = 0.0
        self.cash_equity_plug = 0.0
        if cash_equity_override is not None and case != "promoter":
            # Used by the Monte Carlo / copula engines: reuse the deterministic
            # close-day equity instead of re-solving the funding plug (and the
            # five-year cash probe) on every draw.
            self.cash_equity = round(float(cash_equity_override), 2)
            self.cash_equity_buffer = round(
                max(0.0, self.cash_equity - self._close_day_equity()), 2
            )
            self.cash_equity_plug = round(
                max(0.0, self.cash_equity - self.base_cash_equity), 2
            )
        elif case == "promoter":
            self.cash_equity = self.base_cash_equity
        else:
            close_equity = max(self.base_cash_equity, self._close_day_equity())
            probe = self._project(5, cash_equity=close_equity)
            min_cash = float(probe["ending_cash"].min())
            buffer = max(
                0.0, round(float(self.financing.minimum_cash_balance) - min_cash, 2)
            )
            self.cash_equity_buffer = buffer
            self.cash_equity = round(close_equity + buffer, 2)
            self.cash_equity_plug = round(
                max(0.0, self.cash_equity - self.base_cash_equity), 2
            )

    # ------------------------------------------------------------------
    # Close-day uses
    # ------------------------------------------------------------------
    def _close_day_equity(self) -> float:
        """Cash equity needed for total sources to equal total uses at close."""
        cash_uses = (
            self.cash_capex
            + float(self.financing.idc_amount)
            + float(self.capex.total_input_vat)
            + float(self.financing.pre_opening_costs)
            + float(self.financing.initial_working_capital)
            + self.dsra_amount
        )
        sources_without_equity = (
            float(self.financing.senior_debt_principal)
            + float(self.capex.total_input_vat)
            + float(self.financing.initial_credit_line_draw)
        )
        return round(max(0.0, cash_uses - sources_without_equity), 2)

    @property
    def total_equity_at_close(self) -> float:
        """Total equity contributed at close: cash equity + in-kind land."""
        return round(self.cash_equity + self.financing.land_in_kind_value, 2)

    @property
    def total_project_investment(self) -> float:
        """
        All-in project investment for the unlevered return.

        CapEx (including the in-kind land at opportunity value) plus the
        close-day costs that create an asset or a required reserve: IDC,
        pre-opening costs, the opening working capital and the DSRA. The VAT
        bridge is excluded because it is a pure wash (drawn and refunded).
        """
        return round(
            self.capex.total_capex
            + float(self.financing.idc_amount)
            + float(self.financing.pre_opening_costs)
            + float(self.financing.initial_working_capital)
            + self.dsra_amount,
            2,
        )

    def debt_sizing(self) -> Dict[str, float]:
        """
        Tests the requested LTV facility against the DSCR constraint.

        The bank sizes the loan on the minimum pre-tax CFADS over the amortising
        years (EBITDA - FF&E reserve, before tax and before interest) at the
        target DSCR. The binding constraint is the lower of the LTV cap and the
        DSCR cap.
        """
        df = self.run_projection(5)
        pretax_cfads = (df["ebitda"] - df["ffe_reserve"]).iloc[1:]
        min_cfads = float(pretax_cfads.min()) if len(pretax_cfads) else 0.0
        max_debt_service = min_cfads / self.financing.target_dscr

        r = self.debt_engine.monthly_rate
        n = self.debt_engine.amortization_periods
        if r > 0:
            pmt = r * (1.0 + r) ** n / ((1.0 + r) ** n - 1.0)
        else:
            pmt = 1.0 / n
        principal_dscr = (
            max(0.0, max_debt_service / (pmt * 12.0)) if pmt > 0 else 0.0
        )
        principal_ltv = self.financing.base_capex * self.financing.debt_share
        if min_cfads <= 0:
            binding = "NONE (negative CFADS)"
        else:
            binding = "LTV" if principal_ltv <= principal_dscr else "DSCR"

        return {
            "min_pretax_cfads": round(min_cfads, 2),
            "max_annual_debt_service": round(max_debt_service, 2),
            "principal_ltv_cap": round(principal_ltv, 2),
            "principal_dscr_cap": round(principal_dscr, 2),
            "requested_principal": round(self.financing.senior_debt_principal, 2),
            "binding_constraint": binding,
            "implied_ltv_pct": round(
                min(principal_ltv, principal_dscr) / self.financing.base_capex * 100.0,
                2,
            ),
        }

    @property
    def annual_debt_service_max(self) -> float:
        """Maximum annual senior debt service over the projection (DSCR sizing)."""
        sched = self.debt_engine.get_annual_schedule_df()
        return float(sched["payment"].max())

    @property
    def dsra_amount(self) -> float:
        """Contractual DSRA: N months of the maximum annual debt service."""
        if self.financing.dsra_months <= 0:
            return 0.0
        return round(
            self.annual_debt_service_max * self.financing.dsra_months / 12.0, 2
        )

    @property
    def cash_capex(self) -> float:
        """CapEx paid in cash (the land is contributed in kind in mgmt/market)."""
        return round(
            self.capex.total_capex
            - (self.capex.land.amount if self.financing.land_in_kind else 0.0),
            2,
        )

    def sources_uses_at_close(self, cash_equity: Optional[float] = None) -> Dict[str, float]:
        """Sources & uses at close (used by the funding engine and the Excel)."""
        cash_equity = self.cash_equity if cash_equity is None else cash_equity
        uses = {
            "land_in_kind": round(self.financing.land_in_kind_value, 2),
            "cash_capex": self.cash_capex,
            "idc": float(self.financing.idc_amount),
            "input_vat": float(self.capex.total_input_vat),
            "pre_opening_costs": float(self.financing.pre_opening_costs),
            "initial_working_capital": float(self.financing.initial_working_capital),
            "dsra": self.dsra_amount,
            "operating_cash_buffer": round(self.cash_equity_buffer, 2),
        }
        sources = {
            "senior_debt": float(self.financing.senior_debt_principal),
            "vat_bridge": float(self.capex.total_input_vat),
            "credit_line": float(self.financing.initial_credit_line_draw),
            "land_in_kind": round(self.financing.land_in_kind_value, 2),
            "cash_equity": round(float(cash_equity), 2),
        }
        uses["total_uses"] = round(sum(uses.values()), 2)
        sources["total_sources"] = round(sum(sources.values()), 2)
        sources["cash_equity_surplus_deficit"] = round(
            sources["total_sources"] - uses["total_uses"], 2
        )
        return {"uses": uses, "sources": sources}

    # ------------------------------------------------------------------
    # Revenue and variable costs
    # ------------------------------------------------------------------
    def _apply_reform_overlay(
        self, rev: Dict[str, float], year: int
    ) -> Dict[str, float]:
        """
        Adds the external F&B and experience revenue lines to the management
        revenue base. In the three as-is cases the overlay is zero, so the
        original statements are unchanged.
        """
        if self.reform is None:
            rev.update(
                {
                    "rev_external_fnb": 0.0,
                    "rev_experiences": 0.0,
                    "cogs_external_fnb": 0.0,
                    "cogs_experiences": 0.0,
                    "external_covers": 0.0,
                }
            )
            return rev

        r = self.reform
        external_ramp = (
            r.external_ramp_year1 if year == 1
            else r.external_ramp_year2 if year == 2
            else 1.0
        )
        experience_ramp = (
            r.experiences_ramp_year1 if year == 1
            else r.experiences_ramp_year2 if year == 2
            else 1.0
        )

        external_covers = r.external_covers_per_day * 365.0 * external_ramp
        external_revenue = round(external_covers * r.external_ticket, 2)
        experience_revenue = round(r.experiences_revenue * experience_ramp, 2)

        rev["rev_external_fnb"] = external_revenue
        rev["rev_experiences"] = experience_revenue
        rev["cogs_external_fnb"] = round(
            external_revenue * r.external_cogs_ratio, 2
        )
        rev["cogs_experiences"] = round(
            experience_revenue * (1.0 - r.experiences_ebitda_margin), 2
        )
        rev["external_covers"] = round(external_covers, 2)
        rev["total_revenue"] = round(
            rev["total_revenue"] + external_revenue + experience_revenue, 2
        )
        return rev

    def calculate_revenue_for_year(self, year: int) -> Dict[str, float]:
        """Calculates annual revenue, key-nights, guests and the variable-cost stack."""
        occ_mult = self.scenario.occupancy_multiplier
        adr_mult = self.scenario.adr_multiplier

        if self.rev_cfg.calibration_mode in ("promoter", "market"):
            if self.rev_cfg.calibration_mode == "promoter":
                room_nights = float(self.rev_cfg.promoter_room_nights_y1)
                house_nights = float(self.rev_cfg.promoter_house_nights_y1)
                meals = float(self.rev_cfg.promoter_meals_y1)
                room_adr = self.rev_cfg.promoter_room_adr
                house_adr = self.rev_cfg.promoter_house_adr
                ticket = self.rev_cfg.promoter_restaurant_ticket
                g2 = self.rev_cfg.promoter_growth_y2
                g3 = self.rev_cfg.promoter_growth_y3
            else:
                room_nights = float(self.rev_cfg.market_room_nights_y1)
                house_nights = float(self.rev_cfg.market_house_nights_y1)
                meals = float(self.rev_cfg.market_meals_y1)
                room_adr = self.rev_cfg.market_room_adr
                house_adr = self.rev_cfg.market_house_adr
                ticket = self.rev_cfg.market_restaurant_ticket
                g2 = self.rev_cfg.market_growth_y2
                g3 = self.rev_cfg.market_growth_y3

            if year == 1:
                factor = 1.0
            elif year == 2:
                factor = g2
            elif year == 3:
                factor = g2 * g3
            else:
                factor = g2 * g3 * (1.05 ** (year - 3))

            room_nights *= factor * occ_mult
            house_nights *= factor * occ_mult
            meals *= factor * occ_mult
            rev_rooms = room_nights * room_adr * adr_mult
            rev_house = house_nights * house_adr * adr_mult
            rev_restaurant = meals * ticket * adr_mult

            cogs_restaurant = (
                0.0
                if not self.rev_cfg.apply_full_cost_stack
                else rev_restaurant * self.rev_cfg.restaurant_cogs_ratio
            )
            occupied_days = (room_nights + house_nights) / (
                self.rev_cfg.double_rooms_count + self.rev_cfg.full_house_count
            )
            guests = (
                room_nights * self.rev_cfg.guests_per_double_room
                + house_nights * self.rev_cfg.guests_per_full_house
            )
            return self._apply_reform_overlay(
                {
                    "rev_rooms": round(rev_rooms, 2),
                    "rev_house": round(rev_house, 2),
                    "rev_restaurant": round(rev_restaurant, 2),
                    "total_revenue": round(rev_rooms + rev_house + rev_restaurant, 2),
                    "cogs_restaurant": round(cogs_restaurant, 2),
                    "occupied_days": occupied_days,
                    "room_nights": room_nights,
                    "house_nights": house_nights,
                    "guests": guests,
                },
                year,
            )

        if self.rev_cfg.calibration_mode == "leader_excel":
            excel_rev_base = {1: 96_628.0, 2: 126_855.0, 3: 159_863.0, 4: 167_856.0, 5: 176_249.0}
            base_rev = excel_rev_base.get(year, 159_863.0 * (1.05 ** (year - 3)))
            tot_rev = round(base_rev * occ_mult * adr_mult, 2)
            rev_rooms = round(tot_rev * 0.40, 2)
            rev_house = round(tot_rev * 0.25, 2)
            rev_restaurant = round(tot_rev - rev_rooms - rev_house, 2)
            cogs_restaurant = round(rev_restaurant * self.rev_cfg.restaurant_cogs_ratio, 2)
            occupied_days = tot_rev / 1_500.0
            guests = occupied_days * 21.0
            return self._apply_reform_overlay(
                {
                    "rev_rooms": rev_rooms,
                    "rev_house": rev_house,
                    "rev_restaurant": rev_restaurant,
                    "total_revenue": tot_rev,
                    "cogs_restaurant": cogs_restaurant,
                    "occupied_days": occupied_days,
                    "room_nights": occupied_days * 7,
                    "house_nights": occupied_days,
                    "guests": guests,
                },
                year,
            )

        # Management case: INE monthly seasonality with the management target
        # occupancy (31.36% at stabilisation) and an explicit two-year ramp-up.
        # No nominal ADR growth is assumed after stabilisation (conservative).
        ramp_up = 0.90 if year == 1 else 1.00
        effective_occ_mult = occ_mult * ramp_up
        base_occ = get_annual_weighted_occupancy(SEGOVIA_INE_MONTHLY) * effective_occ_mult
        occupied_days = base_occ * 365

        room_nights = occupied_days * self.rev_cfg.double_rooms_count
        house_nights = occupied_days * self.rev_cfg.full_house_count
        guests = (
            room_nights * self.rev_cfg.guests_per_double_room
            + house_nights * self.rev_cfg.guests_per_full_house
        )

        rev_rooms = room_nights * self.rev_cfg.double_room_adr * adr_mult
        rev_house = house_nights * self.rev_cfg.full_house_adr * adr_mult
        rev_restaurant = guests * self.rev_cfg.restaurant_average_ticket * adr_mult
        cogs_restaurant = rev_restaurant * self.rev_cfg.restaurant_cogs_ratio

        return self._apply_reform_overlay(
            {
                "rev_rooms": round(rev_rooms, 2),
                "rev_house": round(rev_house, 2),
                "rev_restaurant": round(rev_restaurant, 2),
                "total_revenue": round(rev_rooms + rev_house + rev_restaurant, 2),
                "cogs_restaurant": round(cogs_restaurant, 2),
                "occupied_days": occupied_days,
                "room_nights": room_nights,
                "house_nights": house_nights,
                "guests": guests,
            },
            year,
        )

    def _variable_costs(self, rev: Dict[str, float]) -> Dict[str, float]:
        """Full USALI-style variable-cost stack."""
        if not self.rev_cfg.apply_full_cost_stack:
            return {
                "ota_commission": 0.0,
                "amenities": 0.0,
                "breakfast_cost": 0.0,
                "total_variable_costs": float(rev["cogs_restaurant"]),
            }

        lodging_revenue = rev["rev_rooms"] + rev["rev_house"]
        ota_commission = (
            lodging_revenue
            * self.rev_cfg.ota_share
            * self.rev_cfg.ota_commission_rate
        )
        amenities = rev["occupied_days"] * self.rev_cfg.amenities_per_occupied_day
        breakfast = rev["guests"] * self.rev_cfg.breakfast_cost_per_guest_day
        total_variable = (
            rev["cogs_restaurant"]
            + float(rev.get("cogs_external_fnb", 0.0))
            + float(rev.get("cogs_experiences", 0.0))
            + ota_commission
            + amenities
            + breakfast
        )
        return {
            "ota_commission": round(ota_commission, 2),
            "amenities": round(amenities, 2),
            "breakfast_cost": round(breakfast, 2),
            "total_variable_costs": round(total_variable, 2),
        }

    # ------------------------------------------------------------------
    # Equity plug
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Full projection
    # ------------------------------------------------------------------
    def run_projection(self, projection_years: int = 5) -> pd.DataFrame:
        """Executes the full projection across the specified horizon."""
        return self._project(projection_years, cash_equity=self.cash_equity)

    def _project(self, projection_years: int, cash_equity: float) -> pd.DataFrame:
        debt_schedule = self.debt_engine.get_annual_schedule_df()

        records: List[AnnualStatementRecord] = []

        idc = float(self.financing.idc_amount)
        pre_opening = float(self.financing.pre_opening_costs)
        initial_wc = float(self.financing.initial_working_capital)
        dsra = self.dsra_amount
        input_vat_capex = float(self.capex.total_input_vat)
        cash_capex = self.cash_capex
        land_in_kind = round(self.financing.land_in_kind_value, 2)

        gross_ppe = round(self.capex.total_capex + idc, 2)
        gross_intangibles = pre_opening
        accum_depr = 0.0
        accum_amort = 0.0
        ending_cash = initial_wc
        restricted_cash = round(dsra, 2)
        retained_earnings = 0.0
        capital_subsidies = 0.0
        vat_receivable = 0.0
        vat_bridge = 0.0
        credit_line_balance = float(self.financing.initial_credit_line_draw)

        # Reset the tax engine for deterministic re-runs.
        self.tax_engine = CorporateTaxEngine()

        for y in range(1, projection_years + 1):
            rev = self.calculate_revenue_for_year(y)
            variable = self._variable_costs(rev)
            total_variable = float(variable["total_variable_costs"])
            gross_margin = round(rev["total_revenue"] - total_variable, 2)

            incremental_payroll = (
                round(
                    self.reform.incremental_fte
                    * self.reform.loaded_cost_per_fte,
                    2,
                )
                if self.reform is not None
                else 0.0
            )
            reform_cost_savings = (
                float(self.reform.cost_savings)
                if self.reform is not None
                else 0.0
            )
            labor_cost = round(
                (self.labor.total_annual_payroll + incremental_payroll)
                * self.scenario.opex_multiplier,
                2,
            )
            fixed_opex_cost = round(
                max(
                    0.0,
                    self.opex.total_fixed_opex - reform_cost_savings,
                )
                * self.scenario.opex_multiplier,
                2,
            )
            total_opex = round(labor_cost + fixed_opex_cost, 2)

            ebitda = round(gross_margin - total_opex, 2)
            ffe_reserve = round(
                rev["total_revenue"] * self.rev_cfg.ffe_reserve_rate
                if self.rev_cfg.apply_full_cost_stack else 0.0,
                2,
            )

            ppe_depreciation = round(self.capex.annual_depreciation, 2)
            preopening_amort = (
                round(pre_opening / PREOPENING_AMORTIZATION_YEARS, 2)
                if pre_opening > 0 else 0.0
            )
            depreciation = round(ppe_depreciation + preopening_amort, 2)
            ebit = round(ebitda - depreciation, 2)

            debt_row = debt_schedule[debt_schedule["year"] == y].iloc[0]
            senior_interest = float(debt_row["interest"])
            principal_repayment = float(debt_row["principal"])
            ending_debt_balance = float(debt_row["ending_balance"])
            st_debt = float(debt_row["short_term_debt"])
            lt_debt = float(debt_row["long_term_debt"])
            debt_service = round(senior_interest + principal_repayment, 2)

            # VAT bridge interest: drawn at close, repaid in Month 18 (mid-Year 2).
            if y == 1:
                bridge_interest = round(
                    input_vat_capex * self.financing.credit_line_interest, 2
                )
            elif y == 2:
                bridge_interest = round(
                    input_vat_capex * self.financing.credit_line_interest * 0.5, 2
                )
            else:
                bridge_interest = 0.0
            total_interest = round(senior_interest + bridge_interest, 2)

            ebt = round(ebit - total_interest, 2)
            tax_res = self.tax_engine.calculate_tax(y, ebt)
            corporate_tax = tax_res["tax_expense"]
            deferred_tax_asset = tax_res["deferred_tax_asset"]
            net_income = round(ebt - corporate_tax, 2)

            # Operating VAT: a pass-through. We compute it for disclosure only.
            vat_settle = self.vat_engine.calculate_annual_vat_settlement(
                year=y,
                revenue_lodging=rev["rev_rooms"] + rev["rev_house"],
                revenue_restaurant=rev["rev_restaurant"]
                + float(rev.get("rev_external_fnb", 0.0)),
                capex_expenditure=0.0,
                taxable_opex=fixed_opex_cost + total_variable,
                request_annual_refund=False,
            )
            operating_vat = float(vat_settle["vat_payable"])

            # Cash Flow from Operations (VAT is collected and remitted in-year).
            cfo = round(net_income + depreciation, 2)

            # Cash Flow from Investing.
            if y == 1:
                cfi = round(
                    -(cash_capex + idc + input_vat_capex + pre_opening
                      + initial_wc + dsra + ffe_reserve),
                    2,
                )
            elif y == 2:
                cfi = round(input_vat_capex - ffe_reserve, 2)
            else:
                cfi = round(-ffe_reserve, 2)

            # Cash Flow from Financing.
            leader_inflow = 0.0
            if y == 1:
                vat_bridge = input_vat_capex
                cff = round(
                    self.financing.senior_debt_principal
                    + float(cash_equity)
                    + vat_bridge
                    + credit_line_balance
                    - principal_repayment,
                    2,
                )
            else:
                if (
                    self.financing.leader_subsidy_amount > 0
                    and y == self.financing.leader_disbursement_year
                ):
                    leader_inflow = self.financing.leader_subsidy_amount
                    capital_subsidies += leader_inflow
                repay_bridge = vat_bridge if y == 2 else 0.0
                if y == 2:
                    vat_bridge = 0.0
                cff = round(
                    leader_inflow - repay_bridge - principal_repayment, 2
                )

            net_cash_flow = round(cfo + cfi + cff, 2)
            ending_cash = round(ending_cash + net_cash_flow, 2)
            restricted_cash = round(restricted_cash + ffe_reserve, 2)

            # FCFF / FCFE. CapEx and equity sit at t=0, so the operating series
            # excludes the Year-1 CapEx outflows.
            effective_tax_rate = self.tax_engine.cit_rate
            fcff = round(
                ebit * (1.0 - effective_tax_rate)
                + depreciation
                - ffe_reserve
                + leader_inflow,
                2,
            )
            fcfe = round(
                fcff - total_interest * (1.0 - effective_tax_rate) - principal_repayment, 2
            )
            fcff_ex_capex = fcff
            fcfe_proper = round(
                net_income
                + depreciation
                - ffe_reserve
                - principal_repayment
                + leader_inflow,
                2,
            )

            # Balance Sheet.
            accum_depr = round(accum_depr + ppe_depreciation, 2)
            accum_amort = round(accum_amort + preopening_amort, 2)
            net_ppe = round(gross_ppe - accum_depr, 2)
            net_intangibles = round(gross_intangibles - accum_amort, 2)
            vat_receivable = input_vat_capex if y == 1 else 0.0

            total_assets = round(
                net_ppe
                + net_intangibles
                + ending_cash
                + restricted_cash
                + vat_receivable,
                2,
            )

            total_debt = ending_debt_balance
            total_liabilities = round(
                total_debt + vat_bridge + credit_line_balance, 2
            )

            retained_earnings = round(retained_earnings + net_income, 2)
            share_capital = round(land_in_kind + float(cash_equity), 2)
            total_equity = round(
                share_capital + retained_earnings + capital_subsidies, 2
            )

            bs_discrepancy = round(
                total_assets - (total_liabilities + total_equity), 2
            )

            cfads = round(ebitda - ffe_reserve - corporate_tax, 2)

            record = AnnualStatementRecord(
                year=y,
                revenue_rooms=rev["rev_rooms"],
                revenue_full_house=rev["rev_house"],
                revenue_restaurant=rev["rev_restaurant"],
                total_revenue=rev["total_revenue"],
                cogs_restaurant=rev["cogs_restaurant"],
                ota_commission=variable["ota_commission"],
                amenities=variable["amenities"],
                breakfast_cost=variable["breakfast_cost"],
                total_variable_costs=total_variable,
                gross_margin=gross_margin,
                labor_expense=labor_cost,
                fixed_opex=fixed_opex_cost,
                total_opex=total_opex,
                ebitda=ebitda,
                ffe_reserve=ffe_reserve,
                cfads=cfads,
                ppe_depreciation=ppe_depreciation,
                preopening_amortization=preopening_amort,
                depreciation=depreciation,
                ebit=ebit,
                senior_interest=senior_interest,
                bridge_interest=bridge_interest,
                interest_expense=total_interest,
                debt_service=debt_service,
                ebt=ebt,
                corporate_tax=corporate_tax,
                net_income=net_income,
                operating_vat_settlement=round(operating_vat, 2),
                cfo=cfo,
                cfi=cfi,
                cff=cff,
                net_cash_flow=net_cash_flow,
                ending_cash=ending_cash,
                fcff=fcff,
                fcfe=fcfe,
                fcff_ex_capex=fcff_ex_capex,
                fcfe_proper=fcfe_proper,
                gross_ppe=gross_ppe,
                accumulated_depreciation=accum_depr,
                net_ppe=net_ppe,
                gross_intangibles=gross_intangibles,
                accumulated_amortization=accum_amort,
                net_intangibles=net_intangibles,
                working_capital_assets=0.0,
                cash_and_equivalents=ending_cash,
                restricted_cash=restricted_cash,
                vat_receivable=vat_receivable,
                deferred_tax_asset=deferred_tax_asset,
                total_assets=total_assets,
                short_term_debt=st_debt,
                long_term_debt=lt_debt,
                total_debt=total_debt,
                credit_line_drawn=round(vat_bridge + credit_line_balance, 2),
                vat_bridge=round(vat_bridge, 2),
                total_liabilities=total_liabilities,
                share_capital=share_capital,
                retained_earnings=retained_earnings,
                capital_subsidies=capital_subsidies,
                total_equity=total_equity,
                balance_sheet_discrepancy=bs_discrepancy,
                revenue_external_fnb=float(rev.get("rev_external_fnb", 0.0)),
                revenue_experiences=float(rev.get("rev_experiences", 0.0)),
                cogs_external_fnb=float(rev.get("cogs_external_fnb", 0.0)),
                cogs_experiences=float(rev.get("cogs_experiences", 0.0)),
                external_covers=float(rev.get("external_covers", 0.0)),
                incremental_payroll=incremental_payroll,
                cost_savings=reform_cost_savings,
            )
            records.append(record)

        df = pd.DataFrame([r.__dict__ for r in records])
        return df
