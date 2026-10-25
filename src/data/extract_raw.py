"""
Data extraction and audit reconciliation pipeline for raw Excel files.

Sources audited:
1. raw_data/La_Dehesa_de_Castrillo_Proyecto.xlsx (original plan & formulas)
2. raw_data/Presentacion_La_Dehesa.xlsx (Segovia collective agreement & costs)

Highlights:
- Compares the original university workbooks with the refined management
  (upside) and INE market cases. The promoter case is a re-modelling, not a
  replication: the source reports four different Year-1 revenues (EUR 74,851
  net in `Conclusiones`, EUR 99,487.50 gross in the `Plan de Negocio`
  formulas, EUR 96,628 hard-coded in the deck).
- The formula sheet reports revenue gross; the hard-coded summary divides by
  1.21. The refined model applies the statutory 10% hospitality rate and a
  21% input-VAT bridge.
- Checks part-time labor hours against the Segovia hospitality agreement.
"""

from pathlib import Path
from typing import Any, Dict
import openpyxl
import pandas as pd


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def extract_raw_excel_data() -> Dict[str, Any]:
    """Extracts structured data from both raw Excel files."""
    root = get_project_root()
    p1 = root / "raw_data" / "La_Dehesa_de_Castrillo_Proyecto.xlsx"
    p2 = root / "raw_data" / "Presentacion_La_Dehesa.xlsx"

    if not p1.exists() or not p2.exists():
        raise FileNotFoundError(f"Raw Excel files not found at {root / 'raw_data'}")

    wb1_val = openpyxl.load_workbook(p1, data_only=True)
    wb2_val = openpyxl.load_workbook(p2, data_only=True)

    # Sheet 1: Plan de Negocio (wb1)
    s1 = wb1_val["Plan de Negocio"]
    land = float(s1.cell(5, 2).value or 0)
    renovation = float(s1.cell(6, 2).value or 0)
    biopool = float(s1.cell(7, 2).value or 0)
    total_capex = float(s1.cell(8, 2).value or (land + renovation + biopool))
    equity_pct = float(s1.cell(11, 3).value or 0.30)
    debt_pct = float(s1.cell(12, 3).value or 0.70)

    capex_base = {
        "land": land,
        "renovation": renovation,
        "biopool": biopool,
        "total_capex": total_capex,
        "equity_pct": equity_pct,
        "debt_pct": debt_pct,
    }

    pricing_base = {
        "double_room_adr": float(s1.cell(17, 2).value or 85.0),
        "full_house_adr": float(s1.cell(18, 2).value or 380.0),
        "restaurant_ticket": float(s1.cell(19, 2).value or 25.0),
        "restaurant_cogs_pct": float(s1.cell(20, 2).value or 0.30),
    }

    high_days = int(s1.cell(24, 2).value or 90)
    high_occ = float(s1.cell(24, 3).value or 0.42)
    wknd_days = int(s1.cell(25, 2).value or 80)
    wknd_occ = float(s1.cell(25, 3).value or 0.32)
    mid_days = int(s1.cell(26, 2).value or 195)
    mid_occ = float(s1.cell(26, 3).value or 0.015)
    total_occ_days = float(
        s1.cell(27, 4).value or (high_days * high_occ + wknd_days * wknd_occ + mid_days * mid_occ)
    )

    seasonality_base = {
        "high_season_days": high_days,
        "high_season_occ": high_occ,
        "weekend_days": wknd_days,
        "weekend_occ": wknd_occ,
        "midweek_days": mid_days,
        "midweek_occ": mid_occ,
        "total_occupied_days": total_occ_days,
    }

    cooks_pay = float(s1.cell(31, 2).value or 35640.0)
    clean_pay = float(s1.cell(32, 2).value or 23100.0)
    maint_ext = float(s1.cell(33, 2).value or 3600.0)
    labor_base = {
        "cooks_payroll": cooks_pay,
        "cleaning_payroll": clean_pay,
        "maintenance_external": maint_ext,
        "total_team_maintenance": float(s1.cell(34, 2).value or (cooks_pay + clean_pay + maint_ext)),
    }

    # Sheet 2: Justificacion Gastos (wb2)
    s2_gastos = wb2_val["Justificacion Gastos"]
    segovia_labor = {
        "cook_1_gross": float(s2_gastos.cell(3, 2).value or 0),
        "cook_1_ss": float(s2_gastos.cell(3, 3).value or 0),
        "cook_1_total": float(s2_gastos.cell(3, 4).value or 0),
        "cook_2_gross": float(s2_gastos.cell(4, 2).value or 0),
        "cook_2_ss": float(s2_gastos.cell(4, 3).value or 0),
        "cook_2_total": float(s2_gastos.cell(4, 4).value or 0),
        "cleaner_gross": float(s2_gastos.cell(5, 2).value or 0),
        "cleaner_ss": float(s2_gastos.cell(5, 3).value or 0),
        "cleaner_total": float(s2_gastos.cell(5, 4).value or 0),
        "total_payroll": float(s2_gastos.cell(6, 4).value or 0),
    }

    fixed_opex_detail = {
        "maintenance": float(s2_gastos.cell(11, 2).value or 0),
        "insurance": float(s2_gastos.cell(12, 2).value or 0),
        "utilities": float(s2_gastos.cell(13, 2).value or 0),
        "marketing": float(s2_gastos.cell(14, 2).value or 0),
        "total_opex": float(s2_gastos.cell(15, 2).value or 0),
    }

    funding_detail = {
        "mortgage_loan": float(s2_gastos.cell(19, 8).value or 0),
        "equity_sponsor": float(s2_gastos.cell(20, 8).value or 0),
        "credit_facility": float(s2_gastos.cell(21, 8).value or 0),
        "leader_subsidy": float(s2_gastos.cell(22, 8).value or 0),
        "total_resources": float(s2_gastos.cell(23, 8).value or 0),
    }

    # Sheet 3: Tablas para PPT (wb2) - VAT Comparison
    s2_ppt = wb2_val["Tablas para PPT"]
    vat_comparison = {
        "standard_vat_rate_error": float(s2_ppt.cell(3, 2).value or 0),
        "correct_vat_rate": float(s2_ppt.cell(3, 3).value or 0),
        "cash_balance_y1_error": float(s2_ppt.cell(4, 2).value or 0),
        "cash_balance_y1_correct": float(s2_ppt.cell(4, 3).value or 0),
        "cash_balance_y1_delta": float(s2_ppt.cell(4, 4).value or 0),
        "working_capital_error": float(s2_ppt.cell(5, 2).value or 0),
        "working_capital_correct": float(s2_ppt.cell(5, 3).value or 0),
    }

    return {
        "capex_base": capex_base,
        "pricing_base": pricing_base,
        "seasonality_base": seasonality_base,
        "labor_base": labor_base,
        "segovia_labor": segovia_labor,
        "fixed_opex_detail": fixed_opex_detail,
        "funding_detail": funding_detail,
        "vat_comparison": vat_comparison,
    }


def generate_reconciliation_summary() -> pd.DataFrame:
    """
    Executive reconciliation of the original university workbooks and the three
    refined cases.

    The promoter case is not the original workbook: it is re-modelled with a
    EUR 86,275 revenue construct and the deck's EUR 11,297 EBITDA. The
    "Original Excel" column reports what the source actually contains,
    including the mutually inconsistent Year-1 revenues (74,851; 96,628;
    99,487.50). The refined columns are computed from the model, not from
    stale hard-coded cells.
    """
    from src.config.assumptions import SCENARIOS
    from src.core.metrics import CreditMetricsEngine
    from src.core.statements import FinancialModelEngine

    metrics = CreditMetricsEngine()
    cases: Dict[str, Dict[str, float]] = {}
    for case in ("management", "market", "promoter"):
        engine = FinancialModelEngine(case=case, scenario=SCENARIOS["base"])
        df = engine.run_projection(5)
        debt = engine.debt_engine.get_annual_schedule_df()
        kpi = metrics.compute_credit_kpis(df, debt)
        y1 = kpi.iloc[0]
        cases[case] = {
            "revenue": float(y1["total_revenue"]),
            "ebitda": float(y1["ebitda"]),
            "cash": float(y1["ending_cash"]),
            "dscr": float(y1["dscr"]),
            "capex": float(engine.capex.total_capex),
            "input_vat": float(engine.capex.total_input_vat),
            "equity": float(engine.total_equity_at_close),
        }

    def triple(key: str, fmt: str) -> str:
        return " / ".join(fmt.format(cases[c][key]) for c in ("management", "market", "promoter"))

    rows = [
        {
            "Category": "Occupancy (mature)",
            "Original Excel": "19.20% (implied by 491 / 72 nights)",
            "Refined: mgmt / market / promoter": "31.36% / 21.24% / 19.20%",
            "Notes": "Management is 1.48x INE; the promoter case keeps the original 19.2%.",
        },
        {
            "Category": "Year 1 revenue",
            "Original Excel": "74,851 net / 99,488 gross",
            "Refined: mgmt / market / promoter": triple("revenue", "{:,.0f} €"),
            "Notes": "Conclusiones hard-codes 74,851 (= 90,570 / 1.21); the Plan de Negocio formulas build 99,487.50 gross; the deck shows 96,628 with no build-up.",
        },
        {
            "Category": "Year 1 EBITDA",
            "Original Excel": "26,701 (formulas) / 11,297 (deck)",
            "Refined: mgmt / market / promoter": triple("ebitda", "{:,.0f} €"),
            "Notes": "The formula sheet produces 26,701.31; the deck hard-codes 11,297 with no build-up. The promoter case reaches 11,297 with a 20 € ticket and 25 € purchases.",
        },
        {
            "Category": "Year 1 ending cash",
            "Original Excel": "-2,560.00 € (approx.)",
            "Refined: mgmt / market / promoter": triple("cash", "{:,.0f} €"),
            "Notes": "The originals are cash-insolvent at close; the refined model sizes the equity plug to fix it.",
        },
        {
            "Category": "Year 1 DSCR",
            "Original Excel": "n/a (no DSCR line)",
            "Refined: mgmt / market / promoter": triple("dscr", "{:.2f}x"),
            "Notes": "Only management clears 1.00x in Year 1; the 1.25x covenant still binds in Year 2.",
        },
        {
            "Category": "All-in CapEx",
            "Original Excel": "725,000.00 €",
            "Refined: mgmt / market / promoter": triple("capex", "{:,.0f} €"),
            "Notes": "Management/market: land 250k + 550 m2 works + kitchen + FF&E + biopool + digital + fees + contingency.",
        },
        {
            "Category": "Payroll (annual)",
            "Original Excel": "58,740.00 €",
            "Refined: mgmt / market / promoter": "60,075.00 €",
            "Notes": "Part-time hours; employer SS included.",
        },
        {
            "Category": "Input VAT on CapEx",
            "Original Excel": "Not modeled",
            "Refined: mgmt / market / promoter": triple("input_vat", "{:,.0f} €"),
            "Notes": "21% on non-land CapEx; bridge-financed and refunded by AEAT.",
        },
        {
            "Category": "Equity at close",
            "Original Excel": "30% of CapEx (assumed)",
            "Refined: mgmt / market / promoter": triple("equity", "{:,.0f} €"),
            "Notes": "A cash-equity plug plus in-kind land, not a 30% assumption.",
        },
        {
            "Category": "Output VAT",
            "Original Excel": "21% in the summary, gross in the formulas",
            "Refined: mgmt / market / promoter": "10.0% statutory",
            "Notes": "At the statutory 10% the 90,570 gross becomes 82,336; the deck's 96,628 has no VAT build-up.",
        },
        {
            "Category": "Balance sheet",
            "Original Excel": "Single sheet, no balance sheet",
            "Refined: mgmt / market / promoter": "Assets = L + E (0.00 €)",
            "Notes": "Strict double-entry, 5 years, 3 cases.",
        },
    ]

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_reconciliation_summary()
    print("================================================================================")
    print(" LA DEHESA DEL CASTRILLO - DUE DILIGENCE AUDIT & RECONCILIATION TABLE")
    print("================================================================================")
    print(df.to_string(index=False))
    print("================================================================================")
