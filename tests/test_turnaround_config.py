"""
Tests for the T8 cabin-turnaround configuration.

The config is the single source of truth for Act 4: if these numbers drift the
narrative in the README and the Excel no longer ties. They are tested against
the arithmetic of the budget, not against a second copy of the answer.
"""

import pytest

from src.config.assumptions import CapExStructure, SCENARIOS
from src.config.turnaround import (
    CabinProduct,
    TurnaroundConfig,
    adr_variant,
    debt_variant,
    occupancy_variant,
    with_exit_cap,
)
from src.core.statements import FinancialModelEngine


def test_capex_budget_arithmetic():
    cfg = TurnaroundConfig.base()
    capex = cfg.capex

    assert capex.works == pytest.approx(560_000.0)
    assert capex.fees == pytest.approx(33_600.0)
    assert capex.contingency == pytest.approx(28_000.0)
    assert capex.cash_capex == pytest.approx(621_600.0)
    assert capex.total_capex == pytest.approx(871_600.0)
    assert capex.input_vat == pytest.approx(130_536.0)


def test_installed_cost_bridges_module_price_to_benchmark():
    cfg = TurnaroundConfig.base()
    assert cfg.capex.installed_cost_per_cabin == pytest.approx(93_600.0)
    # The EUR 60k module is the shell; fees, contingency, infrastructure, FF&E,
    # digital and the pond share are the EUR 33.6k gap.
    assert (
        cfg.capex.installed_cost_per_cabin - cfg.cabins.unit_cost
    ) == pytest.approx(33_600.0)
    # And the benchmark band is EUR 85-110k installed.
    assert 85_000 <= cfg.capex.installed_cost_per_cabin <= 110_000


def test_capex_structure_maps_onto_shared_engine():
    cfg = TurnaroundConfig.base()
    structure = cfg.build_capex()

    assert isinstance(structure, CapExStructure)
    assert structure.total_capex == pytest.approx(871_600.0)
    assert structure.cabins.amount == pytest.approx(360_000.0)
    assert structure.infrastructure.amount == pytest.approx(70_000.0)
    assert structure.kitchen_equipment.amount == 0.0
    # 360k*3% + 40k*10% + 70k*10% + 60k*3% + 20k*10% + 10k*25%
    # + fees 33.6k*3% + contingency 28k*3% = 29,948
    assert structure.annual_depreciation == pytest.approx(29_948.0)


def test_financing_builds_to_450k_and_dsra():
    cfg = TurnaroundConfig.base()
    financing = cfg.build_financing()

    assert financing.senior_debt_principal == pytest.approx(450_000.0, abs=0.01)
    assert financing.loan_interest_rate == pytest.approx(0.0425)
    assert financing.loan_tenure_years == 20
    assert financing.grace_months == 12
    assert financing.idc_amount == pytest.approx(19_125.0)
    assert financing.arrangement_fee == pytest.approx(4_500.0)
    assert financing.land_in_kind is True
    assert financing.leader_subsidy_amount == 0.0


def test_payroll_and_fixed_opex():
    cfg = TurnaroundConfig.base()
    labor = cfg.build_labor()
    opex = cfg.build_opex()

    assert labor.total_annual_payroll == pytest.approx(60_950.0)
    assert labor.total_fte == pytest.approx(2.0)
    assert len(labor.roles) == 2
    assert opex.total_fixed_opex == pytest.approx(37_000.0)


def test_config_validation_rejects_impossible_inputs():
    with pytest.raises(ValueError):
        TurnaroundConfig(cabins=CabinProduct(count=0))
    with pytest.raises(ValueError):
        TurnaroundConfig(cabins=CabinProduct(occupancy=(0.5, 1.2)))


def test_cabins_only_removes_the_lodge_scope():
    cfg = TurnaroundConfig.cabins_only()
    assert cfg.lodge.enabled is False
    assert cfg.keys == 6
    assert cfg.capex.cash_capex == pytest.approx(555_000.0)
    assert cfg.build_capex().total_capex == pytest.approx(805_000.0)


def test_variants_change_only_their_axis():
    base = TurnaroundConfig.base()
    adr = adr_variant(0.10)
    assert adr.cabins.adr == pytest.approx(231.0)
    assert adr.lodge.adr == pytest.approx(462.0)
    assert adr.capex.cash_capex == base.capex.cash_capex

    occ = occupancy_variant(0.45)
    assert occ.cabins.occupancy_for_year(3) == pytest.approx(0.45)

    debt = debt_variant(400_000)
    assert debt.financing.debt == pytest.approx(400_000.0)
    assert debt.build_financing().senior_debt_principal == pytest.approx(400_000.0, abs=0.01)

    cap = with_exit_cap(0.095)
    assert cap.exit_cap_rate == pytest.approx(0.095)


def test_as_is_capex_untouched_by_the_new_slots():
    """The T8 slots default to zero: the three as-is cases keep their totals."""
    default = CapExStructure()
    assert default.cabins.amount == 0.0
    assert default.infrastructure.amount == 0.0
    assert default.total_capex == pytest.approx(1_050_100.0)
    assert default.total_base_capex == pytest.approx(840_000.0)

    promoter = FinancialModelEngine(case="promoter", scenario=SCENARIOS["base"])
    assert promoter.capex.total_capex == pytest.approx(725_000.0)
    assert promoter.financing.arrangement_fee == 0.0
