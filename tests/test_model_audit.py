"""
Unit tests for ModelAuditEngine and the computed due-diligence audit.

The audit is deliberately allowed to fail. These tests lock in the honest
result: 9 of 16 rules pass, 1 is not applicable (the promoter case has no
single source figure to reconcile), and 5 material plus 1 warning exception
remain open. If a future change fixes a material exception, update the expected
counts and the verdict rather than weakening the rule.
"""

from pathlib import Path
import json

from src.core.model_audit import ModelAuditEngine


EXPECTED_MATERIAL = {
    "RULE_05_MANAGEMENT_DSCR",
    "RULE_11_PHASE2_SELF_FUNDING",
    "RULE_12_RETURNS_VS_WACC",
    "RULE_14_MARKET_DSCR",
    "RULE_15_EQUITY_REQUIREMENT",
}
EXPECTED_WARNING = {"RULE_10_OCCUPANCY_VS_INE"}


def test_model_audit_payload_generation():
    engine = ModelAuditEngine()
    payload = engine.generate_audit_payload()

    assert {"meta", "case_summary", "funding", "break_even",
            "ground_truth_metrics", "guardrail_audit_rules",
            "execution_status"} <= set(payload)

    assert payload["meta"]["schema_version"] == "4.0.0"
    assert "Ley 37/1992" in str(payload["meta"]["governing_statutes"])
    assert "Instituto Nacional de Estad" in str(payload["meta"]["governing_statutes"])

    metrics = payload["ground_truth_metrics"]
    for key in (
        "capex_total", "capex_per_sqm", "input_vat",
        "management_revenue_y1", "management_ebitda_y1",
        "management_dscr_min", "management_cash_equity",
        "market_revenue_y1", "market_ebitda_y1",
        "promoter_revenue_y1", "promoter_ebitda_y1",
        "covenant_breakeven_occupancy", "covenant_breakeven_adr",
        "phase2_cash_need", "phase2_funding_gap",
        "project_irr_exit", "equity_irr_exit",
    ):
        assert key in metrics, f"Missing metric: {key}"

    assert metrics["capex_total"]["value"] == 1_050_100.0
    assert metrics["capex_per_sqm"]["value"] == 1_000.0
    assert metrics["input_vat"]["value"] == 168_021.0
    assert metrics["management_revenue_y1"]["value"] == 154_548.0
    assert metrics["management_ebitda_y1"]["value"] == 24_279.92
    assert metrics["management_dscr_min"]["value"] == 1.15
    assert metrics["management_cash_equity"]["value"] == 521_090.22
    assert metrics["management_equity_ratio"]["value"] == 0.4962
    assert metrics["market_ebitda_y1"]["value"] == -18_565.58
    assert metrics["promoter_revenue_y1"]["value"] == 86_275.0
    assert metrics["promoter_ebitda_y1"]["value"] == 11_297.0
    assert metrics["covenant_breakeven_occupancy"]["value"] == 0.3205
    assert metrics["covenant_breakeven_adr"]["value"] == 86.64
    assert metrics["phase2_funding_gap"]["value"] == -252_241.06
    assert metrics["project_irr_exit"]["value"] == -0.094874

    cases = payload["case_summary"]
    assert set(cases) == {"management", "market", "promoter"}
    assert cases["management"]["revenue_y1"] == 154_548.0
    assert cases["management"]["ebitda_y1"] == 24_279.92
    assert cases["management"]["cash_equity"] == 521_090.22
    assert cases["market"]["revenue_y1"] == 95_555.0
    assert cases["market"]["ebitda_y1"] == -18_565.58
    assert cases["promoter"]["revenue_y1"] == 86_275.0
    assert cases["promoter"]["ebitda_y1"] == 11_297.0
    assert cases["market"]["dscr_y1"] < 1.0
    assert cases["promoter"]["dscr_y1"] < 1.0

    # The structure closes in the realistic cases; the original promoter case
    # keeps its EUR 20k line and its liquidity gap.
    mgmt = payload["funding"]["management"]
    assert mgmt["funding_gap_at_close"] == 0.0
    assert mgmt["total_uses_at_close"] == 1_306_646.22
    assert mgmt["total_sources_at_close"] == 1_306_646.22
    assert mgmt["dscr_cap_principal"] == 339_144.92
    assert mgmt["binding_constraint"] == "DSCR"
    assert "FUNDED" in mgmt["funding_status"]

    promoter = payload["funding"]["promoter"]
    assert promoter["funding_gap_at_close"] == 20_000.0
    assert "LIQUIDITY GAP" in promoter["funding_status"]

    gate = payload["funding"]["phase2_gate"]
    assert gate["phase2_funding_gap"] == -252_241.06
    assert gate["phase2_proceed"] is False

    guardrails = payload["guardrail_audit_rules"]
    assert len(guardrails) == 16
    by_id = {g["rule_id"]: g for g in guardrails}
    assert len(by_id) == 16

    failed_material = {
        g["rule_id"] for g in guardrails
        if g["status"] == "FAILED" and g["severity"] == "MATERIAL"
    }
    failed_warning = {
        g["rule_id"] for g in guardrails
        if g["status"] == "FAILED" and g["severity"] == "WARNING"
    }
    assert failed_material == EXPECTED_MATERIAL
    assert failed_warning == EXPECTED_WARNING

    # RULE_13 must not claim a source reconciliation: it reads the source
    # cells, reports them and is marked NOT_APPLICABLE.
    rule_13 = by_id["RULE_13_PROMOTER_CALIBRATION"]
    assert rule_13["status"] == "NOT_APPLICABLE"
    assert rule_13["actual_value"]["deck_revenue_b11"] == 96_628
    assert rule_13["actual_value"]["deck_ebitda_b12"] == 11_297
    assert rule_13["actual_value"]["plan_revenue_conclusiones_b5"] == 74_851
    assert rule_13["actual_value"]["plan_revenue_formula"] == 99_487.50
    assert rule_13["actual_value"]["model_revenue"] == 86_275.0

    status = payload["execution_status"]
    assert status["all_guardrails_satisfied"] is False
    assert status["total_rules_evaluated"] == 16
    assert status["total_rules_passed"] == 9
    assert status["total_rules_failed"] == 6
    assert status["total_rules_not_applicable"] == 1
    assert status["material_exceptions"] == sorted(EXPECTED_MATERIAL)
    assert status["warning_exceptions"] == sorted(EXPECTED_WARNING)
    assert status["audit_verdict"] == "CONDITIONAL - 5 MATERIAL EXCEPTION(S)"


def test_model_audit_json_export_file(tmp_path: Path):
    engine = ModelAuditEngine(export_dir=tmp_path)
    exported_path = engine.export_json()

    assert exported_path.exists()
    assert exported_path.is_file()

    with open(exported_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["meta"]["project_name"] == "La Dehesa del Castrillo S.L."
    assert data["meta"]["schema_version"] == "4.0.0"
    assert data["execution_status"]["all_guardrails_satisfied"] is False
    assert data["execution_status"]["total_rules_passed"] == 9
    assert data["execution_status"]["total_rules_failed"] == 6
    assert data["execution_status"]["total_rules_not_applicable"] == 1
