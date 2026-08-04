import pandas as pd

from psx_ml.c10.capacity import (
    attach_point_in_time_liquidity,
)


def test_asof_join_uses_latest_prior_valid_liquidity() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "signal_date": ["2025-01-10"],
            "trade_date": ["2025-01-13"],
            "symbol": ["AAA"],
            "notional": [100.0],
        }
    )

    liquidity = pd.DataFrame(
        {
            "trade_date": [
                "2025-01-08",
                "2025-01-10",
                "2025-01-13",
            ],
            "symbol": ["AAA", "AAA", "AAA"],
            "turnover_median_20obs_adj": [
                1_000.0,
                float("nan"),
                9_999.0,
            ],
        }
    )

    result = attach_point_in_time_liquidity(
        trades,
        liquidity,
    )

    assert result.loc[
        0,
        "liquidity_date",
    ] == pd.Timestamp("2025-01-08")

    assert result.loc[
        0,
        "reference_turnover_20obs",
    ] == 1_000.0

    assert result.loc[
        0,
        "liquidity_age_calendar_days",
    ] == 2

    assert not bool(
        result.loc[
            0,
            "liquidity_exact_date_match",
        ]
    )


def test_asof_join_never_uses_future_liquidity() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "signal_date": ["2025-01-10"],
            "trade_date": ["2025-01-13"],
            "symbol": ["AAA"],
            "notional": [100.0],
        }
    )

    liquidity = pd.DataFrame(
        {
            "trade_date": ["2025-01-13"],
            "symbol": ["AAA"],
            "turnover_median_20obs_adj": [9_999.0],
        }
    )

    result = attach_point_in_time_liquidity(
        trades,
        liquidity,
    )

    assert not bool(
        result.loc[
            0,
            "liquidity_available",
        ]
    )
    assert pd.isna(
        result.loc[
            0,
            "liquidity_date",
        ]
    )
    assert result.loc[
        0,
        "reference_turnover_20obs",
    ] == 0.0


def test_exact_signal_date_liquidity_is_preferred() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "signal_date": ["2025-01-10"],
            "trade_date": ["2025-01-13"],
            "symbol": ["AAA"],
            "notional": [100.0],
        }
    )

    liquidity = pd.DataFrame(
        {
            "trade_date": [
                "2025-01-08",
                "2025-01-10",
            ],
            "symbol": ["AAA", "AAA"],
            "turnover_median_20obs_adj": [
                1_000.0,
                2_000.0,
            ],
        }
    )

    result = attach_point_in_time_liquidity(
        trades,
        liquidity,
    )

    assert result.loc[
        0,
        "reference_turnover_20obs",
    ] == 2_000.0

    assert bool(
        result.loc[
            0,
            "liquidity_exact_date_match",
        ]
    )

    assert result.loc[
        0,
        "liquidity_age_calendar_days",
    ] == 0
