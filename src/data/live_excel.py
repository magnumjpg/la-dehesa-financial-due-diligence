"""
Live, formula-driven Excel tabs for the La Dehesa del Castrillo model.

The exporter writes a report pack (Python snapshots) plus four institutional
tabs that actually calculate:

1. Read Me & Checks  - model map, the three cases, live integrity checks and
                       the headline findings.
2. Inputs            - every hard-coded assumption in one place (rows 5-48).
3. Live Model        - a formula-driven five-year P&L, cash flow, debt, tax
                       (with BIN carry-forward) and balance sheet that
                       replicates the Python management case (rows 5-62),
                       followed by a Live-vs-Python comparison block.
4. Funding & Audit   - sources & uses by case, the close-day reconciliation,
                       the Phase II gate and the computed audit rules.

A fifth tab, ``build_debt_schedule``, replaces the old value-only debt tab with
a 240-month French amortisation schedule (12-month interest-only grace, 20-year
tenure) and an annual summary built with SUMIF.

Conventions
-----------
* Every blue Inputs cell is a hard-coded assumption; every Live Model cell in
  columns B-F is a formula linked to Inputs, the Debt Schedule or another live
  row. Nothing in the live block is a pasted value.
* The model rounds each monthly payment to two decimals, exactly like
  ``DebtAmortizationEngine``. That is why the Year-2 annual service is
  EUR 27,647.64 (12 x 2,303.97), not 27,647.61.
* Operating VAT is a pass-through: revenue is net of VAT and the output VAT is
  remitted net of recoverable operating VAT, so CFO = net income + D&A. Only
  the CapEx input VAT is bridge-financed.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

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

# ---------------------------------------------------------------------------
# Stable row maps. Other functions and the Read Me checks reference these
# numbers, so do not renumber without updating the cross-sheet formulas.
# ---------------------------------------------------------------------------
INPUT_ROW: Dict[str, int] = {
    "mature_occupancy": 5,
    "ramp_y1": 6,
    "ramp_y2": 7,
    "ramp_y3": 8,
    "ramp_y4": 9,
    "ramp_y5": 10,
    "double_rooms": 11,
    "full_houses": 12,
    "room_adr": 13,
    "house_adr": 14,
    "restaurant_ticket": 15,
    "diners_per_occupied_day": 16,
    "restaurant_cogs_ratio": 17,
    "ota_share": 18,
    "ota_commission_rate": 19,
    "amenities_per_occupied_day": 20,
    "breakfast_per_guest_day": 21,
    "guests_per_occupied_day": 22,
    "ffe_reserve_rate": 23,
    "annual_payroll": 24,
    "fixed_opex": 25,
    "corporate_tax_rate": 26,
    "total_capex": 27,
    "land_in_kind": 28,
    "cash_capex": 29,
    "annual_ppe_depreciation": 30,
    "preopening_costs": 31,
    "preopening_amort_years": 32,
    "senior_debt_principal": 33,
    "loan_interest_rate": 34,
    "loan_tenure_years": 35,
    "grace_months": 36,
    "idc": 37,
    "input_vat": 38,
    "vat_bridge_interest_rate": 39,
    "leader_grant": 40,
    "target_dscr": 41,
    "initial_working_capital": 42,
    "dsra": 43,
    "cash_equity": 44,
    "total_equity_at_close": 45,
    "ine_market_occupancy": 46,
    "promoter_occupancy": 47,
    "credit_line_limit": 48,
}

LIVE: Dict[str, int] = {
    "occupancy": 5,
    "occupied_days": 6,
    "room_nights": 7,
    "house_nights": 8,
    "guests": 9,
    "room_rev": 10,
    "house_rev": 11,
    "rest_rev": 12,
    "total_rev": 13,
    "cogs": 14,
    "ota": 15,
    "amenities": 16,
    "breakfast": 17,
    "variable_costs": 18,
    "gross_margin": 19,
    "payroll": 20,
    "fixed_opex": 21,
    "ebitda": 22,
    "ffe_reserve": 23,
    "ppe_depreciation": 24,
    "preopening_amort": 25,
    "depreciation": 26,
    "ebit": 27,
    "begin_debt": 28,
    "senior_interest": 29,
    "principal": 30,
    "end_debt": 31,
    "bridge_interest": 32,
    "interest_expense": 33,
    "ebt": 34,
    "bin_opening": 35,
    "taxable_base": 36,
    "tax": 37,
    "bin_closing": 38,
    "net_income": 39,
    "cfo": 40,
    "cfi": 41,
    "cff": 42,
    "net_cash_flow": 43,
    "end_cash": 44,
    "cfads": 45,
    "debt_service": 46,
    "dscr": 47,
    "gross_ppe": 48,
    "accum_depr": 49,
    "net_ppe": 50,
    "accum_amort": 51,
    "net_intangibles": 52,
    "restricted_cash": 53,
    "vat_receivable": 54,
    "total_assets": 55,
    "vat_bridge": 56,
    "total_liabilities": 57,
    "share_capital": 58,
    "retained_earnings": 59,
    "capital_subsidies": 60,
    "total_equity": 61,
    "bs_check": 62,
}

# Debt Schedule layout.
DEBT_PARAM_START = 4
DEBT_SUMMARY_HEADER = 15
DEBT_SUMMARY_START = 16
DEBT_MONTHLY_HEADER = 24
DEBT_MONTHLY_START = 25
DEBT_MONTHLY_END = 264

LIVE_CHECK_HEADER = 65
LIVE_CHECK_START = 66
LIVE_CHECK_COVENANT = LIVE_CHECK_START + 8  # 8 comparison checks, then the covenant test

YEARS = [1, 2, 3, 4, 5]
COLS = ["B", "C", "D", "E", "F"]

REVENUE_LABELS = {
    "occupancy": "Occupancy (% of available days)",
    "occupied_days": "Occupied day-equivalents",
    "room_nights": "Double-room nights",
    "house_nights": "Full-house nights",
    "guests": "Guest-days",
    "room_rev": "Room revenue",
    "house_rev": "Full-house revenue",
    "rest_rev": "Restaurant revenue",
    "total_rev": "Total revenue",
    "cogs": "Restaurant COGS (30%)",
    "ota": "OTA commissions (9% blended)",
    "amenities": "Amenities and housekeeping",
    "breakfast": "Breakfast cost",
    "variable_costs": "Total variable costs",
    "gross_margin": "Gross margin",
    "payroll": "Payroll (incl. 35% social security)",
    "fixed_opex": "Fixed operating expenses",
    "ebitda": "EBITDA",
    "ffe_reserve": "FF&E reserve (3% of revenue)",
    "ppe_depreciation": "PP&E depreciation",
    "preopening_amort": "Pre-opening amortisation (5 years)",
    "depreciation": "Total D&A",
    "ebit": "EBIT",
    "begin_debt": "Beginning senior debt",
    "senior_interest": "Senior interest",
    "principal": "Principal repayment",
    "end_debt": "Ending senior debt",
    "bridge_interest": "VAT bridge interest",
    "interest_expense": "Total interest",
    "ebt": "EBT",
    "bin_opening": "Opening tax losses (BINs)",
    "taxable_base": "Taxable base after BINs",
    "tax": "Corporate tax (25%)",
    "bin_closing": "Closing tax losses (BINs)",
    "net_income": "Net income",
    "cfo": "Cash flow from operations",
    "cfi": "Cash flow from investing",
    "cff": "Cash flow from financing",
    "net_cash_flow": "Net change in cash",
    "end_cash": "Ending cash (unrestricted)",
    "cfads": "CFADS (EBITDA - FF&E - tax)",
    "debt_service": "Senior debt service",
    "dscr": "DSCR (x)",
    "gross_ppe": "Gross PP&E (incl. capitalised IDC)",
    "accum_depr": "Accumulated depreciation",
    "net_ppe": "Net PP&E",
    "accum_amort": "Accumulated amortisation",
    "net_intangibles": "Net intangibles (pre-opening)",
    "restricted_cash": "Restricted cash (DSRA + FF&E reserve)",
    "vat_receivable": "VAT receivable (AEAT)",
    "total_assets": "TOTAL ASSETS",
    "vat_bridge": "VAT bridge (liability)",
    "total_liabilities": "Total liabilities",
    "share_capital": "Share capital (land in kind + cash equity)",
    "retained_earnings": "Retained earnings",
    "capital_subsidies": "Capital subsidies (LEADER)",
    "total_equity": "Total equity",
    "bs_check": "Balance check (assets - liabilities - equity)",
}

BOLD_ROWS = {
    "total_rev", "gross_margin", "ebitda", "ebit", "net_income",
    "end_cash", "cfads", "dscr", "total_assets", "total_liabilities",
    "total_equity", "bs_check",
}

MONEY_ROWS = {
    "room_rev", "house_rev", "rest_rev", "total_rev", "cogs", "ota",
    "amenities", "breakfast", "variable_costs", "gross_margin", "payroll",
    "fixed_opex", "ebitda", "ffe_reserve", "ppe_depreciation",
    "preopening_amort", "depreciation", "ebit", "begin_debt",
    "senior_interest", "principal", "end_debt", "bridge_interest",
    "interest_expense", "ebt", "bin_opening", "taxable_base", "tax",
    "bin_closing", "net_income", "cfo", "cfi", "cff", "net_cash_flow",
    "end_cash", "cfads", "debt_service", "gross_ppe", "accum_depr",
    "net_ppe", "accum_amort", "net_intangibles", "restricted_cash",
    "vat_receivable", "total_assets", "vat_bridge", "total_liabilities",
    "share_capital", "retained_earnings", "capital_subsidies",
    "total_equity", "bs_check",
}

COUNT_ROWS = {"occupied_days", "room_nights", "house_nights", "guests"}


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


def _inp(key: str) -> str:
    """Absolute reference to an Inputs cell, e.g. Inputs!$B$33."""
    return f"Inputs!$B${INPUT_ROW[key]}"


def _inp_row(row: int) -> str:
    """Absolute reference to an Inputs row by number."""
    return f"Inputs!$B${row}"


# ---------------------------------------------------------------------------
# Read Me & Checks
# ---------------------------------------------------------------------------
def build_readme(wb, st: Dict[str, Any], case_facts: Dict[str, Dict[str, Any]], gate: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Read Me & Checks", index=0)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "LA DEHESA DEL CASTRILLO S.L. - MODEL MAP, CASES & INTEGRITY CHECKS"
    ws["A1"].font = st["title"]
    ws["A2"] = (
        "A live, formula-driven management case alongside the independent INE market case "
        "and a faithful replication of the original promoter simulator."
    )
    ws["A2"].font = st["note"]

    ws["A4"] = "1. MODEL MAP"
    ws["A4"].font = st["bold"]
    _header_row(ws, 5, ["Tab", "Purpose"], st)
    model_map = [
        ("Read Me & Checks", "This page: map, case definitions, live checks and headline findings."),
        ("Inputs", "Every hard-coded assumption in one place (rows 5-48)."),
        ("Live Model", "Formula-driven 5-year P&L, cash flow, tax, debt and balance sheet; reconciles to Python."),
        ("Funding & Audit", "Sources & uses by case, close-day reconciliation, Phase II gate and computed audit."),
        ("Executive Scorecard", "One-page underwriting scorecard (management case, Python snapshot)."),
        ("3-Statement Model", "Full Python output: P&L, cash flow and balance sheet."),
        ("Debt Schedule", "240-month French amortisation (12-month grace, 20 years) with SUMIF annual summary."),
        ("Scenario Stress-Testing", "Conservative / base / optimistic scenarios and the 2-D Year-2 DSCR matrix."),
        ("Monte Carlo Risk", "1,000-draw stochastic credit simulation on the minimum DSCR."),
        ("Credit Risk & Copula", "Gaussian / Student-t / Clayton tail risk on the Year-2 DSCR."),
        ("Unit Economics & Runway", "RevPAR, TRevPAR, contribution margin and the 24-month cash runway."),
        ("Phase II Expansion", "Landscape suites and biopool: CapEx, P&L, phase gate and consolidated impact."),
    ]
    for r, (tab, purpose) in enumerate(model_map, start=6):
        _write_row(ws, r, [tab, purpose], st, number_format="@")
        ws.cell(row=r, column=1).font = st["bold"]

    ws["A19"] = "2. THREE CASES (DO NOT CONFUSE THEM)"
    ws["A19"].font = st["bold"]
    _header_row(ws, 20, ["Case", "Occupancy", "Revenue Y1", "EBITDA Y1", "DSCR Y1", "Use"], st)
    cases = [
        (
            "Management (upside)",
            f"{get_annual_weighted_occupancy() * 100:.2f}%",
            case_facts["management"]["revenue_y1"],
            case_facts["management"]["ebitda_y1"],
            case_facts["management"]["dscr_y1"],
            "Headline case: 31.36% mature occupancy, 1.48x the INE market average.",
        ),
        (
            "INE market",
            f"{get_market_occupancy() * 100:.2f}%",
            case_facts["market"]["revenue_y1"],
            case_facts["market"]["ebitda_y1"],
            case_facts["market"]["dscr_y1"],
            "Independent benchmark: EBITDA is negative in Year 1 and does not cover debt service.",
        ),
        (
            "Promoter (original Excel)",
            f"{PROMOTER_OCCUPANCY * 100:.2f}%",
            case_facts["promoter"]["revenue_y1"],
            case_facts["promoter"]["ebitda_y1"],
            case_facts["promoter"]["dscr_y1"],
            "Faithful replication of the author's original university simulator.",
        ),
    ]
    for r, row in enumerate(cases, start=21):
        _write_row(ws, r, list(row), st, number_format="#,##0.00")
        ws.cell(row=r, column=1).font = st["bold"]
        ws.cell(row=r, column=2).number_format = "0.00%"
        ws.cell(row=r, column=5).number_format = "0.00"

    ws["A25"] = "3. KEY INTEGRITY CHECKS (LIVE FORMULAS)"
    ws["A25"].font = st["bold"]
    _header_row(ws, 26, ["Check", "Where", "Result"], st)
    bs = LIVE["bs_check"]
    checks = [
        (
            "Assets = liabilities + equity (max absolute)",
            f"Live Model!B{bs}:F{bs}",
            f'=IF(MAX(ABS(\'Live Model\'!B{bs}),ABS(\'Live Model\'!C{bs}),'
            f'ABS(\'Live Model\'!D{bs}),ABS(\'Live Model\'!E{bs}),ABS(\'Live Model\'!F{bs}))<1,"PASS","FAIL")',
        ),
        ("Live revenue vs. Python (Year 1)", f"Live Model!E{LIVE_CHECK_START}", f"='Live Model'!E{LIVE_CHECK_START}"),
        ("Live EBITDA vs. Python (Year 1)", f"Live Model!E{LIVE_CHECK_START + 1}", f"='Live Model'!E{LIVE_CHECK_START + 1}"),
        ("Live DSCR vs. Python (Year 2, binding year)", f"Live Model!E{LIVE_CHECK_START + 2}", f"='Live Model'!E{LIVE_CHECK_START + 2}"),
        ("Live ending cash vs. Python (Year 1)", f"Live Model!E{LIVE_CHECK_START + 3}", f"='Live Model'!E{LIVE_CHECK_START + 3}"),
        ("Live ending cash vs. Python (Year 2)", f"Live Model!E{LIVE_CHECK_START + 4}", f"='Live Model'!E{LIVE_CHECK_START + 4}"),
        ("Live net income vs. Python (Year 1)", f"Live Model!E{LIVE_CHECK_START + 5}", f"='Live Model'!E{LIVE_CHECK_START + 5}"),
        (
            "DSCR covenant (minimum of Years 1-5 >= 1.25x)",
            f"Live Model!E{LIVE_CHECK_COVENANT}",
            f"='Live Model'!E{LIVE_CHECK_COVENANT}",
        ),
        (
            "Senior debt fully amortised by month 240",
            f"Debt Schedule!G{DEBT_MONTHLY_END}",
            f'=IF(ABS(\'Debt Schedule\'!G{DEBT_MONTHLY_END})<1,"PASS","FAIL")',
        ),
        ("Sources equal uses at close (management)", "Funding & Audit!B27", '=IF(ABS(\'Funding & Audit\'!B27)<1,"PASS","FAIL")'),
        ("VAT bridge within the EUR 175k limit", "Funding & Audit!B23", '=IF(\'Funding & Audit\'!B23<=175000,"PASS","FAIL")'),
        ("Phase II phase gate", f"Funding & Audit!B{38}", "='Funding & Audit'!B38"),
    ]
    for r, (check, where, formula) in enumerate(checks, start=27):
        _write_row(ws, r, [check, where, formula], st, number_format="@")
        ws.cell(row=r, column=3).font = st["bold"]
        ws.cell(row=r, column=3).alignment = Alignment(horizontal="center")

    ws["A40"] = "4. HEADLINE FINDINGS"
    ws["A40"].font = st["bold"]
    mgmt = case_facts["management"]["result"]
    findings = [
        (
            "The all-in asset cost is EUR 1,050,100 (land, 550 m2 of works, kitchen, FF&E, "
            "biopool, digital, fees and contingency). The cash equity plug is EUR "
            f"{mgmt.cash_equity_required:,.2f}, or {mgmt.equity_to_capex_pct:.1f}% of CapEx, not the 30% in the business plan."
        ),
        (
            "The EUR 367,535 facility is 35% LTV, but the binding constraint is the DSCR: "
            f"the 1.25x cap supports EUR {mgmt.dscr_cap_principal:,.2f} ({mgmt.dscr_cap_ltv_pct:.1f}% LTV). "
            "The requested loan breaches the covenant in Year 2 (1.15x)."
        ),
        (
            "The independent INE market case (21.24%) is negative at EBITDA level in Year 1 "
            f"(EUR {case_facts['market']['ebitda_y1']:,.2f}) and its DSCR is {case_facts['market']['dscr_y1']:.2f}x."
        ),
        (
            "The original promoter case (19.2%) replicates the author's university Excel "
            "(EUR 86,275 revenue / EUR 11,297 EBITDA) and is structurally insolvent at the debt service level."
        ),
        (
            "Phase II needs EUR "
            f"{gate['phase2_cash_need']:,.2f} but Phase I generates EUR {gate['phase1_cash_end_y2']:,.2f} "
            f"of cash by the end of Year 2: the gate is negative by EUR {abs(gate['phase2_funding_gap']):,.2f}."
        ),
        (
            "The credit-committee recommendation is DECLINE AS STRUCTURED (RESIZE REQUIRED). "
            "The covenant break-even is 32.05% occupancy or an ADR of EUR 86.64; a 10% equity IRR needs EUR 116.36."
        ),
        (
            "The Clayton copula puts P(breach of 1.25x) at 50.7% and the worst-1% annual CFADS "
            "shortfall at EUR 62,786 against a EUR 13,824 contractual DSRA."
        ),
        (
            "The model is deliberately honest: the business does not earn its 8.5% cost of capital "
            "at the planned occupancy and ADR, and the workbook says so rather than hiding it."
        ),
    ]
    for r, text in enumerate(findings, start=41):
        cell = ws.cell(row=r, column=1, value=f"- {text}")
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        ws.row_dimensions[r].height = 30

    ws["A50"] = "5. DISCLAIMER"
    ws["A50"].font = st["bold"]
    ws["A51"] = (
        "This is a portfolio model built from the author's own university work, public INE data and "
        "public convenio tables. It is not investment advice. The management case is an upside case; "
        "the market and promoter cases are the honest downside anchors."
    )
    ws["A51"].font = st["note"]
    ws["A51"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A51:F51")
    ws.row_dimensions[51].height = 44

    ws.column_dimensions["A"].width = 58
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 24
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["E"].width = 22
    ws.column_dimensions["F"].width = 46


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def build_inputs(wb, engine: FinancialModelEngine, df_proj, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Inputs", index=1)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "MODEL INPUTS - MANAGEMENT CASE (ALL HARD-CODED ASSUMPTIONS IN ONE PLACE)"
    ws["A1"].font = st["title"]
    ws["A2"] = (
        "Change any blue input and the Live Model recalculates. The report tabs are Python snapshots "
        "and do not recalculate."
    )
    ws["A2"].font = st["note"]

    _header_row(ws, 4, ["Input", "Value", "Unit", "Source / basis"], st)

    inputs = [
        ("Mature occupancy", get_annual_weighted_occupancy(), "pct", "%", "Management case: 31.36% (1.48x the INE market average)"),
        ("Year 1 ramp", 0.90, "pct", "%", "90% of mature occupancy"),
        ("Year 2 ramp", 1.00, "pct", "%", "100% of mature occupancy"),
        ("Year 3 ramp", 1.00, "pct", "%", "No nominal ADR growth after stabilisation"),
        ("Year 4 ramp", 1.00, "pct", "%", "No nominal ADR growth after stabilisation"),
        ("Year 5 ramp", 1.00, "pct", "%", "No nominal ADR growth after stabilisation"),
        ("Double rooms", 7, "count", "rooms", "Boutique hotel inventory"),
        ("Full houses", 1, "count", "house", "Casa rural completa"),
        ("Room ADR", 85.0, "money", "EUR/night", "Planned net ADR (no nominal uplift)"),
        ("House ADR", 380.0, "money", "EUR/night", "Whole-house nightly rate"),
        ("Restaurant ticket", 25.0, "money", "EUR/meal", "Management case (original simulator: EUR 20)"),
        ("Diners per occupied day", 21, "count", "covers", "7 rooms x 2 guests + 1 house x 7 guests"),
        ("Restaurant COGS", 0.30, "pct", "%", "30% food and beverage cost"),
        ("OTA share", 0.60, "pct", "%", "60% of lodging sold through OTAs"),
        ("OTA commission", 0.15, "pct", "%", "15% commission on OTA bookings (9% blended)"),
        ("Amenities per occupied day", 35.0, "money", "EUR/day", "Housekeeping and guest supplies"),
        ("Breakfast per guest-day", 5.0, "money", "EUR/guest-day", "Breakfast cost per guest"),
        ("Guests per occupied day", 21, "count", "guests", "7 rooms x 2 + 1 house x 7"),
        ("FF&E reserve", 0.03, "pct", "%", "3% of revenue, deducted before debt service"),
        ("Annual payroll", engine.labor.total_annual_payroll, "money", "EUR", "2.09 FTE part-time contracts + 35% social security"),
        ("Fixed operating expenses", engine.opex.total_fixed_opex, "money", "EUR", "Maintenance, insurance, utilities, marketing, PMS, admin"),
        ("Corporate tax rate", 0.25, "pct", "%", "Ley 27/2014 (with BIN carry-forward in the live model)"),
        ("Total CapEx (net of VAT)", engine.capex.total_capex, "money", "EUR", "Land 250k + works 550k + kitchen 55k + FF&E 65k + biopool 40k + digital 12k + fees 42.6k + contingency 35.5k"),
        ("Land contributed in kind", engine.financing.land_in_kind_value, "money", "EUR", "Sponsor contributes the 25-ha estate"),
        ("Cash CapEx", engine.cash_capex, "money", "EUR", "All-in cost less the in-kind land"),
        ("Annual PP&E depreciation", engine.capex.annual_depreciation, "money", "EUR", "Linear fiscal tables (Ley 27/2014)"),
        ("Pre-opening costs", float(engine.financing.pre_opening_costs), "money", "EUR", "Capitalised and amortised over five years"),
        ("Pre-opening amortisation years", 5, "count", "years", "Straight line"),
        ("Senior debt principal", engine.financing.senior_debt_principal, "money", "EUR", "35% LTV of the all-in cost"),
        ("Senior interest rate", engine.financing.loan_interest_rate, "pct", "%", "Fixed 4.0% (2026 rural hotel terms)"),
        ("Loan tenure", float(engine.financing.loan_tenure_years), "count", "years", "French amortisation over 240 months"),
        ("Grace period", float(engine.financing.grace_months), "count", "months", "Interest-only after opening"),
        ("Interest during construction (IDC)", float(engine.financing.idc_amount), "money", "EUR", "12 construction months, paid at close"),
        ("Input VAT (bridge-funded)", float(engine.capex.total_input_vat), "money", "EUR", "21% on non-land CapEx; refunded by AEAT"),
        ("VAT bridge interest rate", engine.financing.credit_line_interest, "pct", "%", "5.5% on the drawn bridge"),
        ("LEADER grant", engine.financing.leader_subsidy_amount, "money", "EUR", "Month 14, post-close; cannot fund close-day uses"),
        ("Target DSCR", engine.financing.target_dscr, "x", "x", "Bank covenant floor"),
        ("Initial working capital", float(engine.financing.initial_working_capital), "money", "EUR", "Opening cash for the ramp-up"),
        ("DSRA", engine.dsra_amount, "money", "EUR", "Six months of the maximum annual debt service"),
        ("Cash equity (plug)", engine.cash_equity, "money", "EUR", "Closes the structure; 49.6% of CapEx"),
        ("Total equity at close", engine.total_equity_at_close, "money", "EUR", "Cash equity + land in kind"),
        ("INE market occupancy", get_market_occupancy(), "pct", "%", "INE EOTR Segovia 2025 (reference only)"),
        ("Promoter occupancy", PROMOTER_OCCUPANCY, "pct", "%", "Original Excel (491 / 2,555 room-nights)"),
        ("Committed revolver limit", engine.financing.credit_line_limit, "money", "EUR", "Seasonal liquidity backstop"),
    ]

    assert len(inputs) == len(INPUT_ROW), "Inputs rows and INPUT_ROW map are out of sync"

    formats = {
        "pct": "0.00%",
        "money": "#,##0.00",
        "count": "#,##0",
        "x": "0.00",
    }
    for r, (name, value, kind, unit, source) in enumerate(inputs, start=5):
        cell = ws.cell(row=r, column=1, value=name)
        cell.font = st["bold"]
        cell.border = st["border"]
        vcell = ws.cell(row=r, column=2, value=value)
        vcell.font = Font(name="Calibri", size=11, bold=True, color="1D4ED8")
        vcell.fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
        vcell.border = st["border"]
        vcell.number_format = formats[kind]
        ucell = ws.cell(row=r, column=3, value=unit)
        ucell.font = st["regular"]
        ucell.border = st["border"]
        scell = ws.cell(row=r, column=4, value=source)
        scell.font = st["note"]
        scell.border = st["border"]

    ws["A50"] = "CASE DEFINITIONS"
    ws["A50"].font = st["bold"]
    definitions = [
        (
            "Management (upside)",
            "31.36% mature occupancy (0.90 ramp in Year 1), one on-site meal per guest per day at EUR 25. "
            "Full realistic cost stack and the 35% LTV / 20-year structure. This is the headline case.",
        ),
        (
            "INE market",
            "21.24% official Segovia room occupancy, original unit economics (EUR 85 / EUR 380 / EUR 20) "
            "with the original 1.25x / 1.20x volume ramp, and the same full cost stack.",
        ),
        (
            "Promoter",
            "19.20% occupancy, 491 room-nights, 72 house-nights, 859 meals at EUR 20, 4.5% / 25-year debt, "
            "no grant and the original EUR 729k cost base. Replicates the original university Excel exactly.",
        ),
    ]
    for r, (name, text) in enumerate(definitions, start=51):
        ws.cell(row=r, column=1, value=name).font = st["bold"]
        ws.cell(row=r, column=1).alignment = Alignment(vertical="top")
        cell = ws.cell(row=r, column=2, value=text)
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        ws.row_dimensions[r].height = 44

    ws.column_dimensions["A"].width = 36
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 78


# ---------------------------------------------------------------------------
# Debt Schedule
# ---------------------------------------------------------------------------
def build_debt_schedule(wb, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Debt Schedule")
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "SENIOR DEBT SCHEDULE - 20 YEARS, 4.0% FIXED, 12-MONTH INTEREST-ONLY GRACE"
    ws["A1"].font = st["title"]
    ws["A2"] = (
        "The French payment is computed over the 228 months that remain after the grace period. "
        "Each monthly payment is rounded to two decimals, matching the Python debt engine."
    )
    ws["A2"].font = st["note"]

    ws["A4"] = "LOAN PARAMETERS"
    ws["A4"].font = st["bold"]
    params = [
        ("Principal", f"={_inp('senior_debt_principal')}", "#,##0.00"),
        ("Annual interest rate", f"={_inp('loan_interest_rate')}", "0.00%"),
        ("Tenure (years)", f"={_inp('loan_tenure_years')}", "#,##0"),
        ("Grace (months)", f"={_inp('grace_months')}", "#,##0"),
        ("Monthly rate", "=B5/12", "0.000000"),
        ("Amortisation months", "=B6*12-B7", "#,##0"),
        ("Monthly payment", "=IF(B8>0,B4*B8*(1+B8)^B9/((1+B8)^B9-1),B4/B9)", "#,##0.00"),
        ("Annual service (Year 2+)", "=ROUND(B10,2)*12", "#,##0.00"),
        ("Total months", "=B6*12", "#,##0"),
    ]
    for r, (label, formula, fmt) in enumerate(params, start=DEBT_PARAM_START):
        ws.cell(row=r, column=1, value=label).font = st["bold"]
        ws.cell(row=r, column=1).border = st["border"]
        cell = ws.cell(row=r, column=2, value=formula)
        cell.number_format = fmt
        cell.font = Font(name="Calibri", size=11, bold=True, color="1D4ED8")
        cell.border = st["border"]

    # Annual summary (SUMIF over the monthly table).
    ws["A14"] = "ANNUAL SUMMARY (SUMIF OF THE MONTHLY SCHEDULE)"
    ws["A14"].font = st["bold"]
    _header_row(
        ws,
        DEBT_SUMMARY_HEADER,
        ["Year", "Beginning balance", "Payment", "Principal", "Interest", "Ending balance", "Short-term debt", "Long-term debt"],
        st,
    )
    month_range = f"$B${DEBT_MONTHLY_START}:$B${DEBT_MONTHLY_END}"
    for i in range(5):
        r = DEBT_SUMMARY_START + i
        year = i + 1
        ws.cell(row=r, column=1, value=year)
        ws.cell(row=r, column=2, value="=$B$4" if i == 0 else f"=F{r - 1}")
        ws.cell(row=r, column=3, value=f"=SUMIF({month_range},$A{r},$D${DEBT_MONTHLY_START}:$D${DEBT_MONTHLY_END})")
        ws.cell(row=r, column=4, value=f"=SUMIF({month_range},$A{r},$E${DEBT_MONTHLY_START}:$E${DEBT_MONTHLY_END})")
        ws.cell(row=r, column=5, value=f"=SUMIF({month_range},$A{r},$F${DEBT_MONTHLY_START}:$F${DEBT_MONTHLY_END})")
        ws.cell(row=r, column=6, value=f"=B{r}-D{r}")
        ws.cell(row=r, column=7, value=f"=SUMIF({month_range},$A{r}+1,$E${DEBT_MONTHLY_START}:$E${DEBT_MONTHLY_END})")
        ws.cell(row=r, column=8, value=f"=MAX(0,F{r}-G{r})")
        for c in range(1, 9):
            cell = ws.cell(row=r, column=c)
            cell.border = st["border"]
            cell.font = st["regular"]
            cell.number_format = "#,##0" if c == 1 else "#,##0.00"

    # Monthly schedule.
    ws.cell(
        row=DEBT_MONTHLY_HEADER - 1,
        column=1,
        value="MONTHLY AMORTISATION SCHEDULE (240 MONTHS)",
    ).font = st["bold"]
    _header_row(
        ws,
        DEBT_MONTHLY_HEADER,
        ["Month", "Year", "Beginning balance", "Payment", "Principal", "Interest", "Ending balance"],
        st,
    )
    pmt = "ROUND($B$10,2)"
    for month in range(1, 241):
        r = DEBT_MONTHLY_START + month - 1
        ws.cell(row=r, column=1, value=1 if month == 1 else f"=A{r - 1}+1")
        ws.cell(row=r, column=2, value=f"=ROUNDUP(A{r}/12,0)")
        ws.cell(row=r, column=3, value="=$B$4" if month == 1 else f"=G{r - 1}")
        ws.cell(row=r, column=4, value=(
            f"=IF(A{r}<=$B$7,F{r},"
            f"IF(OR(A{r}=$B$12,C{r}+F{r}<={pmt}),C{r}+F{r},{pmt}))"
        ))
        ws.cell(row=r, column=5, value=f"=D{r}-F{r}")
        ws.cell(row=r, column=6, value=f"=ROUND(C{r}*$B$8,2)")
        ws.cell(row=r, column=7, value=f"=ROUND(C{r}-E{r},2)")
        for c in range(1, 8):
            cell = ws.cell(row=r, column=c)
            cell.border = st["border"]
            cell.font = st["regular"]
            cell.number_format = "#,##0" if c in (1, 2) else "#,##0.00"

    ws.column_dimensions["A"].width = 26
    for col in "BCDEFGH":
        ws.column_dimensions[col].width = 18
    ws.freeze_panes = f"A{DEBT_MONTHLY_START}"


# ---------------------------------------------------------------------------
# Live Model
# ---------------------------------------------------------------------------
def build_live_model(wb, engine: FinancialModelEngine, df_kpi, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Live Model", index=2)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "LIVE 5-YEAR MODEL - FORMULA-DRIVEN MANAGEMENT CASE"
    ws["A1"].font = st["title"]
    ws["A2"] = (
        "Every value in columns B-F is a formula linked to the Inputs tab and the Debt Schedule. "
        "The check block compares the live output with the Python model."
    )
    ws["A2"].font = st["note"]

    _header_row(ws, 4, ["Line Item", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"], st)

    for key, row in LIVE.items():
        cell = ws.cell(row=row, column=1, value=REVENUE_LABELS[key])
        cell.font = st["bold"] if key in BOLD_ROWS else st["regular"]
        cell.border = st["border"]

    for i, col in enumerate(COLS):
        prev = COLS[i - 1] if i > 0 else None

        # Revenue and the full USALI cost stack.
        ws[f"{col}{LIVE['occupancy']}"] = (
            f"={_inp('mature_occupancy')}*{_inp_row(INPUT_ROW['ramp_y1'] + i)}"
        )
        ws[f"{col}{LIVE['occupied_days']}"] = f"=365*{col}{LIVE['occupancy']}"
        ws[f"{col}{LIVE['room_nights']}"] = f"={col}{LIVE['occupied_days']}*{_inp('double_rooms')}"
        ws[f"{col}{LIVE['house_nights']}"] = f"={col}{LIVE['occupied_days']}*{_inp('full_houses')}"
        ws[f"{col}{LIVE['guests']}"] = f"={col}{LIVE['occupied_days']}*{_inp('guests_per_occupied_day')}"
        ws[f"{col}{LIVE['room_rev']}"] = f"={col}{LIVE['room_nights']}*{_inp('room_adr')}"
        ws[f"{col}{LIVE['house_rev']}"] = f"={col}{LIVE['house_nights']}*{_inp('house_adr')}"
        ws[f"{col}{LIVE['rest_rev']}"] = f"={col}{LIVE['guests']}*{_inp('restaurant_ticket')}"
        ws[f"{col}{LIVE['total_rev']}"] = f"=SUM({col}{LIVE['room_rev']}:{col}{LIVE['rest_rev']})"
        ws[f"{col}{LIVE['cogs']}"] = f"={col}{LIVE['rest_rev']}*{_inp('restaurant_cogs_ratio')}"
        ws[f"{col}{LIVE['ota']}"] = (
            f"=({col}{LIVE['room_rev']}+{col}{LIVE['house_rev']})*{_inp('ota_share')}*{_inp('ota_commission_rate')}"
        )
        ws[f"{col}{LIVE['amenities']}"] = f"={col}{LIVE['occupied_days']}*{_inp('amenities_per_occupied_day')}"
        ws[f"{col}{LIVE['breakfast']}"] = f"={col}{LIVE['guests']}*{_inp('breakfast_per_guest_day')}"
        ws[f"{col}{LIVE['variable_costs']}"] = f"=SUM({col}{LIVE['cogs']}:{col}{LIVE['breakfast']})"
        ws[f"{col}{LIVE['gross_margin']}"] = f"={col}{LIVE['total_rev']}-{col}{LIVE['variable_costs']}"
        ws[f"{col}{LIVE['payroll']}"] = f"={_inp('annual_payroll')}"
        ws[f"{col}{LIVE['fixed_opex']}"] = f"={_inp('fixed_opex')}"
        ws[f"{col}{LIVE['ebitda']}"] = (
            f"={col}{LIVE['gross_margin']}-{col}{LIVE['payroll']}-{col}{LIVE['fixed_opex']}"
        )
        ws[f"{col}{LIVE['ffe_reserve']}"] = f"={col}{LIVE['total_rev']}*{_inp('ffe_reserve_rate')}"
        ws[f"{col}{LIVE['ppe_depreciation']}"] = f"={_inp('annual_ppe_depreciation')}"
        ws[f"{col}{LIVE['preopening_amort']}"] = f"={_inp('preopening_costs')}/{_inp('preopening_amort_years')}"
        ws[f"{col}{LIVE['depreciation']}"] = f"={col}{LIVE['ppe_depreciation']}+{col}{LIVE['preopening_amort']}"
        ws[f"{col}{LIVE['ebit']}"] = f"={col}{LIVE['ebitda']}-{col}{LIVE['depreciation']}"

        # Debt (annual summary rows 16-20 of the Debt Schedule).
        debt_row = DEBT_SUMMARY_START + i
        ws[f"{col}{LIVE['begin_debt']}"] = f"='Debt Schedule'!B{debt_row}"
        ws[f"{col}{LIVE['senior_interest']}"] = f"='Debt Schedule'!E{debt_row}"
        ws[f"{col}{LIVE['principal']}"] = f"='Debt Schedule'!D{debt_row}"
        ws[f"{col}{LIVE['end_debt']}"] = f"='Debt Schedule'!F{debt_row}"
        if i == 0:
            ws[f"{col}{LIVE['bridge_interest']}"] = f"={_inp('input_vat')}*{_inp('vat_bridge_interest_rate')}"
        elif i == 1:
            ws[f"{col}{LIVE['bridge_interest']}"] = f"={_inp('input_vat')}*{_inp('vat_bridge_interest_rate')}*0.5"
        else:
            ws[f"{col}{LIVE['bridge_interest']}"] = "=0"
        ws[f"{col}{LIVE['interest_expense']}"] = (
            f"={col}{LIVE['senior_interest']}+{col}{LIVE['bridge_interest']}"
        )
        ws[f"{col}{LIVE['ebt']}"] = f"={col}{LIVE['ebit']}-{col}{LIVE['interest_expense']}"

        # Spanish corporate tax with BIN carry-forward.
        ws[f"{col}{LIVE['bin_opening']}"] = "=0" if i == 0 else f"={prev}{LIVE['bin_closing']}"
        ws[f"{col}{LIVE['taxable_base']}"] = f"=MAX(0,{col}{LIVE['ebt']}-{col}{LIVE['bin_opening']})"
        ws[f"{col}{LIVE['tax']}"] = f"={col}{LIVE['taxable_base']}*{_inp('corporate_tax_rate')}"
        ws[f"{col}{LIVE['bin_closing']}"] = (
            f"={col}{LIVE['bin_opening']}"
            f"+IF({col}{LIVE['ebt']}<0,-{col}{LIVE['ebt']},0)"
            f"-IF({col}{LIVE['ebt']}>0,MIN({col}{LIVE['bin_opening']},{col}{LIVE['ebt']}),0)"
        )
        ws[f"{col}{LIVE['net_income']}"] = f"={col}{LIVE['ebt']}-{col}{LIVE['tax']}"

        # Cash flow.
        ws[f"{col}{LIVE['cfo']}"] = f"={col}{LIVE['net_income']}+{col}{LIVE['depreciation']}"
        if i == 0:
            ws[f"{col}{LIVE['cfi']}"] = (
                f"=-({_inp('cash_capex')}+{_inp('idc')}+{_inp('input_vat')}+{_inp('preopening_costs')}"
                f"+{_inp('initial_working_capital')}+{_inp('dsra')}+{col}{LIVE['ffe_reserve']})"
            )
        elif i == 1:
            ws[f"{col}{LIVE['cfi']}"] = f"={_inp('input_vat')}-{col}{LIVE['ffe_reserve']}"
        else:
            ws[f"{col}{LIVE['cfi']}"] = f"=-{col}{LIVE['ffe_reserve']}"

        if i == 0:
            ws[f"{col}{LIVE['cff']}"] = (
                f"={_inp('senior_debt_principal')}+{_inp('cash_equity')}+{_inp('input_vat')}"
                f"-{col}{LIVE['principal']}"
            )
        elif i == 1:
            ws[f"{col}{LIVE['cff']}"] = (
                f"={_inp('leader_grant')}-{_inp('input_vat')}-{col}{LIVE['principal']}"
            )
        else:
            ws[f"{col}{LIVE['cff']}"] = f"=-{col}{LIVE['principal']}"

        ws[f"{col}{LIVE['net_cash_flow']}"] = (
            f"={col}{LIVE['cfo']}+{col}{LIVE['cfi']}+{col}{LIVE['cff']}"
        )
        if i == 0:
            ws[f"{col}{LIVE['end_cash']}"] = f"={_inp('initial_working_capital')}+{col}{LIVE['net_cash_flow']}"
        else:
            ws[f"{col}{LIVE['end_cash']}"] = f"={prev}{LIVE['end_cash']}+{col}{LIVE['net_cash_flow']}"

        ws[f"{col}{LIVE['cfads']}"] = (
            f"={col}{LIVE['ebitda']}-{col}{LIVE['ffe_reserve']}-{col}{LIVE['tax']}"
        )
        ws[f"{col}{LIVE['debt_service']}"] = (
            f"={col}{LIVE['senior_interest']}+{col}{LIVE['principal']}"
        )
        ws[f"{col}{LIVE['dscr']}"] = f"={col}{LIVE['cfads']}/{col}{LIVE['debt_service']}"

        # Balance sheet.
        ws[f"{col}{LIVE['gross_ppe']}"] = f"={_inp('total_capex')}+{_inp('idc')}"
        if i == 0:
            ws[f"{col}{LIVE['accum_depr']}"] = f"={col}{LIVE['ppe_depreciation']}"
            ws[f"{col}{LIVE['accum_amort']}"] = f"={col}{LIVE['preopening_amort']}"
            ws[f"{col}{LIVE['retained_earnings']}"] = f"={col}{LIVE['net_income']}"
            ws[f"{col}{LIVE['capital_subsidies']}"] = "=0"
            ws[f"{col}{LIVE['restricted_cash']}"] = f"={_inp('dsra')}+{col}{LIVE['ffe_reserve']}"
        else:
            ws[f"{col}{LIVE['accum_depr']}"] = f"={prev}{LIVE['accum_depr']}+{col}{LIVE['ppe_depreciation']}"
            ws[f"{col}{LIVE['accum_amort']}"] = f"={prev}{LIVE['accum_amort']}+{col}{LIVE['preopening_amort']}"
            ws[f"{col}{LIVE['retained_earnings']}"] = f"={prev}{LIVE['retained_earnings']}+{col}{LIVE['net_income']}"
            if i == 1:
                ws[f"{col}{LIVE['capital_subsidies']}"] = f"={prev}{LIVE['capital_subsidies']}+{_inp('leader_grant')}"
            else:
                ws[f"{col}{LIVE['capital_subsidies']}"] = f"={prev}{LIVE['capital_subsidies']}"
            ws[f"{col}{LIVE['restricted_cash']}"] = f"={prev}{LIVE['restricted_cash']}+{col}{LIVE['ffe_reserve']}"

        ws[f"{col}{LIVE['net_ppe']}"] = f"={col}{LIVE['gross_ppe']}-{col}{LIVE['accum_depr']}"
        ws[f"{col}{LIVE['net_intangibles']}"] = f"={_inp('preopening_costs')}-{col}{LIVE['accum_amort']}"
        ws[f"{col}{LIVE['vat_receivable']}"] = f"={_inp('input_vat')}" if i == 0 else "=0"
        ws[f"{col}{LIVE['total_assets']}"] = (
            f"={col}{LIVE['net_ppe']}+{col}{LIVE['net_intangibles']}+{col}{LIVE['end_cash']}"
            f"+{col}{LIVE['restricted_cash']}+{col}{LIVE['vat_receivable']}"
        )
        ws[f"{col}{LIVE['vat_bridge']}"] = f"={_inp('input_vat')}" if i == 0 else "=0"
        ws[f"{col}{LIVE['total_liabilities']}"] = f"={col}{LIVE['end_debt']}+{col}{LIVE['vat_bridge']}"
        ws[f"{col}{LIVE['share_capital']}"] = f"={_inp('land_in_kind')}+{_inp('cash_equity')}"
        ws[f"{col}{LIVE['total_equity']}"] = (
            f"={col}{LIVE['share_capital']}+{col}{LIVE['retained_earnings']}+{col}{LIVE['capital_subsidies']}"
        )
        ws[f"{col}{LIVE['bs_check']}"] = (
            f"={col}{LIVE['total_assets']}-{col}{LIVE['total_liabilities']}-{col}{LIVE['total_equity']}"
        )

    # Formats.
    for key, row in LIVE.items():
        for col in COLS:
            cell = ws[f"{col}{row}"]
            cell.border = st["border"]
            if key == "occupancy":
                cell.number_format = "0.00%"
            elif key == "dscr":
                cell.number_format = "0.00"
            elif key in COUNT_ROWS:
                cell.number_format = "#,##0.0"
            elif key in MONEY_ROWS:
                cell.number_format = "#,##0.00"

    # Checks block: live vs. Python.
    ws.cell(row=LIVE_CHECK_HEADER - 1, column=1, value="CHECKS: LIVE MODEL VS. PYTHON OUTPUT").font = st["bold"]
    _header_row(ws, LIVE_CHECK_HEADER, ["Check", "Python", "Live", "Difference", "Status"], st)
    checks = [
        ("Revenue Year 1 (EUR)", float(df_kpi.iloc[0]["total_revenue"]), f"=B{LIVE['total_rev']}", 1.0),
        ("EBITDA Year 1 (EUR)", float(df_kpi.iloc[0]["ebitda"]), f"=B{LIVE['ebitda']}", 1.0),
        ("DSCR Year 2 - binding year (x)", float(df_kpi.iloc[1]["dscr"]), f"=C{LIVE['dscr']}", 0.01),
        ("Ending cash Year 1 (EUR)", float(df_kpi.iloc[0]["ending_cash"]), f"=B{LIVE['end_cash']}", 1.0),
        ("Ending cash Year 2 (EUR)", float(df_kpi.iloc[1]["ending_cash"]), f"=C{LIVE['end_cash']}", 1.0),
        ("Net income Year 1 (EUR)", float(df_kpi.iloc[0]["net_income"]), f"=B{LIVE['net_income']}", 1.0),
        ("Minimum DSCR Years 1-5 (x)", float(df_kpi["dscr"].min()), f"=MIN(B{LIVE['dscr']}:F{LIVE['dscr']})", 0.01),
        ("Maximum balance-sheet discrepancy (EUR)", 0.0, f"=MAX(ABS(B{LIVE['bs_check']}),ABS(C{LIVE['bs_check']}),ABS(D{LIVE['bs_check']}),ABS(E{LIVE['bs_check']}),ABS(F{LIVE['bs_check']}))", 1.0),
    ]
    for i, (name, py_val, live_formula, tolerance) in enumerate(checks, start=LIVE_CHECK_START):
        ws.cell(row=i, column=1, value=name).font = st["bold"]
        ws.cell(row=i, column=1).border = st["border"]
        ws.cell(row=i, column=2, value=py_val).number_format = (
            "0.00" if "(x)" in name else "#,##0.00"
        )
        ws.cell(row=i, column=2).border = st["border"]
        ws.cell(row=i, column=3, value=live_formula).number_format = (
            "0.00" if "(x)" in name else "#,##0.00"
        )
        ws.cell(row=i, column=3).border = st["border"]
        ws.cell(row=i, column=4, value=f"=C{i}-B{i}").number_format = (
            "0.00" if "(x)" in name else "#,##0.00"
        )
        ws.cell(row=i, column=4).border = st["border"]
        _status_formula(ws, i, 5, f"ABS(D{i})<={tolerance}", st)

    # Covenant and audit flags.
    cov_row = LIVE_CHECK_START + len(checks)
    ws.cell(row=cov_row, column=1, value="Covenant test: minimum DSCR >= target DSCR").font = st["bold"]
    ws.cell(row=cov_row, column=1).border = st["border"]
    ws.cell(row=cov_row, column=4, value=f"=MIN(B{LIVE['dscr']}:F{LIVE['dscr']})").number_format = "0.00"
    ws.cell(row=cov_row, column=4).border = st["border"]
    _status_formula(ws, cov_row, 5, f"D{cov_row}>={_inp('target_dscr')}", st)

    note_row = cov_row + 2
    ws.cell(row=note_row, column=1, value=(
        "Note: the VAT bridge is a balance-sheet item (drawn in Year 1, repaid with the AEAT refund in Year 2), "
        "not an operating inflow. CFO is net income plus D&A because operating VAT is a pass-through."
    )).font = st["note"]
    ws.cell(row=note_row, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=6)
    ws.row_dimensions[note_row].height = 32

    ws.column_dimensions["A"].width = 52
    for col in COLS:
        ws.column_dimensions[col].width = 18


# ---------------------------------------------------------------------------
# Funding & Audit
# ---------------------------------------------------------------------------
def build_funding_audit(wb, st: Dict[str, Any], case_facts: Dict[str, Dict[str, Any]], gate: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Funding & Audit", index=3)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "SOURCES & USES, CLOSE-DAY RECONCILIATION, PHASE II GATE AND COMPUTED AUDIT"
    ws["A1"].font = st["title"]
    ws["A2"] = (
        "The honest funding layer: it books every close-day use, tests the requested facility against the "
        "DSCR cap and lets the audit fail where the business case fails."
    )
    ws["A2"].font = st["note"]

    # Section 1: capital structure by case.
    ws["A4"] = "1. CAPITAL STRUCTURE AND FUNDING TEST BY CASE"
    ws["A4"].font = st["bold"]
    _header_row(
        ws,
        5,
        ["Case", "Total uses at close", "Total sources at close", "Gap at close", "VAT bridge Y1",
         "DSCR-capped debt", "Equity / CapEx %", "Minimum DSCR", "Binding constraint", "Status", "Check"],
        st,
    )
    for r, case in enumerate(("management", "market", "promoter"), start=6):
        f = case_facts[case]["result"]
        _write_row(ws, r, [
            case,
            f.total_uses_at_close,
            f.total_sources_at_close,
            f.funding_gap_at_close,
            f.vat_bridge_drawn_y1,
            f.dscr_cap_principal,
            f.equity_to_capex_pct / 100.0,
            f.dscr_min,
            f.binding_constraint,
            f.funding_status,
        ], st)
        ws.cell(row=r, column=1).font = st["bold"]
        ws.cell(row=r, column=7).number_format = "0.00%"
        ws.cell(row=r, column=8).number_format = "0.00"
        cell = ws.cell(row=r, column=11, value=f'=IF(ABS(D{r})<1,"PASS","FAIL")')
        cell.font = st["bold"]
        cell.alignment = Alignment(horizontal="center")

    # Section 2: close-day sources & uses (management).
    ws["A11"] = "2. CLOSE-DAY SOURCES & USES - MANAGEMENT CASE (EUR)"
    ws["A11"].font = st["bold"]
    _header_row(ws, 12, ["Item", "Amount"], st)
    mgmt = case_facts["management"]["result"]
    uses = [
        ("Land contributed in kind", mgmt.land_in_kind),
        ("Cash CapEx (works, kitchen, FF&E, biopool, digital, fees)", mgmt.cash_capex),
        ("Interest during construction (IDC)", mgmt.idc),
        ("Input VAT (bridge-funded)", mgmt.input_vat),
        ("Pre-opening costs (capitalised)", mgmt.pre_opening_costs),
        ("Initial working capital", mgmt.initial_working_capital),
        ("DSRA (six months of debt service)", mgmt.dsra),
        ("Operating cash buffer", mgmt.operating_cash_buffer),
    ]
    for r, (label, value) in enumerate(uses, start=13):
        ws.cell(row=r, column=1, value=label).border = st["border"]
        cell = ws.cell(row=r, column=2, value=value)
        cell.number_format = "#,##0.00"
        cell.border = st["border"]

    ws.cell(row=21, column=1, value="TOTAL USES").font = st["bold"]
    ws.cell(row=21, column=1).border = st["border"]
    ws.cell(row=21, column=2, value="=SUM(B13:B20)").font = st["bold"]
    ws.cell(row=21, column=2).number_format = "#,##0.00"
    ws.cell(row=21, column=2).border = st["border"]

    sources = [
        ("Senior debt (35% LTV)", mgmt.senior_debt),
        ("VAT bridge (separate EUR 175k facility)", mgmt.vat_bridge),
        ("Land in kind", mgmt.land_in_kind),
        ("Cash equity (the plug that closes the structure)", mgmt.cash_equity_required),
    ]
    for r, (label, value) in enumerate(sources, start=22):
        ws.cell(row=r, column=1, value=label).border = st["border"]
        cell = ws.cell(row=r, column=2, value=value)
        cell.number_format = "#,##0.00"
        cell.border = st["border"]

    ws.cell(row=26, column=1, value="TOTAL SOURCES").font = st["bold"]
    ws.cell(row=26, column=1).border = st["border"]
    ws.cell(row=26, column=2, value="=SUM(B22:B25)").font = st["bold"]
    ws.cell(row=26, column=2).number_format = "#,##0.00"
    ws.cell(row=26, column=2).border = st["border"]

    ws.cell(row=27, column=1, value="FUNDING GAP AT CLOSE (sources - uses)").font = st["bold"]
    ws.cell(row=27, column=1).border = st["border"]
    ws.cell(row=27, column=2, value="=B26-B21").font = st["bold"]
    ws.cell(row=27, column=2).number_format = "#,##0.00"
    ws.cell(row=27, column=2).border = st["border"]
    status = ws.cell(row=27, column=3, value='=IF(ABS(B27)<1,"PASS","FAIL")')
    status.font = st["bold"]
    status.alignment = Alignment(horizontal="center")

    ws.cell(row=28, column=1, value="Cash equity / total CapEx").border = st["border"]
    ws.cell(row=28, column=2, value=f"=B25/{_inp('total_capex')}").number_format = "0.00%"
    ws.cell(row=28, column=2).border = st["border"]
    ws.cell(row=29, column=1, value="Senior debt / total CapEx (LTV)").border = st["border"]
    ws.cell(row=29, column=2, value=f"=B22/{_inp('total_capex')}").number_format = "0.00%"
    ws.cell(row=29, column=2).border = st["border"]

    # Section 3: Phase II gate.
    ws["A31"] = "3. PHASE II PHASE GATE (PHASE I MUST BE COVENANT-COMPLIANT AND FUND THE EXPANSION)"
    ws["A31"].font = st["bold"]
    gate_rows = [
        ("Phase I cash at end of Year 2 (EUR)", gate["phase1_cash_end_y2"], "#,##0.00"),
        ("Phase II cash need (net CapEx + input VAT) (EUR)", gate["phase2_cash_need"], "#,##0.00"),
        ("Phase II funding gap (EUR)", gate["phase2_funding_gap"], "#,##0.00"),
        ("Phase I DSCR Year 3 (x)", gate["phase1_dscr_y3"], "0.00"),
        ("DSCR condition (>= 1.25x)", "PASS" if gate["dscr_condition_met"] else "FAIL", "@"),
        ("Cash condition (Phase I cash >= Phase II need)", "PASS" if gate["cash_condition_met"] else "FAIL", "@"),
        ("Phase II proceed", "YES" if gate["phase2_proceed"] else "NO", "@"),
    ]
    for r, (label, value, fmt) in enumerate(gate_rows, start=32):
        ws.cell(row=r, column=1, value=label).font = st["bold"]
        ws.cell(row=r, column=1).border = st["border"]
        cell = ws.cell(row=r, column=2, value=value)
        cell.border = st["border"]
        cell.font = st["regular"]
        cell.number_format = fmt
        if isinstance(value, str) and value in ("PASS", "FAIL", "YES", "NO"):
            cell.font = st["bold"]
            cell.fill = st["green"] if value in ("PASS", "YES") else st["red"]
        if r == 38:
            cell.fill = st["green"] if gate["phase2_proceed"] else st["red"]
            cell.font = st["bold"]

    # Section 4: computed audit rules.
    ws["A41"] = "4. COMPUTED AUDIT RULES (THE AUDIT CAN FAIL)"
    ws["A41"].font = st["bold"]
    _header_row(ws, 42, ["Rule ID", "Rule", "Severity", "Status", "Actual", "Threshold"], st)
    payload = ModelAuditEngine().generate_audit_payload()
    for r, rule in enumerate(payload["guardrail_audit_rules"], start=43):
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

    status_row = 43 + len(payload["guardrail_audit_rules"])
    ws.cell(row=status_row, column=1, value="AUDIT VERDICT").font = st["bold"]
    ws.cell(row=status_row, column=2, value=payload["execution_status"]["audit_verdict"]).font = st["bold"]
    ws.cell(row=status_row, column=2).fill = st["amber"]

    # Section 5: key findings.
    findings_row = status_row + 2
    ws.cell(row=findings_row, column=1, value="5. KEY FUNDING FINDINGS").font = st["bold"]
    findings = [
        (
            f"Close-day uses are EUR {mgmt.total_uses_at_close:,.2f} against EUR {mgmt.total_sources_at_close:,.2f} "
            "of sources. The structure closes only because the cash equity line is a reported plug of "
            f"EUR {mgmt.cash_equity_required:,.2f} ({mgmt.equity_to_capex_pct:.1f}% of CapEx), not 30%."
        ),
        (
            f"The requested EUR {mgmt.senior_debt:,.2f} facility is within 35% LTV but breaches the 1.25x covenant "
            f"in Year 2 (1.15x). The DSCR cap is EUR {mgmt.dscr_cap_principal:,.2f} "
            f"({mgmt.dscr_cap_ltv_pct:.1f}% LTV)."
        ),
        (
            f"The VAT bridge is EUR {mgmt.vat_bridge:,.2f}, inside the EUR {mgmt.vat_bridge_limit:,.2f} limit, and "
            "is repaid with the AEAT refund in Month 18. It is a separate facility, not the old EUR 50k revolver."
        ),
        (
            "The LEADER grant (EUR 163,000) arrives in Month 14 and is booked as a capital subsidy; it cannot fund "
            "close-day uses and is not double-counted in Phase II."
        ),
        (
            f"Phase II needs EUR {gate['phase2_cash_need']:,.2f} but Phase I generates EUR {gate['phase1_cash_end_y2']:,.2f} "
            f"of cash by the end of Year 2: a EUR {abs(gate['phase2_funding_gap']):,.2f} funding gap. The gate is NO."
        ),
        (
            f"The audit verdict is {payload['execution_status']['audit_verdict']}: "
            f"{payload['execution_status']['total_rules_passed']} of "
            f"{payload['execution_status']['total_rules_evaluated']} rules pass. This is deliberate, not a bug."
        ),
    ]
    for r, text in enumerate(findings, start=findings_row + 1):
        cell = ws.cell(row=r, column=1, value=f"- {text}")
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=11)
        ws.row_dimensions[r].height = 40

    widths = {"A": 58, "B": 24, "C": 22, "D": 16, "E": 22, "F": 20, "G": 18, "H": 14, "I": 26, "J": 58, "K": 10}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def add_live_model_tabs(wb, engine: FinancialModelEngine, df_proj, df_kpi, debt_sched) -> None:
    """Adds the live tabs (and the formula-driven debt schedule) to the workbook."""
    st = _styles()

    # One deterministic projection per case, computed once and shared.
    case_facts: Dict[str, Dict[str, Any]] = {}
    for case in ("management", "market", "promoter"):
        funding_engine = SourcesUsesEngine(case=case)
        result = funding_engine.compute()
        df = funding_engine.df
        case_facts[case] = {
            "result": result,
            "revenue_y1": float(df.iloc[0]["total_revenue"]),
            "ebitda_y1": float(df.iloc[0]["ebitda"]),
            "dscr_y1": result.dscr_y1,
        }

    exp_engine = ExpansionFinancialEngine()
    mgmt = case_facts["management"]["result"]
    gate = exp_engine.compute_phase_gate(
        phase1_cash_end_y2=mgmt.cash_by_year[1],
        phase1_dscr_y3=mgmt.dscr_by_year[2],
    )

    build_readme(wb, st, case_facts, gate)
    build_inputs(wb, engine, df_proj, st)
    build_debt_schedule(wb, st)
    build_live_model(wb, engine, df_kpi, st)
    build_funding_audit(wb, st, case_facts, gate)

    preferred = [
        "Read Me & Checks", "Inputs", "Live Model", "Funding & Audit",
        "Executive Scorecard", "3-Statement Model", "Debt Schedule",
        "Scenario Stress-Testing", "Monte Carlo Risk", "Credit Risk & Copula",
        "Unit Economics & Runway", "Phase II Expansion",
    ]
    existing = [name for name in preferred if name in wb.sheetnames]
    remaining = [name for name in wb.sheetnames if name not in existing]
    wb._sheets = [wb[name] for name in existing + remaining]
