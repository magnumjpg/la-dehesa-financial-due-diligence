"""
Unit tests for the core financial model engine.
Validates:
- French loan amortization math and balance convergence to zero.
- VAT and Corporate Income Tax shield calculations.
- Three-statement accounting reconciliation: Assets == Liabilities + Equity.
- DSCR, ICR and break-even calculations.
"""

import pytest
import pandas as pd
from src.core.debt import DebtAmortizationEngine
from src.core.tax import VATEngine, CorporateTaxEngine
from src.core.statements import FinancialModelEngine
from src.core.metrics import CreditMetricsEngine, calculate_irr, calculate_npv
from src.config.assumptions import SCENARIOS


def test_french_debt_amortization_schedule():
    engine = DebtAmortizationEngine(principal=507_500.0, annual_interest_rate=0.035, tenure_years=15)
    monthly_df = engine.get_monthly_schedule_df()
    annual_df = engine.get_annual_schedule_df()

    assert len(monthly_df) == 180
    assert len(annual_df) == 15

    # Check beginning balance
    assert monthly_df.iloc[0]["beginning_balance"] == 507_500.0
    # Final ending balance must be 0
    assert monthly_df.iloc[-1]["ending_balance"] == 0.0

    # Total principal repaid must equal initial loan principal
    total_principal_repaid = round(annual_df["principal"].sum(), 2)
    assert total_principal_repaid == 507_500.0

    # Every period: payment == principal + interest (within rounding)
    for _, row in monthly_df.iterrows():
        assert row["payment"] == pytest.approx(row["principal"] + row["interest"], abs=0.02)


def test_vat_engine_calculations():
    vat = VATEngine(vat_hospitality_rate=0.10, vat_general_rate=0.21)

    # Year 1: High CapEx of 729k generates heavy input VAT
    y1_vat = vat.calculate_annual_vat_settlement(
        year=1,
        revenue_lodging=60_000.0,
        revenue_restaurant=30_000.0,
        capex_expenditure=729_000.0,
        taxable_opex=15_000.0,
    )

    # Output VAT: (60k + 30k) * 10% = 9.000 €
    assert y1_vat["total_output_vat"] == 9_000.0
    # Input VAT: 729k * 21% + 15k * 21% = 153.090 + 3.150 = 156.240 €
    assert y1_vat["total_input_vat"] == 156_240.0
    # Net refund requested: 156.240 - 9.000 = 147.240 €
    assert y1_vat["refund_due"] == 147_240.0
    assert y1_vat["vat_payable"] == 0.0


def test_corporate_tax_bins_carryforward():
    tax = CorporateTaxEngine(cit_rate=0.25)

    # Year 1 loss: -20.000 € -> 0 tax, 20.000 € BINs
    t1 = tax.calculate_tax(year=1, ebt=-20_000.0)
    assert t1["tax_expense"] == 0.0
    assert t1["closing_bins"] == 20_000.0
    assert t1["deferred_tax_asset"] == 5_000.0

    # Year 2 small profit: +8.000 € -> compensated with BINs, 0 tax, 12.000 € remaining
    t2 = tax.calculate_tax(year=2, ebt=8_000.0)
    assert t2["tax_expense"] == 0.0
    assert t2["applied_bins"] == 8_000.0
    assert t2["closing_bins"] == 12_000.0

    # Year 3 profit: +25.000 € -> 12.000 € BINs applied, 13.000 € taxable base, 3.250 € tax
    t3 = tax.calculate_tax(year=3, ebt=25_000.0)
    assert t3["applied_bins"] == 12_000.0
    assert t3["taxable_base"] == 13_000.0
    assert t3["tax_expense"] == 3_250.0
    assert t3["closing_bins"] == 0.0


def test_three_statement_projection_and_balance_sheet_equality():
    engine = FinancialModelEngine(scenario=SCENARIOS["base"])
    df = engine.run_projection(projection_years=5)

    assert len(df) == 5

    # Check Balance Sheet discrepancy is 0 (Assets == Liabilities + Equity)
    # Allows minor rounding tolerance <= 0.05 € across 5 years of compound flows
    for _, row in df.iterrows():
        assert abs(row["balance_sheet_discrepancy"]) <= 0.05, (
            f"Year {row['year']} balance sheet out of balance by {row['balance_sheet_discrepancy']} €"
        )

    # Net PPE decreases linearly with depreciation
    assert df.iloc[0]["net_ppe"] > df.iloc[4]["net_ppe"]

    # Cash balance remains strictly positive
    assert all(c > 0 for c in df["ending_cash"])


def test_credit_metrics_and_dscr():
    engine = FinancialModelEngine(scenario=SCENARIOS["base"])
    df_proj = engine.run_projection(projection_years=5)
    debt_sched = engine.debt_engine.get_annual_schedule_df()

    credit_engine = CreditMetricsEngine(target_dscr=1.25)
    df_kpi = credit_engine.compute_credit_kpis(df_proj, debt_sched)

    assert "dscr" in df_kpi.columns
    assert "icr" in df_kpi.columns

    # As revenues ramp up from Year 1 to Year 3, DSCR expands
    assert df_kpi.iloc[2]["dscr"] > df_kpi.iloc[0]["dscr"]

    # Test returns calculation
    returns = credit_engine.compute_returns_summary(df_proj)
    assert returns["discount_wacc"] == 0.08
    assert returns["equity_irr"] is not None


def test_breakeven_occupancy_analysis():
    credit_engine = CreditMetricsEngine(target_dscr=1.25)
    # Example operational cost: 71.034 € fixed opex + labor
    be = credit_engine.compute_breakeven_occupancy(
        fixed_costs_annual=71_034.0,
        debt_service_annual=43_500.0,
        daily_revenue_at_100_occ=1_600.0,
        cogs_ratio=0.15,
    )

    assert 0.10 <= be["operating_breakeven_occupancy"] <= 0.25
    assert be["debt_service_breakeven_occupancy"] > be["operating_breakeven_occupancy"]
    assert be["bank_covenant_breakeven_occupancy"] > be["debt_service_breakeven_occupancy"]
