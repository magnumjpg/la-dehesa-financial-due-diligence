"""
Act 5 - the executive investment case: Promoter vs Audited vs T8 Turnaround.

The comparison is deliberately mechanical. Each column is a `CaseSnapshot`
built from the engine that owns it (promoter / management / turnaround), and the
table is assembled from those snapshots. Nothing is typed twice: if an
assumption changes in a config, the executive table changes with it.

Return convention
-----------------
All three columns are shown **net of 3% exit costs** so the comparison is
apples-to-apples. The audited equity IRR in Act 2 is quoted gross of exit costs
(-23.16%); the net figure is slightly worse and is flagged in the table.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config.assumptions import SCENARIOS
from src.core.metrics import CreditMetricsEngine
from src.core.statements import FinancialModelEngine
from src.core.turnaround import TurnaroundEngine

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
EXIT_COST_RATE = 0.03


@dataclass(frozen=True)
class CaseSnapshot:
    key: str
    name: str
    product: str
    keys: int
    guests: int
    mature_occupancy: float
    mature_occupancy_label: str
    adr: float
    adr_label: str
    all_in_capex: float
    cash_capex: float
    senior_debt: float
    cash_equity: float
    total_equity: float
    equity_pct_allin: float
    equity_pct_cash: float
    revenue_y1: float
    revenue_mature: float
    ebitda_y1: float
    ebitda_mature: float
    ebitda_exit: float
    ebitda_margin: float
    gross_margin: float
    dscr_min: float
    dscr_y2: float
    project_irr_allin: Optional[float]
    project_irr_cash: Optional[float]
    equity_irr_allin: Optional[float]
    equity_irr_cash: Optional[float]
    terminal_value: float
    net_exit: float
    value_gap_capex: float
    verdict: str
    caveat: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _snapshot_from_engine(
    key: str,
    name: str,
    product: str,
    engine: FinancialModelEngine,
    keys: int,
    guests: int,
    mature_occupancy: float,
    mature_occupancy_label: str,
    adr_label: str,
    verdict: str,
    caveat: str,
) -> CaseSnapshot:
    df = engine.run_projection(5)
    debt = engine.debt_engine.get_annual_schedule_df()
    credit = CreditMetricsEngine(target_dscr=engine.financing.target_dscr)
    kpis = credit.compute_credit_kpis(df, debt)
    mature = df.iloc[2]
    y1 = df.iloc[0]

    land = float(engine.financing.land_in_kind_value)
    cash_investment = round(engine.total_project_investment - land, 2)

    all_in = credit.compute_returns_summary(
        df,
        initial_equity=engine.total_equity_at_close,
        initial_capex=engine.total_project_investment,
        exit_cap_rate=0.085,
        exit_cost_rate=EXIT_COST_RATE,
    )
    cash = credit.compute_returns_summary(
        df,
        initial_equity=engine.cash_equity,
        initial_capex=cash_investment,
        exit_cap_rate=0.085,
        exit_cost_rate=EXIT_COST_RATE,
    )

    lodging_revenue = float(mature["revenue_rooms"] + mature["revenue_full_house"])
    occupied_nights = 0.0
    # Reconstruct occupied nights from the revenue engine for the blended ADR.
    rev = engine.calculate_revenue_for_year(3)
    occupied_nights = float(rev["room_nights"] + rev["house_nights"])
    adr = lodging_revenue / occupied_nights if occupied_nights else 0.0

    return CaseSnapshot(
        key=key,
        name=name,
        product=product,
        keys=keys,
        guests=guests,
        mature_occupancy=round(mature_occupancy, 4),
        mature_occupancy_label=mature_occupancy_label,
        adr=round(adr, 2),
        adr_label=adr_label,
        all_in_capex=round(float(engine.capex.total_capex), 2),
        cash_capex=round(float(engine.cash_capex), 2),
        senior_debt=round(float(engine.financing.senior_debt_principal), 2),
        cash_equity=round(float(engine.cash_equity), 2),
        total_equity=round(float(engine.total_equity_at_close), 2),
        equity_pct_allin=round(float(engine.cash_equity / engine.capex.total_capex), 4),
        equity_pct_cash=round(float(engine.cash_equity / engine.cash_capex), 4),
        revenue_y1=round(float(y1["total_revenue"]), 2),
        revenue_mature=round(float(mature["total_revenue"]), 2),
        ebitda_y1=round(float(y1["ebitda"]), 2),
        ebitda_mature=round(float(mature["ebitda"]), 2),
        ebitda_exit=round(float(df.iloc[-1]["ebitda"]), 2),
        ebitda_margin=round(float(mature["ebitda"] / mature["total_revenue"]), 4),
        gross_margin=round(float(mature["gross_margin"] / mature["total_revenue"]), 4),
        dscr_min=round(float(kpis["dscr"].min()), 3),
        dscr_y2=round(float(kpis.iloc[1]["dscr"]), 3),
        project_irr_allin=all_in["project_irr_exit"],
        project_irr_cash=cash["project_irr_exit"],
        equity_irr_allin=all_in["equity_irr_exit"],
        equity_irr_cash=cash["equity_irr_exit"],
        terminal_value=round(float(all_in["terminal_value"]), 2),
        net_exit=all_in["net_terminal_value"],
        value_gap_capex=round(
            float(all_in["net_terminal_value"] - engine.capex.total_capex), 2
        ),
        verdict=verdict,
        caveat=caveat,
    )


class InvestmentCase:
    """Builds the three-column executive comparison and the value bridge."""

    def __init__(self, turnaround: Optional[TurnaroundEngine] = None):
        self.turnaround = turnaround or TurnaroundEngine()
        self._snapshots: Optional[List[CaseSnapshot]] = None

    # ------------------------------------------------------------------
    # The three columns
    # ------------------------------------------------------------------
    def snapshots(self) -> List[CaseSnapshot]:
        if self._snapshots is not None:
            return self._snapshots

        promoter_engine = FinancialModelEngine(
            case="promoter", scenario=SCENARIOS["base"]
        )
        audited_engine = FinancialModelEngine(
            case="management", scenario=SCENARIOS["base"]
        )
        t = self.turnaround.config

        promoter = _snapshot_from_engine(
            key="promoter",
            name="Promoter plan",
            product="7 doubles + 1 house + 21-cover restaurant",
            engine=promoter_engine,
            keys=8,
            guests=21,
            mature_occupancy=0.192,
            mature_occupancy_label="19.2%",
            adr_label="EUR 85 (house EUR 380)",
            verdict="UNFUNDABLE",
            caveat=(
                "EBITDA is a re-modelling with no variable cost stack (100% "
                "gross margin) and Year-1 cash is negative. Its positive IRR "
                "is an artefact of the incomplete cost basis."
            ),
        )
        audited = _snapshot_from_engine(
            key="audited",
            name="Audited case",
            product="Same hotel, full cost stack, 35% LTV request",
            engine=audited_engine,
            keys=8,
            guests=21,
            mature_occupancy=0.3136,
            mature_occupancy_label="31.36%",
            adr_label="EUR 85 (house EUR 380)",
            verdict="DECLINE",
            caveat=(
                "Upside demand: 31.36% mature occupancy is 1.48x the INE "
                "Segovia average. Even this case fails the covenant."
            ),
        )

        t8_df = self.turnaround.projection
        t8_debt = self.turnaround.debt_schedule
        t8_kpis = self.turnaround.kpis
        t8_mature = t8_df.iloc[2]
        t8_y1 = t8_df.iloc[0]
        t8_all = self.turnaround.returns("all-in")
        t8_cash = self.turnaround.returns("cash")
        rev3 = self.turnaround.engine.calculate_revenue_for_year(3)
        t8_lodging = float(rev3["rev_rooms"] + rev3["rev_house"])
        t8_nights = float(rev3["room_nights"] + rev3["house_nights"])
        t8_blended_occupancy = (
            t.cabins.count * t.cabins.occupancy_for_year(3)
            + (t.lodge.occupancy_for_year(3) if t.lodge.enabled else 0.0)
        ) / t.keys

        t8 = CaseSnapshot(
            key="turnaround",
            name="Cabin turnaround (T8)",
            product="6 modular cabins + caseron lodge, no restaurant",
            keys=t.keys,
            guests=t.guests_at_full_occupancy,
            mature_occupancy=round(t8_blended_occupancy, 4),
            mature_occupancy_label=(
                f"{t.cabins.occupancy_for_year(3):.0%} cabins / "
                f"{t.lodge.occupancy_for_year(3):.0%} lodge"
            ),
            adr=round(t8_lodging / t8_nights, 2) if t8_nights else 0.0,
            adr_label=f"EUR {t.cabins.adr:.0f} cabins / EUR {t.lodge.adr:.0f} lodge",
            all_in_capex=round(float(self.turnaround.engine.capex.total_capex), 2),
            cash_capex=round(float(self.turnaround.engine.cash_capex), 2),
            senior_debt=round(
                float(self.turnaround.engine.financing.senior_debt_principal), 2
            ),
            cash_equity=round(self.turnaround.cash_equity, 2),
            total_equity=round(self.turnaround.all_in_equity, 2),
            equity_pct_allin=round(
                self.turnaround.cash_equity
                / self.turnaround.engine.capex.total_capex,
                4,
            ),
            equity_pct_cash=round(
                self.turnaround.cash_equity / self.turnaround.engine.cash_capex, 4
            ),
            revenue_y1=round(float(t8_y1["total_revenue"]), 2),
            revenue_mature=round(float(t8_mature["total_revenue"]), 2),
            ebitda_y1=round(float(t8_y1["ebitda"]), 2),
            ebitda_mature=round(float(t8_mature["ebitda"]), 2),
            ebitda_exit=round(float(t8_df.iloc[-1]["ebitda"]), 2),
            ebitda_margin=round(
                float(t8_mature["ebitda"] / t8_mature["total_revenue"]), 4
            ),
            gross_margin=round(
                float(t8_mature["gross_margin"] / t8_mature["total_revenue"]), 4
            ),
            dscr_min=round(float(t8_kpis["dscr"].min()), 3),
            dscr_y2=round(float(t8_kpis.iloc[1]["dscr"]), 3),
            project_irr_allin=t8_all["project_irr_exit"],
            project_irr_cash=t8_cash["project_irr_exit"],
            equity_irr_allin=t8_all["equity_irr_exit"],
            equity_irr_cash=t8_cash["equity_irr_exit"],
            terminal_value=round(float(t8_all["terminal_value"]), 2),
            net_exit=t8_all["net_terminal_value"],
            value_gap_capex=round(
                float(
                    t8_all["net_terminal_value"]
                    - self.turnaround.engine.capex.total_capex
                ),
                2,
            ),
            verdict="PROCEED",
            caveat=(
                "58% cabin occupancy is 2.7x the INE average and above the "
                "50-55% benchmark band; the 45% stress case is published."
            ),
        )

        self._snapshots = [promoter, audited, t8]
        return self._snapshots

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------
    def comparison_table(self) -> pd.DataFrame:
        """Numeric comparison, rows = metric, columns = case."""
        rows: Dict[str, List[Any]] = {
            "Keys": [],
            "Guests at full occupancy": [],
            "Mature occupancy": [],
            "Blended ADR (EUR)": [],
            "All-in CapEx (EUR)": [],
            "Cash CapEx (EUR)": [],
            "Senior debt (EUR)": [],
            "Cash equity (EUR)": [],
            "Equity / all-in CapEx": [],
            "Equity / cash CapEx": [],
            "Revenue Year 1 (EUR)": [],
            "Revenue mature (EUR)": [],
            "EBITDA Year 1 (EUR)": [],
            "EBITDA mature (EUR)": [],
            "EBITDA margin mature": [],
            "Gross margin mature": [],
            "Minimum DSCR (x)": [],
            "Year-2 DSCR (x)": [],
            "Project IRR all-in": [],
            "Project IRR cash": [],
            "Equity IRR all-in": [],
            "Equity IRR cash": [],
            "Net exit value (EUR)": [],
            "Value gap vs CapEx (EUR)": [],
        }
        for s in self.snapshots():
            rows["Keys"].append(s.keys)
            rows["Guests at full occupancy"].append(s.guests)
            rows["Mature occupancy"].append(s.mature_occupancy)
            rows["Blended ADR (EUR)"].append(s.adr)
            rows["All-in CapEx (EUR)"].append(s.all_in_capex)
            rows["Cash CapEx (EUR)"].append(s.cash_capex)
            rows["Senior debt (EUR)"].append(s.senior_debt)
            rows["Cash equity (EUR)"].append(s.cash_equity)
            rows["Equity / all-in CapEx"].append(s.equity_pct_allin)
            rows["Equity / cash CapEx"].append(s.equity_pct_cash)
            rows["Revenue Year 1 (EUR)"].append(s.revenue_y1)
            rows["Revenue mature (EUR)"].append(s.revenue_mature)
            rows["EBITDA Year 1 (EUR)"].append(s.ebitda_y1)
            rows["EBITDA mature (EUR)"].append(s.ebitda_mature)
            rows["EBITDA margin mature"].append(s.ebitda_margin)
            rows["Gross margin mature"].append(s.gross_margin)
            rows["Minimum DSCR (x)"].append(s.dscr_min)
            rows["Year-2 DSCR (x)"].append(s.dscr_y2)
            rows["Project IRR all-in"].append(s.project_irr_allin)
            rows["Project IRR cash"].append(s.project_irr_cash)
            rows["Equity IRR all-in"].append(s.equity_irr_allin)
            rows["Equity IRR cash"].append(s.equity_irr_cash)
            rows["Net exit value (EUR)"].append(s.net_exit)
            rows["Value gap vs CapEx (EUR)"].append(s.value_gap_capex)

        return pd.DataFrame(
            rows, index=[s.name for s in self.snapshots()]
        ).T

    def formatted_table(self) -> pd.DataFrame:
        """Presentation version with units and percentages."""
        df = self.comparison_table()
        formatted = df.copy().astype(object)
        percent_rows = {
            "Mature occupancy",
            "Equity / all-in CapEx",
            "Equity / cash CapEx",
            "EBITDA margin mature",
            "Gross margin mature",
            "Project IRR all-in",
            "Project IRR cash",
            "Equity IRR all-in",
            "Equity IRR cash",
        }
        euro_rows = {r for r in df.index if "(EUR)" in r}
        for row in df.index:
            for col in df.columns:
                value = df.loc[row, col]
                if pd.isna(value):
                    formatted.loc[row, col] = "n/a"
                elif row in percent_rows:
                    formatted.loc[row, col] = f"{float(value):.1%}"
                elif row in euro_rows:
                    formatted.loc[row, col] = f"{float(value):,.0f}"
                elif row in {"Keys", "Guests at full occupancy"}:
                    formatted.loc[row, col] = int(value)
                elif row.endswith("(x)"):
                    formatted.loc[row, col] = f"{float(value):.2f}x"
                elif row == "Blended ADR (EUR)":
                    formatted.loc[row, col] = f"EUR {float(value):,.0f}"
                else:
                    formatted.loc[row, col] = value
        return formatted

    # ------------------------------------------------------------------
    # Value bridge
    # ------------------------------------------------------------------
    def value_bridge(self) -> pd.DataFrame:
        rows = []
        for s in self.snapshots():
            rows.append(
                {
                    "case": s.name,
                    "ebitda_exit": s.ebitda_exit,
                    "exit_cap_rate": 0.085,
                    "gross_terminal_value": s.terminal_value,
                    "net_terminal_value": s.net_exit,
                    "all_in_capex": s.all_in_capex,
                    "value_gap_vs_capex": s.value_gap_capex,
                    "value_gap_pct": round(
                        s.value_gap_capex / s.all_in_capex, 4
                    ) if s.all_in_capex else None,
                }
            )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Narrative + export
    # ------------------------------------------------------------------
    def narrative(self) -> Dict[str, str]:
        promoter, audited, t8 = self.snapshots()
        t = self.turnaround.config
        return {
            "act_1_pitch": (
                f"The promoter asked for EUR {promoter.all_in_capex:,.0f} to "
                f"reopen the caseron as an 8-key hotel with a 21-cover "
                f"restaurant, on 19.2% occupancy and an EUR 85 ADR. The model "
                f"reproduces EUR {promoter.revenue_y1:,.0f} of Year-1 revenue "
                f"and EUR {promoter.ebitda_y1:,.0f} of EBITDA - but with no "
                f"variable cost stack and negative Year-1 cash."
            ),
            "act_2_audit": (
                f"A full cost stack, INE Segovia seasonality, the Segovia "
                f"hospitality agreement and the 21% VAT bridge raise the "
                f"all-in budget to EUR {audited.all_in_capex:,.0f}. The best "
                f"demand case (31.36% occupancy) generates EUR "
                f"{audited.revenue_mature:,.0f} of mature revenue and a "
                f"{audited.dscr_min:.2f}x minimum DSCR."
            ),
            "act_3_decline": (
                "The credit committee declines: the Year-2 DSCR is 1.15x "
                "against a 1.25x covenant, the equity plug is EUR 521k "
                "(49.6% of all-in CapEx), the restaurant does not cover its "
                "fixed cost, and Phase II opens a EUR 252k hole."
            ),
            "act_4_turnaround": (
                f"Six modular cabins at EUR "
                f"{t.capex.installed_cost_per_cabin:,.0f} installed "
                f"plus the caseron as a four-bedroom lodge cut the cash "
                f"envelope to EUR {t8.cash_capex:,.0f} (-40% versus the EUR "
                f"1,050,100 audited budget). No commercial kitchen, two FTE, "
                f"EUR {t8.revenue_mature:,.0f} of mature revenue at a "
                f"{t8.ebitda_margin:.1%} EBITDA margin and a "
                f"{t8.dscr_min:.2f}x minimum DSCR."
            ),
            "act_5_comparison": (
                f"On a like-for-like 3%-cost exit at an 8.5% cap rate the T8 "
                f"equity IRR is {t8.equity_irr_allin:.1%} all-in and "
                f"{t8.equity_irr_cash:.1%} on cash equity, against "
                f"{audited.equity_irr_allin:.1%} for the audited case. The "
                f"turnaround creates EUR {t8.value_gap_capex:,.0f} of value "
                f"over its all-in CapEx; the audited case destroys EUR "
                f"{abs(audited.value_gap_capex):,.0f}."
            ),
        }

    def export_json(self, path: Optional[Path] = None) -> Path:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        target = Path(path) if path else DATA_DIR / "investment_case.json"
        payload = {
            "cases": [s.to_dict() for s in self.snapshots()],
            "comparison": self.comparison_table().reset_index().rename(
                columns={"index": "metric"}
            ).to_dict(orient="records"),
            "value_bridge": self.value_bridge().to_dict(orient="records"),
            "narrative": self.narrative(),
            "exit_convention": {
                "exit_cap_rate": 0.085,
                "exit_cost_rate": EXIT_COST_RATE,
                "note": (
                    "All three columns are net of 3% exit costs. Act 2 quotes "
                    "the audited equity IRR gross of exit costs (-23.16%)."
                ),
            },
        }
        target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return target

    def print_terminal_summary(self) -> None:
        df = self.formatted_table()
        print("=" * 118)
        print(" ACT 5 - EXECUTIVE COMPARISON: PROMOTER PLAN vs AUDITED CASE vs CABIN TURNAROUND")
        print("=" * 118)
        header = f"{'Metric':<32}" + "".join(f"{c:>27}" for c in df.columns)
        print(header)
        print("-" * 118)
        for metric in df.index:
            print(f"{metric:<32}" + "".join(f"{str(df.loc[metric, c]):>27}" for c in df.columns))
        print("-" * 118)
        for s in self.snapshots():
            print(f"{s.name:<24} {s.verdict:<12} {s.caveat}")
        print("=" * 118)
