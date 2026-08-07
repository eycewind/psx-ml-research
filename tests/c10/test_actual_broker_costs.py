import pandas as pd
import pytest

from psx_ml.c10.costs import (
    ACTUAL_BROKER_ALL_IN,
    apply_trade_costs,
)


def test_actual_broker_schedule_matches_agp_buy_record() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2026-06-09"],
            "symbol": ["AGP"],
            "side": ["BUY"],
            "shares": [40.0],
            "notional": [7553.21],
        }
    )

    result = apply_trade_costs(
        trades,
        ACTUAL_BROKER_ALL_IN,
    )

    assert result.loc[0, "brokerage"] == pytest.approx(
        11.329815,
        abs=0.03,
    )
    assert result.loc[0, "sst"] == pytest.approx(
        result.loc[0, "brokerage"] * 0.15
    )
    assert result.loc[0, "cdc"] == pytest.approx(0.20)
    assert result.loc[0, "total_transaction_cost"] == pytest.approx(
        13.21,
        abs=0.05,
    )


def test_actual_broker_schedule_is_close_to_dgkc_buy_record() -> None:
    trades = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": ["2026-06-17"],
            "symbol": ["DGKC"],
            "side": ["BUY"],
            "shares": [225.0],
            "notional": [49530.15],
        }
    )

    result = apply_trade_costs(
        trades,
        ACTUAL_BROKER_ALL_IN,
    )

    # Model uses the nominal 0.15% commission rule.
    assert result.loc[0, "brokerage"] == pytest.approx(
        74.295225,
    )

    assert result.loc[0, "sst"] == pytest.approx(
        result.loc[0, "brokerage"] * 0.15
    )

    assert result.loc[0, "cdc"] == pytest.approx(
        1.125
    )

    # Actual broker ledger total was PKR 86.41.
    # Small variation is allowed because displayed gross/rate values
    # may be rounded or include broker-side adjustments.
    assert result.loc[0, "total_transaction_cost"] == pytest.approx(
        86.41,
        abs=0.20,
    )