"""
Unit tests for UnitEconomicsEngine and MonthlyCashEngine.
"""

import pytest
import pandas as pd
from src.core.unit_economics import UnitEconomicsEngine, UnitEconomicsMetrics
from src.core.monthly_cash import MonthlyCashEngine, MonthlyRunwaySummary


def test_unit_economics_metrics_baseline():
    engine = UnitEconomicsEngine()
    metrics = engine.compute_unit_metrics()

    assert isinstance(metrics, UnitEconomicsMetrics)
    assert metrics.total_keys == 8
    assert metrics.annual_available_keys == 2920

    # Capacity revenue at 100% occupancy: 7*85 + 380 = 975 lodging; 21*25 = 525 dining -> 1500 total
    assert metrics.daily_lodging_revenue == 975.0
    assert metrics.daily_restaurant_revenue == 525.0
    assert metrics.daily_gross_revenue == 1500.0

    # Variable costs & Contribution margin
    assert metrics.daily_total_variable_cost > 0.0
    assert metrics.unit_contribution_margin_eur > 1000.0
    assert 0.75 < metrics.unit_contribution_margin_pct < 0.90

    # Fixed cost and debt burden ordering
    assert metrics.annual_fixed_overhead == 72234.0
    assert metrics.operating_breakeven_days < metrics.cash_debt_breakeven_days
    assert metrics.cash_debt_breakeven_days < metrics.covenant_125_breakeven_days


def test_revpar_trevpar_schedule():
    engine = UnitEconomicsEngine()
    df_sched = engine.compute_revpar_trevpar_schedule()

    assert len(df_sched) == 3
    assert "RevPAR (€)" in df_sched.columns
    assert "TRevPAR (€)" in df_sched.columns

    y1_revpar = df_sched.loc[df_sched["Year"] == 1, "RevPAR (€)"].iloc[0]
    y1_trevpar = df_sched.loc[df_sched["Year"] == 1, "TRevPAR (€)"].iloc[0]
    y3_trevpar = df_sched.loc[df_sched["Year"] == 3, "TRevPAR (€)"].iloc[0]

    # TRevPAR must be higher than RevPAR due to dining revenue
    assert y1_trevpar > y1_revpar
    # Growth with maturity
    assert y3_trevpar > y1_trevpar


def test_monthly_cash_flow_schedule():
    # Unfunded: opening cash is the adjusted close cash (-€55,978.44), so the
    # €50k line is maxed and the winter trough is negative. This is the honest
    # downside that the old €56,750 "buffer" hid.
    mc = MonthlyCashEngine()
    df_monthly = mc.run_monthly_schedule(horizon_months=24)

    assert len(df_monthly) == 24
    assert (df_monthly["month_index"] == list(range(1, 25))).all()
    assert (df_monthly["credit_line_drawn"] <= 50_000.0).all()

    summary = mc.get_runway_summary(df_monthly)
    assert isinstance(summary, MonthlyRunwaySummary)
    assert summary.liquidity_cushion_never_breached is False
    assert summary.year1_trough_month_index == 3  # March
    assert summary.year1_trough_cash_balance == pytest.approx(-17_906.26, abs=0.01)
    assert summary.year1_max_credit_line_draw == 50_000.0
    assert summary.year1_ending_cash > 0
    assert summary.year2_ending_cash > summary.year1_ending_cash


def test_monthly_cash_flow_after_equity_injection():
    # Funded: add the recommended €70,768.18 equity injection. The trough sits
    # at the €10,000 policy floor and the line draw is only €7,138.08.
    mc = MonthlyCashEngine(initial_cash_buffer=-55_978.44 + 70_768.18)
    df_monthly = mc.run_monthly_schedule(horizon_months=24)
    summary = mc.get_runway_summary(df_monthly)

    assert summary.year1_trough_cash_balance == pytest.approx(10_000.00, abs=0.01)
    assert summary.year1_max_credit_line_draw == pytest.approx(7_138.08, abs=0.01)
    assert summary.liquidity_cushion_never_breached is True
    assert summary.year1_ending_cash > 0

    # The AEAT refund repays the VAT bridge: it is not a second inflow.
    m18 = df_monthly[df_monthly["month_index"] == 18].iloc[0]
    assert m18["tax_bridge_inflows"] == pytest.approx(143_596.37, abs=0.01)
    assert m18["vat_bridge_repayment"] == pytest.approx(-143_596.37, abs=0.01)
