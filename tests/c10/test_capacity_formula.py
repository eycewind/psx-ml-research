import pandas as pd
import pytest

from psx_ml.c10.capacity import (
    CapacityScenario,
    evaluate_capacity_scenario,
)


def test_capacity_fill_ratio_formula() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-03"],
            "signal_date": ["2025-01-02"],
            "symbol": ["AAA"],
            "notional": [100_000.0],
            "reference_turnover_20obs": [
                1_000_000.0
            ],
            "liquidity_available": [True],
        }
    )

    scenario = CapacityScenario(
        scenario_id="test",
        portfolio_capital=2_000_000.0,
        participation_rate=0.10,
        base_capital=1_000_000.0,
    )

    result = evaluate_capacity_scenario(
        trades,
        scenario,
    )

    assert result.loc[
        0,
        "scaled_trade_notional",
    ] == pytest.approx(200_000.0)

    assert result.loc[
        0,
        "capacity_notional",
    ] == pytest.approx(100_000.0)

    assert result.loc[
        0,
        "fill_ratio",
    ] == pytest.approx(0.5)

    assert result.loc[
        0,
        "capacity_unfilled_notional",
    ] == pytest.approx(100_000.0)

    assert not bool(
        result.loc[
            0,
            "fully_feasible",
        ]
    )
