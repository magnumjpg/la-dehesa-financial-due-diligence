"""
Live, formula-driven Excel tabs for the T8 cabin turnaround (Act 4 / Act 5).

Three tabs are added to the master workbook:

1. ``T8 Inputs``        - every T8 assumption in one place (blue cells).
2. ``T8 Debt Schedule`` - 240-month French amortisation of the EUR 450,000
                          senior facility (12-month interest-only grace,
                          20-year tenure) and a SUMIF annual summary.
3. ``T8 Live Model``    - revenue, USALI variable costs, EBITDA, tax with BIN
                          carry-forward, cash flow, balance sheet, DSCR and a
                          live returns block (project / equity IRR on the cash
                          and all-in bases).

Nothing in the live block is a pasted value: columns B-F are formulas linked to
``T8 Inputs`` and ``T8 Debt Schedule``. The check block compares the live
output with the Python ``TurnaroundEngine`` so a broken link fails loudly.
"""

from typing import Any, Dict, List

from openpyxl.styles import Alignment, Font, PatternFill

from src.data.live_excel import _header_row, _status_formula, _styles


# ---------------------------------------------------------------------------
# Stable row maps. Do not renumber without updating the cross-sheet formulas.
# ---------------------------------------------------------------------------
T8_INPUT_ROW: Dict[str, int] = {
    "cabins_count": 5,
    "cabin_adr": 6,
    "cabin_occ_y1": 7,
    "cabin_occ_y2": 8,
    "cabin_occ_y3": 9,
    "cabin_occ_y4": 10,
    "cabin_occ_y5": 11,
    "lodge_enabled": 12,
    "lodge_adr": 13,
    "lodge_occ_y1": 14,
    "lodge_occ_y2": 15,
    "lodge_occ_y3": 16,
    "lodge_occ_y4": 17,
    "lodge_occ_y5": 18,
    "cabin_guests": 19,
    "lodge_guests": 20,
    "housekeeping_cabin": 21,
    "housekeeping_lodge": 22,
    "energy_cabin": 23,
    "energy_lodge": 24,
    "consumables_cabin": 25,
    "consumables_lodge": 26,
    "breakfast": 27,
    "ota_share": 28,
    "ota_commission": 29,
    "payment_fee": 30,
    "annual_payroll": 31,
    "fixed_opex": 32,
    "ffe_reserve": 33,
    "experiences_y1": 34,
    "experiences_y2": 35,
    "experiences_y3": 36,
    "experiences_y4": 37,
    "experiences_y5": 38,
    "experience_margin": 39,
    "corporate_tax": 40,
    "cash_capex": 41,
    "land_in_kind": 42,
    "total_capex": 43,
    "annual_depreciation": 44,
    "preopening": 45,
    "preopening_years": 46,
    "arrangement_fee": 47,
    "senior_debt": 48,
    "interest_rate": 49,
    "tenure_years": 50,
    "grace_months": 51,
    "idc": 52,
    "input_vat": 53,
    "vat_bridge_rate": 54,
    "target_dscr": 55,
    "initial_working_capital": 56,
    "dsra": 57,
    "cash_equity": 58,
    "total_equity": 59,
    "exit_cap": 60,
    "exit_cost": 61,
    "discount_rate": 62,
}

T8_LIVE: Dict[str, int] = {
    "cabin_occ": 5,
    "lodge_occ": 6,
    "cabin_nights": 7,
    "lodge_nights": 8,
    "guests": 9,
    "cabin_rev": 10,
    "lodge_rev": 11,
    "exp_rev": 12,
    "total_rev": 13,
    "ota": 14,
    "housekeeping": 15,
    "breakfast": 16,
    "energy": 17,
    "consumables": 18,
    "payment": 19,
    "exp_cogs": 20,
    "total_variable": 21,
    "gross_margin": 22,
    "payroll": 23,
    "fixed_opex": 24,
    "ebitda": 25,
    "ffe": 26,
    "ppe_depr": 27,
    "preop_amort": 28,
    "depreciation": 29,
    "ebit": 30,
    "begin_debt": 31,
    "senior_interest": 32,
    "principal": 33,
    "end_debt": 34,
    "bridge_interest": 35,
    "interest_expense": 36,
    "ebt": 37,
    "bin_opening": 38,
    "taxable_base": 39,
    "tax": 40,
    "bin_closing": 41,
    "net_income": 42,
    "cfo": 43,
    "cfi": 44,
    "cff": 45,
    "net_cash_flow": 46,
    "end_cash": 47,
    "cfads": 48,
    "debt_service": 49,
    "dscr": 50,
    "gross_ppe": 51,
    "accum_depr": 52,
    "accum_amort": 53,
    "retained_earnings": 54,
    "capital_subsidies": 55,
    "restricted_cash": 56,
    "net_ppe": 57,
    "net_intangibles": 58,
    "vat_receivable": 59,
    "total_assets": 60,
    "vat_bridge": 61,
    "total_liabilities": 62,
    "share_capital": 63,
    "total_equity": 64,
    "bs_check": 65,
    "fcff": 66,
    "fcfe": 67,
}

LIVE_LABELS: Dict[str, str] = {
    "cabin_occ": "Cabin occupancy",
    "lodge_occ": "Lodge occupancy",
    "cabin_nights": "Cabin nights sold",
    "lodge_nights": "Lodge nights sold",
    "guests": "Guest-nights",
    "cabin_rev": "Cabin revenue (EUR)",
    "lodge_rev": "Lodge revenue (EUR)",
    "exp_rev": "Experiences revenue (EUR)",
    "total_rev": "Total revenue (EUR)",
    "ota": "OTA commission (EUR)",
    "housekeeping": "Housekeeping (EUR)",
    "breakfast": "Breakfast baskets (EUR)",
    "energy": "Energy (EUR)",
    "consumables": "Consumables (EUR)",
    "payment": "Payment fees (EUR)",
    "exp_cogs": "Experience cost of sales (EUR)",
    "total_variable": "Total variable costs (EUR)",
    "gross_margin": "Gross margin (EUR)",
    "payroll": "Payroll, 2.0 FTE loaded (EUR)",
    "fixed_opex": "Fixed operating expenses (EUR)",
    "ebitda": "EBITDA (EUR)",
    "ffe": "FF&E reserve (EUR)",
    "ppe_depr": "PP&E depreciation (EUR)",
    "preop_amort": "Pre-opening + fee amortisation (EUR)",
    "depreciation": "Total depreciation (EUR)",
    "ebit": "EBIT (EUR)",
    "begin_debt": "Beginning senior debt (EUR)",
    "senior_interest": "Senior interest (EUR)",
    "principal": "Principal repayment (EUR)",
    "end_debt": "Ending senior debt (EUR)",
    "bridge_interest": "VAT bridge interest (EUR)",
    "interest_expense": "Total interest expense (EUR)",
    "ebt": "EBT (EUR)",
    "bin_opening": "BIN carried forward, opening (EUR)",
    "taxable_base": "Taxable base (EUR)",
    "tax": "Corporate tax (EUR)",
    "bin_closing": "BIN carried forward, closing (EUR)",
    "net_income": "Net income (EUR)",
    "cfo": "Cash flow from operations (EUR)",
    "cfi": "Cash flow from investing (EUR)",
    "cff": "Cash flow from financing (EUR)",
    "net_cash_flow": "Net cash flow (EUR)",
    "end_cash": "Ending cash (EUR)",
    "cfads": "CFADS (EUR)",
    "debt_service": "Debt service (EUR)",
    "dscr": "DSCR (x)",
    "gross_ppe": "Gross PP&E (EUR)",
    "accum_depr": "Accumulated depreciation (EUR)",
    "accum_amort": "Accumulated amortisation (EUR)",
    "retained_earnings": "Retained earnings (EUR)",
    "capital_subsidies": "Capital subsidies (EUR)",
    "restricted_cash": "Restricted cash / DSRA + FF&E (EUR)",
    "net_ppe": "Net PP&E (EUR)",
    "net_intangibles": "Net intangibles (EUR)",
    "vat_receivable": "VAT receivable (EUR)",
    "total_assets": "Total assets (EUR)",
    "vat_bridge": "VAT bridge drawn (EUR)",
    "total_liabilities": "Total liabilities (EUR)",
    "share_capital": "Share capital + land in kind (EUR)",
    "total_equity": "Total equity (EUR)",
    "bs_check": "Balance-sheet check (EUR)",
    "fcff": "FCFF, unlevered (EUR)",
    "fcfe": "FCFE, proper (EUR)",
}

BOLD_ROWS = {
    "total_rev", "gross_margin", "ebitda", "ebit", "net_income",
    "end_cash", "dscr", "total_assets", "total_equity", "bs_check",
}

COLS = ["B", "C", "D", "E", "F"]
T8_DEBT_SHEET = "T8 Debt Schedule"
DEBT_PARAM_START = 4
DEBT_SUMMARY_HEADER = 15
DEBT_SUMMARY_START = 16
DEBT_MONTHLY_HEADER = 23
DEBT_MONTHLY_START = 24

CHECK_HEADER = 71
CHECK_START = 72
RETURNS_HEADER = 86
RETURNS_START = 87
CF_HEADER = 99
CF_START = 100


def _tinp(key: str) -> str:
    """Absolute reference to a T8 Inputs cell, e.g. 'T8 Inputs'!$B$48."""
    return f"'T8 Inputs'!$B${T8_INPUT_ROW[key]}"


def _t8_debt_ref(col: str, year_index: int) -> str:
    return f"'{T8_DEBT_SHEET}'!{col}{DEBT_SUMMARY_START + year_index}"


# ---------------------------------------------------------------------------
# T8 Inputs
# ---------------------------------------------------------------------------
def build_t8_inputs(wb, turnaround, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="T8 Inputs")
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "T8 INPUTS - CABIN TURNAROUND (ALL HARD-CODED ASSUMPTIONS)"
    ws["A1"].font = st["title"]
    ws["A2"] = (
        "Change any blue input and both T8 Debt Schedule and T8 Live Model "
        "recalculate. The base case is six 40 m2 modular cabins plus the "
        "caseron converted into a four-bedroom lodge; there is no commercial "
        "restaurant."
    )
    ws["A2"].font = st["note"]

    _header_row(ws, 4, ["Input", "Value", "Unit", "Source / basis"], st)

    t = turnaround.config
    fin = turnaround.engine.financing
    capex = turnaround.engine.capex
    uses = turnaround.use_of_funds

    inputs = [
        ("Cabins", t.cabins.count, "count", "cabins", "Six modular Nordic cabins, 2 bedrooms, 35-45 m2"),
        ("Cabin ADR", t.cabins.adr, "money", "EUR/night", "Net ADR, no nominal uplift after stabilisation"),
        ("Cabin occupancy Y1", t.cabins.occupancy[0], "pct", "%", "First operating year"),
        ("Cabin occupancy Y2", t.cabins.occupancy[1], "pct", "%", "Ramp year"),
        ("Cabin occupancy Y3", t.cabins.occupancy[2], "pct", "%", "Stabilised"),
        ("Cabin occupancy Y4", t.cabins.occupancy[3], "pct", "%", "Stabilised"),
        ("Cabin occupancy Y5", t.cabins.occupancy[4], "pct", "%", "Stabilised"),
        ("Lodge enabled", 1 if t.lodge.enabled else 0, "count", "0/1", "Caserón converted into one four-bedroom lodge"),
        ("Lodge ADR", t.lodge.adr, "money", "EUR/night", "Whole-lodge nightly rate"),
        ("Lodge occupancy Y1", t.lodge.occupancy[0], "pct", "%", "First operating year"),
        ("Lodge occupancy Y2", t.lodge.occupancy[1], "pct", "%", "Ramp year"),
        ("Lodge occupancy Y3", t.lodge.occupancy[2], "pct", "%", "Stabilised"),
        ("Lodge occupancy Y4", t.lodge.occupancy[3], "pct", "%", "Stabilised"),
        ("Lodge occupancy Y5", t.lodge.occupancy[4], "pct", "%", "Stabilised"),
        ("Guests per cabin night", t.cabins.guests_per_occupied_night, "count", "guests", "2.4 guests per occupied cabin night"),
        ("Guests per lodge night", t.lodge.guests_per_occupied_night, "count", "guests", "Full house, 8 guests"),
        ("Housekeeping, cabin", t.cabins.housekeeping_per_night, "money", "EUR/night", "Cleaning and linen"),
        ("Housekeeping, lodge", t.lodge.housekeeping_per_night, "money", "EUR/night", "Cleaning and linen"),
        ("Energy, cabin", t.cabins.energy_per_night, "money", "EUR/night", "Variable utilities only"),
        ("Energy, lodge", t.lodge.energy_per_night, "money", "EUR/night", "Variable utilities only"),
        ("Consumables, cabin", t.cabins.consumables_per_night, "money", "EUR/night", "Amenities and supplies"),
        ("Consumables, lodge", t.lodge.consumables_per_night, "money", "EUR/night", "Amenities and supplies"),
        ("Breakfast per guest-day", t.opex.breakfast_per_guest_day, "money", "EUR/guest-day", "Breakfast basket, no kitchen brigade"),
        ("OTA share", t.opex.ota_share, "pct", "%", "55% of lodging sold through OTAs"),
        ("OTA commission", t.opex.ota_commission_rate, "pct", "%", "15% on OTA bookings"),
        ("Payment fee", t.opex.payment_fee_rate, "pct", "%", "Card and payment-gateway fees"),
        ("Annual payroll", t.opex.annual_payroll, "money", "EUR", "2.0 FTE x EUR 23,000 gross + 32.5% employer SS"),
        ("Fixed operating expenses", turnaround.engine.opex.total_fixed_opex, "money", "EUR", "Maintenance, insurance, utilities, marketing, PMS, admin"),
        ("FF&E reserve", t.opex.ffe_reserve_rate, "pct", "%", "3.5% of revenue"),
        ("Experiences revenue Y1", t.opex.experiences_revenue[0], "money", "EUR", "Guided walks, tastings and local partnerships"),
        ("Experiences revenue Y2", t.opex.experiences_revenue[1], "money", "EUR", "Ramp year"),
        ("Experiences revenue Y3", t.opex.experiences_revenue[2], "money", "EUR", "Stabilised"),
        ("Experiences revenue Y4", t.opex.experiences_revenue[3], "money", "EUR", "Stabilised"),
        ("Experiences revenue Y5", t.opex.experiences_revenue[4], "money", "EUR", "Stabilised"),
        ("Experience margin", t.opex.experience_margin, "pct", "%", "72% contribution margin"),
        ("Corporate tax rate", 0.25, "pct", "%", "Ley 27/2014, with BIN carry-forward"),
        ("Cash CapEx (net of VAT)", turnaround.engine.cash_capex, "money", "EUR", "Works 560k + fees 33.6k + contingency 28k"),
        ("Land contributed in kind", fin.land_in_kind_value, "money", "EUR", "25-ha estate at opportunity value"),
        ("All-in CapEx", capex.total_capex, "money", "EUR", "Cash CapEx + land"),
        ("Annual PP&E depreciation", capex.annual_depreciation, "money", "EUR", "Fiscal tables; land excluded"),
        ("Pre-opening costs", fin.pre_opening_costs, "money", "EUR", "Capitalised and amortised over five years"),
        ("Pre-opening amortisation years", 5, "count", "years", "Straight line"),
        ("Arrangement fee", fin.arrangement_fee, "money", "EUR", "1% of the EUR 450k facility, capitalised"),
        ("Senior debt principal", fin.senior_debt_principal, "money", "EUR", "EUR 450k facility"),
        ("Senior interest rate", fin.loan_interest_rate, "pct", "%", "Fixed 4.25%"),
        ("Loan tenure", float(fin.loan_tenure_years), "count", "years", "20 years"),
        ("Grace period", float(fin.grace_months), "count", "months", "12-month interest-only grace"),
        ("Interest during construction (IDC)", fin.idc_amount, "money", "EUR", "12 construction months, paid at close"),
        ("Input VAT (bridge-funded)", capex.total_input_vat, "money", "EUR", "21% on non-land CapEx; refunded by AEAT"),
        ("VAT bridge interest rate", fin.credit_line_interest, "pct", "%", "5.5% on the drawn bridge"),
        ("Target DSCR", fin.target_dscr, "x", "x", "Bank covenant floor"),
        ("Initial working capital", fin.initial_working_capital, "money", "EUR", "Opening cash"),
        ("DSRA", turnaround.engine.dsra_amount, "money", "EUR", "Six months of maximum annual debt service"),
        ("Cash equity (plug)", turnaround.cash_equity, "money", "EUR", "Closes the structure; 40.6% of cash CapEx"),
        ("Total equity at close", turnaround.all_in_equity, "money", "EUR", "Cash equity + land in kind"),
        ("Exit cap rate", t.exit_cap_rate, "pct", "%", "8.5% on exit-year EBITDA"),
        ("Exit cost rate", t.exit_cost_rate, "pct", "%", "3% selling costs"),
        ("Discount rate", t.discount_rate, "pct", "%", "9% cost of capital"),
    ]
    assert len(inputs) == len(T8_INPUT_ROW), "T8 inputs rows and map are out of sync"

    formats = {"pct": "0.00%", "money": "#,##0.00", "count": "#,##0", "x": "0.00"}
    for r, (name, value, kind, unit, source) in enumerate(inputs, start=5):
        c = ws.cell(row=r, column=1, value=name)
        c.font = st["bold"]
        c.border = st["border"]
        v = ws.cell(row=r, column=2, value=value)
        v.font = Font(name="Calibri", size=11, bold=True, color="1D4ED8")
        v.fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
        v.border = st["border"]
        v.number_format = formats[kind]
        u = ws.cell(row=r, column=3, value=unit)
        u.font = st["regular"]
        u.border = st["border"]
        s = ws.cell(row=r, column=4, value=source)
        s.font = st["note"]
        s.border = st["border"]

    ws["A65"] = "SOURCES & USES AT CLOSE (LIVE)"
    ws["A65"].font = st["bold"]
    _header_row(ws, 66, ["Use of funds", "EUR"], st)
    for i, key in enumerate(
        ("cash_capex", "idc", "arrangement_fee", "input_vat_bridge",
         "pre_opening", "working_capital", "dsra")
    ):
        r = 67 + i
        ws.cell(row=r, column=1, value=key.replace("_", " ").title()).font = st["regular"]
        ws.cell(row=r, column=1).border = st["border"]
        c = ws.cell(row=r, column=2, value=uses["uses"][key])
        c.number_format = "#,##0.00"
        c.border = st["border"]
    ws.cell(row=74, column=1, value="Total uses").font = st["bold"]
    ws.cell(row=74, column=1).border = st["border"]
    c = ws.cell(row=74, column=2, value=uses["total_uses"])
    c.number_format = "#,##0.00"
    c.font = st["bold"]
    c.border = st["border"]

    ws["A76"] = "SOURCES AT CLOSE (LIVE)"
    ws["A76"].font = st["bold"]
    _header_row(ws, 77, ["Source", "EUR"], st)
    for i, key in enumerate(("senior_debt", "vat_bridge", "cash_equity", "land_in_kind")):
        r = 78 + i
        ws.cell(row=r, column=1, value=key.replace("_", " ").title()).font = st["regular"]
        ws.cell(row=r, column=1).border = st["border"]
        c = ws.cell(row=r, column=2, value=uses["sources"][key])
        c.number_format = "#,##0.00"
        c.border = st["border"]
    ws.cell(row=82, column=1, value="Total sources").font = st["bold"]
    ws.cell(row=82, column=1).border = st["border"]
    c = ws.cell(row=82, column=2, value=uses["total_sources"])
    c.number_format = "#,##0.00"
    c.font = st["bold"]
    c.border = st["border"]
    ws.cell(row=84, column=1, value="Cash sources minus cash uses").font = st["bold"]
    ws.cell(row=84, column=1).border = st["border"]
    c = ws.cell(row=84, column=2, value=round(uses["total_cash_sources"] - uses["total_uses"], 2))
    c.number_format = "#,##0.00"
    c.font = st["bold"]
    c.border = st["border"]

    ws.column_dimensions["A"].width = 36
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 82


# ---------------------------------------------------------------------------
# T8 Debt Schedule
# ---------------------------------------------------------------------------
def build_t8_debt_schedule(wb, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title=T8_DEBT_SHEET)
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "T8 SENIOR DEBT - EUR 450,000, 4.25% FIXED, 20 YEARS, 12-MONTH GRACE"
    ws["A1"].font = st["title"]
    ws["A2"] = (
        "The French payment is computed over the 228 months that remain after "
        "the grace period. Each monthly payment is rounded to two decimals, "
        "matching the Python debt engine."
    )
    ws["A2"].font = st["note"]

    ws["A4"] = "LOAN PARAMETERS"
    ws["A4"].font = st["bold"]
    params = [
        ("Principal", f"={_tinp('senior_debt')}", "#,##0.00"),
        ("Annual interest rate", f"={_tinp('interest_rate')}", "0.00%"),
        ("Tenure (years)", f"={_tinp('tenure_years')}", "#,##0"),
        ("Grace (months)", f"={_tinp('grace_months')}", "#,##0"),
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

    ws["A14"] = "ANNUAL SUMMARY (SUMIF OF THE MONTHLY SCHEDULE)"
    ws["A14"].font = st["bold"]
    _header_row(
        ws,
        DEBT_SUMMARY_HEADER,
        ["Year", "Beginning balance", "Payment", "Principal", "Interest",
         "Ending balance", "Short-term debt", "Long-term debt"],
        st,
    )
    month_range = f"$B${DEBT_MONTHLY_START}:$B${DEBT_MONTHLY_START + 239}"
    for i in range(5):
        r = DEBT_SUMMARY_START + i
        ws.cell(row=r, column=1, value=i + 1)
        ws.cell(row=r, column=2, value="=$B$4" if i == 0 else f"=F{r - 1}")
        ws.cell(row=r, column=3, value=f"=SUMIF({month_range},$A{r},$D${DEBT_MONTHLY_START}:$D${DEBT_MONTHLY_START + 239})")
        ws.cell(row=r, column=4, value=f"=SUMIF({month_range},$A{r},$E${DEBT_MONTHLY_START}:$E${DEBT_MONTHLY_START + 239})")
        ws.cell(row=r, column=5, value=f"=SUMIF({month_range},$A{r},$F${DEBT_MONTHLY_START}:$F${DEBT_MONTHLY_START + 239})")
        ws.cell(row=r, column=6, value=f"=B{r}-D{r}")
        ws.cell(row=r, column=7, value=f"=SUMIF({month_range},$A{r}+1,$E${DEBT_MONTHLY_START}:$E${DEBT_MONTHLY_START + 239})")
        ws.cell(row=r, column=8, value=f"=MAX(0,F{r}-G{r})")
        for c in range(1, 9):
            cell = ws.cell(row=r, column=c)
            cell.border = st["border"]
            cell.font = st["regular"]
            cell.number_format = "#,##0" if c == 1 else "#,##0.00"

    ws.cell(
        row=DEBT_MONTHLY_HEADER - 1,
        column=1,
        value="MONTHLY AMORTISATION SCHEDULE (240 MONTHS)",
    ).font = st["bold"]
    _header_row(
        ws,
        DEBT_MONTHLY_HEADER,
        ["Month", "Year", "Beginning balance", "Payment", "Principal",
         "Interest", "Ending balance"],
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
# T8 Live Model
# ---------------------------------------------------------------------------
def build_t8_live_model(wb, turnaround, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="T8 Live Model")
    ws.views.sheetView[0].showGridLines = False
    ws["A1"] = "LIVE 5-YEAR MODEL - FORMULA-DRIVEN T8 CABIN TURNAROUND"
    ws["A1"].font = st["title"]
    ws["A2"] = (
        "Every value in columns B-F is a formula linked to T8 Inputs and the T8 "
        "Debt Schedule. The check block compares the live output with the "
        "Python TurnaroundEngine; the returns block prices the exit at 8.5%."
    )
    ws["A2"].font = st["note"]

    _header_row(ws, 4, ["Line Item", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"], st)

    for key, row in T8_LIVE.items():
        cell = ws.cell(row=row, column=1, value=LIVE_LABELS[key])
        cell.font = st["bold"] if key in BOLD_ROWS else st["regular"]
        cell.border = st["border"]

    cabin_occ_rows = [T8_INPUT_ROW[f"cabin_occ_y{i}"] for i in range(1, 6)]
    lodge_occ_rows = [T8_INPUT_ROW[f"lodge_occ_y{i}"] for i in range(1, 6)]
    exp_rows = [T8_INPUT_ROW[f"experiences_y{i}"] for i in range(1, 6)]

    for i, col in enumerate(COLS):
        prev = COLS[i - 1] if i > 0 else None

        # Revenue.
        ws[f"{col}{T8_LIVE['cabin_occ']}"] = f"={_tinp_row(cabin_occ_rows[i])}"
        ws[f"{col}{T8_LIVE['lodge_occ']}"] = (
            f"={_tinp_row(lodge_occ_rows[i])}*{_tinp('lodge_enabled')}"
        )
        ws[f"{col}{T8_LIVE['cabin_nights']}"] = (
            f"={col}{T8_LIVE['cabin_occ']}*365*{_tinp('cabins_count')}"
        )
        ws[f"{col}{T8_LIVE['lodge_nights']}"] = (
            f"={col}{T8_LIVE['lodge_occ']}*365"
        )
        ws[f"{col}{T8_LIVE['guests']}"] = (
            f"={col}{T8_LIVE['cabin_nights']}*{_tinp('cabin_guests')}"
            f"+{col}{T8_LIVE['lodge_nights']}*{_tinp('lodge_guests')}"
        )
        ws[f"{col}{T8_LIVE['cabin_rev']}"] = (
            f"={col}{T8_LIVE['cabin_nights']}*{_tinp('cabin_adr')}"
        )
        ws[f"{col}{T8_LIVE['lodge_rev']}"] = (
            f"={col}{T8_LIVE['lodge_nights']}*{_tinp('lodge_adr')}"
        )
        ws[f"{col}{T8_LIVE['exp_rev']}"] = f"={_tinp_row(exp_rows[i])}"
        ws[f"{col}{T8_LIVE['total_rev']}"] = (
            f"=SUM({col}{T8_LIVE['cabin_rev']}:{col}{T8_LIVE['exp_rev']})"
        )

        # Variable costs.
        ws[f"{col}{T8_LIVE['ota']}"] = (
            f"=({col}{T8_LIVE['cabin_rev']}+{col}{T8_LIVE['lodge_rev']})"
            f"*{_tinp('ota_share')}*{_tinp('ota_commission')}"
        )
        ws[f"{col}{T8_LIVE['housekeeping']}"] = (
            f"={col}{T8_LIVE['cabin_nights']}*{_tinp('housekeeping_cabin')}"
            f"+{col}{T8_LIVE['lodge_nights']}*{_tinp('housekeeping_lodge')}"
        )
        ws[f"{col}{T8_LIVE['breakfast']}"] = (
            f"={col}{T8_LIVE['guests']}*{_tinp('breakfast')}"
        )
        ws[f"{col}{T8_LIVE['energy']}"] = (
            f"={col}{T8_LIVE['cabin_nights']}*{_tinp('energy_cabin')}"
            f"+{col}{T8_LIVE['lodge_nights']}*{_tinp('energy_lodge')}"
        )
        ws[f"{col}{T8_LIVE['consumables']}"] = (
            f"={col}{T8_LIVE['cabin_nights']}*{_tinp('consumables_cabin')}"
            f"+{col}{T8_LIVE['lodge_nights']}*{_tinp('consumables_lodge')}"
        )
        ws[f"{col}{T8_LIVE['payment']}"] = (
            f"={col}{T8_LIVE['total_rev']}*{_tinp('payment_fee')}"
        )
        ws[f"{col}{T8_LIVE['exp_cogs']}"] = (
            f"={col}{T8_LIVE['exp_rev']}*(1-{_tinp('experience_margin')})"
        )
        ws[f"{col}{T8_LIVE['total_variable']}"] = (
            f"=SUM({col}{T8_LIVE['ota']}:{col}{T8_LIVE['exp_cogs']})"
        )
        ws[f"{col}{T8_LIVE['gross_margin']}"] = (
            f"={col}{T8_LIVE['total_rev']}-{col}{T8_LIVE['total_variable']}"
        )
        ws[f"{col}{T8_LIVE['payroll']}"] = f"={_tinp('annual_payroll')}"
        ws[f"{col}{T8_LIVE['fixed_opex']}"] = f"={_tinp('fixed_opex')}"
        ws[f"{col}{T8_LIVE['ebitda']}"] = (
            f"={col}{T8_LIVE['gross_margin']}-{col}{T8_LIVE['payroll']}-{col}{T8_LIVE['fixed_opex']}"
        )

        # Depreciation.
        ws[f"{col}{T8_LIVE['ffe']}"] = (
            f"={col}{T8_LIVE['total_rev']}*{_tinp('ffe_reserve')}"
        )
        ws[f"{col}{T8_LIVE['ppe_depr']}"] = f"={_tinp('annual_depreciation')}"
        ws[f"{col}{T8_LIVE['preop_amort']}"] = (
            f"=({_tinp('preopening')}+{_tinp('arrangement_fee')})/{_tinp('preopening_years')}"
        )
        ws[f"{col}{T8_LIVE['depreciation']}"] = (
            f"={col}{T8_LIVE['ppe_depr']}+{col}{T8_LIVE['preop_amort']}"
        )
        ws[f"{col}{T8_LIVE['ebit']}"] = f"={col}{T8_LIVE['ebitda']}-{col}{T8_LIVE['depreciation']}"

        # Debt.
        ws[f"{col}{T8_LIVE['begin_debt']}"] = f"={_t8_debt_ref('B', i)}"
        ws[f"{col}{T8_LIVE['senior_interest']}"] = f"={_t8_debt_ref('E', i)}"
        ws[f"{col}{T8_LIVE['principal']}"] = f"={_t8_debt_ref('D', i)}"
        ws[f"{col}{T8_LIVE['end_debt']}"] = f"={_t8_debt_ref('F', i)}"
        if i == 0:
            ws[f"{col}{T8_LIVE['bridge_interest']}"] = f"={_tinp('input_vat')}*{_tinp('vat_bridge_rate')}"
        elif i == 1:
            ws[f"{col}{T8_LIVE['bridge_interest']}"] = (
                f"={_tinp('input_vat')}*{_tinp('vat_bridge_rate')}*0.5"
            )
        else:
            ws[f"{col}{T8_LIVE['bridge_interest']}"] = "=0"
        ws[f"{col}{T8_LIVE['interest_expense']}"] = (
            f"={col}{T8_LIVE['senior_interest']}+{col}{T8_LIVE['bridge_interest']}"
        )
        ws[f"{col}{T8_LIVE['ebt']}"] = (
            f"={col}{T8_LIVE['ebit']}-{col}{T8_LIVE['interest_expense']}"
        )

        # Corporate tax with BIN carry-forward.
        ws[f"{col}{T8_LIVE['bin_opening']}"] = (
            "=0" if i == 0 else f"={prev}{T8_LIVE['bin_closing']}"
        )
        ws[f"{col}{T8_LIVE['taxable_base']}"] = (
            f"=MAX(0,{col}{T8_LIVE['ebt']}-{col}{T8_LIVE['bin_opening']})"
        )
        ws[f"{col}{T8_LIVE['tax']}"] = (
            f"={col}{T8_LIVE['taxable_base']}*{_tinp('corporate_tax')}"
        )
        ws[f"{col}{T8_LIVE['bin_closing']}"] = (
            f"={col}{T8_LIVE['bin_opening']}"
            f"+IF({col}{T8_LIVE['ebt']}<0,-{col}{T8_LIVE['ebt']},0)"
            f"-IF({col}{T8_LIVE['ebt']}>0,MIN({col}{T8_LIVE['bin_opening']},{col}{T8_LIVE['ebt']}),0)"
        )
        ws[f"{col}{T8_LIVE['net_income']}"] = f"={col}{T8_LIVE['ebt']}-{col}{T8_LIVE['tax']}"

        # Cash flow.
        ws[f"{col}{T8_LIVE['cfo']}"] = (
            f"={col}{T8_LIVE['net_income']}+{col}{T8_LIVE['depreciation']}"
        )
        if i == 0:
            ws[f"{col}{T8_LIVE['cfi']}"] = (
                f"=-({_tinp('cash_capex')}+{_tinp('idc')}+{_tinp('input_vat')}"
                f"+{_tinp('preopening')}+{_tinp('arrangement_fee')}"
                f"+{_tinp('initial_working_capital')}+{_tinp('dsra')}"
                f"+{col}{T8_LIVE['ffe']})"
            )
        elif i == 1:
            ws[f"{col}{T8_LIVE['cfi']}"] = f"={_tinp('input_vat')}-{col}{T8_LIVE['ffe']}"
        else:
            ws[f"{col}{T8_LIVE['cfi']}"] = f"=-{col}{T8_LIVE['ffe']}"

        if i == 0:
            ws[f"{col}{T8_LIVE['cff']}"] = (
                f"={_tinp('senior_debt')}+{_tinp('cash_equity')}+{_tinp('input_vat')}"
                f"-{col}{T8_LIVE['principal']}"
            )
        elif i == 1:
            ws[f"{col}{T8_LIVE['cff']}"] = (
                f"=-{_tinp('input_vat')}-{col}{T8_LIVE['principal']}"
            )
        else:
            ws[f"{col}{T8_LIVE['cff']}"] = f"=-{col}{T8_LIVE['principal']}"

        ws[f"{col}{T8_LIVE['net_cash_flow']}"] = (
            f"={col}{T8_LIVE['cfo']}+{col}{T8_LIVE['cfi']}+{col}{T8_LIVE['cff']}"
        )
        ws[f"{col}{T8_LIVE['end_cash']}"] = (
            f"={_tinp('initial_working_capital')}+{col}{T8_LIVE['net_cash_flow']}"
            if i == 0
            else f"={prev}{T8_LIVE['end_cash']}+{col}{T8_LIVE['net_cash_flow']}"
        )

        ws[f"{col}{T8_LIVE['cfads']}"] = (
            f"={col}{T8_LIVE['ebitda']}-{col}{T8_LIVE['ffe']}-{col}{T8_LIVE['tax']}"
        )
        ws[f"{col}{T8_LIVE['debt_service']}"] = (
            f"={col}{T8_LIVE['senior_interest']}+{col}{T8_LIVE['principal']}"
        )
        ws[f"{col}{T8_LIVE['dscr']}"] = (
            f"={col}{T8_LIVE['cfads']}/{col}{T8_LIVE['debt_service']}"
        )

        # Balance sheet.
        ws[f"{col}{T8_LIVE['gross_ppe']}"] = f"={_tinp('total_capex')}+{_tinp('idc')}"
        if i == 0:
            ws[f"{col}{T8_LIVE['accum_depr']}"] = f"={col}{T8_LIVE['ppe_depr']}"
            ws[f"{col}{T8_LIVE['accum_amort']}"] = f"={col}{T8_LIVE['preop_amort']}"
            ws[f"{col}{T8_LIVE['retained_earnings']}"] = f"={col}{T8_LIVE['net_income']}"
            ws[f"{col}{T8_LIVE['capital_subsidies']}"] = "=0"
            ws[f"{col}{T8_LIVE['restricted_cash']}"] = (
                f"={_tinp('dsra')}+{col}{T8_LIVE['ffe']}"
            )
        else:
            ws[f"{col}{T8_LIVE['accum_depr']}"] = (
                f"={prev}{T8_LIVE['accum_depr']}+{col}{T8_LIVE['ppe_depr']}"
            )
            ws[f"{col}{T8_LIVE['accum_amort']}"] = (
                f"={prev}{T8_LIVE['accum_amort']}+{col}{T8_LIVE['preop_amort']}"
            )
            ws[f"{col}{T8_LIVE['retained_earnings']}"] = (
                f"={prev}{T8_LIVE['retained_earnings']}+{col}{T8_LIVE['net_income']}"
            )
            ws[f"{col}{T8_LIVE['capital_subsidies']}"] = (
                f"={prev}{T8_LIVE['capital_subsidies']}"
            )
            ws[f"{col}{T8_LIVE['restricted_cash']}"] = (
                f"={prev}{T8_LIVE['restricted_cash']}+{col}{T8_LIVE['ffe']}"
            )

        ws[f"{col}{T8_LIVE['net_ppe']}"] = (
            f"={col}{T8_LIVE['gross_ppe']}-{col}{T8_LIVE['accum_depr']}"
        )
        ws[f"{col}{T8_LIVE['net_intangibles']}"] = (
            f"=({_tinp('preopening')}+{_tinp('arrangement_fee')})-{col}{T8_LIVE['accum_amort']}"
        )
        ws[f"{col}{T8_LIVE['vat_receivable']}"] = f"={_tinp('input_vat')}" if i == 0 else "=0"
        ws[f"{col}{T8_LIVE['total_assets']}"] = (
            f"={col}{T8_LIVE['net_ppe']}+{col}{T8_LIVE['net_intangibles']}"
            f"+{col}{T8_LIVE['end_cash']}+{col}{T8_LIVE['restricted_cash']}"
            f"+{col}{T8_LIVE['vat_receivable']}"
        )
        ws[f"{col}{T8_LIVE['vat_bridge']}"] = f"={_tinp('input_vat')}" if i == 0 else "=0"
        ws[f"{col}{T8_LIVE['total_liabilities']}"] = (
            f"={col}{T8_LIVE['end_debt']}+{col}{T8_LIVE['vat_bridge']}"
        )
        ws[f"{col}{T8_LIVE['share_capital']}"] = (
            f"={_tinp('land_in_kind')}+{_tinp('cash_equity')}"
        )
        ws[f"{col}{T8_LIVE['total_equity']}"] = (
            f"={col}{T8_LIVE['share_capital']}+{col}{T8_LIVE['retained_earnings']}"
            f"+{col}{T8_LIVE['capital_subsidies']}"
        )
        ws[f"{col}{T8_LIVE['bs_check']}"] = (
            f"={col}{T8_LIVE['total_assets']}-{col}{T8_LIVE['total_liabilities']}"
            f"-{col}{T8_LIVE['total_equity']}"
        )

        # Free cash flows used by the returns block.
        ws[f"{col}{T8_LIVE['fcff']}"] = (
            f"={col}{T8_LIVE['ebit']}*(1-{_tinp('corporate_tax')})"
            f"+{col}{T8_LIVE['depreciation']}-{col}{T8_LIVE['ffe']}"
        )
        ws[f"{col}{T8_LIVE['fcfe']}"] = (
            f"={col}{T8_LIVE['net_income']}+{col}{T8_LIVE['depreciation']}"
            f"-{col}{T8_LIVE['ffe']}-{col}{T8_LIVE['principal']}"
        )

    # Formats.
    for key, row in T8_LIVE.items():
        for col in COLS:
            cell = ws[f"{col}{row}"]
            cell.border = st["border"]
            if key in ("cabin_occ", "lodge_occ"):
                cell.number_format = "0.00%"
            elif key == "dscr":
                cell.number_format = "0.00"
            elif key in ("cabin_nights", "lodge_nights", "guests"):
                cell.number_format = "#,##0"
            else:
                cell.number_format = "#,##0.00"

    # ------------------------------------------------------------------
    # Checks: live vs Python
    # ------------------------------------------------------------------
    engine = turnaround.engine
    df = turnaround.projection
    kpis = turnaround.kpis

    ws.cell(row=CHECK_HEADER - 1, column=1, value="CHECKS: LIVE T8 MODEL VS. PYTHON ENGINE").font = st["bold"]
    _header_row(ws, CHECK_HEADER, ["Check", "Python", "Live", "Difference", "Status"], st)
    checks = [
        ("Revenue Year 1 (EUR)", float(df.iloc[0]["total_revenue"]), f"=B{T8_LIVE['total_rev']}", 1.0),
        ("Revenue Year 3 (EUR)", float(df.iloc[2]["total_revenue"]), f"=D{T8_LIVE['total_rev']}", 1.0),
        ("EBITDA Year 1 (EUR)", float(df.iloc[0]["ebitda"]), f"=B{T8_LIVE['ebitda']}", 1.0),
        ("EBITDA Year 3 (EUR)", float(df.iloc[2]["ebitda"]), f"=D{T8_LIVE['ebitda']}", 1.0),
        ("Net income Year 1 (EUR)", float(df.iloc[0]["net_income"]), f"=B{T8_LIVE['net_income']}", 1.0),
        ("Ending cash Year 1 (EUR)", float(df.iloc[0]["ending_cash"]), f"=B{T8_LIVE['end_cash']}", 1.0),
        ("Ending cash Year 2 (EUR)", float(df.iloc[1]["ending_cash"]), f"=C{T8_LIVE['end_cash']}", 1.0),
        ("DSCR Year 2 - binding year (x)", float(kpis.iloc[1]["dscr"]), f"=C{T8_LIVE['dscr']}", 0.01),
        ("Minimum DSCR Years 1-5 (x)", float(kpis["dscr"].min()), f"=MIN(B{T8_LIVE['dscr']}:F{T8_LIVE['dscr']})", 0.01),
        ("Maximum balance-sheet discrepancy (EUR)", 0.0, f"=MAX(ABS(B{T8_LIVE['bs_check']}),ABS(C{T8_LIVE['bs_check']}),ABS(D{T8_LIVE['bs_check']}),ABS(E{T8_LIVE['bs_check']}),ABS(F{T8_LIVE['bs_check']}))", 1.0),
    ]
    for i, (name, py_val, live_formula, tolerance) in enumerate(checks, start=CHECK_START):
        ws.cell(row=i, column=1, value=name).font = st["bold"]
        ws.cell(row=i, column=1).border = st["border"]
        c = ws.cell(row=i, column=2, value=py_val)
        c.number_format = "0.00" if "(x)" in name else "#,##0.00"
        c.border = st["border"]
        c = ws.cell(row=i, column=3, value=live_formula)
        c.number_format = "0.00" if "(x)" in name else "#,##0.00"
        c.border = st["border"]
        c = ws.cell(row=i, column=4, value=f"=C{i}-B{i}")
        c.number_format = "0.00" if "(x)" in name else "#,##0.00"
        c.border = st["border"]
        _status_formula(ws, i, 5, f"ABS(D{i})<={tolerance}", st)

    cov_row = CHECK_START + len(checks)
    ws.cell(row=cov_row, column=1, value="Covenant test: minimum DSCR >= target DSCR").font = st["bold"]
    ws.cell(row=cov_row, column=1).border = st["border"]
    c = ws.cell(row=cov_row, column=4, value=f"=MIN(B{T8_LIVE['dscr']}:F{T8_LIVE['dscr']})")
    c.number_format = "0.00"
    c.border = st["border"]
    _status_formula(ws, cov_row, 5, f"D{cov_row}>={_tinp('target_dscr')}", st)

    # ------------------------------------------------------------------
    # Returns block
    # ------------------------------------------------------------------
    all_in = turnaround.returns("all-in")
    cash = turnaround.returns("cash")

    ws.cell(row=RETURNS_HEADER, column=1, value="RETURNS - EXIT AT 8.5% CAP RATE, 3% SELLING COSTS").font = st["bold"]
    returns_rows = [
        ("Exit-year EBITDA (EUR)", f"=F{T8_LIVE['ebitda']}", "#,##0.00"),
        ("Gross terminal value (EUR)", f"=MAX(0,B{RETURNS_START}/{_tinp('exit_cap')})", "#,##0.00"),
        ("Net terminal value after 3% costs (EUR)", f"=B{RETURNS_START + 1}*(1-{_tinp('exit_cost')})", "#,##0.00"),
        ("Ending debt (EUR)", f"=F{T8_LIVE['end_debt']}", "#,##0.00"),
        ("Net equity proceeds (EUR)", f"=MAX(0,B{RETURNS_START + 2}-B{RETURNS_START + 3})", "#,##0.00"),
    ]
    for i, (label, formula, fmt) in enumerate(returns_rows):
        r = RETURNS_START + i
        ws.cell(row=r, column=1, value=label).font = st["regular"]
        ws.cell(row=r, column=1).border = st["border"]
        c = ws.cell(row=r, column=2, value=formula)
        c.number_format = fmt
        c.border = st["border"]

    _header_row(ws, CF_HEADER, ["Year", "0", "1", "2", "3", "4", "5"], st)
    for j in range(6):
        c = ws.cell(row=CF_HEADER + 1, column=2 + j, value=j)
        c.border = st["border"]
        c.font = st["regular"]
        c.alignment = Alignment(horizontal="center")

    total_investment_allin = turnaround.all_in_project_investment
    total_investment_cash = turnaround.cash_project_investment
    equity_allin = turnaround.all_in_equity
    equity_cash = turnaround.cash_equity

    blocks = [
        (
            "Project cash flow - all-in",
            -total_investment_allin,
            tuple(f"={col}{T8_LIVE['fcff']}" for col in COLS),
        ),
        (
            "Project cash flow - cash basis",
            -total_investment_cash,
            tuple(f"={col}{T8_LIVE['fcff']}" for col in COLS),
        ),
        (
            "Equity cash flow - all-in",
            -equity_allin,
            tuple(f"={col}{T8_LIVE['fcfe']}" for col in COLS),
        ),
        (
            "Equity cash flow - cash basis",
            -equity_cash,
            tuple(f"={col}{T8_LIVE['fcfe']}" for col in COLS),
        ),
    ]
    for k, (label, t0, flows) in enumerate(blocks):
        r = CF_START + k
        ws.cell(row=r, column=1, value=label).font = st["bold"] if k < 2 else st["regular"]
        ws.cell(row=r, column=1).border = st["border"]
        c = ws.cell(row=r, column=2, value=t0)
        c.number_format = "#,##0.00"
        c.border = st["border"]
        for j, formula in enumerate(flows, start=0):
            c = ws.cell(row=r, column=3 + j, value=formula)
            c.number_format = "#,##0.00"
            c.border = st["border"]
        # Terminal value is added to the final operating year.
        c = ws[f"G{r}"]
        c.value = f"={c.value}+$B${RETURNS_START + 2}" if k < 2 else f"={c.value}+$B${RETURNS_START + 4}"
        c.number_format = "#,##0.00"
        c.border = st["border"]

    irr_header = CF_START + 5
    ws.cell(row=irr_header, column=1, value="IRR / NPV").font = st["bold"]
    labels = [
        ("Project IRR - all-in", f"=IRR(B{CF_START}:G{CF_START})", "0.00%"),
        ("Project IRR - cash", f"=IRR(B{CF_START + 1}:G{CF_START + 1})", "0.00%"),
        ("Equity IRR - all-in", f"=IRR(B{CF_START + 2}:G{CF_START + 2})", "0.00%"),
        ("Equity IRR - cash", f"=IRR(B{CF_START + 3}:G{CF_START + 3})", "0.00%"),
        ("Project NPV - all-in", f"=B{CF_START}+NPV({_tinp('discount_rate')},C{CF_START}:G{CF_START})", "#,##0.00"),
        ("Project NPV - cash", f"=B{CF_START + 1}+NPV({_tinp('discount_rate')},C{CF_START + 1}:G{CF_START + 1})", "#,##0.00"),
        ("Equity NPV - all-in", f"=B{CF_START + 2}+NPV({_tinp('discount_rate')},C{CF_START + 2}:G{CF_START + 2})", "#,##0.00"),
        ("Equity NPV - cash", f"=B{CF_START + 3}+NPV({_tinp('discount_rate')},C{CF_START + 3}:G{CF_START + 3})", "#,##0.00"),
    ]
    for i, (label, formula, fmt) in enumerate(labels, start=irr_header + 1):
        ws.cell(row=i, column=1, value=label).font = st["regular"]
        ws.cell(row=i, column=1).border = st["border"]
        c = ws.cell(row=i, column=2, value=formula)
        c.number_format = fmt
        c.border = st["border"]
        c.font = st["bold"]

    # Python reference column, so the reader can see the reconciliation.
    py_header = irr_header + 9
    _header_row(ws, py_header, ["Python reference", "Value"], st)
    py_rows = [
        ("Project IRR - all-in (Python)", all_in["project_irr_exit"]),
        ("Project IRR - cash (Python)", cash["project_irr_exit"]),
        ("Equity IRR - all-in (Python)", all_in["equity_irr_exit"]),
        ("Equity IRR - cash (Python)", cash["equity_irr_exit"]),
        ("Project NPV - all-in (Python)", all_in["project_npv"]),
        ("Project NPV - cash (Python)", cash["project_npv"]),
    ]
    for i, (label, value) in enumerate(py_rows, start=py_header + 1):
        ws.cell(row=i, column=1, value=label).font = st["regular"]
        ws.cell(row=i, column=1).border = st["border"]
        c = ws.cell(row=i, column=2, value=round(float(value), 6))
        c.number_format = "0.00%" if "IRR" in label else "#,##0.00"
        c.border = st["border"]

    note_row = py_header + len(py_rows) + 2
    ws.cell(row=note_row, column=1, value=(
        "Note: the all-in basis adds the EUR 250,000 land contributed in kind; "
        "the cash basis excludes it. The EUR 130,536 VAT bridge is a balance-"
        "sheet item, not part of the investment base or of operating cash flow."
    )).font = st["note"]
    ws.cell(row=note_row, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=6)
    ws.row_dimensions[note_row].height = 32

    ws.column_dimensions["A"].width = 54
    for col in COLS + ["G"]:
        ws.column_dimensions[col].width = 18


def _tinp_row(row: int) -> str:
    """Absolute reference to a specific T8 Inputs row."""
    return f"'T8 Inputs'!$B${row}"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def add_t8_model_tabs(wb, turnaround) -> None:
    """Adds T8 Inputs, T8 Debt Schedule and T8 Live Model."""
    st = _styles()
    build_t8_inputs(wb, turnaround, st)
    build_t8_debt_schedule(wb, st)
    build_t8_live_model(wb, turnaround, st)
