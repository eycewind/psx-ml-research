import pandas as pd
import pytest

from psx_ml.c10.portfolio import build_frictionless_portfolio


def test_unavailable_selected_entry_is_rejected() -> None:
    mapped = pd.DataFrame(
        {
            "policy_id": ["P1"],
            "trade_date": pd.to_datetime(["2025-01-02"]),
            "symbol": ["AAA"],
            "next_session_date": pd.to_datetime(["2025-01-03"]),
            "entry_available": [False],
        }
    )

    prices = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2025-01-03"]),
            "symbol": ["AAA"],
            "open_adj": [100.0],
            "close_adj": [101.0],
        }
    )

    with pytest.raises(ValueError, match="unavailable selected"):
        build_frictionless_portfolio(
            policy_id="P1",
            mapped_selections=mapped,
            prices=prices,
        )


def test_new_selection_still_requires_real_open() -> None:
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
            "trade_date": pd.to_datetime(["2025-01-03"]),
            "symbol": ["AAA"],
            "open_adj": [float("nan")],
            "close_adj": [101.0],
        }
    )

    with pytest.raises(ValueError, match="newly selected"):
        build_frictionless_portfolio(
            policy_id="P1",
            mapped_selections=mapped,
            prices=prices,
        )
