"""
Unit Economics and Contribution Margin Engine for La Dehesa del Castrillo S.L.

Formalizes:
1. RevPAR (Revenue Per Available Room) and TRevPAR (Total Revenue Per Available Room).
2. Granular unit economics per occupied day and per room-night.
3. Variable cost schedules: F&B COGS, OTA/Channel acquisition commissions, and guest amenities.
4. Unit Contribution Margin (€ and %) and operational leverage over fixed overhead and debt service.
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


@dataclass(frozen=True)
class UnitEconomicsMetrics:
    # Inventory
    total_keys: int                  # 7 rooms + 1 country house = 8 keys
    annual_available_keys: int       # 8 * 365 = 2,920 key-nights
    double_rooms_available: int      # 7 * 365 = 2,555 room-nights
    country_house_available: int     # 1 * 365 = 365 house-nights

    # Full Capacity Run-Rate (100% day equivalent)
    daily_lodging_revenue: float     # €975.00 (€595 rooms + €380 house)
    daily_restaurant_revenue: float  # €525.00 (21 diners @ €25)
    daily_gross_revenue: float       # €1,500.00

    # Variable Costs per Occupied Day
    daily_cogs_restaurant: float     # 30% of €525 = €157.50
    daily_ota_commission: float      # 60% OTA share * 15% comm on lodging (€975) = €87.75
    daily_amenities_cleaning: float  # Variable supplies & laundry = €35.00
    daily_total_variable_cost: float # €280.25
    daily_variable_cost_ratio: float # 18.68%

    # Unit Contribution Margin
    unit_contribution_margin_eur: float  # €1,219.75 per occupied day
    unit_contribution_margin_pct: float  # 81.32%

    # Per-Room Key Equivalent (Boutique Room + 2 Diners)
    room_rev_per_occupied_night: float   # €85 + €50 = €135.00
    room_var_cost_per_occupied_night: float # €15 (F&B) + €7.65 (OTA) + €4.00 = €26.65
    room_contribution_margin_eur: float  # €108.35
    room_contribution_margin_pct: float  # 80.26%

    # Fixed Burden & Operating Leverage
    annual_fixed_labor: float            # €60,075.00
    annual_fixed_opex: float             # €12,159.00
    annual_fixed_overhead: float         # €72,234.00
    annual_senior_debt_service: float    # €43,521.84
    annual_total_fixed_burden: float     # €115,755.84

    # Breakeven Occupied Days & Occupancy Rates
    operating_breakeven_days: float      # €72,234 / €1,219.75 = 59.2 days (16.23%)
    cash_debt_breakeven_days: float      # €115,756 / €1,219.75 = 94.9 days (26.00%)
    covenant_125_breakeven_days: float   # €126,636 / €1,219.75 = 103.8 days (28.44%)


class UnitEconomicsEngine:
    """Computes RevPAR, TRevPAR, and granular contribution margins."""

    def __init__(
        self,
        rev_cfg: RevenueModelConfig = RevenueModelConfig(),
        labor_cfg: LaborStructure = LaborStructure(),
        opex_cfg: FixedOpexStructure = FixedOpexStructure(),
        financing_cfg: FinancingStructure = FinancingStructure(),
        ota_share: float = 0.60,
        ota_commission_rate: float = 0.15,
        daily_amenities_cost: float = 35.0,
    ):
        self.rev_cfg = rev_cfg
        self.labor_cfg = labor_cfg
        self.opex_cfg = opex_cfg
        self.financing_cfg = financing_cfg
        self.ota_share = ota_share
        self.ota_commission_rate = ota_commission_rate
        self.daily_amenities_cost = daily_amenities_cost

    def compute_unit_metrics(self) -> UnitEconomicsMetrics:
        """Calculates foundational unit economics at 100% capacity baseline."""
        rooms_rev = self.rev_cfg.double_rooms_count * self.rev_cfg.double_room_adr
        house_rev = self.rev_cfg.full_house_count * self.rev_cfg.full_house_adr
        daily_lodging = rooms_rev + house_rev

        diners = (
            self.rev_cfg.double_rooms_count * self.rev_cfg.restaurant_diners_per_double_room
            + self.rev_cfg.full_house_count * self.rev_cfg.restaurant_diners_per_full_house
        )
        daily_dining = diners * self.rev_cfg.restaurant_average_ticket
        daily_gross = daily_lodging + daily_dining

        # Variable cost schedule
        cogs_fnb = daily_dining * self.rev_cfg.restaurant_cogs_ratio
        ota_comm = daily_lodging * self.ota_share * self.ota_commission_rate
        amenities = self.daily_amenities_cost
        tot_var = cogs_fnb + ota_comm + amenities
        var_ratio = tot_var / daily_gross

        unit_cm_eur = daily_gross - tot_var
        unit_cm_pct = unit_cm_eur / daily_gross

        # Per room-night equivalent (1 double room + 2 restaurant covers)
        room_gross = self.rev_cfg.double_room_adr + (2 * self.rev_cfg.restaurant_average_ticket)
        room_var = (
            (2 * self.rev_cfg.restaurant_average_ticket * self.rev_cfg.restaurant_cogs_ratio)
            + (self.rev_cfg.double_room_adr * self.ota_share * self.ota_commission_rate)
            + (amenities / (self.rev_cfg.double_rooms_count + self.rev_cfg.full_house_count))
        )
        room_cm_eur = room_gross - room_var
        room_cm_pct = room_cm_eur / room_gross

        # Fixed overhead
        fixed_labor = self.labor_cfg.total_annual_payroll
        fixed_opex = self.opex_cfg.total_fixed_opex
        fixed_overhead = fixed_labor + fixed_opex

        # Senior debt service (15 yr @ 3.5%, 507.5k)
        r_monthly = self.financing_cfg.loan_interest_rate / 12.0
        n_months = self.financing_cfg.loan_tenure_years * 12
        p = self.financing_cfg.senior_debt_principal
        pmt_monthly = p * (r_monthly * (1 + r_monthly) ** n_months) / ((1 + r_monthly) ** n_months - 1)
        annual_debt_service = pmt_monthly * 12.0

        total_fixed_burden = fixed_overhead + annual_debt_service

        # Breakeven occupied days
        op_be_days = fixed_overhead / unit_cm_eur
        cash_be_days = total_fixed_burden / unit_cm_eur
        cov_125_burden = fixed_overhead + (annual_debt_service * self.financing_cfg.target_dscr)
        cov_be_days = cov_125_burden / unit_cm_eur

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
            daily_total_variable_cost=round(tot_var, 2),
            daily_variable_cost_ratio=round(var_ratio, 4),
            unit_contribution_margin_eur=round(unit_cm_eur, 2),
            unit_contribution_margin_pct=round(unit_cm_pct, 4),
            room_rev_per_occupied_night=round(room_gross, 2),
            room_var_cost_per_occupied_night=round(room_var, 2),
            room_contribution_margin_eur=round(room_cm_eur, 2),
            room_contribution_margin_pct=round(room_cm_pct, 4),
            annual_fixed_labor=round(fixed_labor, 2),
            annual_fixed_opex=round(fixed_opex, 2),
            annual_fixed_overhead=round(fixed_overhead, 2),
            annual_senior_debt_service=round(annual_debt_service, 2),
            annual_total_fixed_burden=round(total_fixed_burden, 2),
            operating_breakeven_days=round(op_be_days, 1),
            cash_debt_breakeven_days=round(cash_be_days, 1),
            covenant_125_breakeven_days=round(cov_be_days, 1),
        )

    def compute_revpar_trevpar_schedule(self) -> pd.DataFrame:
        """Computes RevPAR and TRevPAR across Year 1 to Year 3."""
        base_occ = get_annual_weighted_occupancy(SEGOVIA_INE_MONTHLY)
        total_keys = self.rev_cfg.double_rooms_count + self.rev_cfg.full_house_count
        annual_available_keys = total_keys * 365  # 2,920 key-nights

        # Ramp-up factors from model
        years_data = [
            {"year": 1, "ramp": 0.90, "label": "Year 1 (Ramp-up)"},
            {"year": 2, "ramp": 1.00, "label": "Year 2 (Stabilized)"},
            {"year": 3, "ramp": 1.05, "label": "Year 3 (Mature)"},
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

            # Contribution margin generated
            var_cost = occupied_days * metrics.daily_total_variable_cost
            cm_generated = tot_rev - var_cost
            fixed_cost_coverage = cm_generated / metrics.annual_total_fixed_burden

            rows.append({
                "Year": yd["year"],
                "Stage": yd["label"],
                "Occupancy Rate": f"{effective_occ * 100:.2f}%",
                "Occupied Days": round(occupied_days, 1),
                "Lodging Revenue (€)": round(lodging_rev, 2),
                "Total Revenue (€)": round(tot_rev, 2),
                "RevPAR (€)": round(revpar, 2),
                "TRevPAR (€)": round(trevpar, 2),
                "Contribution Margin (€)": round(cm_generated, 2),
                "Fixed Burden Coverage": f"{fixed_cost_coverage:.2f}x",
            })

        return pd.DataFrame(rows)

    def print_terminal_summary(self):
        """Prints formatted institutional summary of unit economics and contribution margin."""
        m = self.compute_unit_metrics()
        df_schedule = self.compute_revpar_trevpar_schedule()

        print("=" * 88)
        print(" UNIT ECONOMICS & CONTRIBUTION MARGIN AUDIT (USALI & MARGINAL COSTING)")
        print("=" * 88)
        print(f"Capacity:                        8 Keys (7 Double Rooms + 1 Country House) = 2,920 Unit-Nights/yr")
        print(f"Daily Gross Revenue @ 100% Occ:  €{m.daily_gross_revenue:,.2f} (€{m.daily_lodging_revenue:,.2f} Lodging + €{m.daily_restaurant_revenue:,.2f} F&B)")
        print(f"Variable Costs per Occupied Day: €{m.daily_total_variable_cost:,.2f} ({m.daily_variable_cost_ratio*100:.1f}% variable cost ratio)")
        print(f"  - F&B COGS (30%):              €{m.daily_cogs_restaurant:,.2f}")
        print(f"  - OTA Commissions (60% @ 15%): €{m.daily_ota_commission:,.2f}")
        print(f"  - Amenities & Guest Supplies:  €{m.daily_amenities_cleaning:,.2f}")
        print(f"Unit Contribution Margin:        €{m.unit_contribution_margin_eur:,.2f} / occupied day ({m.unit_contribution_margin_pct*100:.2f}%)")
        print(f"Room-Night Unit Margin:          €{m.room_contribution_margin_eur:,.2f} / room-night ({m.room_contribution_margin_pct*100:.2f}%)")
        print("-" * 88)
        print(f"Fixed Annual Overhead:           €{m.annual_fixed_overhead:,.2f} (Labor €{m.annual_fixed_labor:,.2f} + OPEX €{m.annual_fixed_opex:,.2f})")
        print(f"Senior Debt Service:             €{m.annual_senior_debt_service:,.2f} (15Y French amortization @ 3.5%)")
        print(f"Total Annual Fixed Burden:       €{m.annual_total_fixed_burden:,.2f}")
        print(f"Operating Break-Even:            {m.operating_breakeven_days:.1f} occupied days ({m.operating_breakeven_days / 365 * 100:.2f}% occupancy)")
        print(f"Cash Debt Service Break-Even:    {m.cash_debt_breakeven_days:.1f} occupied days ({m.cash_debt_breakeven_days / 365 * 100:.2f}% occupancy)")
        print(f"Bank Covenant Floor (1.25x DSCR):{m.covenant_125_breakeven_days:.1f} occupied days ({m.covenant_125_breakeven_days / 365 * 100:.2f}% occupancy)")
        print("-" * 88)
        print("RevPAR & TRevPAR Expansion Schedule:")
        print(df_schedule.to_string(index=False))
        print("=" * 88)
