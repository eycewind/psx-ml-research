import pandas as pd
import pytest

from psx_ml.c10.capacity import (
    CapacityScenario,
    evaluate_capacity_scenario,
)


def test_invalid_participation_rate_is_rejected() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-03"],
            "signal_date": ["2025-01-02"],
            "symbol": ["AAA"],
            "notional": [100.0],
            "reference_turnover_20obs": [1_000.0],
            "liquidity_available": [True],
        }
    )

    with pytest.raises(
        ValueError,
        match="cannot exceed",
    ):
        evaluate_capacity_scenario(
            trades,
            CapacityScenario(
                scenario_id="bad",
                portfolio_capital=1_000_000.0,
                participation_rate=1.5,
            ),
        )
