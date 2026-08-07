import pandas as pd
import pytest

from psx_ml.c10.portfolio import (
    PortfolioConfig,
    build_frictionless_portfolio,
    summarize_frictionless_nav,
)


def test_nav_identity_and_daily_returns() -> None:
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
                    "2025-01-03",
                    "2025-01-06",
                ]
            ),
            "symbol": ["AAA", "AAA"],
            "open_adj": [100.0, 110.0],
            "close_adj": [110.0, 121.0],
        }
    )

    result = build_frictionless_portfolio(
        policy_id="P1",
        mapped_selections=mapped,
        prices=prices,
        config=PortfolioConfig(starting_capital=1_000.0),
    )

    nav = result.nav

    assert nav.iloc[0]["nav_close"] == pytest.approx(1_100.0)
    assert nav.iloc[0]["daily_return"] == pytest.approx(0.10)

    assert nav.iloc[1]["nav_close"] == pytest.approx(1_210.0)
    assert nav.iloc[1]["daily_return"] == pytest.approx(0.10)

    assert (
        nav["nav_close"] - nav["cash"] - nav["invested_value"]
    ).abs().max() < 1e-9

    summary = summarize_frictionless_nav(
        nav,
        starting_capital=1_000.0,
    )
    assert summary["total_return"] == pytest.approx(0.21)
