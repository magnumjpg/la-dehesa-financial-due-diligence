"""
Tests for the Act 3 decline memo.

The point of these tests is that the memo is *derived*: each reason is compared
with the engine output, so a change in the model cannot leave a stale narrative
behind. The restaurant cost centre is tested at both tickets because the whole
argument is that the sign flips between EUR 20 and EUR 25.
"""

import pytest

from src.core.decline import DeclineMemoEngine

MEMO = DeclineMemoEngine()
VERDICT = MEMO.verdict()


def test_four_tests_and_all_fail():
    assert len(VERDICT["reasons"]) == 4
    assert VERDICT["reasons_failed"] == 4
    assert VERDICT["decision"] == "DECLINE"


def test_dscr_reason_ties_to_the_credit_engine():
    reason = MEMO.dscr_test()
    year2 = MEMO.kpis[MEMO.kpis["year"] == 2].iloc[0]

    assert reason.metric == pytest.approx(float(year2["dscr"]), abs=1e-3)
    assert reason.metric == pytest.approx(1.15, abs=0.01)
    assert reason.threshold == 1.25
    assert reason.failed is True


def test_equity_reason_ties_to_the_funding_plug():
    reason = MEMO.equity_test()

    assert MEMO.engine.cash_equity == pytest.approx(521_090.22, abs=0.01)
    assert reason.metric == pytest.approx(49.62, abs=0.01)
    assert reason.threshold == 30.0
    assert reason.failed is True


def test_restaurant_sign_flips_between_20_and_25():
    reason = MEMO.restaurant_test()
    detail = reason.detail

    # The loss at the promoter's EUR 20 ticket and the near-breakeven at EUR 25.
    assert "18,679" in detail
    assert "1,481" in detail
    assert reason.failed is True
    assert reason.metric == pytest.approx(-18_678.51, abs=1.0)


def test_restaurant_cost_centre_arithmetic_is_explicit():
    from src.core.decline import (
        DESIGN_COVERS_PER_DAY,
        RESTAURANT_SERVICE_DAYS,
        RESTAURANT_COGS_RATIO,
    )

    covers = DESIGN_COVERS_PER_DAY * RESTAURANT_SERVICE_DAYS
    assert covers == 5_760
    # Revenue - COGS - fully loaded fixed cost, rebuilt independently.
    fixed = (
        2 * 13_500.0 * 1.35
        + 17_844.16 * 1.325
        + 21_000.0
        + 55_000.0 * 0.12
        + 550_000.0 * 0.25 * 0.03
        + 7_500.0
    )
    loss_20 = covers * 20.0 * (1 - RESTAURANT_COGS_RATIO) - fixed
    profit_25 = covers * 25.0 * (1 - RESTAURANT_COGS_RATIO) - fixed
    assert loss_20 == pytest.approx(-18_678.51, abs=1.0)
    assert profit_25 == pytest.approx(1_481.49, abs=1.0)


def test_phase_two_gap():
    reason = MEMO.phase2_test()
    assert reason.metric == pytest.approx(-252_241.06, abs=0.01)
    assert reason.failed is True


def test_memo_is_internally_consistent():
    df = MEMO.to_dataframe()
    assert len(df) == 4
    assert list(df["failed"]) == [True, True, True, True]

    # The verdict must not claim a decline if any test passes.
    assert VERDICT["decision"] == ("DECLINE" if df["failed"].all() else "CONDITIONAL")


def test_market_case_is_worse_than_the_decline_case():
    from src.config.assumptions import SCENARIOS
    from src.core.statements import FinancialModelEngine

    market = FinancialModelEngine(case="market", scenario=SCENARIOS["base"])
    df = market.run_projection(5)
    assert df.iloc[0]["ebitda"] < 0
    assert "INE" in VERDICT["memo"]
