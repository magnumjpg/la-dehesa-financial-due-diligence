"""
Programmatic Model Audit & Data Room Integrity Engine for La Dehesa del Castrillo S.L.

This is a *computed* audit, not a self-certification checklist. Every rule is
evaluated against the model output and can fail. The audit deliberately reports
the material exceptions (DSCR covenant breach in Year 2, negative project
returns, a 49.6% cash-equity requirement, Phase II shortfall, market-case
insolvency, upside occupancy vs. INE) alongside the genuine strengths
(balance-sheet equality, payroll hourly compliance, VAT treatment and the
promoter-case calibration target).

Rules (16):
1.  Balance-sheet equality (Assets == Liabilities + Equity).
2.  Hospitality VAT rate (10% on lodging and restaurant).
3.  CapEx input VAT (21% on non-land CapEx) recognised as a fiscal asset.
4.  Payroll hourly compliance vs. SMI 2026 and the Segovia convenio.
5.  Management-case minimum DSCR over the projection (>= 1.25x).
6.  Minimum cash balance over the projection (>= 0).
7.  DSRA sizing vs. six months of the maximum annual debt service.
8.  Sources & uses at close (no funding gap).
9.  VAT bridge within its stated limit.
10. Management occupancy vs. INE market occupancy.
11. Phase II self-funding / phase gate.
12. Project IRR with exit vs. the 8% WACC.
13. Promoter-case calibration to the presentation's headline figures.
14. Market-case minimum DSCR (>= 1.25x).
15. Cash equity requirement vs. the original 30% assumption.
16. FF&E reserve of 3% of revenue deducted from CFADS.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.assumptions import (
    SCENARIOS,
    SMI_2026_HOURLY,
)
from src.config.ine_weights import get_annual_weighted_occupancy, get_market_occupancy
from src.core.statements import FinancialModelEngine
from src.core.metrics import BreakEvenEngine, CreditMetricsEngine
from src.core.funding import SourcesUsesEngine
from src.core.expansion import ExpansionFinancialEngine

SCHEMA_VERSION = "4.0.0"


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
            initial_equity=engine.total_equity_at_close,
            initial_capex=engine.total_project_investment,
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
            phase1_cash_end_y2=funding_mgmt.cash_by_year[1],
            phase1_dscr_y3=funding_mgmt.dscr_by_year[2],
        )

        breakeven = BreakEvenEngine(case="management").compute()

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
            capex_expenditure=0.0,
            taxable_opex=float(mgmt_y1["fixed_opex"] + mgmt_y1["total_variable_costs"]),
            request_annual_refund=False,
        )
        net_revenue_y1 = float(mgmt_y1["total_revenue"])
        applied_vat_rate = (
            round(vat_y1["total_output_vat"] / net_revenue_y1, 6)
            if net_revenue_y1 else 0.0
        )

        input_vat = float(mgmt_engine.capex.total_input_vat)
        expected_input_vat = round(
            (mgmt_engine.capex.total_capex - mgmt_engine.capex.land.amount) * 0.21, 2
        )

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

        ffe_ok = abs(
            float(mgmt_y1["ffe_reserve"])
            - float(mgmt_y1["total_revenue"]) * mgmt_engine.rev_cfg.ffe_reserve_rate
        ) <= 1.0

        equity_ratio = funding_mgmt.cash_equity_required / mgmt_engine.capex.total_capex

        # --- Metrics catalogue ------------------------------------------------
        metrics_catalog: List[AuditMetric] = [
            AuditMetric(
                "capex_total", "Total Phase I CapEx (realistic budget)", mgmt_engine.capex.total_capex, "EUR",
                "Land 250k + 550 m2 @ 1,000 EUR/m2 + kitchen 55k + FF&E 65k + biopool 40k + digital 12k + fees 42.6k + contingency 35.5k",
                "Project technical due diligence", "Capital Expenditure",
            ),
            AuditMetric(
                "capex_per_sqm", "Renovation cost per square metre",
                round(mgmt_engine.capex.renovation.amount / 550.0, 2), "EUR/m2",
                "Renovation 550,000 / 550 m2", "Technical due diligence", "Capital Expenditure",
            ),
            AuditMetric(
                "input_vat", "Deductible input VAT on CapEx", input_vat, "EUR",
                "21% * (total CapEx - land)", "Ley 37/1992 (IVA)", "Tax Asset",
            ),
            AuditMetric(
                "management_revenue_y1", "Management-case Year-1 revenue", float(mgmt_y1["total_revenue"]), "EUR",
                "31.36% mature occupancy (ramped to 28.2% in Y1) * 8 keys * ADR + one meal per guest at EUR 25",
                "Python management case (upside)", "P&L Operations",
            ),
            AuditMetric(
                "management_ebitda_y1", "Management-case Year-1 EBITDA", float(mgmt_y1["ebitda"]), "EUR",
                "Revenue - variable stack - payroll (60,075) - fixed opex (30,500)",
                "Operating P&L", "P&L Operations",
            ),
            AuditMetric(
                "management_dscr_min", "Management-case minimum DSCR (Years 1-5)", funding_mgmt.dscr_min, "ratio",
                "(EBITDA - FF&E reserve - tax) / senior debt service", "Bank covenant (floor 1.25x)", "Credit Solvency",
            ),
            AuditMetric(
                "management_cash_equity", "Cash equity required at close", funding_mgmt.cash_equity_required, "EUR",
                "Total uses - senior debt - VAT bridge - land in kind",
                "Sources & Uses analysis", "Funding",
            ),
            AuditMetric(
                "management_equity_ratio", "Cash equity / total CapEx", round(equity_ratio, 4), "percentage",
                "Cash equity / total CapEx", "Sources & Uses analysis", "Funding",
            ),
            AuditMetric(
                "management_total_equity", "Total equity at close (cash + land in kind)",
                mgmt_engine.total_equity_at_close, "EUR",
                "Cash equity + in-kind land", "Sources & Uses analysis", "Funding",
            ),
            AuditMetric(
                "market_revenue_y1", "INE market-case Year-1 revenue", float(mkt_y1["total_revenue"]), "EUR",
                "INE 21.24% occupancy * original unit economics (EUR 85/EUR 380/EUR 20)",
                "INE EOTR Segovia 2025", "P&L Operations",
            ),
            AuditMetric(
                "market_ebitda_y1", "INE market-case Year-1 EBITDA", float(mkt_y1["ebitda"]), "EUR",
                "Revenue - variable stack - payroll - fixed opex", "Operating P&L", "P&L Operations",
            ),
            AuditMetric(
                "promoter_revenue_y1", "Promoter-case Year-1 revenue (re-modelled)", float(prom_y1["total_revenue"]), "EUR",
                "491 room-nights * EUR 85 + 72 house-nights * EUR 380 + 859 covers * EUR 20",
                "Presentation headline (re-modelled)", "Calibration",
            ),
            AuditMetric(
                "promoter_ebitda_y1", "Promoter-case Year-1 EBITDA (re-modelled)", float(prom_y1["ebitda"]), "EUR",
                "86,275 revenue - 60,075 realistic payroll - 14,903 other opex",
                "Presentation headline (re-modelled)", "Calibration",
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
                "covenant_breakeven_occupancy", "Mature occupancy required for a 1.25x covenant",
                breakeven["covenant_breakeven_occupancy_mature"], "percentage",
                "Bisection on the occupancy multiplier until min DSCR = 1.25x",
                "Computed break-even", "Break-even",
            ),
            AuditMetric(
                "covenant_breakeven_adr", "ADR required for a 1.25x covenant at base occupancy",
                breakeven["covenant_breakeven_adr"], "EUR",
                "Bisection on the ADR multiplier until min DSCR = 1.25x",
                "Computed break-even", "Break-even",
            ),
            AuditMetric(
                "equity_irr_10pct_adr", "ADR required for a 10% equity IRR (8.5% exit)",
                breakeven["equity_irr_10pct_adr"], "EUR",
                "Bisection on the ADR multiplier until the equity IRR reaches 10%",
                "Computed break-even", "Break-even",
            ),
            AuditMetric(
                "phase2_cash_need", "Phase II cash need (CapEx + VAT)", phase_gate["phase2_cash_need"], "EUR",
                "359,970 + 75,593.70", "Phase II expansion budget", "Phase II",
            ),
            AuditMetric(
                "phase2_funding_gap", "Phase II funding gap", phase_gate["phase2_funding_gap"], "EUR",
                "Phase I cash at end of Year 2 - Phase II cash need", "Phase gate", "Phase II",
            ),
            AuditMetric(
                "project_irr_exit", "Project IRR with 8.5% exit (management case)", mgmt_returns["project_irr_exit"], "percentage",
                "Unlevered FCF + terminal value at an 8.5% cap rate", "DCF / exit valuation", "Returns",
            ),
            AuditMetric(
                "equity_irr_exit", "Equity IRR with 8.5% exit (management case)", mgmt_returns["equity_irr_exit"], "percentage",
                "Levered FCF + terminal equity value", "DCF / exit valuation", "Returns",
            ),
            AuditMetric(
                "terminal_value", "Terminal value at an 8.5% cap rate", mgmt_returns["terminal_value"], "EUR",
                "Year-5 EBITDA / 8.5%", "Exit valuation", "Returns",
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
                "Verify that the VAT pass-through, the FF&E reserve and the in-kind land are booked on both sides.",
            ),
            self._rule(
                "RULE_02_HOSPITALITY_VAT_RATE",
                "Hospitality statutory VAT rate (10%)",
                "Lodging and restaurant revenue must be taxed at 10%, not 21%.",
                "applied_vat_rate == 0.10",
                abs(applied_vat_rate - 0.10) <= 0.0001, applied_vat_rate, 0.10,
                "Recalibrate output VAT to Ley 37/1992 art. 91.Uno.2.2o.",
            ),
            self._rule(
                "RULE_03_CAPEX_INPUT_VAT",
                "CapEx input VAT recognised as a fiscal asset",
                "21% input VAT on non-land CapEx must be booked as a receivable, not expensed.",
                "input_vat == 21% * (capex - land)",
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
                "Management-case minimum DSCR covenant",
                "The management case must meet the 1.25x bank covenant in every projection year.",
                "min(dscr_y1..y5) >= 1.25",
                funding_mgmt.dscr_min >= 1.25, funding_mgmt.dscr_min, 1.25,
                "Year 2 breaches the covenant when amortisation starts. Extend the grace period, "
                "reduce the facility or inject equity before the first amortising payment.",
            ),
            self._rule(
                "RULE_06_MINIMUM_CASH",
                "Minimum cash balance over the projection",
                "Cash must remain non-negative after the equity plug and the DSRA.",
                "min(cash_y1..y5) >= 0",
                funding_mgmt.min_cash >= 0, funding_mgmt.min_cash, 0.0,
                "Increase the equity injection or the revolving facility.",
            ),
            self._rule(
                "RULE_07_DSRA_SIZING",
                "DSRA sizing vs. six months of maximum debt service",
                "The DSRA must cover at least six months of the maximum annual senior debt service.",
                "dsra >= 0.5 * max(annual_debt_service)",
                funding_mgmt.dsra >= 0.5 * mgmt_engine.annual_debt_service_max - 0.01,
                funding_mgmt.dsra,
                round(0.5 * mgmt_engine.annual_debt_service_max, 2),
                "Pledge the DSRA in escrow before financial close.",
                severity="WARNING",
            ),
            self._rule(
                "RULE_08_SOURCES_USES_CLOSE",
                "Sources & uses at close",
                "Close-day sources must cover close-day uses.",
                "sources_at_close - uses_at_close >= 0",
                funding_mgmt.funding_gap_at_close >= -0.01,
                funding_mgmt.funding_gap_at_close, 0.0,
                "Add equity or a larger VAT/working-capital facility.",
            ),
            self._rule(
                "RULE_09_VAT_BRIDGE_LIMIT",
                "VAT bridge within its stated limit",
                "The gross input VAT drawn on the bridge must not exceed the 175,000 facility.",
                "vat_bridge <= vat_bridge_limit",
                funding_mgmt.vat_bridge <= funding_mgmt.vat_bridge_limit,
                funding_mgmt.vat_bridge, funding_mgmt.vat_bridge_limit,
                "Size the bridge on the gross input VAT (168,021) or request a larger facility.",
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
                "Do not double-count the LEADER grant and VAT refund. Raise the shortfall or phase the expansion.",
            ),
            self._rule(
                "RULE_12_RETURNS_VS_WACC",
                "Project IRR with exit vs. 8% WACC",
                "The management-case project IRR with an 8.5% exit cap rate must exceed the 8% WACC.",
                "project_irr_exit >= 0.08",
                (mgmt_returns["project_irr_exit"] or 0.0) >= 0.08,
                mgmt_returns["project_irr_exit"], 0.08,
                "The all-in cost (1.05m) is not recovered by the exit value (terminal EBITDA / 8.5%). "
                "Revisit ADR, occupancy or the renovation scope.",
            ),
            self._rule(
                "RULE_13_PROMOTER_CALIBRATION",
                "Promoter-case calibration to the presentation headline",
                "The promoter case must land on its declared calibration target: the presentation's "
                "Year-1 revenue (86,275) and EBITDA (11,297). This is not a replication test: the "
                "source workbooks report 74,851 net (Conclusiones), 99,487.50 gross (Plan de Negocio "
                "formulas) and 96,628 (deck), and the 11,297 EBITDA has no build-up.",
                "abs(revenue - 86,275) <= 1 and abs(EBITDA - 11,297) <= 1",
                prom_rev_ok and prom_ebitda_ok,
                {"revenue": float(prom_y1["total_revenue"]), "ebitda": float(prom_y1["ebitda"])},
                {"revenue": 86_275.0, "ebitda": 11_297.0},
                "Re-modelled, not replicated. README section 2 reconciles the four revenue "
                "figures and the EUR 20 vs EUR 25 restaurant ticket.",
                severity="INFO",
            ),
            self._rule(
                "RULE_14_MARKET_DSCR",
                "INE market-case minimum DSCR covenant",
                "The independent INE market case must also meet the 1.25x covenant.",
                "min(market_dscr) >= 1.25",
                funding_mkt.dscr_min >= 1.25, funding_mkt.dscr_min, 1.25,
                "At 21.24% occupancy the project does not cover debt service. Re-size the debt or add equity.",
            ),
            self._rule(
                "RULE_15_EQUITY_REQUIREMENT",
                "Cash equity requirement vs. the 30% assumption",
                "The cash equity needed to close the structure must not exceed 30% of total CapEx.",
                "cash_equity / total_capex <= 0.30",
                equity_ratio <= 0.30, round(equity_ratio, 4), 0.30,
                "The original 30% equity assumption is not financeable at 35% LTV: the structure "
                "needs ~50% cash equity plus the land in kind.",
            ),
            self._rule(
                "RULE_16_FFE_RESERVE",
                "FF&E reserve deducted from CFADS",
                "A 3% FF&E reserve must be deducted from EBITDA before debt service.",
                "ffe_reserve == 3% * revenue",
                ffe_ok, float(mgmt_y1["ffe_reserve"]),
                round(float(mgmt_y1["total_revenue"]) * 0.03, 2),
                "Book the reserve as restricted cash and deduct it from CFADS.",
                severity="INFO",
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
                "jurisdiction": "Kingdom of Spain (Castilla y Leon, Segovia)",
                "governing_statutes": [
                    "Ley 37/1992 (Impuesto sobre el Valor Anadido)",
                    "Ley 27/2014 (Impuesto sobre Sociedades)",
                    "Convenio Colectivo Provincial de Hosteleria de Segovia (BOCyL)",
                    "Instituto Nacional de Estadistica (EOTR Segovia)",
                    "Real Decreto 126/2026 (SMI 2026)",
                ],
                "schema_version": SCHEMA_VERSION,
                "framework": "Computed Model Audit & Funding-Gap Verification",
                "deterministic_output": True,
            },
            "case_summary": {
                "management": {
                    "revenue_y1": float(mgmt_y1["total_revenue"]),
                    "ebitda_y1": float(mgmt_y1["ebitda"]),
                    "cfads_y1": float(mgmt_y1["cfads"]),
                    "dscr_y1": float(mgmt_y1["dscr"]),
                    "dscr_min": funding_mgmt.dscr_min,
                    "cash_y1": float(mgmt_y1["ending_cash"]),
                    "cash_equity": funding_mgmt.cash_equity_required,
                    "total_equity": mgmt_engine.total_equity_at_close,
                    "project_irr_exit": mgmt_returns["project_irr_exit"],
                    "equity_irr_exit": mgmt_returns["equity_irr_exit"],
                    "terminal_value": mgmt_returns["terminal_value"],
                },
                "market": {
                    "revenue_y1": float(mkt_y1["total_revenue"]),
                    "ebitda_y1": float(mkt_y1["ebitda"]),
                    "cfads_y1": float(mkt_y1["cfads"]),
                    "dscr_y1": float(mkt_y1["dscr"]),
                    "dscr_min": funding_mkt.dscr_min,
                    "cash_y1": float(mkt_y1["ending_cash"]),
                    "cash_equity": funding_mkt.cash_equity_required,
                    "project_irr_exit": mkt_returns["project_irr_exit"],
                },
                "promoter": {
                    "revenue_y1": float(prom_y1["total_revenue"]),
                    "ebitda_y1": float(prom_y1["ebitda"]),
                    "cfads_y1": float(prom_y1["cfads"]),
                    "dscr_y1": float(prom_y1["dscr"]),
                    "dscr_min": funding_prom.dscr_min,
                    "cash_y1": float(prom_y1["ending_cash"]),
                    "cash_equity": funding_prom.cash_equity_required,
                },
            },
            "funding": {
                "management": asdict(funding_mgmt),
                "market": asdict(funding_mkt),
                "promoter": asdict(funding_prom),
                "phase2_gate": phase_gate,
            },
            "break_even": breakeven,
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
            print(f"  {case.upper():10s} Revenue Y1 EUR {values['revenue_y1']:>12,.2f} | "
                  f"EBITDA EUR {values['ebitda_y1']:>12,.2f} | DSCR min {values['dscr_min']:.2f}x | "
                  f"Cash equity EUR {values['cash_equity']:>12,.2f}")
        print("-" * 88)
        print("Break-even (management case):")
        be = payload["break_even"]
        print(f"  Base mature occupancy:         {be['base_occupancy_mature']}")
        print(f"  Operating break-even:          {be['operating_breakeven_occupancy_mature']}")
        print(f"  Covenant occupancy required:   {be['covenant_breakeven_occupancy_mature']}")
        print(f"  Covenant ADR required:         EUR {be['covenant_breakeven_adr']}")
        print(f"  ADR for a 10% equity IRR:      EUR {be['equity_irr_10pct_adr']}")
        print("-" * 88)
        print("Guardrail Integrity Status:")
        for r in payload["guardrail_audit_rules"]:
            flag = "[PASS]" if r["status"] == "PASSED" else "[FAIL]"
            print(f"  {flag} {r['rule_id']}: {r['rule_name']} (Actual: {r['actual_value']})")
        print("=" * 88)
