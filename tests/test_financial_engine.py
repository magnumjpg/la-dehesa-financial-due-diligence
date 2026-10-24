"""
Unit tests for the core financial model engine.
Validates:
- French loan amortization with a 12-month grace period and zero convergence.
- VAT and Corporate Income Tax shield calculations.
- Three-statement accounting reconciliation: Assets == Liabilities + Equity.
- DSCR, ICR and break-even calculations on the realistic 20-year structure.
"""

import pytest

from src.core.debt import DebtAmortizationEngine
from src.core.tax import VATEngine, CorporateTaxEngine
from src.core.statements import FinancialModelEngine
from src.core.metrics import CreditMetricsEngine, BreakEvenEngine
from src.config.assumptions import SCENARIOS


def test_french_debt_amortization_schedule():
    engine = DebtAmortizationEngine(
        principal=367_535.0,
        annual_interest_rate=0.04,
        tenure_years=20,
        grace_months=12,
    )
    monthly_df = engine.get_monthly_schedule_df()
    annual_df = engine.get_annual_schedule_df()

    assert len(monthly_df) == 240
    assert len(annual_df) == 20

    assert monthly_df.iloc[0]["beginning_balance"] == 367_535.0
    assert monthly_df.iloc[-1]["ending_balance"] == 0.0

    total_principal_repaid = round(annual_df["principal"].sum(), 2)
    assert total_principal_repaid == 367_535.0

    # Year 1 is interest-only (12-month grace): 367,535 * 4.0% = 14,701.44.
    assert annual_df.iloc[0]["payment"] == pytest.approx(14_701.44, abs=0.01)
    assert annual_df.iloc[0]["principal"] == pytest.approx(0.0, abs=0.01)
    # Year 2 is the first amortising year: 12 x 2,303.97 = 27,647.64.
    assert annual_df.iloc[1]["payment"] == pytest.approx(27_647.64, abs=0.01)
    assert annual_df.iloc[1]["principal"] == pytest.approx(13_186.24, abs=0.01)
    assert annual_df.iloc[1]["interest"] == pytest.approx(14_461.40, abs=0.01)

    for _, row in monthly_df.iterrows():
        assert row["payment"] == pytest.approx(row["principal"] + row["interest"], abs=0.02)


def test_vat_engine_calculations():
    vat = VATEngine(vat_hospitality_rate=0.10, vat_general_rate=0.21)

    # Year 1: heavy CapEx generates input VAT that is refundable.
    y1_vat = vat.calculate_annual_vat_settlement(
        year=1,
        revenue_lodging=60_000.0,
        revenue_restaurant=30_000.0,
        capex_expenditure=800_100.0,
        taxable_opex=15_000.0,
    )

    # Output VAT: (60k + 30k) * 10% = 9,000.
    assert y1_vat["total_output_vat"] == 9_000.0
    # Input VAT: 800,100 * 21% + 15,000 * 21% = 168,021 + 3,150 = 171,171.
    assert y1_vat["total_input_vat"] == 171_171.0
    assert y1_vat["refund_due"] == 162_171.0
    assert y1_vat["vat_payable"] == 0.0


def test_corporate_tax_bins_carryforward():
    tax = CorporateTaxEngine(cit_rate=0.25)

    t1 = tax.calculate_tax(year=1, ebt=-20_000.0)
    assert t1["tax_expense"] == 0.0
    assert t1["closing_bins"] == 20_000.0
    assert t1["deferred_tax_asset"] == 5_000.0

    t2 = tax.calculate_tax(year=2, ebt=8_000.0)
    assert t2["tax_expense"] == 0.0
    assert t2["applied_bins"] == 8_000.0
    assert t2["closing_bins"] == 12_000.0

    t3 = tax.calculate_tax(year=3, ebt=25_000.0)
    assert t3["applied_bins"] == 12_000.0
    assert t3["taxable_base"] == 13_000.0
    assert t3["tax_expense"] == 3_250.0
    assert t3["closing_bins"] == 0.0


def test_three_statement_projection_and_balance_sheet_equality():
    engine = FinancialModelEngine(case="management", scenario=SCENARIOS["base"])
    df = engine.run_projection(projection_years=5)

    assert len(df) == 5

    for _, row in df.iterrows():
        assert abs(row["balance_sheet_discrepancy"]) <= 0.01, (
            f"Year {row['year']} balance sheet out of balance by {row['balance_sheet_discrepancy']}"
        )

    # Net PPE decreases linearly with depreciation.
    assert df.iloc[0]["net_ppe"] > df.iloc[4]["net_ppe"]

    # Cash stays positive in the management case; the market case is floored at
    # the EUR 15k minimum balance by the equity plug.
    assert all(c > 0 for c in df["ending_cash"])
    assert df.iloc[0]["ending_cash"] == pytest.approx(20_700.88, abs=0.01)


def test_credit_metrics_and_dscr():
    engine = FinancialModelEngine(case="management", scenario=SCENARIOS["base"])
    df_proj = engine.run_projection(projection_years=5)
    debt_sched = engine.debt_engine.get_annual_schedule_df()

    credit_engine = CreditMetricsEngine(target_dscr=1.25)
    df_kpi = credit_engine.compute_credit_kpis(df_proj, debt_sched)

    assert "dscr" in df_kpi.columns
    assert "icr" in df_kpi.columns

    # Year 1 is interest-only: DSCR 1.34x. The first amortising year (Year 2)
    # is the binding year at 1.15x, and it stays there because there is no
    # nominal ADR growth.
    assert df_kpi.iloc[0]["dscr"] == pytest.approx(1.34, abs=0.01)
    assert df_kpi.iloc[1]["dscr"] == pytest.approx(1.15, abs=0.01)
    assert df_kpi.iloc[2]["dscr"] == pytest.approx(1.15, abs=0.01)

    returns = credit_engine.compute_returns_summary(
        df_proj,
        initial_equity=engine.total_equity_at_close,
        initial_capex=engine.total_project_investment,
    )
    assert returns["discount_wacc"] == 0.08
    assert returns["equity_irr"] is not None
    assert returns["equity_irr_exit"] < 0


def test_breakeven_occupancy_analysis():
    be = BreakEvenEngine(case="management").compute()

    assert be["base_occupancy_mature"] == pytest.approx(0.3136, abs=0.0001)
    assert be["operating_breakeven_occupancy_mature"] == pytest.approx(0.2226, abs=0.001)
    assert be["debt_service_breakeven_occupancy_mature"] == pytest.approx(0.3028, abs=0.001)
    assert be["covenant_breakeven_occupancy_mature"] == pytest.approx(0.3205, abs=0.001)
    assert be["operating_breakeven_occupancy_mature"] < be["debt_service_breakeven_occupancy_mature"]
    assert be["debt_service_breakeven_occupancy_mature"] < be["covenant_breakeven_occupancy_mature"]
    assert be["covenant_breakeven_adr"] == pytest.approx(86.64, abs=0.01)
    assert be["equity_irr_10pct_adr"] == pytest.approx(116.36, abs=0.01)
