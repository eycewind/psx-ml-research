from __future__ import annotations

import pandas as pd


def build_market_calendar(
    prices: pd.DataFrame,
) -> pd.DataFrame:
    dates = (
        prices[["trade_date"]]
        .drop_duplicates()
        .sort_values("trade_date")
        .reset_index(drop=True)
    )

    dates["next_session_date"] = dates["trade_date"].shift(-1)

    return dates


def map_next_session_entries(
    selections: pd.DataFrame,
    prices: pd.DataFrame,
) -> pd.DataFrame:
    calendar = build_market_calendar(prices)

    result = selections.merge(
        calendar,
        on="trade_date",
        how="left",
        validate="many_to_one",
    )

    execution_prices = prices[
        [
            "trade_date",
            "symbol",
            "open_adj",
            "close_adj",
            "volume_adj",
            "adj_factor",
        ]
    ].rename(
        columns={
            "trade_date": "next_session_date",
            "open_adj": "entry_open_adj",
            "close_adj": "entry_session_close_adj",
            "volume_adj": "entry_volume_adj",
            "adj_factor": "entry_adj_factor",
        }
    )

    result = result.merge(
        execution_prices,
        on=["next_session_date", "symbol"],
        how="left",
        validate="many_to_one",
    )

    result["entry_available"] = (
        result["next_session_date"].notna()
        & result["entry_open_adj"].notna()
        & (result["entry_open_adj"] > 0)
    )

    result["entry_missing_reason"] = pd.NA

    result.loc[
        result["next_session_date"].isna(),
        "entry_missing_reason",
    ] = "no_next_market_session"

    result.loc[
        result["next_session_date"].notna()
        & result["entry_open_adj"].isna(),
        "entry_missing_reason",
    ] = "symbol_missing_on_next_session"

    result.loc[
        result["entry_open_adj"].notna()
        & (result["entry_open_adj"] <= 0),
        "entry_missing_reason",
    ] = "invalid_next_open"

    return result
