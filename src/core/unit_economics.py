"""
Unit Economics and Contribution Margin Engine for La Dehesa del Castrillo S.L.

Formalizes:
1. RevPAR (Revenue Per Available Room) and TRevPAR (Total Revenue Per Available Room).
2. Granular unit economics per occupied day and per room-night.
3. The full variable-cost stack: F&B COGS, OTA commissions, guest amenities,
   breakfast and the 3% FF&E reserve that ranks ahead of debt service.
4. Unit contribution margin and the operating / debt-service / covenant
   break-even occupancy implied by that margin.

The per-day contribution margin is the bridge between the P&L and the exact
break-even computed by `BreakEvenEngine`; both use the same cost stack, so the
static day-count break-even and the full-engine bisection agree to within
rounding. The operating break-even is defined on EBITDA (before the FF&E
reserve); the debt-service and covenant break-evens use CFADS (after FF&E), as
the DSCR test does.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import pandas as pd

from src.config.assumptions import (
    FinancingStructure,
    FixedOpexStructure,
    LaborStructure,
    RevenueModelConfig,
)
from src.config.ine_weights import SEGOVIA_INE_MONTHLY, get_annual_weighted_occupancy
from src.core.debt import DebtAmortizationEngine


@dataclass(frozen=True)
class UnitEconomicsMetrics:
    # Inventory
    total_keys: int                  # 7 rooms + 1 country house = 8 keys
    annual_available_keys: int       # 8 * 365 = 2,920 key-nights
    double_rooms_available: int      # 7 * 365 = 2,555 room-nights
    country_house_available: int     # 1 * 365 = 365 house-nights

    # Full-capacity run-rate (100% occupied day)
    daily_lodging_revenue: float     # EUR 975.00 (EUR 595 rooms + EUR 380 house)
    daily_restaurant_revenue: float  # EUR 525.00 (21 diners @ EUR 25)
    daily_gross_revenue: float       # EUR 1,500.00

    # Variable costs per occupied day
    daily_cogs_restaurant: float     # 30% of EUR 525 = EUR 157.50
    daily_ota_commission: float      # 60% OTA share * 15% on lodging (EUR 975) = EUR 87.75
    daily_amenities_cleaning: float  # EUR 35 per occupied day
    daily_breakfast: float           # 21 guests * EUR 5 = EUR 105.00
    daily_total_variable_cost: float # EUR 385.25
    daily_variable_cost_ratio: float # 25.68%

    # FF&E reserve (3% of revenue, deducted before debt service)
    daily_ffe_reserve: float         # EUR 45.00
    daily_cash_margin: float         # EUR 1,069.75 (gross - variable - FF&E)

    # Unit contribution margin
    unit_contribution_margin_eur: float  # EUR 1,069.75 per occupied day
    unit_contribution_margin_pct: float  # 71.32%

    # Per-room key equivalent (boutique room + 2 diners)
    room_rev_per_occupied_night: float
    room_var_cost_per_occupied_night: float
    room_contribution_margin_eur: float
    room_contribution_margin_pct: float

    # Fixed burden and operating leverage
    annual_fixed_labor: float
    annual_fixed_opex: float
    annual_fixed_overhead: float
    annual_senior_debt_service: float
    annual_total_fixed_burden: float

    # Break-even occupied days and occupancy
    operating_breakeven_days: float
    cash_debt_breakeven_days: float
    covenant_125_breakeven_days: float


class UnitEconomicsEngine:
    """Computes RevPAR, TRevPAR, and granular contribution margins."""

    def __init__(
        self,
        rev_cfg: RevenueModelConfig = RevenueModelConfig(),
        labor_cfg: LaborStructure = LaborStructure(),
        opex_cfg: FixedOpexStructure = FixedOpexStructure(),
        financing_cfg: FinancingStructure = FinancingStructure(),
    ):
        self.rev_cfg = rev_cfg
        self.labor_cfg = labor_cfg
        self.opex_cfg = opex_cfg
        self.financing_cfg = financing_cfg

    def compute_unit_metrics(self) -> UnitEconomicsMetrics:
        """Calculates the unit economics at the 100%-occupancy baseline."""
        rooms_rev = self.rev_cfg.double_rooms_count * self.rev_cfg.double_room_adr
        house_rev = self.rev_cfg.full_house_count * self.rev_cfg.full_house_adr
        daily_lodging = rooms_rev + house_rev

        diners = (
            self.rev_cfg.double_rooms_count * self.rev_cfg.restaurant_diners_per_double_room
            + self.rev_cfg.full_house_count * self.rev_cfg.restaurant_diners_per_full_house
        )
        daily_dining = diners * self.rev_cfg.restaurant_average_ticket
        daily_gross = daily_lodging + daily_dining

        # Variable cost stack
        cogs_fnb = daily_dining * self.rev_cfg.restaurant_cogs_ratio
        ota_comm = (
            daily_lodging * self.rev_cfg.ota_share * self.rev_cfg.ota_commission_rate
        )
        amenities = self.rev_cfg.amenities_per_occupied_day
        breakfast = diners * self.rev_cfg.breakfast_cost_per_guest_day
        tot_var = cogs_fnb + ota_comm + amenities + breakfast
        var_ratio = tot_var / daily_gross

        ffe = daily_gross * self.rev_cfg.ffe_reserve_rate
        cash_margin = daily_gross - tot_var - ffe

        # Per room-night equivalent (1 double room + 2 restaurant covers)
        room_gross = self.rev_cfg.double_room_adr + (
            2 * self.rev_cfg.restaurant_average_ticket
        )
        room_var = (
            (2 * self.rev_cfg.restaurant_average_ticket * self.rev_cfg.restaurant_cogs_ratio)
            + (self.rev_cfg.double_room_adr * self.rev_cfg.ota_share * self.rev_cfg.ota_commission_rate)
            + (self.rev_cfg.amenities_per_occupied_day / (self.rev_cfg.double_rooms_count + self.rev_cfg.full_house_count))
            + (2 * self.rev_cfg.breakfast_cost_per_guest_day)
            + (room_gross * self.rev_cfg.ffe_reserve_rate)
        )
        room_cm_eur = room_gross - room_var

        # Fixed overhead
        fixed_labor = self.labor_cfg.total_annual_payroll
        fixed_opex = self.opex_cfg.total_fixed_opex
        fixed_overhead = fixed_labor + fixed_opex

        # Senior debt service: 20 years at 4.0% with a 12-month grace period.
        debt = DebtAmortizationEngine(
            principal=self.financing_cfg.senior_debt_principal,
            annual_interest_rate=self.financing_cfg.loan_interest_rate,
            tenure_years=self.financing_cfg.loan_tenure_years,
            grace_months=self.financing_cfg.grace_months,
        )
        annual_debt_service = float(debt.get_annual_schedule_df()["payment"].max())

        total_fixed_burden = fixed_overhead + annual_debt_service

        op_be_days = fixed_overhead / (daily_gross - tot_var)
        cash_be_days = total_fixed_burden / cash_margin
        cov_125_burden = fixed_overhead + (
            annual_debt_service * self.financing_cfg.target_dscr
        )
        cov_be_days = cov_125_burden / cash_margin

        total_keys = self.rev_cfg.double_rooms_count + self.rev_cfg.full_house_count

        return UnitEconomicsMetrics(
            total_keys=total_keys,
            annual_available_keys=total_keys * 365,
            double_rooms_available=self.rev_cfg.double_rooms_count * 365,
            country_house_available=self.rev_cfg.full_house_count * 365,
            daily_lodging_revenue=round(daily_lodging, 2),
            daily_restaurant_revenue=round(daily_dining, 2),
            daily_gross_revenue=round(daily_gross, 2),
            daily_cogs_restaurant=round(cogs_fnb, 2),
            daily_ota_commission=round(ota_comm, 2),
            daily_amenities_cleaning=round(amenities, 2),
            daily_breakfast=round(breakfast, 2),
            daily_total_variable_cost=round(tot_var, 2),
            daily_variable_cost_ratio=round(var_ratio, 4),
            daily_ffe_reserve=round(ffe, 2),
            daily_cash_margin=round(cash_margin, 2),
            unit_contribution_margin_eur=round(cash_margin, 2),
            unit_contribution_margin_pct=round(cash_margin / daily_gross, 4),
            room_rev_per_occupied_night=round(room_gross, 2),
            room_var_cost_per_occupied_night=round(room_var, 2),
            room_contribution_margin_eur=round(room_cm_eur, 2),
            room_contribution_margin_pct=round(room_cm_eur / room_gross, 4),
            annual_fixed_labor=round(fixed_labor, 2),
            annual_fixed_opex=round(fixed_opex, 2),
            annual_fixed_overhead=round(fixed_overhead, 2),
            annual_senior_debt_service=round(annual_debt_service, 2),
            annual_total_fixed_burden=round(total_fixed_burden, 2),
            operating_breakeven_days=round(op_be_days, 2),
            cash_debt_breakeven_days=round(cash_be_days, 1),
            covenant_125_breakeven_days=round(cov_be_days, 1),
        )

    def compute_revpar_trevpar_schedule(self) -> pd.DataFrame:
        """Computes RevPAR and TRevPAR across Years 1 to 3."""
        base_occ = get_annual_weighted_occupancy(SEGOVIA_INE_MONTHLY)
        total_keys = self.rev_cfg.double_rooms_count + self.rev_cfg.full_house_count
        annual_available_keys = total_keys * 365

        years_data = [
            {"year": 1, "ramp": 0.90, "label": "Year 1 (Ramp-up)"},
            {"year": 2, "ramp": 1.00, "label": "Year 2 (Stabilised)"},
            {"year": 3, "ramp": 1.00, "label": "Year 3 (Mature)"},
        ]

        metrics = self.compute_unit_metrics()
        rows = []

        for yd in years_data:
            ramp = yd["ramp"]
            effective_occ = base_occ * ramp
            occupied_days = effective_occ * 365
            lodging_rev = occupied_days * metrics.daily_lodging_revenue
            restaurant_rev = occupied_days * metrics.daily_restaurant_revenue
            tot_rev = lodging_rev + restaurant_rev

            revpar = lodging_rev / annual_available_keys
            trevpar = tot_rev / annual_available_keys

            cash_margin = occupied_days * metrics.unit_contribution_margin_eur
            fixed_cost_coverage = cash_margin / metrics.annual_total_fixed_burden

            rows.append({
                "Year": yd["year"],
                "Stage": yd["label"],
                "Occupancy Rate": f"{effective_occ * 100:.2f}%",
                "Occupied Days": round(occupied_days, 1),
                "Lodging Revenue (EUR)": round(lodging_rev, 2),
                "Total Revenue (EUR)": round(tot_rev, 2),
                "RevPAR (EUR)": round(revpar, 2),
                "TRevPAR (EUR)": round(trevpar, 2),
                "Cash Margin (EUR)": round(cash_margin, 2),
                "Fixed Burden Coverage": f"{fixed_cost_coverage:.2f}x",
            })

        return pd.DataFrame(rows)

    def print_terminal_summary(self):
        """Prints the institutional summary of unit economics."""
        m = self.compute_unit_metrics()
        df_schedule = self.compute_revpar_trevpar_schedule()

        print("=" * 88)
        print(" UNIT ECONOMICS & CONTRIBUTION MARGIN AUDIT (USALI & MARGINAL COSTING)")
        print("=" * 88)
        print(f"Capacity:                        8 keys (7 double rooms + 1 country house) = 2,920 unit-nights/yr")
        print(f"Daily Gross Revenue @ 100% Occ:  EUR {m.daily_gross_revenue:,.2f} ({m.daily_lodging_revenue:,.2f} lodging + {m.daily_restaurant_revenue:,.2f} F&B)")
        print(f"Variable Costs per Occupied Day: EUR {m.daily_total_variable_cost:,.2f} ({m.daily_variable_cost_ratio*100:.1f}% of revenue)")
        print(f"  - F&B COGS (30%):              EUR {m.daily_cogs_restaurant:,.2f}")
        print(f"  - OTA Commissions (60% @ 15%): EUR {m.daily_ota_commission:,.2f}")
        print(f"  - Amenities & Guest Supplies:  EUR {m.daily_amenities_cleaning:,.2f}")
        print(f"  - Breakfast (21 guests @ 5):   EUR {m.daily_breakfast:,.2f}")
        print(f"  - FF&E Reserve (3%):           EUR {m.daily_ffe_reserve:,.2f}")
        print(f"Cash Margin:                     EUR {m.unit_contribution_margin_eur:,.2f} / occupied day ({m.unit_contribution_margin_pct*100:.2f}%)")
        print(f"Room-Night Unit Margin:          EUR {m.room_contribution_margin_eur:,.2f} / room-night ({m.room_contribution_margin_pct*100:.2f}%)")
        print("-" * 88)
        print(f"Fixed Annual Overhead:           EUR {m.annual_fixed_overhead:,.2f} (labour {m.annual_fixed_labor:,.2f} + OPEX {m.annual_fixed_opex:,.2f})")
        print(f"Senior Debt Service:             EUR {m.annual_senior_debt_service:,.2f} (20Y French amortisation @ 4.0%, 12M grace)")
        print(f"Total Annual Fixed Burden:       EUR {m.annual_total_fixed_burden:,.2f}")
        print(f"Operating Break-Even:            {m.operating_breakeven_days:.1f} occupied days ({m.operating_breakeven_days / 365 * 100:.2f}% occupancy)")
        print(f"Cash Debt Service Break-Even:    {m.cash_debt_breakeven_days:.1f} occupied days ({m.cash_debt_breakeven_days / 365 * 100:.2f}% occupancy)")
        print(f"Bank Covenant Floor (1.25x DSCR):{m.covenant_125_breakeven_days:.1f} occupied days ({m.covenant_125_breakeven_days / 365 * 100:.2f}% occupancy)")
        print("-" * 88)
        print("RevPAR & TRevPAR Expansion Schedule:")
        print(df_schedule.to_string(index=False))
        print("=" * 88)
