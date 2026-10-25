"""
Honesty audit of the promoter case against the two source workbooks.

The promoter case is a re-modelling calibrated to the presentation headline
(EUR 86,275 revenue / EUR 11,297 EBITDA), not a replication. This file pins the
arithmetic behind that statement so the documentation cannot drift:

* the source contains four mutually inconsistent Year-1 revenues;
* both summary sheets are entirely hard-coded, so the EUR 11,297 EBITDA has no
  build-up anywhere in the workbooks;
* the model's own EBITDA is the deck figure by construction, and it prices
  restaurant covers at EUR 20 while costing them at EUR 25.
"""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from src.config.assumptions import SCENARIOS
from src.core.statements import FinancialModelEngine

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "raw_data" / "La_Dehesa_de_Castrillo_Proyecto.xlsx"
DECK = ROOT / "raw_data" / "Presentacion_La_Dehesa.xlsx"


def _formula_cells(sheet):
    return [
        cell.coordinate
        for row in sheet.iter_rows()
        for cell in row
        if isinstance(cell.value, str) and cell.value.startswith("=")
    ]


def test_source_contains_four_inconsistent_year_one_revenues():
    plan_values = load_workbook(PLAN, data_only=True)
    plan_formulas = load_workbook(PLAN, data_only=False)
    deck_values = load_workbook(DECK, data_only=True)

    # 1. Hard-coded net revenue in the conclusions sheet.
    assert plan_values["Conclusiones y Viabilidad"]["B5"].value == 74_851

    # 2. The formula sheet builds a different, gross figure from 66.325
    #    occupied days (90 * 42% + 80 * 32% + 195 * 1.5%).
    occupied_days = 90 * 0.42 + 80 * 0.32 + 195 * 0.015
    assert occupied_days == pytest.approx(66.325)
    plan = plan_formulas["Plan de Negocio"]
    assert plan["B41"].value == "=SUM(B38:B40)"
    assert plan["B19"].value == 25  # restaurant ticket in the source
    assert plan["B20"].value == 0.3
    gross_formula_build = (
        occupied_days * 7 * 85
        + occupied_days * 380
        + (occupied_days * 7 * 2 + occupied_days * 7) * 25
    )
    assert gross_formula_build == pytest.approx(99_487.50)

    # 3. The deck's revenue is a literal.
    assert deck_values["Tablas para PPT"]["B11"].value == 96_628
    assert deck_values["Tablas para PPT"]["B12"].value == 11_297

    # 4. The EUR 74,851 net figure is the 90,570 gross build divided by 1.21.
    promoter_gross = 491 * 85 + 72 * 380 + 859 * 25
    assert promoter_gross == 90_570
    assert promoter_gross / 1.21 == pytest.approx(74_851, abs=1)
    assert promoter_gross / 1.10 == pytest.approx(82_336.36, abs=0.01)

    # Four source readings of the same year, no two of which agree: the two
    # formula-sheet/net figures, the gross build behind the net figure, and the
    # deck literal. Restating the 90,570 gross at 10% adds a fifth number.
    source_readings = {74_851, 99_487.50, 96_628, 90_570}
    assert len(source_readings) == 4
    assert 82_336.36 not in source_readings


def test_both_summary_sheets_are_entirely_hard_coded():
    plan = load_workbook(PLAN, data_only=False)
    deck = load_workbook(DECK, data_only=False)

    assert _formula_cells(plan["Conclusiones y Viabilidad"]) == []
    assert _formula_cells(deck["Tablas para PPT"]) == []
    # Only the Plan de Negocio sheet carries live formulas.
    assert _formula_cells(plan["Plan de Negocio"])


def test_promoter_case_is_a_remodelling_not_a_replication():
    engine = FinancialModelEngine(case="promoter", scenario=SCENARIOS["base"])
    revenue = engine.calculate_revenue_for_year(1)

    # Revenue: the deck figure, but with a EUR 20 ticket, not the source's 25.
    assert engine.rev_cfg.promoter_restaurant_ticket == 20.0
    assert revenue["rev_restaurant"] == pytest.approx(859 * 20, abs=0.01)
    assert revenue["total_revenue"] == pytest.approx(86_275.00, abs=0.01)

    # EBITDA: 86,275 - 60,075 realistic payroll - 14,903 other opex.
    assert engine.labor.total_annual_payroll == pytest.approx(60_075.00)
    assert engine.opex.total_fixed_opex == pytest.approx(14_903.00)
    assert engine.opex.purchases == pytest.approx(6_444.00)
    assert 86_275 - 60_075 - 14_903 == 11_297

    # The purchases line is costed at the EUR 25 ticket while revenue prices
    # the same covers at EUR 20. The EUR 1.50 gap is rounding in the source.
    assert 859 * 25 * 0.30 == pytest.approx(6_444, abs=1.5)


def test_the_deck_pair_cannot_be_reproduced_from_the_source_formula_sheet():
    # The source's own P&L produces 26,701.31, not 11,297.
    source_ebitda = (
        99_487.50
        - 10_446.19  # 30% of the 34,820.63 F&B revenue
        - 62_340.00  # 35,640 + 23,100 payroll + 3,600 maintenance
    )
    assert source_ebitda == pytest.approx(26_701.31, abs=0.01)

    # The deck's revenue is not any of the figures the source can build.
    for candidate in (74_851, 99_487.50, 82_336.36, 90_570, 86_275):
        assert abs(candidate - 96_628) > 1


def test_the_19_2_percent_occupancy_is_implied_not_quoted():
    # 491 room-nights over seven rooms is 19.22% of the year, which is where
    # the case's occupancy comes from. Neither workbook stores 19.2%.
    assert 491 / 7 / 365 == pytest.approx(0.1922, abs=0.0001)
    assert 66.325 / 365 == pytest.approx(0.1817, abs=0.0001)

    for path in (PLAN, DECK):
        wb = load_workbook(path, data_only=True)
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    value = cell.value
                    if isinstance(value, (int, float)):
                        assert abs(float(value) - 0.192) > 0.0005, f"{path.name}!{ws.title}!{cell.coordinate}"
                    elif isinstance(value, str):
                        assert "19,2" not in value
                        assert "19.2" not in value
