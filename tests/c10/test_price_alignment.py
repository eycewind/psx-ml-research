import pandas as pd

from psx_ml.c10.prices import map_next_session_entries


def test_next_market_session_open_is_used() -> None:
    selections = pd.DataFrame(
        {
            "policy_id": ["P1_broad_canonical"],
            "trade_date": pd.to_datetime(["2025-01-03"]),
            "symbol": ["AAA"],
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
            "open_adj": [100.0, 102.0],
            "close_adj": [101.0, 103.0],
            "volume_adj": [1000.0, 1200.0],
            "adj_factor": [1.0, 1.0],
        }
    )

    result = map_next_session_entries(
        selections,
        prices,
    )

    assert result.loc[0, "next_session_date"] == pd.Timestamp(
        "2025-01-06"
    )
    assert result.loc[0, "entry_open_adj"] == 102.0
    assert bool(result.loc[0, "entry_available"])


def test_missing_symbol_on_next_session_is_explicit() -> None:
    selections = pd.DataFrame(
        {
            "policy_id": ["P1_broad_canonical"],
            "trade_date": pd.to_datetime(["2025-01-03"]),
            "symbol": ["BBB"],
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
            "open_adj": [100.0, 102.0],
            "close_adj": [101.0, 103.0],
            "volume_adj": [1000.0, 1200.0],
            "adj_factor": [1.0, 1.0],
        }
    )

    result = map_next_session_entries(
        selections,
        prices,
    )

    assert not bool(result.loc[0, "entry_available"])
    assert (
        result.loc[0, "entry_missing_reason"]
        == "symbol_missing_on_next_session"
    )
