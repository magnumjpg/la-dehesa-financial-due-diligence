"""
Financial and operational assumptions for La Dehesa del Castrillo S.L.

This module formalizes institutional parameters for:
1. CapEx breakdown (depreciable vs. non-depreciable asset bases).
2. Capital structure (senior debt, sponsor equity, VAT bridge, LEADER grant).
3. Labour cost schedules under the Segovia Provincial Hospitality Agreement.
4. Operational inventory, pricing, and the full USALI-style cost stack
   (F&B COGS, OTA commissions, guest amenities, breakfast, FF&E reserve).
5. Tax regimes: VAT (10% hospitality vs 21% CapEx/OPEX) and Corporate Income
   Tax (25%).
6. Debt sizing and covenant constraints (French amortization with a
   construction/grace period, minimum DSCR).

The management and market cases use the realistic 2026 cost structure. The
promoter case keeps the original simulator's demand drivers and financing
structure, but it is a re-modelling calibrated to the presentation's headline
figures, not a replication of either source workbook: the workbooks disagree
with each other on Year-1 revenue and the EUR 11,297 EBITDA has no build-up.
README section 2 reconciles the four revenue figures and the two EBITDA
figures the source contains.
"""

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CapExAsset:
    """Individual CapEx asset item with depreciation and VAT classification."""
    name: str
    amount: float
    vat_rate: float
    depreciation_rate: float  # Annual tax-deductible depreciation rate (Ley 27/2014)
    is_depreciable: bool


ZERO_ASSET = CapExAsset(
    name="",
    amount=0.0,
    vat_rate=0.21,
    depreciation_rate=0.0,
    is_depreciable=False,
)


@dataclass(frozen=True)
class CapExStructure:
    """
    Project CapEx structure.

    The realistic budget is based on a 550 m2 refurbishment at EUR 1,000/m2
    (mid-range for a structural reform in rural Castilla y Leon, excluding
    luxury finishes), plus a commercial kitchen, FF&E, the biopool, digital
    infrastructure, professional fees (6% of works) and a 5% contingency.

    Land is non-depreciable and, in the management/market cases, is contributed
    in kind by the sponsor. The promoter case uses the original EUR 725k budget
    and purchases the land, which is the financing structure the original
    university Excel assumed.
    """
    land: CapExAsset = CapExAsset(
        name="Terreno (25 ha en Segovia)",
        amount=250_000.0,
        vat_rate=0.21,
        depreciation_rate=0.0,
        is_depreciable=False,
    )
    renovation: CapExAsset = CapExAsset(
        name="Reforma Integral (550 m2 a 1.000 EUR/m2)",
        amount=550_000.0,
        vat_rate=0.21,
        depreciation_rate=0.03,  # 3% annual (edificaciones hoteleras)
        is_depreciable=True,
    )
    kitchen_equipment: CapExAsset = CapExAsset(
        name="Equipamiento de cocina y lavanderia",
        amount=55_000.0,
        vat_rate=0.21,
        depreciation_rate=0.12,  # 12% annual (maquinaria hosteleria)
        is_depreciable=True,
    )
    ffe: CapExAsset = CapExAsset(
        name="Mobiliario, textiles y equipamiento de habitaciones",
        amount=65_000.0,
        vat_rate=0.21,
        depreciation_rate=0.10,  # 10% annual (mobiliario)
        is_depreciable=True,
    )
    biopool_landscaping: CapExAsset = CapExAsset(
        name="Biopiscina y Paisajismo",
        amount=40_000.0,
        vat_rate=0.21,
        depreciation_rate=0.10,  # 10% annual (instalaciones exteriores)
        is_depreciable=True,
    )
    digitalization: CapExAsset = CapExAsset(
        name="Digitalizacion, PMS y cerraduras",
        amount=12_000.0,
        vat_rate=0.21,
        depreciation_rate=0.25,  # 25% annual (software y hardware)
        is_depreciable=True,
    )
    professional_fees: CapExAsset = CapExAsset(
        name="Honorarios tecnicos, licencias y direccion de obra (6%)",
        amount=42_600.0,
        vat_rate=0.21,
        depreciation_rate=0.03,
        is_depreciable=True,
    )
    contingency: CapExAsset = CapExAsset(
        name="Contingencia de obra (5%)",
        amount=35_500.0,
        vat_rate=0.21,
        depreciation_rate=0.03,
        is_depreciable=True,
    )

    @property
    def total_base_capex(self) -> float:
        """Land + hard construction + biopool (EUR 840,000 in the realistic budget)."""
        return self.land.amount + self.renovation.amount + self.biopool_landscaping.amount

    @property
    def total_capex(self) -> float:
        """Total initial asset cost, net of VAT (EUR 1,050,100 realistic budget)."""
        return (
            self.land.amount
            + self.renovation.amount
            + self.kitchen_equipment.amount
            + self.ffe.amount
            + self.biopool_landscaping.amount
            + self.digitalization.amount
            + self.professional_fees.amount
            + self.contingency.amount
        )

    @property
    def total_cash_capex(self) -> float:
        """Cash paid to contractors/sellers if land is purchased (all assets)."""
        return self.total_capex

    @property
    def total_input_vat(self) -> float:
        """Deductible input VAT at 21%.

        Spanish rural land is frequently VAT-exempt or bought from an individual
        (no recoverable VAT). The model therefore does not claim recoverable VAT
        on the land; it applies 21% only to construction, equipment, fees and
        contingency. This is deliberately conservative.
        """
        return round(
            (self.total_capex - self.land.amount) * 0.21,
            2,
        )

    @property
    def annual_depreciation(self) -> float:
        """Total annual accounting depreciation under linear fiscal tables."""
        return round(
            sum(
                asset.amount * asset.depreciation_rate
                for asset in (
                    self.renovation,
                    self.kitchen_equipment,
                    self.ffe,
                    self.biopool_landscaping,
                    self.digitalization,
                    self.professional_fees,
                    self.contingency,
                )
                if asset.is_depreciable
            ),
            2,
        )

    @classmethod
    def original_promoter(cls) -> "CapExStructure":
        """The original EUR 725k budget: land 250k + works 440k + biopool 35k."""
        return cls(
            renovation=CapExAsset(
                name="Reforma Integral (550 m2 civil works)",
                amount=440_000.0,
                vat_rate=0.21,
                depreciation_rate=0.03,
                is_depreciable=True,
            ),
            biopool_landscaping=CapExAsset(
                name="Biopiscina y Paisajismo",
                amount=35_000.0,
                vat_rate=0.21,
                depreciation_rate=0.13,
                is_depreciable=True,
            ),
            digitalization=CapExAsset(
                name="Digitalizacion y PMS (Kit Digital)",
                amount=0.0,
                vat_rate=0.21,
                depreciation_rate=0.25,
                is_depreciable=True,
            ),
            kitchen_equipment=ZERO_ASSET,
            ffe=ZERO_ASSET,
            professional_fees=ZERO_ASSET,
            contingency=ZERO_ASSET,
        )


@dataclass(frozen=True)
class FinancingStructure:
    """
    Capital structure and liquidity backstops.

    The original 70% LTV / 15-year structure is not supportable once the full
    operating cost stack is included. The realistic structure is 35% LTV,
    20-year amortization, 4.0% fixed, a 12-month construction period (interest
    capitalised as IDC) and a 12-month post-opening grace period. Land is
    contributed in kind, so the bank lends against the full asset value while
    the cash equity funds the works.

    The VAT bridge is a separate EUR 175k facility, sized on the gross input
    VAT. The EUR 50k revolving line in the original model was too small and has
    been replaced by an explicit bridge limit.
    """
    base_capex: float = 1_050_100.0
    debt_share: float = 0.35
    equity_share: float = 0.30
    land_in_kind: bool = True
    credit_line_limit: float = 175_000.0
    credit_line_interest: float = 0.055  # 5.5% annual on drawn bridge
    initial_credit_line_draw: float = 0.0
    leader_subsidy_amount: float = 163_000.0
    leader_disbursement_month: int = 14
    leader_disbursement_year: int = 2

    # Close-day funding requirements.
    pre_opening_costs: float = 35_000.0
    initial_working_capital: float = 25_000.0
    minimum_cash_balance: float = 15_000.0
    dsra_months: int = 6
    vat_bridge_limit: float = 175_000.0
    vat_refund_month: int = 18

    # Construction and senior debt.
    construction_months: int = 12          # interest during construction (IDC)
    grace_months: int = 12                 # interest-only after opening
    loan_tenure_years: int = 20
    loan_interest_rate: float = 0.04       # fixed 4.0% (2026 rural hotel terms)
    loan_payments_per_year: int = 12

    # Underwriting covenants.
    target_dscr: float = 1.25
    critical_dscr: float = 1.00

    @property
    def senior_debt_principal(self) -> float:
        """Senior debt sized on 35% of the realistic all-in asset cost."""
        return round(self.base_capex * self.debt_share, 2)

    @property
    def sponsor_equity(self) -> float:
        """Cash sponsor equity (30% of all-in asset cost)."""
        return round(self.base_capex * self.equity_share, 2)

    @property
    def land_in_kind_value(self) -> float:
        return 250_000.0 if self.land_in_kind else 0.0

    @property
    def idc_amount(self) -> float:
        """Interest during construction, paid at close and included in uses."""
        return round(
            self.senior_debt_principal
            * self.loan_interest_rate
            * self.construction_months
            / 12.0,
            2,
        )

    @property
    def total_equity_at_close(self) -> float:
        """Base (30%) cash equity plus the in-kind land contribution."""
        return round(self.sponsor_equity + self.land_in_kind_value, 2)


@dataclass(frozen=True)
class EmployeeRole:
    """
    Employee compensation under the Segovia Provincial Hospitality Agreement.
    BOCyL - Convenio Colectivo Provincial de Hosteleria de Segovia.

    The original university report documents part-time contracts adapted to
    production: two cooks share ~1,900 hours and the housekeeper works 1,792
    hours. The annual gross amounts below are therefore *part-time* annual
    costs, not full-time convenio salaries. The model records the hours and
    FTE equivalent explicitly so that the hourly cost can be audited against
    the SMI and the convenio tables.
    """
    title: str
    group: str
    headcount: int
    base_gross_annual: float
    annual_hours: float = 1_764.0
    employer_social_security_rate: float = 0.35

    @property
    def annual_employer_cost_per_employee(self) -> float:
        return self.base_gross_annual * (1.0 + self.employer_social_security_rate)

    @property
    def total_annual_cost(self) -> float:
        return self.headcount * self.annual_employer_cost_per_employee

    @property
    def fte(self) -> float:
        return self.annual_hours / 1_764.0

    @property
    def hourly_gross_cost(self) -> float:
        return self.base_gross_annual / self.annual_hours if self.annual_hours > 0 else 0.0

    @property
    def hourly_employer_cost(self) -> float:
        return self.annual_employer_cost_per_employee / self.annual_hours if self.annual_hours > 0 else 0.0


# Statutory reference values (2026).
SMI_2026_ANNUAL: float = 17_094.0
SMI_2026_HOURLY: float = 9.69
CONVENIO_SEGOVIA_2026_HOURLY: Dict[str, float] = {
    "Jefe de Cocina": 19_641.89 / 1_764.0,
    "Cocinero": 17_844.16 / 1_764.0,
    "Camarero": 17_844.16 / 1_764.0,
    "Auxiliar de pisos": 15_916.22 / 1_764.0,
    "Recepcionista": 18_713.66 / 1_764.0,
}


@dataclass(frozen=True)
class LaborStructure:
    """Labour structure aligned with the original part-time contract design."""
    roles: List[EmployeeRole] = field(
        default_factory=lambda: [
            EmployeeRole(
                title="Cocinera 1 (Jefa de Cocina)",
                group="Grupo II - Produccion Hosteleria",
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
        """Total annual labour expense including employer social security (EUR 60,075)."""
        return sum(role.total_annual_cost for role in self.roles)

    @property
    def total_fte(self) -> float:
        return sum(role.headcount * role.fte for role in self.roles)

    @property
    def total_hours(self) -> float:
        return sum(role.headcount * role.annual_hours for role in self.roles)

    @property
    def hourly_compliance(self) -> List[Dict[str, float]]:
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
    """Fixed non-payroll operational overhead (excl. VAT).

    The original EUR 12,159 schedule was thin for a 550 m2 hotel with a
    restaurant, a biopool and 25 ha of grounds. The realistic schedule below
    totals EUR 30,500 and includes property tax, accounting/legal support,
    waste and a maintenance contract. The promoter case overrides it with the
    source's own four cost lines (maintenance, insurance, utilities and
    purchases), which with the realistic payroll produce the presentation's
    EUR 11,297 EBITDA.
    """
    maintenance: float = 6_000.0
    insurance: float = 2_500.0
    utilities: float = 9_000.0
    marketing_seo: float = 4_000.0
    pms_software: float = 2_000.0
    admin_accounting: float = 3_500.0
    property_tax_waste: float = 2_000.0
    other: float = 1_500.0
    purchases: float = 0.0  # Promoter case: F&B purchases booked as opex

    @property
    def total_fixed_opex(self) -> float:
        return round(
            self.maintenance
            + self.insurance
            + self.utilities
            + self.marketing_seo
            + self.pms_software
            + self.admin_accounting
            + self.property_tax_waste
            + self.other
            + self.purchases,
            2,
        )


@dataclass(frozen=True)
class RevenueModelConfig:
    """
    Inventory, pricing and the full variable-cost stack.

    - 7 double rooms and 1 full rural house.
    - Restaurant: one on-site meal per guest per day (21 covers at full
      occupancy), average ticket EUR 25 (management) / EUR 20 (market,
      promoter).
    - OTA channel: 60% of lodging sold through OTAs at 15% commission
      (9.0% blended on lodging revenue).
    - Amenities/housekeeping: EUR 35 per occupied day (whole property).
    - Breakfast: EUR 5 per guest per day (21 guests at full occupancy).
    - FF&E reserve: 3% of revenue, deducted from CFADS for DSCR and returns.
    """
    double_rooms_count: int = 7
    double_room_adr: float = 85.0
    full_house_count: int = 1
    full_house_adr: float = 380.0

    restaurant_average_ticket: float = 25.0
    restaurant_cogs_ratio: float = 0.30
    restaurant_diners_per_double_room: float = 2.0
    restaurant_diners_per_full_house: float = 7.0

    # Full cost stack.
    apply_full_cost_stack: bool = True
    ota_share: float = 0.60
    ota_commission_rate: float = 0.15
    amenities_per_occupied_day: float = 35.0
    breakfast_cost_per_guest_day: float = 5.0
    guests_per_double_room: float = 2.0
    guests_per_full_house: float = 7.0
    ffe_reserve_rate: float = 0.03

    hospitality_vat_rate: float = 0.10

    # Realistic ramp-up parameters.
    mpi_year_1: float = 0.60
    adr_factor_year_1: float = 0.85
    mpi_year_2: float = 0.85
    adr_factor_year_2: float = 0.95
    mpi_year_3: float = 1.00
    adr_factor_year_3: float = 1.00

    calibration_mode: str = "ine_market"

    # Promoter case: volumes and prices behind the presentation's EUR 86,275.
    # The source cell `Plan de Negocio!B19` prices the restaurant at EUR 25;
    # the EUR 20 ticket is the one that reproduces the deck's revenue, so the
    # purchases line below (EUR 6,444) is costed at a different ticket from
    # the revenue it supports. README section 2 documents the mismatch.
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
    corporate_income_tax_rate: float = 0.25
    vat_hospitality_rate: float = 0.10
    vat_general_rate: float = 0.21
    bin_carryforward_limit: float = 1.0


@dataclass(frozen=True)
class ScenarioDrivers:
    """Multipliers applied to baseline for scenario stress-testing."""
    name: str
    occupancy_multiplier: float
    adr_multiplier: float
    opex_multiplier: float
    interest_rate_delta: float


SCENARIOS: Dict[str, ScenarioDrivers] = {
    "conservative": ScenarioDrivers(
        name="Conservador (Stress-Test)",
        occupancy_multiplier=0.85,
        adr_multiplier=0.95,
        opex_multiplier=1.10,
        interest_rate_delta=0.015,
    ),
    "base": ScenarioDrivers(
        name="Caso Base (INE Calibrado)",
        occupancy_multiplier=1.00,
        adr_multiplier=1.00,
        opex_multiplier=1.00,
        interest_rate_delta=0.00,
    ),
    "optimistic": ScenarioDrivers(
        name="Optimista (Consolidacion)",
        occupancy_multiplier=1.20,
        adr_multiplier=1.10,
        opex_multiplier=0.98,
        interest_rate_delta=-0.005,
    ),
}
