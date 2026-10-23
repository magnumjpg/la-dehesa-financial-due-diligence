"""
Unit tests for scenario stress-testing and Monte Carlo simulations.
"""

import pytest
import pandas as pd
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

    # Base scenario Y1 revenue should exceed Conservative Y1 revenue
    base_rev = float(results["base"].iloc[0]["total_revenue"])
    cons_rev = float(results["conservative"].iloc[0]["total_revenue"])
    assert base_rev > cons_rev


def test_sensitivity_matrix_dscr():
    engine = ScenarioEngine(target_dscr=1.25)
    matrix = engine.generate_sensitivity_matrix_dscr()

    assert matrix.shape == (7, 7)
    # Higher occupancy factor increases DSCR in every column
    assert matrix.iloc[6, 0] > matrix.iloc[0, 0]


def test_monte_carlo_execution_and_statistics():
    sim = MonteCarloSimulator(iterations=100, random_seed=42)
    df_sim, summary = sim.run_simulation()

    assert len(df_sim) == 100
    assert summary.iterations == 100
    assert summary.mean_dscr_y1 > 1.00
    assert 0.0 <= summary.prob_covenant_breach_y1 <= 1.0
    assert summary.p5_dscr_y1 < summary.median_dscr_y1 < summary.p95_dscr_y1
