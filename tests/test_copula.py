"""
Unit test suite for the Multivariate Copula Simulation Engine and Credit Committee Underwriting.

Tests:
1. Copula generation and uniformity of marginals (Kolmogorov-Smirnov goodness-of-fit).
2. Correlation matrix properties (positive definiteness and symmetry).
3. Vectorized Year-2 cash flow and DSCR calculation consistency with core accounting statements.
4. Tail risk ordering: Clayton copula produces heavier lower tail shortfall than Gaussian copula.
5. Credit Committee Memorandum generation, DSRA sizing adequacy and the honest verdict.
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
    engine = CopulaSimulationEngine(n_simulations=1000)
    corr = engine.corr_matrix

    assert np.allclose(corr, corr.T), "Correlation matrix must be symmetric."
    eigenvalues = np.linalg.eigvals(corr)
    assert np.all(eigenvalues > 0), "Correlation matrix must be strictly positive definite."


def test_copula_uniform_marginals():
    engine = CopulaSimulationEngine(n_simulations=10_000, random_seed=42)
    rng = np.random.default_rng(42)

    u_gauss = engine._generate_gaussian_copula(rng)
    u_t = engine._generate_student_t_copula(rng)
    u_clayton = engine._generate_clayton_copula(rng)

    for name, u_draws in [("Gaussian", u_gauss), ("Student-t", u_t), ("Clayton", u_clayton)]:
        assert u_draws.shape == (10_000, 4)
        assert np.all((u_draws >= 0.0) & (u_draws <= 1.0)), f"{name} draws must be in [0, 1]."

        ks_stat, p_val = stats.kstest(u_draws[:, 0], "uniform")
        assert p_val > 0.005, f"{name} marginal 0 failed uniformity test (p={p_val:.4f})."


def test_vectorized_dscr_matches_financial_model_engine():
    """The copula tests the Year-2 DSCR (first amortising year) on the full stack."""
    engine = CopulaSimulationEngine(n_simulations=10)

    occ_arr = np.array([1.0, 0.85, 1.20, 1.10])
    adr_arr = np.array([1.0, 0.95, 1.10, 1.05])
    rate_arr = np.array([0.0, 0.015, -0.005, 0.01])
    opex_arr = np.array([1.0, 1.10, 0.98, 1.03])

    dscr_vec, cfads_vec, ds_vec = engine._evaluate_vectorized_dscr(
        occ_arr, adr_arr, rate_arr, opex_arr
    )

    # Baseline is the deterministic Year-2 DSCR before rounding.
    assert dscr_vec[0] == pytest.approx(1.1534, abs=1e-3)
    assert cfads_vec[0] == pytest.approx(31_889.98, abs=0.05)

    for i in range(len(occ_arr)):
        sc = ScenarioDrivers(
            name=f"test_{i}",
            occupancy_multiplier=occ_arr[i],
            adr_multiplier=adr_arr[i],
            opex_multiplier=opex_arr[i],
            interest_rate_delta=rate_arr[i],
        )
        stmt_engine = FinancialModelEngine(scenario=sc)
        df_p = stmt_engine.run_projection(projection_years=2)
        debt_sched = stmt_engine.debt_engine.get_annual_schedule_df()
        df_kpi = CreditMetricsEngine().compute_credit_kpis(df_p, debt_sched)

        expected_dscr = float(df_kpi.iloc[1]["dscr"])
        expected_ds = float(df_kpi.iloc[1]["debt_service"])
        expected_cfads = float(df_kpi.iloc[1]["cfads"])

        assert np.isclose(dscr_vec[i], expected_dscr, atol=0.02), f"Scenario {i} DSCR mismatch."
        assert np.isclose(cfads_vec[i], expected_cfads, atol=1.0), f"Scenario {i} CFADS mismatch."
        assert np.isclose(ds_vec[i], expected_ds, atol=1.0), f"Scenario {i} Debt service mismatch."


def test_tail_risk_ordering():
    """
    Under Clayton (theta=1.8), joint downside clustering causes a lower 99% CVaR
    and a larger annual cash shortfall than the Gaussian benchmark.
    """
    engine = CopulaSimulationEngine(n_simulations=30_000, random_seed=42)
    results = engine.run_comparative_analysis()

    assert results.clayton.cvar_99 < results.gaussian.cvar_99, (
        f"Clayton CVaR 99% ({results.clayton.cvar_99:.2f}x) should be strictly lower than "
        f"Gaussian CVaR 99% ({results.gaussian.cvar_99:.2f}x)."
    )

    assert results.clayton.tail_deficit_cvar99_eur > results.gaussian.tail_deficit_cvar99_eur, (
        f"Clayton tail deficit ({results.clayton.tail_deficit_cvar99_eur:,.0f} EUR) must exceed "
        f"Gaussian ({results.gaussian.tail_deficit_cvar99_eur:,.0f} EUR)."
    )

    # The recommended DSRA covers the Clayton tail, so it exceeds the 6-month covenant.
    assert results.dsra_standard_6m == pytest.approx(13_823.82, abs=0.01)
    assert results.dsra_standard_12m == pytest.approx(27_647.64, abs=0.01)
    assert results.dsra_recommended_tail >= results.dsra_standard_6m
    assert results.annual_debt_service_y2 == pytest.approx(27_647.64, abs=0.01)


def test_credit_committee_memo_structure_and_no_em_dashes():
    memo_gen = CreditCommitteeMemo()
    memo_text = memo_gen.generate_markdown_report()

    assert "# BANK CREDIT COMMITTEE UNDERWRITING MEMORANDUM" in memo_text
    assert "**Facility Reference:** CRE-SME-2026-CASTRILLO-001" in memo_text
    assert "Executive summary and facility terms" in memo_text
    assert "Solvency, coverage and break-even profile" in memo_text
    assert "Copula tail risk on the Year-2 DSCR" in memo_text
    assert "DSRA sizing and liquidity structure" in memo_text
    assert "Credit committee decision and conditions" in memo_text
    assert "DECLINE AS STRUCTURED (RESIZE REQUIRED)" in memo_text

    # The memo must disclose the plug and the DSCR cap, not hide them.
    assert "521,090.22" in memo_text
    assert "49.6% of CapEx" in memo_text
    assert "339,144.92" in memo_text

    # Strict compliance: zero em dashes allowed.
    assert "\u2014" not in memo_text, "Em dashes are strictly forbidden in Credit Committee Memorandum."

    assert memo_gen.recommendation == "DECLINE AS STRUCTURED (RESIZE REQUIRED)"
    assert memo_gen.cash_equity == pytest.approx(521_090.22, abs=0.01)
    assert memo_gen.equity_to_capex == pytest.approx(49.6229, abs=1e-3)
