import pandas as pd
import pytest

from psx_ml.c10.portfolio import (
    PortfolioConfig,
    build_frictionless_portfolio,
)


def test_initial_rebalance_is_equal_weight() -> None:
    mapped = pd.DataFrame(
        {
            "policy_id": ["P1", "P1"],
            "trade_date": pd.to_datetime(
                ["2025-01-02", "2025-01-02"]
            ),
            "symbol": ["AAA", "BBB"],
            "next_session_date": pd.to_datetime(
                ["2025-01-03", "2025-01-03"]
            ),
            "entry_available": [True, True],
        }
    )

    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                [
                    "2025-01-03",
                    "2025-01-03",
                ]
            ),
            "symbol": ["AAA", "BBB"],
            "open_adj": [100.0, 200.0],
            "close_adj": [110.0, 180.0],
        }
    )

    result = build_frictionless_portfolio(
        policy_id="P1",
        mapped_selections=mapped,
        prices=prices,
        config=PortfolioConfig(starting_capital=1_000.0),
    )

    buys = result.trades.sort_values("symbol").reset_index(drop=True)

    assert buys["side"].tolist() == ["BUY", "BUY"]
    assert buys["notional"].tolist() == pytest.approx([500.0, 500.0])
    assert buys["shares"].tolist() == pytest.approx([5.0, 2.5])
    assert result.nav.iloc[0]["nav_close"] == pytest.approx(1_000.0)
    assert result.nav.iloc[0]["cash"] == pytest.approx(0.0)
