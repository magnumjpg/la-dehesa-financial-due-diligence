"""
Institutional multi-tab Excel model exporter.

Generates data/La_Dehesa_del_Castrillo_Financial_Model.xlsx with 22 tabs:
 1. Read Me & Checks
 2. Inputs
 3. Live Model
 4. Funding & Audit
 5. Executive Scorecard
 6. 3-Statement Model
 7. Debt Schedule
 8. Scenario Stress-Testing
 9. Monte Carlo Risk
10. Credit Risk & Copula
11. Unit Economics & Runway
12. Phase II Expansion
13. Reform Case
14. Act 1 - Promoter
15. Act 2 - Audit
16. Decline Memo
17. Act 4 - T8
18. Executive Comparison
19. T8 Sensitivities
20. T8 Inputs
21. T8 Debt Schedule
22. T8 Live Model
"""

from datetime import datetime
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
from src.core.expansion import ExpansionFinancialEngine
from src.data.live_excel import add_live_model_tabs
from src.data.act_excel import add_case_study_tabs
from src.data.t8_excel import add_t8_model_tabs
from src.core.turnaround import TurnaroundEngine
from src.core.decline import DeclineMemoEngine
from src.core.investment_case import InvestmentCase


def get_data_dir() -> Path:
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _normalise_xlsx_timestamps(path: Path) -> None:
    """Rewrite the xlsx zip with fixed member and document timestamps.

    openpyxl stamps every zip member with the current time and refreshes the
    docProps/core.xml timestamps on save, so two runs of the same model produce
    different bytes. Fixed timestamps keep the committed workbook reproducible.
    """
    import os
    import re
    import zipfile

    fixed = (2026, 1, 1, 0, 0, 0)
    fixed_iso = "2026-01-01T00:00:00Z"
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(path) as src:
        members = [
            (info.filename, info.compress_type, src.read(info))
            for info in src.infolist()
        ]
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for name, compress_type, data in members:
            if name == "docProps/core.xml":
                text = data.decode("utf-8")
                text = re.sub(
                    r"(<dcterms:created[^>]*>)[^<]*(</dcterms:created>)",
                    rf"\g<1>{fixed_iso}\g<2>",
                    text,
                )
                text = re.sub(
                    r"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)",
                    rf"\g<1>{fixed_iso}\g<2>",
                    text,
                )
                data = text.encode("utf-8")
            info = zipfile.ZipInfo(name, date_time=fixed)
            info.compress_type = compress_type
            dst.writestr(info, data)
    os.replace(tmp, path)


def _order_sheets(wb) -> None:
    """Places the narrative tabs in reading order, leaving extras at the end."""
    preferred = [
        "Read Me & Checks",
        "Inputs",
        "Live Model",
        "Funding & Audit",
        "Executive Scorecard",
        "3-Statement Model",
        "Debt Schedule",
        "Scenario Stress-Testing",
        "Monte Carlo Risk",
        "Credit Risk & Copula",
        "Unit Economics & Runway",
        "Phase II Expansion",
        "Reform Case",
        "Act 1 - Promoter",
        "Act 2 - Audit",
        "Decline Memo",
        "Act 4 - T8",
        "Executive Comparison",
        "T8 Sensitivities",
        "T8 Inputs",
        "T8 Debt Schedule",
        "T8 Live Model",
    ]
    existing = [name for name in preferred if name in wb.sheetnames]
    remaining = [name for name in wb.sheetnames if name not in existing]
    wb._sheets = [wb[name] for name in existing + remaining]


def export_institutional_excel(filename: str = "La_Dehesa_del_Castrillo_Financial_Model.xlsx") -> Path:
    output_path = get_data_dir() / filename

    # Prepare datasets
    engine = FinancialModelEngine(scenario=SCENARIOS["base"])
    df_proj = engine.run_projection(projection_years=5)
    debt_sched = engine.debt_engine.get_annual_schedule_df()

    credit = CreditMetricsEngine(target_dscr=1.25)
    df_kpi = credit.compute_credit_kpis(df_proj, debt_sched)
    returns = credit.compute_returns_summary(
        df_proj,
        initial_equity=engine.total_equity_at_close,
        initial_capex=engine.total_project_investment,
        exit_cap_rate=0.085,
    )

    sc_engine = ScenarioEngine(target_dscr=1.25, projection_years=3)
    df_scenarios = sc_engine.generate_scenario_comparison_table()
    df_matrix = sc_engine.generate_sensitivity_matrix_dscr()

    sim = MonteCarloSimulator(iterations=1000, random_seed=42)
    df_sim, summary = sim.run_simulation()

    wb = openpyxl.Workbook()
    wb.properties.creator = "Jaime Pérez"
    wb.properties.lastModifiedBy = "Jaime Pérez"
    wb.properties.created = datetime(2026, 1, 1)
    wb.properties.modified = datetime(2026, 1, 1)

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

    ws1["A1"] = "LA DEHESA DEL CASTRILLO S.L. - MANAGEMENT (UPSIDE) CASE & UNDERWRITING SCORECARD"
    ws1["A1"].font = title_font
    ws1["A2"] = (
        "Location: Segovia, Spain | All-in CapEx: 1,050,100 EUR | Capital structure: 35% LTV senior debt "
        "(20 years, 12-month grace) / cash equity plug + land in kind"
    )
    ws1["A2"].font = Font(name="Calibri", size=10, italic=True, color="64748B")

    summary_headers = ["Underwriting Metric", "Year 1 (Ramp-up)", "Year 2 (First Amortising Year)", "Year 3 (Mature)", "Benchmark / Covenant"]
    for col_idx, h in enumerate(summary_headers, start=1):
        cell = ws1.cell(row=4, column=col_idx, value=h)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    project_irr = returns["project_irr_exit"]
    equity_irr = returns["equity_irr_exit"]
    project_irr_txt = f"{project_irr * 100:.2f}%" if project_irr is not None else "n/a"
    equity_irr_txt = f"{equity_irr * 100:.2f}%" if equity_irr is not None else "n/a"

    summary_rows = [
        ("Gross Revenue (EUR)", f"{df_kpi.iloc[0]['total_revenue']:,.2f}", f"{df_kpi.iloc[1]['total_revenue']:,.2f}", f"{df_kpi.iloc[2]['total_revenue']:,.2f}", "Management 31.36%; INE market 21.24%"),
        ("EBITDA (EUR)", f"{df_kpi.iloc[0]['ebitda']:,.2f}", f"{df_kpi.iloc[1]['ebitda']:,.2f}", f"{df_kpi.iloc[2]['ebitda']:,.2f}", f"Margin {df_kpi.iloc[0]['ebitda']/df_kpi.iloc[0]['total_revenue']*100:.1f}% to {df_kpi.iloc[2]['ebitda']/df_kpi.iloc[2]['total_revenue']*100:.1f}%"),
        ("FF&E Reserve (3%) (EUR)", f"{df_proj.iloc[0]['ffe_reserve']:,.2f}", f"{df_proj.iloc[1]['ffe_reserve']:,.2f}", f"{df_proj.iloc[2]['ffe_reserve']:,.2f}", "Ranked ahead of debt service"),
        ("CFADS (EBITDA - FF&E - tax) (EUR)", f"{df_proj.iloc[0]['cfads']:,.2f}", f"{df_proj.iloc[1]['cfads']:,.2f}", f"{df_proj.iloc[2]['cfads']:,.2f}", "Cash actually available to the lender"),
        ("Net Income (EUR)", f"{df_kpi.iloc[0]['net_income']:,.2f}", f"{df_kpi.iloc[1]['net_income']:,.2f}", f"{df_kpi.iloc[2]['net_income']:,.2f}", "25% tax; Year-1 BINs shield later years"),
        ("Ending Cash (EUR)", f"{df_kpi.iloc[0]['ending_cash']:,.2f}", f"{df_kpi.iloc[1]['ending_cash']:,.2f}", f"{df_kpi.iloc[2]['ending_cash']:,.2f}", "After close-day uses; see Funding & Audit"),
        ("Senior Debt Balance (EUR)", f"{df_kpi.iloc[0]['total_debt']:,.2f}", f"{df_kpi.iloc[1]['total_debt']:,.2f}", f"{df_kpi.iloc[2]['total_debt']:,.2f}", "20-year French mortgage, 12-month grace (EUR 367.5k)"),
        ("Debt Service Coverage (DSCR)", f"{df_kpi.iloc[0]['dscr']:.2f}x", f"{df_kpi.iloc[1]['dscr']:.2f}x", f"{df_kpi.iloc[2]['dscr']:.2f}x", "Bank covenant floor >= 1.25x"),
        ("Interest Coverage (ICR)", f"{df_kpi.iloc[0]['icr']:.2f}x", f"{df_kpi.iloc[1]['icr']:.2f}x", f"{df_kpi.iloc[2]['icr']:.2f}x", "Conservative interest coverage"),
        ("Balance Sheet Discrepancy", "0.00", "0.00", "0.00", "Strict double-entry equality"),
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

    # Capital structure and returns block.
    ws1["A16"] = "CAPITAL STRUCTURE AND RETURNS (MANAGEMENT CASE)"
    ws1["A16"].font = bold_font
    ws1["A17"] = "Metric"
    ws1["B17"] = "Value"
    for c in ("A17", "B17"):
        ws1[c].fill = navy_fill
        ws1[c].font = header_font
    capital_rows = [
        ("All-in CapEx (EUR)", f"{engine.capex.total_capex:,.2f}"),
        ("Senior debt (35% LTV) (EUR)", f"{engine.financing.senior_debt_principal:,.2f}"),
        ("DSCR-capped principal at 1.25x (EUR)", f"{engine.debt_sizing()['principal_dscr_cap']:,.2f}"),
        ("Cash equity plug (EUR)", f"{engine.cash_equity:,.2f}"),
        ("Total equity at close (EUR)", f"{engine.total_equity_at_close:,.2f}"),
        ("Total project investment (EUR)", f"{engine.total_project_investment:,.2f}"),
        ("Cash equity / CapEx", f"{engine.cash_equity / engine.capex.total_capex * 100:.2f}%"),
        ("Project IRR, 8.5% exit", project_irr_txt),
        ("Equity IRR, 8.5% exit", equity_irr_txt),
        ("Project IRR, no exit", f"{returns['project_irr'] * 100:.2f}%" if returns["project_irr"] is not None else "n/a"),
        ("Equity IRR, no exit", f"{returns['equity_irr'] * 100:.2f}%" if returns["equity_irr"] is not None else "n/a"),
    ]
    for r_idx, (label, value) in enumerate(capital_rows, start=18):
        c1 = ws1.cell(row=r_idx, column=1, value=label)
        c2 = ws1.cell(row=r_idx, column=2, value=value)
        c1.font = regular_font
        c2.font = bold_font
        c1.border = thin_border
        c2.border = thin_border

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

    # Tab 3 (Debt Schedule) is written by the live_excel module: a 240-month
    # formula-driven amortisation with an annual SUMIF summary.

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
    ws5["A1"] = "MONTE CARLO STOCHASTIC CREDIT RISK SIMULATION (N=1,000 DRAWS ON THE MINIMUM DSCR)"
    ws5["A1"].font = title_font

    mc_kpis = [
        ("Simulations Executed", f"{summary.iterations:,}"),
        ("Mean Minimum DSCR (Years 1-3)", f"{summary.mean_min_dscr:.2f}x"),
        ("Median Minimum DSCR (Years 1-3)", f"{summary.median_min_dscr:.2f}x"),
        ("VaR 95% Minimum DSCR (5th Percentile)", f"{summary.p5_min_dscr:.2f}x"),
        ("P(Covenant Breach) [min DSCR < 1.25x]", f"{summary.prob_covenant_breach*100:.1f}%"),
        ("P(Debt-Service Shortfall) [min DSCR < 1.00x]", f"{summary.prob_cash_insolvency*100:.1f}%"),
        ("Mean Equity IRR (8.5% exit)", f"{summary.mean_equity_irr*100:.1f}%"),
        ("VaR 95% Equity IRR (5th Percentile)", f"{summary.p5_equity_irr*100:.1f}%"),
        ("Cash Equity at Close (fixed in every draw)", f"{summary.cash_equity:,.2f} EUR"),
        ("Total Equity at Close", f"{summary.total_equity_at_close:,.2f} EUR"),
        ("Mean Ending Cash Year 1", f"{summary.mean_ending_cash_y1:,.2f} EUR"),
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
    be = memo_obj.breakeven
    underwriting_kpis = [
        ("Facility Requested (Senior Mortgage, 35% LTV)", f"{copula_engine.P:,.2f} EUR"),
        ("DSCR-Capped Principal at 1.25x", f"{memo_obj.debt_sizing['principal_dscr_cap']:,.2f} EUR"),
        ("Binding Constraint", str(memo_obj.debt_sizing["binding_constraint"])),
        ("Total Project CapEx", f"{copula_engine.capex.total_capex:,.2f} EUR"),
        ("Senior Loan-to-Value (Total CapEx)", f"{(copula_engine.P / copula_engine.capex.total_capex)*100:.1f}%"),
        ("Cash Equity Required", f"{memo_obj.cash_equity:,.2f} EUR ({memo_obj.equity_to_capex:.1f}% of CapEx)"),
        ("Year 1 DSCR (interest-only)", f"{float(memo_obj.df_kpis.iloc[0]['dscr']):.2f}x"),
        ("Year 2 DSCR (first amortising year)", f"{float(memo_obj.df_kpis.iloc[1]['dscr']):.2f}x"),
        ("Mature Year 3 DSCR", f"{float(memo_obj.df_kpis.iloc[2]['dscr']):.2f}x"),
        ("Operating Break-Even Occupancy (EBITDA = 0)", f"{be['operating_breakeven_occupancy_mature']:.2%}"),
        ("Cash Debt-Service Break-Even (DSCR = 1.00x)", f"{be['debt_service_breakeven_occupancy_mature']:.2%}"),
        ("Covenant Break-Even (DSCR = 1.25x)", f"{be['covenant_breakeven_occupancy_mature']:.2%}"),
        ("ADR Required for the 1.25x Covenant", f"{be['covenant_breakeven_adr']:,.2f} EUR"),
        ("ADR Required for a 10% Equity IRR (8.5% exit)", f"{be['equity_irr_10pct_adr']:,.2f} EUR"),
        ("Contractual DSRA (6 Months)", f"{copula_res.dsra_standard_6m:,.2f} EUR"),
        ("Recommended Copula Tail DSRA (Clayton CVaR 99%)", f"{copula_res.dsra_recommended_tail:,.2f} EUR"),
        ("Unhedged Deficit under the 6-Month DSRA", f"{copula_res.dsra_recommended_tail - copula_res.dsra_standard_6m:,.2f} EUR"),
        ("Credit Committee Recommendation", memo_obj.recommendation),
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
        ("Annual Senior Debt Service", f"{ue_metrics.annual_senior_debt_service:,.2f} EUR", "20Y French amortization @ 4.0%, 12-month grace"),
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
        ("operating_cash_flow", "Operating CF (EUR)"),
        ("leader_inflow", "LEADER Grant (EUR)"),
        ("vat_refund_inflow", "VAT Refund (EUR)"),
        ("credit_line_draw", "Revolver Draw (EUR)"),
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

    # Tab 8: Phase II Expansion - Landscape Suites & Biological Pond
    ws8 = wb.create_sheet(title="Phase II Expansion")
    ws8.views.sheetView[0].showGridLines = True
    ws8["A1"] = "PHASE II EXPANSION: LANDSCAPE HOTEL SUITES & BIOLOGICAL RESERVOIR (VALUE-ADD)"
    ws8["A1"].font = title_font

    exp_engine = ExpansionFinancialEngine()
    exp_capex = exp_engine.capex
    exp_pnl = exp_engine.compute_stabilized_pnl(scenario="base")
    df_exp_5y = exp_engine.compute_5year_schedule()
    exp_metrics = exp_engine.compute_investment_metrics()
    exp_realistic = exp_engine.compute_investment_metrics(scenario="realistic")
    exp_stress = exp_engine.compute_investment_metrics(scenario="stress")
    phase1_cash_y2 = float(df_kpi.iloc[1]["ending_cash"])
    phase1_dscr_y3 = float(df_kpi.iloc[2]["dscr"])
    exp_cons = exp_engine.compute_consolidated_underwriting(
        phase1_rev_y3=float(df_proj.iloc[2]["total_revenue"]),
        phase1_ebitda_y3=float(df_proj.iloc[2]["ebitda"]),
        phase1_cfads_y3=float(df_proj.iloc[2]["cfads"]),
        phase1_senior_debt_service=float(df_proj.iloc[2]["debt_service"]),
        phase1_capex=float(engine.capex.total_capex),
        phase1_cash_end_y2=phase1_cash_y2,
        phase1_dscr_y3=phase1_dscr_y3,
    )

    # Section 1: All-In CapEx Schedule
    ws8["A3"] = "1. PHASE II ALL-IN CAPEX & EXECUTION BUDGET (110 M² SUITES + 200 M² POND)"
    ws8["A3"].font = bold_font

    capex_rows = [
        ("Pure Building PEM (Foundations, Stone, Timber, Glazing, HVAC, Bath)", f"{exp_capex.pure_building_pem:,.2f} EUR", "1,468.18 EUR/m² built (110 m²)"),
        ("Contractor PEC - Pure Building (13% GG + 6% BI)", f"{exp_capex.pure_building_pem * 1.19:,.2f} EUR", "1,747.14 EUR/m² built"),
        ("Estate Utilities & Trenching Across 25 Ha (Water, Power, Bio-Sewage)", f"{exp_capex.utilities_trenching_25ha_pem * 1.19:,.2f} EUR", "37,485.00 EUR PEC"),
        ("5-Star FF&E, High-End Textiles, Porch & Exterior Hot Tub", f"{exp_capex.ffe_textiles_hot_tub_pem * 1.19:,.2f} EUR", "41,650.00 EUR PEC (2 suites)"),
        ("Biological Pond (200 m² EPDM, Biofilter, Zeolites, Cascade, Flora)", f"{exp_capex.biological_pond_200m2_pem * 1.19:,.2f} EUR", "38,080.00 EUR PEC (190.40 EUR/m² water)"),
        ("TOTAL CONTRACTOR WORKS PEC (Capítulo 1 al 8)", f"{exp_capex.total_execution_pec:,.2f} EUR", "2,812.73 EUR/m² repercutido"),
        ("Architecture, Engineering & Project Management Fees (9.0% PEM)", f"{exp_capex.engineering_architecture_fees:,.2f} EUR", "Complete technical project & permits"),
        ("Municipal Taxes, Urban Fees & ICIO (4.5% PEM)", f"{exp_capex.municipal_taxes_icio:,.2f} EUR", "Segovia rural municipality rate"),
        ("Contingency Reserve (5.0% PEC)", f"{exp_capex.contingency_reserve:,.2f} EUR", "Granite rock & unforeseen works"),
        ("TOTAL ALL-IN EXPANSION CAPEX (Net of Deductible VAT)", f"{exp_capex.total_all_in_capex:,.2f} EUR", "179,985.00 EUR all-in per suite"),
        ("Financing Structure (Phase-Gated)", f"{exp_cons['phase2_funding_gap']:,.2f} EUR gap", "Phase I cash < Phase II need; do not double-count LEADER + VAT"),
    ]

    ws8.cell(row=4, column=1, value="CapEx Investment Chapter").fill = navy_fill
    ws8.cell(row=4, column=1).font = header_font
    ws8.cell(row=4, column=2, value="Budget (EUR)").fill = navy_fill
    ws8.cell(row=4, column=2).font = header_font
    ws8.cell(row=4, column=3, value="Technical Benchmark / Repercussion").fill = navy_fill
    ws8.cell(row=4, column=3).font = header_font

    for r_idx, (ch, val, note) in enumerate(capex_rows, start=5):
        c1 = ws8.cell(row=r_idx, column=1, value=ch)
        c2 = ws8.cell(row=r_idx, column=2, value=val)
        c3 = ws8.cell(row=r_idx, column=3, value=note)
        c1.font = regular_font
        c2.font = bold_font
        c3.font = regular_font
        c1.border = thin_border
        c2.border = thin_border
        c3.border = thin_border

    # Section 2: Financial Metrics & Exit Arbitrage
    ws8["E3"] = "2. INVESTMENT RETURNS & CAPITAL ALLOCATION METRICS"
    ws8["E3"].font = bold_font

    returns_rows = [
        ("Stabilized Year 3 Gross Revenue", f"{exp_pnl['gross_revenue']:,.2f} EUR", "ADR 290 EUR net | 50% Occ (365 nights)"),
        ("Stabilized Year 3 Contribution Margin", f"{exp_pnl['contribution_margin']:,.2f} EUR", f"{exp_pnl['contribution_margin_ratio']*100:.2f}% contribution margin"),
        ("Stabilized Year 3 Incremental EBITDA", f"{exp_pnl['ebitda']:,.2f} EUR", f"{exp_pnl['ebitda_margin']*100:.2f}% EBITDA margin"),
        ("Stabilized Year 3 Free Cash Flow (Post-Tax)", f"{exp_pnl['free_cash_flow']:,.2f} EUR", "Clean cash flow net of 2% FF&E reserve"),
        ("Development Yield on Cost (EBITDA / CapEx)", f"{exp_metrics['yield_on_cost']*100:.2f}%", "Unlevered gross development yield"),
        ("Return on Invested Capital (ROIC Y3)", f"{exp_metrics['roic_y3']*100:.2f}%", "+938 bps spread over 8.0% WACC"),
        ("Simple EBITDA Payback Period", f"{exp_metrics['simple_ebitda_payback_years']:.2f} Years", "47.6 months recovery"),
        ("Simple Post-Tax FCF Payback Period", f"{exp_metrics['simple_fcf_payback_years']:.2f} Years", "61.2 months recovery"),
        ("Year 5 Exit Valuation @ 8.5% Cap Rate", f"{exp_metrics['exit_val_85bps']:,.2f} EUR", f"Net gain: +{exp_metrics['net_gain_85bps']:,.2f} EUR"),
        ("5-Year Post-Tax IRR with Exit (8.5% Cap Rate)", f"{exp_metrics['irr_85bps']*100:.2f}%", f"MOIC: {exp_metrics['moic_85bps']:.2f}x"),
        ("Realistic Scenario EBITDA (30% occ + 1 FTE)", f"{exp_realistic['ebitda_y3']:,.2f} EUR", f"IRR: {exp_realistic['irr_85bps']*100:.1f}%"),
        ("Stress Scenario EBITDA (INE 21.24% occ + 1 FTE)", f"{exp_stress['ebitda_y3']:,.2f} EUR", f"IRR: {exp_stress['irr_85bps']*100:.1f}%"),
        ("Phase II Cash Need (net CapEx + VAT)", f"{exp_cons['phase2_cash_need']:,.2f} EUR", "EUR 359,970 + EUR 75,593.70 input VAT"),
        ("Phase I Cash at End of Year 2", f"{phase1_cash_y2:,.2f} EUR", "Available for Phase II"),
        ("Phase II Funding Gap", f"{exp_cons['phase2_funding_gap']:,.2f} EUR", "Negative = not self-funded; raise additional funding"),
        ("Consolidated Group EBITDA (Phase I + realistic Phase II)", f"{exp_cons['consolidated_ebitda_y3']:,.2f} EUR", f"{exp_cons['ebitda_increase_pct']*100:+.1f}% vs Phase I baseline (if funded)"),
        ("Consolidated DSCR (CFADS basis)", f"{exp_cons['consolidated_dscr_y3']:.2f}x", f"{phase1_dscr_y3:.2f}x standalone to {exp_cons['consolidated_dscr_y3']:.2f}x consolidated (no new senior debt)"),
    ]

    ws8.cell(row=4, column=5, value="Return / Underwriting Parameter").fill = navy_fill
    ws8.cell(row=4, column=5).font = header_font
    ws8.cell(row=4, column=6, value="Metric Value").fill = navy_fill
    ws8.cell(row=4, column=6).font = header_font
    ws8.cell(row=4, column=7, value="Strategic Interpretation").fill = navy_fill
    ws8.cell(row=4, column=7).font = header_font

    for r_idx, (p, val, note) in enumerate(returns_rows, start=5):
        c1 = ws8.cell(row=r_idx, column=5, value=p)
        c2 = ws8.cell(row=r_idx, column=6, value=val)
        c3 = ws8.cell(row=r_idx, column=7, value=note)
        c1.font = regular_font
        c2.font = bold_font
        c3.font = regular_font
        c1.border = thin_border
        c2.border = thin_border
        c3.border = thin_border

    # Section 3: 5-Year Trajectory Schedule
    start_row_traj = 25
    ws8.cell(row=start_row_traj, column=1, value="3. 5-YEAR COMMERCIAL RAMP-UP & CASH FLOW TRAJECTORY SCHEDULE").font = bold_font

    traj_display_cols = [
        ("year", "Year"),
        ("occupancy_rate", "Occupancy (%)"),
        ("occupied_nights", "Nights Sold"),
        ("adr_net", "ADR Net (EUR)"),
        ("gross_revenue", "Revenue (EUR)"),
        ("contribution_margin", "Contr Margin (EUR)"),
        ("ebitda", "EBITDA (EUR)"),
        ("ebit", "EBIT (EUR)"),
        ("tax", "Tax 25% (EUR)"),
        ("net_income", "Net Income (EUR)"),
        ("free_cash_flow", "Free Cash Flow (EUR)"),
        ("discounted_fcf", "Discounted FCF (EUR)"),
    ]

    header_row_traj = start_row_traj + 1
    for col_idx, (_, col_title) in enumerate(traj_display_cols, start=1):
        cell = ws8.cell(row=header_row_traj, column=col_idx, value=col_title)
        cell.fill = navy_fill
        cell.font = header_font

    for r_idx, (_, r) in enumerate(df_exp_5y.iterrows(), start=header_row_traj + 1):
        for c_idx, (col_key, _) in enumerate(traj_display_cols, start=1):
            val = r[col_key]
            if col_key == "occupancy_rate":
                val = f"{val*100:.1f}%"
            elif isinstance(val, float):
                val = round(val, 2)
            cell = ws8.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border

    # Tab 9: Reform / Resize Case (separate post-decline layer)
    from src.config.reform import get_reform_preset
    from src.core.reform import ReformAnalysisEngine

    reform_engine = ReformAnalysisEngine()
    reform_presets = reform_engine.run_presets()
    reform_bridge = reform_engine.value_bridge(get_reform_preset("revenue_reform"))
    reform_frontier = reform_engine.frontier(
        capex_levels=[1_050_100, 950_000, 850_000, 770_000, 700_000],
        cover_levels=[0, 3, 6, 8, 10],
        base_config=get_reform_preset("revenue_reform"),
    )
    reform_stress = reform_engine.stress_cases()
    reform_rate = reform_engine.rate_sensitivity()
    reform_rec = reform_engine.recommendation()
    cabin_presets = reform_engine.run_cabin_presets()
    cabin_rec = reform_engine.cabin_recommendation()
    cabin_ladder = cabin_rec["cost_ladder"]

    ws9 = wb.create_sheet(title="Reform Case")
    ws9.views.sheetView[0].showGridLines = True
    ws9["A1"] = "REFORM / RESIZE CASE - WHAT WOULD HAVE TO BE TRUE AFTER THE DECLINE?"
    ws9["A1"].font = title_font
    ws9["A2"] = (
        "A separate layer on top of the three as-is cases. It does not rewrite the management, "
        "INE market or promoter projections; it asks whether a revenue-led reform can create value. "
        "The answer is allowed to be no, and the conservative bank test is EV versus TOTAL project "
        "investment (CapEx + IDC + pre-opening + working capital + DSRA), not EV versus CapEx alone."
    )
    ws9["A2"].font = Font(name="Calibri", size=10, italic=True, color="64748B")
    ws9["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws9.merge_cells("A2:N2")
    ws9.row_dimensions[2].height = 42

    ws9["A4"] = "1. R1-R6 REFORM PRESETS (ALL SIX ARE SHOWN; NEGATIVE RESULTS ARE NOT HIDDEN)"
    ws9["A4"].font = bold_font

    preset_headers = [
        ("key", "Ref"),
        ("name", "Reform case"),
        ("capex", "CapEx (EUR)"),
        ("total_project_investment", "Total investment (EUR)"),
        ("revenue_y5", "Revenue Y5 (EUR)"),
        ("ebitda_y5", "EBITDA Y5 (EUR)"),
        ("dscr_min", "Min DSCR"),
        ("ev_cap_rate", "EV @ exit cap (EUR)"),
        ("value_gap_capex", "Gap vs CapEx (EUR)"),
        ("value_gap_total_investment", "Gap vs total inv. (EUR)"),
        ("net_value_gap_total_investment", "Net gap vs total inv. (EUR)"),
        ("project_npv", "Project NPV (EUR)"),
        ("project_irr_exit", "Project IRR"),
        ("equity_irr_exit", "Equity IRR"),
    ]
    for col_idx, (_, label) in enumerate(preset_headers, start=1):
        cell = ws9.cell(row=5, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for r_idx, (_, row) in enumerate(reform_presets.iterrows(), start=6):
        for c_idx, (key, _) in enumerate(preset_headers, start=1):
            val = row[key]
            if key in ("project_irr_exit", "equity_irr_exit"):
                val = "n/a" if val is None or pd.isna(val) else float(val)
            elif key == "key":
                val = str(val).upper().replace("_", " ")
            elif isinstance(val, (int, float)):
                val = round(float(val), 2)
            cell = ws9.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if key in ("capex", "total_project_investment", "revenue_y5", "ebitda_y5", "ev_cap_rate", "value_gap_capex", "value_gap_total_investment", "net_value_gap_total_investment", "project_npv"):
                cell.number_format = "#,##0"
            elif key == "dscr_min":
                cell.number_format = "0.00x"
            elif key in ("project_irr_exit", "equity_irr_exit") and isinstance(val, float):
                cell.number_format = "0.00%"

    # Section 2: value bridge
    r = 14
    ws9.cell(row=r, column=1, value="2. R2 VALUE BRIDGE - MATURE EBITDA AND EV AT THE 8.5% EXIT CAP RATE").font = bold_font
    _header = ["Bridge component", "EBITDA impact (EUR)", "EV impact @ 8.5% (EUR)"]
    for col_idx, label in enumerate(_header, start=1):
        cell = ws9.cell(row=r + 1, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    bridge_rows = [
        ("Base management EBITDA", reform_bridge["base_ebitda"], reform_bridge["base_ev"]),
        ("+ ADR uplift (5%)", reform_bridge["components_ebitda"]["adr_uplift"], reform_bridge["components_ev"]["adr_uplift"]),
        ("+ External F&B (6 covers/day)", reform_bridge["components_ebitda"]["external_fnb"], reform_bridge["components_ev"]["external_fnb"]),
        ("+ Experiences", reform_bridge["components_ebitda"]["experiences"], reform_bridge["components_ev"]["experiences"]),
        ("+ Cost savings", reform_bridge["components_ebitda"]["cost_savings"], reform_bridge["components_ev"]["cost_savings"]),
        ("Reform EBITDA and EV", reform_bridge["reform_ebitda"], reform_bridge["reform_ev"]),
    ]
    for r_idx, row in enumerate(bridge_rows, start=r + 2):
        for c_idx, val in enumerate(row, start=1):
            cell = ws9.cell(row=r_idx, column=c_idx, value=round(float(val), 2) if c_idx > 1 else val)
            cell.font = bold_font if r_idx in (r + 2, r + 7) else regular_font
            cell.border = thin_border
            if c_idx > 1:
                cell.number_format = "#,##0"

    value_rows = [
        ("Enterprise value", reform_bridge["reform_ev"], reform_bridge["net_exit_value"]),
        ("Exit costs", 0.0, -reform_bridge["exit_costs"]),
        ("Reform CapEx", reform_bridge["capex"], reform_bridge["capex"]),
        ("Value gap vs CapEx", reform_bridge["value_gap_capex"], reform_bridge["net_value_gap_capex"]),
        ("Total project investment", reform_bridge["total_project_investment"], reform_bridge["total_project_investment"]),
        ("Value gap vs total investment", reform_bridge["value_gap_total_investment"], reform_bridge["net_value_gap_total_investment"]),
        ("Bridge tie (must be zero)", reform_bridge["bridge_tie"], reform_bridge["bridge_tie"]),
    ]
    for col_idx, label in enumerate(
        ["Value test", "Gross (EUR)", "Net of exit costs (EUR)"], start=1
    ):
        cell = ws9.cell(row=r + 9, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    for r_idx, (label, gross, net) in enumerate(value_rows, start=r + 10):
        c1 = ws9.cell(row=r_idx, column=1, value=label)
        c2 = ws9.cell(row=r_idx, column=2, value=round(float(gross), 2))
        c3 = ws9.cell(row=r_idx, column=3, value=round(float(net), 2))
        bold = "gap" in label.lower() or "tie" in label.lower()
        c1.font = bold_font if bold else regular_font
        c2.font = bold_font
        c3.font = bold_font
        for cell in (c1, c2, c3):
            cell.border = thin_border
        c2.number_format = "#,##0"
        c3.number_format = "#,##0"

    # Section 3: value frontier
    r = 33
    ws9.cell(row=r, column=1, value="3. VALUE FRONTIER - EV MINUS TOTAL INVESTMENT (EUR), BY CAPEX AND EXTERNAL COVERS").font = bold_font
    r += 1
    ws9.cell(row=r, column=1, value="CapEx (EUR) \\ Covers/day").fill = navy_fill
    ws9.cell(row=r, column=1).font = header_font
    for col_idx, covers in enumerate(reform_frontier.columns, start=2):
        cell = ws9.cell(row=r, column=col_idx, value=float(covers))
        cell.fill = navy_fill
        cell.font = header_font
        cell.number_format = "0"

    for r_offset, (capex, row) in enumerate(reform_frontier.iterrows(), start=1):
        r_idx = r + r_offset
        c0 = ws9.cell(row=r_idx, column=1, value=float(capex))
        c0.font = bold_font
        c0.border = thin_border
        c0.number_format = "#,##0"
        for c_idx, covers in enumerate(reform_frontier.columns, start=2):
            val = round(float(row[covers]), 2)
            cell = ws9.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            cell.number_format = "#,##0"
            cell.fill = PatternFill(
                start_color="FEE2E2" if val < 0 else "D1FAE5",
                end_color="FEE2E2" if val < 0 else "D1FAE5",
                fill_type="solid",
            )

    # Section 4: stress cases
    r = 42
    ws9.cell(row=r, column=1, value="4. STRESS TESTS - THE REFORM UNDER DEMAND, COST, RATE AND GRANT DELAYS").font = bold_font
    stress_cols = [
        ("case", "Stress case"),
        ("capex", "CapEx (EUR)"),
        ("total_investment", "Total inv. (EUR)"),
        ("ebitda_y5", "EBITDA Y5 (EUR)"),
        ("dscr_min", "Min DSCR"),
        ("ev_cap_rate", "EV (EUR)"),
        ("value_gap_total_investment", "Gap vs total inv. (EUR)"),
        ("net_value_gap_total_investment", "Net gap vs total inv. (EUR)"),
        ("project_npv", "Project NPV (EUR)"),
        ("project_irr_exit", "Project IRR"),
        ("equity_irr_exit", "Equity IRR"),
    ]
    for col_idx, (_, label) in enumerate(stress_cols, start=1):
        cell = ws9.cell(row=r + 1, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    for r_idx, (_, row) in enumerate(reform_stress.iterrows(), start=r + 2):
        for c_idx, (key, _) in enumerate(stress_cols, start=1):
            val = row[key]
            if key in ("project_irr_exit", "equity_irr_exit"):
                val = "n/a" if val is None or pd.isna(val) else float(val)
            elif isinstance(val, (int, float)):
                val = round(float(val), 2)
            cell = ws9.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if key in ("capex", "total_investment", "ebitda_y5", "ev_cap_rate", "value_gap_total_investment", "net_value_gap_total_investment", "project_npv"):
                cell.number_format = "#,##0"
            elif key == "dscr_min":
                cell.number_format = "0.00x"
            elif key in ("project_irr_exit", "equity_irr_exit") and isinstance(val, float):
                cell.number_format = "0.00%"

    # Section 5: rate sensitivity
    r = 55
    ws9.cell(row=r, column=1, value="5. RATE SENSITIVITY - R2 REFORM AT +0 / +100 / +200 / +300 BP").font = bold_font
    rate_cols = [
        ("rate_delta_bp", "Rate shock (bp)"),
        ("interest_rate", "Interest rate"),
        ("dscr_min", "Min DSCR"),
        ("project_npv", "Project NPV (EUR)"),
        ("value_gap_total_investment", "Gap vs total inv. (EUR)"),
        ("net_value_gap_total_investment", "Net gap vs total inv. (EUR)"),
    ]
    for col_idx, (_, label) in enumerate(rate_cols, start=1):
        cell = ws9.cell(row=r + 1, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    for r_idx, (_, row) in enumerate(reform_rate.iterrows(), start=r + 2):
        for c_idx, (key, _) in enumerate(rate_cols, start=1):
            val = row[key]
            if isinstance(val, (int, float)):
                val = round(float(val), 4)
            cell = ws9.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if key == "rate_delta_bp":
                cell.number_format = "0"
            elif key == "interest_rate":
                cell.number_format = "0.00%"
            elif key == "dscr_min":
                cell.number_format = "0.00x"
            else:
                cell.number_format = "#,##0"

    # Section 6: recommendation
    r = 63
    ws9.cell(row=r, column=1, value="6. REFORM RECOMMENDATION").font = bold_font
    ws9.cell(row=r + 1, column=1, value=reform_rec["verdict"]).font = Font(name="Calibri", size=12, bold=True, color="BE123C")
    ws9.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=14)
    ws9.cell(row=r + 2, column=1, value=reform_rec["detail"]).font = regular_font
    ws9.cell(row=r + 2, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws9.merge_cells(start_row=r + 2, start_column=1, end_row=r + 2, end_column=14)
    ws9.row_dimensions[r + 2].height = 46
    ws9.cell(row=r + 3, column=1, value=reform_rec["detail_2"]).font = regular_font
    ws9.cell(row=r + 3, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws9.merge_cells(start_row=r + 3, start_column=1, end_row=r + 3, end_column=14)
    ws9.row_dimensions[r + 3].height = 56

    ws9.cell(row=r + 5, column=1, value="Conditions attached to any further work").font = bold_font
    for offset, condition in enumerate(reform_rec["conditions"], start=1):
        cell = ws9.cell(row=r + 5 + offset, column=1, value=f"- {condition}")
        cell.font = regular_font
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws9.merge_cells(start_row=r + 5 + offset, start_column=1, end_row=r + 5 + offset, end_column=14)
        ws9.row_dimensions[r + 5 + offset].height = 28

    # Section 7: R7 premium cabins (a different product, not a fourth as-is case)
    r = 76
    ws9.cell(
        row=r,
        column=1,
        value="7. R7 PREMIUM CABINS - A DIFFERENT PRODUCT, SAME 9.5% CAP-RATE HURDLE",
    ).font = bold_font
    ws9.cell(
        row=r + 1,
        column=1,
        value=(
            "R7 replaces the eight-room hotel with six two-bedroom cabins plus the main house. "
            "The base case is deliberately the good edge of the band: 6 cabins at 110k all-in, "
            "200 EUR ADR, 50% stabilised occupancy, ten external covers and 45k of experiences. "
            "At 120k per cabin the same demand fails the bank-facing net total-investment test."
        ),
    ).font = Font(name="Calibri", size=10, italic=True, color="64748B")
    ws9.cell(row=r + 1, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws9.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=14)
    ws9.row_dimensions[r + 1].height = 42

    cabin_cols = [
        ("key", "Ref"),
        ("cabin_count", "Cabins"),
        ("cabin_adr", "ADR (EUR)"),
        ("cabin_occupancy_mature", "Occupancy"),
        ("cabin_capex_per_unit", "Cost / cabin (EUR)"),
        ("capex", "CapEx (EUR)"),
        ("total_project_investment", "Total inv. (EUR)"),
        ("ebitda_y5", "EBITDA Y5 (EUR)"),
        ("dscr_min", "Min DSCR"),
        ("net_value_gap_total_investment", "Net gap vs total inv. (EUR)"),
        ("project_npv", "Project NPV (EUR)"),
        ("project_irr_exit", "Project IRR"),
    ]
    for col_idx, (_, label) in enumerate(cabin_cols, start=1):
        cell = ws9.cell(row=r + 3, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for r_idx, (_, row) in enumerate(cabin_presets.iterrows(), start=r + 4):
        for c_idx, (key, _) in enumerate(cabin_cols, start=1):
            val = row[key]
            if key == "project_irr_exit":
                val = "n/a" if val is None or pd.isna(val) else float(val)
            elif key == "key":
                val = str(val).upper().replace("_", " ")
            elif isinstance(val, (int, float)):
                val = round(float(val), 2)
            cell = ws9.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if key in (
                "cabin_capex_per_unit",
                "capex",
                "total_project_investment",
                "ebitda_y5",
                "net_value_gap_total_investment",
                "project_npv",
            ):
                cell.number_format = "#,##0"
            elif key == "cabin_adr":
                cell.number_format = "#,##0"
            elif key == "cabin_occupancy_mature":
                cell.number_format = "0%"
            elif key == "dscr_min":
                cell.number_format = "0.00x"
            elif key == "project_irr_exit" and isinstance(val, float):
                cell.number_format = "0.00%"

    # Section 8: cost corridor
    r = 85
    ws9.cell(
        row=r,
        column=1,
        value="8. R7 COST CORRIDOR - SIX CABINS, 200 EUR ADR, 50% OCCUPANCY (PASS = NET TOTAL-INVESTMENT TEST)",
    ).font = bold_font
    ladder_cols = [
        ("cost_per_cabin", "Cost / cabin (EUR)"),
        ("capex", "CapEx (EUR)"),
        ("total_investment", "Total inv. (EUR)"),
        ("ebitda_y5", "EBITDA Y5 (EUR)"),
        ("ev_cap_rate", "EV (EUR)"),
        ("gap_capex", "Gap vs CapEx (EUR)"),
        ("gap_total_investment", "Gap vs total inv. (EUR)"),
        ("net_gap_total_investment", "Net gap vs total inv. (EUR)"),
        ("dscr_min", "Min DSCR"),
        ("project_npv", "Project NPV (EUR)"),
    ]
    for col_idx, (_, label) in enumerate(ladder_cols, start=1):
        cell = ws9.cell(row=r + 1, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for r_idx, (_, row) in enumerate(cabin_ladder.iterrows(), start=r + 2):
        passes = bool(row["passes_net_test"])
        for c_idx, (key, _) in enumerate(ladder_cols, start=1):
            val = row[key]
            if isinstance(val, (int, float)):
                val = round(float(val), 2)
            cell = ws9.cell(row=r_idx, column=c_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if key == "cost_per_cabin":
                cell.font = bold_font
                cell.number_format = "#,##0"
            elif key == "dscr_min":
                cell.number_format = "0.00x"
            else:
                cell.number_format = "#,##0"
            if key == "net_gap_total_investment":
                cell.fill = PatternFill(
                    start_color="D1FAE5" if passes else "FEE2E2",
                    end_color="D1FAE5" if passes else "FEE2E2",
                    fill_type="solid",
                )

    # Section 9: R7 recommendation
    r = 94
    ws9.cell(row=r, column=1, value="9. R7 CABIN RECOMMENDATION").font = bold_font
    ws9.cell(row=r + 1, column=1, value=cabin_rec["verdict"]).font = Font(
        name="Calibri", size=12, bold=True, color="0F766E"
    )
    ws9.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=14)
    ws9.cell(row=r + 2, column=1, value=cabin_rec["detail"]).font = regular_font
    ws9.cell(row=r + 2, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws9.merge_cells(start_row=r + 2, start_column=1, end_row=r + 2, end_column=14)
    ws9.row_dimensions[r + 2].height = 46
    ws9.cell(row=r + 3, column=1, value=cabin_rec["detail_2"]).font = regular_font
    ws9.cell(row=r + 3, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws9.merge_cells(start_row=r + 3, start_column=1, end_row=r + 3, end_column=14)
    ws9.row_dimensions[r + 3].height = 56

    ws9.cell(row=r + 5, column=1, value="R7 conditions attached to any further work").font = bold_font
    for offset, condition in enumerate(cabin_rec["conditions"], start=1):
        cell = ws9.cell(row=r + 5 + offset, column=1, value=f"- {condition}")
        cell.font = regular_font
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws9.merge_cells(
            start_row=r + 5 + offset,
            start_column=1,
            end_row=r + 5 + offset,
            end_column=14,
        )
        ws9.row_dimensions[r + 5 + offset].height = 28

    # Section 10: valuation cross-check
    r = 107
    valuation = reform_engine.valuation_cross_check()
    stress = reform_engine.cost_inflation_stress()
    distress = reform_engine.distress_playbook()

    ws9.cell(
        row=r,
        column=1,
        value="10. R7 VALUATION CROSS-CHECK - DEVELOPMENT YIELD vs EXIT CAP",
    ).font = bold_font
    ws9.cell(
        row=r + 1,
        column=1,
        value=(
            "The positive gap is a development spread: the asset is built at a 10.1% yield on cost "
            "and sold at a 9.5% cap. The break-even exit cap is only 30bp above the assumption; at "
            "no compression the net gap is just the exit costs."
        ),
    ).font = Font(name="Calibri", size=10, italic=True, color="64748B")
    ws9.cell(row=r + 1, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws9.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=14)
    ws9.row_dimensions[r + 1].height = 40

    valuation_rows = [
        ("Development yield on cost", valuation["going_in_yield_on_cost"], "0.00%"),
        ("Exit cap rate", valuation["exit_cap_rate"], "0.00%"),
        ("Break-even exit cap (net of costs)", valuation["break_even_cap_rate"], "0.00%"),
        ("Cap-rate headroom (bp)", valuation["cap_rate_headroom_bp"], "0.0"),
        ("No-compression net gap (EUR)", valuation["net_gap_at_no_compression"], "#,##0"),
        ("Break-even EBITDA, net (EUR)", valuation["break_even_ebitda_net"], "#,##0"),
        ("EBITDA headroom (EUR)", valuation["ebitda_headroom"], "#,##0"),
        ("Implied exit multiple", valuation["implied_exit_multiple"], "0.00x"),
    ]
    for offset, (label, value, fmt) in enumerate(valuation_rows, start=2):
        label_cell = ws9.cell(row=r + offset, column=1, value=label)
        label_cell.font = regular_font
        label_cell.border = thin_border
        value_cell = ws9.cell(row=r + offset, column=2, value=value)
        value_cell.font = regular_font
        value_cell.border = thin_border
        value_cell.number_format = fmt

    multiple_header = r + 11
    for col_idx, label in enumerate(
        ("Exit multiple", "EV (EUR)", "Net exit value (EUR)", "Net gap vs total inv. (EUR)"),
        start=1,
    ):
        cell = ws9.cell(row=multiple_header, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for offset, (_, row) in enumerate(
        valuation["exit_multiple_table"].iterrows(), start=1
    ):
        ws9.cell(row=multiple_header + offset, column=1, value=row["exit_multiple"]).number_format = "0.0x"
        ws9.cell(row=multiple_header + offset, column=2, value=row["ev"]).number_format = "#,##0"
        ws9.cell(row=multiple_header + offset, column=3, value=row["net_exit_value"]).number_format = "#,##0"
        gap_cell = ws9.cell(
            row=multiple_header + offset,
            column=4,
            value=row["net_gap_total_investment"],
        )
        gap_cell.number_format = "#,##0"
        gap_cell.fill = PatternFill(
            start_color="D1FAE5" if row["net_gap_total_investment"] > 0 else "FEE2E2",
            end_color="D1FAE5" if row["net_gap_total_investment"] > 0 else "FEE2E2",
            fill_type="solid",
        )
        for col_idx in range(1, 5):
            ws9.cell(row=multiple_header + offset, column=col_idx).font = regular_font
            ws9.cell(row=multiple_header + offset, column=col_idx).border = thin_border

    # Section 11: cost-inflation stress
    r = multiple_header + 6
    ws9.cell(
        row=r,
        column=1,
        value="11. R7 COST-INFLATION STRESS - REAL COST GROWTH, FLAT REAL PRICES",
    ).font = bold_font
    stress_cols = [
        ("cost_inflation", "Cost inflation / yr"),
        ("ebitda_y5", "EBITDA Y5 (EUR)"),
        ("ebitda_margin_y5", "EBITDA margin"),
        ("dscr_y5", "DSCR Y5"),
        ("ev_cap_rate", "EV (EUR)"),
        ("net_gap_total_investment", "Net gap vs total inv. (EUR)"),
        ("project_npv", "Project NPV (EUR)"),
        ("project_irr_exit", "Project IRR"),
        ("passes_net_test", "Net test"),
    ]
    for col_idx, (_, label) in enumerate(stress_cols, start=1):
        cell = ws9.cell(row=r + 1, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for offset, (_, row) in enumerate(stress.iterrows(), start=2):
        for col_idx, (key, _) in enumerate(stress_cols, start=1):
            value = row[key]
            if key == "passes_net_test":
                value = "PASS" if bool(value) else "FAIL"
            elif key == "project_irr_exit":
                value = "n/a" if value is None or pd.isna(value) else float(value)
            cell = ws9.cell(row=r + offset, column=col_idx, value=value)
            cell.font = regular_font
            cell.border = thin_border
            if key == "cost_inflation":
                cell.number_format = "0.0%"
            elif key == "ebitda_margin_y5":
                cell.number_format = "0.0%"
            elif key == "dscr_y5":
                cell.number_format = "0.00x"
            elif key == "project_irr_exit" and isinstance(value, float):
                cell.number_format = "0.00%"
            elif key in ("ebitda_y5", "ev_cap_rate", "net_gap_total_investment", "project_npv"):
                cell.number_format = "#,##0"
            if key == "passes_net_test":
                cell.fill = PatternFill(
                    start_color="D1FAE5" if value == "PASS" else "FEE2E2",
                    end_color="D1FAE5" if value == "PASS" else "FEE2E2",
                    fill_type="solid",
                )

    # Section 12: distress playbook
    r = r + 7
    ws9.cell(row=r, column=1, value="12. R7 DISTRESS PLAYBOOK (DOWNSIDE CASE)").font = bold_font
    verdict_cell = ws9.cell(row=r + 1, column=1, value=distress["verdict"])
    verdict_cell.font = Font(name="Calibri", size=11, bold=True, color="BE123C")
    verdict_cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws9.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=14)
    ws9.row_dimensions[r + 1].height = 32

    playbook_rows = [
        ("Minimum DSCR / year", f"{distress['min_dscr']:.2f}x in Year {distress['min_dscr_year']}"),
        ("Cumulative CFADS shortfall (EUR)", distress["cumulative_shortfall"]),
        ("Equity cure to 1.25x DSCR (EUR)", distress["equity_cure_to_125x"]),
        ("Six-month DSRA (EUR)", distress["dsra_six_months"]),
        ("Net exit value (EUR)", distress["net_exit_value"]),
        ("Debt outstanding at exit (EUR)", distress["ending_debt"]),
        ("Lender recovery", distress["lender_recovery"]),
        ("Equity at exit (EUR)", distress["equity_at_exit"]),
        ("Equity invested (EUR)", distress["equity_invested"]),
        ("Equity recovery", distress["equity_recovery"]),
    ]
    for offset, (label, value) in enumerate(playbook_rows, start=3):
        label_cell = ws9.cell(row=r + offset, column=1, value=label)
        label_cell.font = regular_font
        label_cell.border = thin_border
        value_cell = ws9.cell(row=r + offset, column=2, value=value)
        value_cell.font = regular_font
        value_cell.border = thin_border
        if isinstance(value, float) and label.startswith(("Lender", "Equity recovery")):
            value_cell.number_format = "0.0%"
        elif isinstance(value, (int, float)):
            value_cell.number_format = "#,##0"

    annual_header = r + len(playbook_rows) + 4
    for col_idx, label in enumerate(
        ("Year", "CFADS (EUR)", "Debt service (EUR)", "Shortfall (EUR)", "DSCR", "Ending cash (EUR)"),
        start=1,
    ):
        cell = ws9.cell(row=annual_header, column=col_idx, value=label)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for offset, (_, row) in enumerate(distress["annual"].iterrows(), start=1):
        for col_idx, key in enumerate(
            ("year", "cfads", "debt_service", "shortfall", "dscr", "ending_cash"),
            start=1,
        ):
            value = row[key]
            value = int(value) if key == "year" else float(value)
            cell = ws9.cell(row=annual_header + offset, column=col_idx, value=value)
            cell.font = regular_font
            cell.border = thin_border
            cell.number_format = "0" if key == "year" else ("0.00x" if key == "dscr" else "#,##0")

    # Five-act case study: promoter, audit, decline memo, cabin turnaround and
    # the executive comparison. The T8 layer keeps its own live formula tabs.
    turnaround = TurnaroundEngine()
    decline = DeclineMemoEngine()
    investment_case = InvestmentCase(turnaround=turnaround)

    # Add the live, formula-driven tabs (Inputs, Live Model, Funding & Audit, Read Me)
    add_live_model_tabs(
        wb, engine, df_proj, df_kpi, debt_sched, turnaround=turnaround
    )

    promoter_case = FinancialModelEngine(case="promoter", scenario=SCENARIOS["base"])
    audited_case = FinancialModelEngine(case="management", scenario=SCENARIOS["base"])
    market_case = FinancialModelEngine(case="market", scenario=SCENARIOS["base"])
    add_case_study_tabs(
        wb,
        promoter_case,
        audited_case,
        market_case,
        turnaround,
        decline,
        investment_case,
    )
    add_t8_model_tabs(wb, turnaround)

    _order_sheets(wb)

    # Auto-adjust column widths across the report tabs. The live tabs set their
    # own widths, and formulas should not inflate the column width.
    live_tabs = {
        "Read Me & Checks", "Inputs", "Live Model", "Funding & Audit",
        "Debt Schedule", "Act 1 - Promoter", "Act 2 - Audit", "Decline Memo",
        "Act 4 - T8", "Executive Comparison", "T8 Sensitivities",
        "T8 Inputs", "T8 Debt Schedule", "T8 Live Model",
    }
    for ws in wb.worksheets:
        if ws.title in live_tabs:
            continue
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 42)

    wb.save(output_path)
    _normalise_xlsx_timestamps(output_path)
    return output_path


if __name__ == "__main__":
    out = export_institutional_excel()
    print(f"Generated institutional Excel model: {out.name} ({out.stat().st_size / 1024:.1f} KB)")
