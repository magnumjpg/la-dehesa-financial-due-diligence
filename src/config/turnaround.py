"""
T8 - "Cabin Turnaround" configuration for La Dehesa del Castrillo.

This is the Act 4 / Act 5 layer of the case: the promoter's original 8-room
hotel with a 21-cover restaurant is replaced by six modular Nordic cabins plus
the stone caseron converted into a single four-bedroom lodge. The commercial
restaurant disappears; breakfast is a basket, dinner is a partnership with
local asadores, and the payroll falls from 2.9 FTE (two part-time cooks and a
housekeeper) to 2.0 FTE with no kitchen brigade.

Design rules
------------
* Every number used by the model lives here, in one frozen dataclass tree.
  The engine never hard-codes a T8 assumption.
* `build_capex()` maps the T8 budget onto the shared `CapExStructure` so the
  3-statement engine, the balance sheet and the tax depreciation tables are
  exactly the same code paths as the audited case.
* The land stays in the perimeter at its EUR 250,000 opportunity value. The
  headline cash-on-cash return is therefore reported on cash equity, and the
  all-in return adds the land back (see `TurnaroundEngine.returns`).

Capital budget (net of VAT)
---------------------------
    Cabins 6 x 60,000                        360,000
    Natural pond / biopool                    40,000
    Common infrastructure                     70,000
    Caseron light refresh (lodge)             60,000
    FF&E (cabins + lodge)                     20,000
    Digital, PMS and locks                    10,000
    -------------------------------------------------
    Works                                    560,000
    Technical fees (6%)                       33,600
    Contingency (5%)                          28,000
    -------------------------------------------------
    Cash CapEx                               621,600
    Land in kind (opportunity value)         250,000
    -------------------------------------------------
    All-in CapEx                             871,600

The EUR 60,000 module price is the shell; the installed cost per cabin net of
land and the caseron refresh is EUR 93,600 ((621,600 - 60,000) / 6), which is
the number that reconciles with the EUR 85,000-110,000 installed band in
BENCHMARKS_R7_ES.md.
"""

from dataclasses import asdict, dataclass, replace
from typing import Any, Dict, Optional, Tuple

from src.config.assumptions import (
    ZERO_ASSET,
    CapExAsset,
    CapExStructure,
    EmployeeRole,
    FinancingStructure,
    FixedOpexStructure,
    LaborStructure,
)

YEARS = 5


def _ramp(values: Tuple[float, ...], year: int) -> float:
    """Returns the value for `year` (1-based), holding the last one flat."""
    if not values:
        raise ValueError("An occupancy/experience ramp cannot be empty")
    return float(values[min(max(year, 1), len(values)) - 1])


@dataclass(frozen=True)
class CabinProduct:
    """Six modular cabins: 2 bedrooms, 4 guests, 35-45 m2."""

    count: int = 6
    area_m2: float = 40.0
    bedrooms: int = 2
    max_guests: int = 4
    guests_per_occupied_night: float = 2.4
    adr: float = 210.0
    unit_cost: float = 60_000.0
    occupancy: Tuple[float, ...] = (0.50, 0.56, 0.58, 0.58, 0.58)
    housekeeping_per_night: float = 25.0
    energy_per_night: float = 8.0
    consumables_per_night: float = 5.0

    def occupancy_for_year(self, year: int) -> float:
        return _ramp(self.occupancy, year)

    @property
    def total_cost(self) -> float:
        return round(self.count * self.unit_cost, 2)

    @property
    def available_nights(self) -> float:
        return float(self.count * 365)


@dataclass(frozen=True)
class LodgeProduct:
    """The 550 m2 stone caseron, converted into one four-bedroom lodge."""

    enabled: bool = True
    bedrooms: int = 4
    max_guests: int = 8
    guests_per_occupied_night: float = 8.0
    adr: float = 420.0
    occupancy: Tuple[float, ...] = (0.32, 0.38, 0.40, 0.40, 0.40)
    housekeeping_per_night: float = 45.0
    energy_per_night: float = 15.0
    consumables_per_night: float = 10.0

    def occupancy_for_year(self, year: int) -> float:
        return _ramp(self.occupancy, year) if self.enabled else 0.0

    @property
    def available_nights(self) -> float:
        return 365.0 if self.enabled else 0.0


@dataclass(frozen=True)
class TurnaroundCapEx:
    """T8 capital budget, net of VAT."""

    land: float = 250_000.0
    cabins: float = 360_000.0
    biopool: float = 40_000.0
    infrastructure: float = 70_000.0
    caseron_refresh: float = 60_000.0
    ffe: float = 20_000.0
    digital: float = 10_000.0
    fees_rate: float = 0.06
    contingency_rate: float = 0.05

    @property
    def works(self) -> float:
        return round(
            self.cabins
            + self.biopool
            + self.infrastructure
            + self.caseron_refresh
            + self.ffe
            + self.digital,
            2,
        )

    @property
    def fees(self) -> float:
        return round(self.works * self.fees_rate, 2)

    @property
    def contingency(self) -> float:
        return round(self.works * self.contingency_rate, 2)

    @property
    def cash_capex(self) -> float:
        return round(self.works + self.fees + self.contingency, 2)

    @property
    def total_capex(self) -> float:
        return round(self.cash_capex + self.land, 2)

    @property
    def input_vat(self) -> float:
        return round(self.cash_capex * 0.21, 2)

    @property
    def installed_cost_per_cabin(self) -> float:
        """Cash CapEx net of the caseron refresh, per cabin."""
        return round((self.cash_capex - self.caseron_refresh) / 6.0, 2)

    def build_capex(self) -> CapExStructure:
        """Maps the T8 budget onto the shared CapExStructure.

        Depreciation follows the same fiscal tables as the audited case:
        3% for the modular units and the caseron works, 10% for the pond,
        infrastructure and FF&E, 25% for software and digital hardware.
        """
        return CapExStructure(
            land=CapExAsset(
                name="Terreno (25 ha, aportado en especie)",
                amount=self.land,
                vat_rate=0.21,
                depreciation_rate=0.0,
                is_depreciable=False,
            ),
            renovation=CapExAsset(
                name="Reforma ligera del caseron (lodge 4 habitaciones)",
                amount=self.caseron_refresh,
                vat_rate=0.21,
                depreciation_rate=0.03,
                is_depreciable=True,
            ),
            cabins=CapExAsset(
                name="6 cabanas modulares nordicas (2 hab., 40 m2)",
                amount=self.cabins,
                vat_rate=0.21,
                depreciation_rate=0.03,
                is_depreciable=True,
            ),
            kitchen_equipment=ZERO_ASSET,
            ffe=CapExAsset(
                name="FF&E cabanas y lodge",
                amount=self.ffe,
                vat_rate=0.21,
                depreciation_rate=0.10,
                is_depreciable=True,
            ),
            biopool_landscaping=CapExAsset(
                name="Estanque natural / biopiscina y paisajismo",
                amount=self.biopool,
                vat_rate=0.21,
                depreciation_rate=0.10,
                is_depreciable=True,
            ),
            infrastructure=CapExAsset(
                name="Infraestructura comun (accesos, agua, solar, saneamiento)",
                amount=self.infrastructure,
                vat_rate=0.21,
                depreciation_rate=0.10,
                is_depreciable=True,
            ),
            digitalization=CapExAsset(
                name="Digitalizacion, PMS y cerraduras",
                amount=self.digital,
                vat_rate=0.21,
                depreciation_rate=0.25,
                is_depreciable=True,
            ),
            professional_fees=CapExAsset(
                name="Honorarios tecnicos, licencias y direccion de obra (6%)",
                amount=self.fees,
                vat_rate=0.21,
                depreciation_rate=0.03,
                is_depreciable=True,
            ),
            contingency=CapExAsset(
                name="Contingencia de obra (5%)",
                amount=self.contingency,
                vat_rate=0.21,
                depreciation_rate=0.03,
                is_depreciable=True,
            ),
        )


@dataclass(frozen=True)
class TurnaroundFinancing:
    """EUR 450k senior facility, 4.25% fixed, 20 years, 12+12 months."""

    debt: float = 450_000.0
    rate: float = 0.0425
    tenure_years: int = 20
    construction_months: int = 12
    grace_months: int = 12
    target_dscr: float = 1.25
    pre_opening_costs: float = 25_000.0
    initial_working_capital: float = 15_000.0
    minimum_cash_balance: float = 15_000.0
    dsra_months: int = 6
    arrangement_fee_rate: float = 0.01
    credit_line_interest: float = 0.055
    vat_bridge_limit: float = 150_000.0
    vat_refund_month: int = 18

    def build_financing(self, all_in_capex: float, land: float) -> FinancingStructure:
        """Returns the shared FinancingStructure calibrated to T8.

        `debt_share` is expressed on the all-in CapEx (land included) so the
        engine's `senior_debt_principal` property reproduces exactly EUR
        450,000. The 30% base equity is deliberately set below the plug: the
        model reports the equity actually required, not a 30% target.
        """
        return FinancingStructure(
            base_capex=all_in_capex,
            debt_share=self.debt / all_in_capex,
            equity_share=0.25,
            land_in_kind=True,
            credit_line_limit=self.vat_bridge_limit,
            credit_line_interest=self.credit_line_interest,
            initial_credit_line_draw=0.0,
            leader_subsidy_amount=0.0,
            leader_disbursement_month=14,
            leader_disbursement_year=2,
            pre_opening_costs=self.pre_opening_costs,
            initial_working_capital=self.initial_working_capital,
            minimum_cash_balance=self.minimum_cash_balance,
            dsra_months=self.dsra_months,
            vat_bridge_limit=self.vat_bridge_limit,
            vat_refund_month=self.vat_refund_month,
            construction_months=self.construction_months,
            grace_months=self.grace_months,
            loan_tenure_years=self.tenure_years,
            loan_interest_rate=self.rate,
            target_dscr=self.target_dscr,
            arrangement_fee_rate=self.arrangement_fee_rate,
        )


@dataclass(frozen=True)
class TurnaroundOpex:
    """Lean operating structure: 2 FTE, no commercial kitchen."""

    fte: float = 2.0
    gross_per_fte: float = 23_000.0
    social_security_rate: float = 0.325
    fixed_opex: float = 37_000.0
    ffe_reserve_rate: float = 0.035
    ota_share: float = 0.55
    ota_commission_rate: float = 0.15
    payment_fee_rate: float = 0.015
    breakfast_per_guest_day: float = 12.0
    experiences_revenue: Tuple[float, ...] = (25_000, 30_000, 30_000, 30_000, 30_000)
    experience_margin: float = 0.72

    @property
    def loaded_cost_per_fte(self) -> float:
        return round(self.gross_per_fte * (1.0 + self.social_security_rate), 2)

    @property
    def annual_payroll(self) -> float:
        return round(self.fte * self.loaded_cost_per_fte, 2)

    def experiences_for_year(self, year: int) -> float:
        return _ramp(self.experiences_revenue, year)

    def build_labor(self) -> LaborStructure:
        """Two full-time roles at EUR 23,000 gross plus 32.5% employer SS."""
        return LaborStructure(
            roles=[
                EmployeeRole(
                    title="Guest experience & revenue manager",
                    group="Grupo I - Recepcion y gestion",
                    headcount=1,
                    base_gross_annual=self.gross_per_fte,
                    annual_hours=1_764.0,
                    employer_social_security_rate=self.social_security_rate,
                ),
                EmployeeRole(
                    title="Housekeeping & maintenance",
                    group="Grupo III - Mantenimiento e higiene",
                    headcount=1,
                    base_gross_annual=self.gross_per_fte,
                    annual_hours=1_764.0,
                    employer_social_security_rate=self.social_security_rate,
                ),
            ]
        )

    def build_opex(self) -> FixedOpexStructure:
        """EUR 37,000 fixed overhead, reconciled line by line."""
        return FixedOpexStructure(
            maintenance=9_000.0,
            insurance=3_500.0,
            utilities=8_000.0,
            marketing_seo=5_500.0,
            pms_software=3_000.0,
            admin_accounting=4_000.0,
            property_tax_waste=2_500.0,
            other=1_500.0,
            purchases=0.0,
        )


@dataclass(frozen=True)
class TurnaroundConfig:
    """Full T8 configuration: product, CapEx, financing, operations, exit."""

    name: str = "T8"
    cabins: CabinProduct = CabinProduct()
    lodge: LodgeProduct = LodgeProduct()
    capex: TurnaroundCapEx = TurnaroundCapEx()
    financing: TurnaroundFinancing = TurnaroundFinancing()
    opex: TurnaroundOpex = TurnaroundOpex()
    exit_cap_rate: float = 0.085
    exit_cost_rate: float = 0.03
    discount_rate: float = 0.09

    def __post_init__(self) -> None:
        if self.cabins.count < 1:
            raise ValueError("T8 requires at least one cabin")
        if self.cabins.adr <= 0 or (self.lodge.enabled and self.lodge.adr <= 0):
            raise ValueError("ADR must be positive")
        for label, ramp in (
            ("cabins", self.cabins.occupancy),
            ("lodge", self.lodge.occupancy),
        ):
            if any(o < 0 or o > 1 for o in ramp):
                raise ValueError(f"{label} occupancy must be within [0, 1]")

    @classmethod
    def base(cls) -> "TurnaroundConfig":
        return cls()

    @classmethod
    def cabins_only(cls) -> "TurnaroundConfig":
        """Sensitivity: drop the caseron lodge and its refresh budget."""
        base = cls()
        return replace(
            base,
            name="T8 cabins-only",
            lodge=replace(base.lodge, enabled=False),
            capex=replace(base.capex, caseron_refresh=0.0),
        )

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    @property
    def keys(self) -> int:
        return self.cabins.count + (1 if self.lodge.enabled else 0)

    @property
    def guests_at_full_occupancy(self) -> int:
        return (
            self.cabins.count * self.cabins.max_guests
            + (self.lodge.max_guests if self.lodge.enabled else 0)
        )

    @property
    def all_in_capex(self) -> float:
        return self.capex.total_capex

    @property
    def cash_capex(self) -> float:
        return self.capex.cash_capex

    def build_capex(self) -> CapExStructure:
        return self.capex.build_capex()

    def build_financing(self) -> FinancingStructure:
        return self.financing.build_financing(
            all_in_capex=self.capex.total_capex,
            land=self.capex.land,
        )

    def build_labor(self) -> LaborStructure:
        return self.opex.build_labor()

    def build_opex(self) -> FixedOpexStructure:
        return self.opex.build_opex()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["summary"] = {
            "keys": self.keys,
            "guests_at_full_occupancy": self.guests_at_full_occupancy,
            "works": self.capex.works,
            "fees": self.capex.fees,
            "contingency": self.capex.contingency,
            "cash_capex": self.capex.cash_capex,
            "land_in_kind": self.capex.land,
            "all_in_capex": self.capex.total_capex,
            "input_vat": self.capex.input_vat,
            "installed_cost_per_cabin": self.capex.installed_cost_per_cabin,
            "annual_payroll": self.opex.annual_payroll,
            "senior_debt": self.financing.debt,
            "debt_to_cash_capex_pct": round(
                self.financing.debt / self.capex.cash_capex * 100.0, 2
            ),
            "debt_to_all_in_capex_pct": round(
                self.financing.debt / self.capex.total_capex * 100.0, 2
            ),
        }
        return data


# Convenience: the three T8 variants used by the Act 5 sensitivity grid.
def adr_variant(delta: float) -> TurnaroundConfig:
    base = TurnaroundConfig.base()
    return replace(
        base,
        name=f"T8 ADR {delta:+.0%}",
        cabins=replace(base.cabins, adr=round(base.cabins.adr * (1 + delta), 2)),
        lodge=replace(base.lodge, adr=round(base.lodge.adr * (1 + delta), 2)),
    )


def occupancy_variant(mature: float) -> TurnaroundConfig:
    base = TurnaroundConfig.base()
    cabins = tuple(
        round(min(1.0, o * mature / base.cabins.occupancy[-1]), 4)
        for o in base.cabins.occupancy
    )
    lodge = tuple(
        round(min(1.0, o * mature / base.lodge.occupancy[-1]), 4)
        for o in base.lodge.occupancy
    )
    return replace(
        base,
        name=f"T8 occupancy {mature:.0%}",
        cabins=replace(base.cabins, occupancy=cabins),
        lodge=replace(base.lodge, occupancy=lodge),
    )


def debt_variant(amount: float) -> TurnaroundConfig:
    base = TurnaroundConfig.base()
    return replace(
        base,
        name=f"T8 debt {amount / 1000:.0f}k",
        financing=replace(base.financing, debt=float(amount)),
    )


def with_exit_cap(cap: float) -> TurnaroundConfig:
    return replace(TurnaroundConfig.base(), exit_cap_rate=float(cap))


__all__ = [
    "CabinProduct",
    "LodgeProduct",
    "TurnaroundCapEx",
    "TurnaroundConfig",
    "TurnaroundFinancing",
    "TurnaroundOpex",
    "adr_variant",
    "debt_variant",
    "occupancy_variant",
    "with_exit_cap",
]
