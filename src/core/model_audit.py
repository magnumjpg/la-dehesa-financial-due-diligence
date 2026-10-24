"""
Programmatic Model Audit & Data Room Integrity Engine for La Dehesa del Castrillo S.L.

This is a *computed* audit, not a self-certification checklist. Every rule is
evaluated against the model output and can fail. The audit intentionally
reports material exceptions (funding gap, credit-line inconsistency, Phase II
double-spend, market-case covenant breach) alongside the genuine strengths
(balance-sheet equality, payroll hourly compliance, promoter-case replication).

Rules:
1. Balance-sheet equality (Assets == Liabilities + Equity).
2. Hospitality VAT rate (10% on lodging and restaurant).
3. CapEx input VAT (21%) recognised as a fiscal asset.
4. Payroll hourly compliance vs. SMI 2026 and the Segovia convenio.
5. Management-case DSCR covenant (>= 1.25x).
6. Adjusted Year-1 cash after pre-opening, working capital and DSRA.
7. DSRA sizing vs. the 6-month debt service.
8. Sources & uses at close (no funding gap).
9. Credit-line utilisation (model bridge <= stated limit).
10. Management occupancy vs. INE market occupancy.
11. Phase II self-funding / phase gate.
12. Returns consistency (project IRR with exit >= WACC).
13. Promoter-case replication of the original university simulator.
14. Market-case DSCR covenant.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.assumptions import (
    CapExStructure,
    FinancingStructure,
    LaborStructure,
    FixedOpexStructure,
    RevenueModelConfig,
    SCENARIOS,
    SMI_2026_HOURLY,
    CONVENIO_SEGOVIA_2026_HOURLY,
)
from src.config.ine_weights import get_annual_weighted_occupancy, get_market_occupancy
from src.core.statements import FinancialModelEngine
from src.core.metrics import CreditMetricsEngine
from src.core.funding import SourcesUsesEngine
from src.core.expansion import ExpansionFinancialEngine


@dataclass
class AuditMetric:
    metric_id: str
    name: str
    value: Any
    unit: str
    formula: str
    statutory_source: str
    category: str
    tolerance: float = 0.01


@dataclass
class AuditGuardrailRule:
    rule_id: str
    rule_name: str
    description: str
    condition_expression: str
    status: str  # "PASSED" or "FAILED"
    actual_value: Any
    threshold: Any
    remediation_guidance: str
    severity: str = "MATERIAL"  # MATERIAL, WARNING, INFO


class ModelAuditEngine:
    """Executes computed due-diligence verification and model-integrity checks."""

    def __init__(self, export_dir: Optional[Path] = None):
        self.export_dir = export_dir or (Path(__file__).resolve().parent.parent.parent / "data")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.export_file = self.export_dir / "model_audit_summary.json"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _rule(
        rule_id: str,
        rule_name: str,
        description: str,
        condition_expression: str,
        passed: bool,
        actual_value: Any,
        threshold: Any,
        remediation: str,
        severity: str = "MATERIAL",
    ) -> AuditGuardrailRule:
        return AuditGuardrailRule(
            rule_id=rule_id,
            rule_name=rule_name,
            description=description,
            condition_expression=condition_expression,
            status="PASSED" if passed else "FAILED",
            actual_value=actual_value,
            threshold=threshold,
            remediation_guidance=remediation,
            severity=severity,
        )

    def _run_case(self, case: str):
        engine = FinancialModelEngine(case=case, scenario=SCENARIOS["base"])
        df = engine.run_projection(projection_years=5)
        debt = engine.debt_engine.get_annual_schedule_df()
        credit = CreditMetricsEngine(target_dscr=1.25)
        kpi = credit.compute_credit_kpis(df, debt)
        returns = credit.compute_returns_summary(
            df,
            initial_equity=engine.financing.sponsor_equity,
            initial_capex=engine.capex.total_capex,
        )
        return engine, df, debt, kpi, returns

    # ------------------------------------------------------------------
    # Main payload
    # ------------------------------------------------------------------
    def generate_audit_payload(self) -> Dict[str, Any]:
        """Computes the audit payload from the management, market and promoter cases."""
        mgmt_engine, mgmt_df, mgmt_debt, mgmt_kpi, mgmt_returns = self._run_case("management")
        mkt_engine, mkt_df, mkt_debt, mkt_kpi, mkt_returns = self._run_case("market")
        prom_engine, prom_df, prom_debt, prom_kpi, prom_returns = self._run_case("promoter")

        funding_mgmt = SourcesUsesEngine(case="management").compute()
        funding_mkt = SourcesUsesEngine(case="market").compute()
        funding_prom = SourcesUsesEngine(case="promoter").compute()

        expansion = ExpansionFinancialEngine()
        phase_gate = expansion.compute_phase_gate(
            phase1_cash_end_y2=funding_mgmt.cash_y2_model,
            phase1_dscr_y3=float(mgmt_kpi.iloc[2]["dscr"]),
        )

        # --- Computed metrics -------------------------------------------------
        mgmt_y1 = mgmt_kpi.iloc[0]
        mgmt_y2 = mgmt_kpi.iloc[1]
        mgmt_y3 = mgmt_kpi.iloc[2]
        mkt_y1 = mkt_kpi.iloc[0]
        prom_y1 = prom_kpi.iloc[0]

        max_bs_diff = max(
            float(mgmt_df["balance_sheet_discrepancy"].abs().max()),
            float(mkt_df["balance_sheet_discrepancy"].abs().max()),
            float(prom_df["balance_sheet_discrepancy"].abs().max()),
        )

        # VAT rate actually applied in Year 1 (output VAT / net revenue).
        vat_y1 = mgmt_engine.vat_engine.calculate_annual_vat_settlement(
            year=1,
            revenue_lodging=float(mgmt_y1["revenue_rooms"] + mgmt_y1["revenue_full_house"]),
            revenue_restaurant=float(mgmt_y1["revenue_restaurant"]),
            capex_expenditure=mgmt_engine.capex.total_capex,
            taxable_opex=float(mgmt_y1["fixed_opex"] + mgmt_y1["cogs_restaurant"]),
            request_annual_refund=True,
        )
        net_revenue_y1 = float(mgmt_y1["total_revenue"])
        applied_vat_rate = (
            round(vat_y1["total_output_vat"] / net_revenue_y1, 6)
            if net_revenue_y1 else 0.0
        )

        input_vat = float(mgmt_engine.capex.total_input_vat)
        expected_input_vat = round(mgmt_engine.capex.total_capex * 0.21, 2)

        payroll_rows = mgmt_engine.labor.hourly_compliance
        payroll_smi_ok = all(r["compliant_smi"] for r in payroll_rows)
        payroll_convenio_ok = all(r["compliant_convenio"] for r in payroll_rows)
        min_hourly_gross = min(r["hourly_gross"] for r in payroll_rows)
        min_reference = min(r["convenio_hourly"] for r in payroll_rows)

        mgmt_occ = get_annual_weighted_occupancy()
        market_occ = get_market_occupancy()
        occ_ratio = mgmt_occ / market_occ if market_occ else 0.0

        prom_rev_ok = abs(float(prom_y1["total_revenue"]) - 86_275.0) <= 1.0
        prom_ebitda_ok = abs(float(prom_y1["ebitda"]) - 11_297.0) <= 1.0

        # --- Metrics catalogue ------------------------------------------------
        metrics_catalog: List[AuditMetric] = [
            AuditMetric(
                "capex_total", "Total Phase I CapEx", mgmt_engine.capex.total_capex, "EUR",
                "Land 250k + Renovation 440k + Biopool 35k + Digitalization 4k",
                "Project technical due diligence", "Capital Expenditure",
            ),
            AuditMetric(
                "input_vat", "Deductible input VAT on CapEx", input_vat, "EUR",
                "21% * total CapEx", "Ley 37/1992 (IVA)", "Tax Asset",
            ),
            AuditMetric(
                "management_revenue_y1", "Management-case Year-1 revenue", float(mgmt_y1["total_revenue"]), "EUR",
                "31.36% mature occupancy * one on-site meal per guest per day * €25 ticket",
                "Python management case (upside)", "P&L Operations",
            ),
            AuditMetric(
                "management_ebitda_y1", "Management-case Year-1 EBITDA", float(mgmt_y1["ebitda"]), "EUR",
                "Revenue - COGS - payroll (€60,075) - fixed opex (€12,159)",
                "Operating P&L", "P&L Operations",
            ),
            AuditMetric(
                "management_dscr_y1", "Management-case Year-1 DSCR", float(mgmt_y1["dscr"]), "ratio",
                "(EBITDA - tax) / annual debt service", "Bank covenant (floor 1.25x)", "Credit Solvency",
            ),
            AuditMetric(
                "market_revenue_y1", "INE market-case Year-1 revenue", float(mkt_y1["total_revenue"]), "EUR",
                "INE 21.24% occupancy * original unit economics (€85/€380/€20)",
                "INE EOTR Segovia 2025", "P&L Operations",
            ),
            AuditMetric(
                "market_ebitda_y1", "INE market-case Year-1 EBITDA", float(mkt_y1["ebitda"]), "EUR",
                "Revenue - COGS - payroll - fixed opex", "Operating P&L", "P&L Operations",
            ),
            AuditMetric(
                "market_dscr_y1", "INE market-case Year-1 DSCR", float(mkt_y1["dscr"]), "ratio",
                "(EBITDA - tax) / annual debt service", "Bank covenant (floor 1.25x)", "Credit Solvency",
            ),
            AuditMetric(
                "promoter_revenue_y1", "Promoter-case Year-1 revenue", float(prom_y1["total_revenue"]), "EUR",
                "491 room-nights * €85 + 72 house-nights * €380 + 859 meals * €20",
                "Original university simulator", "Replication",
            ),
            AuditMetric(
                "promoter_ebitda_y1", "Promoter-case Year-1 EBITDA", float(prom_y1["ebitda"]), "EUR",
                "€86,275 - €14,903 opex - €60,075 payroll", "Original university simulator", "Replication",
            ),
            AuditMetric(
                "management_occupancy", "Management-case mature occupancy", round(mgmt_occ, 4), "percentage",
                "Day-weighted average of the management monthly series", "Python management case", "Occupancy",
            ),
            AuditMetric(
                "market_occupancy", "INE Segovia market occupancy", round(market_occ, 4), "percentage",
                "Day-weighted average of the INE monthly series", "INE EOTR Segovia 2025", "Occupancy",
            ),
            AuditMetric(
                "funding_gap_close", "Funding gap at close", funding_mgmt.funding_gap_at_close, "EUR",
                "Sources at close - uses at close (CapEx + VAT + pre-opening + WC + DSRA)",
                "Sources & Uses analysis", "Liquidity",
            ),
            AuditMetric(
                "credit_line_drawn_y1", "Credit line / VAT bridge drawn in Year 1", funding_mgmt.model_credit_line_drawn_y1, "EUR",
                "Model credit_line_drawn (VAT bridge) at end of Year 1", "Model cash flow", "Liquidity",
            ),
            AuditMetric(
                "phase2_cash_need", "Phase II cash need (net CapEx + VAT)", phase_gate["phase2_cash_need"], "EUR",
                "€359,970 + €75,593.70", "Phase II expansion budget", "Phase II",
            ),
            AuditMetric(
                "phase2_funding_gap", "Phase II funding gap", phase_gate["phase2_funding_gap"], "EUR",
                "Phase I cash at end of Year 2 - Phase II cash need", "Phase gate", "Phase II",
            ),
            AuditMetric(
                "project_irr_exit", "Project IRR with 8.5% exit (management case)", mgmt_returns["project_irr_exit"], "percentage",
                "Unlevered FCF + terminal value at 8.5% cap rate", "DCF / exit valuation", "Returns",
            ),
            AuditMetric(
                "equity_irr_exit", "Equity IRR with 8.5% exit (management case)", mgmt_returns["equity_irr_exit"], "percentage",
                "Levered FCF + terminal equity value", "DCF / exit valuation", "Returns",
            ),
        ]

        # --- Guardrail rules --------------------------------------------------
        guardrails: List[AuditGuardrailRule] = [
            self._rule(
                "RULE_01_BALANCE_SHEET_EQUALITY",
                "Strict double-entry balance-sheet equality",
                "Assets must equal liabilities plus equity across all three cases.",
                "abs(total_assets - (total_liabilities + total_equity)) <= 0.01",
                max_bs_diff <= 0.01, round(max_bs_diff, 4), 0.01,
                "Verify VAT credit and financing facilities are balanced across CFO, CFI and CFF.",
            ),
            self._rule(
                "RULE_02_HOSPITALITY_VAT_RATE",
                "Hospitality statutory VAT rate (10%)",
                "Lodging and restaurant revenue must be taxed at 10%, not 21%.",
                "applied_vat_rate == 0.10",
                abs(applied_vat_rate - 0.10) <= 0.0001, applied_vat_rate, 0.10,
                "Recalibrate output VAT to Ley 37/1992 art. 91.Uno.2.2º.",
            ),
            self._rule(
                "RULE_03_CAPEX_INPUT_VAT",
                "CapEx input VAT recognised as a fiscal asset",
                "21% input VAT on CapEx must be booked as a receivable, not expensed.",
                "input_vat == 21% * capex",
                abs(input_vat - expected_input_vat) <= 1.0, input_vat, expected_input_vat,
                "Book the Modelo 303/390 deductible VAT asset and disclose the bridge facility.",
            ),
            self._rule(
                "RULE_04_PAYROLL_HOURLY_COMPLIANCE",
                "Payroll hourly compliance (SMI 2026 and Segovia convenio)",
                "Each part-time role's gross hourly cost must be at least the SMI and the convenio reference.",
                "min(hourly_gross) >= max(SMI_hourly, convenio_hourly)",
                payroll_smi_ok and payroll_convenio_ok,
                {"min_hourly_gross": min_hourly_gross, "min_reference": round(min_reference, 2),
                 "smi_ok": payroll_smi_ok, "convenio_ok": payroll_convenio_ok},
                round(max(SMI_2026_HOURLY, min_reference), 2),
                "If the contracts are full-time, the annual salaries are below the convenio. Document the part-time hours.",
                severity="MATERIAL",
            ),
            self._rule(
                "RULE_05_MANAGEMENT_DSCR",
                "Management-case Year-1 DSCR covenant",
                "The management case must meet the 1.25x bank covenant in Year 1.",
                "management_dscr_y1 >= 1.25",
                float(mgmt_y1["dscr"]) >= 1.25, float(mgmt_y1["dscr"]), 1.25,
                "If DSCR < 1.25x, inject equity, extend the grace period or reduce debt.",
            ),
            self._rule(
                "RULE_06_ADJUSTED_CASH_TROUGH",
                "Adjusted Year-1 cash after omitted close-day uses",
                "Year-1 cash must remain positive after pre-opening, working capital and DSRA.",
                "adjusted_cash_y1 >= 0",
                funding_mgmt.cash_y1_adjusted >= 0, funding_mgmt.cash_y1_adjusted, 0.0,
                "Fund the €70.8k close-day gap with additional equity or a larger facility.",
            ),
            self._rule(
                "RULE_07_DSRA_SIZING",
                "DSRA sizing vs. six months of debt service",
                "The DSRA must cover at least six months of senior debt service.",
                "dsra >= 6/12 * annual_debt_service",
                funding_mgmt.dsra >= 0.5 * float(mgmt_debt.iloc[0]["payment"]),
                funding_mgmt.dsra, round(0.5 * float(mgmt_debt.iloc[0]["payment"]), 2),
                "Pledge the DSRA in escrow before financial close.",
                severity="WARNING",
            ),
            self._rule(
                "RULE_08_SOURCES_USES_CLOSE",
                "Sources & uses at close",
                "Close-day sources must cover close-day uses.",
                "sources_at_close - uses_at_close >= 0",
                funding_mgmt.funding_gap_at_close >= 0,
                funding_mgmt.funding_gap_at_close, 0.0,
                "Add €70.8k of equity or a larger VAT/working-capital facility.",
            ),
            self._rule(
                "RULE_09_CREDIT_LINE_LIMIT",
                "Credit-line utilisation vs. stated limit",
                "The model's Year-1 VAT bridge must not exceed the stated €50k revolving line.",
                "credit_line_drawn_y1 <= 50,000",
                funding_mgmt.model_credit_line_drawn_y1 <= funding_mgmt.credit_line_limit,
                funding_mgmt.model_credit_line_drawn_y1, funding_mgmt.credit_line_limit,
                "Disclose the VAT bridge as a separate €153k facility or increase the line to €150k.",
            ),
            self._rule(
                "RULE_10_OCCUPANCY_VS_INE",
                "Management occupancy vs. INE market benchmark",
                "The management case should not exceed 1.10x the official INE market occupancy without justification.",
                "management_occupancy <= 1.10 * market_occupancy",
                occ_ratio <= 1.10, round(occ_ratio, 2), 1.10,
                "Present the 31.36% case as an upside case and lead with the 21.24% market case.",
                severity="WARNING",
            ),
            self._rule(
                "RULE_11_PHASE2_SELF_FUNDING",
                "Phase II self-funding / phase gate",
                "Phase II may proceed only if Phase I cash covers the full Phase II cash need.",
                "phase1_cash_end_y2 >= phase2_cash_need",
                phase_gate["phase2_proceed"], phase_gate["phase2_funding_gap"], 0.0,
                "Do not double-count the LEADER grant and VAT refund. Raise €241.6k or phase the expansion.",
            ),
            self._rule(
                "RULE_12_RETURNS_VS_WACC",
                "Project IRR with exit vs. 8% WACC",
                "The management-case project IRR with an 8.5% exit cap rate must exceed the 8% WACC.",
                "project_irr_exit >= 0.08",
                (mgmt_returns["project_irr_exit"] or 0.0) >= 0.08,
                mgmt_returns["project_irr_exit"], 0.08,
                "If IRR < WACC, the exit cap rate or the operating assumptions must be revisited.",
            ),
            self._rule(
                "RULE_13_PROMOTER_REPLICATION",
                "Promoter-case replication of the original simulator",
                "The promoter case must reproduce the original Excel's Year-1 revenue (€86,275) and EBITDA (€11,297).",
                "abs(revenue - 86,275) <= 1 and abs(EBITDA - 11,297) <= 1",
                prom_rev_ok and prom_ebitda_ok,
                {"revenue": float(prom_y1["total_revenue"]), "ebitda": float(prom_y1["ebitda"])},
                {"revenue": 86_275.0, "ebitda": 11_297.0},
                "Reconcile the original Excel units, prices and opex.",
                severity="INFO",
            ),
            self._rule(
                "RULE_14_MARKET_DSCR",
                "INE market-case Year-1 DSCR covenant",
                "The independent INE market case must also meet the 1.25x covenant.",
                "market_dscr_y1 >= 1.25",
                float(mkt_y1["dscr"]) >= 1.25, float(mkt_y1["dscr"]), 1.25,
                "At 21.24% occupancy the project does not cover debt service. Re-size the debt or add equity.",
            ),
        ]

        material_failures = [
            g.rule_id for g in guardrails
            if g.status == "FAILED" and g.severity == "MATERIAL"
        ]
        warning_failures = [
            g.rule_id for g in guardrails
            if g.status == "FAILED" and g.severity == "WARNING"
        ]
        all_passed = all(g.status == "PASSED" for g in guardrails)

        if material_failures:
            verdict = f"CONDITIONAL - {len(material_failures)} MATERIAL EXCEPTION(S)"
        elif warning_failures:
            verdict = f"CONDITIONAL - {len(warning_failures)} WARNING(S)"
        else:
            verdict = "PASSED - MODEL INTEGRITY VERIFIED"

        payload = {
            "meta": {
                "project_name": "La Dehesa del Castrillo S.L.",
                "legal_form": "Sociedad de Responsabilidad Limitada (S.L.)",
                "industry_sector": "Boutique Hospitality & Agritourism Estate",
                "jurisdiction": "Kingdom of Spain (Castilla y León, Segovia)",
                "governing_statutes": [
                    "Ley 37/1992 (Impuesto sobre el Valor Añadido)",
                    "Ley 27/2014 (Impuesto sobre Sociedades)",
                    "Convenio Colectivo Provincial de Hostelería de Segovia (BOCyL)",
                    "Instituto Nacional de Estadística (EOTR Segovia)",
                    "Real Decreto 126/2026 (SMI 2026)",
                ],
                "export_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "schema_version": "3.0.0",
                "framework": "Computed Model Audit & Funding-Gap Verification",
            },
            "case_summary": {
                "management": {
                    "revenue_y1": float(mgmt_y1["total_revenue"]),
                    "ebitda_y1": float(mgmt_y1["ebitda"]),
                    "dscr_y1": float(mgmt_y1["dscr"]),
                    "cash_y1": float(mgmt_y1["ending_cash"]),
                    "project_irr_exit": mgmt_returns["project_irr_exit"],
                    "equity_irr_exit": mgmt_returns["equity_irr_exit"],
                },
                "market": {
                    "revenue_y1": float(mkt_y1["total_revenue"]),
                    "ebitda_y1": float(mkt_y1["ebitda"]),
                    "dscr_y1": float(mkt_y1["dscr"]),
                    "cash_y1": float(mkt_y1["ending_cash"]),
                    "project_irr_exit": mkt_returns["project_irr_exit"],
                },
                "promoter": {
                    "revenue_y1": float(prom_y1["total_revenue"]),
                    "ebitda_y1": float(prom_y1["ebitda"]),
                    "dscr_y1": float(prom_y1["dscr"]),
                    "cash_y1": float(prom_y1["ending_cash"]),
                },
            },
            "funding": {
                "management": asdict(funding_mgmt),
                "market": asdict(funding_mkt),
                "promoter": asdict(funding_prom),
                "phase2_gate": phase_gate,
            },
            "ground_truth_metrics": {m.metric_id: asdict(m) for m in metrics_catalog},
            "guardrail_audit_rules": [asdict(g) for g in guardrails],
            "execution_status": {
                "all_guardrails_satisfied": all_passed,
                "total_rules_evaluated": len(guardrails),
                "total_rules_passed": sum(1 for g in guardrails if g.status == "PASSED"),
                "total_rules_failed": sum(1 for g in guardrails if g.status == "FAILED"),
                "material_exceptions": material_failures,
                "warning_exceptions": warning_failures,
                "audit_verdict": verdict,
            },
        }
        return payload

    def export_json(self) -> Path:
        """Serializes the audit payload to JSON."""
        payload = self.generate_audit_payload()
        with open(self.export_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return self.export_file

    def print_terminal_summary(self):
        """Prints the computed audit summary to the console."""
        payload = self.generate_audit_payload()
        status = payload["execution_status"]

        print("=" * 88)
        print(" COMPUTED MODEL AUDIT & DATA ROOM INTEGRITY LAYER")
        print("=" * 88)
        print(f"Schema Version:                  {payload['meta']['schema_version']}")
        print(f"Framework:                       {payload['meta']['framework']}")
        print(f"Ground-Truth Metrics Count:      {len(payload['ground_truth_metrics'])}")
        print(f"Audit Rules Evaluated:           {status['total_rules_evaluated']}")
        print(f"Rules Passed:                    {status['total_rules_passed']} / {status['total_rules_evaluated']}")
        print(f"Material Exceptions:             {len(status['material_exceptions'])}")
        print(f"Warning Exceptions:              {len(status['warning_exceptions'])}")
        print(f"Audit Verdict:                   {status['audit_verdict']}")
        print("-" * 88)
        print("Case Summary:")
        for case, values in payload["case_summary"].items():
            print(f"  {case.upper():10s} Revenue Y1 €{values['revenue_y1']:>12,.2f} | "
                  f"EBITDA €{values['ebitda_y1']:>12,.2f} | DSCR {values['dscr_y1']:.2f}x")
        print("-" * 88)
        print("Guardrail Integrity Status:")
        for r in payload["guardrail_audit_rules"]:
            flag = "[PASS]" if r["status"] == "PASSED" else "[FAIL]"
            print(f"  {flag} {r['rule_id']}: {r['rule_name']} (Actual: {r['actual_value']})")
        print("=" * 88)
