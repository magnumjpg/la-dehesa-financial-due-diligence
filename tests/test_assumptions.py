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
    RevenueModelConfig,
    SCENARIOS,
)
from src.config.ine_weights import (
    SEGOVIA_INE_MONTHLY,
    get_annual_weighted_occupancy,
    get_excel_original_seasonality,
)
from src.data.extract_raw import extract_raw_excel_data, generate_reconciliation_summary


def test_capex_accounting_identity():
    capex = CapExStructure()
    assert capex.total_base_capex == 725_000.0
    assert capex.total_capex == 729_000.0
    assert capex.land.amount == 250_000.0
    assert capex.renovation.amount == 440_000.0
    assert capex.biopool_landscaping.amount == 35_000.0
    assert capex.digitalization.amount == 4_000.0
    assert not capex.land.is_depreciable
    assert capex.renovation.is_depreciable


def test_vat_tax_credit_identity():
    capex = CapExStructure()
    # 21% input VAT on 725.000 € is 152.250 €
    assert capex.total_base_capex * 0.21 == 152_250.0
    # Annual linear tax depreciation
    # Renovation: 440.000 * 3% = 13.200 €
    # Biopool: 35.000 * 10% = 3.500 €
    # Digitalization: 4.000 * 25% = 1.000 €
    assert capex.annual_depreciation == (13_200.0 + 3_500.0 + 1_000.0)


def test_capital_structure_ratios():
    fin = FinancingStructure()
    assert fin.debt_share + fin.equity_share == 1.0
    assert fin.senior_debt_principal == 507_500.0
    assert fin.sponsor_equity == 217_500.0
    assert fin.target_dscr >= 1.25


def test_segovia_collective_agreement_labor_costs():
    labor = LaborStructure()
    # Cook 1 & 2: 13.500 * 1.35 = 18.225 € each
    # Cleaner: 17.500 * 1.35 = 23.625 €
    # Total = 18.225 * 2 + 23.625 = 60.075 €
    assert labor.total_annual_payroll == 60_075.0


def test_ine_seasonality_properties():
    assert len(SEGOVIA_INE_MONTHLY) == 12
    total_days = sum(m.days_in_month for m in SEGOVIA_INE_MONTHLY)
    assert total_days == 365

    annual_occ = get_annual_weighted_occupancy(SEGOVIA_INE_MONTHLY)
    assert 0.25 <= annual_occ <= 0.40  # Realistic Segovia high-end range

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
    assert len(df_summary) == 10
    assert list(df_summary.columns) == [
        "Category",
        "Original Excel",
        "Refined: mgmt / market / promoter",
        "Notes",
    ]

    by_cat = {r["Category"]: r for _, r in df_summary.iterrows()}
    assert "31.36% / 21.24% / 19.20%" in by_cat["Occupancy (mature)"]["Refined: mgmt / market / promoter"]
    assert "154,548" in by_cat["Year 1 revenue"]["Refined: mgmt / market / promoter"]
    assert "66,086" in by_cat["Year 1 EBITDA"]["Refined: mgmt / market / promoter"]
    assert "-2,553" in by_cat["Year 1 ending cash"]["Refined: mgmt / market / promoter"]
    assert "1.34x / 0.40x / 0.33x" in by_cat["Year 1 DSCR"]["Refined: mgmt / market / promoter"]
    assert "0.00" in by_cat["Balance sheet"]["Refined: mgmt / market / promoter"]

    # The old "VAT paper trap" and "solvency confirmed" claims must be gone.
    text = df_summary.to_string()
    assert "Flawed standard" not in text
    assert "Solvency confirmed" not in text
    assert "did not apply 21%" in text
