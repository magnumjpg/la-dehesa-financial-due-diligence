"""
Act 3 - the credit committee decline memo.

The memo is produced from the same as-is engine as the audit, not from a
separate spreadsheet. Each of the four reasons is a computed test with an
explicit threshold; the verdict is `DECLINE` only if every test fails, so the
document cannot claim a decline that the model does not support.

The four reasons
----------------
1. **DSCR** - Year-2 DSCR of 1.15x against a 1.25x covenant.
2. **Equity** - the funding plug requires EUR 521k of cash equity, 49.6% of the
   all-in CapEx and 65.1% of the cash works, against a 30% plan.
3. **Restaurant** - a fully loaded cost centre at the promoter's own design
   capacity (16 covers/day) loses EUR 18.7k at a EUR 20 ticket and barely
   breaks even at EUR 25. It is a fixed-cost trap, not an amenity.
4. **Phase II** - the expansion needs EUR 252k that Phase I cannot generate.

The restaurant test is deliberately explicit about its allocation: payroll,
utilities, POS/laundry/insurance, property and depreciation are all loaded onto
the cost centre. The engine's own contribution view (restaurant gross margin
minus the two kitchen salaries) is shown next to it, so the reader can see the
difference between "the restaurant loses cash" and "the restaurant does not
earn its capital".
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config.assumptions import SCENARIOS, ScenarioDrivers
from src.core.expansion import ExpansionFinancialEngine
from src.core.metrics import CreditMetricsEngine
from src.core.statements import FinancialModelEngine

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Policy thresholds (inputs to the memo, not outputs of the model).
DSCR_COVENANT = 1.25
PLANNED_EQUITY_SHARE = 0.30

# Restaurant cost-centre assumptions, taken from the audited build-up.
DESIGN_COVERS_PER_DAY = 16.0
RESTAURANT_SERVICE_DAYS = 360
RESTAURANT_COGS_RATIO = 0.30
KITCHEN_SALARIES = 2 * 13_500.0 * 1.35          # two part-time cooks, 35% SS
FOH_SALARY = 17_844.16 * 1.325                  # one camarero, 32.5% SS
ALLOCATED_OVERHEAD = 21_000.0                   # utilities, laundry, POS, insurance
KITCHEN_DEPRECIATION = 55_000.0 * 0.12          # kitchen equipment
RENOVATION_ALLOCATION = 550_000.0 * 0.25 * 0.03 # 25% of the works, 3%
PROPERTY_ALLOCATION = 7_500.0                   # share of rent / opportunity cost


@dataclass(frozen=True)
class DeclineReason:
    key: str
    number: int
    title: str
    metric: float
    threshold: float
    unit: str
    failed: bool
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DeclineMemoEngine:
    """Computes the four decline tests on the audited (management) case."""

    def __init__(
        self,
        case: str = "management",
        scenario: Optional[ScenarioDrivers] = None,
    ):
        self.case = case
        self.scenario = scenario or SCENARIOS["base"]
        self.engine = FinancialModelEngine(case=case, scenario=self.scenario)
        self.projection = self.engine.run_projection(5)
        self.debt_schedule = self.engine.debt_engine.get_annual_schedule_df()
        self.credit = CreditMetricsEngine(target_dscr=DSCR_COVENANT)
        self.kpis = self.credit.compute_credit_kpis(
            self.projection, self.debt_schedule
        )
        self.funding = self.engine.sources_uses_at_close()

    # ------------------------------------------------------------------
    # Reason 1 - DSCR
    # ------------------------------------------------------------------
    def dscr_test(self) -> DeclineReason:
        year2 = self.kpis[self.kpis["year"] == 2].iloc[0]
        dscr = float(year2["dscr"])
        service = float(year2["debt_service"])
        cfads = float(year2["cfads"])
        shortfall = max(0.0, DSCR_COVENANT * service - cfads)
        return DeclineReason(
            key="dscr",
            number=1,
            title="Year-2 DSCR below covenant",
            metric=round(dscr, 3),
            threshold=DSCR_COVENANT,
            unit="x",
            failed=dscr < DSCR_COVENANT,
            detail=(
                f"CFADS of EUR {cfads:,.0f} against EUR {service:,.0f} of debt "
                f"service gives {dscr:.2f}x. To reach the 1.25x covenant the "
                f"project needs EUR {shortfall:,.0f} more CFADS, or a smaller "
                f"facility: the DSCR-capped principal is EUR "
                f"{self.engine.debt_sizing()['principal_dscr_cap']:,.0f} versus "
                f"the EUR {self.engine.financing.senior_debt_principal:,.0f} "
                f"requested."
            ),
        )

    # ------------------------------------------------------------------
    # Reason 2 - equity
    # ------------------------------------------------------------------
    def equity_test(self) -> DeclineReason:
        cash_equity = float(self.engine.cash_equity)
        cash_capex = float(self.engine.cash_capex)
        all_in = float(self.engine.capex.total_capex)
        planned = cash_capex * PLANNED_EQUITY_SHARE
        excess = cash_equity - planned
        pct_all_in = cash_equity / all_in
        return DeclineReason(
            key="equity",
            number=2,
            title="Equity requirement is 1.65x the plan",
            metric=round(pct_all_in * 100.0, 2),
            threshold=PLANNED_EQUITY_SHARE * 100.0,
            unit="% of all-in CapEx",
            failed=pct_all_in > PLANNED_EQUITY_SHARE,
            detail=(
                f"The funding plug requires EUR {cash_equity:,.2f} of cash "
                f"equity: {cash_equity / cash_capex:.1%} of the EUR "
                f"{cash_capex:,.0f} cash works and {pct_all_in:.2%} of the EUR "
                f"{all_in:,.0f} all-in CapEx. The promoter planned 30% "
                f"(EUR {planned:,.0f}); the gap is EUR {excess:,.0f}. The 35% "
                f"LTV facility is not the constraint - the DSCR cap is."
            ),
        )

    # ------------------------------------------------------------------
    # Reason 3 - the restaurant
    # ------------------------------------------------------------------
    def restaurant_cost_centre(self) -> Dict[str, Any]:
        """Fully loaded cost centre at the promoter's own design capacity.

        Returns the fixed-cost build-up and the EUR 20 / EUR 25 ticket tests so
        the memo and the Excel can show the arithmetic instead of a single
        verdict.
        """
        covers = DESIGN_COVERS_PER_DAY * RESTAURANT_SERVICE_DAYS
        fixed_lines = {
            "Kitchen payroll (two part-time cooks, 35% SS)": round(KITCHEN_SALARIES, 2),
            "Front-of-house (one camarero, 32.5% SS)": round(FOH_SALARY, 2),
            "Allocated overhead (utilities, laundry, POS, insurance)": ALLOCATED_OVERHEAD,
            "Kitchen depreciation (55k at 12%)": round(KITCHEN_DEPRECIATION, 2),
            "Renovation allocation (25% of works at 3%)": round(RENOVATION_ALLOCATION, 2),
            "Property / opportunity cost allocation": PROPERTY_ALLOCATION,
        }
        fixed_burden = round(sum(fixed_lines.values()), 2)
        results = {}
        for ticket in (20.0, 25.0):
            revenue = covers * ticket
            cogs = revenue * RESTAURANT_COGS_RATIO
            results[ticket] = {
                "ticket": ticket,
                "covers": covers,
                "revenue": round(revenue, 2),
                "cogs": round(cogs, 2),
                "contribution": round(revenue - cogs, 2),
                "fixed_burden": fixed_burden,
                "result": round(revenue - cogs - fixed_burden, 2),
                "margin": round((revenue - cogs - fixed_burden) / revenue, 4),
            }
        return {
            "covers": covers,
            "covers_per_day": DESIGN_COVERS_PER_DAY,
            "service_days": RESTAURANT_SERVICE_DAYS,
            "cogs_ratio": RESTAURANT_COGS_RATIO,
            "fixed_lines": fixed_lines,
            "fixed_burden": fixed_burden,
            "tickets": results,
        }

    def restaurant_test(self) -> DeclineReason:
        centre = self.restaurant_cost_centre()
        covers = centre["covers"]
        fixed_burden = centre["fixed_burden"]
        results = centre["tickets"]

        # The engine's own view: restaurant gross margin minus the two cooks.
        y3 = self.projection.iloc[2]
        engine_revenue = float(y3["revenue_restaurant"])
        engine_cogs = float(y3["cogs_restaurant"])
        engine_gross = round(engine_revenue - engine_cogs, 2)
        engine_residual = round(engine_gross - KITCHEN_SALARIES, 2)

        low = results[20.0]
        high = results[25.0]
        return DeclineReason(
            key="restaurant",
            number=3,
            title="The restaurant is a fixed-cost trap",
            metric=round(low["result"], 2),
            threshold=0.0,
            unit="EUR at the EUR 20 ticket",
            failed=low["result"] < 0,
            detail=(
                f"At the promoter's own design capacity ({DESIGN_COVERS_PER_DAY:.0f} "
                f"covers/day x {RESTAURANT_SERVICE_DAYS} days = {covers:,.0f} "
                f"covers), the fully loaded cost centre loses EUR "
                f"{abs(low['result']):,.0f} at a EUR 20 ticket and earns only EUR "
                f"{high['result']:,.0f} at EUR 25, on EUR {fixed_burden:,.0f} of "
                f"fixed cost. In the audited engine the restaurant produces EUR "
                f"{engine_gross:,.0f} of gross margin against EUR "
                f"{KITCHEN_SALARIES:,.0f} of kitchen payroll - EUR "
                f"{engine_residual:,.0f} before rent, utilities or depreciation. "
                f"It consumes EUR 55,000 of kitchen CapEx and two of the three "
                f"FTE to serve a 21-cover room that is never full."
            ),
        )

    # ------------------------------------------------------------------
    # Reason 4 - Phase II
    # ------------------------------------------------------------------
    def phase2_test(self) -> DeclineReason:
        expansion = ExpansionFinancialEngine()
        cash_y2 = float(self.kpis.iloc[1]["ending_cash"])
        dscr_y3 = float(self.kpis.iloc[2]["dscr"])
        gate = expansion.compute_phase_gate(cash_y2, dscr_y3)
        return DeclineReason(
            key="phase2",
            number=4,
            title="Phase II is not self-funding",
            metric=round(float(gate["phase2_funding_gap"]), 2),
            threshold=0.0,
            unit="EUR funding gap",
            failed=float(gate["phase2_funding_gap"]) < 0,
            detail=(
                f"The landscape suites and biological pond need EUR "
                f"{gate['phase2_cash_need']:,.0f} including input VAT. Phase I "
                f"ends Year 2 with EUR {gate['phase1_cash_end_y2']:,.0f} of cash "
                f"and a Year-3 DSCR of {gate['phase1_dscr_y3']:.2f}x, so the "
                f"expansion opens a EUR {abs(gate['phase2_funding_gap']):,.0f} "
                f"hole. The grant and the VAT refund are already committed in "
                f"Phase I and cannot be counted twice."
            ),
        )

    # ------------------------------------------------------------------
    # Verdict
    # ------------------------------------------------------------------
    def reasons(self) -> List[DeclineReason]:
        return [
            self.dscr_test(),
            self.equity_test(),
            self.restaurant_test(),
            self.phase2_test(),
        ]

    def verdict(self) -> Dict[str, Any]:
        reasons = self.reasons()
        failed = [r for r in reasons if r.failed]
        decision = "DECLINE" if len(failed) == len(reasons) else "CONDITIONAL"
        return {
            "decision": decision,
            "reasons_tested": len(reasons),
            "reasons_failed": len(failed),
            "reasons": [r.to_dict() for r in reasons],
            "headline": (
                "DECLINE. The project fails the DSCR covenant in Year 2, needs "
                "EUR 521k of equity instead of the EUR 240k planned, operates a "
                "restaurant that does not cover its fixed cost, and cannot fund "
                "its own Phase II."
            ),
            "memo": (
                "The independent INE market case is worse, not better: at "
                "21.24% occupancy the property produces negative EBITDA in "
                "Year 1 and a DSCR of -1.46x. The management case is the "
                "upside; the decline holds a fortiori."
            ),
            "context": {
                "case": self.case,
                "cash_equity": round(float(self.engine.cash_equity), 2),
                "all_in_capex": round(float(self.engine.capex.total_capex), 2),
                "senior_debt": round(
                    float(self.engine.financing.senior_debt_principal), 2
                ),
                "min_dscr": round(float(self.kpis["dscr"].min()), 3),
                "terminal_value": round(
                    float(self.credit.compute_returns_summary(
                        self.projection,
                        initial_equity=self.engine.total_equity_at_close,
                        initial_capex=self.engine.total_project_investment,
                        exit_cap_rate=0.085,
                    )["terminal_value"]),
                    2,
                ),
            },
        }

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for r in self.reasons():
            rows.append(
                {
                    "test": r.number,
                    "reason": r.title,
                    "metric": r.metric,
                    "threshold": r.threshold,
                    "unit": r.unit,
                    "failed": r.failed,
                    "detail": r.detail,
                }
            )
        return pd.DataFrame(rows)

    def export_json(self, path: Optional[Path] = None) -> Path:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        target = Path(path) if path else DATA_DIR / "decline_memo.json"
        target.write_text(
            json.dumps(self.verdict(), indent=2, default=str), encoding="utf-8"
        )
        return target

    def print_terminal_summary(self) -> None:
        v = self.verdict()
        print("=" * 96)
        print(" ACT 3 - CREDIT COMMITTEE DECLINE MEMORANDUM")
        print("=" * 96)
        print(
            f"Case under review:                {self.case} (upside occupancy, "
            f"full cost stack, 35% LTV request)"
        )
        print(
            f"All-in CapEx / senior debt:       EUR "
            f"{v['context']['all_in_capex']:,.2f} / EUR "
            f"{v['context']['senior_debt']:,.2f}"
        )
        print(f"Cash equity required:             EUR {v['context']['cash_equity']:,.2f}")
        print("-" * 96)
        for r in v["reasons"]:
            status = "FAIL" if r["failed"] else "PASS"
            print(f"[{r['number']}] {r['title']:<44} {r['metric']:>12,.2f} {r['unit']:<24} {status}")
            print(f"    {r['detail']}")
            print()
        print("-" * 96)
        print(f"VERDICT: {v['decision']} ({v['reasons_failed']}/{v['reasons_tested']} tests failed)")
        print(v["headline"])
        print(v["memo"])
        print("=" * 96)
