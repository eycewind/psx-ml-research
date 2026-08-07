import pandas as pd

from psx_ml.c10.capacity import (
    CapacityScenario,
    evaluate_capacity_scenario,
)


def test_more_capital_cannot_improve_fill_ratio() -> None:
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

    small = evaluate_capacity_scenario(
        trades,
        CapacityScenario(
            scenario_id="small",
            portfolio_capital=1_000_000.0,
            participation_rate=0.10,
        ),
    )

    large = evaluate_capacity_scenario(
        trades,
        CapacityScenario(
            scenario_id="large",
            portfolio_capital=10_000_000.0,
            participation_rate=0.10,
        ),
    )

    assert (
        large.loc[0, "fill_ratio"]
        <= small.loc[0, "fill_ratio"]
    )


def test_higher_participation_cannot_reduce_fill_ratio() -> None:
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

    low = evaluate_capacity_scenario(
        trades,
        CapacityScenario(
            scenario_id="low",
            portfolio_capital=5_000_000.0,
            participation_rate=0.05,
        ),
    )

    high = evaluate_capacity_scenario(
        trades,
        CapacityScenario(
            scenario_id="high",
            portfolio_capital=5_000_000.0,
            participation_rate=0.20,
        ),
    )

    assert (
        high.loc[0, "fill_ratio"]
        >= low.loc[0, "fill_ratio"]
    )
