"""
Live, formula-driven Excel tabs for the La Dehesa del Castrillo model.

The original exporter wrote value-only report tabs (zero formulas). This module
adds four institutional tabs on top of the report pack:

1. Read Me & Checks  - model map, case definitions and key checks.
2. Inputs            - every hard-coded assumption in one place.
3. Live Model        - a formula-driven 5-year P&L, cash flow, debt and balance
                       sheet that replicates the Python management case.
4. Funding & Audit   - sources & uses, funding gap, Phase II gate and the
                       computed audit rules (including material exceptions).

The Live Model is intentionally transparent: the revenue formula is
365 * occupancy * (7 rooms * €85 + 1 house * €380 + 21 meals * €25), and the
cash flow is NI + D&A - CapEx - principal + grant. The VAT bridge is a
balance-sheet wash and is excluded from the simplified live cash flow; the
Python model includes it. The "Checks" block compares the live formulas with the
Python output and flags any difference above €1.
"""

from pathlib import Path
from typing import Any, Dict, List

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src.config.assumptions import SCENARIOS
from src.config.ine_weights import (
    get_annual_weighted_occupancy,
    get_market_occupancy,
    PROMOTER_OCCUPANCY,
)
from src.core.expansion import ExpansionFinancialEngine
from src.core.funding import SourcesUsesEngine
from src.core.model_audit import ModelAuditEngine
from src.core.statements import FinancialModelEngine


NAVY = "1E3A8A"
SLATE = "F1F5F9"
AMBER = "FEF3C7"
GREEN = "DCFCE7"
RED = "FEE2E2"


def _styles():
    navy_fill = PatternFill(start_color=NAVY, end_color=NAVY, fill_type="solid")
    slate_fill = PatternFill(start_color=SLATE, end_color=SLATE, fill_type="solid")
    amber_fill = PatternFill(start_color=AMBER, end_color=AMBER, fill_type="solid")
    green_fill = PatternFill(start_color=GREEN, end_color=GREEN, fill_type="solid")
    red_fill = PatternFill(start_color=RED, end_color=RED, fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color=NAVY)
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=11)
    note_font = Font(name="Calibri", size=10, italic=True, color="64748B")
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )
    return {
        "navy": navy_fill,
        "slate": slate_fill,
        "amber": amber_fill,
        "green": green_fill,
        "red": red_fill,
        "header": header_font,
        "title": title_font,
        "bold": bold_font,
        "regular": regular_font,
        "note": note_font,
        "border": thin_border,
    }


def _header_row(ws, row: int, headers: List[str], st: Dict[str, Any]) -> None:
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.fill = st["navy"]
        cell.font = st["header"]
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = st["border"]


def _write_row(ws, row: int, values: List[Any], st: Dict[str, Any], number_format: str = "#,##0.00") -> None:
    for col, v in enumerate(values, start=1):
        cell = ws.cell(row=row, column=col, value=v)
        cell.font = st["regular"]
        cell.border = st["border"]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            cell.number_format = number_format


def _status_formula(ws, row: int, col: int, condition: str, st: Dict[str, Any]) -> None:
    cell = ws.cell(row=row, column=col, value=f'=IF({condition},"PASS","FAIL")')
    cell.font = st["bold"]
    cell.border = st["border"]
    cell.alignment = Alignment(horizontal="center")


def build_readme(wb, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Read Me & Checks", index=0)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "LA DEHESA DEL CASTRILLO S.L. - MODEL MAP, CASES & INTEGRITY CHECKS"
    ws["A1"].font = st["title"]
    ws["A2"] = "This workbook contains a live, formula-driven management case plus the independent INE market case and the original promoter case."
    ws["A2"].font = st["note"]

    ws["A4"] = "1. MODEL MAP"
    ws["A4"].font = st["bold"]
    _header_row(ws, 5, ["Tab", "Purpose"], st)
    model_map = [
        ("Read Me & Checks", "This page: model map, case definitions and integrity checks."),
        ("Inputs", "All hard-coded assumptions (occupancy, ADR, payroll, CapEx, debt, tax, grant)."),
        ("Live Model", "Formula-driven 5-year P&L, cash flow, debt and balance sheet; replicates the Python management case."),
        ("Funding & Audit", "Sources & uses, funding gap, credit-line consistency, Phase II gate and computed audit rules."),
        ("Executive Scorecard", "One-page underwriting scorecard (management case)."),
        ("3-Statement Model", "Full Python output: P&L, cash flow and balance sheet."),
        ("Debt Schedule", "15-year French amortization schedule."),
        ("Scenario Stress-Testing", "Conservative / base / optimistic scenarios and 2D DSCR sensitivity."),
        ("Monte Carlo Risk", "1,000-iteration stochastic credit-risk simulation."),
        ("Credit Risk & Copula", "Gaussian / Student-t / Clayton tail-risk comparison."),
        ("Unit Economics & Runway", "RevPAR, TRevPAR, contribution margin and 24-month cash runway."),
        ("Phase II Expansion", "Landscape suites and biological pond: CapEx, P&L, returns and consolidated impact."),
    ]
    for r, (tab, purpose) in enumerate(model_map, start=6):
        _write_row(ws, r, [tab, purpose], st, number_format="@")
        ws.cell(row=r, column=1).font = st["bold"]

    ws["A19"] = "2. THREE CASES (DO NOT CONFUSE THEM)"
    ws["A19"].font = st["bold"]
    _header_row(ws, 20, ["Case", "Occupancy", "Revenue Y1", "EBITDA Y1", "DSCR Y1", "Use"], st)
    cases = [
        ("Management (upside)", f"{get_annual_weighted_occupancy()*100:.2f}%", 154_548.00, 66_086.46, 1.34, "Headline Python case; 1.48x the INE market average."),
        ("INE market", f"{get_market_occupancy()*100:.2f}%", 95_555.00, 17_621.00, 0.40, "Independent benchmark; does not cover debt service in Year 1."),
        ("Promoter (original Excel)", f"{PROMOTER_OCCUPANCY*100:.2f}%", 86_275.00, 11_297.00, 0.33, "Faithful replication of the original university simulator."),
    ]
    for r, row in enumerate(cases, start=21):
        _write_row(ws, r, list(row), st, number_format="#,##0.00")
        ws.cell(row=r, column=1).font = st["bold"]
        ws.cell(row=r, column=2).number_format = "0.00%"

    ws["A26"] = "3. KEY INTEGRITY CHECKS"
    ws["A26"].font = st["bold"]
    _header_row(ws, 27, ["Check", "Where", "Result"], st)
    checks = [
        ("Balance-sheet equality (Assets = Liabilities + Equity)", "Live Model!B33:F33", '=IF(MAX(ABS(\'Live Model\'!B33),ABS(\'Live Model\'!C33),ABS(\'Live Model\'!D33),ABS(\'Live Model\'!E33),ABS(\'Live Model\'!F33))<1,"PASS","FAIL")'),
        ("Live revenue vs. Python revenue (Year 1)", "Live Model!D37", '=IF(ABS(\'Live Model\'!D37)<1,"PASS","FAIL")'),
        ("Live EBITDA vs. Python EBITDA (Year 1)", "Live Model!D38", '=IF(ABS(\'Live Model\'!D38)<1,"PASS","FAIL")'),
        ("Live DSCR vs. Python DSCR (Year 1)", "Live Model!D39", '=IF(ABS(\'Live Model\'!D39)<0.01,"PASS","FAIL")'),
        ("DSCR covenant (all years >= 1.25x)", "Live Model!B28:F28", '=IF(MIN(\'Live Model\'!B28:F28)>=Inputs!B28,"PASS","FAIL")'),
        ("Sources & uses at close (management)", "Funding & Audit!D6", '=IF(\'Funding & Audit\'!D6>=0,"PASS","FAIL")'),
        ("Credit line / VAT bridge <= stated limit", "Funding & Audit!G6", '=IF(\'Funding & Audit\'!G6<=50000,"PASS","FAIL")'),
        ("Phase II self-funding gate", "Funding & Audit!B13", '=IF(\'Funding & Audit\'!B13>=0,"PASS","FAIL")'),
    ]
    for r, (check, where, formula) in enumerate(checks, start=28):
        _write_row(ws, r, [check, where, formula], st, number_format="@")
        ws.cell(row=r, column=3).font = st["bold"]
        ws.cell(row=r, column=3).alignment = Alignment(horizontal="center")

    ws["A38"] = "4. HEADLINE FINDINGS"
    ws["A38"].font = st["bold"]
    findings = [
        "The management case meets the 1.25x DSCR covenant at 28.23% in Year 1 and 31.36% in Year 2, but that is 1.48x the INE average.",
        "The independent INE market case (21.24%) generates €17.6k EBITDA and a 0.40x DSCR: it does not cover debt service.",
        "The original promoter case (19.2%) replicates the university Excel (€86,275 revenue / €11,297 EBITDA) and ends Year 1 with negative cash.",
        "Close-day uses (pre-opening, working capital, DSRA) create a €70.8k funding gap that the original Python cash flow omitted.",
        "The model draws a €143.6k VAT bridge while the stated revolving line is €50k: disclose the bridge as a separate facility or increase the line.",
        "Phase II needs €435.6k but Phase I only generates €193.9k of cash by the end of Year 2: the Phase II gate is negative (-€241.6k).",
        "Without an exit, the 5-year project IRR is negative; with an 8.5% cap-rate exit it is 15.4% (project) and 29.7% (equity).",
    ]
    for r, text in enumerate(findings, start=39):
        cell = ws.cell(row=r, column=1, value=f"• {text}")
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws["A48"] = "5. DISCLAIMER"
    ws["A48"].font = st["bold"]
    ws["A49"] = ("This is a portfolio model built from the author's own university work, public INE data and public convenio tables. "
                 "It is not investment advice. The management case is an upside case; the market and promoter cases are the honest downside anchors.")
    ws["A49"].font = st["note"]
    ws["A49"].alignment = Alignment(wrap_text=True, vertical="top")

    ws.column_dimensions["A"].width = 58
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 22
    ws.column_dimensions["F"].width = 30


def build_inputs(wb, engine: FinancialModelEngine, df_proj, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Inputs", index=1)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "MODEL INPUTS - MANAGEMENT CASE (ALL HARD-CODED ASSUMPTIONS IN ONE PLACE)"
    ws["A1"].font = st["title"]
    ws["A2"] = "Change any blue input and the Live Model recalculates. The report tabs are Python snapshots and do not recalculate."
    ws["A2"].font = st["note"]

    _header_row(ws, 4, ["Input", "Value", "Unit / Source"], st)
    inputs = [
        ("Mature occupancy", get_annual_weighted_occupancy(), "%", "Management case: 31.36% (1.48x INE market)"),
        ("Year 1 ramp", 0.90, "%", "90% of mature occupancy"),
        ("Year 2 ramp", 1.00, "%", "100% of mature occupancy"),
        ("Year 3 ramp", 1.05, "%", "105% mature (stabilized)"),
        ("Year 4 ramp", 1.05, "%", "105% mature"),
        ("Year 5 ramp", 1.05, "%", "105% mature"),
        ("Double rooms", 7, "rooms", "Boutique hotel inventory"),
        ("Full houses", 1, "house", "Casa rural completa"),
        ("Room ADR", 85.0, "€/night", "Original university price"),
        ("House ADR", 380.0, "€/night", "Original university price"),
        ("Restaurant ticket", 25.0, "€/meal", "Management case (original: €20)"),
        ("Diners per occupied day", 21, "meals", "7 rooms x 2 + 1 house x 7"),
        ("Restaurant COGS", 0.30, "%", "30% food & beverage cost"),
        ("Annual payroll", engine.labor.total_annual_payroll, "€", "2.09 FTE part-time (35% SS)"),
        ("Fixed opex", engine.opex.total_fixed_opex, "€", "Maintenance, insurance, utilities, marketing, PMS"),
        ("CapEx", engine.capex.total_capex, "€", "Land 250k + renovation 440k + biopool 35k + digital 4k"),
        ("Annual depreciation", engine.capex.annual_depreciation, "€", "Ley 27/2014 tables"),
        ("Senior debt", engine.financing.senior_debt_principal, "€", "70% of base CapEx"),
        ("Sponsor equity", engine.financing.sponsor_equity, "€", "30% of base CapEx"),
        ("Interest rate", engine.financing.loan_interest_rate, "%", "Senior mortgage"),
        ("Tenure", engine.financing.loan_tenure_years, "years", "French amortization"),
        ("Corporate tax rate", 0.25, "%", "Ley 27/2014"),
        ("LEADER grant (Year 2)", engine.financing.leader_subsidy_amount, "€", "Post-close, Month 14"),
        ("Target DSCR", 1.25, "x", "Bank covenant floor"),
        ("INE market occupancy", get_market_occupancy(), "%", "INE EOTR Segovia 2025"),
        ("Promoter occupancy", PROMOTER_OCCUPANCY, "%", "Original Excel (491 / 2,555 room-nights)"),
        ("VAT bridge (Year 1)", float(df_proj.iloc[0]["vat_receivable"]), "€", "AEAT refund bridge (net)"),
        ("VAT bridge interest rate", engine.financing.credit_line_interest, "%", "5.5% annual on the drawn bridge"),
    ]
    for r, (name, value, unit, source) in enumerate(inputs, start=5):
        cell = ws.cell(row=r, column=1, value=name)
        cell.font = st["bold"]
        cell.border = st["border"]
        vcell = ws.cell(row=r, column=2, value=value)
        vcell.font = Font(name="Calibri", size=11, bold=True, color="1D4ED8")
        vcell.fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
        vcell.border = st["border"]
        vcell.number_format = "0.00%" if unit == "%" else ("#,##0.00" if isinstance(value, float) else "#,##0")
        ucell = ws.cell(row=r, column=3, value=unit)
        ucell.font = st["regular"]
        ucell.border = st["border"]
        scell = ws.cell(row=r, column=4, value=source)
        scell.font = st["note"]
        scell.border = st["border"]

    ws["A35"] = "CASE DEFINITIONS"
    ws["A35"].font = st["bold"]
    definitions = [
        ("Management (upside)", "31.36% mature occupancy, one on-site meal per guest per day, €25 ticket. This is the headline Python case."),
        ("INE market", "21.24% official Segovia room occupancy (2025), original unit economics (€85/€380/€20, 859 meals at 19.2% scaled to 21.24%)."),
        ("Promoter", "19.20% occupancy, 491 room-nights, 72 house-nights, 859 meals, €85/€380/€20, 4.5%/25Y debt, no grant. Replicates the original Excel."),
    ]
    for r, (name, text) in enumerate(definitions, start=36):
        ws.cell(row=r, column=1, value=name).font = st["bold"]
        ws.cell(row=r, column=2, value=text).font = st["regular"]
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")

    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 62


def build_live_model(wb, engine: FinancialModelEngine, df_kpi, debt_sched, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Live Model", index=2)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "LIVE 5-YEAR MODEL - FORMULA-DRIVEN MANAGEMENT CASE"
    ws["A1"].font = st["title"]
    ws["A2"] = "Every value in columns B-F is a formula linked to the Inputs tab and the Debt Schedule. The Checks block compares the live output with Python."
    ws["A2"].font = st["note"]

    _header_row(ws, 4, ["Line Item", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"], st)

    years = [1, 2, 3, 4, 5]
    cols = ["B", "C", "D", "E", "F"]

    # Row map
    rows = {
        "occupancy": 5,
        "occupied_days": 6,
        "room_rev": 7,
        "house_rev": 8,
        "rest_rev": 9,
        "total_rev": 10,
        "cogs": 11,
        "payroll": 12,
        "fixed_opex": 13,
        "ebitda": 14,
        "depreciation": 15,
        "ebit": 16,
        "begin_debt": 17,
        "interest": 18,
        "principal": 19,
        "end_debt": 20,
        "ebt": 21,
        "tax": 22,
        "net_income": 23,
        "cfo": 24,
        "cfi": 25,
        "cff": 26,
        "end_cash": 27,
        "dscr": 28,
        "net_ppe": 29,
        "total_assets": 30,
        "equity": 31,
        "liab_equity": 32,
        "balance_check": 33,
    }
    labels = {
        "occupancy": "Occupancy (% of available days)",
        "occupied_days": "Occupied day-equivalents",
        "room_rev": "Room revenue (€)",
        "house_rev": "Full-house revenue (€)",
        "rest_rev": "Restaurant revenue (€)",
        "total_rev": "Total revenue (€)",
        "cogs": "Restaurant COGS (€)",
        "payroll": "Payroll (€)",
        "fixed_opex": "Fixed opex (€)",
        "ebitda": "EBITDA (€)",
        "depreciation": "Depreciation (€)",
        "ebit": "EBIT (€)",
        "begin_debt": "Beginning senior debt (€)",
        "interest": "Interest expense (€)",
        "principal": "Principal repayment (€)",
        "end_debt": "Ending senior debt (€)",
        "ebt": "EBT (€)",
        "tax": "Corporate tax (€)",
        "net_income": "Net income (€)",
        "cfo": "Cash flow from operations (€)",
        "cfi": "Cash flow from investing (€)",
        "cff": "Cash flow from financing (€)",
        "end_cash": "Ending cash (€)",
        "dscr": "DSCR (x)",
        "net_ppe": "Net PP&E (€)",
        "total_assets": "Total assets (€)",
        "equity": "Equity incl. capital subsidies (€)",
        "liab_equity": "Liabilities + equity (€)",
        "balance_check": "Balance check (€)",
    }
    for key, row in rows.items():
        cell = ws.cell(row=row, column=1, value=labels[key])
        cell.font = st["bold"] if key in ("total_rev", "ebitda", "net_income", "end_cash", "dscr", "balance_check") else st["regular"]
        cell.border = st["border"]

    # Occupancy and revenue formulas
    for i, (year, col) in enumerate(zip(years, cols)):
        ramp_row = 6 + i  # Inputs!B6..B10 are the ramp factors
        ws[f"{col}{rows['occupancy']}"] = f"=Inputs!$B$5*Inputs!$B${ramp_row}"
        ws[f"{col}{rows['occupied_days']}"] = f"=365*{col}{rows['occupancy']}"
        ws[f"{col}{rows['room_rev']}"] = f"={col}{rows['occupied_days']}*Inputs!$B$11*Inputs!$B$13"
        ws[f"{col}{rows['house_rev']}"] = f"={col}{rows['occupied_days']}*Inputs!$B$12*Inputs!$B$14"
        ws[f"{col}{rows['rest_rev']}"] = f"={col}{rows['occupied_days']}*Inputs!$B$16*Inputs!$B$15"
        ws[f"{col}{rows['total_rev']}"] = f"=SUM({col}{rows['room_rev']}:{col}{rows['rest_rev']})"
        ws[f"{col}{rows['cogs']}"] = f"={col}{rows['rest_rev']}*Inputs!$B$17"
        ws[f"{col}{rows['payroll']}"] = "=Inputs!$B$18"
        ws[f"{col}{rows['fixed_opex']}"] = "=Inputs!$B$19"
        ws[f"{col}{rows['ebitda']}"] = f"={col}{rows['total_rev']}-{col}{rows['cogs']}-{col}{rows['payroll']}-{col}{rows['fixed_opex']}"
        ws[f"{col}{rows['depreciation']}"] = "=Inputs!$B$21"
        ws[f"{col}{rows['ebit']}"] = f"={col}{rows['ebitda']}-{col}{rows['depreciation']}"

        # Debt schedule references (row 4 = Year 1)
        debt_row = 4 + i
        ws[f"{col}{rows['begin_debt']}"] = f"='Debt Schedule'!B{debt_row}"
        ws[f"{col}{rows['interest']}"] = f"='Debt Schedule'!E{debt_row}"
        ws[f"{col}{rows['principal']}"] = f"='Debt Schedule'!D{debt_row}"
        ws[f"{col}{rows['end_debt']}"] = f"='Debt Schedule'!F{debt_row}"
        if i == 1:
            # Python charges one full year of 5.5% bridge interest on the Year 1
            # VAT facility; the facility is repaid in Year 2.
            ws[f"{col}{rows['ebt']}"] = f"={col}{rows['ebit']}-{col}{rows['interest']}-Inputs!$B$31*Inputs!$B$32"
        else:
            ws[f"{col}{rows['ebt']}"] = f"={col}{rows['ebit']}-{col}{rows['interest']}"
        ws[f"{col}{rows['tax']}"] = f"=MAX(0,{col}{rows['ebt']}*Inputs!$B$26)"
        ws[f"{col}{rows['net_income']}"] = f"={col}{rows['ebt']}-{col}{rows['tax']}"
        ws[f"{col}{rows['cfo']}"] = f"={col}{rows['net_income']}+{col}{rows['depreciation']}"
        ws[f"{col}{rows['cfi']}"] = "=-Inputs!$B$20" if i == 0 else "=0"
        if i == 0:
            ws[f"{col}{rows['cff']}"] = f"=Inputs!$B$22+Inputs!$B$23-{col}{rows['principal']}"
        elif i == 1:
            ws[f"{col}{rows['cff']}"] = f"=-{col}{rows['principal']}+Inputs!$B$27"
        else:
            ws[f"{col}{rows['cff']}"] = f"=-{col}{rows['principal']}"
        if i == 0:
            ws[f"{col}{rows['end_cash']}"] = f"={col}{rows['cfo']}+{col}{rows['cfi']}+{col}{rows['cff']}"
        else:
            prev = cols[i - 1]
            ws[f"{col}{rows['end_cash']}"] = f"={prev}{rows['end_cash']}+{col}{rows['cfo']}+{col}{rows['cfi']}+{col}{rows['cff']}"
        ws[f"{col}{rows['dscr']}"] = f"=({col}{rows['ebitda']}-{col}{rows['tax']})/({col}{rows['interest']}+{col}{rows['principal']})"
        if i == 0:
            ws[f"{col}{rows['net_ppe']}"] = f"=Inputs!$B$20-{col}{rows['depreciation']}"
            ws[f"{col}{rows['equity']}"] = f"=Inputs!$B$23+{col}{rows['net_income']}"
        else:
            prev = cols[i - 1]
            ws[f"{col}{rows['net_ppe']}"] = f"={prev}{rows['net_ppe']}-{col}{rows['depreciation']}"
            grant_term = f"+Inputs!$B$27" if i == 1 else ""
            ws[f"{col}{rows['equity']}"] = f"={prev}{rows['equity']}+{col}{rows['net_income']}{grant_term}"
        ws[f"{col}{rows['total_assets']}"] = f"={col}{rows['net_ppe']}+{col}{rows['end_cash']}"
        ws[f"{col}{rows['liab_equity']}"] = f"={col}{rows['end_debt']}+{col}{rows['equity']}"
        ws[f"{col}{rows['balance_check']}"] = f"={col}{rows['total_assets']}-{col}{rows['liab_equity']}"

    # Number formats
    for key, row in rows.items():
        for col in cols:
            cell = ws[f"{col}{row}"]
            cell.border = st["border"]
            if key in ("occupancy",):
                cell.number_format = "0.00%"
            elif key in ("dscr",):
                cell.number_format = "0.00"
            elif key in ("occupied_days",):
                cell.number_format = "#,##0.0"
            else:
                cell.number_format = "#,##0.00"

    # Checks block
    ws["A35"] = "CHECKS: LIVE MODEL VS. PYTHON OUTPUT"
    ws["A35"].font = st["bold"]
    _header_row(ws, 36, ["Check", "Python", "Live", "Difference", "Status"], st)
    checks = [
        ("Revenue Year 1 (€)", float(df_kpi.iloc[0]["total_revenue"]), f"=B{rows['total_rev']}"),
        ("EBITDA Year 1 (€)", float(df_kpi.iloc[0]["ebitda"]), f"=B{rows['ebitda']}"),
        ("DSCR Year 1 (x)", float(df_kpi.iloc[0]["dscr"]), f"=B{rows['dscr']}"),
        ("Ending cash Year 1 (€)", float(df_kpi.iloc[0]["ending_cash"]), f"=B{rows['end_cash']}"),
    ]
    for i, (name, py_val, live_formula) in enumerate(checks, start=37):
        ws.cell(row=i, column=1, value=name).font = st["bold"]
        ws.cell(row=i, column=1).border = st["border"]
        ws.cell(row=i, column=2, value=py_val).number_format = "#,##0.00"
        ws.cell(row=i, column=2).border = st["border"]
        ws.cell(row=i, column=3, value=live_formula).number_format = "#,##0.00"
        ws.cell(row=i, column=3).border = st["border"]
        ws.cell(row=i, column=4, value=f"=C{i}-B{i}").number_format = "#,##0.00"
        ws.cell(row=i, column=4).border = st["border"]
        _status_formula(ws, i, 5, f"ABS(D{i})<1", st)

    ws["A42"] = "Balance-sheet check (max absolute) (€)"
    ws["A42"].font = st["bold"]
    ws["B42"] = "=MAX(ABS(B33),ABS(C33),ABS(D33),ABS(E33),ABS(F33))"
    ws["B42"].number_format = "#,##0.00"
    ws["C42"] = '=IF(B42<1,"PASS","FAIL")'
    ws["C42"].font = st["bold"]
    ws["A43"] = "DSCR covenant (all years >= 1.25x)"
    ws["A43"].font = st["bold"]
    ws["B43"] = "=MIN(B28:F28)"
    ws["B43"].number_format = "0.00"
    ws["C43"] = '=IF(B43>=Inputs!B28,"PASS","FAIL")'
    ws["C43"].font = st["bold"]
    ws["A44"] = "Note: the VAT bridge is a balance-sheet wash and is excluded from this simplified live cash flow; the Python model includes it."
    ws["A44"].font = st["note"]
    ws["A44"].alignment = Alignment(wrap_text=True, vertical="top")

    ws.column_dimensions["A"].width = 44
    for col in cols:
        ws.column_dimensions[col].width = 18


def build_funding_audit(wb, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Funding & Audit", index=3)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "SOURCES & USES, FUNDING GAP, PHASE II GATE AND COMPUTED AUDIT"
    ws["A1"].font = st["title"]
    ws["A2"] = "This tab is the honest funding layer: it includes the close-day uses omitted by the original cash flow and the Phase II double-spend test."
    ws["A2"].font = st["note"]

    # Section 1: Sources & Uses
    ws["A4"] = "1. SOURCES & USES AT CLOSE (€)"
    ws["A4"].font = st["bold"]
    _header_row(ws, 5, ["Case", "Uses at close", "Sources at close", "Gap at close", "Adj. cash Y1", "DSCR Y1", "Credit line drawn", "Status", "Check"], st)

    funding = {case: SourcesUsesEngine(case=case).compute() for case in ("management", "market", "promoter")}
    for r, case in enumerate(("management", "market", "promoter"), start=6):
        f = funding[case]
        _write_row(ws, r, [
            case,
            f.total_uses_at_close,
            f.total_sources_at_close,
            f.funding_gap_at_close,
            f.cash_y1_adjusted,
            f.dscr_y1,
            f.model_credit_line_drawn_y1,
            f.funding_status,
        ], st)
        ws.cell(row=r, column=1).font = st["bold"]
        ws.cell(row=r, column=6).number_format = "0.00"
        # Formula-driven status
        ws.cell(row=r, column=9, value=f'=IF(D{r}>=0,"PASS","FAIL")').font = st["bold"]
        ws.cell(row=r, column=9).alignment = Alignment(horizontal="center")

    ws["A10"] = "2. PHASE II PHASE GATE"
    ws["A10"].font = st["bold"]
    exp = ExpansionFinancialEngine()
    phase1_cash = funding["management"].cash_y2_model
    phase1_dscr = funding["management"].dscr_y3
    gate = exp.compute_phase_gate(phase1_cash, phase1_dscr)
    gate_rows = [
        ("Phase I cash at end of Year 2 (€)", phase1_cash),
        ("Phase II cash need (net CapEx + VAT) (€)", gate["phase2_cash_need"]),
        ("Phase II funding gap (€)", gate["phase2_funding_gap"]),
        ("Phase I DSCR Year 3 (x)", gate["phase1_dscr_y3"]),
        ("DSCR condition (>= 1.25x)", "PASS" if gate["dscr_condition_met"] else "FAIL"),
        ("Cash condition (Phase I cash >= Phase II need)", "PASS" if gate["cash_condition_met"] else "FAIL"),
        ("Phase II proceed", "YES" if gate["phase2_proceed"] else "NO"),
    ]
    for r, (label, value) in enumerate(gate_rows, start=11):
        ws.cell(row=r, column=1, value=label).font = st["bold"]
        ws.cell(row=r, column=1).border = st["border"]
        cell = ws.cell(row=r, column=2, value=value)
        cell.border = st["border"]
        cell.font = st["regular"]
        if isinstance(value, float):
            cell.number_format = "#,##0.00"
        if isinstance(value, str) and value in ("PASS", "FAIL", "YES", "NO"):
            cell.font = st["bold"]
            cell.fill = st["green"] if value in ("PASS", "YES") else st["red"]

    # Section 3: Audit rules
    ws["A20"] = "3. COMPUTED AUDIT RULES (THE AUDIT CAN FAIL)"
    ws["A20"].font = st["bold"]
    _header_row(ws, 21, ["Rule ID", "Rule", "Severity", "Status", "Actual", "Threshold"], st)
    payload = ModelAuditEngine().generate_audit_payload()
    for r, rule in enumerate(payload["guardrail_audit_rules"], start=22):
        actual = rule["actual_value"]
        if isinstance(actual, dict):
            actual = ", ".join(f"{k}={v}" for k, v in actual.items())
        _write_row(ws, r, [
            rule["rule_id"],
            rule["rule_name"],
            rule["severity"],
            rule["status"],
            actual,
            rule["threshold"] if not isinstance(rule["threshold"], dict) else str(rule["threshold"]),
        ], st, number_format="@")
        status_cell = ws.cell(row=r, column=4)
        status_cell.font = st["bold"]
        status_cell.fill = st["green"] if rule["status"] == "PASSED" else st["red"]
        status_cell.alignment = Alignment(horizontal="center")

    status_row = 22 + len(payload["guardrail_audit_rules"]) + 1
    ws.cell(row=status_row, column=1, value="AUDIT VERDICT").font = st["bold"]
    ws.cell(row=status_row, column=2, value=payload["execution_status"]["audit_verdict"]).font = st["bold"]
    ws.cell(row=status_row, column=2).fill = st["amber"]

    # Section 4: Key findings
    findings_row = status_row + 2
    ws.cell(row=findings_row, column=1, value="4. KEY FUNDING FINDINGS").font = st["bold"]
    findings = [
        "The management case's close-day uses are €948,858 vs. €878,090 of sources: a €70,768 gap before any operating cash flow.",
        "The model draws a €143,596 VAT bridge, but the stated revolving credit line is €50,000. The bridge must be disclosed as a separate facility.",
        "The LEADER grant (€163,000) arrives in Month 14 and cannot fund close-day uses.",
        "Phase II needs €435,564 but Phase I only generates €193,950 of cash by the end of Year 2: a €241,614 funding gap.",
        "The audit verdict is CONDITIONAL: 5 material exceptions and 1 warning. This is deliberate, not a bug.",
    ]
    for r, text in enumerate(findings, start=findings_row + 1):
        cell = ws.cell(row=r, column=1, value=f"• {text}")
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 42
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 20
    ws.column_dimensions["F"].width = 16
    ws.column_dimensions["G"].width = 20
    ws.column_dimensions["H"].width = 52
    ws.column_dimensions["I"].width = 12


def add_live_model_tabs(wb, engine: FinancialModelEngine, df_proj, df_kpi, debt_sched) -> None:
    """Adds the four live tabs and puts them first in the workbook."""
    st = _styles()
    build_readme(wb, st)
    build_inputs(wb, engine, df_proj, st)
    build_live_model(wb, engine, df_kpi, debt_sched, st)
    build_funding_audit(wb, st)

    # Reorder: live tabs first, then the original report tabs.
    preferred = [
        "Read Me & Checks", "Inputs", "Live Model", "Funding & Audit",
        "Executive Scorecard", "3-Statement Model", "Debt Schedule",
        "Scenario Stress-Testing", "Monte Carlo Risk", "Credit Risk & Copula",
        "Unit Economics & Runway", "Phase II Expansion",
    ]
    existing = [name for name in preferred if name in wb.sheetnames]
    remaining = [name for name in wb.sheetnames if name not in existing]
    wb._sheets = [wb[name] for name in existing + remaining]
