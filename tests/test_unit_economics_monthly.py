"""
Unit tests for UnitEconomicsEngine and MonthlyCashEngine.
"""

import pytest

from src.core.unit_economics import UnitEconomicsEngine, UnitEconomicsMetrics
from src.core.monthly_cash import MonthlyCashEngine, MonthlyRunwaySummary


def test_unit_economics_metrics_baseline():
    engine = UnitEconomicsEngine()
    metrics = engine.compute_unit_metrics()

    assert isinstance(metrics, UnitEconomicsMetrics)
    assert metrics.total_keys == 8
    assert metrics.annual_available_keys == 2920

    # Capacity revenue at 100% occupancy: 7*85 + 380 = 975 lodging; 21*25 = 525 dining.
    assert metrics.daily_lodging_revenue == 975.0
    assert metrics.daily_restaurant_revenue == 525.0
    assert metrics.daily_gross_revenue == 1500.0

    # The full cost stack cuts the contribution margin to 71.3% (not 85%).
    assert metrics.daily_total_variable_cost == 385.25
    assert metrics.unit_contribution_margin_eur == 1069.75
    assert metrics.unit_contribution_margin_pct == pytest.approx(0.7132, abs=0.001)

    # Fixed cost and debt burden ordering.
    assert metrics.annual_fixed_overhead == 90_575.0
    assert metrics.annual_senior_debt_service == 27_647.64
    assert metrics.operating_breakeven_days == pytest.approx(81.2, abs=0.1)
    assert metrics.operating_breakeven_days < metrics.cash_debt_breakeven_days
    assert metrics.cash_debt_breakeven_days < metrics.covenant_125_breakeven_days
    assert metrics.covenant_125_breakeven_days == pytest.approx(117.0, abs=0.1)


def test_revpar_trevpar_schedule():
    engine = UnitEconomicsEngine()
    df_sched = engine.compute_revpar_trevpar_schedule()

    assert len(df_sched) == 3
    assert "RevPAR (EUR)" in df_sched.columns
    assert "TRevPAR (EUR)" in df_sched.columns

    y1_revpar = df_sched.loc[df_sched["Year"] == 1, "RevPAR (EUR)"].iloc[0]
    y1_trevpar = df_sched.loc[df_sched["Year"] == 1, "TRevPAR (EUR)"].iloc[0]
    y2_trevpar = df_sched.loc[df_sched["Year"] == 2, "TRevPAR (EUR)"].iloc[0]

    assert y1_revpar == pytest.approx(34.40, abs=0.01)
    assert y1_trevpar == pytest.approx(52.93, abs=0.01)
    assert y1_trevpar > y1_revpar
    assert y2_trevpar > y1_trevpar


def test_monthly_cash_flow_schedule():
    mc = MonthlyCashEngine()
    df_monthly = mc.run_monthly_schedule(horizon_months=24)

    assert len(df_monthly) == 24
    assert (df_monthly["month_index"] == list(range(1, 25))).all()
    assert (df_monthly["credit_line_draw"] <= 175_000.0).all()

    # The EUR 15k minimum balance is enforced by a small seasonal revolver.
    assert (df_monthly["ending_cash_balance"] >= 15_000.0 - 0.01).all()
    assert df_monthly["credit_line_balance"].max() < 5_000.0

    summary = mc.get_runway_summary(df_monthly)
    assert isinstance(summary, MonthlyRunwaySummary)
    assert summary.liquidity_cushion_never_breached is True
    assert summary.requires_credit_line is True
    assert summary.year1_trough_month_index == 4  # April
    assert summary.year1_trough_cash_balance == pytest.approx(12_004.01, abs=0.01)
    assert summary.year1_trough_actual_cash == pytest.approx(15_000.00, abs=0.01)
    assert summary.year1_max_credit_line_draw == pytest.approx(2_995.99, abs=0.01)
    assert summary.revolver_repaid_month == 7
    assert summary.year1_ending_cash == pytest.approx(20_700.88, abs=0.01)
    assert summary.year2_ending_cash == pytest.approx(183_322.64, abs=0.01)

    # Monthly and annual statements reconcile exactly.
    assert summary.annual_reconciliation_max_diff == pytest.approx(0.0, abs=0.01)


def test_vat_bridge_is_repaid_with_the_aeat_refund():
    mc = MonthlyCashEngine()
    df_monthly = mc.run_monthly_schedule(horizon_months=24)

    m18 = df_monthly[df_monthly["month_index"] == 18].iloc[0]
    assert m18["vat_refund_inflow"] == pytest.approx(168_021.00, abs=0.01)
    assert m18["vat_bridge_repayment"] == pytest.approx(-168_021.00, abs=0.01)

    # The LEADER grant arrives in Month 14 and is not double counted.
    m14 = df_monthly[df_monthly["month_index"] == 14].iloc[0]
    assert m14["leader_inflow"] == pytest.approx(163_000.00, abs=0.01)
    assert df_monthly["leader_inflow"].sum() == pytest.approx(163_000.00, abs=0.01)
