"""
Unit tests for Phase II Expansion Financial Engine (Landscape Suites & Biological Pond).
"""

import pytest
from src.core.expansion import (
    ExpansionFinancialEngine,
    ExpansionCapExBreakdown,
    ExpansionOperatingAssumptions,
)


def test_expansion_capex_accounting_equality():
    capex = ExpansionCapExBreakdown()
    assert capex.pure_building_pem == 161_500.0
    assert capex.total_execution_pem == 260_000.0
    assert capex.total_execution_pec == 309_400.0
    assert capex.engineering_architecture_fees == 23_400.0
    assert capex.municipal_taxes_icio == 11_700.0
    assert capex.contingency_reserve == 15_470.0
    assert capex.total_all_in_capex == 359_970.0
    assert capex.input_vat_21pct == pytest.approx(75_593.70, abs=0.01)


def test_expansion_stabilized_pnl_base():
    engine = ExpansionFinancialEngine()
    pnl = engine.compute_stabilized_pnl(scenario="base")

    assert pnl["occupied_nights"] == 365.0
    assert pnl["lodging_revenue"] == 105_850.0
    assert pnl["fnb_revenue"] == pytest.approx(40_332.50, abs=0.1)
    assert pnl["gross_revenue"] == pytest.approx(146_182.50, abs=0.1)
    assert pnl["contribution_margin"] == pytest.approx(114_020.53, abs=0.1)
    assert pnl["contribution_margin_ratio"] == pytest.approx(0.78, abs=0.01)
    assert pnl["ebitda"] == pytest.approx(99_620.53, abs=0.1)
    assert pnl["ebitda_margin"] == pytest.approx(0.6815, abs=0.01)
    assert pnl["free_cash_flow"] == pytest.approx(75_841.41, abs=0.5)


def test_expansion_5year_rampup_and_returns():
    engine = ExpansionFinancialEngine()
    df_5y = engine.compute_5year_schedule()

    assert len(df_5y) == 5
    assert df_5y.iloc[0]["occupancy_rate"] == pytest.approx(0.375, abs=0.001)  # 75% ramp
    assert df_5y.iloc[1]["occupancy_rate"] == pytest.approx(0.450, abs=0.001)  # 90% ramp
    assert df_5y.iloc[2]["occupancy_rate"] == pytest.approx(0.500, abs=0.001)  # 100% mature

    m = engine.compute_investment_metrics()
    assert m["roic_y3"] == pytest.approx(0.1738, abs=0.005)
    assert m["yield_on_cost"] == pytest.approx(0.2767, abs=0.005)
    assert m["simple_ebitda_payback_years"] < 4.10
    assert m["simple_fcf_payback_years"] < 5.20
    assert m["exit_val_85bps"] == pytest.approx(1_219_355.23, rel=0.01)
    assert m["net_gain_85bps"] > 850_000.0
    assert m["moic_85bps"] > 4.30


def test_expansion_consolidated_underwriting():
    engine = ExpansionFinancialEngine()
    cons = engine.compute_consolidated_underwriting()

    assert cons["consolidated_rev_y3"] == pytest.approx(326_488.50, abs=0.1)
    assert cons["consolidated_ebitda_y3"] == pytest.approx(188_760.39, abs=0.1)
    assert cons["ebitda_increase_pct"] == pytest.approx(1.1176, abs=0.01)
    assert cons["consolidated_dscr_y3"] > 3.50
    assert cons["consolidated_valuation_85bps"] > 2_200_000.0


def test_expansion_realistic_and_stress_scenarios():
    engine = ExpansionFinancialEngine()

    realistic = engine.compute_investment_metrics(scenario="realistic")
    assert realistic["ebitda_y3"] == pytest.approx(51_435.20, abs=0.01)
    assert realistic["irr_85bps"] == pytest.approx(0.196402, abs=1e-5)
    assert realistic["moic_85bps"] == pytest.approx(2.2471, abs=0.001)

    stress = engine.compute_investment_metrics(scenario="stress")
    assert stress["ebitda_y3"] == pytest.approx(25_185.88, abs=0.01)
    assert stress["irr_85bps"] == pytest.approx(0.020746, abs=1e-5)
    assert stress["net_gain_85bps"] < 0


def test_phase_two_gate_is_negative_for_management_case():
    engine = ExpansionFinancialEngine()
    gate = engine.compute_phase_gate(phase1_cash_end_y2=193_949.95, phase1_dscr_y3=1.73)

    assert gate["phase1_cash_end_y2"] == 193_949.95
    assert gate["phase2_cash_need"] == 435_563.70
    assert gate["phase2_funding_gap"] == -241_613.75
    assert gate["dscr_condition_met"] is True
    assert gate["cash_condition_met"] is False
    assert gate["phase2_proceed"] is False
    assert "DO NOT PROCEED" in gate["recommendation"]


def test_consolidated_underwriting_uses_the_phase_gate():
    engine = ExpansionFinancialEngine()
    cons = engine.compute_consolidated_underwriting(
        phase1_cash_end_y2=193_949.95,
        phase1_dscr_y3=1.73,
    )

    assert cons["phase2_funding_gap"] == -241_613.75
    assert cons["phase2_cash_condition_met"] is False
    assert cons["phase2_proceed"] is False
    # The consolidated DSCR is only valid if Phase II is actually funded.
    assert cons["consolidated_dscr_y3"] == pytest.approx(4.3357, abs=1e-3)

