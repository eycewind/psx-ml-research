import pandas as pd
import pytest

from psx_ml.c11.live_orders import (
    PRIMARY_ALLOCATION_ID,
    build_signal_plan,
    build_session_open_orders,
)


def _sel():
    return pd.DataFrame({
        "policy_id": [
            "D_P4_kmi30_strict",
            "D_P4_kmi30_strict",
            "D_P5_shariah_screened",
            "D_P5_shariah_screened",
        ],
        "trade_date": pd.to_datetime(["2025-12-22"] * 4),
        "symbol": ["AAA", "BBB", "AAA", "CCC"],
        "shariah_eligible": [True] * 4,
        "shariah_source": ["kmi30", "kmi30", "screen", "screen"],
        "shariah_confidence": ["high", "high", "medium", "medium"],
    })


def _closes():
    return pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-12-22"] * 3),
        "symbol": ["AAA", "BBB", "CCC"],
        "close_adj": [100.0, 50.0, 25.0],
    })


def test_signal_plan_merges_overlap_and_freezes_limit() -> None:
    out = build_signal_plan(
        selections=_sel(),
        signal_date="2025-12-22",
        signal_closes=_closes(),
    )
    assert set(out["symbol"]) == {"AAA", "BBB", "CCC"}
    assert out["target_weight"].sum() == pytest.approx(1.0)

    w = dict(zip(out["symbol"], out["target_weight"]))
    # P4: 25% / two names = 12.5% each
    # P5: 75% / two names = 37.5% each
    assert w["AAA"] == pytest.approx(0.50)
    assert w["BBB"] == pytest.approx(0.125)
    assert w["CCC"] == pytest.approx(0.375)

    aaa = out.loc[out["symbol"] == "AAA"].iloc[0]
    assert aaa["buy_limit_price"] == pytest.approx(102.0)
    assert bool(aaa["p4_selected"])
    assert bool(aaa["p5_selected"])
    assert aaa["sizing_status"] == "DEFER_TO_SESSION_OPEN"


def test_signal_plan_rejects_non_shariah_input() -> None:
    s = _sel()
    s.loc[s["symbol"] == "CCC", "shariah_eligible"] = False
    with pytest.raises(ValueError):
        build_signal_plan(
            selections=s,
            signal_date="2025-12-22",
            signal_closes=_closes(),
        )


def test_session_open_orders_sells_first_and_respects_buy_limit() -> None:
    plan = build_signal_plan(
        selections=_sel(),
        signal_date="2025-12-22",
        signal_closes=_closes(),
    )
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-12-23"] * 4),
        "symbol": ["AAA", "BBB", "CCC", "OLD"],
        "open_adj": [101.0, 55.0, 24.0, 10.0],
    })
    positions = pd.DataFrame({
        "symbol": ["OLD"],
        "shares": [100],
    })
    orders = build_session_open_orders(
        signal_plan=plan,
        execution_date="2025-12-23",
        session_opens=opens,
        current_positions=positions,
        cash=10_000.0,
    )

    old = orders.loc[orders["symbol"] == "OLD"].iloc[0]
    assert old["order_side"] == "SELL"
    assert old["order_shares"] == 100

    aaa = orders.loc[orders["symbol"] == "AAA"].iloc[0]
    assert aaa["order_side"] == "BUY"
    assert aaa["status"] == "READY"
    assert aaa["order_type"] == "BUY_AT_OPEN"

    bbb = orders.loc[orders["symbol"] == "BBB"].iloc[0]
    assert bbb["order_side"] == "BUY"
    assert bbb["status"] == "LIMIT_WAIT"
    assert bbb["order_type"] == "LIMIT_DAY"
    assert bbb["buy_limit_price"] == pytest.approx(51.0)


def test_session_open_orders_whole_shares_and_nonnegative_cash() -> None:
    plan = build_signal_plan(
        selections=_sel(),
        signal_date="2025-12-22",
        signal_closes=_closes(),
    )
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-12-23"] * 3),
        "symbol": ["AAA", "BBB", "CCC"],
        "open_adj": [100.0, 50.0, 25.0],
    })
    positions = pd.DataFrame({"symbol": pd.Series(dtype=str), "shares": pd.Series(dtype=int)})
    orders = build_session_open_orders(
        signal_plan=plan,
        execution_date="2025-12-23",
        session_opens=opens,
        current_positions=positions,
        cash=1_000.0,
    )
    q = orders.loc[orders["order_side"] == "BUY", "order_shares"]
    assert ((q >= 0) & (q == q.astype(int))).all()
    assert float(orders["cash_after_planned_orders"].iloc[0]) >= -1e-7


def test_session_open_orders_omit_exact_target_hold_rows() -> None:
    plan = build_signal_plan(
        selections=_sel(),
        signal_date="2025-12-22",
        signal_closes=_closes(),
    )
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-12-23"] * 3),
        "symbol": ["AAA", "BBB", "CCC"],
        "open_adj": [100.0, 50.0, 25.0],
    })
    positions = pd.DataFrame({
        "symbol": ["AAA"],
        "shares": [5],
    })
    orders = build_session_open_orders(
        signal_plan=plan,
        execution_date="2025-12-23",
        session_opens=opens,
        current_positions=positions,
        cash=500.0,
    )

    assert "AAA" not in set(orders["symbol"])
    assert "HOLD" not in set(orders["order_side"])


def test_session_open_orders_uses_deployable_capital_not_broker_nav() -> None:
    plan = build_signal_plan(
        selections=_sel(),
        signal_date="2025-12-22",
        signal_closes=_closes(),
    )
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-12-23"] * 4),
        "symbol": ["AAA", "BBB", "CCC", "OLD"],
        "open_adj": [100.0, 50.0, 25.0, 100.0],
    })
    positions = pd.DataFrame({"symbol": ["OLD"], "shares": [340]})

    orders = build_session_open_orders(
        signal_plan=plan,
        execution_date="2025-12-23",
        session_opens=opens,
        current_positions=positions,
        cash=23_800.0,
        deployable_capital_pkr=50_000.0,
    )

    targets = dict(zip(orders["symbol"], orders["target_shares"]))
    assert targets["AAA"] == 250
    assert targets["BBB"] == 125
    assert targets["CCC"] == 750


def test_session_open_orders_extra_broker_cash_does_not_increase_target_shares() -> None:
    plan = build_signal_plan(
        selections=_sel(),
        signal_date="2025-12-22",
        signal_closes=_closes(),
    )
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-12-23"] * 3),
        "symbol": ["AAA", "BBB", "CCC"],
        "open_adj": [100.0, 50.0, 25.0],
    })
    positions = pd.DataFrame({"symbol": pd.Series(dtype=str), "shares": pd.Series(dtype=int)})

    low_cash = build_session_open_orders(
        signal_plan=plan,
        execution_date="2025-12-23",
        session_opens=opens,
        current_positions=positions,
        cash=60_000.0,
        deployable_capital_pkr=50_000.0,
    )
    high_cash = build_session_open_orders(
        signal_plan=plan,
        execution_date="2025-12-23",
        session_opens=opens,
        current_positions=positions,
        cash=160_000.0,
        deployable_capital_pkr=50_000.0,
    )

    low_targets = dict(zip(low_cash["symbol"], low_cash["target_shares"]))
    high_targets = dict(zip(high_cash["symbol"], high_cash["target_shares"]))
    assert high_targets == low_targets


def test_session_open_orders_mari_target_already_held_no_duplicate_buy() -> None:
    plan = pd.DataFrame({
        "allocation_id": [PRIMARY_ALLOCATION_ID],
        "trade_date": pd.to_datetime(["2026-08-18"]),
        "symbol": ["MARI"],
        "target_weight": [0.1333],
        "signal_close": [654.0],
        "buy_limit_price": [667.08],
        "shariah_eligible": [True],
    })
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2026-08-19"]),
        "symbol": ["MARI"],
        "open_adj": [667.0],
    })
    positions = pd.DataFrame({"symbol": ["MARI"], "shares": [9]})

    orders = build_session_open_orders(
        signal_plan=plan,
        execution_date="2026-08-19",
        session_opens=opens,
        current_positions=positions,
        cash=23_688.0,
        deployable_capital_pkr=50_000.0,
    )

    assert orders.empty


def test_session_open_orders_broker_cash_constrains_buy_affordability() -> None:
    plan = pd.DataFrame({
        "allocation_id": [PRIMARY_ALLOCATION_ID],
        "trade_date": pd.to_datetime(["2026-08-18"]),
        "symbol": ["AAA"],
        "target_weight": [1.0],
        "signal_close": [100.0],
        "buy_limit_price": [102.0],
        "shariah_eligible": [True],
    })
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2026-08-19"]),
        "symbol": ["AAA"],
        "open_adj": [100.0],
    })
    positions = pd.DataFrame({"symbol": pd.Series(dtype=str), "shares": pd.Series(dtype=int)})

    orders = build_session_open_orders(
        signal_plan=plan,
        execution_date="2026-08-19",
        session_opens=opens,
        current_positions=positions,
        cash=1_000.0,
        deployable_capital_pkr=50_000.0,
    )
    row = orders.iloc[0]

    assert row["target_shares"] == 500
    assert 0 < row["order_shares"] < 500
    assert row["reason"] == "OPEN_WITHIN_LIMIT_CASH_CLIPPED"
    assert row["cash_after_planned_orders"] >= -1e-7


def test_session_open_orders_lower_cash_changes_executable_not_desired_target() -> None:
    plan = pd.DataFrame({
        "allocation_id": [PRIMARY_ALLOCATION_ID],
        "trade_date": pd.to_datetime(["2026-08-18"]),
        "symbol": ["AAA"],
        "target_weight": [1.0],
        "signal_close": [100.0],
        "buy_limit_price": [102.0],
        "shariah_eligible": [True],
    })
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2026-08-19"]),
        "symbol": ["AAA"],
        "open_adj": [100.0],
    })
    positions = pd.DataFrame({"symbol": pd.Series(dtype=str), "shares": pd.Series(dtype=int)})

    higher_cash = build_session_open_orders(
        signal_plan=plan,
        execution_date="2026-08-19",
        session_opens=opens,
        current_positions=positions,
        cash=10_000.0,
        deployable_capital_pkr=50_000.0,
    )
    lower_cash = build_session_open_orders(
        signal_plan=plan,
        execution_date="2026-08-19",
        session_opens=opens,
        current_positions=positions,
        cash=1_000.0,
        deployable_capital_pkr=50_000.0,
    )

    assert higher_cash.iloc[0]["target_shares"] == 500
    assert lower_cash.iloc[0]["target_shares"] == 500
    assert lower_cash.iloc[0]["order_shares"] < higher_cash.iloc[0]["order_shares"]


def test_session_open_orders_reduces_existing_position_with_deployable_capital() -> None:
    plan = pd.DataFrame({
        "allocation_id": [PRIMARY_ALLOCATION_ID],
        "trade_date": pd.to_datetime(["2026-08-18"]),
        "symbol": ["AAA"],
        "target_weight": [0.20],
        "signal_close": [100.0],
        "buy_limit_price": [102.0],
        "shariah_eligible": [True],
    })
    opens = pd.DataFrame({
        "trade_date": pd.to_datetime(["2026-08-19"]),
        "symbol": ["AAA"],
        "open_adj": [100.0],
    })
    positions = pd.DataFrame({"symbol": ["AAA"], "shares": [150]})

    orders = build_session_open_orders(
        signal_plan=plan,
        execution_date="2026-08-19",
        session_opens=opens,
        current_positions=positions,
        cash=25_000.0,
        deployable_capital_pkr=50_000.0,
    )
    row = orders.iloc[0]

    assert row["order_side"] == "SELL"
    assert row["target_shares"] == 100
    assert row["order_shares"] == 50
