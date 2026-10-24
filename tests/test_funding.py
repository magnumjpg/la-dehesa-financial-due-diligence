"""
Unit tests for the Sources & Uses / funding engine.

The engine books every close-day use in the three-statement model. The cash
equity is a reported plug, not a 30% assumption, and the requested facility is
tested against the DSCR cap. The promoter case keeps the original EUR 20k line,
which is why it still shows a funding gap at close.
"""

import pytest

from src.core.funding import SourcesUsesEngine


def test_management_sources_uses_close():
    f = SourcesUsesEngine(case="management").compute()

    assert f.total_capex == 1_050_100.0
    assert f.land_in_kind == 250_000.0
    assert f.cash_capex == 800_100.0
    assert f.input_vat == 168_021.0
    assert f.idc == 14_701.40
    assert f.pre_opening_costs == 35_000.0
    assert f.initial_working_capital == 25_000.0
    assert f.dsra == 13_823.82

    assert f.total_uses_at_close == pytest.approx(1_306_646.22, abs=0.01)
    assert f.total_sources_at_close == pytest.approx(1_306_646.22, abs=0.01)
    assert f.funding_gap_at_close == pytest.approx(0.0, abs=0.01)
    assert f.recommended_equity_injection == 0.0

    # The plug: 49.62% of CapEx in cash, plus the in-kind land.
    assert f.cash_equity_required == pytest.approx(521_090.22, abs=0.01)
    assert f.equity_to_capex_pct == pytest.approx(49.62, abs=0.01)
    assert f.total_equity_at_close == pytest.approx(771_090.22, abs=0.01)
    assert f.total_project_investment == pytest.approx(1_138_625.22, abs=0.01)

    # The 35% LTV facility complies with LTV but fails the DSCR cap.
    assert f.ltv_pct == 35.0
    assert f.dscr_cap_principal == pytest.approx(339_144.92, abs=0.01)
    assert f.binding_constraint == "DSCR"
    assert f.dscr_cap_ltv_pct == pytest.approx(32.3, abs=0.01)
    assert f.dscr_cap_principal < f.senior_debt

    # VAT bridge is a separate facility inside its limit; the LEADER grant is
    # post-close and cannot fund close-day uses.
    assert f.vat_bridge_drawn_y1 == 168_021.0
    assert f.vat_bridge_limit == 175_000.0
    assert f.vat_bridge_excess == 0.0
    assert f.leader_grant == 163_000.0
    assert f.credit_line_at_close == 0.0

    assert f.dscr_y1 == 1.34
    assert f.dscr_min == 1.15
    assert "FUNDED" in f.funding_status


def test_market_case_is_funded_but_below_one_x():
    f = SourcesUsesEngine(case="market").compute()

    assert f.funding_gap_at_close == pytest.approx(0.0, abs=0.01)
    assert f.cash_equity_required == pytest.approx(556_465.05, abs=0.01)
    assert f.cash_equity_buffer == pytest.approx(35_374.83, abs=0.01)
    assert f.total_uses_at_close == pytest.approx(1_342_021.05, abs=0.01)
    assert f.total_sources_at_close == pytest.approx(1_342_021.05, abs=0.01)

    # Negative CFADS means no debt can satisfy a 1.25x DSCR.
    assert f.dscr_cap_principal == 0.0
    assert f.binding_constraint == "NONE (negative CFADS)"
    assert f.dscr_y1 == -1.46
    assert f.min_cash == 15_000.00
    assert "BELOW 1.00x" in f.funding_status


def test_promoter_case_keeps_the_original_funding_gap():
    f = SourcesUsesEngine(case="promoter").compute()

    assert f.total_uses_at_close == 824_750.0
    assert f.total_sources_at_close == 844_750.0
    assert f.funding_gap_at_close == 20_000.0
    assert f.credit_line_at_close == 20_000.0
    assert f.cash_equity_required == 217_500.0
    assert f.equity_to_capex_pct == 30.0
    assert f.vat_bridge_excess == 79_750.0
    assert f.min_cash < 0
    assert "LIQUIDITY GAP" in f.funding_status


def test_phase_two_gate_blocks_all_cases():
    for case in ("management", "market", "promoter"):
        gate = SourcesUsesEngine(case=case).phase_gate(359_970.0, 75_593.70)
        assert gate["phase2_cash_need"] == pytest.approx(435_563.70, abs=0.01)
        assert gate["phase2_funding_gap"] < 0
        assert gate["cash_condition_met"] is False
        assert gate["phase2_proceed"] is False
        assert "DO NOT PROCEED" in gate["recommendation"]

    mgmt_gate = SourcesUsesEngine(case="management").phase_gate(359_970.0, 75_593.70)
    assert mgmt_gate["phase1_cash_end_y2"] == pytest.approx(183_322.64, abs=0.01)
    assert mgmt_gate["phase2_funding_gap"] == pytest.approx(-252_241.06, abs=0.01)
    # Phase I DSCR in Year 3 is 1.15x, below the 1.25x gate, so both
    # conditions fail: covenant and cash.
    assert mgmt_gate["dscr_condition_met"] is False

    promoter_gate = SourcesUsesEngine(case="promoter").phase_gate(359_970.0, 75_593.70)
    assert promoter_gate["dscr_condition_met"] is True
    assert promoter_gate["cash_condition_met"] is False
    assert promoter_gate["phase2_proceed"] is False
