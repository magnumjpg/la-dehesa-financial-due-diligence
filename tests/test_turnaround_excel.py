"""Excel integration tests for the five-act case study and the T8 live layer.

The workbook is generated once per module. The live tabs are then recalculated
with the ``formulas`` engine, so a broken cross-sheet reference fails here
instead of only failing when a human opens the file.
"""

from pathlib import Path

import numpy as np
import openpyxl
import pytest

from src.core.turnaround import TurnaroundEngine
from src.data.export_excel import export_institutional_excel


MODEL_NAME = "test_turnaround_case_study.xlsx"


@pytest.fixture(scope="module")
def workbook_path() -> Path:
    path = export_institutional_excel(MODEL_NAME)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def workbook(workbook_path: Path):
    return openpyxl.load_workbook(workbook_path)


@pytest.fixture(scope="module")
def calculated(workbook_path: Path):
    formulas = pytest.importorskip("formulas")
    model = formulas.ExcelModel().loads(str(workbook_path)).finish()
    return model.calculate()


def _value(calculated, sheet: str, cell: str):
    key = (
        f"'[{MODEL_NAME}]{sheet.upper()}'!{cell}"
    )
    result = calculated.get(key)
    if result is None:
        return None
    value = result.value
    array = np.asarray(value)
    if array.size == 1:
        return float(array.reshape(-1)[0])
    return value


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------
def test_workbook_has_the_full_five_act_narrative(workbook):
    names = workbook.sheetnames
    for tab in (
        "Act 1 - Promoter",
        "Act 2 - Audit",
        "Decline Memo",
        "Act 4 - T8",
        "Executive Comparison",
        "T8 Sensitivities",
        "T8 Inputs",
        "T8 Debt Schedule",
        "T8 Live Model",
    ):
        assert tab in names, f"{tab} is missing from the workbook"

    # The acts must appear in narrative order, after the as-is report pack.
    assert names.index("Act 1 - Promoter") < names.index("Act 2 - Audit")
    assert names.index("Act 2 - Audit") < names.index("Decline Memo")
    assert names.index("Decline Memo") < names.index("Act 4 - T8")
    assert names.index("Act 4 - T8") < names.index("Executive Comparison")


def test_readme_keeps_the_three_case_anchor_and_adds_the_t8_block(workbook):
    ws = workbook["Read Me & Checks"]
    # Regression: promoter row must stay at C24/D24 for the reconciliation test.
    assert ws["C24"].value == 86_275
    assert ws["D24"].value == 11_297

    assert ws["A19"].value == "Act 1-5 & T8"
    assert "T8 TURNAROUND" in str(ws["A56"].value)
    assert "18.95%" in str(ws["B62"].value)


def test_decline_memo_states_the_four_reasons_and_the_verdict(workbook):
    ws = workbook["Decline Memo"]
    text = " ".join(
        str(cell.value) for row in ws.iter_rows() for cell in row if cell.value
    )
    assert "DECLINE" in text
    assert "DSCR" in text
    assert "252" in text or "Phase II" in text


def test_executive_comparison_has_the_three_columns(workbook):
    ws = workbook["Executive Comparison"]
    names = [
        str(cell.value)
        for row in ws.iter_rows(min_col=1, max_col=1)
        for cell in row
        if cell.value
    ]
    joined = " ".join(names)
    assert "Promoter plan" in joined
    assert "Audited case" in joined
    assert "Cabin turnaround (T8)" in joined


# ---------------------------------------------------------------------------
# Live formulas
# ---------------------------------------------------------------------------
def test_t8_live_model_check_block_reconciles_to_python(calculated):
    differences = [_value(calculated, "T8 Live Model", f"D{r}") for r in range(72, 82)]
    assert all(v is not None for v in differences)
    for row, diff in zip(range(72, 82), differences):
        assert abs(float(diff)) <= 1.0, f"Row {row} differs from Python by {diff}"

    covenant = float(_value(calculated, "T8 Live Model", "D82"))
    assert covenant == pytest.approx(2.3121, abs=0.001)


def test_t8_live_returns_match_the_python_engine(calculated):
    engine = TurnaroundEngine()
    all_in = engine.returns("all-in")
    cash = engine.returns("cash")

    assert float(_value(calculated, "T8 Live Model", "B106")) == pytest.approx(
        all_in["project_irr_exit"], abs=1e-5
    )
    assert float(_value(calculated, "T8 Live Model", "B107")) == pytest.approx(
        cash["project_irr_exit"], abs=1e-5
    )
    assert float(_value(calculated, "T8 Live Model", "B108")) == pytest.approx(
        all_in["equity_irr_exit"], abs=1e-5
    )
    assert float(_value(calculated, "T8 Live Model", "B109")) == pytest.approx(
        cash["equity_irr_exit"], abs=1e-5
    )

    assert float(_value(calculated, "T8 Live Model", "B89")) == pytest.approx(
        all_in["net_terminal_value"], abs=1.0
    )


def test_t8_live_balance_sheet_is_clean_in_every_year(calculated):
    for col in "BCDEF":
        diff = float(_value(calculated, "T8 Live Model", f"{col}65"))
        assert abs(diff) < 1.0


def test_t8_debt_schedule_amortises_to_zero_in_month_240(calculated):
    ending = float(_value(calculated, "T8 Debt Schedule", "G263"))
    assert abs(ending) < 1.0
