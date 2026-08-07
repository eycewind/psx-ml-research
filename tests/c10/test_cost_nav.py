import pandas as pd
import pytest

from psx_ml.c10.costs import (
    CostSchedule,
    apply_trade_costs,
    build_costed_nav,
)


def test_zero_cost_overlay_matches_gross_nav() -> None:
    nav = pd.DataFrame(
        {
            "policy_id": ["P1", "P1"],
            "trade_date": ["2025-01-02", "2025-01-03"],
            "nav_close": [1_100.0, 1_210.0],
            "daily_return": [0.10, 0.10],
        }
    )
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-02"],
            "symbol": ["AAA"],
            "side": ["BUY"],
            "shares": [10.0],
            "notional": [1_000.0],
        }
    )
    schedule = CostSchedule(
        schedule_id="zero",
        brokerage_rate=0.0,
        brokerage_per_share=0.0,
    )
    costed = apply_trade_costs(trades, schedule)
    result = build_costed_nav(
        gross_nav=nav,
        costed_trades=costed,
        starting_capital=1_000.0,
    )
    assert result["net_nav"].tolist() == pytest.approx([1_100.0, 1_210.0])


def test_cost_is_deducted_before_gross_return() -> None:
    nav = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-02"],
            "nav_close": [1_100.0],
            "daily_return": [0.10],
        }
    )
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-02"],
            "symbol": ["AAA"],
            "side": ["BUY"],
            "shares": [10.0],
            "notional": [1_000.0],
        }
    )
    schedule = CostSchedule(
        schedule_id="ten_percent",
        brokerage_rate=0.10,
        brokerage_per_share=0.0,
    )
    costed = apply_trade_costs(trades, schedule)
    result = build_costed_nav(
        gross_nav=nav,
        costed_trades=costed,
        starting_capital=1_000.0,
    )
    expected = 1_000.0 * (1.0 - 0.10) * (1.0 + 0.10)
    assert result.loc[0, "net_nav"] == pytest.approx(expected)
    assert result.loc[0, "net_daily_return"] == pytest.approx(-0.01)
