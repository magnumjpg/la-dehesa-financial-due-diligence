"""
Unit tests for the Sources & Uses / funding-gap engine.

These tests deliberately assert that the model is underfunded at close. The
purpose of the funding layer is to disclose the gap, not to make it disappear.
"""

from src.core.funding import SourcesUsesEngine


def test_management_sources_uses_gap():
    f = SourcesUsesEngine(case="management").compute()

    assert f.total_uses_at_close == 948_858.18
    assert f.total_sources_at_close == 878_090.00
    assert f.funding_gap_at_close == -70_768.18
    assert f.recommended_equity_injection == 70_768.18
    assert f.recommended_debt_increase == 0.0

    # The model reports positive Year 1 cash, but the omitted close-day uses
    # turn it negative.
    assert f.cash_y1_model == 10_789.74
    assert f.cash_y1_adjusted == -55_978.44
    assert f.minimum_adjusted_cash == -55_978.44

    assert f.dscr_y1 == 1.34
    assert f.model_credit_line_drawn_y1 == 143_596.37
    assert f.credit_line_limit == 50_000.00
    assert f.credit_line_utilisation_pct == 287.19
    assert "UNDERFUNDED" in f.funding_status


def test_market_and_promoter_are_also_underfunded():
    market = SourcesUsesEngine(case="market").compute()
    promoter = SourcesUsesEngine(case="promoter").compute()

    assert market.dscr_y1 == 0.40
    assert market.cash_y1_adjusted == -96_683.54
    assert market.model_credit_line_drawn_y1 > market.credit_line_limit

    assert promoter.dscr_y1 == 0.33
    assert promoter.funding_gap_at_close == -41_925.10
    assert promoter.recommended_equity_injection == 41_925.10
    assert promoter.cash_y1_adjusted == -64_478.30
    assert promoter.model_credit_line_drawn_y1 > promoter.credit_line_limit
    assert "UNDERFUNDED" in promoter.funding_status


def test_phase_two_gate_blocks_all_cases():
    # Phase II: €359,970 net CapEx + €75,593.70 VAT.
    for case in ("management", "market", "promoter"):
        gate = SourcesUsesEngine(case=case).phase_gate(359_970.0, 75_593.70)
        assert gate["phase2_cash_need"] == 435_563.70
        assert gate["phase2_funding_gap"] < 0
        assert gate["cash_condition_met"] is False
        assert gate["phase2_proceed"] is False
        assert "DO NOT PROCEED" in gate["recommendation"]

    mgmt_gate = SourcesUsesEngine(case="management").phase_gate(359_970.0, 75_593.70)
    assert mgmt_gate["phase1_cash_end_y2"] == 193_949.95
    assert mgmt_gate["phase2_funding_gap"] == -241_613.75
    assert mgmt_gate["dscr_condition_met"] is True
