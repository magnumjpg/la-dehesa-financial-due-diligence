"""
Unit tests for scenario stress-testing and Monte Carlo simulations.
"""

import pytest

from src.scenarios.scenario_analysis import ScenarioEngine
from src.simulation.monte_carlo import MonteCarloSimulator


def test_scenario_comparison_generation():
    engine = ScenarioEngine(target_dscr=1.25, projection_years=3)
    results = engine.run_all_scenarios()

    assert "conservative" in results
    assert "base" in results
    assert "optimistic" in results

    df_comp = engine.generate_scenario_comparison_table()
    assert len(df_comp) == 6

    base_rev = float(results["base"].iloc[0]["total_revenue"])
    cons_rev = float(results["conservative"].iloc[0]["total_revenue"])
    assert base_rev > cons_rev


def test_sensitivity_matrix_dscr():
    engine = ScenarioEngine(target_dscr=1.25)
    matrix = engine.generate_sensitivity_matrix_dscr()

    assert matrix.shape == (7, 7)
    # The matrix is the Year-2 DSCR (first amortising year): at a 100% demand
    # factor and a 4.0% rate it equals the model's 1.15x.
    assert matrix.loc["100% Occ Factor", "4.0% Rate"] == pytest.approx(1.15, abs=0.01)
    # Higher occupancy raises DSCR in every rate column.
    assert matrix.iloc[6, 0] > matrix.iloc[3, 0]
    assert matrix.iloc[3, 0] > matrix.iloc[0, 0]


def test_monte_carlo_execution_and_statistics():
    sim = MonteCarloSimulator(iterations=100, random_seed=42)
    df_sim, summary = sim.run_simulation()

    assert len(df_sim) == 100
    assert summary.iterations == 100
    assert "sim_id" in df_sim.columns
    assert {"dscr_y1", "dscr_y2", "min_dscr", "covenant_breach"} <= set(df_sim.columns)

    assert 0.5 < summary.mean_min_dscr < 2.5
    assert 0.0 <= summary.prob_covenant_breach <= 1.0
    assert 0.0 <= summary.prob_cash_insolvency <= 1.0
    assert summary.p5_min_dscr < summary.median_min_dscr < summary.p95_min_dscr
    assert summary.cash_equity == pytest.approx(521_090.22, abs=0.01)
    assert summary.total_equity_at_close == pytest.approx(771_090.22, abs=0.01)
