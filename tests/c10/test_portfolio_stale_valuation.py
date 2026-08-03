import pandas as pd
import pytest

from psx_ml.c10.portfolio import (
    PortfolioConfig,
    build_frictionless_portfolio,
)


def test_missing_current_close_carries_prior_close_without_lookahead() -> None:
    mapped = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": pd.to_datetime(["2025-01-02"]),
            "symbol": ["AAA"],
            "next_session_date": pd.to_datetime(["2025-01-03"]),
            "entry_available": [True],
        }
    )

    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                [
                    "2025-01-02",
                    "2025-01-03",
                    "2025-01-06",
                    "2025-01-07",
                ]
            ),
            "symbol": ["AAA", "AAA", "AAA", "AAA"],
            "open_adj": [99.0, 100.0, 100.0, 120.0],
            "close_adj": [99.0, 101.0, float("nan"), 121.0],
        }
    )

    result = build_frictionless_portfolio(
        policy_id="P1",
        mapped_selections=mapped,
        prices=prices,
        config=PortfolioConfig(starting_capital=1_000.0),
    )

    stale_position = result.positions.loc[
        result.positions["trade_date"] == pd.Timestamp("2025-01-06")
    ].iloc[0]

    assert stale_position["close_adj"] == pytest.approx(101.0)
    assert stale_position["valuation_price_date"] == pd.Timestamp(
        "2025-01-03"
    )
    assert bool(stale_position["stale_valuation"])
    assert stale_position["stale_calendar_days"] == 3

    stale_nav = result.nav.loc[
        result.nav["trade_date"] == pd.Timestamp("2025-01-06")
    ].iloc[0]

    assert stale_nav["nav_close"] == pytest.approx(1_010.0)
    assert stale_nav["stale_holdings_count"] == 1

    next_nav = result.nav.loc[
        result.nav["trade_date"] == pd.Timestamp("2025-01-07")
    ].iloc[0]

    assert next_nav["nav_close"] == pytest.approx(1_210.0)
    assert next_nav["stale_holdings_count"] == 0
