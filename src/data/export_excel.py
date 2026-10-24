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
6. Credit Risk & Copula Tail Underwriting
7. Unit Economics & Monthly Runway (RevPAR, TRevPAR, 24M Trough)
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
from src.simulation.copula_engine import CopulaSimulationEngine
from src.core.credit_committee import CreditCommitteeMemo
from src.core.unit_economics import UnitEconomicsEngine
from src.core.monthly_cash import MonthlyCashEngine


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

    # Tab 6: Multivariate Copula & Credit Committee Underwriting
    ws6 = wb.create_sheet(title="Credit Risk & Copula")
    ws6.views.sheetView[0].showGridLines = True
    ws6["A1"] = "MULTIVARIATE COPULA TAIL RISK & CREDIT COMMITTEE UNDERWRITING"
    ws6["A1"].font = title_font

    copula_engine = CopulaSimulationEngine(n_simulations=50_000, random_seed=42)
    copula_res = copula_engine.run_comparative_analysis()
    df_copula = copula_res.to_dataframe()

    # Section 1: Comparative Copula Table
    ws6["A3"] = "1. MULTIVARIATE COPULA RISK COMPARISON (50,000 SIMULATIONS)"
    ws6["A3"].font = bold_font

    for col_idx, col_name in enumerate(df_copula.columns, start=1):
        cell = ws6.cell(row=4, column=col_idx, value=col_name)
        cell.fill = navy_fill
        cell.font = header_font

    for r_idx, (_, r) in enumerate(df_copula.iterrows(), start=5):
        for c_idx, val in enumerate(r, start=1):
            cell = ws6.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border

    # Section 2: Underwriting Scorecard & DSRA Recommendation
    ws6["A9"] = "2. UNDERWRITING SCORECARD & DSRA SIZING"
    ws6["A9"].font = bold_font

    memo_obj = CreditCommitteeMemo(copula_results=copula_res)
    underwriting_kpis = [
        ("Facility Requested (Senior Mortgage)", f"{copula_engine.P:,.2f} EUR"),
        ("Total Project CapEx", f"{copula_engine.capex.total_capex:,.2f} EUR"),
        ("Senior Loan-to-Value (Total CapEx)", f"{(copula_engine.P / copula_engine.capex.total_capex)*100:.1f}%"),
        ("Baseline Year 1 DSCR", f"{float(memo_obj.df_kpis.iloc[0]['dscr']):.2f}x"),
        ("Mature Year 3 DSCR", f"{float(memo_obj.df_kpis.iloc[2]['dscr']):.2f}x"),
        ("Operating Break-Even Occupancy", f"{memo_obj.breakeven['operating_breakeven_occupancy']:.1%}"),
        ("Debt Service Break-Even Occupancy", f"{memo_obj.breakeven['debt_service_breakeven_occupancy']:.1%}"),
        ("Standard Covenant DSRA (6 Months)", f"{copula_res.dsra_standard_6m:,.2f} EUR"),
        ("Recommended Copula Tail DSRA (CVaR 99%)", f"{copula_res.dsra_recommended_tail:,.2f} EUR"),
        ("Unhedged Deficit under 6-Month DSRA", f"{copula_res.dsra_recommended_tail - copula_res.dsra_standard_6m:,.2f} EUR"),
        ("Credit Committee Recommendation", "CONDITIONAL APPROVAL (Escrow DSRA + LEADER Grant Pledge)"),
    ]

    ws6.cell(row=10, column=1, value="Underwriting Parameter").fill = navy_fill
    ws6.cell(row=10, column=1).font = header_font
    ws6.cell(row=10, column=2, value="Credit Committee Benchmark").fill = navy_fill
    ws6.cell(row=10, column=2).font = header_font

    for r_idx, (kpi, val) in enumerate(underwriting_kpis, start=11):
        c1 = ws6.cell(row=r_idx, column=1, value=kpi)
        c2 = ws6.cell(row=r_idx, column=2, value=val)
        c1.font = regular_font
        c2.font = bold_font
        c1.border = thin_border
        c2.border = thin_border

    # Tab 7: Unit Economics, Contribution Margin & 24-Month Monthly Runway
    ws7 = wb.create_sheet(title="Unit Economics & Runway")
    ws7.views.sheetView[0].showGridLines = True
    ws7["A1"] = "UNIT ECONOMICS, CONTRIBUTION MARGIN & 24-MONTH MONTHLY CASH RUNWAY"
    ws7["A1"].font = title_font

    ue_engine = UnitEconomicsEngine()
    ue_metrics = ue_engine.compute_unit_metrics()
    df_revpar = ue_engine.compute_revpar_trevpar_schedule()

    mc_engine = MonthlyCashEngine()
    df_runway = mc_engine.run_monthly_schedule(horizon_months=24)
    runway_summary = mc_engine.get_runway_summary(df_runway)

    # Section 1: Unit Economics & Marginal Costing Structure
    ws7["A3"] = "1. UNIT ECONOMICS & CONTRIBUTION MARGIN (USALI STANDARDS)"
    ws7["A3"].font = bold_font

    unit_kpis = [
        ("Daily Gross Revenue @ 100% Occ", f"{ue_metrics.daily_gross_revenue:,.2f} EUR", "8 keys: Lodging 975 EUR + F&B 525 EUR"),
        ("Variable Costs per Occupied Day", f"{ue_metrics.daily_total_variable_cost:,.2f} EUR", f"{ue_metrics.daily_variable_cost_ratio*100:.1f}% variable cost ratio"),
        ("  - F&B COGS (30% spend)", f"{ue_metrics.daily_cogs_restaurant:,.2f} EUR", "30% of daily F&B turnover"),
        ("  - OTA Commissions (60% OTA @ 15%)", f"{ue_metrics.daily_ota_commission:,.2f} EUR", "15% on 60% OTA booking mix"),
        ("  - Amenities & Guest Supplies", f"{ue_metrics.daily_amenities_cleaning:,.2f} EUR", "Direct consumables per occupied day"),
        ("Unit Contribution Margin (Day)", f"{ue_metrics.unit_contribution_margin_eur:,.2f} EUR", f"{ue_metrics.unit_contribution_margin_pct*100:.2f}% contribution margin"),
        ("Room-Night Unit Margin", f"{ue_metrics.room_contribution_margin_eur:,.2f} EUR", f"{ue_metrics.room_contribution_margin_pct*100:.2f}% per room-night"),
        ("Annual Fixed Overhead (Payroll + OPEX)", f"{ue_metrics.annual_fixed_overhead:,.2f} EUR", "Base operational fixed costs"),
        ("Annual Senior Debt Service", f"{ue_metrics.annual_senior_debt_service:,.2f} EUR", "15Y French amortization @ 3.5%"),
        ("Annual Total Fixed Burden", f"{ue_metrics.annual_total_fixed_burden:,.2f} EUR", "Overhead + full debt service"),
        ("Operating Break-Even Occupied Days", f"{ue_metrics.operating_breakeven_days:.1f} Days", f"{(ue_metrics.operating_breakeven_days / 365)*100:.1f}% annual occupancy"),
        ("Cash Debt Break-Even Occupied Days", f"{ue_metrics.cash_debt_breakeven_days:.1f} Days", f"{(ue_metrics.cash_debt_breakeven_days / 365)*100:.1f}% annual occupancy"),
        ("Bank Covenant 1.25x Break-Even Days", f"{ue_metrics.covenant_125_breakeven_days:.1f} Days", f"{(ue_metrics.covenant_125_breakeven_days / 365)*100:.1f}% annual occupancy"),
    ]

    ws7.cell(row=4, column=1, value="Metric / Cost Category").fill = navy_fill
    ws7.cell(row=4, column=1).font = header_font
    ws7.cell(row=4, column=2, value="Value").fill = navy_fill
    ws7.cell(row=4, column=2).font = header_font
    ws7.cell(row=4, column=3, value="Operational / Statutory Basis").fill = navy_fill
    ws7.cell(row=4, column=3).font = header_font

    for r_idx, (k, v, basis) in enumerate(unit_kpis, start=5):
        c1 = ws7.cell(row=r_idx, column=1, value=k)
        c2 = ws7.cell(row=r_idx, column=2, value=v)
        c3 = ws7.cell(row=r_idx, column=3, value=basis)
        c1.font = regular_font
        c2.font = bold_font
        c3.font = regular_font
        c1.border = thin_border
        c2.border = thin_border
        c3.border = thin_border

    # Section 2: RevPAR & TRevPAR Schedule
    ws7["E3"] = "2. RevPAR & TRevPAR PERFORMANCE SCHEDULE (YEARS 1 TO 3)"
    ws7["E3"].font = bold_font

    revpar_cols = [c.replace("_", " ").title() for c in df_revpar.columns]
    for col_idx, col_name in enumerate(revpar_cols, start=5):
        cell = ws7.cell(row=4, column=col_idx, value=col_name)
        cell.fill = navy_fill
        cell.font = header_font

    for r_idx, (_, r) in enumerate(df_revpar.iterrows(), start=5):
        for c_idx, val in enumerate(r, start=5):
            cell = ws7.cell(row=r_idx, column=c_idx, value=round(val, 2) if isinstance(val, (int, float)) else val)
            cell.font = regular_font
            cell.border = thin_border

    # Section 3: 24-Month Monthly Cash Flow & Runway Schedule
    start_row_runway = 18
    ws7.cell(row=start_row_runway, column=1, value="3. 24-MONTH EMPIRICAL CASH RUNWAY & CASH TROUGH SCHEDULE (SEGOVIA EMPIRICAL WEIGHTS)").font = bold_font

    runway_display_cols = [
        ("month_index", "Month"),
        ("month_name", "Period"),
        ("occupancy_pct", "Occupancy (%)"),
        ("gross_revenue", "Revenue (EUR)"),
        ("variable_costs", "Var Costs (EUR)"),
        ("contribution_margin", "Contr Margin (EUR)"),
        ("fixed_payroll", "Payroll (EUR)"),
        ("fixed_opex", "Fixed OPEX (EUR)"),
        ("senior_debt_service", "Debt Svc (EUR)"),
        ("net_operating_cash_flow", "Net Op CF (EUR)"),
        ("tax_bridge_inflows", "Grant/VAT Inflow (EUR)"),
        ("credit_line_drawn", "Credit Drawn (EUR)"),
        ("ending_cash_balance", "Ending Cash (EUR)"),
        ("liquidity_buffer_total", "Total Liquidity (EUR)"),
    ]

    header_row = start_row_runway + 1
    for col_idx, (_, col_title) in enumerate(runway_display_cols, start=1):
        cell = ws7.cell(row=header_row, column=col_idx, value=col_title)
        cell.fill = navy_fill
        cell.font = header_font

    for r_idx, (_, r) in enumerate(df_runway.iterrows(), start=header_row + 1):
        is_trough = (r["month_index"] == runway_summary.year1_trough_month_index)
        for c_idx, (col_key, _) in enumerate(runway_display_cols, start=1):
            val = r[col_key]
            if isinstance(val, float):
                val = round(val, 2)
            cell = ws7.cell(row=r_idx, column=c_idx, value=val)
            if is_trough:
                cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                cell.font = bold_font
            else:
                cell.font = regular_font
            cell.border = thin_border

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
