"""
Unit tests for ModelAuditEngine and the computed due-diligence audit.

The audit is deliberately allowed to fail. These tests lock in the honest
result: 8 of 14 rules pass, 5 material exceptions and 1 warning remain open.
If a future change fixes a material exception, update the expected counts and
the verdict rather than weakening the rule.
"""

from pathlib import Path
import json

from src.core.model_audit import ModelAuditEngine


EXPECTED_MATERIAL = {
    "RULE_06_ADJUSTED_CASH_TROUGH",
    "RULE_08_SOURCES_USES_CLOSE",
    "RULE_09_CREDIT_LINE_LIMIT",
    "RULE_11_PHASE2_SELF_FUNDING",
    "RULE_14_MARKET_DSCR",
}
EXPECTED_WARNING = {"RULE_10_OCCUPANCY_VS_INE"}


def test_model_audit_payload_generation():
    engine = ModelAuditEngine()
    payload = engine.generate_audit_payload()

    assert {"meta", "case_summary", "funding", "ground_truth_metrics",
            "guardrail_audit_rules", "execution_status"} <= set(payload)

    # Meta checks
    assert payload["meta"]["schema_version"] == "3.0.0"
    assert "Ley 37/1992" in str(payload["meta"]["governing_statutes"])
    assert "Instituto Nacional de Estad" in str(payload["meta"]["governing_statutes"])

    # Metrics count and required keys
    metrics = payload["ground_truth_metrics"]
    for key in (
        "capex_total", "management_revenue_y1", "management_ebitda_y1",
        "management_dscr_y1", "market_revenue_y1", "market_dscr_y1",
        "promoter_revenue_y1", "funding_gap_close", "credit_line_drawn_y1",
        "phase2_cash_need", "phase2_funding_gap", "project_irr_exit",
        "equity_irr_exit",
    ):
        assert key in metrics, f"Missing metric: {key}"

    assert metrics["capex_total"]["value"] == 729_000.0
    assert metrics["management_revenue_y1"]["value"] == 154_548.0
    assert metrics["management_ebitda_y1"]["value"] == 66_086.46
    assert metrics["management_dscr_y1"]["value"] >= 1.25
    assert metrics["funding_gap_close"]["value"] == -70_768.18
    assert metrics["credit_line_drawn_y1"]["value"] == 143_596.37
    assert metrics["phase2_funding_gap"]["value"] == -241_613.75

    # Three cases
    cases = payload["case_summary"]
    assert set(cases) == {"management", "market", "promoter"}
    assert cases["management"]["revenue_y1"] == 154_548.0
    assert cases["management"]["ebitda_y1"] == 66_086.46
    assert cases["market"]["revenue_y1"] == 95_555.0
    assert cases["promoter"]["revenue_y1"] == 86_275.0
    assert cases["promoter"]["ebitda_y1"] == 11_297.0
    assert cases["market"]["dscr_y1"] < 1.0
    assert cases["promoter"]["dscr_y1"] < 1.0

    # Funding gap is disclosed, not hidden
    mgmt = payload["funding"]["management"]
    assert mgmt["funding_gap_at_close"] == -70_768.18
    assert mgmt["cash_y1_adjusted"] == -55_978.44
    assert mgmt["model_credit_line_drawn_y1"] == 143_596.37
    assert mgmt["credit_line_limit"] == 50_000.0
    assert "UNDERFUNDED" in mgmt["funding_status"]

    # Phase II gate is negative
    gate = payload["funding"]["phase2_gate"]
    assert gate["phase2_funding_gap"] == -241_613.75
    assert gate["phase2_proceed"] is False

    # Guardrails: 14 rules, 8 pass, 5 material + 1 warning fail
    guardrails = payload["guardrail_audit_rules"]
    assert len(guardrails) == 14
    by_id = {g["rule_id"]: g for g in guardrails}
    assert len(by_id) == 14

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

    status = payload["execution_status"]
    assert status["all_guardrails_satisfied"] is False
    assert status["total_rules_evaluated"] == 14
    assert status["total_rules_passed"] == 8
    assert status["total_rules_failed"] == 6
    assert status["material_exceptions"] == sorted(EXPECTED_MATERIAL)
    assert status["warning_exceptions"] == sorted(EXPECTED_WARNING)
    assert status["audit_verdict"].startswith("CONDITIONAL")
    assert "5 MATERIAL EXCEPTION" in status["audit_verdict"]


def test_model_audit_json_export_file(tmp_path: Path):
    engine = ModelAuditEngine(export_dir=tmp_path)
    exported_path = engine.export_json()

    assert exported_path.exists()
    assert exported_path.is_file()

    with open(exported_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["meta"]["project_name"] == "La Dehesa del Castrillo S.L."
    assert data["meta"]["schema_version"] == "3.0.0"
    assert data["execution_status"]["all_guardrails_satisfied"] is False
    assert data["execution_status"]["total_rules_passed"] == 8
    assert data["execution_status"]["total_rules_failed"] == 6
