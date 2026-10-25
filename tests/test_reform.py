"""
Tests for the reform / resize overlay.

The reform is a separate layer on top of the three as-is cases. These tests
guard four things:

1. The as-is cases are byte-for-byte unchanged when no reform is supplied.
2. The reform still produces a fully balanced three-statement model.
3. The value bridge ties exactly to the reform P&L (no hand-written plug).
4. The conclusion is allowed to stay negative: only the aggressive demand
   corner clears the WACC, and it still fails the total-investment test.
"""

import pytest

from src.config.assumptions import SCENARIOS
from src.config.ine_weights import MARKET_OCCUPANCY
from src.config.reform import CAPEX_ONLY, DOWNSIDE, REVENUE_REFORM
from src.core.metrics import CreditMetricsEngine
from src.core.reform import ReformAnalysisEngine
from src.core.statements import FinancialModelEngine


# The presets are deterministic, so the engine is shared to keep the suite fast.
ENGINE = ReformAnalysisEngine()
R2 = ENGINE.run_config(REVENUE_REFORM, key="revenue_reform")


def _as_is_projection(case: str):
    engine = FinancialModelEngine(case=case, scenario=SCENARIOS["base"])
    df = engine.run_projection(5)
    return engine, df


def test_reform_overlay_leaves_as_is_cases_unchanged():
    engine, df = _as_is_projection("management")

    assert df.iloc[-1]["ebitda"] == pytest.approx(37_041.58, abs=0.01)
    assert (df["revenue_external_fnb"] == 0.0).all()
    assert (df["revenue_experiences"] == 0.0).all()
    assert (df["incremental_payroll"] == 0.0).all()
    assert (df["cost_savings"] == 0.0).all()
    assert (df["balance_sheet_discrepancy"].abs() < 0.01).all()
    assert engine.reform is None


def test_reform_structure_and_balance_sheet():
    engine = FinancialModelEngine(
        case="reform", reform=REVENUE_REFORM, scenario=SCENARIOS["base"]
    )
    df = engine.run_projection(5)

    # Capital structure follows the reform config, not the as-is defaults.
    assert REVENUE_REFORM.total_capex == pytest.approx(1_050_100.0, abs=0.01)
    assert engine.financing.senior_debt_principal == pytest.approx(367_535.0, abs=0.01)
    assert engine.financing.leader_subsidy_amount == pytest.approx(162_765.50, abs=0.01)
    assert engine.total_project_investment == pytest.approx(1_138_625.22, abs=0.05)

    # The overlay is additive but the statement identity must still hold.
    assert (df["balance_sheet_discrepancy"].abs() < 0.01).all()
    assert df.iloc[-1]["revenue_external_fnb"] == pytest.approx(61_320.0, abs=0.01)
    assert df.iloc[-1]["revenue_experiences"] == pytest.approx(12_000.0, abs=0.01)
    assert df.iloc[-1]["incremental_payroll"] == pytest.approx(28_000.0, abs=0.01)


def test_value_bridge_ties_to_reform_ebitda():
    bridge = ENGINE.value_bridge(REVENUE_REFORM)

    assert bridge["bridge_tie"] == pytest.approx(0.0, abs=0.01)
    assert bridge["reform_ebitda"] == pytest.approx(71_321.37, abs=0.01)
    assert bridge["reform_ebitda"] == pytest.approx(R2.ebitda_y5, abs=0.01)
    assert bridge["total_increment_ebitda"] == pytest.approx(
        R2.ebitda_y5 - bridge["base_ebitda"], abs=0.01
    )

    components = bridge["components_ebitda"]
    assert components["external_fnb"] > 0
    assert components["experiences"] > 0
    assert components["adr_uplift"] > 0
    assert components["cost_savings"] > 0


def test_capex_only_reform_does_not_create_value():
    result = ENGINE.run_config(CAPEX_ONLY, key="capex_only")

    # No demand lever means no EBITDA uplift: the reform is pure capital.
    assert result.ebitda_y5 == pytest.approx(37_041.58, abs=0.01)
    assert result.value_gap_capex < 0
    assert result.value_gap_total_investment < 0
    assert result.project_npv < 0


def test_frontier_direction_is_economically_sensible():
    # A deliberately small grid keeps the test fast while still proving the
    # direction of both levers.
    frontier = ENGINE.frontier(
        capex_levels=[1_050_100, 850_000],
        cover_levels=[0, 6, 10],
        base_config=REVENUE_REFORM,
    )

    assert frontier.shape == (2, 3)
    # More external covers must improve the total-investment value gap.
    assert frontier.loc[850_000, 10.0] > frontier.loc[850_000, 6.0]
    assert frontier.loc[850_000, 6.0] > frontier.loc[850_000, 0.0]
    # Less capital at the same demand must also improve it.
    assert frontier.loc[850_000, 6.0] > frontier.loc[1_050_100, 6.0]


def test_recommendation_keeps_the_decline_and_flags_the_boundary_case():
    rec = ENGINE.recommendation()

    assert rec["stance"] == "decline_with_boundary"
    assert rec["clearing_cases"] == ["aggressive"]
    assert "DECLINE" in rec["verdict"]

    results = rec["results"]
    assert results["aggressive"].project_npv > 0
    assert results["aggressive"].value_gap_total_investment < 0
    assert results["aggressive"].net_value_gap_capex > 0
    assert results["aggressive"].net_value_gap_total_investment < 0
    assert results["revenue_reform"].project_npv < 0
    assert results["value_engineered"].project_npv < 0
    assert results["resize_850"].project_npv < 0


def test_exit_costs_make_the_value_gap_more_conservative():
    assert R2.exit_cost_rate == pytest.approx(0.03, abs=1e-9)
    assert R2.exit_costs == pytest.approx(
        R2.ev_cap_rate * R2.exit_cost_rate, abs=0.01
    )
    assert R2.net_exit_value == pytest.approx(
        R2.ev_cap_rate - R2.exit_costs, abs=0.01
    )
    assert R2.net_value_gap_capex < R2.value_gap_capex
    assert R2.net_value_gap_total_investment < R2.value_gap_total_investment


def test_rate_sensitivity_moves_dscr_and_npv_in_the_expected_direction():
    sensitivity = ENGINE.rate_sensitivity()

    assert list(sensitivity["rate_delta_bp"]) == [0, 100, 200, 300]
    assert sensitivity.iloc[0]["interest_rate"] == pytest.approx(0.04, abs=1e-9)
    assert sensitivity.iloc[-1]["interest_rate"] == pytest.approx(0.07, abs=1e-9)
    assert sensitivity.iloc[0]["dscr_min"] > sensitivity.iloc[-1]["dscr_min"]
    assert sensitivity.iloc[0]["project_npv"] > sensitivity.iloc[-1]["project_npv"]


def test_downside_is_pinned_to_ine_and_its_value_is_floored_at_zero():
    r6 = ENGINE.run_config(DOWNSIDE, key="downside")

    # R6 must genuinely run at the INE anchor, not merely be labelled INE.
    assert DOWNSIDE.demand_anchor == pytest.approx(MARKET_OCCUPANCY, abs=1e-9)
    assert r6.ebitda_y5 < 0
    assert r6.dscr_min < 0

    # A loss-making asset does not have a negative enterprise value.
    assert r6.ev_cap_rate == 0.0
    assert r6.net_exit_value == 0.0
    assert r6.net_value_gap_total_investment == pytest.approx(
        -r6.total_project_investment, abs=0.01
    )
    assert r6.project_npv < ENGINE.run_config(
        REVENUE_REFORM, key="revenue_reform"
    ).project_npv


def test_leader_delay_shifts_the_grant_to_year_three():
    regular = FinancialModelEngine(
        case="reform", reform=REVENUE_REFORM, scenario=SCENARIOS["base"]
    ).run_projection(5)
    delayed = FinancialModelEngine(
        case="reform", reform=DOWNSIDE, scenario=SCENARIOS["base"]
    ).run_projection(5)

    assert regular.iloc[1]["capital_subsidies"] == pytest.approx(162_765.50, abs=0.01)
    assert delayed.iloc[1]["capital_subsidies"] == pytest.approx(0.0, abs=0.01)
    assert delayed.iloc[2]["capital_subsidies"] == pytest.approx(
        DOWNSIDE.leader_subsidy, abs=0.01
    )


def test_reform_presets_keep_the_as_is_returns_engine_consistent():
    credit = CreditMetricsEngine(target_dscr=1.25, discount_wacc=0.08)
    engine = FinancialModelEngine(
        case="reform", reform=REVENUE_REFORM, scenario=SCENARIOS["base"]
    )
    df = engine.run_projection(5)
    kpi = credit.compute_credit_kpis(df, engine.debt_engine.get_annual_schedule_df())

    assert kpi["dscr"].min() == pytest.approx(2.13, abs=0.01)
    assert (kpi["dscr_covenant_pass"]).all()
    assert df.iloc[-1]["ending_cash"] > 0
