from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from psx_ml.c10.portfolio import PortfolioResult, _build_close_history, _build_price_lookup, _get_valid_open, _resolve_close
from psx_ml.c11.execution_portfolio import (
    ExecutionConfig,
    _affordable_buy_shares,
    _empty_nav,
    _empty_positions,
    _empty_trades,
    _record_trade,
    resolve_buy_execution,
)


REQUIRED_TARGET_COLUMNS = {
    "policy_id",
    "trade_date",
    "symbol",
    "target_weight",
    "next_session_date",
    "entry_available",
}


def normalize_target_weights(targets: pd.DataFrame) -> pd.DataFrame:
    """Validate one merged target portfolio per signal date.

    `target_weight` is the desired whole-portfolio weight after aggregating
    policy sleeves. Overlapping names must already be merged before this step.
    """
    missing = sorted(REQUIRED_TARGET_COLUMNS - set(targets.columns))
    if missing:
        raise ValueError(f"Weighted targets missing columns: {missing}")

    out = targets.copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.normalize()
    out["next_session_date"] = pd.to_datetime(
        out["next_session_date"]
    ).dt.normalize()
    out["symbol"] = out["symbol"].astype(str)
    out["target_weight"] = pd.to_numeric(
        out["target_weight"], errors="raise"
    ).astype(float)

    if out.duplicated(["policy_id", "trade_date", "symbol"]).any():
        raise ValueError("Duplicate weighted target policy/date/symbol rows")
    if not np.isfinite(out["target_weight"]).all():
        raise ValueError("Non-finite target weights")
    if (out["target_weight"] <= 0).any():
        raise ValueError("Target weights must be positive")
    if not out["entry_available"].astype(bool).all():
        raise ValueError("Weighted target contains unavailable next-session entry")

    sums = out.groupby(["policy_id", "trade_date"])["target_weight"].sum()
    if not np.allclose(sums.to_numpy(), 1.0, atol=1e-10, rtol=0):
        bad = sums.loc[~np.isclose(sums, 1.0, atol=1e-10, rtol=0)]
        raise ValueError(f"Target weights do not sum to 1: {bad.head().to_dict()}")

    return out.sort_values(
        ["policy_id", "trade_date", "symbol"]
    ).reset_index(drop=True)


def build_weighted_execution_portfolio(
    *,
    policy_id: str,
    mapped_targets: pd.DataFrame,
    prices: pd.DataFrame,
    config: ExecutionConfig,
) -> PortfolioResult:
    """CP3 execution mechanics with explicit per-symbol portfolio weights.

    The execution rule remains frozen:
      signal close +2%, touch proxy, next session only, no chase,
      whole shares, exact costs, no leverage.

    Sizing remains CP2/CP3-style next-open whole-share sizing, except target
    notional is based on the supplied aggregated portfolio weights rather than
    equal weight across symbols.
    """
    if not np.isfinite(config.starting_capital) or config.starting_capital <= 0:
        raise ValueError("starting_capital must be finite and positive")
    if config.fill_mode != "touch_fill" or not np.isclose(
        config.buy_limit_premium, 0.02
    ):
        raise ValueError("CP4B supports only the frozen CP3 primary execution rule")

    targets = normalize_target_weights(mapped_targets)
    targets = targets.loc[targets["policy_id"] == policy_id].copy()
    if targets.empty:
        raise ValueError(f"No weighted targets for {policy_id}")

    prices = prices.copy()
    prices["trade_date"] = pd.to_datetime(prices["trade_date"]).dt.normalize()

    open_lookup = _build_price_lookup(prices, "open_adj")
    low_lookup = _build_price_lookup(prices, "low_adj")
    close_lookup = _build_price_lookup(prices, "close_adj")
    close_history = _build_close_history(prices)
    market_dates = prices["trade_date"].drop_duplicates().sort_values().reset_index(drop=True)

    schedule_rows = targets[
        ["trade_date", "next_session_date"]
    ].drop_duplicates().sort_values(["next_session_date", "trade_date"])
    if schedule_rows["next_session_date"].duplicated().any():
        raise ValueError("Multiple signal dates map to the same rebalance date")

    schedule: dict[pd.Timestamp, dict[str, object]] = {}
    for row in schedule_rows.itertuples(index=False):
        signal_date = pd.Timestamp(row.trade_date)
        rebalance_date = pd.Timestamp(row.next_session_date)
        day = targets.loc[targets["trade_date"] == signal_date]
        schedule[rebalance_date] = {
            "signal_date": signal_date,
            "target_weights": dict(
                zip(day["symbol"].astype(str), day["target_weight"].astype(float))
            ),
        }

    first_rebalance = min(schedule)
    valuation_dates = market_dates.loc[market_dates >= first_rebalance]

    holdings: dict[str, int] = {}
    source_signal_by_symbol: dict[str, pd.Timestamp] = {}
    rebalance_date_by_symbol: dict[str, pd.Timestamp] = {}
    pending_exits: dict[str, dict[str, pd.Timestamp]] = {}

    cash = float(config.starting_capital)
    previous_nav_close = float(config.starting_capital)
    current_signal_date: pd.Timestamp | None = None
    trade_rows: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []
    nav_rows: list[dict[str, object]] = []

    for valuation_date_value in valuation_dates:
        valuation_date = pd.Timestamp(valuation_date_value)
        rebalance_event = schedule.get(valuation_date)
        target_weights_today: dict[str, float] = {}
        selected_today: set[str] = set()
        day_cost = 0.0
        target_symbol_count = 0
        purchasable_target_count = 0
        skipped_price_count = 0
        buy_addition_attempt_count = 0
        missed_buy_count = 0
        unfunded_buy_count = 0
        open_buy_fill_count = 0
        touch_buy_fill_count = 0

        if rebalance_event is not None:
            current_signal_date = pd.Timestamp(rebalance_event["signal_date"])
            target_weights_today = dict(rebalance_event["target_weights"])
            selected_today = set(target_weights_today)
            target_symbol_count = len(selected_today)
            for symbol in selected_today:
                pending_exits.pop(symbol, None)

        # Deferred exits use first later valid open exactly as CP3.
        for symbol in sorted(list(pending_exits)):
            if symbol in selected_today:
                continue
            open_price = _get_valid_open(
                open_lookup, trade_date=valuation_date, symbol=symbol
            )
            if open_price is None:
                continue
            pre = int(holdings[symbol])
            flow, fee = _record_trade(
                trade_rows,
                policy_id=policy_id,
                starting_capital=config.starting_capital,
                signal_date=pending_exits[symbol]["signal_date"],
                trade_date=valuation_date,
                symbol=symbol,
                side="SELL",
                shares=pre,
                price=open_price,
                pre_shares=pre,
                post_shares=0,
                target_shares=0,
                target_weight=0.0,
                reason="deferred_exit",
                schedule=config.cost_schedule,
                deferred_from_date=pending_exits[symbol]["deferred_from_date"],
            )
            cash += flow
            day_cost += fee
            holdings.pop(symbol)
            source_signal_by_symbol.pop(symbol, None)
            rebalance_date_by_symbol.pop(symbol, None)
            pending_exits.pop(symbol)

        if rebalance_event is not None:
            assert current_signal_date is not None

            new_symbols = selected_today - set(holdings)
            missing_new = sorted(
                s
                for s in new_symbols
                if _get_valid_open(
                    open_lookup, trade_date=valuation_date, symbol=s
                )
                is None
            )
            if missing_new:
                raise ValueError(
                    "Missing or invalid open_adj for newly selected symbols on "
                    f"{valuation_date.date().isoformat()}: {missing_new}"
                )

            # Full exits first.
            outgoing = set(holdings) - selected_today
            for symbol in sorted(outgoing):
                open_price = _get_valid_open(
                    open_lookup, trade_date=valuation_date, symbol=symbol
                )
                if open_price is None:
                    pending_exits[symbol] = {
                        "signal_date": current_signal_date,
                        "deferred_from_date": valuation_date,
                    }
                    continue
                pre = int(holdings[symbol])
                flow, fee = _record_trade(
                    trade_rows,
                    policy_id=policy_id,
                    starting_capital=config.starting_capital,
                    signal_date=current_signal_date,
                    trade_date=valuation_date,
                    symbol=symbol,
                    side="SELL",
                    shares=pre,
                    price=open_price,
                    pre_shares=pre,
                    post_shares=0,
                    target_shares=0,
                    target_weight=0.0,
                    reason="rebalance_exit",
                    schedule=config.cost_schedule,
                )
                cash += flow
                day_cost += fee
                holdings.pop(symbol)
                source_signal_by_symbol.pop(symbol, None)
                rebalance_date_by_symbol.pop(symbol, None)

            frozen_symbols = {
                s
                for s in holdings
                if _get_valid_open(
                    open_lookup, trade_date=valuation_date, symbol=s
                )
                is None
            }
            frozen_value = 0.0
            for symbol in sorted(frozen_symbols):
                mark = _resolve_close(
                    close_history,
                    symbol=symbol,
                    valuation_date=valuation_date,
                    strictly_before=True,
                )
                frozen_value += holdings[symbol] * float(mark["close_adj"])

            tradable_selected = selected_today - frozen_symbols
            tradable_existing_value = 0.0
            for symbol in sorted(tradable_selected & set(holdings)):
                p = _get_valid_open(
                    open_lookup, trade_date=valuation_date, symbol=symbol
                )
                assert p is not None
                tradable_existing_value += holdings[symbol] * p

            nav_open_before_rebalance_costs = (
                cash + frozen_value + tradable_existing_value
            )
            if (
                not np.isfinite(nav_open_before_rebalance_costs)
                or nav_open_before_rebalance_costs <= 0
            ):
                raise ValueError("Invalid opening NAV")

            allocatable_value = max(
                nav_open_before_rebalance_costs - frozen_value, 0.0
            )

            tradable_weight_sum = sum(
                target_weights_today[s] for s in tradable_selected
            )
            if tradable_selected and tradable_weight_sum <= 0:
                raise ValueError("Invalid tradable target-weight sum")

            desired: dict[str, int] = {}
            effective_weights: dict[str, float] = {}
            open_prices: dict[str, float] = {}
            for symbol in sorted(tradable_selected):
                p = _get_valid_open(
                    open_lookup, trade_date=valuation_date, symbol=symbol
                )
                assert p is not None
                open_prices[symbol] = p

                # Frozen selected holdings remain untouched. The residual
                # allocatable sleeve is distributed among tradable targets
                # in proportion to their original merged target weights.
                effective_weight = (
                    target_weights_today[symbol] / tradable_weight_sum
                )
                effective_weights[symbol] = effective_weight
                target_notional = allocatable_value * effective_weight
                desired[symbol] = max(
                    int(math.floor(target_notional / p)), 0
                )
                if desired[symbol] >= 1:
                    purchasable_target_count += 1
                else:
                    skipped_price_count += 1

            # Reductions first.
            for symbol in sorted(tradable_selected):
                pre = int(holdings.get(symbol, 0))
                target = desired[symbol]
                if target >= pre:
                    continue
                qty = pre - target
                p = open_prices[symbol]
                post = target
                flow, fee = _record_trade(
                    trade_rows,
                    policy_id=policy_id,
                    starting_capital=config.starting_capital,
                    signal_date=current_signal_date,
                    trade_date=valuation_date,
                    symbol=symbol,
                    side="SELL",
                    shares=qty,
                    price=p,
                    pre_shares=pre,
                    post_shares=post,
                    target_shares=target,
                    target_weight=target_weights_today[symbol],
                    reason="rebalance_target",
                    schedule=config.cost_schedule,
                )
                cash += flow
                day_cost += fee
                if post > 0:
                    holdings[symbol] = post
                    source_signal_by_symbol[symbol] = current_signal_date
                    rebalance_date_by_symbol[symbol] = valuation_date
                else:
                    holdings.pop(symbol, None)
                    source_signal_by_symbol.pop(symbol, None)
                    rebalance_date_by_symbol.pop(symbol, None)

            # Additions use the frozen CP3 one-session BUY rule.
            for symbol in sorted(tradable_selected):
                pre = int(holdings.get(symbol, 0))
                target = desired[symbol]
                wanted = target - pre
                if wanted <= 0:
                    if target > 0:
                        source_signal_by_symbol[symbol] = current_signal_date
                        rebalance_date_by_symbol[symbol] = valuation_date
                    continue

                buy_addition_attempt_count += 1
                signal_close = _get_valid_open(
                    close_lookup,
                    trade_date=current_signal_date,
                    symbol=symbol,
                )
                session_low = _get_valid_open(
                    low_lookup,
                    trade_date=valuation_date,
                    symbol=symbol,
                )
                session_open = open_prices[symbol]

                execution = None
                if signal_close is not None and session_low is not None:
                    execution = resolve_buy_execution(
                        signal_close=signal_close,
                        session_open=session_open,
                        session_low=session_low,
                        buy_limit_premium=config.buy_limit_premium,
                        fill_mode=config.fill_mode,
                    )

                if execution is None:
                    missed_buy_count += 1
                    if pre > 0:
                        source_signal_by_symbol[symbol] = current_signal_date
                        rebalance_date_by_symbol[symbol] = valuation_date
                    continue

                buy_price, fill_quality, limit_price = execution
                qty = _affordable_buy_shares(
                    desired_shares=wanted,
                    price=buy_price,
                    cash=cash,
                    schedule=config.cost_schedule,
                )
                if qty <= 0:
                    unfunded_buy_count += 1
                    if pre > 0:
                        source_signal_by_symbol[symbol] = current_signal_date
                        rebalance_date_by_symbol[symbol] = valuation_date
                    continue

                if fill_quality == "open":
                    open_buy_fill_count += 1
                elif fill_quality == "intraday_touch_proxy":
                    touch_buy_fill_count += 1

                post = pre + qty
                flow, fee = _record_trade(
                    trade_rows,
                    policy_id=policy_id,
                    starting_capital=config.starting_capital,
                    signal_date=current_signal_date,
                    trade_date=valuation_date,
                    symbol=symbol,
                    side="BUY",
                    shares=qty,
                    price=buy_price,
                    pre_shares=pre,
                    post_shares=post,
                    target_shares=target,
                    target_weight=target_weights_today[symbol],
                    reason="rebalance_target",
                    schedule=config.cost_schedule,
                    buy_limit_price=limit_price,
                    fill_mode=config.fill_mode,
                    fill_quality=fill_quality,
                )
                cash += flow
                day_cost += fee
                holdings[symbol] = post
                source_signal_by_symbol[symbol] = current_signal_date
                rebalance_date_by_symbol[symbol] = valuation_date

            if abs(cash) <= config.cash_tolerance:
                cash = 0.0
            if cash < -config.cash_tolerance:
                raise ValueError(
                    f"Negative cash {cash} for {policy_id} at capital "
                    f"{config.starting_capital} on "
                    f"{valuation_date.date().isoformat()}"
                )

        if not holdings:
            nav_close = cash
            daily_return = nav_close / previous_nav_close - 1.0
            nav_rows.append(
                {
                    "policy_id": policy_id,
                    "starting_capital": float(config.starting_capital),
                    "trade_date": valuation_date,
                    "nav_close": nav_close,
                    "cash": cash,
                    "invested_value": 0.0,
                    "daily_return": daily_return,
                    "cumulative_return": nav_close / config.starting_capital - 1.0,
                    "holdings_count": 0,
                    "target_symbol_count": (
                        target_symbol_count if rebalance_event is not None else np.nan
                    ),
                    "purchasable_target_count": (
                        purchasable_target_count if rebalance_event is not None else np.nan
                    ),
                    "skipped_price_count": (
                        skipped_price_count if rebalance_event is not None else np.nan
                    ),
                    "residual_cash_fraction": 1.0,
                    "stale_holdings_count": 0,
                    "pending_exit_count": len(pending_exits),
                    "rebalance_flag": rebalance_event is not None,
                    "source_signal_date": current_signal_date,
                    "transaction_cost": day_cost,
                    "buy_addition_attempt_count": buy_addition_attempt_count,
                    "missed_buy_count": missed_buy_count,
                    "unfunded_buy_count": unfunded_buy_count,
                    "open_buy_fill_count": open_buy_fill_count,
                    "touch_buy_fill_count": touch_buy_fill_count,
                }
            )
            previous_nav_close = nav_close
            continue

        market_values: dict[str, float] = {}
        close_marks: dict[str, dict[str, object]] = {}
        stale_count = 0
        for symbol in sorted(holdings):
            mark = _resolve_close(
                close_history,
                symbol=symbol,
                valuation_date=valuation_date,
                strictly_before=False,
            )
            close_marks[symbol] = mark
            market_values[symbol] = (
                holdings[symbol] * float(mark["close_adj"])
            )
            stale_count += int(bool(mark["stale_valuation"]))

        invested = float(sum(market_values.values()))
        nav_close = cash + invested
        if not np.isfinite(nav_close) or nav_close <= 0:
            raise ValueError("Invalid closing NAV")

        for symbol in sorted(holdings):
            mark = close_marks[symbol]
            position_rows.append(
                {
                    "policy_id": policy_id,
                    "starting_capital": float(config.starting_capital),
                    "trade_date": valuation_date,
                    "symbol": symbol,
                    "shares": int(holdings[symbol]),
                    "close_adj": float(mark["close_adj"]),
                    "valuation_price_date": pd.Timestamp(
                        mark["valuation_price_date"]
                    ),
                    "stale_valuation": bool(mark["stale_valuation"]),
                    "stale_calendar_days": int(mark["stale_calendar_days"]),
                    "market_value": market_values[symbol],
                    "weight_close": market_values[symbol] / nav_close,
                    "source_signal_date": source_signal_by_symbol[symbol],
                    "rebalance_date": rebalance_date_by_symbol[symbol],
                    "pending_exit": symbol in pending_exits,
                }
            )

        daily_return = nav_close / previous_nav_close - 1.0
        nav_rows.append(
            {
                "policy_id": policy_id,
                "starting_capital": float(config.starting_capital),
                "trade_date": valuation_date,
                "nav_close": nav_close,
                "cash": cash,
                "invested_value": invested,
                "daily_return": daily_return,
                "cumulative_return": nav_close / config.starting_capital - 1.0,
                "holdings_count": len(holdings),
                "target_symbol_count": (
                    target_symbol_count if rebalance_event is not None else np.nan
                ),
                "purchasable_target_count": (
                    purchasable_target_count if rebalance_event is not None else np.nan
                ),
                "skipped_price_count": (
                    skipped_price_count if rebalance_event is not None else np.nan
                ),
                "residual_cash_fraction": cash / nav_close,
                "stale_holdings_count": stale_count,
                "pending_exit_count": len(pending_exits),
                "rebalance_flag": rebalance_event is not None,
                "source_signal_date": current_signal_date,
                "transaction_cost": day_cost,
                "buy_addition_attempt_count": buy_addition_attempt_count,
                "missed_buy_count": missed_buy_count,
                "unfunded_buy_count": unfunded_buy_count,
                "open_buy_fill_count": open_buy_fill_count,
                "touch_buy_fill_count": touch_buy_fill_count,
            }
        )
        previous_nav_close = nav_close

    trades = pd.DataFrame(trade_rows) if trade_rows else _empty_trades()
    positions = (
        pd.DataFrame(position_rows) if position_rows else _empty_positions()
    )
    nav = pd.DataFrame(nav_rows) if nav_rows else _empty_nav()

    if not trades.empty:
        trades = trades.sort_values(
            ["trade_date", "symbol", "side"]
        ).reset_index(drop=True)
    if not positions.empty:
        positions = positions.sort_values(
            ["trade_date", "symbol"]
        ).reset_index(drop=True)
    if not nav.empty:
        nav = nav.sort_values("trade_date").reset_index(drop=True)

    return PortfolioResult(trades=trades, positions=positions, nav=nav)
