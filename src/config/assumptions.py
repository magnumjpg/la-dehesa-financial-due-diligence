"""
Financial and operational assumptions for La Dehesa del Castrillo S.L.

This module formalizes institutional parameters for:
1. CapEx breakdown (depreciable vs. non-depreciable asset bases).
2. Capital structure (Senior Debt, Sponsor Equity, Credit Line, LEADER grant).
3. Labor cost schedules under the Segovia Provincial Hospitality Collective Agreement.
4. Operational inventory, pricing, and variable margins.
5. Tax regimes: VAT (10% hospitality vs 21% CapEx/OPEX) and Corporate Income Tax (25%).
6. Debt sizing and covenant constraints (French amortization, minimum DSCR).
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class CapExAsset:
    """Individual CapEx asset item with depreciation and VAT classification."""
    name: str
    amount: float
    vat_rate: float
    depreciation_rate: float  # Annual tax-deductible depreciation rate (Ley 27/2014)
    is_depreciable: bool


@dataclass(frozen=True)
class CapExStructure:
    """
    Project CapEx structure.
    Land is non-depreciable. Buildings and installations are depreciated
    according to Spanish Corporate Income Tax official tables (IS).
    """
    land: CapExAsset = CapExAsset(
        name="Terreno (25 ha en Segovia)",
        amount=250_000.0,
        vat_rate=0.21,
        depreciation_rate=0.0,
        is_depreciable=False,
    )
    renovation: CapExAsset = CapExAsset(
        name="Reforma Integral (550 m2 civil works)",
        amount=440_000.0,
        vat_rate=0.21,
        depreciation_rate=0.03,  # 3% annual (Edificaciones comerciales/hostelería)
        is_depreciable=True,
    )
    biopool_landscaping: CapExAsset = CapExAsset(
        name="Biopiscina y Paisajismo",
        amount=35_000.0,
        vat_rate=0.21,
        depreciation_rate=0.10,  # 10% annual (Instalaciones y acondicionamiento exterior)
        is_depreciable=True,
    )
    digitalization: CapExAsset = CapExAsset(
        name="Digitalizacion y PMS (Kit Digital)",
        amount=4_000.0,
        vat_rate=0.21,
        depreciation_rate=0.25,  # 25% annual (Software, cerraduras inteligentes, hardware)
        is_depreciable=True,
    )

    @property
    def total_base_capex(self) -> float:
        """Total base CapEx excluding digitalization buffer (725.000 €)."""
        return self.land.amount + self.renovation.amount + self.biopool_landscaping.amount

    @property
    def total_capex(self) -> float:
        """Total initial asset acquisition cost (729.000 €)."""
        return self.total_base_capex + self.digitalization.amount

    @property
    def total_input_vat(self) -> float:
        """Initial input VAT (IVA soportado deducible al 21%)."""
        return (
            self.land.amount * self.land.vat_rate
            + self.renovation.amount * self.renovation.vat_rate
            + self.biopool_landscaping.amount * self.biopool_landscaping.vat_rate
            + self.digitalization.amount * self.digitalization.vat_rate
        )

    @property
    def annual_depreciation(self) -> float:
        """Total annual accounting depreciation under linear fiscal tables."""
        return (
            self.renovation.amount * self.renovation.depreciation_rate
            + self.biopool_landscaping.amount * self.biopool_landscaping.depreciation_rate
            + self.digitalization.amount * self.digitalization.depreciation_rate
        )


@dataclass(frozen=True)
class FinancingStructure:
    """
    Capital structure and liquidity backstops.
    Base loan sized at 70% of base CapEx (725.000 €), 30% Sponsor Equity.
    Working capital facilities: 50.000 € revolving credit line for VAT bridge.
    LEADER program subsidy: 163.000 € grant disbursed post-audit.
    """
    base_capex: float = 725_000.0
    debt_share: float = 0.70
    equity_share: float = 0.30
    credit_line_limit: float = 50_000.0
    credit_line_interest: float = 0.055  # 5.5% annual on drawn amount
    initial_credit_line_draw: float = 0.0  # Promoter case: 20,000 € opening draw
    leader_subsidy_amount: float = 163_000.0  # LEADER EU rural development grant
    leader_disbursement_month: int = 14  # Typical administrative review delay

    # Close-day funding requirements that the original model omitted.
    pre_opening_costs: float = 25_000.0      # Pre-opening staff, permits, launch marketing
    initial_working_capital: float = 20_000.0  # Opening inventory, deposits, utilities
    dsra_months: int = 6                     # Debt service reserve account (months)
    vat_bridge_limit: float = 153_090.0      # Dedicated VAT refund bridge facility
    vat_refund_month: int = 18               # Conservative AEAT refund timing (M18)

    # Senior Debt parameters (Mortgage loan)
    loan_tenure_years: int = 15
    loan_interest_rate: float = 0.035  # Euribor 12M + Spread baseline (3.50%)
    loan_payments_per_year: int = 12   # Monthly debt service

    # Underwriting covenants
    target_dscr: float = 1.25          # Minimum Debt Service Coverage Ratio
    critical_dscr: float = 1.00        # Default threshold

    @property
    def senior_debt_principal(self) -> float:
        return round(self.base_capex * self.debt_share, 2)  # 507.500 €

    @property
    def sponsor_equity(self) -> float:
        return round(self.base_capex * self.equity_share, 2)  # 217.500 €


@dataclass(frozen=True)
class EmployeeRole:
    """
    Employee compensation under the Segovia Provincial Hospitality Agreement.
    BOCyL - Convenio Colectivo Provincial de Hostelería de Segovia.

    The original university report (Trabajo Control Presupuestario) documents
    part-time contracts adapted to production: two cooks share ~1,900 hours
    and the housekeeper works 1,792 hours. The annual gross amounts below are
    therefore *part-time* annual costs, not full-time convenio salaries. The
    model records the hours and FTE equivalent explicitly so that the hourly
    cost can be audited against the SMI and the convenio tables.
    """
    title: str
    group: str
    headcount: int
    base_gross_annual: float
    annual_hours: float = 1_764.0  # Full-time equivalent hours (1,764 h/year)
    employer_social_security_rate: float = 0.35  # 35.0% SS Patronal

    @property
    def annual_employer_cost_per_employee(self) -> float:
        return self.base_gross_annual * (1.0 + self.employer_social_security_rate)

    @property
    def total_annual_cost(self) -> float:
        return self.headcount * self.annual_employer_cost_per_employee

    @property
    def fte(self) -> float:
        """Full-time equivalent of the contracted hours (1,764 h/year)."""
        return self.annual_hours / 1_764.0

    @property
    def hourly_gross_cost(self) -> float:
        return self.base_gross_annual / self.annual_hours if self.annual_hours > 0 else 0.0

    @property
    def hourly_employer_cost(self) -> float:
        return self.annual_employer_cost_per_employee / self.annual_hours if self.annual_hours > 0 else 0.0


# Statutory reference values (2026).
SMI_2026_ANNUAL: float = 17_094.0          # 14 payments x 1,221 € (RD 126/2026)
SMI_2026_HOURLY: float = 9.69               # 17,094 / 1,764 h
CONVENIO_SEGOVIA_2026_HOURLY: Dict[str, float] = {
    "Jefe de Cocina": 19_641.89 / 1_764.0,   # 11.13 €/h
    "Cocinero": 17_844.16 / 1_764.0,         # 10.12 €/h
    "Camarero": 17_844.16 / 1_764.0,         # 10.12 €/h
    "Auxiliar de pisos": 15_916.22 / 1_764.0,  # 9.02 €/h
    "Recepcionista": 18_713.66 / 1_764.0,    # 10.61 €/h
}


@dataclass(frozen=True)
class LaborStructure:
    """Labor structure aligned with the original part-time contract design."""
    roles: List[EmployeeRole] = field(
        default_factory=lambda: [
            EmployeeRole(
                title="Cocinera 1 (Jefa de Cocina)",
                group="Grupo II - Producción Hostelería",
                headcount=1,
                base_gross_annual=13_500.0,
                annual_hours=950.0,
                employer_social_security_rate=0.35,
            ),
            EmployeeRole(
                title="Cocinera 2 (Apoyo Cocina y Sala)",
                group="Grupo II - Apoyo Sala y Eventos",
                headcount=1,
                base_gross_annual=13_500.0,
                annual_hours=950.0,
                employer_social_security_rate=0.35,
            ),
            EmployeeRole(
                title="Personal de Limpieza y Mantenimiento",
                group="Grupo III - Mantenimiento e Higiene",
                headcount=1,
                base_gross_annual=17_500.0,
                annual_hours=1_792.0,
                employer_social_security_rate=0.35,
            ),
        ]
    )

    @property
    def total_annual_payroll(self) -> float:
        """Total annual labor expense including employer social security (60.075 €)."""
        return sum(role.total_annual_cost for role in self.roles)

    @property
    def total_fte(self) -> float:
        """Total full-time equivalent headcount (2.09 FTE, not 3 FTE)."""
        return sum(role.headcount * role.fte for role in self.roles)

    @property
    def total_hours(self) -> float:
        return sum(role.headcount * role.annual_hours for role in self.roles)

    @property
    def hourly_compliance(self) -> List[Dict[str, float]]:
        """Per-role hourly cost vs. SMI and convenio reference rates."""
        result = []
        for role in self.roles:
            convenio_key = (
                "Jefe de Cocina" if "Jefa" in role.title
                else "Cocinero" if "Cocina" in role.title
                else "Auxiliar de pisos"
            )
            reference = CONVENIO_SEGOVIA_2026_HOURLY.get(convenio_key, SMI_2026_HOURLY)
            result.append({
                "role": role.title,
                "annual_hours": role.annual_hours,
                "fte": role.fte,
                "hourly_gross": round(role.hourly_gross_cost, 2),
                "hourly_employer": round(role.hourly_employer_cost, 2),
                "smi_hourly": SMI_2026_HOURLY,
                "convenio_hourly": round(reference, 2),
                "compliant_smi": role.hourly_gross_cost >= SMI_2026_HOURLY,
                "compliant_convenio": role.hourly_gross_cost >= reference,
            })
        return result


@dataclass(frozen=True)
class FixedOpexStructure:
    """Fixed non-payroll operational overhead (excl. VAT)."""
    maintenance: float = 3_600.0   # Biopool specialist, pruning, HVAC
    insurance: float = 1_200.0     # All-risk rural hotel comprehensive policy
    utilities: float = 3_659.0     # Water, grid electricity, biomass pellets
    marketing_seo: float = 2_500.0 # OTA commissions optimization, local SEO, website
    pms_software: float = 1_200.0  # Cloud PMS, smart lock API, channel manager
    purchases: float = 0.0         # Original promoter case: F&B purchases booked as opex

    @property
    def total_fixed_opex(self) -> float:
        return (
            self.maintenance
            + self.insurance
            + self.utilities
            + self.marketing_seo
            + self.pms_software
            + self.purchases
        )


@dataclass(frozen=True)
class RevenueModelConfig:
    """
    Inventory, room counts, pricing assumptions, and launch penetration schedule.
    Units:
    - 7 Double Rooms (boutique rural hotel)
    - 1 Full Rural House (Casa Rural completa, 10-12 pax capacity)
    - Restaurant: 25 € average spend per diner, 30% Cost of Goods Sold (COGS).
    
    Launch Penetration Strategy (Market Penetration Index - MPI):
    - Year 1: Introductory pricing (85% of standard ADR) and promotional ramp-up
      (60% of market occupancy, ~18.8% real occupancy / ~68.7 days, matching the 
      original Excel's conservative 66.3 days / 18.2%).
    - Year 2: Stabilization (95% ADR, 85% market occupancy, ~26.7%).
    - Year 3+: Mature asset at full market potential (100% ADR, 100% INE benchmark occupancy).
    """
    double_rooms_count: int = 7
    double_room_adr: float = 85.0   # Mature average daily rate per room (net of VAT)
    full_house_count: int = 1
    full_house_adr: float = 380.0   # Mature average daily rate full house (net of VAT)

    restaurant_average_ticket: float = 25.0
    restaurant_cogs_ratio: float = 0.30  # 30% food & beverage margin cost
    restaurant_diners_per_double_room: float = 2.0  # 2 diners per occupied room-night
    restaurant_diners_per_full_house: float = 7.0   # 7 diners per occupied house-night

    hospitality_vat_rate: float = 0.10  # 10% statutory rate (Ley 37/1992 art. 91.Uno.2.2º)

    # Realistic ramp-up parameters
    mpi_year_1: float = 0.60        # 60% of mature market occupancy in Year 1
    adr_factor_year_1: float = 0.85 # 15% promotional launch discount on rack rates
    mpi_year_2: float = 0.85        # 85% of mature market occupancy in Year 2
    adr_factor_year_2: float = 0.95 # 5% promotional discount in Year 2
    mpi_year_3: float = 1.00        # 100% mature market occupancy
    adr_factor_year_3: float = 1.00 # 100% mature rack rate

    # Case selector:
    # - "ine_market" / "management": current Python base (31.36% mature occupancy,
    #   one on-site meal per guest per day, €25 ticket). This is an UPSIDE case.
    # - "market": INE Segovia 2025 (21.24%) with the original unit economics
    #   (€85 room, €380 house, €20 ticket, 859 meals at 19.2% scaled to 21.24%).
    # - "promoter": exact original university simulator (491 rooms, 72 house,
    #   859 meals, €85/€380/€20, +25% Y2, +20% Y3).
    calibration_mode: str = "ine_market"

    # Original promoter simulator (La_Dehesa_de_Castrillo.xlsx, "Plan y Simulador Completo")
    promoter_room_nights_y1: int = 491
    promoter_house_nights_y1: int = 72
    promoter_meals_y1: int = 859
    promoter_room_adr: float = 85.0
    promoter_house_adr: float = 380.0
    promoter_restaurant_ticket: float = 20.0
    promoter_growth_y2: float = 1.25
    promoter_growth_y3: float = 1.20

    # INE market case: original unit economics scaled from 19.2% to 21.24%.
    market_room_nights_y1: int = 543
    market_house_nights_y1: int = 80
    market_meals_y1: int = 950
    market_room_adr: float = 85.0
    market_house_adr: float = 380.0
    market_restaurant_ticket: float = 20.0
    market_growth_y2: float = 1.25
    market_growth_y3: float = 1.20


@dataclass(frozen=True)
class TaxPolicyConfig:
    """Fiscal and tax framework."""
    corporate_income_tax_rate: float = 0.25  # 25% general corporate rate
    vat_hospitality_rate: float = 0.10       # 10% on room lodging and restaurant
    vat_general_rate: float = 0.21           # 21% on CapEx, repairs, energy, services
    bin_carryforward_limit: float = 1.0      # 100% deduction of tax loss carryforwards for SMEs up to 1M€


@dataclass(frozen=True)
class ScenarioDrivers:
    """Multipliers applied to baseline for scenario stress-testing."""
    name: str
    occupancy_multiplier: float
    adr_multiplier: float
    opex_multiplier: float
    interest_rate_delta: float  # Basis points or percentage points added to benchmark


SCENARIOS: Dict[str, ScenarioDrivers] = {
    "conservative": ScenarioDrivers(
        name="Conservador (Stress-Test)",
        occupancy_multiplier=0.85,
        adr_multiplier=0.95,
        opex_multiplier=1.10,
        interest_rate_delta=0.015,  # +150 bps interest rate hike
    ),
    "base": ScenarioDrivers(
        name="Caso Base (INE Calibrado)",
        occupancy_multiplier=1.00,
        adr_multiplier=1.00,
        opex_multiplier=1.00,
        interest_rate_delta=0.00,
    ),
    "optimistic": ScenarioDrivers(
        name="Optimista (Consolidación)",
        occupancy_multiplier=1.20,
        adr_multiplier=1.10,
        opex_multiplier=0.98,
        interest_rate_delta=-0.005,  # -50 bps rate relief
    ),
}
