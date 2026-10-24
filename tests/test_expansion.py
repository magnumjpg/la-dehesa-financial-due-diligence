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
