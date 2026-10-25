"""
Reform / resize case configuration.

This is deliberately a *separate* layer from the three as-is cases. The base
model answers "what does the project look like as structured?"; this module
answers the follow-on question a credit committee actually asks after a
decline: "what would have to be true for a reform of the asset to create
value?"

The levers are explicit and auditable:

1. Capital / scope: renovation, kitchen, FF&E, biopool, digital, fees and
   contingency. Land is kept at its opportunity value (EUR 250k) so the
   analysis does not flatter the project by treating the site as free.
2. Revenue: external F&B covers per day, average ticket, external COGS,
   experiences, ADR uplift, cost savings and the incremental FTE needed to
   service the extra demand.
3. Financing: the same 35% LTV / 20-year / 4.0% senior structure, a
   LEADER grant scaled to the reform budget, the VAT bridge, pre-opening,
   working capital and the contractual DSRA.

The reform is *not* a goal-seek. The presets below are deliberately
conservative enough that one of them can still fail; the analysis is expected
to report a negative result where the economics do not close.
"""

from dataclasses import dataclass, replace
from typing import Dict, Tuple

from src.config.assumptions import CapExAsset, CapExStructure


@dataclass(frozen=True)
class ReformConfig:
    """A single, fully specified reform configuration."""

    name: str = "Reform case"
    thesis: str = ""

    # --- Capital / scope (net of VAT) ---------------------------------
    land_amount: float = 250_000.0
    renovation_amount: float = 550_000.0
    kitchen_amount: float = 55_000.0
    ffe_amount: float = 65_000.0
    biopool_amount: float = 40_000.0
    digital_amount: float = 12_000.0
    professional_fees_rate: float = 0.06
    contingency_rate: float = 0.05

    # --- Revenue levers ------------------------------------------------
    external_covers_per_day: float = 6.0
    external_ticket: float = 28.0
    external_cogs_ratio: float = 0.32
    external_ramp_year1: float = 0.70
    external_ramp_year2: float = 0.90

    experiences_revenue: float = 12_000.0
    experiences_ebitda_margin: float = 0.70
    experiences_ramp_year1: float = 0.70
    experiences_ramp_year2: float = 0.90

    adr_uplift: float = 0.05
    cost_savings: float = 5_000.0
    incremental_fte: float = 1.0
    loaded_cost_per_fte: float = 28_000.0

    # --- Financing / close-day costs ----------------------------------
    leader_subsidy_rate: float = 0.155
    leader_subsidy_cap: float = 163_000.0
    leader_disbursement_year: int = 2
    debt_share: float = 0.35
    loan_interest_rate: float = 0.04
    loan_tenure_years: int = 20
    construction_months: int = 12
    grace_months: int = 12
    pre_opening_costs: float = 35_000.0
    initial_working_capital: float = 25_000.0
    dsra_months: int = 6

    # --- Valuation -----------------------------------------------------
    exit_cap_rate: float = 0.085
    discount_rate: float = 0.08

    # ------------------------------------------------------------------
    # Capital-stack helpers
    # ------------------------------------------------------------------
    @property
    def works_base(self) -> float:
        """Works and equipment to which fees and contingency apply."""
        return (
            self.renovation_amount
            + self.kitchen_amount
            + self.ffe_amount
            + self.biopool_amount
        )

    @property
    def professional_fees(self) -> float:
        return round(self.works_base * self.professional_fees_rate, 2)

    @property
    def contingency(self) -> float:
        return round(self.works_base * self.contingency_rate, 2)

    @property
    def total_capex(self) -> float:
        return round(
            self.land_amount
            + self.renovation_amount
            + self.kitchen_amount
            + self.ffe_amount
            + self.biopool_amount
            + self.digital_amount
            + self.professional_fees
            + self.contingency,
            2,
        )

    @property
    def non_land_capex(self) -> float:
        return round(self.total_capex - self.land_amount, 2)

    @property
    def total_input_vat(self) -> float:
        return round(self.non_land_capex * 0.21, 2)

    @property
    def leader_subsidy(self) -> float:
        """LEADER grant, capped and scaled to the reform budget."""
        return round(
            min(self.leader_subsidy_cap, self.total_capex * self.leader_subsidy_rate),
            2,
        )

    @property
    def annual_depreciation(self) -> float:
        return round(
            self.renovation_amount * 0.03
            + self.kitchen_amount * 0.12
            + self.ffe_amount * 0.10
            + self.biopool_amount * 0.10
            + self.digital_amount * 0.25
            + self.professional_fees * 0.03
            + self.contingency * 0.03,
            2,
        )

    def build_capex(self) -> CapExStructure:
        """Converts the reform budget into the model's CapEx structure."""
        return CapExStructure(
            land=CapExAsset(
                name="Terreno (25 ha en Segovia)",
                amount=self.land_amount,
                vat_rate=0.21,
                depreciation_rate=0.0,
                is_depreciable=False,
            ),
            renovation=CapExAsset(
                name="Reforma Integral (alcance reformado)",
                amount=self.renovation_amount,
                vat_rate=0.21,
                depreciation_rate=0.03,
                is_depreciable=True,
            ),
            kitchen_equipment=CapExAsset(
                name="Equipamiento de cocina y lavanderia",
                amount=self.kitchen_amount,
                vat_rate=0.21,
                depreciation_rate=0.12,
                is_depreciable=True,
            ),
            ffe=CapExAsset(
                name="Mobiliario, textiles y equipamiento de habitaciones",
                amount=self.ffe_amount,
                vat_rate=0.21,
                depreciation_rate=0.10,
                is_depreciable=True,
            ),
            biopool_landscaping=CapExAsset(
                name="Biopiscina y Paisajismo",
                amount=self.biopool_amount,
                vat_rate=0.21,
                depreciation_rate=0.10,
                is_depreciable=True,
            ),
            digitalization=CapExAsset(
                name="Digitalizacion, PMS y cerraduras",
                amount=self.digital_amount,
                vat_rate=0.21,
                depreciation_rate=0.25,
                is_depreciable=True,
            ),
            professional_fees=CapExAsset(
                name="Honorarios tecnicos, licencias y direccion de obra",
                amount=self.professional_fees,
                vat_rate=0.21,
                depreciation_rate=0.03,
                is_depreciable=True,
            ),
            contingency=CapExAsset(
                name="Contingencia de obra",
                amount=self.contingency,
                vat_rate=0.21,
                depreciation_rate=0.03,
                is_depreciable=True,
            ),
        )

    def scale_non_land_capex(self, factor: float) -> "ReformConfig":
        """Scales the non-land budget, keeping the land at opportunity value."""
        return replace(
            self,
            renovation_amount=round(self.renovation_amount * factor, 2),
            kitchen_amount=round(self.kitchen_amount * factor, 2),
            ffe_amount=round(self.ffe_amount * factor, 2),
            biopool_amount=round(self.biopool_amount * factor, 2),
            digital_amount=round(self.digital_amount * factor, 2),
        )

    def with_total_capex(self, target_total_capex: float) -> "ReformConfig":
        """
        Returns a config whose total CapEx is approximately the target.

        Used for the capital frontier only. The scaling is applied uniformly to
        the non-land budget, which is a sensitivity device rather than a
        contractor's budget.
        """
        if target_total_capex <= self.land_amount:
            raise ValueError("Target CapEx must exceed the land value")
        lo, hi = 0.05, 3.0
        best = self.scale_non_land_capex(1.0)
        for _ in range(80):
            mid = (lo + hi) / 2.0
            candidate = self.scale_non_land_capex(mid)
            best = candidate
            if candidate.total_capex < target_total_capex:
                lo = mid
            else:
                hi = mid
        return best

    def describe(self) -> Dict[str, float]:
        """Compact dictionary for reports and tests."""
        return {
            "total_capex": self.total_capex,
            "non_land_capex": self.non_land_capex,
            "total_input_vat": self.total_input_vat,
            "leader_subsidy": self.leader_subsidy,
            "annual_depreciation": self.annual_depreciation,
            "external_covers_per_day": self.external_covers_per_day,
            "external_ticket": self.external_ticket,
            "incremental_fte": self.incremental_fte,
            "adr_uplift": self.adr_uplift,
        }


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

# R1: capital-only. A 900k budget with no revenue change. It exists to show
# that value engineering alone cannot close a 600k+ value gap.
CAPEX_ONLY = ReformConfig(
    name="R1 Capital-only (900k)",
    thesis=(
        "Value-engineer the same eight-room product to ~900k. No new demand, "
        "no ADR uplift and no extra F&B covers."
    ),
    renovation_amount=460_000.0,
    kitchen_amount=45_000.0,
    ffe_amount=55_000.0,
    biopool_amount=20_000.0,
    digital_amount=8_000.0,
    external_covers_per_day=0.0,
    external_ticket=0.0,
    experiences_revenue=0.0,
    adr_uplift=0.0,
    cost_savings=0.0,
    incremental_fte=0.0,
)

# R2: the main revenue-led reform on the current 1.05M budget. Six external
# covers per day is already a destination-restaurant assumption; one FTE is
# the minimum labour step-up.
REVENUE_REFORM = ReformConfig(
    name="R2 Revenue reform (1.05M)",
    thesis=(
        "Keep the full eight-room refurbishment, add six external F&B covers "
        "per day, experiences, a 5% price uplift and 5k of cost savings. One "
        "incremental FTE services the extra covers."
    ),
    external_covers_per_day=6.0,
    external_ticket=28.0,
    external_cogs_ratio=0.32,
    experiences_revenue=12_000.0,
    adr_uplift=0.05,
    cost_savings=5_000.0,
    incremental_fte=1.0,
)

# R3: revenue reform plus a 900k value-engineered budget. This tests whether
# the capital lever can bridge the remaining gap without cutting the room
# count (and therefore without destroying the room revenue base).
VALUE_ENGINEERED = replace(
    REVENUE_REFORM,
    name="R3 Revenue + value engineering (900k)",
    thesis=(
        "Same demand levers as R2, but the eight-room product is delivered for "
        "~900k through a simpler refurbishment, a smaller biopool and tighter "
        "FF&E/fees."
    ),
    renovation_amount=460_000.0,
    kitchen_amount=45_000.0,
    ffe_amount=55_000.0,
    biopool_amount=20_000.0,
    digital_amount=8_000.0,
)

# R4: the only combination that clears the 1.05M asset value in the cap-rate
# bridge: eight external covers, a 10% price uplift and one FTE. It is shown
# as a boundary case, not as a recommendation.
AGGRESSIVE = replace(
    REVENUE_REFORM,
    name="R4 Aggressive demand (1.05M)",
    thesis=(
        "Eight external covers per day, a 10% price uplift and one FTE. This is "
        "the aggressive corner that can clear the asset value; it is not a "
        "base-case underwriting assumption."
    ),
    external_covers_per_day=8.0,
    adr_uplift=0.10,
)

# R5: a 850k value-engineered variant with one FTE. It is the closest thing
# to a viable full eight-room reform on an asset-value basis.
RESIZE_850 = replace(
    VALUE_ENGINEERED,
    name="R5 Lean scope (850k)",
    thesis=(
        "A leaner 850k eight-room refurbishment with six external covers, a 5% "
        "price uplift and one FTE. It tests the minimum capital envelope."
    ),
    renovation_amount=420_000.0,
    kitchen_amount=45_000.0,
    ffe_amount=50_000.0,
    biopool_amount=15_000.0,
    digital_amount=8_000.0,
)

# R6: a severe but plausible downside. INE occupancy, half the external
# covers, a 10% price cut, 1.5 FTE, 20% CapEx overrun, a 10% exit cap, a
# 200 bp rate increase and a one-year LEADER delay.
DOWNSIDE = replace(
    RESIZE_850,
    name="R6 Downside / stress",
    thesis=(
        "INE 21.24% occupancy, three external covers per day, 25 EUR ticket, "
        "1.5 FTE, 20% CapEx overrun, 10% exit cap, +200 bp rates and a "
        "one-year LEADER delay."
    ),
    external_covers_per_day=3.0,
    external_ticket=25.0,
    external_cogs_ratio=0.35,
    experiences_revenue=6_000.0,
    adr_uplift=-0.10,
    cost_savings=0.0,
    incremental_fte=1.5,
    leader_disbursement_year=3,
    exit_cap_rate=0.10,
    discount_rate=0.09,
).scale_non_land_capex(1.20)


REFORM_PRESETS: Dict[str, ReformConfig] = {
    "capex_only": CAPEX_ONLY,
    "revenue_reform": REVENUE_REFORM,
    "value_engineered": VALUE_ENGINEERED,
    "aggressive": AGGRESSIVE,
    "resize_850": RESIZE_850,
    "downside": DOWNSIDE,
}


def get_reform_preset(name: str) -> ReformConfig:
    try:
        return REFORM_PRESETS[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown reform preset '{name}'. Available: {sorted(REFORM_PRESETS)}"
        ) from exc
