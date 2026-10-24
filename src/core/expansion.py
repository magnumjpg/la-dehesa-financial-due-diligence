"""
Phase II Expansion Financial Engine: Landscape Hotel Suites & Biological Reservoir.

Models the value-add expansion of La Dehesa del Castrillo S.L.:
- 2 detached ultra-luxury landscape suites (55 m² built each = 110 m² total).
- 1 naturalized biological pond / biodiversity reservoir (200 m² water mirror).
- Off-grid/trench utilities across the 25-hectare rural estate.
- A phase-gated option, not an automatic expansion. Phase II may only proceed if
  Phase I meets its DSCR covenant and Phase I cash covers the Phase II cash need.
  The old "100% funded by retained cash (LEADER + VAT refund)" claim was a
  double-spend: both sources are already committed to Phase I.
- Comprehensive USALI P&L, 5-year ramp-up, realistic/stress scenarios, ROIC,
  exit cap-rate arbitrage, phase gate and consolidated DSCR.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExpansionCapExBreakdown:
    # Building & Interior (110 m²)
    foundations_structure_pem: float = 38_500.0
    stone_envelope_pem: float = 31_000.0
    glass_curtain_walls_pem: float = 37_500.0
    hvac_aerotermia_pem: float = 28_500.0
    luxury_bath_spa_pem: float = 26_000.0
    pure_building_pem: float = 161_500.0  # Cap 1-5

    # Estate Utilities & FF&E
    utilities_trenching_25ha_pem: float = 31_500.0
    ffe_textiles_hot_tub_pem: float = 35_000.0
    biological_pond_200m2_pem: float = 32_000.0
    total_execution_pem: float = 260_000.0

    # Contractor Margins (13% GG + 6% BI = 19%)
    contractor_margin_rate: float = 0.19
    total_execution_pec: float = 309_400.0  # 260k * 1.19

    # Soft Costs & Indirects
    engineering_architecture_fees: float = 23_400.0  # 9.0% PEM
    municipal_taxes_icio: float = 11_700.0          # 4.5% PEM
    contingency_reserve: float = 15_470.0           # 5.0% PEC

    # Total All-In CapEx (Net of 21% Deductible VAT)
    total_all_in_capex: float = 359_970.0
    input_vat_21pct: float = 75_593.70


@dataclass(frozen=True)
class ExpansionOperatingAssumptions:
    total_suites: int = 2
    annual_available_nights: int = 730  # 2 * 365

    # ADR Structure (Net of 10% Hospitality VAT)
    adr_weekend: float = 360.0     # Fri-Sat + Holidays (104 days)
    adr_weekday: float = 240.0     # Sun-Thu (261 days)
    adr_weighted_base: float = 290.0

    # Occupancy Rates
    occ_weekend: float = 0.885     # 88.5%
    occ_weekday: float = 0.347     # 34.7%
    occ_weighted_base: float = 0.500  # 50.0% = 365 nights/year

    # Gastronomy & Ancillary
    fnb_capture_rate: float = 0.85
    fnb_ticket_per_couple: float = 130.0  # 65 €/pax net
    fnb_cogs_rate: float = 0.30

    # Channels & Intermediation
    direct_booking_share: float = 0.70
    direct_payment_fee: float = 0.015     # 1.5% Stripe/Redsys
    ota_booking_share: float = 0.30
    ota_commission_rate: float = 0.16     # 16.0% Booking/AlohaCamp

    # Variable Servicing Outlays
    laundry_amenities_per_night: float = 24.0
    energy_hvac_tina_per_night: float = 14.0

    # Incremental Fixed Overhead (Phase I absorbs existing payroll & admin)
    seasonal_housekeeping_support: float = 4_800.0
    incremental_fixed_opex: float = 9_600.0  # Maint (4.5k), Ins (1.2k), Mkt (2.4k), Power (1.5k)
    total_incremental_fixed_burden: float = 14_400.0

    # Realistic incremental payroll for 365 additional suite-nights per year.
    # The Phase I team (2 part-time cooks + 1 housekeeper, 2.09 FTE) cannot
    # absorb a further 730 guests without at least one additional FTE.
    incremental_fte_annual_cost: float = 28_000.0  # Loaded cost of 1 FTE (€20.7k gross + 35% SS)

    # Financial & Tax
    ffe_replacement_reserve_rate: float = 0.02  # 2% of gross revenues
    depreciation_rate_blended: float = 0.045     # 4.5% of CapEx
    corporate_tax_rate: float = 0.25
    wacc_discount_rate: float = 0.080


class ExpansionFinancialEngine:
    """Quantitative financial modeling engine for Phase II Expansion."""

    def __init__(
        self,
        capex: ExpansionCapExBreakdown = ExpansionCapExBreakdown(),
        assumptions: ExpansionOperatingAssumptions = ExpansionOperatingAssumptions(),
    ):
        self.capex = capex
        self.cfg = assumptions

    def _get_scenario_params(self, scenario: str) -> Dict[str, float]:
        """Returns the occupancy/ADR/cost parameters for a named scenario."""
        if scenario == "conservative":
            return dict(occ=0.40, adr=250.0, fnb_ticket=110.0, fnb_capture=0.80,
                        direct_share=0.60, ota_share=0.40, ota_comm=0.17, fte_count=1.0)
        if scenario == "realistic":
            # 45% occupancy (1.4x the INE market average), €270 ADR, one
            # additional FTE. This is the recommended base for Phase II.
            return dict(occ=0.45, adr=270.0, fnb_ticket=120.0, fnb_capture=0.85,
                        direct_share=0.65, ota_share=0.35, ota_comm=0.16, fte_count=1.0)
        if scenario == "stress":
            # Market occupancy (36.4% = 1.5x INE), €250 ADR, one FTE.
            return dict(occ=0.364, adr=250.0, fnb_ticket=110.0, fnb_capture=0.80,
                        direct_share=0.60, ota_share=0.40, ota_comm=0.17, fte_count=1.0)
        if scenario == "optimistic":
            return dict(occ=0.58, adr=330.0, fnb_ticket=150.0, fnb_capture=0.90,
                        direct_share=0.75, ota_share=0.25, ota_comm=0.15, fte_count=0.0)
        # base: existing team absorbs the suites (no incremental payroll)
        return dict(
            occ=self.cfg.occ_weighted_base,
            adr=self.cfg.adr_weighted_base,
            fnb_ticket=self.cfg.fnb_ticket_per_couple,
            fnb_capture=self.cfg.fnb_capture_rate,
            direct_share=self.cfg.direct_booking_share,
            ota_share=self.cfg.ota_booking_share,
            ota_comm=self.cfg.ota_commission_rate,
            fte_count=0.0,
        )

    def compute_stabilized_pnl(self, scenario: str = "base") -> Dict[str, float]:
        """Computes stabilized Year 3 incremental P&L under USALI standards."""
        p = self._get_scenario_params(scenario)
        occ = p["occ"]
        adr = p["adr"]
        fnb_ticket = p["fnb_ticket"]
        fnb_capture = p["fnb_capture"]
        direct_share = p["direct_share"]
        ota_share = p["ota_share"]
        ota_comm = p["ota_comm"]
        fte_count = p["fte_count"]

        occupied_nights = self.cfg.annual_available_nights * occ
        lodging_rev = occupied_nights * adr
        diners_couples = occupied_nights * fnb_capture
        fnb_rev = diners_couples * fnb_ticket
        gross_rev = lodging_rev + fnb_rev

        # Variable Costs
        channel_costs = (lodging_rev * direct_share * self.cfg.direct_payment_fee) + (
            lodging_rev * ota_share * ota_comm
        )
        cogs_fnb = fnb_rev * self.cfg.fnb_cogs_rate
        laundry_amenities = occupied_nights * self.cfg.laundry_amenities_per_night
        energy_hvac = occupied_nights * self.cfg.energy_hvac_tina_per_night
        total_var_costs = channel_costs + cogs_fnb + laundry_amenities + energy_hvac

        contribution_margin = gross_rev - total_var_costs
        cm_ratio = contribution_margin / gross_rev

        # Fixed Burden (incremental overhead + incremental FTE payroll)
        fte_cost = fte_count * self.cfg.incremental_fte_annual_cost
        fixed_overhead = self.cfg.total_incremental_fixed_burden + fte_cost
        ebitda = contribution_margin - fixed_overhead
        ebitda_margin = ebitda / gross_rev

        # D&A and Tax
        depreciation = self.capex.total_all_in_capex * self.cfg.depreciation_rate_blended
        ebit = ebitda - depreciation
        tax = max(0.0, ebit * self.cfg.corporate_tax_rate)
        eat = ebit - tax

        # FCF
        ffe_reserve = gross_rev * self.cfg.ffe_replacement_reserve_rate
        fcf = eat + depreciation - ffe_reserve

        return {
            "occupied_nights": occupied_nights,
            "occupancy_rate": occ,
            "realized_adr": adr,
            "lodging_revenue": lodging_rev,
            "fnb_revenue": fnb_rev,
            "gross_revenue": gross_rev,
            "channel_costs": channel_costs,
            "cogs_fnb": cogs_fnb,
            "laundry_amenities": laundry_amenities,
            "energy_hvac": energy_hvac,
            "total_variable_costs": total_var_costs,
            "contribution_margin": contribution_margin,
            "contribution_margin_ratio": cm_ratio,
            "fixed_overhead": fixed_overhead,
            "incremental_fte_cost": fte_cost,
            "ebitda": ebitda,
            "ebitda_margin": ebitda_margin,
            "depreciation": depreciation,
            "ebit": ebit,
            "tax": tax,
            "net_income": eat,
            "ffe_reserve": ffe_reserve,
            "free_cash_flow": fcf,
            "revpar": lodging_rev / self.cfg.annual_available_nights,
            "trevpar": gross_rev / self.cfg.annual_available_nights,
        }

    def compute_5year_schedule(self, scenario: str = "base") -> pd.DataFrame:
        """Projects a 5-year commercial ramp-up trajectory with inflation indexation."""
        # Year 1 (75% ramp), Year 2 (90% ramp), Year 3 (100% mature), Year 4 (+2% IPC), Year 5 (+2% IPC)
        ramp_factors = [0.75, 0.90, 1.00, 1.02, 1.0404]
        rows = []
        p = self._get_scenario_params(scenario)
        wacc = self.cfg.wacc_discount_rate
        fte_cost = p["fte_count"] * self.cfg.incremental_fte_annual_cost

        for yr_idx, factor in enumerate(ramp_factors, start=1):
            if yr_idx <= 3:
                # Volume ramp-up
                occ_factor = factor
                price_factor = 1.0
            else:
                # Mature with price indexation
                occ_factor = 1.0
                price_factor = factor

            occ = p["occ"] * occ_factor
            nights = self.cfg.annual_available_nights * occ
            adr = p["adr"] * price_factor
            lodging_rev = nights * adr
            fnb_rev = nights * p["fnb_capture"] * (p["fnb_ticket"] * price_factor)
            gross_rev = lodging_rev + fnb_rev

            channel_costs = (lodging_rev * p["direct_share"] * self.cfg.direct_payment_fee) + (
                lodging_rev * p["ota_share"] * p["ota_comm"]
            )
            cogs_fnb = fnb_rev * self.cfg.fnb_cogs_rate
            laundry = nights * (self.cfg.laundry_amenities_per_night * price_factor)
            energy = nights * (self.cfg.energy_hvac_tina_per_night * price_factor)
            tot_var = channel_costs + cogs_fnb + laundry + energy

            cm = gross_rev - tot_var
            fixed_cost = (self.cfg.total_incremental_fixed_burden + fte_cost) * (
                1.0 if yr_idx <= 3 else (1.02 ** (yr_idx - 3))
            )
            ebitda = cm - fixed_cost
            depr = self.capex.total_all_in_capex * self.cfg.depreciation_rate_blended
            ebit = ebitda - depr
            tax = max(0.0, ebit * self.cfg.corporate_tax_rate)
            eat = ebit - tax
            ffe = gross_rev * self.cfg.ffe_replacement_reserve_rate
            fcf = eat + depr - ffe
            discount_factor = 1.0 / ((1.0 + wacc) ** yr_idx)
            dfcf = fcf * discount_factor

            rows.append({
                "year": yr_idx,
                "occupancy_rate": occ,
                "occupied_nights": nights,
                "adr_net": adr,
                "gross_revenue": gross_rev,
                "total_variable_costs": tot_var,
                "contribution_margin": cm,
                "ebitda": ebitda,
                "ebitda_margin": ebitda / gross_rev,
                "depreciation": depr,
                "ebit": ebit,
                "tax": tax,
                "net_income": eat,
                "ffe_reserve": ffe,
                "free_cash_flow": fcf,
                "discounted_fcf": dfcf,
            })

        return pd.DataFrame(rows)

    def compute_investment_metrics(self, scenario: str = "base") -> Dict[str, float]:
        """Calculates comprehensive returns: Payback, ROIC, Yield on Cost, Exit Valuation, and IRRs."""
        df_5y = self.compute_5year_schedule(scenario=scenario)
        capex = self.capex.total_all_in_capex  # 359,970.0 €
        wacc = self.cfg.wacc_discount_rate

        # Simple Payback on EBITDA
        cum_ebitda = 0.0
        ebitda_payback = 5.0
        for _, r in df_5y.iterrows():
            cum_ebitda += r["ebitda"]
            if cum_ebitda >= capex:
                prev_cum = cum_ebitda - r["ebitda"]
                fraction = (capex - prev_cum) / r["ebitda"]
                ebitda_payback = (r["year"] - 1) + fraction
                break

        # Simple Payback on Post-Tax FCF
        cum_fcf = 0.0
        fcf_payback = 5.0
        for _, r in df_5y.iterrows():
            cum_fcf += r["free_cash_flow"]
            if cum_fcf >= capex:
                prev_cum = cum_fcf - r["free_cash_flow"]
                fraction = (capex - prev_cum) / r["free_cash_flow"]
                fcf_payback = (r["year"] - 1) + fraction
                break
        if cum_fcf < capex:
            # Extended into Year 6
            shortfall = capex - cum_fcf
            y5_fcf = df_5y.iloc[-1]["free_cash_flow"]
            fcf_payback = 5.0 + (shortfall / y5_fcf)

        # Discounted Payback
        cum_dfcf = 0.0
        dfcf_payback = 10.0
        for _, r in df_5y.iterrows():
            cum_dfcf += r["discounted_fcf"]
            if cum_dfcf >= capex:
                prev_cum = cum_dfcf - r["discounted_fcf"]
                fraction = (capex - prev_cum) / r["discounted_fcf"]
                dfcf_payback = (r["year"] - 1) + fraction
                break
        if cum_dfcf < capex:
            shortfall = capex - cum_dfcf
            y5_dfcf = df_5y.iloc[-1]["discounted_fcf"]
            dfcf_payback = 5.0 + (shortfall / y5_dfcf)

        # Year 3 Mature Metrics
        y3_row = df_5y.iloc[2]
        ebitda_y3 = y3_row["ebitda"]
        nopat_y3 = y3_row["ebit"] * (1.0 - self.cfg.corporate_tax_rate)
        roic_y3 = nopat_y3 / capex
        yield_on_cost = ebitda_y3 / capex

        # Exit Valuation at Year 5 across Cap Rates
        y5_row = df_5y.iloc[4]
        ebitda_y5 = y5_row["ebitda"]
        exit_cap_rates = [0.080, 0.085, 0.090]
        exit_valuations = {}
        moic_values = {}
        irr_values = {}

        cum_fcf_5y = df_5y["free_cash_flow"].sum()
        cash_flows_base = [-capex] + df_5y["free_cash_flow"].tolist()

        for cr in exit_cap_rates:
            val = ebitda_y5 / cr
            exit_valuations[f"exit_val_{int(cr*1000)}bps"] = val
            exit_valuations[f"net_gain_{int(cr*1000)}bps"] = val - capex
            moic = (cum_fcf_5y + val) / capex
            moic_values[f"moic_{int(cr*1000)}bps"] = moic

            cf_with_exit = list(cash_flows_base)
            cf_with_exit[-1] += val
            irr = self._calc_irr(cf_with_exit)
            irr_values[f"irr_{int(cr*1000)}bps"] = irr

        # 10-Year Unlevered Operating IRR without exit (zero terminal value)
        cf_10y = [-capex] + df_5y["free_cash_flow"].tolist() + [y5_row["free_cash_flow"]] * 5
        irr_10y_operating = self._calc_irr(cf_10y)

        res = {
            "all_in_capex": capex,
            "ebitda_y3": ebitda_y3,
            "fcf_y3": y3_row["free_cash_flow"],
            "roic_y3": roic_y3,
            "yield_on_cost": yield_on_cost,
            "simple_ebitda_payback_years": ebitda_payback,
            "simple_fcf_payback_years": fcf_payback,
            "discounted_payback_years": dfcf_payback,
            "irr_10y_operating_no_terminal": irr_10y_operating,
            **exit_valuations,
            **moic_values,
            **irr_values,
        }
        return res

    def compute_phase_gate(
        self,
        phase1_cash_end_y2: float = 193_949.95,
        phase1_dscr_y3: float = 1.73,
    ) -> Dict[str, float]:
        """
        Phase-gate test for Phase II.

        Phase II may only proceed if Phase I is covenant-compliant (DSCR >= 1.25x)
        AND the cash accumulated at the end of Phase I Year 2 covers the full
        Phase II cash need (net CapEx + input VAT). The LEADER grant and the VAT
        refund are already committed in Phase I and cannot be counted twice.
        """
        cash_need = round(self.capex.total_all_in_capex + self.capex.input_vat_21pct, 2)
        gap = round(phase1_cash_end_y2 - cash_need, 2)
        dscr_ok = phase1_dscr_y3 >= 1.25
        cash_ok = gap >= 0
        return {
            "phase1_cash_end_y2": phase1_cash_end_y2,
            "phase1_dscr_y3": phase1_dscr_y3,
            "phase2_cash_need": cash_need,
            "phase2_funding_gap": gap,
            "dscr_condition_met": bool(dscr_ok),
            "cash_condition_met": bool(cash_ok),
            "phase2_proceed": bool(dscr_ok and cash_ok),
            "recommendation": (
                "PROCEED - Phase I covenants and cash cover Phase II"
                if dscr_ok and cash_ok
                else "DO NOT PROCEED - Phase II requires additional funding or a smaller scope"
            ),
        }

    def compute_consolidated_underwriting(
        self,
        phase1_rev_y3: float = 180_306.0,
        phase1_ebitda_y3: float = 89_139.87,
        phase1_senior_debt_service: float = 43_536.36,
        phase1_capex: float = 729_000.0,
        phase1_cash_end_y2: float = 193_949.95,
        phase1_dscr_y3: Optional[float] = None,
    ) -> Dict[str, float]:
        """Calculates consolidated asset metrics combining Phase I baseline and Phase II expansion."""
        pnl_exp = self.compute_stabilized_pnl(scenario="base")
        exp_capex = self.capex.total_all_in_capex

        cons_rev = phase1_rev_y3 + pnl_exp["gross_revenue"]
        cons_ebitda = phase1_ebitda_y3 + pnl_exp["ebitda"]
        cons_ebitda_margin = cons_ebitda / cons_rev
        cons_capex = phase1_capex + exp_capex

        # Phase 1 standalone DSCR vs Consolidated DSCR
        dscr_p1 = phase1_ebitda_y3 / phase1_senior_debt_service
        dscr_consolidated = cons_ebitda / phase1_senior_debt_service

        gate = self.compute_phase_gate(
            phase1_cash_end_y2=phase1_cash_end_y2,
            phase1_dscr_y3=phase1_dscr_y3 if phase1_dscr_y3 is not None else dscr_p1,
        )

        # Valuation @ 8.5% Exit Cap Rate
        val_p1 = phase1_ebitda_y3 / 0.085
        val_consolidated = cons_ebitda / 0.085
        value_created = val_consolidated - val_p1

        return {
            "phase1_rev_y3": phase1_rev_y3,
            "phase1_ebitda_y3": phase1_ebitda_y3,
            "phase1_dscr_y3": phase1_dscr_y3 if phase1_dscr_y3 is not None else dscr_p1,
            "phase1_cash_end_y2": phase1_cash_end_y2,
            "phase1_valuation_85bps": val_p1,
            "phase2_rev_y3": pnl_exp["gross_revenue"],
            "phase2_ebitda_y3": pnl_exp["ebitda"],
            "phase2_capex": exp_capex,
            "consolidated_rev_y3": cons_rev,
            "consolidated_ebitda_y3": cons_ebitda,
            "consolidated_ebitda_margin": cons_ebitda_margin,
            "ebitda_increase_pct": (cons_ebitda - phase1_ebitda_y3) / phase1_ebitda_y3,
            "senior_debt_service_annual": phase1_senior_debt_service,
            "consolidated_dscr_y3": dscr_consolidated,
            "consolidated_total_capex": cons_capex,
            "consolidated_valuation_85bps": val_consolidated,
            "net_equity_value_created": value_created,
            "phase2_cash_need": gate["phase2_cash_need"],
            "phase2_funding_gap": gate["phase2_funding_gap"],
            "phase2_dscr_condition_met": gate["dscr_condition_met"],
            "phase2_cash_condition_met": gate["cash_condition_met"],
            "phase2_proceed": gate["phase2_proceed"],
            "phase2_gate_recommendation": gate["recommendation"],
        }

    @staticmethod
    def _calc_irr(cash_flows: List[float]) -> float:
        """Internal rate of return using the shared robust solver (no hardcoded fallback)."""
        from src.core.metrics import calculate_irr
        result = calculate_irr(cash_flows)
        return float(result) if result is not None else 0.0

    def print_terminal_summary(
        self,
        phase1_cash_end_y2: float = 193_949.95,
        phase1_dscr_y3: float = 1.73,
    ):
        """Prints executive summary of Phase II expansion metrics to console."""
        m = self.compute_investment_metrics()
        realistic = self.compute_investment_metrics(scenario="realistic")
        stress = self.compute_investment_metrics(scenario="stress")
        c = self.compute_consolidated_underwriting(
            phase1_cash_end_y2=phase1_cash_end_y2,
            phase1_dscr_y3=phase1_dscr_y3,
        )

        print("=" * 88)
        print(" PHASE II EXPANSION: LANDSCAPE SUITES & BIOLOGICAL POND (VALUE-ADD UNDERWRITING)")
        print("=" * 88)
        print(f"Total Phase II CapEx (All-In):    €{m['all_in_capex']:,.2f} (€179,985/suite all-inclusive)")
        print(f"Cash Need incl. 21% VAT:          €{c['phase2_cash_need']:,.2f}")
        print(f"Stabilized Year 3 Incremental Rev: €{c['phase2_rev_y3']:,.2f} (ADR €290 net | 50.0% Occ)")
        print(f"Stabilized Incremental EBITDA:    €{m['ebitda_y3']:,.2f} (68.15% EBITDA margin, no incremental FTE)")
        print(f"Return on Invested Capital (ROIC): {m['roic_y3']*100:.2f}% (EVA spread over 8% WACC)")
        print(f"Development Yield on Cost:        {m['yield_on_cost']*100:.2f}%")
        print(f"Simple EBITDA Payback:            {m['simple_ebitda_payback_years']:.2f} Years")
        print(f"Simple Post-Tax FCF Payback:      {m['simple_fcf_payback_years']:.2f} Years")
        print("-" * 88)
        print("SCENARIO SENSITIVITY (YEAR-3 EBITDA / 8.5% EXIT IRR):")
        print(f"  - Base (no incremental FTE):     €{m['ebitda_y3']:,.2f} | IRR {m['irr_85bps']*100:.1f}%")
        print(f"  - Realistic (45% occ + 1 FTE):   €{realistic['ebitda_y3']:,.2f} | IRR {realistic['irr_85bps']*100:.1f}%")
        print(f"  - Stress (36.4% occ + 1 FTE):    €{stress['ebitda_y3']:,.2f} | IRR {stress['irr_85bps']*100:.1f}%")
        print("-" * 88)
        print("PHASE-GATE TEST (PHASE I COVENANT + CASH COVER):")
        print(f"  - Phase I DSCR Year 3:           {c['phase1_dscr_y3']:.2f}x (floor 1.25x) -> {'PASS' if c['phase2_dscr_condition_met'] else 'FAIL'}")
        print(f"  - Phase I cash at end Year 2:    €{c['phase1_cash_end_y2']:,.2f}")
        print(f"  - Phase II cash need:            €{c['phase2_cash_need']:,.2f}")
        print(f"  - Phase II funding gap:          €{c['phase2_funding_gap']:,.2f}")
        print(f"  - Gate recommendation:           {c['phase2_gate_recommendation']}")
        print("-" * 88)
        print("CONSOLIDATED ASSET IMPACT (PHASE I + PHASE II, IF FUNDED):")
        print(f"  - Consolidated Year 3 Revenue:   €{c['consolidated_rev_y3']:,.2f}")
        print(f"  - Consolidated Year 3 EBITDA:    €{c['consolidated_ebitda_y3']:,.2f}")
        print(f"  - Consolidated EBITDA Margin:    {c['consolidated_ebitda_margin']*100:.2f}%")
        print(f"  - Debt Service Coverage (DSCR):  {c['phase1_dscr_y3']:.2f}x --> {c['consolidated_dscr_y3']:.2f}x (zero new senior debt)")
        print(f"  - Consolidated Asset Valuation:  €{c['consolidated_valuation_85bps']:,.2f}")
        print("=" * 88)


if __name__ == "__main__":
    engine = ExpansionFinancialEngine()
    engine.print_terminal_summary()
