"""
Three-case tests: management (upside), INE market, and promoter (original).

The management case is the headline Python case, but it is not the base case.
The market case uses the official INE Segovia occupancy, and the promoter case
replicates the author's original university Excel.
"""

import pytest

from src.config.assumptions import SCENARIOS
from src.core.metrics import CreditMetricsEngine
from src.core.statements import FinancialModelEngine


def _case(case: str):
    engine = FinancialModelEngine(case=case, scenario=SCENARIOS["base"])
    df = engine.run_projection(5)
    debt = engine.debt_engine.get_annual_schedule_df()
    kpi = CreditMetricsEngine().compute_credit_kpis(df, debt)
    returns = CreditMetricsEngine().compute_returns_summary(
        df,
        initial_equity=engine.financing.sponsor_equity,
        initial_capex=engine.capex.total_capex,
        exit_cap_rate=0.085,
    )
    return engine, df, kpi, returns


def test_management_case_is_the_upside():
    engine, df, kpi, returns = _case("management")
    y1 = kpi.iloc[0]

    assert y1["total_revenue"] == 154_548.00
    assert y1["ebitda"] == 66_086.46
    assert y1["dscr"] == 1.34
    assert y1["ending_cash"] == 10_789.74
    assert kpi["balance_sheet_discrepancy"].abs().max() == 0.0

    assert returns["project_irr"] == pytest.approx(-0.20892, abs=1e-5)
    assert returns["project_irr_exit"] == pytest.approx(0.154291, abs=1e-5)
    assert returns["equity_irr_exit"] == pytest.approx(0.297382, abs=1e-5)
    assert returns["terminal_value"] == pytest.approx(1_048_704.35, abs=0.01)


def test_market_case_does_not_cover_debt_service_in_year_one():
    engine, df, kpi, returns = _case("market")
    y1 = kpi.iloc[0]

    assert y1["total_revenue"] == 95_555.00
    assert y1["ebitda"] == 17_621.00
    assert y1["dscr"] == 0.40
    assert y1["ending_cash"] == -29_915.36
    assert kpi["balance_sheet_discrepancy"].abs().max() == 0.0

    assert returns["project_irr"] < 0
    assert returns["project_irr_exit"] == pytest.approx(0.096319, abs=1e-5)
    assert returns["equity_irr_exit"] == pytest.approx(0.174276, abs=1e-5)


def test_promoter_case_replicates_the_original_excel():
    engine, df, kpi, returns = _case("promoter")
    y1 = kpi.iloc[0]

    # The original Excel reports €86,275 revenue, €11,297 EBITDA and about
    # -€2,560 of Year 1 cash.
    assert y1["total_revenue"] == 86_275.00
    assert y1["ebitda"] == 11_297.00
    assert y1["dscr"] == 0.33
    assert abs(y1["ending_cash"] - (-2_560.00)) < 10.0
    assert kpi["balance_sheet_discrepancy"].abs().max() == 0.0

    # The promoter case uses 4.5% / 25-year debt and no LEADER grant.
    assert engine.financing.loan_interest_rate == 0.045
    assert engine.financing.loan_tenure_years == 25
    assert engine.financing.leader_subsidy_amount == 0.0

    assert returns["project_irr"] < 0
    assert returns["project_irr_exit"] == pytest.approx(0.06838, abs=1e-5)
    assert returns["equity_irr_exit"] == pytest.approx(0.109467, abs=1e-5)


def test_no_case_recovers_capex_without_an_exit():
    for case in ("management", "market", "promoter"):
        _, _, _, returns = _case(case)
        assert returns["project_irr"] < 0, case
        assert returns["project_irr_exit"] > 0, case
