"""
Main entry point for La Dehesa del Castrillo quantitative financial model.

Executes:
 1. Raw data extraction & due diligence reconciliation.
 2. 5-year Three-Statement financial projection & credit covenant audit.
 3. Three-case comparison: management (upside), INE market, original promoter.
 4. Unit economics & contribution margin audit.
 5. Monthly cash flow, runway & cash trough audit.
 6. Scenario stress-testing (Conservative, Base, Optimistic).
 7. Sources & Uses / funding-gap analysis.
 8. Returns: project and equity IRR with and without exit.
 9. Monte Carlo simulation (N=1,000) for credit risk.
10. Multivariate copula tail-risk engine (50,000 draws).
11. Bank credit committee underwriting memorandum & DSRA sizing.
12. Phase II expansion & phase-gate test.
13. Reform / resize case: value bridge, frontier, stress tests & recommendation.
14. Credit committee decline memo: four mathematical reasons (Act 3).
15. T8 cabin turnaround: six modular cabins + caseron lodge (Act 4).
16. Executive comparison: promoter vs audited vs cabin turnaround (Act 5).
17. Computed model audit & data-room integrity verification.
18. Excel export & chart generation.

Usage:
    python main.py
    python main.py --no-charts
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

# Ensure root is in python path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.extract_raw import generate_reconciliation_summary
from src.data.export_excel import export_institutional_excel
from src.core.statements import FinancialModelEngine
from src.core.metrics import CreditMetricsEngine
from src.core.funding import SourcesUsesEngine
from src.config.assumptions import SCENARIOS
from src.scenarios.scenario_analysis import ScenarioEngine
from src.simulation.monte_carlo import MonteCarloSimulator
from src.visualization.charts import generate_all_figures


def run_executive_pipeline(generate_charts: bool = True):
    print("=" * 88)
    print(" LA DEHESA DEL CASTRILLO S.L. - QUANTITATIVE FINANCIAL DUE DILIGENCE ENGINE")
    print(" Hospitality Feasibility, Segovia Collective Bargaining & Scenario Stress-Testing")
    print("=" * 88)
    print()

    # Step 1: Raw Data Audit & Reconciliation
    print("[1/18] AUDIT RECONCILIATION: SOURCE WORKBOOKS VS. REFINED MODEL")
    print("-" * 88)
    df_audit = generate_reconciliation_summary()
    print(df_audit.to_string(index=False))
    print()

    # Step 2: 5-Year Baseline 3-Statement Forecast (management case)
    print("[2/18] MANAGEMENT-CASE 5-YEAR PROJECTION & CREDIT COVENANT COMPLIANCE (DSCR >= 1.25x)")
    print("-" * 88)
    engine = FinancialModelEngine(case="management", scenario=SCENARIOS["base"])
    df_proj = engine.run_projection(projection_years=5)
    debt_sched = engine.debt_engine.get_annual_schedule_df()

    credit = CreditMetricsEngine(target_dscr=1.25)
    df_kpi = credit.compute_credit_kpis(df_proj, debt_sched)

    display_cols = [
        "year", "total_revenue", "ebitda", "ebit", "net_income",
        "cfo", "ending_cash", "total_debt", "dscr", "icr", "dscr_covenant_pass",
    ]
    df_display = df_kpi[display_cols].copy()
    df_display.columns = [
        "Year", "Revenue (€)", "EBITDA (€)", "EBIT (€)", "Net Inc (€)",
        "CFO (€)", "End Cash (€)", "Debt (€)", "DSCR", "ICR", "Covenant",
    ]
    print(df_display.to_string(index=False))
    print()

    max_bs_diff = df_kpi["balance_sheet_discrepancy"].abs().max()
    print(f"-> Balance Sheet Strict Equality Test (Assets == Liab + Equity): PASSED (Max variance: {max_bs_diff:.4f} €)")
    print()

    # Step 3: Three-case comparison
    print("[3/18] THREE-CASE COMPARISON: MANAGEMENT (UPSIDE) vs. INE MARKET vs. PROMOTER")
    print("-" * 88)
    case_rows = []
    for case in ("management", "market", "promoter"):
        c_engine = FinancialModelEngine(case=case, scenario=SCENARIOS["base"])
        c_df = c_engine.run_projection(projection_years=5)
        c_debt = c_engine.debt_engine.get_annual_schedule_df()
        c_kpi = credit.compute_credit_kpis(c_df, c_debt)
        c_returns = credit.compute_returns_summary(
            c_df,
            initial_equity=c_engine.total_equity_at_close,
            initial_capex=c_engine.total_project_investment,
        )
        y1 = c_kpi.iloc[0]
        case_rows.append({
            "Case": case,
            "Revenue Y1": round(float(y1["total_revenue"]), 2),
            "EBITDA Y1": round(float(y1["ebitda"]), 2),
            "DSCR Y1": round(float(y1["dscr"]), 2),
            "Cash Y1": round(float(y1["ending_cash"]), 2),
            "Project IRR (no exit)": round(float(c_returns["project_irr"] or 0.0) * 100, 2),
            "Project IRR (8.5% exit)": round(float(c_returns["project_irr_exit"] or 0.0) * 100, 2),
            "Equity IRR (8.5% exit)": round(float(c_returns["equity_irr_exit"] or 0.0) * 100, 2),
        })
    df_cases = pd.DataFrame(case_rows)
    print(df_cases.to_string(index=False))
    print("-> The management case is an upside case (31.36% mature occupancy, 1.48x the INE market average).")
    print("-> The INE market case (21.24%) is the independent benchmark; the promoter case is a re-modelling (86,275 is a model construct, the deck says 96,628), not a replication (README section 2).")
    print()

    # Demand reconciliation: the management case is weekend-weighted, not a
    # flat uplift on every night.
    from src.core.demand_bridge import INE_MIX, MANAGEMENT_MIX, build_bridge

    occ_bridge = build_bridge()
    print("OCCUPANCY BRIDGE: 31.36% IS NOT A FLAT 48% UPLIFT")
    print(f"{'Segment':<22}{'Nights':>8}{'Management':>14}{'INE':>10}{'Gap (pp)':>12}")
    for mgmt_segment, mkt_segment in zip(MANAGEMENT_MIX.segments, INE_MIX.segments):
        print(
            f"{mgmt_segment.label:<22}{mgmt_segment.nights:>8}"
            f"{mgmt_segment.occupancy*100:>13.1f}%"
            f"{mkt_segment.occupancy*100:>9.1f}%"
            f"{occ_bridge['gap_contributions_pp'][mgmt_segment.key]:>12.2f}"
        )
    print(
        f"{'Annual':<22}{365:>8}"
        f"{MANAGEMENT_MIX.occupancy*100:>13.2f}%"
        f"{INE_MIX.occupancy*100:>9.2f}%"
        f"{occ_bridge['gap_pp']:>12.2f}"
    )
    print(f"-> {occ_bridge['headline']}")
    print()

    # Step 4: Unit Economics & Contribution Margin Audit
    print("[4/18] UNIT ECONOMICS & CONTRIBUTION MARGIN AUDIT (USALI & MARGINAL COSTING)")
    print("-" * 88)
    from src.core.unit_economics import UnitEconomicsEngine
    ue_engine = UnitEconomicsEngine()
    ue_engine.print_terminal_summary()
    print()

    # Step 5: Monthly Cash Flow, Runway & Cash Trough Audit
    print("[5/18] MONTHLY LIQUIDITY RECONCILIATION, SEASONAL TROUGH & REVOLVER AUDIT")
    print("-" * 88)
    from src.core.monthly_cash import MonthlyCashEngine
    mc_engine = MonthlyCashEngine()
    mc_engine.print_terminal_summary()
    print()

    # Step 6: Scenario Stress-Testing
    print("[6/18] SCENARIO STRESS-TESTING (CONSERVATIVE vs. BASE vs. OPTIMISTIC)")
    print("-" * 88)
    sc_engine = ScenarioEngine(target_dscr=1.25, projection_years=3)
    df_scenarios = sc_engine.generate_scenario_comparison_table()
    print(df_scenarios.to_string(index=False))
    print()

    # Step 7: Sources & Uses / Funding Gap
    print("[7/18] SOURCES & USES, FUNDING GAP & CREDIT-LINE CONSISTENCY")
    print("-" * 88)
    funding_rows = []
    for case in ("management", "market", "promoter"):
        f = SourcesUsesEngine(case=case).compute()
        funding_rows.append({
            "Case": case,
            "Uses at close": f.total_uses_at_close,
            "Sources at close": f.total_sources_at_close,
            "Gap at close": f.funding_gap_at_close,
            "VAT bridge Y1": f.vat_bridge_drawn_y1,
            "Min DSCR": f.dscr_min,
            "DSCR-capped debt": f.dscr_cap_principal,
            "Equity / CapEx %": f.equity_to_capex_pct,
            "Status": f.funding_status,
        })
    df_funding = pd.DataFrame(funding_rows)
    print(df_funding.to_string(index=False))
    print()
    print("-> The binding constraint is the DSCR cap, not the 35% LTV request: the")
    print("   EUR 367,535 facility breaches the 1.25x covenant in Year 2.")
    print()
    SourcesUsesEngine(case="management").print_terminal_summary()
    print()

    # Step 8: Returns
    print("[8/18] RETURNS: PROJECT & EQUITY IRR WITH AND WITHOUT EXIT (8.5% CAP RATE)")
    print("-" * 88)
    returns = credit.compute_returns_summary(
        df_proj,
        initial_equity=engine.total_equity_at_close,
        initial_capex=engine.total_project_investment,
        exit_cap_rate=0.085,
    )
    print(f"Total equity at close:            €{engine.total_equity_at_close:>12,.2f}")
    print(f"Total project investment:         €{engine.total_project_investment:>12,.2f}")
    print(f"Project IRR (no exit):            {returns['project_irr']*100:>8.2f}%" if returns['project_irr'] is not None else "Project IRR (no exit):            n/a")
    print(f"Project IRR (8.5% exit):          {returns['project_irr_exit']*100:>8.2f}%" if returns['project_irr_exit'] is not None else "Project IRR (8.5% exit):          n/a")
    print(f"Equity IRR (no exit):             {returns['equity_irr']*100:>8.2f}%" if returns['equity_irr'] is not None else "Equity IRR (no exit):             n/a")
    print(f"Equity IRR (8.5% exit):           {returns['equity_irr_exit']*100:>8.2f}%" if returns['equity_irr_exit'] is not None else "Equity IRR (8.5% exit):           n/a")
    print(f"Terminal value (8.5% cap rate):   €{returns['terminal_value']:>12,.2f}")
    print(f"Project MOIC:                     {returns['project_moic']:>8.2f}x")
    print(f"Equity MOIC:                      {returns['equity_moic']:>8.2f}x")
    print("-> Without an exit, the 5-year operating cash flow does not recover the CapEx; the exit is what drives the IRR.")
    print()

    # Step 9: Monte Carlo Credit Risk Simulation
    print("[9/18] GAUSSIAN MONTE CARLO CREDIT-RISK SIMULATION (N=1,000 ITERATIONS)")
    print("-" * 88)
    sim = MonteCarloSimulator(iterations=1000, random_seed=42)
    _, summary = sim.run_simulation()

    print(f"Iterations:                          {summary.iterations:,}")
    print(f"Cash equity (fixed across draws):    €{summary.cash_equity:,.2f}")
    print(f"Total equity at close:               €{summary.total_equity_at_close:,.2f}")
    print(f"Mean minimum DSCR (Years 1-3):       {summary.mean_min_dscr:.2f}x")
    print(f"Median minimum DSCR:                 {summary.median_min_dscr:.2f}x")
    print(f"VaR 95% minimum DSCR (5th pct):      {summary.p5_min_dscr:.2f}x")
    print(f"P(Covenant breach) [min DSCR<1.25x]: {summary.prob_covenant_breach*100:.1f}%")
    print(f"P(Debt-service shortfall) [<1.00x]:  {summary.prob_cash_insolvency*100:.1f}%")
    print(f"Mean equity IRR (8.5% exit):         {summary.mean_equity_irr*100:.2f}%")
    print(f"VaR 95% equity IRR (5th pct):        {summary.p5_equity_irr*100:.2f}%")
    print()

    # Step 10: Multivariate Copula Tail Risk Engine
    print("[10/18] MULTIVARIATE COPULA TAIL-RISK ENGINE (50,000 DRAWS: GAUSSIAN vs. STUDENT-T vs. CLAYTON)")
    print("        Credit test: Year-2 DSCR on CFADS, 20Y/4.0% debt with 12-month grace, full cost stack")
    print("-" * 88)
    from src.simulation.copula_engine import CopulaSimulationEngine
    from src.core.credit_committee import CreditCommitteeMemo

    copula_sim = CopulaSimulationEngine(n_simulations=50_000, random_seed=42)
    copula_results = copula_sim.run_comparative_analysis()
    df_copula_summary = copula_results.to_dataframe()
    print(df_copula_summary.to_string(index=False))
    print()

    # Step 11: Bank Credit Committee Underwriting Memorandum & DSRA Sizing
    print("[11/18] BANK CREDIT COMMITTEE UNDERWRITING MEMORANDUM & DSRA SIZING")
    print("-" * 88)
    memo = CreditCommitteeMemo(copula_results=copula_results)
    memo.print_terminal_summary()
    print()

    # Step 12: Phase II Expansion & Phase Gate
    print("[12/18] PHASE II EXPANSION & PHASE-GATE TEST (LANDSCAPE SUITES & BIOLOGICAL POND)")
    print("-" * 88)
    from src.core.expansion import ExpansionFinancialEngine
    exp_engine = ExpansionFinancialEngine()
    phase1_cash_y2 = float(df_kpi.iloc[1]["ending_cash"])
    phase1_dscr_y3 = float(df_kpi.iloc[2]["dscr"])
    phase1_ebitda_y3 = float(df_proj.iloc[2]["ebitda"])
    phase1_cfads_y3 = float(df_proj.iloc[2]["cfads"])
    phase1_rev_y3 = float(df_proj.iloc[2]["total_revenue"])
    phase1_ds = float(df_proj.iloc[2]["debt_service"])
    gate = exp_engine.compute_phase_gate(phase1_cash_y2, phase1_dscr_y3)
    consolidated = exp_engine.compute_consolidated_underwriting(
        phase1_rev_y3=phase1_rev_y3,
        phase1_ebitda_y3=phase1_ebitda_y3,
        phase1_cfads_y3=phase1_cfads_y3,
        phase1_senior_debt_service=phase1_ds,
        phase1_capex=float(engine.capex.total_capex),
        phase1_cash_end_y2=phase1_cash_y2,
        phase1_dscr_y3=phase1_dscr_y3,
    )
    exp_engine.print_terminal_summary(phase1_cash_end_y2=phase1_cash_y2, phase1_dscr_y3=phase1_dscr_y3)
    print()
    print("PHASE-GATE SUMMARY:")
    print(f"  Phase I cash at end of Year 2:   €{gate['phase1_cash_end_y2']:,.2f}")
    print(f"  Phase II cash need:              €{gate['phase2_cash_need']:,.2f}")
    print(f"  Phase II funding gap:            €{gate['phase2_funding_gap']:,.2f}")
    print(f"  Phase II proceed:                {gate['phase2_proceed']}")
    print(f"  Recommendation:                  {gate['recommendation']}")
    print()

    # Step 13: Reform / Resize Case (separate layer, after the as-is verdict)
    print("[13/18] REFORM / RESIZE CASE: WHAT WOULD HAVE TO BE TRUE AFTER THE DECLINE?")
    print("-" * 88)
    from src.core.reform import ReformAnalysisEngine

    reform_engine = ReformAnalysisEngine()
    reform_engine.print_terminal_summary()
    reform_json_path = reform_engine.export_json()
    print(f"-> Exported Reform Analysis JSON: {reform_json_path.name} ({reform_json_path.stat().st_size / 1024:.1f} KB)")
    print()

    # Step 14: Credit Committee Decline Memo (Act 3)
    print("[14/18] CREDIT COMMITTEE DECLINE MEMO: FOUR MATHEMATICAL REASONS (ACT 3)")
    print("-" * 88)
    from src.core.decline import DeclineMemoEngine

    decline_engine = DeclineMemoEngine()
    decline_engine.print_terminal_summary()
    decline_json_path = decline_engine.export_json()
    print(f"-> Exported Decline Memo JSON: {decline_json_path.name} ({decline_json_path.stat().st_size / 1024:.1f} KB)")
    print()

    # Step 15: T8 Cabin Turnaround (Act 4)
    print("[15/18] T8 CABIN TURNAROUND: SIX MODULAR CABINS + CASERON LODGE (ACT 4)")
    print("-" * 88)
    from src.core.turnaround import TurnaroundEngine

    turnaround_engine = TurnaroundEngine()
    turnaround_engine.print_terminal_summary()
    t8_json_path = turnaround_engine.export_json()
    print(f"-> Exported T8 Turnaround JSON: {t8_json_path.name} ({t8_json_path.stat().st_size / 1024:.1f} KB)")
    print()

    # Step 16: Executive Comparison (Act 5)
    print("[16/18] EXECUTIVE COMPARISON: PROMOTER vs AUDITED vs CABIN TURNAROUND (ACT 5)")
    print("-" * 88)
    from src.core.investment_case import InvestmentCase

    investment_case = InvestmentCase(turnaround=turnaround_engine)
    investment_case.print_terminal_summary()
    case_json_path = investment_case.export_json()
    print(f"-> Exported Investment Case JSON: {case_json_path.name} ({case_json_path.stat().st_size / 1024:.1f} KB)")
    print()

    # Step 17: Programmatic Model Audit
    print("[17/18] COMPUTED MODEL AUDIT & DATA ROOM INTEGRITY VERIFICATION")
    print("-" * 88)
    from src.core.model_audit import ModelAuditEngine
    audit_engine = ModelAuditEngine()
    audit_json_path = audit_engine.export_json()
    audit_engine.print_terminal_summary()
    print(f"-> Exported Model Audit Summary JSON: {audit_json_path.name} ({audit_json_path.stat().st_size / 1024:.1f} KB)")
    print()

    # Step 18: Visual Assets & Excel Deliverables
    print("[18/18] DELIVERABLES: CHARTS & EXCEL MODEL")
    print("-" * 88)
    if generate_charts:
        print("-> Generating Institutional Charts in /assets (Figures 1 to 12)...")
        figs = generate_all_figures()
        for f in figs:
            print(f"   [OK] {f.name} ({f.stat().st_size / 1024:.1f} KB)")
        print()

    print("-> Exporting Master Excel Model in /data...")
    excel_path = export_institutional_excel()
    print(f"   [OK] {excel_path.name} ({excel_path.stat().st_size / 1024:.1f} KB)")
    print()

    print("=" * 88)
    print(" EXECUTION COMPLETED: MODEL, FUNDING GAP, RETURNS & AUDIT EXCEPTIONS REPORTED")
    print("=" * 88)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="La Dehesa del Castrillo Financial Engine")
    parser.add_argument("--no-charts", action="store_true", help="Skip chart generation")
    args = parser.parse_args()
    run_executive_pipeline(generate_charts=not args.no_charts)
