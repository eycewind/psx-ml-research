import pandas as pd
import pytest

from psx_ml.c10.portfolio import (
    PortfolioConfig,
    build_frictionless_portfolio,
)


def test_missing_exit_open_defers_sale_to_first_later_valid_open() -> None:
    mapped = pd.DataFrame(
        {
            "policy_id": ["P1", "P1"],
            "trade_date": pd.to_datetime(
                ["2023-10-16", "2023-10-23"]
            ),
            "symbol": ["SHSML", "AAA"],
            "next_session_date": pd.to_datetime(
                ["2023-10-17", "2023-10-24"]
            ),
            "entry_available": [True, True],
        }
    )

    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                [
                    "2023-10-16",
                    "2023-10-17",
                    "2023-10-23",
                    "2023-10-24",
                    "2023-10-24",
                    "2023-10-25",
                    "2023-10-25",
                ]
            ),
            "symbol": [
                "SHSML",
                "SHSML",
                "SHSML",
                "SHSML",
                "AAA",
                "SHSML",
                "AAA",
            ],
            "open_adj": [
                190.0,
                192.0,
                194.45,
                float("nan"),
                100.0,
                194.85,
                101.0,
            ],
            "close_adj": [
                190.0,
                194.0,
                195.0,
                195.0,
                100.0,
                193.0,
                101.0,
            ],
        }
    )

    result = build_frictionless_portfolio(
        policy_id="P1",
        mapped_selections=mapped,
        prices=prices,
        config=PortfolioConfig(starting_capital=1_000.0),
    )

    shsml_trades = result.trades.loc[
        result.trades["symbol"] == "SHSML"
    ].sort_values("trade_date")

    assert shsml_trades.iloc[0]["side"] == "BUY"
    assert shsml_trades.iloc[0]["trade_date"] == pd.Timestamp(
        "2023-10-17"
    )

    exit_trade = shsml_trades.iloc[-1]
    assert exit_trade["side"] == "SELL"
    assert exit_trade["trade_date"] == pd.Timestamp("2023-10-25")
    assert exit_trade["price"] == pytest.approx(194.85)
    assert exit_trade["reason"] == "deferred_exit"
    assert exit_trade["deferred_from_date"] == pd.Timestamp(
        "2023-10-24"
    )

    blocked_position = result.positions.loc[
        (result.positions["trade_date"] == pd.Timestamp("2023-10-24"))
        & (result.positions["symbol"] == "SHSML")
    ].iloc[0]

    assert bool(blocked_position["pending_exit"])
    assert blocked_position["close_adj"] == pytest.approx(195.0)

    next_day_positions = set(
        result.positions.loc[
            result.positions["trade_date"] == pd.Timestamp("2023-10-25"),
            "symbol",
        ]
    )
    assert "SHSML" not in next_day_positions


def test_deferred_exit_does_not_use_future_open_on_blocked_day() -> None:
    mapped = pd.DataFrame(
        {
            "policy_id": ["P1", "P1"],
            "trade_date": pd.to_datetime(
                ["2025-01-02", "2025-01-09"]
            ),
            "symbol": ["OLD", "NEW"],
            "next_session_date": pd.to_datetime(
                ["2025-01-03", "2025-01-10"]
            ),
            "entry_available": [True, True],
        }
    )

    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                [
                    "2025-01-02",
                    "2025-01-03",
                    "2025-01-09",
                    "2025-01-10",
                    "2025-01-10",
                    "2025-01-13",
                    "2025-01-13",
                ]
            ),
            "symbol": [
                "OLD",
                "OLD",
                "OLD",
                "OLD",
                "NEW",
                "OLD",
                "NEW",
            ],
            "open_adj": [
                90.0,
                100.0,
                105.0,
                float("nan"),
                50.0,
                200.0,
                55.0,
            ],
            "close_adj": [
                90.0,
                100.0,
                105.0,
                105.0,
                50.0,
                200.0,
                55.0,
            ],
        }
    )

    result = build_frictionless_portfolio(
        policy_id="P1",
        mapped_selections=mapped,
        prices=prices,
        config=PortfolioConfig(starting_capital=1_000.0),
    )

    blocked_day_sales = result.trades.loc[
        (result.trades["symbol"] == "OLD")
        & (result.trades["trade_date"] == pd.Timestamp("2025-01-10"))
        & (result.trades["side"] == "SELL")
    ]
    assert blocked_day_sales.empty

    deferred_sale = result.trades.loc[
        (result.trades["symbol"] == "OLD")
        & (result.trades["side"] == "SELL")
    ].iloc[-1]

    assert deferred_sale["trade_date"] == pd.Timestamp("2025-01-13")
    assert deferred_sale["price"] == pytest.approx(200.0)
