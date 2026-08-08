import pandas as pd
import pytest

from psx_ml.c11.execution_portfolio import (
    ExecutionConfig,
    build_execution_portfolio,
    resolve_buy_execution,
)


def test_open_below_limit_fills_at_open() -> None:
    result = resolve_buy_execution(
        signal_close=100.0,
        session_open=101.0,
        session_low=99.0,
        buy_limit_premium=0.02,
        fill_mode="touch_fill",
    )
    assert result == pytest.approx((101.0, "open", 102.0))


def test_touch_fill_uses_limit_when_open_above_limit() -> None:
    result = resolve_buy_execution(
        signal_close=100.0,
        session_open=104.0,
        session_low=101.0,
        buy_limit_premium=0.02,
        fill_mode="touch_fill",
    )
    assert result == pytest.approx((102.0, "intraday_touch_proxy", 102.0))


def test_open_only_ignores_intraday_touch() -> None:
    result = resolve_buy_execution(
        signal_close=100.0,
        session_open=104.0,
        session_low=101.0,
        buy_limit_premium=0.02,
        fill_mode="open_only",
    )
    assert result is None


def _mapped() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "policy_id": ["P"],
            "trade_date": pd.to_datetime(["2025-01-02"]),
            "symbol": ["AAA"],
            "next_session_date": pd.to_datetime(["2025-01-03"]),
            "entry_available": [True],
        }
    )


def test_missed_buy_is_not_chased_on_later_session() -> None:
    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                ["2025-01-02", "2025-01-03", "2025-01-06"]
            ),
            "symbol": ["AAA", "AAA", "AAA"],
            "open_adj": [100.0, 105.0, 95.0],
            "low_adj": [99.0, 104.0, 90.0],
            "close_adj": [100.0, 104.0, 92.0],
        }
    )
    result = build_execution_portfolio(
        policy_id="P",
        mapped_selections=_mapped(),
        prices=prices,
        config=ExecutionConfig(
            starting_capital=1_000.0,
            buy_limit_premium=0.02,
            fill_mode="touch_fill",
        ),
    )
    assert result.trades.empty
    assert int(result.nav["missed_buy_count"].sum()) == 1
    assert len(result.nav) == 2
    assert result.nav["cash"].tolist() == pytest.approx([1_000.0, 1_000.0])


def test_touch_fill_trade_carries_proxy_metadata() -> None:
    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2025-01-02", "2025-01-03"]),
            "symbol": ["AAA", "AAA"],
            "open_adj": [100.0, 104.0],
            "low_adj": [99.0, 101.0],
            "close_adj": [100.0, 103.0],
        }
    )
    result = build_execution_portfolio(
        policy_id="P",
        mapped_selections=_mapped(),
        prices=prices,
        config=ExecutionConfig(
            starting_capital=10_000.0,
            buy_limit_premium=0.02,
            fill_mode="touch_fill",
        ),
    )
    buy = result.trades.loc[result.trades["side"] == "BUY"].iloc[0]
    assert buy["price"] == pytest.approx(102.0)
    assert buy["buy_limit_price"] == pytest.approx(102.0)
    assert buy["fill_quality"] == "intraday_touch_proxy"
    assert buy["fill_mode"] == "touch_fill"

def test_price_qualified_but_unfunded_buy_is_not_counted_as_fill() -> None:
    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2025-01-02", "2025-01-03"]),
            "symbol": ["AAA", "AAA"],
            "open_adj": [100.0, 100.0],
            "low_adj": [99.0, 99.0],
            "close_adj": [100.0, 100.0],
        }
    )
    # One-share target at the open, but exact fees make the BUY unaffordable.
    result = build_execution_portfolio(
        policy_id="P",
        mapped_selections=_mapped(),
        prices=prices,
        config=ExecutionConfig(
            starting_capital=100.0,
            buy_limit_premium=0.02,
            fill_mode="touch_fill",
        ),
    )
    assert result.trades.empty
    rebalance = result.nav.loc[result.nav["rebalance_flag"]].iloc[0]
    assert int(rebalance["buy_addition_attempt_count"]) == 1
    assert int(rebalance["missed_buy_count"]) == 0
    assert int(rebalance["unfunded_buy_count"]) == 1
    assert int(rebalance["open_buy_fill_count"]) == 0
    assert int(rebalance["touch_buy_fill_count"]) == 0

