"""
Unit tests for institutional assumptions and data configuration.
Validates financial identities, collective bargaining schedules, and tax rules.
"""

import pytest
from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    LaborStructure,
    FixedOpexStructure,
    SCENARIOS,
)
from src.config.ine_weights import (
    SEGOVIA_INE_MONTHLY,
    get_annual_weighted_occupancy,
    get_market_occupancy,
    get_excel_original_seasonality,
)
from src.data.extract_raw import extract_raw_excel_data, generate_reconciliation_summary


def test_capex_accounting_identity():
    capex = CapExStructure()
    assert capex.total_base_capex == 840_000.0  # land + works + biopool
    assert capex.total_capex == 1_050_100.0
    assert capex.land.amount == 250_000.0
    assert capex.renovation.amount == 550_000.0
    assert capex.kitchen_equipment.amount == 55_000.0
    assert capex.ffe.amount == 65_000.0
    assert capex.biopool_landscaping.amount == 40_000.0
    assert capex.digitalization.amount == 12_000.0
    assert capex.professional_fees.amount == 42_600.0
    assert capex.contingency.amount == 35_500.0
    assert not capex.land.is_depreciable
    assert capex.renovation.is_depreciable

    # The promoter case must keep the original EUR 725k budget (no kitchen/FF&E).
    promoter = CapExStructure.original_promoter()
    assert promoter.total_capex == 725_000.0
    assert promoter.renovation.amount == 440_000.0
    assert promoter.biopool_landscaping.amount == 35_000.0


def test_vat_tax_credit_identity():
    capex = CapExStructure()
    # 21% input VAT only on non-land CapEx: (1,050,100 - 250,000) * 21% = 168,021.
    assert capex.total_input_vat == 168_021.0
    assert capex.total_input_vat == pytest.approx((capex.total_capex - capex.land.amount) * 0.21, abs=0.01)

    # Annual linear tax depreciation (Ley 27/2014):
    # Works 3% = 16,500; kitchen 12% = 6,600; FF&E 10% = 6,500;
    # biopool 10% = 4,000; digital 25% = 3,000; fees 3% = 1,278; contingency 3% = 1,065.
    assert capex.annual_depreciation == 38_943.0
    assert capex.annual_depreciation == pytest.approx(
        550_000 * 0.03
        + 55_000 * 0.12
        + 65_000 * 0.10
        + 40_000 * 0.10
        + 12_000 * 0.25
        + 42_600 * 0.03
        + 35_500 * 0.03,
        abs=0.01,
    )

    # The promoter budget keeps the original 21% on its non-land base.
    assert CapExStructure.original_promoter().total_input_vat == 99_750.0


def test_capital_structure_ratios():
    fin = FinancingStructure()
    # The 70/30 split is the *requested* structure, not the funded one: the cash
    # equity plug is computed from sources & uses (49.62% of CapEx).
    assert fin.debt_share == 0.35
    assert fin.equity_share == 0.30
    assert fin.senior_debt_principal == 367_535.0
    assert fin.sponsor_equity == 315_030.0
    assert fin.land_in_kind is True
    assert fin.land_in_kind_value == 250_000.0
    assert fin.total_equity_at_close == 565_030.0  # base 30% + land, before the plug

    # Construction IDC: 367,535 * 4.0% * 12/12.
    assert fin.idc_amount == 14_701.40

    assert fin.loan_interest_rate == 0.04
    assert fin.loan_tenure_years == 20
    assert fin.grace_months == 12
    assert fin.target_dscr == 1.25
    assert fin.credit_line_limit == 175_000.0
    assert fin.vat_bridge_limit == 175_000.0
    assert fin.leader_subsidy_amount == 163_000.0


def test_segovia_collective_agreement_labor_costs():
    labor = LaborStructure()
    # Cook 1 & 2: 13,500 * 1.35 = 18,225 each; cleaner 17,500 * 1.35 = 23,625.
    assert labor.total_annual_payroll == 60_075.0
    assert FixedOpexStructure().total_fixed_opex == 30_500.0


def test_ine_seasonality_properties():
    assert len(SEGOVIA_INE_MONTHLY) == 12
    total_days = sum(m.days_in_month for m in SEGOVIA_INE_MONTHLY)
    assert total_days == 365

    annual_occ = get_annual_weighted_occupancy(SEGOVIA_INE_MONTHLY)
    assert 0.25 <= annual_occ <= 0.40  # Realistic Segovia high-end range
    assert get_annual_weighted_occupancy() == pytest.approx(0.3136, abs=0.0001)
    assert get_market_occupancy() == pytest.approx(0.2124, abs=0.0001)

    excel_base = get_excel_original_seasonality()
    assert excel_base["total_occupied_days"] == pytest.approx(66.325, 0.001)
    assert excel_base["weighted_occupancy"] == pytest.approx(66.325 / 365, 0.001)


def test_scenarios_configured():
    assert "conservative" in SCENARIOS
    assert "base" in SCENARIOS
    assert "optimistic" in SCENARIOS

    cons = SCENARIOS["conservative"]
    assert cons.occupancy_multiplier < 1.0
    assert cons.interest_rate_delta > 0.0


def test_raw_excel_extraction_integrity():
    data = extract_raw_excel_data()
    assert data["capex_base"]["total_capex"] == 725_000.0
    assert data["segovia_labor"]["total_payroll"] == 60_075.0
    assert data["vat_comparison"]["cash_balance_y1_delta"] == 213_000.0

    df_summary = generate_reconciliation_summary()
    assert len(df_summary) == 11
    assert list(df_summary.columns) == [
        "Category",
        "Original Excel",
        "Refined: mgmt / market / promoter",
        "Notes",
    ]

    by_cat = {r["Category"]: r for _, r in df_summary.iterrows()}
    assert "31.36% / 21.24% / 19.20%" in by_cat["Occupancy (mature)"]["Refined: mgmt / market / promoter"]
    assert "154,548" in by_cat["Year 1 revenue"]["Refined: mgmt / market / promoter"]
    assert "24,280" in by_cat["Year 1 EBITDA"]["Refined: mgmt / market / promoter"]
    assert "20,701" in by_cat["Year 1 ending cash"]["Refined: mgmt / market / promoter"]
    assert "1.34x / -1.46x / 0.33x" in by_cat["Year 1 DSCR"]["Refined: mgmt / market / promoter"]
    assert "1,050,100" in by_cat["All-in CapEx"]["Refined: mgmt / market / promoter"]
    assert "168,021" in by_cat["Input VAT on CapEx"]["Refined: mgmt / market / promoter"]
    assert "771,090" in by_cat["Equity at close"]["Refined: mgmt / market / promoter"]
    assert "0.00" in by_cat["Balance sheet"]["Refined: mgmt / market / promoter"]

    # The old "VAT paper trap" and "solvency confirmed" claims must be gone.
    text = df_summary.to_string()
    assert "Flawed standard" not in text
    assert "Solvency confirmed" not in text
    assert "74,851 net / 99,488 gross" in text
    assert "96,628 with no build-up" in text
    assert "729,000" not in text
