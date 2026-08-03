import pandas as pd
import pytest

from psx_ml.c10.portfolio import (
    PortfolioConfig,
    build_frictionless_portfolio,
)


def test_rebalance_trades_net_differences_not_full_liquidation() -> None:
    mapped = pd.DataFrame(
        {
            "policy_id": ["P1", "P1", "P1", "P1"],
            "trade_date": pd.to_datetime(
                [
                    "2025-01-02",
                    "2025-01-02",
                    "2025-01-09",
                    "2025-01-09",
                ]
            ),
            "symbol": ["AAA", "BBB", "AAA", "CCC"],
            "next_session_date": pd.to_datetime(
                [
                    "2025-01-03",
                    "2025-01-03",
                    "2025-01-10",
                    "2025-01-10",
                ]
            ),
            "entry_available": [True, True, True, True],
        }
    )

    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                [
                    "2025-01-03",
                    "2025-01-03",
                    "2025-01-10",
                    "2025-01-10",
                    "2025-01-10",
                ]
            ),
            "symbol": ["AAA", "BBB", "AAA", "BBB", "CCC"],
            "open_adj": [100.0, 100.0, 120.0, 80.0, 100.0],
            "close_adj": [100.0, 100.0, 120.0, 80.0, 100.0],
        }
    )

    result = build_frictionless_portfolio(
        policy_id="P1",
        mapped_selections=mapped,
        prices=prices,
        config=PortfolioConfig(starting_capital=1_000.0),
    )

    second = result.trades.loc[
        result.trades["trade_date"] == pd.Timestamp("2025-01-10")
    ].set_index("symbol")

    assert second.loc["BBB", "side"] == "SELL"
    assert second.loc["BBB", "post_shares"] == pytest.approx(0.0)

    assert second.loc["AAA", "pre_shares"] == pytest.approx(5.0)
    assert second.loc["AAA", "post_shares"] == pytest.approx(
        500.0 / 120.0
    )
    assert second.loc["AAA", "side"] == "SELL"

    assert second.loc["CCC", "side"] == "BUY"
    assert second.loc["CCC", "post_shares"] == pytest.approx(5.0)

    assert result.nav.iloc[-1]["nav_close"] == pytest.approx(1_000.0)
