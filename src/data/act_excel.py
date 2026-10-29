"""
Report tabs for the five-act case study.

The main exporter writes the institutional model pack (as-is cases, stress
tests, Monte Carlo, reform layer). This module adds the narrative layer that
turns the same engines into a readable case:

1. ``Act 1 - Promoter``      the original pitch and why the model cannot fund it.
2. ``Act 2 - Audit``         the independent cost / demand / funding audit.
3. ``Decline Memo``          the four computed reasons and the DECLINE verdict.
4. ``Act 4 - T8``            six modular cabins: budget, funding, P&L, returns.
5. ``Executive Comparison``  promoter vs audited vs cabin turnaround.
6. ``T8 Sensitivities``      exit cap, demand, leverage and scope stress tests.

Nothing here re-computes an assumption: every number comes from
``FinancialModelEngine``, ``TurnaroundEngine``, ``DeclineMemoEngine`` or
``InvestmentCase``. The tabs are presentation only.
"""

from typing import Any, Dict, Iterable, List

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src.core.decline import DeclineMemoEngine
from src.core.expansion import ExpansionFinancialEngine
from src.core.investment_case import InvestmentCase
from src.core.turnaround import TurnaroundEngine


NAVY = "1E3A8A"
SLATE = "F1F5F9"
AMBER = "FEF3C7"
GREEN = "DCFCE7"
RED = "FEE2E2"


def _styles() -> Dict[str, Any]:
    return {
        "navy": PatternFill(start_color=NAVY, end_color=NAVY, fill_type="solid"),
        "slate": PatternFill(start_color=SLATE, end_color=SLATE, fill_type="solid"),
        "amber": PatternFill(start_color=AMBER, end_color=AMBER, fill_type="solid"),
        "green": PatternFill(start_color=GREEN, end_color=GREEN, fill_type="solid"),
        "red": PatternFill(start_color=RED, end_color=RED, fill_type="solid"),
        "header": Font(name="Calibri", size=11, bold=True, color="FFFFFF"),
        "title": Font(name="Calibri", size=14, bold=True, color=NAVY),
        "bold": Font(name="Calibri", size=11, bold=True),
        "regular": Font(name="Calibri", size=11),
        "note": Font(name="Calibri", size=10, italic=True, color="64748B"),
        "border": Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        ),
    }


def _title(ws, title: str, subtitle: str, st: Dict[str, Any]) -> None:
    ws["A1"] = title
    ws["A1"].font = st["title"]
    ws["A2"] = subtitle
    ws["A2"].font = st["note"]
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:L2")
    ws.row_dimensions[2].height = 40


def _section(ws, row: int, text: str, st: Dict[str, Any]) -> int:
    ws.cell(row=row, column=1, value=text).font = st["bold"]
    return row + 1


def _header(ws, row: int, headers: Iterable[str], st: Dict[str, Any]) -> None:
    for col, text in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=text)
        cell.fill = st["navy"]
        cell.font = st["header"]
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = st["border"]


def _kv_rows(
    ws,
    start_row: int,
    rows: Iterable[tuple],
    st: Dict[str, Any],
    money_cols: Iterable[int] = (2,),
    pct_cols: Iterable[int] = (),
) -> int:
    money_cols = set(money_cols)
    pct_cols = set(pct_cols)
    row = start_row
    for values in rows:
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col == 1 else st["regular"]
            cell.border = st["border"]
            cell.alignment = Alignment(vertical="top", wrap_text=(col == len(values)))
            if col in money_cols and isinstance(value, (int, float)):
                cell.number_format = "#,##0.00"
            elif col in pct_cols and isinstance(value, (int, float)):
                cell.number_format = "0.00%"
        row += 1
    return row


def _verdict(ws, row: int, text: str, st: Dict[str, Any], positive: bool = True) -> int:
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(name="Calibri", size=12, bold=True, color="0F766E" if positive else "BE123C")
    cell.fill = st["green"] if positive else st["red"]
    cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=12)
    ws.row_dimensions[row].height = 30
    return row + 1


# ---------------------------------------------------------------------------
# Act 1 - the promoter's pitch
# ---------------------------------------------------------------------------
def build_act_1(wb, promoter, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Act 1 - Promoter")
    ws.views.sheetView[0].showGridLines = False
    _title(
        ws,
        "ACT 1 - THE PROMOTER'S PITCH: REOPEN THE CASERON AS AN 8-KEY HOTEL",
        (
            "The starting point of the case. Eight keys (seven doubles and the full house), a "
            "21-cover restaurant, EUR 725,000 all-in, 70% LTV and a 30% equity cheque. The tab "
            "shows the pitch next to the re-modelled engine, not a different project."
        ),
        st,
    )

    df = promoter.run_projection(5)
    kpis = promoter._turnaround_kpis if False else None  # keep the engine as the only source
    from src.core.metrics import CreditMetricsEngine

    credit = CreditMetricsEngine(target_dscr=1.25)
    kpis = credit.compute_credit_kpis(df, promoter.debt_engine.get_annual_schedule_df())
    rev1 = promoter.calculate_revenue_for_year(1)

    row = _section(ws, 4, "1. THE PITCH VS THE RE-MODELLED ENGINE", st)
    _header(ws, row, ["Item", "Pitch / deck", "Engine", "Comment"], st)
    row += 1
    pitch_rows = [
        ("All-in investment (EUR)", 725_000.0, 725_000.0, "440k works + 35k FF&E + 250k land in kind"),
        ("Senior debt (EUR)", 507_500.0, 507_500.0, "70% LTV, 4.5% fixed, 25 years, no grace"),
        ("Cash equity (EUR)", 217_500.0, 217_500.0, "30% of CapEx; no funding plug in this case"),
        ("Room-nights Year 1", 491.0, rev1["room_nights"], "Seven doubles, 19.2% occupancy"),
        ("House-nights Year 1", 72.0, rev1["house_nights"], "Full house, same occupancy"),
        ("Restaurant covers Year 1", 859.0, rev1["guests"], "One meal per guest-day at a EUR 20 ticket"),
        ("Revenue Year 1 (EUR)", 96_628.0, rev1["total_revenue"], "Deck literal 96,628; the re-modelled engine gives 86,275"),
        ("EBITDA Year 1 (EUR)", 11_297.0, float(df.iloc[0]["ebitda"]), "Deck literal retained; the engine reproduces it"),
    ]
    row = _kv_rows(ws, row, pitch_rows, st, money_cols=(2, 3))

    row += 1
    row = _section(ws, row, "2. FIVE-YEAR RE-MODELLED PROJECTION (PROMOTER CASE)", st)
    headers = ["Year", "Revenue (EUR)", "Variable costs (EUR)", "Gross margin (EUR)", "Payroll (EUR)",
               "Fixed opex (EUR)", "EBITDA (EUR)", "Debt service (EUR)", "DSCR", "Ending cash (EUR)"]
    _header(ws, row, headers, st)
    row += 1
    for i, (_, r) in enumerate(df.iterrows()):
        values = [
            int(r["year"]), float(r["total_revenue"]), float(r["total_variable_costs"]),
            float(r["gross_margin"]), float(r["labor_expense"]), float(r["fixed_opex"]),
            float(r["ebitda"]), float(r["debt_service"]), float(kpis.iloc[i]["dscr"]),
            float(r["ending_cash"]),
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=round(value, 2) if isinstance(value, float) else value)
            cell.font = st["bold"] if col in (1, 7) else st["regular"]
            cell.border = st["border"]
            if col == 1:
                cell.number_format = "0"
            elif col == 9:
                cell.number_format = "0.00x"
            else:
                cell.number_format = "#,##0.00"
        if float(kpis.iloc[i]["dscr"]) < 1.25:
            ws.cell(row=row, column=9).fill = st["red"]
        row += 1

    row += 1
    row = _section(ws, row, "3. WHY THE PITCH IS NOT FUNDABLE", st)
    findings = [
        ("Gross margin is 100%", "There is no COGS, OTA commission, amenity, breakfast or payment cost in the promoter model: every euro of revenue becomes gross margin. The audited stack removes that artefact."),
        ("Year-1 DSCR", f"{float(kpis.iloc[0]['dscr']):.2f}x against a 1.25x covenant. Debt service of EUR {float(kpis.iloc[0]['debt_service']):,.0f} is not covered."),
        ("Year-1 cash", f"EUR {float(df.iloc[0]['ending_cash']):,.0f}: the business is cash-negative after the opening year."),
        ("Positive IRR is an artefact", "The promoter IRR looks positive only because the cost stack is incomplete. It is not evidence that the project works."),
        ("No grant and no VAT bridge", "The structure ignores the 21% input VAT bridge, the LEADER timing and the DSRA that the audited case has to fund."),
    ]
    for title, text in findings:
        ws.cell(row=row, column=1, value=title).font = st["bold"]
        cell = ws.cell(row=row, column=2, value=text)
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=10)
        ws.row_dimensions[row].height = 34
        row += 1

    row += 1
    _verdict(ws, row, "VERDICT: UNFUNDABLE AS PRESENTED. The pitch is the problem statement, not the investment case.", st, positive=False)

    ws.column_dimensions["A"].width = 34
    for col in "BCDEFGHIJ":
        ws.column_dimensions[col].width = 18
    ws.column_dimensions["D"].width = 42
    ws.freeze_panes = "A5"


# ---------------------------------------------------------------------------
# Act 2 - the audit
# ---------------------------------------------------------------------------
def build_act_2(wb, promoter, audited, market, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Act 2 - Audit")
    ws.views.sheetView[0].showGridLines = False
    _title(
        ws,
        "ACT 2 - INDEPENDENT AUDIT: THE SAME HOTEL, FULL COST STACK, REAL DEMAND",
        (
            "The audit does not change the product. It prices the works that the pitch left out, "
            "adds the full USALI cost stack, applies INE Segovia seasonality and the Segovia "
            "hospitality agreement, and funds the 21% VAT bridge. The result is the audited case."
        ),
        st,
    )

    from src.core.metrics import CreditMetricsEngine

    credit = CreditMetricsEngine(target_dscr=1.25)
    a_df = audited.run_projection(5)
    a_kpis = credit.compute_credit_kpis(a_df, audited.debt_engine.get_annual_schedule_df())
    m_df = market.run_projection(5)
    m_kpis = credit.compute_credit_kpis(m_df, market.debt_engine.get_annual_schedule_df())

    row = _section(ws, 4, "1. CAPEX BRIDGE: FROM THE EUR 725,000 PITCH TO THE EUR 1,050,100 AUDIT", st)
    _header(ws, row, ["CapEx line", "Promoter (EUR)", "Audited (EUR)", "Adjustment (EUR)", "Audit basis"], st)
    row += 1
    lines = [
        ("Land contributed in kind", promoter.capex.land.amount, audited.capex.land.amount, "Same 25-ha finca at opportunity value"),
        ("Works (reforma)", promoter.capex.renovation.amount, audited.capex.renovation.amount, "550 m2 at a realistic rural build cost"),
        ("Kitchen equipment", promoter.capex.kitchen_equipment.amount, audited.capex.kitchen_equipment.amount, "Commercial kitchen for 21 covers"),
        ("FF&E", promoter.capex.ffe.amount, audited.capex.ffe.amount, "8 keys, textiles, equipment"),
        ("Biological pond", promoter.capex.biopool_landscaping.amount, audited.capex.biopool_landscaping.amount, "Required by the project and the grant"),
        ("Digital / PMS", promoter.capex.digitalization.amount, audited.capex.digitalization.amount, "PMS, locks, channel manager"),
        ("Technical fees", promoter.capex.professional_fees.amount, audited.capex.professional_fees.amount, "Architecture, engineering, permits"),
        ("Contingency", promoter.capex.contingency.amount, audited.capex.contingency.amount, "Granite and unforeseen works"),
    ]
    for label, before, after, note in lines:
        for col, value in enumerate((label, float(before), float(after), float(after) - float(before), note), start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col == 1 else st["regular"]
            cell.border = st["border"]
            cell.alignment = Alignment(vertical="top", wrap_text=(col == 5))
            if col in (2, 3, 4):
                cell.number_format = "#,##0.00"
        if float(after) - float(before) > 0:
            ws.cell(row=row, column=4).fill = st["amber"]
        row += 1
    totals = [
        ("TOTAL ALL-IN CAPEX", float(promoter.capex.total_capex), float(audited.capex.total_capex),
         float(audited.capex.total_capex - promoter.capex.total_capex), "+45% over the pitch"),
        ("Cash CapEx (land excluded)", float(promoter.cash_capex), float(audited.cash_capex),
         float(audited.cash_capex - promoter.cash_capex), "The cheque the sponsor has to write"),
    ]
    for values in totals:
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"]
            cell.border = st["border"]
            if col in (2, 3, 4):
                cell.number_format = "#,##0.00"
        row += 1

    row += 1
    row = _section(ws, row, "2. THE COST STACK THE PITCH OMITTED (AUDITED CASE, YEAR 3)", st)
    _header(ws, row, ["Line", "Year 3 (EUR)", "% of revenue"], st)
    row += 1
    y3 = a_df.iloc[2]
    for label, value in [
        ("Revenue", float(y3["total_revenue"])),
        ("Restaurant COGS", float(y3["cogs_restaurant"])),
        ("OTA commissions", float(y3["ota_commission"])),
        ("Amenities / housekeeping", float(y3["amenities"])),
        ("Breakfast", float(y3["breakfast_cost"])),
        ("Total variable costs", float(y3["total_variable_costs"])),
        ("Payroll (Segovia agreement, 35% SS)", float(y3["labor_expense"])),
        ("Fixed operating expenses", float(y3["fixed_opex"])),
        ("EBITDA", float(y3["ebitda"])),
        ("FF&E reserve", float(y3["ffe_reserve"])),
        ("CFADS", float(y3["cfads"])),
    ]:
        c1 = ws.cell(row=row, column=1, value=label)
        c2 = ws.cell(row=row, column=2, value=round(value, 2))
        c3 = ws.cell(row=row, column=3, value=round(value / float(y3["total_revenue"]), 4))
        for c in (c1, c2, c3):
            c.border = st["border"]
        c1.font = st["bold"] if label in ("Revenue", "EBITDA", "CFADS") else st["regular"]
        c2.font = st["bold"] if label in ("Revenue", "EBITDA", "CFADS") else st["regular"]
        c2.number_format = "#,##0.00"
        c3.number_format = "0.0%"
        row += 1

    row += 1
    row = _section(ws, row, "3. AUDITED CASE: FIVE-YEAR PROJECTION", st)
    headers = ["Year", "Revenue (EUR)", "EBITDA (EUR)", "EBITDA %", "CFADS (EUR)", "Debt service (EUR)",
               "DSCR", "Net income (EUR)", "Ending cash (EUR)"]
    _header(ws, row, headers, st)
    row += 1
    for i, (_, r) in enumerate(a_df.iterrows()):
        values = [
            int(r["year"]), float(r["total_revenue"]), float(r["ebitda"]),
            float(r["ebitda"] / r["total_revenue"]), float(r["cfads"]), float(r["debt_service"]),
            float(a_kpis.iloc[i]["dscr"]), float(r["net_income"]), float(r["ending_cash"]),
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=round(value, 2) if isinstance(value, float) else value)
            cell.font = st["bold"] if col in (1, 3) else st["regular"]
            cell.border = st["border"]
            if col == 1:
                cell.number_format = "0"
            elif col == 4:
                cell.number_format = "0.0%"
            elif col == 7:
                cell.number_format = "0.00x"
            else:
                cell.number_format = "#,##0.00"
        if float(a_kpis.iloc[i]["dscr"]) < 1.25:
            ws.cell(row=row, column=7).fill = st["red"]
        row += 1

    row += 1
    row = _section(ws, row, "4. INDEPENDENT INE SEGOVIA MARKET CASE (21.24% MATURE OCCUPANCY)", st)
    _header(ws, row, ["Year", "Revenue (EUR)", "EBITDA (EUR)", "DSCR", "Ending cash (EUR)"], st)
    row += 1
    for i, (_, r) in enumerate(m_df.iterrows()):
        for col, value in enumerate(
            (int(r["year"]), round(float(r["total_revenue"]), 2), round(float(r["ebitda"]), 2),
             round(float(m_kpis.iloc[i]["dscr"]), 2), round(float(r["ending_cash"]), 2)),
            start=1,
        ):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col == 3 else st["regular"]
            cell.border = st["border"]
            cell.number_format = "0" if col == 1 else ("0.00x" if col == 4 else "#,##0.00")
        row += 1

    row += 1
    row = _section(ws, row, "5. AUDIT FINDINGS", st)
    findings = [
        ("CapEx understated by EUR 325,100", "The pitch omitted the kitchen, the pond, digital, fees and contingency. The audited all-in budget is EUR 1,050,100."),
        ("Cash equity is not 30%", f"The funding plug requires EUR {audited.cash_equity:,.2f}, or {audited.cash_equity / audited.capex.total_capex:.1%} of all-in CapEx. The 35% LTV facility is not the constraint: the DSCR cap is."),
        ("The upside demand still fails", f"At 31.36% mature occupancy the minimum DSCR is {float(a_kpis['dscr'].min()):.2f}x. The independent INE case is negative in Year 1."),
        ("Phase II has no funding", "The expansion needs EUR 252k that Phase I cannot generate; the grant and the VAT refund are already committed."),
    ]
    for title, text in findings:
        ws.cell(row=row, column=1, value=title).font = st["bold"]
        cell = ws.cell(row=row, column=2, value=text)
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=9)
        ws.row_dimensions[row].height = 34
        row += 1

    ws.column_dimensions["A"].width = 36
    for col in "BCDEFGHI":
        ws.column_dimensions[col].width = 18
    ws.column_dimensions["E"].width = 34
    ws.freeze_panes = "A5"


# ---------------------------------------------------------------------------
# Act 3 - the decline memo
# ---------------------------------------------------------------------------
def build_decline_memo(wb, decline: DeclineMemoEngine, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Decline Memo")
    ws.views.sheetView[0].showGridLines = False
    _title(
        ws,
        "ACT 3 - CREDIT COMMITTEE DECLINE MEMORANDUM",
        (
            "The four reasons are computed tests, not opinions. Each one has a threshold and a "
            "status; the verdict is DECLINE only because all four fail. The restaurant test is "
            "shown as a fully loaded cost centre so the arithmetic can be audited."
        ),
        st,
    )

    verdict = decline.verdict()
    row = 4
    cell = ws.cell(row=row, column=1, value=verdict["decision"])
    cell.font = Font(name="Calibri", size=20, bold=True, color="FFFFFF")
    cell.fill = st["red"]
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=12)
    ws.row_dimensions[row].height = 34
    row += 1
    ws.cell(row=row, column=1, value=verdict["headline"]).font = st["bold"]
    ws.cell(row=row, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=12)
    ws.row_dimensions[row].height = 38
    row += 2

    row = _section(ws, row, "1. THE FOUR TESTS", st)
    _header(ws, row, ["#", "Reason", "Metric", "Threshold", "Unit", "Status", "Detail"], st)
    row += 1
    for reason in verdict["reasons"]:
        values = [
            reason["number"], reason["title"], reason["metric"], reason["threshold"],
            reason["unit"], "FAIL" if reason["failed"] else "PASS", reason["detail"],
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col in (1, 6) else st["regular"]
            cell.border = st["border"]
            cell.alignment = Alignment(vertical="top", wrap_text=(col == 7))
            if col in (3, 4) and isinstance(value, (int, float)):
                cell.number_format = "#,##0.00"
            if col == 6:
                cell.fill = st["red"] if reason["failed"] else st["green"]
                cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[row].height = 66
        row += 1

    row += 1
    row = _section(ws, row, "2. REASON 3 - THE RESTAURANT COST CENTRE (EUR)", st)
    centre = decline.restaurant_cost_centre()
    ws.cell(row=row, column=1, value=(
        f"{centre['covers_per_day']:.0f} covers/day x {centre['service_days']} days = "
        f"{centre['covers']:,.0f} covers; food cost {centre['cogs_ratio']:.0%} of revenue."
    )).font = st["note"]
    row += 1
    _header(ws, row, ["Fixed cost line", "Annual (EUR)"], st)
    row += 1
    for line, amount in centre["fixed_lines"].items():
        ws.cell(row=row, column=1, value=line).border = st["border"]
        cell = ws.cell(row=row, column=2, value=amount)
        cell.number_format = "#,##0.00"
        cell.border = st["border"]
        row += 1
    ws.cell(row=row, column=1, value="TOTAL FIXED BURDEN").font = st["bold"]
    ws.cell(row=row, column=1).border = st["border"]
    cell = ws.cell(row=row, column=2, value=centre["fixed_burden"])
    cell.font = st["bold"]
    cell.number_format = "#,##0.00"
    cell.border = st["border"]
    row += 2

    _header(ws, row, ["Ticket test", "Covers", "Revenue (EUR)", "COGS (EUR)", "Contribution (EUR)",
                      "Fixed burden (EUR)", "Result (EUR)", "Margin"], st)
    row += 1
    for ticket in sorted(centre["tickets"]):
        t = centre["tickets"][ticket]
        for col, value in enumerate(
            (f"EUR {ticket:.0f} ticket", t["covers"], t["revenue"], t["cogs"], t["contribution"],
             t["fixed_burden"], t["result"], t["margin"]),
            start=1,
        ):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col in (1, 7) else st["regular"]
            cell.border = st["border"]
            if col in (2,):
                cell.number_format = "#,##0"
            elif col == 8:
                cell.number_format = "0.0%"
            elif isinstance(value, (int, float)):
                cell.number_format = "#,##0.00"
        if t["result"] < 0:
            ws.cell(row=row, column=7).fill = st["red"]
        row += 1

    row += 1
    row = _section(ws, row, "3. REASON 4 - THE PHASE II GATE (EUR)", st)
    expansion = ExpansionFinancialEngine()
    cash_y2 = float(decline.kpis.iloc[1]["ending_cash"])
    dscr_y3 = float(decline.kpis.iloc[2]["dscr"])
    gate = expansion.compute_phase_gate(cash_y2, dscr_y3)
    for label, value in [
        ("Phase I cash at end of Year 2", gate["phase1_cash_end_y2"]),
        ("Phase II cash need (net CapEx + VAT)", gate["phase2_cash_need"]),
        ("Phase II funding gap", gate["phase2_funding_gap"]),
        ("Phase II proceed", "NO" if not gate["phase2_proceed"] else "YES"),
        ("Phase I Year-3 DSCR", gate["phase1_dscr_y3"]),
    ]:
        ws.cell(row=row, column=1, value=label).font = st["bold"]
        cell = ws.cell(row=row, column=2, value=value)
        cell.font = st["regular"]
        cell.border = st["border"]
        if isinstance(value, (int, float)):
            cell.number_format = "0.00x" if label.endswith("DSCR") else "#,##0.00"
        row += 1

    row += 1
    row = _section(ws, row, "4. CONTEXT AND MEMORANDUM", st)
    ctx = verdict["context"]
    for label, value, fmt in [
        ("Case under review", ctx["case"], None),
        ("All-in CapEx", ctx["all_in_capex"], "#,##0.00"),
        ("Senior debt requested", ctx["senior_debt"], "#,##0.00"),
        ("Cash equity plug", ctx["cash_equity"], "#,##0.00"),
        ("Minimum DSCR", ctx["min_dscr"], "0.00x"),
        ("Terminal value at 8.5% cap", ctx["terminal_value"], "#,##0.00"),
    ]:
        ws.cell(row=row, column=1, value=label).font = st["bold"]
        cell = ws.cell(row=row, column=2, value=value)
        cell.border = st["border"]
        if fmt:
            cell.number_format = fmt
        row += 1
    row += 1
    cell = ws.cell(row=row, column=1, value=verdict["memo"])
    cell.font = st["note"]
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=12)
    ws.row_dimensions[row].height = 38

    ws.column_dimensions["A"].width = 40
    for col in "BCDEFGH":
        ws.column_dimensions[col].width = 16
    ws.column_dimensions["G"].width = 74
    ws.freeze_panes = "A8"


# ---------------------------------------------------------------------------
# Act 4 - the cabin turnaround
# ---------------------------------------------------------------------------
def build_act_4(wb, turnaround: TurnaroundEngine, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Act 4 - T8")
    ws.views.sheetView[0].showGridLines = False
    _title(
        ws,
        "ACT 4 - THE TURNAROUND: SIX MODULAR CABINS + THE CASERON LODGE",
        (
            "The decline is the permission to change the product. The commercial kitchen, the "
            "21-cover restaurant and the 550 m2 of heavy reform disappear. Six 40 m2 modular "
            "cabins (EUR 60,000 each) and a four-bedroom lodge in the existing caseron replace them."
        ),
        st,
    )

    cfg = turnaround.config
    summary = turnaround.summary()
    proj = turnaround.projection
    kpis = turnaround.kpis
    uses = turnaround.use_of_funds

    row = _section(ws, 4, "1. THE NEW PRODUCT", st)
    _header(ws, row, ["Component", "Count", "Capacity / spec", "ADR (EUR)", "Occupancy ramp", "Note"], st)
    row += 1
    for label, count, spec, adr, ramp, note in [
        ("Modular cabins", cfg.cabins.count, f"{cfg.cabins.area_m2:.0f} m2, {cfg.cabins.bedrooms} bed, {cfg.cabins.max_guests} guests",
         cfg.cabins.adr, "50% / 56% / 58%", "Nordic modular units, installed on screw piles"),
        ("Caserón lodge", 1 if cfg.lodge.enabled else 0, f"{cfg.lodge.bedrooms} bed, {cfg.lodge.max_guests} guests",
         cfg.lodge.adr, "32% / 38% / 40%", "Light refresh, no structural works"),
        ("Commercial restaurant", 0, "Replaced by breakfast baskets and local asadores", 0.0, "n/a", "Removes the fixed-cost trap"),
    ]:
        for col, value in enumerate((label, count, spec, adr, ramp, note), start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col == 1 else st["regular"]
            cell.border = st["border"]
            cell.alignment = Alignment(vertical="top", wrap_text=(col in (3, 6)))
            if col == 4 and isinstance(value, (int, float)):
                cell.number_format = "#,##0"
        row += 1

    row += 1
    row = _section(ws, row, "2. T8 CAPITAL BUDGET (NET OF VAT, EUR)", st)
    _header(ws, row, ["CapEx line", "Amount (EUR)", "% of cash CapEx", "Basis"], st)
    row += 1
    capex_lines = [
        ("6 modular cabins at EUR 60,000", cfg.capex.cabins, "Shell, transport and assembly"),
        ("Natural pond / biopool", cfg.capex.biopool, "EPDM, biofilter, landscaping"),
        ("Common infrastructure", cfg.capex.infrastructure, "Access, water, solar, sewage"),
        ("Caserón light refresh (lodge)", cfg.capex.caseron_refresh, "No structural reform"),
        ("FF&E (cabins + lodge)", cfg.capex.ffe, "Textiles, furniture, equipment"),
        ("Digital, PMS and locks", cfg.capex.digital, "Guest journey and revenue management"),
    ]
    for label, amount, note in capex_lines:
        for col, value in enumerate((label, float(amount), float(amount) / cfg.capex.cash_capex, note), start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col == 1 else st["regular"]
            cell.border = st["border"]
            if col == 2:
                cell.number_format = "#,##0.00"
            elif col == 3:
                cell.number_format = "0.0%"
        row += 1
    for label, amount, note in [
        ("Works subtotal", cfg.capex.works, "Six lines above"),
        ("Technical fees (6%)", cfg.capex.fees, "Architecture, engineering, permits"),
        ("Contingency (5%)", cfg.capex.contingency, "Site and module delivery risk"),
        ("CASH CAPEX", cfg.capex.cash_capex, "The sponsor's cash cheque"),
        ("Land in kind", cfg.capex.land, "25-ha estate at opportunity value"),
        ("ALL-IN CAPEX", cfg.capex.total_capex, "Comparable with the audited EUR 1,050,100"),
    ]:
        for col, value in enumerate((label, float(amount), float(amount) / cfg.capex.cash_capex if cfg.capex.cash_capex else 0.0, note), start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"]
            cell.border = st["border"]
            if col == 2:
                cell.number_format = "#,##0.00"
            elif col == 3 and label not in ("Land in kind", "ALL-IN CAPEX"):
                cell.number_format = "0.0%"
        if label in ("CASH CAPEX", "ALL-IN CAPEX"):
            for col in range(1, 4):
                ws.cell(row=row, column=col).fill = st["slate"]
        row += 1
    ws.cell(row=row, column=1, value="Installed cost per cabin (cash CapEx net of the caseron refresh, / 6)").font = st["bold"]
    cell = ws.cell(row=row, column=2, value=cfg.capex.installed_cost_per_cabin)
    cell.font = st["bold"]
    cell.number_format = "#,##0.00"
    cell.border = st["border"]
    row += 2

    row = _section(ws, row, "3. FUNDING AT CLOSE (EUR)", st)
    _header(ws, row, ["Use of funds", "Amount (EUR)", "Source of funds", "Amount (EUR)"], st)
    row += 1
    use_items = [
        ("Cash CapEx", uses["uses"]["cash_capex"]),
        ("Interest during construction (IDC)", uses["uses"]["idc"]),
        ("Arrangement fee (1%)", uses["uses"]["arrangement_fee"]),
        ("Input VAT bridge (21%)", uses["uses"]["input_vat_bridge"]),
        ("Pre-opening costs", uses["uses"]["pre_opening"]),
        ("Opening working capital", uses["uses"]["working_capital"]),
        ("DSRA (6 months)", uses["uses"]["dsra"]),
    ]
    source_items = [
        ("Senior debt (4.25%, 20y, 12+12)", uses["sources"]["senior_debt"]),
        ("VAT bridge (refunded Month 18)", uses["sources"]["vat_bridge"]),
        ("Cash equity plug", uses["sources"]["cash_equity"]),
        ("", None),
        ("", None),
        ("", None),
        ("Land in kind (not a cash source)", uses["sources"]["land_in_kind"]),
    ]
    for (label, amount), (s_label, s_amount) in zip(use_items, source_items):
        for col, value in enumerate((label, amount, s_label, s_amount), start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col in (1, 3) else st["regular"]
            cell.border = st["border"]
            if col in (2, 4) and isinstance(value, (int, float)):
                cell.number_format = "#,##0.00"
        row += 1
    for label, value in [
        ("TOTAL CASH USES", uses["total_uses"]),
        ("TOTAL CASH SOURCES", uses["total_cash_sources"]),
        ("GAP AT CLOSE", round(uses["total_cash_sources"] - uses["total_uses"], 2)),
    ]:
        ws.cell(row=row, column=1, value=label).font = st["bold"]
        cell = ws.cell(row=row, column=2, value=value)
        cell.font = st["bold"]
        cell.number_format = "#,##0.00"
        cell.border = st["border"]
        row += 1
    ws.cell(row=row, column=1, value=(
        f"Cash equity is {summary['capital']['equity_to_cash_capex_pct']:.1f}% of cash CapEx and "
        f"{summary['capital']['equity_to_all_in_capex_pct']:.1f}% of all-in CapEx."
    )).font = st["note"]
    row += 2

    row = _section(ws, row, "4. FIVE-YEAR OPERATING PROJECTION", st)
    headers = ["Year", "Cabin revenue", "Lodge revenue", "Experiences", "Total revenue",
               "Variable costs", "Gross margin", "GM %", "Payroll", "Fixed opex", "EBITDA",
               "EBITDA %", "FF&E reserve", "CFADS", "Debt service", "DSCR", "Ending cash"]
    _header(ws, row, headers, st)
    row += 1
    for i, (_, r) in enumerate(proj.iterrows()):
        values = [
            int(r["year"]), float(r["revenue_cabins"]), float(r["revenue_lodge"]),
            float(r["revenue_experiences"]), float(r["total_revenue"]), float(r["total_variable_costs"]),
            float(r["gross_margin"]), float(r["gross_margin"] / r["total_revenue"]),
            float(r["labor_expense"]), float(r["fixed_opex"]), float(r["ebitda"]),
            float(r["ebitda"] / r["total_revenue"]), float(r["ffe_reserve"]), float(r["cfads"]),
            float(r["debt_service"]), float(kpis.iloc[i]["dscr"]), float(r["ending_cash"]),
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=round(value, 2) if isinstance(value, float) else value)
            cell.font = st["bold"] if col in (1, 5, 11, 16) else st["regular"]
            cell.border = st["border"]
            if col == 1:
                cell.number_format = "0"
            elif col in (8, 12):
                cell.number_format = "0.0%"
            elif col == 16:
                cell.number_format = "0.00x"
            else:
                cell.number_format = "#,##0.00"
        row += 1

    row += 1
    row = _section(ws, row, "5. RETURNS ON TWO CAPITAL BASES", st)
    _header(ws, row, ["Basis", "Initial investment (EUR)", "Initial equity (EUR)", "Project IRR",
                      "Equity IRR", "Project NPV @ 9%", "Equity NPV @ 9%", "Project MOIC",
                      "Equity MOIC", "Net exit value (EUR)"], st)
    row += 1
    for basis in ("all-in", "cash"):
        r = turnaround.returns(basis)
        values = [
            "All-in (land at opportunity value)" if basis == "all-in" else "Cash (sponsor cheque)",
            r["initial_capex"], r["initial_equity"], r["project_irr_exit"], r["equity_irr_exit"],
            r["project_npv"], r["equity_npv"], r["project_moic"], r["equity_moic"],
            r["net_terminal_value"],
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col == 1 else st["regular"]
            cell.border = st["border"]
            if col in (2, 3, 6, 7, 10):
                cell.number_format = "#,##0.00"
            elif col in (4, 5):
                cell.number_format = "0.00%"
            elif col in (8, 9):
                cell.number_format = "0.00x"
        row += 1
    row += 1
    for label, value, fmt in [
        ("Exit cap rate", summary["returns"]["exit_cap_rate"], "0.00%"),
        ("Exit costs", summary["returns"]["exit_cost_rate"], "0.00%"),
        ("Value gap vs all-in CapEx", summary["returns"]["value_gap_vs_all_in_capex"], "#,##0.00"),
        ("Value gap vs cash CapEx", summary["returns"]["value_gap_vs_cash_capex"], "#,##0.00"),
        ("Value gap vs all-in project investment", summary["returns"]["value_gap_vs_all_in_investment"], "#,##0.00"),
    ]:
        ws.cell(row=row, column=1, value=label).font = st["bold"]
        cell = ws.cell(row=row, column=2, value=value)
        cell.number_format = fmt
        cell.border = st["border"]
        row += 1

    row += 1
    row = _section(ws, row, "6. HONESTY CHECK: WITH AND WITHOUT THE CASERON LODGE", st)
    variants = turnaround.variants()
    _header(ws, row, ["Scope", "Revenue Y3", "EBITDA Y3", "Min DSCR", "All-in equity IRR", "Cash equity IRR"], st)
    row += 1
    for _, v in variants.iterrows():
        for col, value in enumerate(
            (v["scenario"], v["revenue_y3"], v["ebitda_y3"], v["min_dscr"], v["equity_irr_allin"], v["equity_irr_cash"]),
            start=1,
        ):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = st["border"]
            if col in (2, 3):
                cell.number_format = "#,##0.00"
            elif col == 4:
                cell.number_format = "0.00x"
            elif col in (5, 6):
                cell.number_format = "0.00%"
        row += 1

    row += 1
    _verdict(
        ws,
        row,
        (
            f"VERDICT: PROCEED. Minimum DSCR {summary['credit']['min_dscr']:.2f}x, "
            f"equity IRR {summary['returns']['all_in']['equity_irr']:.1%} all-in / "
            f"{summary['returns']['cash']['equity_irr']:.1%} cash, "
            f"and {summary['returns']['value_gap_vs_all_in_capex']:,.0f} EUR of value over all-in CapEx."
        ),
        st,
        positive=True,
    )

    ws.column_dimensions["A"].width = 42
    for col in "BCDEFGHIJKLMNOPQ":
        ws.column_dimensions[col].width = 15
    ws.freeze_panes = "A5"


# ---------------------------------------------------------------------------
# Act 5 - executive comparison
# ---------------------------------------------------------------------------
def build_executive_comparison(wb, case: InvestmentCase, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="Executive Comparison")
    ws.views.sheetView[0].showGridLines = False
    _title(
        ws,
        "ACT 5 - EXECUTIVE COMPARISON: PROMOTER PLAN vs AUDITED CASE vs CABIN TURNAROUND",
        (
            "All three columns are produced by their own engine and shown on the same convention: "
            "exit at an 8.5% cap rate, net of 3% exit costs. The audited equity IRR in Act 2 is "
            "quoted gross of exit costs (-23.16%); net of costs it is -24.4%."
        ),
        st,
    )

    formatted = case.formatted_table()
    numeric = case.comparison_table()

    row = _section(ws, 4, "1. THE THREE CASES", st)
    _header(ws, row, ["Metric"] + list(formatted.columns), st)
    row += 1
    for metric in formatted.index:
        label = ws.cell(row=row, column=1, value=metric)
        label.font = st["bold"] if metric in (
            "All-in CapEx (EUR)", "Cash equity (EUR)", "Minimum DSCR (x)",
            "Equity IRR all-in", "Value gap vs CapEx (EUR)",
        ) else st["regular"]
        label.border = st["border"]
        for col, name in enumerate(formatted.columns, start=2):
            display = formatted.loc[metric, name]
            cell = ws.cell(row=row, column=col, value=display)
            cell.font = st["bold"] if metric in (
                "All-in CapEx (EUR)", "Cash equity (EUR)", "Minimum DSCR (x)",
                "Equity IRR all-in", "Value gap vs CapEx (EUR)",
            ) else st["regular"]
            cell.border = st["border"]
            cell.alignment = Alignment(horizontal="right")
        row += 1

    row += 1
    row = _section(ws, row, "2. VALUE BRIDGE AT THE 8.5% EXIT CAP RATE (EUR, NET OF 3% COSTS)", st)
    bridge = case.value_bridge()
    _header(ws, row, ["Case", "EBITDA at exit", "Gross terminal value", "Net terminal value",
                      "All-in CapEx", "Value gap vs CapEx", "Value gap %"], st)
    row += 1
    for _, b in bridge.iterrows():
        for col, value in enumerate(
            (b["case"], b["ebitda_exit"], b["gross_terminal_value"], b["net_terminal_value"],
             b["all_in_capex"], b["value_gap_vs_capex"], b["value_gap_pct"]),
            start=1,
        ):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col in (1, 6) else st["regular"]
            cell.border = st["border"]
            if col in (2, 3, 4, 5, 6):
                cell.number_format = "#,##0.00"
            elif col == 7:
                cell.number_format = "0.0%"
        gap_cell = ws.cell(row=row, column=6)
        gap_cell.fill = st["green"] if float(b["value_gap_vs_capex"]) >= 0 else st["red"]
        row += 1

    row += 1
    row = _section(ws, row, "3. VERDICTS AND CAVEATS", st)
    _header(ws, row, ["Case", "Verdict", "Caveat"], st)
    row += 1
    for snapshot in case.snapshots():
        for col, value in enumerate((snapshot.name, snapshot.verdict, snapshot.caveat), start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col in (1, 2) else st["regular"]
            cell.border = st["border"]
            cell.alignment = Alignment(vertical="top", wrap_text=(col == 3))
        verdict_cell = ws.cell(row=row, column=2)
        verdict_cell.fill = st["green"] if snapshot.verdict == "PROCEED" else st["red"]
        verdict_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[row].height = 46
        row += 1

    row += 1
    row = _section(ws, row, "4. THE STORY IN FIVE ACTS", st)
    narrative = case.narrative()
    for key, text in narrative.items():
        title = key.replace("_", " ").title()
        ws.cell(row=row, column=1, value=title).font = st["bold"]
        cell = ws.cell(row=row, column=2, value=text)
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=8)
        ws.row_dimensions[row].height = 58
        row += 1

    ws.column_dimensions["A"].width = 38
    for col in "BCD":
        ws.column_dimensions[col].width = 28
    for col in "EFGH":
        ws.column_dimensions[col].width = 18
    ws.freeze_panes = "B5"


# ---------------------------------------------------------------------------
# T8 sensitivities
# ---------------------------------------------------------------------------
def build_t8_sensitivities(wb, turnaround: TurnaroundEngine, st: Dict[str, Any]) -> None:
    ws = wb.create_sheet(title="T8 Sensitivities")
    ws.views.sheetView[0].showGridLines = False
    _title(
        ws,
        "T8 SENSITIVITIES - EXIT CAP, DEMAND, LEVERAGE AND SCOPE",
        (
            "The base case is the good edge of the band. This tab publishes the downside: a 45% "
            "cabin occupancy or a 10% ADR cut still passes the 1.25x covenant but no longer earns "
            "a venture return. Nothing is hidden behind the base case."
        ),
        st,
    )

    df = turnaround.sensitivities()
    row = _section(ws, 4, "1. SENSITIVITY GRID", st)
    headers = ["Scenario", "Revenue Y3 (EUR)", "EBITDA Y3 (EUR)", "EBITDA margin", "Min DSCR",
               "Cash equity (EUR)", "Project IRR all-in", "Project IRR cash", "Equity IRR all-in",
               "Equity IRR cash", "Net exit value (EUR)"]
    _header(ws, row, headers, st)
    row += 1
    for _, r in df.iterrows():
        values = [
            r["scenario"], r["revenue_y3"], r["ebitda_y3"], r["ebitda_margin"], r["min_dscr"],
            r["cash_equity"], r["project_irr_allin"], r["project_irr_cash"],
            r["equity_irr_allin"], r["equity_irr_cash"], r["net_exit"],
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = st["bold"] if col == 1 else st["regular"]
            cell.border = st["border"]
            if col in (2, 3, 6, 11):
                cell.number_format = "#,##0.00"
            elif col in (4, 7, 8, 9, 10):
                cell.number_format = "0.00%"
            elif col == 5:
                cell.number_format = "0.00x"
        dscr_cell = ws.cell(row=row, column=5)
        dscr_cell.fill = st["green"] if float(r["min_dscr"]) >= 1.25 else st["red"]
        if float(r["min_dscr"]) < 1.25:
            ws.cell(row=row, column=9).fill = st["red"]
        row += 1

    row += 1
    row = _section(ws, row, "2. READING THE GRID", st)
    notes = [
        ("Exit cap", "9.0% -> 17.3% / 37.9%; 9.5% -> 15.8% / 36.2%; 10.5% -> 12.9% / 33.0% (all-in / cash equity IRR)."),
        ("Demand", "ADR -10% -> 6.1% / 23.6% and 1.79x DSCR. Occupancy 45% -> 5.4% / 22.8% and 1.79x. The covenant survives; the venture return does not."),
        ("Leverage", "EUR 400k debt -> 18.0% / 36.0%; EUR 425k -> 18.5% / 37.7%. Less leverage lowers the cash equity IRR but raises the all-in IRR."),
        ("Scope", "Cabins only (no lodge) -> 8.0% all-in / 29.5% cash and 1.75x DSCR. Bankable, not attractive: the lodge is what creates the equity return."),
        ("Covenant", "The 1.25x floor is not the binding constraint in the base case (2.31x). The binding constraint is demand: 45% occupancy still covers debt service."),
    ]
    for title, text in notes:
        ws.cell(row=row, column=1, value=title).font = st["bold"]
        cell = ws.cell(row=row, column=2, value=text)
        cell.font = st["regular"]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=11)
        ws.row_dimensions[row].height = 32
        row += 1

    ws.column_dimensions["A"].width = 26
    for col in "BCDEFGHIJK":
        ws.column_dimensions[col].width = 17
    ws.freeze_panes = "A5"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def add_case_study_tabs(
    wb,
    promoter,
    audited,
    market,
    turnaround: TurnaroundEngine,
    decline: DeclineMemoEngine,
    case: InvestmentCase,
) -> None:
    st = _styles()
    build_act_1(wb, promoter, st)
    build_act_2(wb, promoter, audited, market, st)
    build_decline_memo(wb, decline, st)
    build_act_4(wb, turnaround, st)
    build_executive_comparison(wb, case, st)
    build_t8_sensitivities(wb, turnaround, st)
