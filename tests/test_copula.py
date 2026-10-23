"""
Unit test suite for the Multivariate Copula Simulation Engine and Credit Committee Underwriting.

Tests:
1. Copula generation and uniformity of marginals (Kolmogorov-Smirnov goodness-of-fit).
2. Correlation matrix properties (positive definiteness and symmetry).
3. Vectorized cash flow and DSCR calculation consistency with core accounting statements.
4. Tail risk ordering: Clayton copula produces heavier lower tail shortfall than Gaussian copula.
5. Credit Committee Memorandum generation and DSRA sizing adequacy.
6. Absolute exclusion of em dashes across all outputs.
"""

import numpy as np
import pytest
from scipy import stats

from src.simulation.copula_engine import CopulaSimulationEngine
from src.core.credit_committee import CreditCommitteeMemo
from src.core.statements import FinancialModelEngine
from src.core.metrics import CreditMetricsEngine
from src.config.assumptions import ScenarioDrivers


def test_copula_correlation_matrix_positive_definite():
    """Verifies that the calibrated correlation matrix is symmetric and positive definite."""
    engine = CopulaSimulationEngine(n_simulations=1000)
    corr = engine.corr_matrix

    # Symmetry
    assert np.allclose(corr, corr.T), "Correlation matrix must be symmetric."
    # Positive definiteness (all eigenvalues > 0)
    eigenvalues = np.linalg.eigvals(corr)
    assert np.all(eigenvalues > 0), "Correlation matrix must be strictly positive definite."


def test_copula_uniform_marginals():
    """Tests that marginal draws from copulas are strictly bounded in (0, 1) and approximately uniform."""
    engine = CopulaSimulationEngine(n_simulations=10_000, random_seed=42)
    rng = np.random.default_rng(42)

    u_gauss = engine._generate_gaussian_copula(rng)
    u_t = engine._generate_student_t_copula(rng)
    u_clayton = engine._generate_clayton_copula(rng)

    for name, u_draws in [("Gaussian", u_gauss), ("Student-t", u_t), ("Clayton", u_clayton)]:
        assert u_draws.shape == (10_000, 4)
        assert np.all((u_draws >= 0.0) & (u_draws <= 1.0)), f"{name} draws must be in [0, 1]."

        # KS test for uniform distribution on marginal 0 (Occupancy)
        ks_stat, p_val = stats.kstest(u_draws[:, 0], "uniform")
        assert p_val > 0.005, f"{name} marginal 0 failed uniformity test (p={p_val:.4f})."


def test_vectorized_dscr_matches_financial_model_engine():
    """Ensures vectorized DSCR evaluation yields identical results to FinancialModelEngine."""
    engine = CopulaSimulationEngine(n_simulations=10)

    # Test baseline scenario (multipliers = 1.0, rate_delta = 0.0)
    occ_arr = np.array([1.0, 0.85, 1.20])
    adr_arr = np.array([1.0, 0.95, 1.10])
    rate_arr = np.array([0.0, 0.015, -0.005])
    opex_arr = np.array([1.0, 1.10, 0.98])

    dscr_vec, cfads_vec, ds_vec = engine._evaluate_vectorized_dscr(occ_arr, adr_arr, rate_arr, opex_arr)

    for i in range(len(occ_arr)):
        sc = ScenarioDrivers(
            name=f"test_{i}",
            occupancy_multiplier=occ_arr[i],
            adr_multiplier=adr_arr[i],
            opex_multiplier=opex_arr[i],
            interest_rate_delta=rate_arr[i],
        )
        stmt_engine = FinancialModelEngine(scenario=sc)
        df_p = stmt_engine.run_projection(projection_years=1)
        debt_sched = stmt_engine.debt_engine.get_annual_schedule_df()
        df_kpi = CreditMetricsEngine().compute_credit_kpis(df_p, debt_sched)

        expected_dscr = float(df_kpi.iloc[0]["dscr"])
        expected_ds = float(df_kpi.iloc[0]["debt_service"])

        assert np.isclose(dscr_vec[i], expected_dscr, atol=0.02), f"Scenario {i} DSCR mismatch."
        assert np.isclose(ds_vec[i], expected_ds, atol=1.0), f"Scenario {i} Debt service mismatch."


def test_tail_risk_ordering():
    """
    Demonstrates the core quantitative hypothesis:
    Under Clayton copula (theta=1.8), joint downside clustering causes:
    1. Lower 99% CVaR than Gaussian (more severe tail collapse).
    2. Higher tail cash shortfall in euros.
    """
    engine = CopulaSimulationEngine(n_simulations=30_000, random_seed=42)
    results = engine.run_comparative_analysis()

    # Clayton CVaR 99% should reflect more severe cash depletion than Gaussian
    assert results.clayton.cvar_99 < results.gaussian.cvar_99, (
        f"Clayton CVaR 99% ({results.clayton.cvar_99:.2f}x) should be strictly lower than "
        f"Gaussian CVaR 99% ({results.gaussian.cvar_99:.2f}x)."
    )

    # Clayton 99% Expected Shortfall deficit in euros must exceed Gaussian deficit
    assert results.clayton.tail_deficit_cvar99_eur > results.gaussian.tail_deficit_cvar99_eur, (
        f"Clayton tail deficit ({results.clayton.tail_deficit_cvar99_eur:,.0f} EUR) must exceed "
        f"Gaussian ({results.gaussian.tail_deficit_cvar99_eur:,.0f} EUR)."
    )

    # Recommended DSRA must be at least as large as 6-month covenant
    assert results.dsra_recommended_tail >= results.dsra_standard_6m


def test_credit_committee_memo_structure_and_no_em_dashes():
    """Verifies that the credit memorandum generates properly and contains zero em dashes."""
    memo_gen = CreditCommitteeMemo()
    memo_text = memo_gen.generate_markdown_report()

    # Structural sections
    assert "# BANK CREDIT COMMITTEE UNDERWRITING MEMORANDUM" in memo_text
    assert "**Facility Reference:** CRE-SME-2026-CASTRILLO-001" in memo_text
    assert "Executive Summary and Facility Terms" in memo_text
    assert "Solvency, Coverage, and Break-Even Profile" in memo_text
    assert "Multivariate Copula Stress Test" in memo_text
    assert "Debt Service Reserve Account (DSRA) Sizing" in memo_text
    assert "Credit Committee Final Recommendation" in memo_text
    assert "CONDITIONAL APPROVAL" in memo_text

    # Strict compliance: Zero em dashes allowed
    assert "—" not in memo_text, "Em dashes are strictly forbidden in Credit Committee Memorandum."
