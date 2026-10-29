"""
T8 turnaround engine: six modular cabins plus the caseron lodge.

The engine is a thin, opinionated wrapper around the shared three-statement
`FinancialModelEngine` (`case="turnaround"`). It does not re-implement the P&L:
it builds the T8 CapEx / financing / labour / opex structures from
`TurnaroundConfig`, runs the audited engine, and reports the two return bases
that the case study needs:

* **cash** - the sponsor's actual cheque: cash CapEx plus IDC, the arrangement
  fee, pre-opening, opening working capital and the DSRA, against cash equity.
* **all-in** - the same cash flows with the EUR 250,000 land contributed in
  kind at its opportunity value. This is the "what if the family had to buy the
  finca" view and the one that is comparable with the audited EUR 1,050,100
  project, which also carries the land.

Neither basis includes the VAT bridge as an investment: it is a pure wash
(drawn at close, refunded by AEAT in Month 18), so it belongs to working
capital financing, not to the project's capital base.
"""

from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config.assumptions import RevenueModelConfig, SCENARIOS, ScenarioDrivers
from src.config.turnaround import (
    TurnaroundConfig,
    adr_variant,
    debt_variant,
    occupancy_variant,
)
from src.core.metrics import CreditMetricsEngine
from src.core.statements import FinancialModelEngine

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class TurnaroundEngine:
    """Runs the T8 cabin case through the shared 3-statement engine."""

    def __init__(
        self,
        config: Optional[TurnaroundConfig] = None,
        scenario: Optional[ScenarioDrivers] = None,
        discount_rate: Optional[float] = None,
    ):
        self.config = config or TurnaroundConfig.base()
        self.scenario = scenario or SCENARIOS["base"]
        self.discount_rate = (
            self.config.discount_rate if discount_rate is None else discount_rate
        )

        capex = self.config.build_capex()
        financing = self.config.build_financing()

        revenue_cfg = RevenueModelConfig(
            double_rooms_count=self.config.cabins.count,
            double_room_adr=self.config.cabins.adr,
            full_house_count=1 if self.config.lodge.enabled else 0,
            full_house_adr=self.config.lodge.adr,
            guests_per_double_room=self.config.cabins.guests_per_occupied_night,
            guests_per_full_house=self.config.lodge.guests_per_occupied_night,
            apply_full_cost_stack=True,
            ota_share=self.config.opex.ota_share,
            ota_commission_rate=self.config.opex.ota_commission_rate,
            ffe_reserve_rate=self.config.opex.ffe_reserve_rate,
            amenities_per_occupied_day=0.0,
            breakfast_cost_per_guest_day=0.0,
            restaurant_average_ticket=0.0,
            restaurant_cogs_ratio=0.0,
            calibration_mode="turnaround",
        )

        self.engine = FinancialModelEngine(
            capex=capex,
            financing=financing,
            labor=self.config.build_labor(),
            opex=self.config.build_opex(),
            revenue_cfg=revenue_cfg,
            scenario=self.scenario,
            case="turnaround",
            turnaround=self.config,
        )
        self.credit = CreditMetricsEngine(
            target_dscr=financing.target_dscr,
            discount_wacc=self.discount_rate,
        )
        self._projection: Optional[pd.DataFrame] = None
        self._kpis: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # Core outputs
    # ------------------------------------------------------------------
    @property
    def projection(self) -> pd.DataFrame:
        if self._projection is None:
            self._projection = self.engine.run_projection(5)
        return self._projection

    @property
    def debt_schedule(self) -> pd.DataFrame:
        return self.engine.debt_engine.get_annual_schedule_df()

    @property
    def kpis(self) -> pd.DataFrame:
        if self._kpis is None:
            self._kpis = self.credit.compute_credit_kpis(
                self.projection, self.debt_schedule
            )
        return self._kpis

    def run_projection(self, years: int = 5) -> pd.DataFrame:
        return self.engine.run_projection(years)

    # ------------------------------------------------------------------
    # Funding identities
    # ------------------------------------------------------------------
    @property
    def cash_project_investment(self) -> float:
        """Cash CapEx plus close-day costs, excluding land and the VAT bridge."""
        fin = self.engine.financing
        return round(
            self.engine.cash_capex
            + fin.idc_amount
            + fin.arrangement_fee
            + fin.pre_opening_costs
            + fin.initial_working_capital
            + self.engine.dsra_amount,
            2,
        )

    @property
    def all_in_project_investment(self) -> float:
        return float(self.engine.total_project_investment)

    @property
    def cash_equity(self) -> float:
        return float(self.engine.cash_equity)

    @property
    def all_in_equity(self) -> float:
        return float(self.engine.total_equity_at_close)

    @property
    def use_of_funds(self) -> Dict[str, float]:
        """A sources & uses table for the T8 structure."""
        fin = self.engine.financing
        uses = {
            "cash_capex": self.engine.cash_capex,
            "idc": round(float(fin.idc_amount), 2),
            "arrangement_fee": round(float(fin.arrangement_fee), 2),
            "input_vat_bridge": round(float(self.engine.capex.total_input_vat), 2),
            "pre_opening": round(float(fin.pre_opening_costs), 2),
            "working_capital": round(float(fin.initial_working_capital), 2),
            "dsra": round(float(self.engine.dsra_amount), 2),
        }
        sources = {
            "senior_debt": round(float(fin.senior_debt_principal), 2),
            "vat_bridge": round(float(self.engine.capex.total_input_vat), 2),
            "cash_equity": self.cash_equity,
            "land_in_kind": round(float(fin.land_in_kind_value), 2),
        }
        return {
            "uses": uses,
            "sources": sources,
            "total_uses": round(sum(uses.values()), 2),
            "total_cash_sources": round(
                sources["senior_debt"] + sources["vat_bridge"] + sources["cash_equity"],
                2,
            ),
            "total_sources": round(sum(sources.values()), 2),
        }

    # ------------------------------------------------------------------
    # Returns
    # ------------------------------------------------------------------
    def returns(
        self,
        basis: str = "all-in",
        exit_cap_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Project and equity IRR on the cash or all-in capital base."""
        if basis not in ("cash", "all-in"):
            raise ValueError("basis must be 'cash' or 'all-in'")
        cap = self.config.exit_cap_rate if exit_cap_rate is None else exit_cap_rate
        initial_capex = (
            self.cash_project_investment if basis == "cash" else self.all_in_project_investment
        )
        initial_equity = self.cash_equity if basis == "cash" else self.all_in_equity
        result = self.credit.compute_returns_summary(
            self.projection,
            initial_equity=initial_equity,
            initial_capex=initial_capex,
            exit_cap_rate=cap,
            exit_cost_rate=self.config.exit_cost_rate,
        )
        result["basis"] = basis
        result["initial_capex"] = round(initial_capex, 2)
        result["initial_equity"] = round(initial_equity, 2)
        result["equity_to_capex_pct"] = round(
            initial_equity / initial_capex * 100.0, 2
        )
        return result

    def returns_table(self) -> pd.DataFrame:
        """Both bases side by side, as used in the Excel and the README."""
        rows: List[Dict[str, Any]] = []
        for basis in ("all-in", "cash"):
            r = self.returns(basis)
            rows.append(
                {
                    "basis": basis,
                    "initial_capex": r["initial_capex"],
                    "initial_equity": r["initial_equity"],
                    "project_irr": r["project_irr"],
                    "project_irr_exit": r["project_irr_exit"],
                    "equity_irr_exit": r["equity_irr_exit"],
                    "project_npv": r["project_npv"],
                    "equity_npv": r["equity_npv"],
                    "project_moic": r["project_moic"],
                    "equity_moic": r["equity_moic"],
                    "terminal_value": r["terminal_value"],
                    "net_terminal_value": r["net_terminal_value"],
                }
            )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Sensitivity grid
    # ------------------------------------------------------------------
    def _row(self, label: str, engine: "TurnaroundEngine") -> Dict[str, Any]:
        proj = engine.projection
        mature = proj.iloc[2]
        r_all = engine.returns("all-in")
        r_cash = engine.returns("cash")
        return {
            "scenario": label,
            "revenue_y3": round(float(mature["total_revenue"]), 2),
            "ebitda_y3": round(float(mature["ebitda"]), 2),
            "ebitda_margin": round(float(mature["ebitda"] / mature["total_revenue"]), 4),
            "min_dscr": round(float(engine.kpis["dscr"].min()), 3),
            "cash_equity": round(engine.cash_equity, 2),
            "project_irr_allin": r_all["project_irr_exit"],
            "project_irr_cash": r_cash["project_irr_exit"],
            "equity_irr_allin": r_all["equity_irr_exit"],
            "equity_irr_cash": r_cash["equity_irr_exit"],
            "net_exit": r_all["net_terminal_value"],
        }

    def sensitivities(self) -> pd.DataFrame:
        """Exit-cap, demand, leverage and scope sensitivities for Act 5."""
        rows: List[Dict[str, Any]] = [self._row("Base", self)]

        for cap in (0.09, 0.095, 0.105):
            r_all = self.returns("all-in", exit_cap_rate=cap)
            r_cash = self.returns("cash", exit_cap_rate=cap)
            proj = self.projection
            rows.append(
                {
                    "scenario": f"Exit cap {cap:.1%}",
                    "revenue_y3": round(float(proj.iloc[2]["total_revenue"]), 2),
                    "ebitda_y3": round(float(proj.iloc[2]["ebitda"]), 2),
                    "ebitda_margin": round(
                        float(proj.iloc[2]["ebitda"] / proj.iloc[2]["total_revenue"]), 4
                    ),
                    "min_dscr": round(float(self.kpis["dscr"].min()), 3),
                    "cash_equity": round(self.cash_equity, 2),
                    "project_irr_allin": r_all["project_irr_exit"],
                    "project_irr_cash": r_cash["project_irr_exit"],
                    "equity_irr_allin": r_all["equity_irr_exit"],
                    "equity_irr_cash": r_cash["equity_irr_exit"],
                    "net_exit": r_all["net_terminal_value"],
                }
            )

        variants = [
            ("ADR -10%", adr_variant(-0.10)),
            ("ADR +10%", adr_variant(0.10)),
            ("Occupancy 45%", occupancy_variant(0.45)),
            ("Occupancy 50%", occupancy_variant(0.50)),
            ("Occupancy 55%", occupancy_variant(0.55)),
            ("Debt EUR 400k", debt_variant(400_000)),
            ("Debt EUR 425k", debt_variant(425_000)),
            ("Cabins only (no lodge)", TurnaroundConfig.cabins_only()),
        ]
        for label, cfg in variants:
            rows.append(self._row(label, TurnaroundEngine(cfg, self.scenario, self.discount_rate)))

        df = pd.DataFrame(rows)
        for col in ("project_irr_allin", "project_irr_cash", "equity_irr_allin", "equity_irr_cash"):
            df[col] = df[col].round(4)
        return df

    def variants(self) -> pd.DataFrame:
        """Base vs cabins-only: the honesty check on the lodge."""
        base = self._row("6 cabins + caseron lodge", self)
        cabins_only = self._row(
            "6 cabins only", TurnaroundEngine(TurnaroundConfig.cabins_only(), self.scenario)
        )
        return pd.DataFrame([base, cabins_only])

    # ------------------------------------------------------------------
    # Summary / export
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        proj = self.projection
        kpis = self.kpis
        r_all = self.returns("all-in")
        r_cash = self.returns("cash")
        mature = proj.iloc[2]  # Year 3 = first fully stabilised year
        year1 = proj.iloc[0]
        year2 = proj.iloc[1]
        exit_year = proj.iloc[-1]

        return {
            "config": self.config.to_dict(),
            "capital": {
                "cash_capex": round(self.engine.cash_capex, 2),
                "all_in_capex": round(self.engine.capex.total_capex, 2),
                "land_in_kind": round(self.engine.financing.land_in_kind_value, 2),
                "input_vat": round(self.engine.capex.total_input_vat, 2),
                "senior_debt": round(self.engine.financing.senior_debt_principal, 2),
                "idc": round(self.engine.financing.idc_amount, 2),
                "arrangement_fee": round(self.engine.financing.arrangement_fee, 2),
                "dsra": round(self.engine.dsra_amount, 2),
                "cash_project_investment": self.cash_project_investment,
                "all_in_project_investment": self.all_in_project_investment,
                "cash_equity": self.cash_equity,
                "all_in_equity": self.all_in_equity,
                "equity_to_cash_capex_pct": round(
                    self.cash_equity / self.engine.cash_capex * 100.0, 2
                ),
                "equity_to_all_in_capex_pct": round(
                    self.cash_equity / self.engine.capex.total_capex * 100.0, 2
                ),
            },
            "operating": {
                "revenue_y1": round(float(year1["total_revenue"]), 2),
                "revenue_y2": round(float(year2["total_revenue"]), 2),
                "revenue_mature": round(float(mature["total_revenue"]), 2),
                "gross_margin_pct": round(
                    float(mature["gross_margin"] / mature["total_revenue"]), 4
                ),
                "ebitda_y1": round(float(year1["ebitda"]), 2),
                "ebitda_y2": round(float(year2["ebitda"]), 2),
                "ebitda_mature": round(float(mature["ebitda"]), 2),
                "ebitda_margin_pct": round(
                    float(mature["ebitda"] / mature["total_revenue"]), 4
                ),
                "payroll": round(self.engine.labor.total_annual_payroll, 2),
                "fixed_opex": round(self.engine.opex.total_fixed_opex, 2),
                "ffe_reserve_y3": round(float(mature["ffe_reserve"]), 2),
            },
            "credit": {
                "dscr_y1": round(float(kpis.iloc[0]["dscr"]), 3),
                "dscr_y2": round(float(kpis.iloc[1]["dscr"]), 3),
                "min_dscr": round(float(kpis["dscr"].min()), 3),
                "min_cash": round(float(proj["ending_cash"].min()), 2),
                "covenant_pass": bool(kpis["dscr_covenant_pass"].all()),
                "max_debt_service": round(float(proj["debt_service"].max()), 2),
            },
            "returns": {
                "all_in": {
                    "project_irr": r_all["project_irr_exit"],
                    "equity_irr": r_all["equity_irr_exit"],
                    "project_npv": r_all["project_npv"],
                    "equity_npv": r_all["equity_npv"],
                    "project_moic": r_all["project_moic"],
                    "equity_moic": r_all["equity_moic"],
                    "terminal_value": r_all["terminal_value"],
                    "net_terminal_value": r_all["net_terminal_value"],
                },
                "cash": {
                    "project_irr": r_cash["project_irr_exit"],
                    "equity_irr": r_cash["equity_irr_exit"],
                    "project_npv": r_cash["project_npv"],
                    "equity_npv": r_cash["equity_npv"],
                    "project_moic": r_cash["project_moic"],
                    "equity_moic": r_cash["equity_moic"],
                },
                "exit_cap_rate": self.config.exit_cap_rate,
                "exit_cost_rate": self.config.exit_cost_rate,
                "discount_rate": self.discount_rate,
                "value_gap_vs_all_in_capex": round(
                    r_all["net_terminal_value"] - self.engine.capex.total_capex, 2
                ),
                "value_gap_vs_cash_capex": round(
                    r_all["net_terminal_value"] - self.engine.cash_capex, 2
                ),
                "value_gap_vs_all_in_investment": round(
                    r_all["net_terminal_value"] - self.all_in_project_investment, 2
                ),
            },
            "exit_year_ebitda": round(float(exit_year["ebitda"]), 2),
            "exit_year_debt": round(float(exit_year["total_debt"]), 2),
        }

    def export_json(self, path: Optional[Path] = None) -> Path:
        import json

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        target = Path(path) if path else DATA_DIR / "turnaround_analysis.json"
        payload = self.summary()
        payload["sensitivities"] = self.sensitivities().to_dict(orient="records")
        payload["variants"] = self.variants().to_dict(orient="records")
        payload["returns_table"] = self.returns_table().to_dict(orient="records")
        target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return target

    # ------------------------------------------------------------------
    # Terminal summary
    # ------------------------------------------------------------------
    def print_terminal_summary(self) -> None:
        s = self.summary()
        proj = self.projection
        print("=" * 96)
        print(" ACT 4 - T8 CABIN TURNAROUND: 6 MODULAR CABINS + CASERON LODGE")
        print("=" * 96)
        print(
            f"Product:                          {s['config']['summary']['keys']} keys, "
            f"{s['config']['summary']['guests_at_full_occupancy']} guests, no commercial restaurant"
        )
        print(
            f"Cash CapEx:                       EUR {s['capital']['cash_capex']:>12,.2f}   "
            f"(land in kind EUR {s['capital']['land_in_kind']:,.0f})"
        )
        print(
            f"All-in CapEx:                     EUR {s['capital']['all_in_capex']:>12,.2f}   "
            f"({s['capital']['all_in_capex'] / 1_050_100 - 1:+.1%} vs audited EUR 1,050,100)"
        )
        print(
            f"Installed cost per cabin:         EUR {s['config']['summary']['installed_cost_per_cabin']:>12,.2f}   "
            f"(module EUR {self.config.cabins.unit_cost:,.0f})"
        )
        print(
            f"Senior debt / cash equity:        EUR {s['capital']['senior_debt']:>12,.2f} / "
            f"EUR {s['capital']['cash_equity']:,.2f} "
            f"({s['capital']['equity_to_cash_capex_pct']:.1f}% of cash CapEx)"
        )
        print(f"Total uses at close:              EUR {self.use_of_funds['total_uses']:>12,.2f}")
        print("-" * 96)
        print(
            f"{'Year':<5}{'Revenue':>12}{'GM %':>8}{'EBITDA':>12}{'EBITDA %':>10}"
            f"{'CFADS':>12}{'DSCR':>8}{'Cash':>12}"
        )
        for _, row in proj.iterrows():
            dscr = float(self.kpis.loc[self.kpis["year"] == row["year"], "dscr"].iloc[0])
            print(
                f"{int(row['year']):<5}{row['total_revenue']:>12,.0f}"
                f"{row['gross_margin'] / row['total_revenue']:>7.1%}"
                f"{row['ebitda']:>12,.0f}"
                f"{row['ebitda'] / row['total_revenue']:>9.1%}"
                f"{row['cfads']:>12,.0f}{dscr:>7.2f}x{row['ending_cash']:>12,.0f}"
            )
        print("-" * 96)
        print(
            f"Minimum DSCR:                     {s['credit']['min_dscr']:.2f}x   "
            f"(covenant 1.25x, headroom {s['credit']['min_dscr'] - 1.25:.2f}x)"
        )
        print(
            f"Exit value @ {self.config.exit_cap_rate:.1%} cap:            "
            f"EUR {s['returns']['all_in']['terminal_value']:>12,.2f} gross / "
            f"EUR {s['returns']['all_in']['net_terminal_value']:,.2f} net of 3% costs"
        )
        print(
            f"Project IRR (all-in / cash):      {s['returns']['all_in']['project_irr']:>8.2%} / "
            f"{s['returns']['cash']['project_irr']:.2%}"
        )
        print(
            f"Equity IRR  (all-in / cash):      {s['returns']['all_in']['equity_irr']:>8.2%} / "
            f"{s['returns']['cash']['equity_irr']:.2%}"
        )
        print(
            f"Value gap vs all-in CapEx:        EUR {s['returns']['value_gap_vs_all_in_capex']:>12,.2f}"
        )
        print("=" * 96)
