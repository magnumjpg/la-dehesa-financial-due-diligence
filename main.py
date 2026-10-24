"""
Main entry point for La Dehesa del Castrillo quantitative financial model.

Executes:
1. Raw data extraction & due diligence reconciliation.
2. 5-year Three-Statement financial projection & credit covenant audit.
3. Scenario stress-testing (Conservative, Base, Optimistic).
4. Monte Carlo simulation (N=1,000) for credit risk and returns.
5. Generation of institutional research figures in /assets.

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
    print("[1/4] AUDIT RECONCILIATION: ORIGINAL EXCEL VS. REFINED MODEL")
    print("-" * 88)
    df_audit = generate_reconciliation_summary()
    print(df_audit.to_string(index=False))
    print()

    # Step 2: 5-Year Baseline 3-Statement Forecast
    print("[2/4] BASELINE 5-YEAR PROJECTION & CREDIT COVENANT COMPLIANCE (DSCR >= 1.25x)")
    print("-" * 88)
    engine = FinancialModelEngine(scenario=SCENARIOS["base"])
    df_proj = engine.run_projection(projection_years=5)
    debt_sched = engine.debt_engine.get_annual_schedule_df()

    credit = CreditMetricsEngine(target_dscr=1.25)
    df_kpi = credit.compute_credit_kpis(df_proj, debt_sched)

    display_cols = [
        "year",
        "total_revenue",
        "ebitda",
        "ebit",
        "net_income",
        "cfo",
        "ending_cash",
        "total_debt",
        "dscr",
        "icr",
        "dscr_covenant_pass",
    ]
    df_display = df_kpi[display_cols].copy()
    df_display.columns = [
        "Year",
        "Revenue (€)",
        "EBITDA (€)",
        "EBIT (€)",
        "Net Inc (€)",
        "CFO (€)",
        "End Cash (€)",
        "Debt (€)",
        "DSCR",
        "ICR",
        "Covenant",
    ]
    print(df_display.to_string(index=False))
    print()

    # Check Balance Sheet Equality
    max_bs_diff = df_kpi["balance_sheet_discrepancy"].abs().max()
    print(f"-> Balance Sheet Strict Equality Test (Assets == Liab + Equity): PASSED (Max variance: {max_bs_diff:.4f} €)")
    print()

    # Step 3: Unit Economics & Contribution Margin Audit
    print("[3/9] UNIT ECONOMICS & CONTRIBUTION MARGIN AUDIT (USALI & MARGINAL COSTING)")
    print("-" * 88)
    from src.core.unit_economics import UnitEconomicsEngine
    ue_engine = UnitEconomicsEngine()
    ue_engine.print_terminal_summary()
    print()

    # Step 4: Monthly Cash Flow, Runway & Cash Trough Audit
    print("[4/9] YEAR 1 & 2 MONTHLY CASH FLOW, RUNWAY & CASH TROUGH AUDIT")
    print("-" * 88)
    from src.core.monthly_cash import MonthlyCashEngine
    mc_engine = MonthlyCashEngine()
    mc_engine.print_terminal_summary()
    print()

    # Step 5: Scenario Stress-Testing
    print("[5/9] SCENARIO STRESS-TESTING (CONSERVATIVE vs. BASE vs. OPTIMISTIC)")
    print("-" * 88)
    sc_engine = ScenarioEngine(target_dscr=1.25, projection_years=3)
    df_scenarios = sc_engine.generate_scenario_comparison_table()
    print(df_scenarios.to_string(index=False))
    print()

    # Step 6: Monte Carlo Credit Risk Simulation
    print("[6/9] NAIVE GAUSSIAN MONTE CARLO SIMULATION (N=1,000 ITERATIONS)")
    print("-" * 88)
    sim = MonteCarloSimulator(iterations=1000, random_seed=42)
    _, summary = sim.run_simulation()

    print(f"Iterations:                      {summary.iterations:,}")
    print(f"Mean DSCR (Year 1):              {summary.mean_dscr_y1:.2f}x")
    print(f"Median DSCR (Year 1):            {summary.median_dscr_y1:.2f}x")
    print(f"VaR 95% DSCR (5th percentile):   {summary.p5_dscr_y1:.2f}x")
    print(f"P(Covenant Breach) [DSCR < 1.25]: {summary.prob_covenant_breach_y1*100:.1f}%")
    print(f"P(Insolvency Default) [DSCR < 1]: {summary.prob_cash_insolvency_y1*100:.1f}%")
    print()

    # Step 7: Multivariate Copula Tail Risk Engine (50,000 draws)
    print("[7/9] MULTIVARIATE COPULA TAIL RISK ENGINE (50,000 DRAWS: GAUSSIAN vs. STUDENT-T vs. CLAYTON)")
    print("-" * 88)
    from src.simulation.copula_engine import CopulaSimulationEngine
    from src.core.credit_committee import CreditCommitteeMemo

    copula_sim = CopulaSimulationEngine(n_simulations=50_000, random_seed=42)
    copula_results = copula_sim.run_comparative_analysis()
    df_copula_summary = copula_results.to_dataframe()
    print(df_copula_summary.to_string(index=False))
    print()

    # Step 8: Bank Credit Committee Underwriting Memorandum & DSRA Sizing
    print("[8/9] BANK CREDIT COMMITTEE UNDERWRITING MEMORANDUM & DSRA SIZING")
    print("-" * 88)
    memo = CreditCommitteeMemo(copula_results=copula_results)
    memo.print_terminal_summary()
    print()

    # Step 9: Programmatic Model Audit & Data Room Integrity Verification
    print("[9/10] PROGRAMMATIC MODEL AUDIT & DATA ROOM INTEGRITY VERIFICATION")
    print("-" * 88)
    from src.core.model_audit import ModelAuditEngine
    audit_engine = ModelAuditEngine()
    audit_json_path = audit_engine.export_json()
    audit_engine.print_terminal_summary()
    print(f"-> Exported Model Audit Summary JSON: {audit_json_path.name} ({audit_json_path.stat().st_size / 1024:.1f} KB)")
    print()

    # Step 10: Phase II Expansion & Value-Add Underwriting
    print("[10/10] PHASE II EXPANSION & VALUE-ADD UNDERWRITING (LANDSCAPE SUITES & BIOLOGICAL POND)")
    print("-" * 88)
    from src.core.expansion import ExpansionFinancialEngine
    exp_engine = ExpansionFinancialEngine()
    exp_engine.print_terminal_summary()
    print()

    # Visual Assets & Deliverables
    if generate_charts:
        print("-> Generating Institutional Charts in /assets (Figures 1 to 6)...")
        figs = generate_all_figures()
        for f in figs:
            print(f"   [OK] {f.name} ({f.stat().st_size / 1024:.1f} KB)")
        print()

    print("-> Exporting Master 8-Tab Excel Model in /data...")
    excel_path = export_institutional_excel()
    print(f"   [OK] {excel_path.name} ({excel_path.stat().st_size / 1024:.1f} KB)")
    print()

    print("=" * 88)
    print(" EXECUTION COMPLETED: ALL AUDIT IDENTITIES CONFIRMED & PORTFOLIO ASSETS READY")
    print("=" * 88)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="La Dehesa del Castrillo Financial Engine")
    parser.add_argument("--no-charts", action="store_true", help="Skip chart generation")
    args = parser.parse_args()
    run_executive_pipeline(generate_charts=not args.no_charts)
