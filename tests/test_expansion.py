"""
Unit tests for Phase II Expansion Financial Engine (Landscape Suites & Biological Pond).
"""

import pytest

from src.core.expansion import (
    ExpansionFinancialEngine,
    ExpansionCapExBreakdown,
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

    # 2 suites * 365 nights * 35% = 255.5 occupied nights.
    assert pnl["occupied_nights"] == pytest.approx(255.5, abs=0.01)
    assert pnl["occupancy_rate"] == pytest.approx(0.35, abs=0.001)
    assert pnl["lodging_revenue"] == pytest.approx(74_095.0, abs=0.01)
    assert pnl["fnb_revenue"] == pytest.approx(28_232.75, abs=0.01)
    assert pnl["gross_revenue"] == pytest.approx(102_327.75, abs=0.01)
    assert pnl["contribution_margin"] == pytest.approx(79_814.37, abs=0.05)
    assert pnl["contribution_margin_ratio"] == pytest.approx(0.78, abs=0.01)
    assert pnl["ebitda"] == pytest.approx(37_414.37, abs=0.05)
    assert pnl["ebitda_margin"] == pytest.approx(0.3656, abs=0.001)
    assert pnl["free_cash_flow"] == pytest.approx(30_063.88, abs=0.05)


def test_expansion_5year_rampup_and_returns():
    engine = ExpansionFinancialEngine()
    df_5y = engine.compute_5year_schedule()

    assert len(df_5y) == 5
    assert df_5y.iloc[0]["occupancy_rate"] == pytest.approx(0.2625, abs=0.001)  # 75% ramp
    assert df_5y.iloc[1]["occupancy_rate"] == pytest.approx(0.3150, abs=0.001)  # 90% ramp
    assert df_5y.iloc[2]["occupancy_rate"] == pytest.approx(0.3500, abs=0.001)  # mature

    m = engine.compute_investment_metrics()
    assert m["roic_y3"] == pytest.approx(0.044203, abs=1e-5)
    assert m["yield_on_cost"] == pytest.approx(0.103937, abs=1e-5)
    assert m["simple_ebitda_payback_years"] == pytest.approx(10.10, abs=0.01)
    assert m["simple_fcf_payback_years"] == pytest.approx(12.34, abs=0.01)
    assert m["exit_val_85bps"] == pytest.approx(457_951.86, rel=0.001)
    assert m["net_gain_85bps"] == pytest.approx(97_981.86, abs=0.5)
    assert m["moic_85bps"] == pytest.approx(1.637935, abs=1e-5)
    assert m["irr_85bps"] == pytest.approx(0.114192, abs=1e-5)


def test_expansion_consolidated_underwriting():
    engine = ExpansionFinancialEngine()
    cons = engine.compute_consolidated_underwriting(
        phase1_rev_y3=171_720.0,
        phase1_ebitda_y3=37_041.58,
        phase1_cfads_y3=31_889.98,
        phase1_senior_debt_service=27_647.64,
        phase1_capex=1_050_100.0,
        phase1_cash_end_y2=183_322.64,
        phase1_dscr_y3=1.1534,
    )

    assert cons["consolidated_rev_y3"] == pytest.approx(253_188.0, abs=0.01)
    assert cons["consolidated_ebitda_y3"] == pytest.approx(57_198.38, abs=0.01)
    assert cons["consolidated_cfads_y3"] == pytest.approx(49_427.88, abs=0.01)
    assert cons["ebitda_increase_pct"] == pytest.approx(0.5442, abs=0.001)
    assert cons["consolidated_dscr_y3"] == pytest.approx(1.7878, abs=0.001)
    assert cons["consolidated_valuation_85bps"] == pytest.approx(672_922.15, rel=0.001)
    assert cons["consolidated_total_capex"] == 1_410_070.0


def test_expansion_realistic_and_stress_scenarios():
    engine = ExpansionFinancialEngine()

    realistic = engine.compute_investment_metrics(scenario="realistic")
    assert realistic["ebitda_y3"] == pytest.approx(20_156.80, abs=0.01)
    assert realistic["irr_85bps"] == pytest.approx(-0.027521, abs=1e-5)
    assert realistic["moic_85bps"] == pytest.approx(0.877512, abs=1e-5)
    assert realistic["net_gain_85bps"] < 0

    # The stress case uses the official INE 21.24% occupancy: EBITDA is
    # negative and the suites destroy capital.
    stress = engine.compute_investment_metrics(scenario="stress")
    assert stress["ebitda_y3"] == pytest.approx(-4_393.65, abs=0.01)
    assert stress["net_gain_85bps"] < 0
    assert stress["moic_85bps"] < 0


def test_phase_two_gate_is_negative_for_management_case():
    engine = ExpansionFinancialEngine()
    gate = engine.compute_phase_gate(phase1_cash_end_y2=183_322.64, phase1_dscr_y3=1.1534)

    assert gate["phase1_cash_end_y2"] == 183_322.64
    assert gate["phase2_cash_need"] == 435_563.70
    assert gate["phase2_funding_gap"] == pytest.approx(-252_241.06, abs=0.01)
    # Phase I DSCR (1.15x) is below the 1.25x gate and Phase I cash does not
    # cover the Phase II need, so the option is not exercisable.
    assert gate["dscr_condition_met"] is False
    assert gate["cash_condition_met"] is False
    assert gate["phase2_proceed"] is False
    assert "DO NOT PROCEED" in gate["recommendation"]


def test_consolidated_underwriting_uses_the_phase_gate():
    engine = ExpansionFinancialEngine()
    cons = engine.compute_consolidated_underwriting(
        phase1_rev_y3=171_720.0,
        phase1_ebitda_y3=37_041.58,
        phase1_cfads_y3=31_889.98,
        phase1_senior_debt_service=27_647.64,
        phase1_capex=1_050_100.0,
        phase1_cash_end_y2=183_322.64,
        phase1_dscr_y3=1.1534,
    )

    assert cons["phase2_cash_need"] == 435_563.70
    assert cons["phase2_funding_gap"] == pytest.approx(-252_241.06, abs=0.01)
    assert cons["phase2_cash_condition_met"] is False
    assert cons["phase2_dscr_condition_met"] is False
    assert cons["phase2_proceed"] is False
    # The consolidated DSCR is a pro-forma metric, only valid if Phase II is
    # actually funded (which the gate says it is not).
    assert cons["consolidated_dscr_y3"] == pytest.approx(1.7878, abs=1e-3)
