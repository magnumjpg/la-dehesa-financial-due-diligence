"""
Tests for the occupancy bridge.

The bridge is the answer to the most obvious challenge to the model: the
management case assumes 31.36% occupancy, roughly 48% above the INE Segovia
average of 21.24%. The tests below pin down that the bridge reconciles to the
model, that it does not hide the midweek hole, and that most of the gap is
weekend capture.
"""

import pytest

from src.config.ine_weights import MANAGEMENT_OCCUPANCY, MARKET_OCCUPANCY
from src.core.demand_bridge import (
    INE_MIX,
    MANAGEMENT_MIX,
    MIDWEEK_NIGHTS,
    PEAK_NIGHTS,
    TOTAL_NIGHTS,
    WEEKEND_NIGHTS,
    build_bridge,
    solve_midweek_occupancy,
)


def test_calendar_adds_up_to_365_nights():
    assert WEEKEND_NIGHTS + PEAK_NIGHTS + MIDWEEK_NIGHTS == TOTAL_NIGHTS == 365


def test_management_mix_reconstructs_the_model_occupancy():
    assert MANAGEMENT_MIX.occupancy == pytest.approx(MANAGEMENT_OCCUPANCY, abs=1e-9)


def test_ine_mix_reconstructs_the_market_occupancy():
    assert INE_MIX.occupancy == pytest.approx(MARKET_OCCUPANCY, abs=1e-9)

    # The INE average is also weekend-weighted, but with a much weaker weekend
    # and a very thin midweek.
    assert INE_MIX.weekend_occupancy > INE_MIX.midweek_occupancy * 4
    assert MANAGEMENT_MIX.weekend_occupancy > MANAGEMENT_MIX.midweek_occupancy * 5


def test_midweek_is_the_residual_and_is_not_flattered():
    # Management midweek is only about 3 pp above the INE midweek. The story is
    # weekend capture, not a full seven-day market.
    assert MANAGEMENT_MIX.midweek_occupancy - INE_MIX.midweek_occupancy < 0.05
    assert MANAGEMENT_MIX.midweek_occupancy < 0.15


def test_gap_decomposition_ties_to_the_total_gap():
    bridge = build_bridge()
    contributions = bridge["gap_contributions_pp"]

    assert sum(contributions.values()) == pytest.approx(bridge["gap_pp"], abs=0.02)
    assert bridge["gap_pp"] == pytest.approx(10.12, abs=0.02)
    assert bridge["gap_shares"]["weekend"] > 0.60
    assert bridge["gap_shares"]["midweek"] < 0.25
    assert "weekend capture" in bridge["headline"]


def test_midweek_solver_rejects_impossible_anchors():
    with pytest.raises(ValueError):
        solve_midweek_occupancy(
            target_occupancy=0.20,
            weekend_occupancy=0.90,
            peak_occupancy=0.80,
        )
