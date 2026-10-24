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
    mc = MonthlyCashEngine(initial_cash_buffer=56_750.0)
    df_monthly = mc.run_monthly_schedule(horizon_months=24)

    assert len(df_monthly) == 24
    assert (df_monthly["month_index"] == list(range(1, 25))).all()

    # Cash balance must remain positive at all times
    assert (df_monthly["ending_cash_balance"] >= 0.0).all()

    # Credit line must not exceed limit
    assert (df_monthly["credit_line_drawn"] <= 50_000.0).all()

    summary = mc.get_runway_summary(df_monthly)
    assert isinstance(summary, MonthlyRunwaySummary)
    assert summary.liquidity_cushion_never_breached is True
    assert summary.year1_trough_month_index in [1, 2, 3]  # Winter trough in Jan-Feb-Mar
    assert summary.year1_trough_cash_balance > 0.0
    assert summary.year2_ending_cash > summary.year1_ending_cash
