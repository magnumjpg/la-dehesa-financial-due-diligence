"""
Unit tests for ModelAuditEngine and programmatic due diligence audit guardrails.
"""

from pathlib import Path
import json
import pytest
from src.core.model_audit import ModelAuditEngine


def test_model_audit_payload_generation():
    engine = ModelAuditEngine()
    payload = engine.generate_audit_payload()

    assert "meta" in payload
    assert "ground_truth_metrics" in payload
    assert "guardrail_audit_rules" in payload
    assert "execution_status" in payload

    # Meta checks
    assert payload["meta"]["schema_version"] == "2.1.0"
    assert "Ley 37/1992" in str(payload["meta"]["governing_statutes"])

    # Metrics count and required keys
    metrics = payload["ground_truth_metrics"]
    assert "capex_total" in metrics
    assert "year1_revenue" in metrics
    assert "year1_ebitda" in metrics
    assert "year1_dscr" in metrics
    assert "revpar_year1" in metrics
    assert "trevpar_year1" in metrics
    assert "unit_contribution_margin_eur" in metrics
    assert "recommended_dsra_sizing" in metrics

    assert metrics["capex_total"]["value"] == 729_000.0
    assert metrics["senior_debt_principal"]["value"] == 507_500.0
    assert metrics["sponsor_equity"]["value"] == 217_500.0
    assert metrics["year1_dscr"]["value"] >= 1.25

    # Guardrails checks
    guardrails = payload["guardrail_audit_rules"]
    assert len(guardrails) >= 7

    for g in guardrails:
        assert g["status"] == "PASSED", f"Guardrail failed: {g['rule_id']}"

    assert payload["execution_status"]["all_guardrails_satisfied"] is True
    assert payload["execution_status"]["total_rules_failed"] == 0


def test_model_audit_json_export_file(tmp_path: Path):
    engine = ModelAuditEngine(export_dir=tmp_path)
    exported_path = engine.export_json()

    assert exported_path.exists()
    assert exported_path.is_file()

    with open(exported_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["meta"]["project_name"] == "La Dehesa del Castrillo S.L."
    assert data["execution_status"]["all_guardrails_satisfied"] is True
