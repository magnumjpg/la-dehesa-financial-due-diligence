"""
Three-case tests: management (upside), INE market, and promoter (original).

The management case is the headline Python case, but it is not the base case.
The market case uses the official INE Segovia occupancy, and the promoter case
is re-modelled to the presentation headline (EUR 86,275 / EUR 11,297).
"""

import pytest

from src.config.assumptions import SCENARIOS
from src.core.metrics import CreditMetricsEngine
from src.core.statements import FinancialModelEngine


def _case(case: str):
    engine = FinancialModelEngine(case=case, scenario=SCENARIOS["base"])
    df = engine.run_projection(5)
    debt = engine.debt_engine.get_annual_schedule_df()
    credit = CreditMetricsEngine()
    kpi = credit.compute_credit_kpis(df, debt)
    returns = credit.compute_returns_summary(
        df,
        initial_equity=engine.total_equity_at_close,
        initial_capex=engine.total_project_investment,
        exit_cap_rate=0.085,
    )
    return engine, df, kpi, returns


def test_management_case_is_the_upside():
    engine, df, kpi, returns = _case("management")
    y1 = kpi.iloc[0]

    assert y1["total_revenue"] == 154_548.00
    assert y1["ebitda"] == 24_279.92
    assert y1["cfads"] == 19_643.48
    assert y1["dscr"] == 1.34
    assert y1["ending_cash"] == 20_700.88
    assert kpi["balance_sheet_discrepancy"].abs().max() == 0.0

    # The covenant binds in the first amortising year and never recovers.
    assert kpi.iloc[1]["dscr"] == 1.15
    assert kpi["dscr"].min() == 1.15

    # A realistic 20-year/4% structure plus the full cost stack means the
    # project does not earn its cost of capital, even with an 8.5% exit.
    assert returns["project_irr"] == pytest.approx(-0.354319, abs=1e-5)
    assert returns["project_irr_exit"] == pytest.approx(-0.094874, abs=1e-5)
    assert returns["equity_irr_exit"] == pytest.approx(-0.231566, abs=1e-5)
    assert returns["terminal_value"] == pytest.approx(435_783.29, abs=0.01)
    assert returns["project_npv"] < 0

    assert engine.cash_equity == pytest.approx(521_090.22, abs=0.01)
    assert engine.total_equity_at_close == pytest.approx(771_090.22, abs=0.01)
    assert engine.total_project_investment == pytest.approx(1_138_625.22, abs=0.01)


def test_market_case_does_not_cover_debt_service_in_year_one():
    engine, df, kpi, returns = _case("market")
    y1 = kpi.iloc[0]

    assert y1["total_revenue"] == 95_555.00
    assert y1["ebitda"] == -18_565.58
    assert y1["cfads"] == -21_432.23
    assert y1["dscr"] == -1.46
    assert y1["ending_cash"] == 15_000.00
    assert kpi["balance_sheet_discrepancy"].abs().max() == 0.0

    # The original 1.25x / 1.20x volume ramp eventually reaches 32% in Year 3,
    # but DSCR never clears 1.00x within the five-year horizon.
    assert kpi["dscr"].max() == 0.86
    assert returns["project_irr"] < 0
    assert returns["project_irr_exit"] == pytest.approx(-0.151813, abs=1e-5)
    assert returns["equity_irr_exit"] == pytest.approx(-0.502186, abs=1e-5)

    assert engine.cash_equity == pytest.approx(556_465.05, abs=0.01)
    assert engine.total_equity_at_close == pytest.approx(806_465.05, abs=0.01)


def test_promoter_case_lands_on_the_presentation_headline():
    engine, df, kpi, returns = _case("promoter")
    y1 = kpi.iloc[0]

    # The presentation hard-codes EUR 86,275 revenue and EUR 11,297 EBITDA.
    # Neither is a formula output in the source; the case reproduces them.
    assert y1["total_revenue"] == 86_275.00
    assert y1["ebitda"] == 11_297.00
    assert y1["cfads"] == 11_297.00
    assert y1["dscr"] == 0.33
    assert y1["ending_cash"] == pytest.approx(-8_039.45, abs=0.01)
    assert kpi["balance_sheet_discrepancy"].abs().max() == 0.0

    # The promoter case uses the original 4.5% / 25-year debt, no grant and the
    # original EUR 725k cost base (land purchased, not contributed in kind).
    assert engine.financing.loan_interest_rate == 0.045
    assert engine.financing.loan_tenure_years == 25
    assert engine.financing.grace_months == 0
    assert engine.financing.leader_subsidy_amount == 0.0
    assert engine.capex.total_capex == 725_000.0
    assert engine.total_equity_at_close == 217_500.0
    assert engine.dsra_amount == 0.0

    # It only clears DSCR from Year 3, and only with an 8.5% exit does the
    # equity return become positive.
    assert kpi.iloc[2]["dscr"] > 1.25
    assert returns["project_irr"] < 0
    assert returns["project_irr_exit"] == pytest.approx(0.06838, abs=1e-5)
    assert returns["equity_irr_exit"] == pytest.approx(0.121235, abs=1e-5)


def test_no_case_recovers_capex_without_an_exit():
    for case in ("management", "market", "promoter"):
        _, _, _, returns = _case(case)
        assert returns["project_irr"] < 0, case

    # Only the original promoter case clears an 8.5% exit; the realistic cases
    # do not, which is the central due-diligence finding.
    promoter_returns = _case("promoter")[3]
    assert promoter_returns["project_irr_exit"] > 0
    assert _case("management")[3]["project_irr_exit"] < 0
    assert _case("market")[3]["project_irr_exit"] < 0
