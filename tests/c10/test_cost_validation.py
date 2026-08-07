import pandas as pd
import pytest

from psx_ml.c10.costs import CostSchedule, apply_trade_costs


def test_negative_cost_rate_is_rejected() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-02"],
            "symbol": ["AAA"],
            "side": ["BUY"],
            "shares": [1.0],
            "notional": [100.0],
        }
    )
    schedule = CostSchedule(
        schedule_id="bad",
        brokerage_rate=-0.001,
        brokerage_per_share=0.03,
    )
    with pytest.raises(ValueError, match="non-negative"):
        apply_trade_costs(trades, schedule)


def test_unknown_trade_side_is_rejected() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-02"],
            "symbol": ["AAA"],
            "side": ["SHORT"],
            "shares": [1.0],
            "notional": [100.0],
        }
    )
    schedule = CostSchedule(
        schedule_id="valid",
        brokerage_rate=0.0015,
        brokerage_per_share=0.03,
    )
    with pytest.raises(ValueError, match="Unexpected trade sides"):
        apply_trade_costs(trades, schedule)
