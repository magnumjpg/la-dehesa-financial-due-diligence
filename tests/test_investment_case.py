"""
Tests for the Act 5 executive comparison.

The comparison is only trustworthy if every column is produced by its own
engine and the value bridge ties. These tests also lock the direction of the
story: T8 must beat the audited case on EBITDA, DSCR and equity IRR while using
less capital.
"""

import pytest

from src.core.investment_case import InvestmentCase

CASE = InvestmentCase()
SNAPSHOTS = {s.key: s for s in CASE.snapshots()}


def test_three_columns_with_the_expected_identity():
    assert set(SNAPSHOTS) == {"promoter", "audited", "turnaround"}
    assert SNAPSHOTS["promoter"].all_in_capex == pytest.approx(725_000.0)
    assert SNAPSHOTS["audited"].all_in_capex == pytest.approx(1_050_100.0)
    assert SNAPSHOTS["turnaround"].all_in_capex == pytest.approx(871_600.0)


def test_turnaround_uses_less_capital_and_earns_more():
    audited = SNAPSHOTS["audited"]
    t8 = SNAPSHOTS["turnaround"]

    assert t8.all_in_capex < audited.all_in_capex
    assert t8.cash_capex < audited.cash_capex
    assert t8.ebitda_mature > audited.ebitda_mature
    assert t8.dscr_min > audited.dscr_min
    assert t8.equity_irr_allin > audited.equity_irr_allin
    assert t8.equity_pct_allin < audited.equity_pct_allin


def test_promoter_case_is_flagged_as_unfundable():
    promoter = SNAPSHOTS["promoter"]
    assert promoter.verdict == "UNFUNDABLE"
    assert promoter.dscr_min < 1.0
    assert "artefact" in promoter.caveat.lower()
    assert promoter.gross_margin == pytest.approx(1.0, abs=1e-9)


def test_audited_case_fails_the_covenant():
    audited = SNAPSHOTS["audited"]
    assert audited.verdict == "DECLINE"
    assert audited.dscr_min == pytest.approx(1.15, abs=0.01)
    assert audited.dscr_min < 1.25
    assert audited.cash_equity == pytest.approx(521_090.22, abs=0.01)


def test_comparison_table_shape_and_monotonicity():
    df = CASE.comparison_table()
    assert df.shape == (24, 3)
    assert list(df.columns) == [
        "Promoter plan",
        "Audited case",
        "Cabin turnaround (T8)",
    ]

    assert df.loc["Revenue Year 1 (EUR)", "Cabin turnaround (T8)"] > df.loc[
        "Revenue Year 1 (EUR)", "Audited case"
    ]
    assert df.loc["All-in CapEx (EUR)", "Cabin turnaround (T8)"] < df.loc[
        "All-in CapEx (EUR)", "Audited case"
    ]


def test_value_bridge_ties_to_net_exit():
    bridge = CASE.value_bridge()
    assert len(bridge) == 3
    for _, row in bridge.iterrows():
        expected = row["gross_terminal_value"] * 0.97
        assert row["net_terminal_value"] == pytest.approx(expected, abs=0.01)
        assert row["value_gap_vs_capex"] == pytest.approx(
            row["net_terminal_value"] - row["all_in_capex"], abs=0.01
        )

    t8 = bridge[bridge["case"] == "Cabin turnaround (T8)"].iloc[0]
    assert t8["value_gap_vs_capex"] == pytest.approx(385_869.20, abs=0.01)


def test_narrative_covers_all_five_acts():
    narrative = CASE.narrative()
    assert list(narrative) == [
        "act_1_pitch",
        "act_2_audit",
        "act_3_decline",
        "act_4_turnaround",
        "act_5_comparison",
    ]
    assert "EUR 725,000" in narrative["act_1_pitch"]
    assert "DECLINE" in narrative["act_3_decline"] or "declines" in narrative["act_3_decline"]
    assert "93,600" in narrative["act_4_turnaround"]


def test_formatted_table_is_display_ready():
    formatted = CASE.formatted_table()
    assert formatted.loc["Mature occupancy", "Cabin turnaround (T8)"] == "55.4%"
    assert formatted.loc["Minimum DSCR (x)", "Audited case"] == "1.15x"
    assert formatted.loc["All-in CapEx (EUR)", "Cabin turnaround (T8)"] == "871,600"
