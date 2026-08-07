import pandas as pd
import pytest

from psx_ml.c10.costs import (
    PSX_MINIMUM_BROKERAGE,
    apply_trade_costs,
)


def test_rate_branch_wins_for_high_priced_share() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-02"],
            "symbol": ["AAA"],
            "side": ["BUY"],
            "shares": [100.0],
            "notional": [100_000.0],
        }
    )
    result = apply_trade_costs(trades, PSX_MINIMUM_BROKERAGE)
    assert result.loc[0, "brokerage_by_rate"] == pytest.approx(150.0)
    assert result.loc[0, "brokerage_by_share"] == pytest.approx(3.0)
    assert result.loc[0, "brokerage"] == pytest.approx(150.0)


def test_per_share_floor_wins_for_low_priced_share() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2025-01-02"],
            "symbol": ["LOW"],
            "side": ["SELL"],
            "shares": [10_000.0],
            "notional": [100_000.0],
        }
    )
    result = apply_trade_costs(trades, PSX_MINIMUM_BROKERAGE)
    assert result.loc[0, "brokerage_by_rate"] == pytest.approx(150.0)
    assert result.loc[0, "brokerage_by_share"] == pytest.approx(300.0)
    assert result.loc[0, "brokerage"] == pytest.approx(300.0)


def test_buy_and_sell_use_same_formula() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1", "P1"],
            "trade_date": ["2025-01-02", "2025-01-09"],
            "symbol": ["AAA", "AAA"],
            "side": ["BUY", "SELL"],
            "shares": [100.0, 100.0],
            "notional": [100_000.0, 100_000.0],
        }
    )
    result = apply_trade_costs(trades, PSX_MINIMUM_BROKERAGE)
    assert result["brokerage"].tolist() == pytest.approx([150.0, 150.0])
