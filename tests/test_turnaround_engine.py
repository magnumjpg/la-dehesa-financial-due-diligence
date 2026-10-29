"""
Tests for the T8 turnaround engine and its two return bases.

The assertions are anchored to the driver arithmetic (not to a stored answer
sheet): revenue is rebuilt from nights x ADR, the variable stack from the
per-night and per-guest rates, and the capital structure from the uses table.
"""

import pytest

from dataclasses import replace

from src.config.turnaround import TurnaroundConfig, occupancy_variant
from src.core.turnaround import TurnaroundEngine

T8 = TurnaroundEngine()


def test_balance_sheet_balances_every_year():
    df = T8.projection
    assert (df["balance_sheet_discrepancy"].abs() < 0.01).all()


def test_revenue_is_rebuilt_from_nights_and_adr():
    cabins = T8.config.cabins
    lodge = T8.config.lodge

    cabin_nights_y1 = 0.50 * 365 * cabins.count
    lodge_nights_y1 = 0.32 * 365
    expected_y1 = (
        cabin_nights_y1 * cabins.adr
        + lodge_nights_y1 * lodge.adr
        + T8.config.opex.experiences_for_year(1)
    )
    assert T8.projection.iloc[0]["total_revenue"] == pytest.approx(expected_y1, abs=0.01)

    cabin_nights_y3 = 0.58 * 365 * cabins.count
    lodge_nights_y3 = 0.40 * 365
    expected_y3 = (
        cabin_nights_y3 * cabins.adr
        + lodge_nights_y3 * lodge.adr
        + T8.config.opex.experiences_for_year(3)
    )
    assert T8.projection.iloc[2]["total_revenue"] == pytest.approx(expected_y3, abs=0.01)


def test_variable_cost_stack_is_built_line_by_line():
    row = T8.projection.iloc[0]
    cfg = T8.config
    lodge_nights = 0.32 * 365
    cabin_nights = 0.50 * 365 * cfg.cabins.count
    guests = (
        cabin_nights * cfg.cabins.guests_per_occupied_night
        + lodge_nights * cfg.lodge.guests_per_occupied_night
    )
    lodging = cabin_nights * cfg.cabins.adr + lodge_nights * cfg.lodge.adr

    assert row["ota_commission"] == pytest.approx(
        lodging * cfg.opex.ota_share * cfg.opex.ota_commission_rate, abs=0.01
    )
    assert row["housekeeping"] == pytest.approx(
        cabin_nights * cfg.cabins.housekeeping_per_night
        + lodge_nights * cfg.lodge.housekeeping_per_night,
        abs=0.01,
    )
    assert row["breakfast_cost"] == pytest.approx(
        guests * cfg.opex.breakfast_per_guest_day, abs=0.01
    )
    assert row["energy"] == pytest.approx(
        cabin_nights * cfg.cabins.energy_per_night
        + lodge_nights * cfg.lodge.energy_per_night,
        abs=0.01,
    )
    assert row["experience_cogs"] == pytest.approx(
        cfg.opex.experiences_for_year(1) * (1 - cfg.opex.experience_margin),
        abs=0.01,
    )
    assert row["cogs_restaurant"] == 0.0
    assert row["revenue_restaurant"] == 0.0


def test_margins_and_ebitda_targets():
    df = T8.projection
    assert (df["gross_margin"] / df["total_revenue"]).iloc[2] == pytest.approx(
        0.581, abs=0.005
    )
    assert df.iloc[0]["ebitda"] == pytest.approx(78_943.11, abs=1.0)
    assert df.iloc[2]["ebitda"] == pytest.approx(110_190.60, abs=1.0)
    assert df.iloc[2]["ebitda"] / df.iloc[2]["total_revenue"] == pytest.approx(
        0.308, abs=0.005
    )


def test_capital_structure_identity():
    uses = T8.use_of_funds
    assert uses["total_uses"] == pytest.approx(833_040.82, abs=0.01)
    assert uses["total_cash_sources"] == pytest.approx(833_040.82, abs=0.01)
    assert uses["sources"]["senior_debt"] == pytest.approx(450_000.0)
    assert uses["sources"]["vat_bridge"] == pytest.approx(130_536.0)
    assert uses["sources"]["cash_equity"] == pytest.approx(252_504.82, abs=0.01)
    assert T8.cash_equity / T8.engine.cash_capex == pytest.approx(0.406, abs=0.002)


def test_project_investment_excludes_the_vat_bridge():
    assert T8.cash_project_investment == pytest.approx(
        621_600 + 19_125 + 4_500 + 25_000 + 15_000 + 17_279.82, abs=0.05
    )
    assert T8.all_in_project_investment == pytest.approx(952_504.82, abs=0.05)
    assert T8.all_in_project_investment - T8.cash_project_investment == pytest.approx(
        250_000.0
    )


def test_covenant_headroom():
    kpis = T8.kpis
    assert kpis["dscr"].min() == pytest.approx(2.31, abs=0.05)
    assert (kpis["dscr"] >= 1.80).all()
    assert kpis["dscr_covenant_pass"].all()


def test_returns_on_both_bases():
    all_in = T8.returns("all-in")
    cash = T8.returns("cash")

    assert all_in["equity_irr_exit"] == pytest.approx(0.1895, abs=0.005)
    assert cash["equity_irr_exit"] == pytest.approx(0.3974, abs=0.005)
    assert all_in["project_irr_exit"] == pytest.approx(0.1260, abs=0.005)
    assert cash["project_irr_exit"] == pytest.approx(0.2070, abs=0.005)

    # The cash base is always the higher return because it excludes the land.
    assert cash["equity_irr_exit"] > all_in["equity_irr_exit"]
    assert cash["project_irr_exit"] > all_in["project_irr_exit"]
    assert all_in["project_npv"] > 0
    assert all_in["equity_npv"] > 0


def test_exit_costs_are_deducted():
    gross = T8.returns("all-in")["terminal_value"]
    net = T8.returns("all-in")["net_terminal_value"]
    assert net == pytest.approx(gross * (1 - T8.config.exit_cost_rate), abs=0.01)


def test_value_gap_identity():
    summary = T8.summary()
    net_exit = summary["returns"]["all_in"]["net_terminal_value"]
    assert summary["returns"]["value_gap_vs_all_in_capex"] == pytest.approx(
        net_exit - summary["capital"]["all_in_capex"], abs=0.01
    )
    assert summary["returns"]["value_gap_vs_cash_capex"] == pytest.approx(
        net_exit - summary["capital"]["cash_capex"], abs=0.01
    )


def test_cabins_only_is_bankable_but_not_attractive():
    df = T8.variants()
    base = df.iloc[0]
    cabins_only = df.iloc[1]

    assert cabins_only["ebitda_y3"] < base["ebitda_y3"]
    assert cabins_only["min_dscr"] >= 1.25
    assert cabins_only["equity_irr_allin"] < base["equity_irr_allin"]
    assert cabins_only["equity_irr_allin"] < 0.12


def test_decay_in_exit_cap_reduces_returns():
    base = T8.returns("all-in")["equity_irr_exit"]
    stressed = T8.returns("all-in", exit_cap_rate=0.095)["equity_irr_exit"]
    assert stressed < base


def test_lower_occupancy_still_clears_the_covenant_but_not_the_hurdle():
    stressed = TurnaroundEngine(occupancy_variant(0.45))
    assert stressed.kpis["dscr"].min() >= 1.25
    assert stressed.returns("all-in")["equity_irr_exit"] < 0.10


def test_cabin_cost_corridor_drives_the_net_test():
    """The documented €85k / €110k cabin stress is a model output, not a footnote."""
    base = TurnaroundConfig.base()

    def engine_at(unit_cost: float) -> TurnaroundEngine:
        cfg = replace(
            base,
            cabins=replace(base.cabins, unit_cost=unit_cost),
            capex=replace(base.capex, cabins=6.0 * unit_cost),
        )
        return TurnaroundEngine(cfg)

    at_85k = engine_at(85_000.0)
    at_110k = engine_at(110_000.0)

    gap_85k = at_85k.returns("all-in")["net_terminal_value"] - at_85k.all_in_project_investment
    gap_110k = (
        at_110k.returns("all-in")["net_terminal_value"] - at_110k.all_in_project_investment
    )

    # The covenant still passes at both points: the cost, not the DSCR, is the binding test.
    assert at_85k.kpis["dscr"].min() >= 1.25
    assert at_110k.kpis["dscr"].min() >= 1.25

    # At the bottom of the benchmark band the case creates value but misses 9% all-in;
    # at the top of the band the net value gap turns negative.
    assert 130_000 < gap_85k < 150_000
    assert at_85k.returns("all-in")["project_irr_exit"] < 0.09
    assert -40_000 < gap_110k < -20_000
