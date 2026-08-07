import pandas as pd
import pytest

from psx_ml.c11.capital_allocation import (
    AllocationDefinition,
    build_allocation_targets,
)
from psx_ml.c11.weighted_execution import normalize_target_weights


def _selections() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "policy_id": ["P4", "P4", "P5", "P5"],
            "trade_date": pd.to_datetime(["2025-01-02"] * 4),
            "symbol": ["AAA", "BBB", "AAA", "CCC"],
            "shariah_eligible": [True] * 4,
        }
    )


def test_overlap_is_aggregated_into_one_target_weight() -> None:
    definition = AllocationDefinition(
        "combo",
        (("P4", 0.50), ("P5", 0.50)),
        "test",
    )
    result = build_allocation_targets(_selections(), definition)
    weights = dict(zip(result["symbol"], result["target_weight"]))

    # Each 50% sleeve has two equal-weight names.
    # AAA is selected by both sleeves: 25% + 25% = 50%.
    assert weights == pytest.approx(
        {"AAA": 0.50, "BBB": 0.25, "CCC": 0.25}
    )
    assert result["symbol"].is_unique
    assert result["target_weight"].sum() == pytest.approx(1.0)


def test_allocation_definition_must_sum_to_one() -> None:
    definition = AllocationDefinition(
        "bad",
        (("P4", 0.60), ("P5", 0.30)),
        "test",
    )
    with pytest.raises(ValueError):
        definition.validate()


def test_non_shariah_sleeve_row_is_rejected() -> None:
    selections = _selections()
    selections.loc[selections["symbol"] == "BBB", "shariah_eligible"] = False
    definition = AllocationDefinition(
        "combo",
        (("P4", 0.50), ("P5", 0.50)),
        "test",
    )
    with pytest.raises(ValueError):
        build_allocation_targets(selections, definition)


def test_weighted_targets_require_unit_sum_per_date() -> None:
    targets = pd.DataFrame(
        {
            "policy_id": ["combo", "combo"],
            "trade_date": pd.to_datetime(["2025-01-02", "2025-01-02"]),
            "symbol": ["AAA", "BBB"],
            "target_weight": [0.7, 0.2],
            "next_session_date": pd.to_datetime(["2025-01-03", "2025-01-03"]),
            "entry_available": [True, True],
        }
    )
    with pytest.raises(ValueError):
        normalize_target_weights(targets)
