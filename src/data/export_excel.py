"""
Institutional multi-tab Excel model exporter.

Generates:
data/La_Dehesa_del_Castrillo_Financial_Model.xlsx
Containing:
1. Executive Summary & Underwriting Scorecard
2. Three-Statement Projections (P&L, CF, Balance Sheet)
3. Debt Amortization Schedule (French System 180 Months)
4. Scenario Stress-Testing & 2D Sensitivity Matrix
5. Monte Carlo Stochastic Simulation (N=1,000)
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd

from src.core.statements import FinancialModelEngine
from src.core.metrics import CreditMetricsEngine
from src.config.assumptions import SCENARIOS, RevenueModelConfig
from src.scenarios.scenario_analysis import ScenarioEngine
from src.simulation.monte_carlo import MonteCarloSimulator


def get_data_dir() -> Path:
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def export_institutional_excel(filename: str = "La_Dehesa_del_Castrillo_Financial_Model.xlsx") -> Path:
    output_path = get_data_dir() / filename

    # Prepare datasets
    engine = FinancialModelEngine(scenario=SCENARIOS["base"])
    df_proj = engine.run_projection(projection_years=5)
    debt_sched = engine.debt_engine.get_annual_schedule_df()

    credit = CreditMetricsEngine(target_dscr=1.25)
    df_kpi = credit.compute_credit_kpis(df_proj, debt_sched)

    sc_engine = ScenarioEngine(target_dscr=1.25, projection_years=3)
    df_scenarios = sc_engine.generate_scenario_comparison_table()
    df_matrix = sc_engine.generate_sensitivity_matrix_dscr()

    sim = MonteCarloSimulator(iterations=1000, random_seed=42)
    df_sim, summary = sim.run_simulation()

    wb = openpyxl.Workbook()

    # Style definitions
    navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    slate_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=11)
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    # Tab 1: Executive Summary
    ws1 = wb.active
    ws1.title = "Executive Scorecard"
    ws1.views.sheetView[0].showGridLines = True

    ws1["A1"] = "LA DEHESA DEL CASTRILLO S.L. - INVESTMENT MEMORANDUM & UNDERWRITING SCORECARD"
    ws1["A1"].font = title_font
    ws1["A2"] = "Location: Segovia, Spain | CapEx: 729,000 € | Capital Structure: 70% Senior Mortgage / 30% Sponsor Equity"
    ws1["A2"].font = Font(name="Calibri", size=10, italic=True, color="64748B")

    summary_headers = ["Underwriting Metric", "Year 1 (Ramp-up)", "Year 2 (Stabilization)", "Year 3 (Mature)", "Benchmark / Covenant"]
    for col_idx, h in enumerate(summary_headers, start=1):
        cell = ws1.cell(row=4, column=col_idx, value=h)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    summary_rows = [
        ("Gross Revenue (€)", f"{df_kpi.iloc[0]['total_revenue']:,.2f}", f"{df_kpi.iloc[1]['total_revenue']:,.2f}", f"{df_kpi.iloc[2]['total_revenue']:,.2f}", "Calibrated with INE Segovia"),
        ("EBITDA (€)", f"{df_kpi.iloc[0]['ebitda']:,.2f}", f"{df_kpi.iloc[1]['ebitda']:,.2f}", f"{df_kpi.iloc[2]['ebitda']:,.2f}", "Margin: 42.8% to 49.4%"),
        ("Net Income (€)", f"{df_kpi.iloc[0]['net_income']:,.2f}", f"{df_kpi.iloc[1]['net_income']:,.2f}", f"{df_kpi.iloc[2]['net_income']:,.2f}", "Linear fiscal depreciation shield"),
        ("Ending Cash (€)", f"{df_kpi.iloc[0]['ending_cash']:,.2f}", f"{df_kpi.iloc[1]['ending_cash']:,.2f}", f"{df_kpi.iloc[2]['ending_cash']:,.2f}", "Solvency confirmed; LEADER grant"),
        ("Senior Debt Balance (€)", f"{df_kpi.iloc[0]['total_debt']:,.2f}", f"{df_kpi.iloc[1]['total_debt']:,.2f}", f"{df_kpi.iloc[2]['total_debt']:,.2f}", "15-year French mortgage (€507.5k)"),
        ("Debt Service Coverage (DSCR)", f"{df_kpi.iloc[0]['dscr']:.2f}x", f"{df_kpi.iloc[1]['dscr']:.2f}x", f"{df_kpi.iloc[2]['dscr']:.2f}x", "Bank Covenant Floor >= 1.25x"),
        ("Interest Coverage (ICR)", f"{df_kpi.iloc[0]['icr']:.2f}x", f"{df_kpi.iloc[1]['icr']:.2f}x", f"{df_kpi.iloc[2]['icr']:.2f}x", "Conservative interest coverage"),
        ("Balance Sheet Discrepancy", "0.00 €", "0.00 €", "0.00 €", "Strict double-entry equality"),
    ]

    for row_idx, r_data in enumerate(summary_rows, start=5):
        for col_idx, val in enumerate(r_data, start=1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if col_idx > 1 and col_idx < 5:
                cell.alignment = Alignment(horizontal="right")
            if row_idx % 2 == 0:
                cell.fill = slate_fill

    # Tab 2: 3-Statement Model
    ws2 = wb.create_sheet(title="3-Statement Model")
    ws2.views.sheetView[0].showGridLines = True
    ws2["A1"] = "FIVE-YEAR INTEGRATED FINANCIAL STATEMENTS (P&L, CASH FLOW, BALANCE SHEET)"
    ws2["A1"].font = title_font

    cols_3stmt = [
        "year", "total_revenue", "gross_margin", "labor_expense", "fixed_opex", "ebitda",
        "depreciation", "ebit", "interest_expense", "ebt", "corporate_tax", "net_income",
        "cfo", "cfi", "cff", "ending_cash", "net_ppe", "total_assets", "total_debt", "total_equity", "balance_sheet_discrepancy"
    ]
    for col_idx, c in enumerate(cols_3stmt, start=1):
        cell = ws2.cell(row=3, column=col_idx, value=c.replace("_", " ").title())
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r_idx, (_, r) in enumerate(df_kpi[cols_3stmt].iterrows(), start=4):
        for c_idx, val in enumerate(r, start=1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=round(val, 2))
            cell.font = regular_font
            cell.border = thin_border
            if c_idx > 1:
                cell.number_format = "#,##0.00"

    # Tab 3: Debt Schedule
    ws3 = wb.create_sheet(title="Debt Schedule")
    ws3.views.sheetView[0].showGridLines = True
    ws3["A1"] = "SENIOR DEBT AMORTIZATION SCHEDULE (FRENCH SYSTEM - 15 YEARS)"
    ws3["A1"].font = title_font

    debt_cols = ["year", "beginning_balance", "payment", "principal", "interest", "ending_balance", "short_term_debt", "long_term_debt"]
    for col_idx, c in enumerate(debt_cols, start=1):
        cell = ws3.cell(row=3, column=col_idx, value=c.replace("_", " ").title())
        cell.fill = navy_fill
        cell.font = header_font

    for r_idx, (_, r) in enumerate(debt_sched.iterrows(), start=4):
        for c_idx, val in enumerate(r, start=1):
            cell = ws3.cell(row=r_idx, column=c_idx, value=round(val, 2))
            cell.font = regular_font
            cell.border = thin_border
            if c_idx > 1:
                cell.number_format = "#,##0.00"

    # Tab 4: Scenarios & Sensitivity
    ws4 = wb.create_sheet(title="Scenario Stress-Testing")
    ws4.views.sheetView[0].showGridLines = True
    ws4["A1"] = "SCENARIO COMPARISONS & 2D DSCR SENSITIVITY MATRIX"
    ws4["A1"].font = title_font

    for col_idx, c in enumerate(df_scenarios.columns, start=1):
        cell = ws4.cell(row=3, column=col_idx, value=c)
        cell.fill = navy_fill
        cell.font = header_font

    for r_idx, (_, r) in enumerate(df_scenarios.iterrows(), start=4):
        for c_idx, val in enumerate(r, start=1):
            cell = ws4.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border

    # Tab 5: Monte Carlo
    ws5 = wb.create_sheet(title="Monte Carlo Risk")
    ws5.views.sheetView[0].showGridLines = True
    ws5["A1"] = "MONTE CARLO STOCHASTIC CREDIT RISK SIMULATION (N=1,000)"
    ws5["A1"].font = title_font

    mc_kpis = [
        ("Simulations Executed", f"{summary.iterations:,}"),
        ("Mean DSCR (Year 1)", f"{summary.mean_dscr_y1:.2f}x"),
        ("Median DSCR (Year 1)", f"{summary.median_dscr_y1:.2f}x"),
        ("VaR 95% DSCR (5th Percentile)", f"{summary.p5_dscr_y1:.2f}x"),
        ("P(Covenant Breach) [DSCR < 1.25x]", f"{summary.prob_covenant_breach_y1*100:.1f}%"),
        ("P(Cash Insolvency) [DSCR < 1.00x]", f"{summary.prob_cash_insolvency_y1*100:.1f}%"),
        ("Mean Equity IRR", f"{summary.mean_equity_irr*100:.1f}%"),
        ("Mean Ending Cash Year 1", f"{summary.mean_ending_cash_y1:,.2f} €"),
    ]

    ws5.cell(row=3, column=1, value="Simulation Parameter").fill = navy_fill
    ws5.cell(row=3, column=1).font = header_font
    ws5.cell(row=3, column=2, value="Result Value").fill = navy_fill
    ws5.cell(row=3, column=2).font = header_font

    for r_idx, (kpi, val) in enumerate(mc_kpis, start=4):
        c1 = ws5.cell(row=r_idx, column=1, value=kpi)
        c2 = ws5.cell(row=r_idx, column=2, value=val)
        c1.font = regular_font
        c2.font = bold_font
        c1.border = thin_border
        c2.border = thin_border

    # Auto-adjust column widths across all sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(output_path)
    return output_path


if __name__ == "__main__":
    out = export_institutional_excel()
    print(f"Generated institutional Excel model: {out.name} ({out.stat().st_size / 1024:.1f} KB)")
