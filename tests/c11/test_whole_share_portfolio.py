import pandas as pd
import pytest

from psx_ml.c11.whole_share_portfolio import WholeShareConfig, build_whole_share_portfolio


def _mapped(symbols):
    return pd.DataFrame({
        "policy_id": ["P"] * len(symbols),
        "trade_date": pd.to_datetime(["2025-01-02"] * len(symbols)),
        "symbol": symbols,
        "next_session_date": pd.to_datetime(["2025-01-03"] * len(symbols)),
        "entry_available": [True] * len(symbols),
    })


def test_whole_shares_and_nonnegative_cash() -> None:
    mapped = _mapped(["AAA", "BBB"])
    prices = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-01-03", "2025-01-03"]),
        "symbol": ["AAA", "BBB"],
        "open_adj": [100.0, 200.0],
        "close_adj": [100.0, 200.0],
    })
    result = build_whole_share_portfolio(
        policy_id="P", mapped_selections=mapped, prices=prices,
        config=WholeShareConfig(starting_capital=1_000.0),
    )
    assert (result.trades["shares"] == result.trades["shares"].round()).all()
    assert result.nav.iloc[-1]["cash"] >= 0
    assert result.nav.iloc[-1]["nav_close"] < 1_000.0  # exact fees deducted


def test_price_above_equal_weight_target_is_skipped() -> None:
    mapped = _mapped(["AAA", "EXPENSIVE"])
    prices = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-01-03", "2025-01-03"]),
        "symbol": ["AAA", "EXPENSIVE"],
        "open_adj": [100.0, 800.0],
        "close_adj": [100.0, 800.0],
    })
    result = build_whole_share_portfolio(
        policy_id="P", mapped_selections=mapped, prices=prices,
        config=WholeShareConfig(starting_capital=1_000.0),
    )
    assert "EXPENSIVE" not in set(result.positions["symbol"])
    assert int(result.nav.iloc[0]["skipped_price_count"]) == 1


def test_fee_aware_buys_never_create_leverage() -> None:
    mapped = _mapped(["AAA", "BBB", "CCC"])
    prices = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-01-03"] * 3),
        "symbol": ["AAA", "BBB", "CCC"],
        "open_adj": [1.0, 1.0, 1.0],
        "close_adj": [1.0, 1.0, 1.0],
    })
    result = build_whole_share_portfolio(
        policy_id="P", mapped_selections=mapped, prices=prices,
        config=WholeShareConfig(starting_capital=100.0),
    )
    assert result.nav.iloc[-1]["cash"] >= -1e-9
    assert result.trades["transaction_cost"].sum() > 0


def test_nav_identity() -> None:
    mapped = _mapped(["AAA"])
    prices = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-01-03", "2025-01-06"]),
        "symbol": ["AAA", "AAA"],
        "open_adj": [100.0, 110.0],
        "close_adj": [110.0, 121.0],
    })
    result = build_whole_share_portfolio(
        policy_id="P", mapped_selections=mapped, prices=prices,
        config=WholeShareConfig(starting_capital=1_000.0),
    )
    error = (result.nav["nav_close"] - result.nav["cash"] - result.nav["invested_value"]).abs().max()
    assert error < 1e-9
