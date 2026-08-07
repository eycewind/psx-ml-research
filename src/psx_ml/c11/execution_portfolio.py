from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from psx_ml.c10.costs import ACTUAL_BROKER_ALL_IN, CostSchedule
from psx_ml.c10.portfolio import (
    PortfolioResult,
    _build_close_history,
    _build_price_lookup,
    _get_valid_open,
    _resolve_close,
)


@dataclass(frozen=True)
class ExecutionConfig:
    starting_capital: float
    buy_limit_premium: float = 0.02
    fill_mode: str = "touch_fill"
    cash_tolerance: float = 1e-6
    cost_schedule: CostSchedule = ACTUAL_BROKER_ALL_IN


def _trade_cost(*, shares: int, price: float, schedule: CostSchedule) -> dict[str, float]:
    notional = float(shares) * float(price)
    brokerage = max(
        notional * schedule.brokerage_rate,
        float(shares) * schedule.brokerage_per_share,
    )
    sst = brokerage * schedule.sst_rate_on_brokerage
    cdc = float(shares) * schedule.cdc_per_share
    levy = notional * schedule.levy_rate_on_notional
    fixed = schedule.fixed_cost_per_trade
    total = brokerage + sst + cdc + levy + fixed
    return {
        "notional": notional,
        "brokerage": brokerage,
        "sst": sst,
        "cdc": cdc,
        "notional_levy": levy,
        "fixed_trade_cost": fixed,
        "transaction_cost": total,
    }


def _empty_trades() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "policy_id", "starting_capital", "signal_date", "trade_date", "symbol",
        "side", "shares", "price", "notional", "brokerage", "sst", "cdc",
        "notional_levy", "fixed_trade_cost", "transaction_cost", "cash_flow",
        "pre_shares", "post_shares", "target_shares", "target_weight", "reason",
        "deferred_from_date", "buy_limit_price", "fill_mode", "fill_quality",
    ])


def _empty_positions() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "policy_id", "starting_capital", "trade_date", "symbol", "shares",
        "close_adj", "valuation_price_date", "stale_valuation",
        "stale_calendar_days", "market_value", "weight_close", "source_signal_date",
        "rebalance_date", "pending_exit",
    ])


def _empty_nav() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "policy_id", "starting_capital", "trade_date", "nav_close", "cash",
        "invested_value", "daily_return", "cumulative_return", "holdings_count",
        "target_symbol_count", "purchasable_target_count", "skipped_price_count",
        "residual_cash_fraction", "stale_holdings_count", "pending_exit_count",
        "rebalance_flag", "source_signal_date", "transaction_cost",
        "buy_addition_attempt_count", "missed_buy_count", "unfunded_buy_count",
        "open_buy_fill_count", "touch_buy_fill_count",
    ])


def _record_trade(
    rows: list[dict[str, object]],
    *,
    policy_id: str,
    starting_capital: float,
    signal_date: pd.Timestamp,
    trade_date: pd.Timestamp,
    symbol: str,
    side: str,
    shares: int,
    price: float,
    pre_shares: int,
    post_shares: int,
    target_shares: int,
    target_weight: float,
    reason: str,
    schedule: CostSchedule,
    deferred_from_date: pd.Timestamp | None = None,
    buy_limit_price: float | None = None,
    fill_mode: str | None = None,
    fill_quality: str | None = None,
) -> tuple[float, float]:
    if shares <= 0 or int(shares) != shares:
        raise ValueError("Whole-share trade quantity must be a positive integer")

    costs = _trade_cost(shares=int(shares), price=price, schedule=schedule)
    if side == "BUY":
        cash_flow = -(costs["notional"] + costs["transaction_cost"])
    elif side == "SELL":
        cash_flow = costs["notional"] - costs["transaction_cost"]
    else:
        raise ValueError(f"Unexpected side: {side}")

    rows.append({
        "policy_id": policy_id,
        "starting_capital": float(starting_capital),
        "signal_date": signal_date,
        "trade_date": trade_date,
        "symbol": symbol,
        "side": side,
        "shares": int(shares),
        "price": float(price),
        **costs,
        "cash_flow": float(cash_flow),
        "pre_shares": int(pre_shares),
        "post_shares": int(post_shares),
        "target_shares": int(target_shares),
        "target_weight": float(target_weight),
        "reason": reason,
        "deferred_from_date": deferred_from_date,
        "buy_limit_price": buy_limit_price,
        "fill_mode": fill_mode,
        "fill_quality": fill_quality,
    })
    return float(cash_flow), float(costs["transaction_cost"])


def _affordable_buy_shares(
    *, desired_shares: int, price: float, cash: float, schedule: CostSchedule
) -> int:
    lo, hi = 0, max(int(desired_shares), 0)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        costs = _trade_cost(shares=mid, price=price, schedule=schedule)
        needed = costs["notional"] + costs["transaction_cost"]
        if needed <= cash + 1e-12:
            lo = mid
        else:
            hi = mid - 1
    return lo


def resolve_buy_execution(
    *,
    signal_close: float,
    session_open: float,
    session_low: float,
    buy_limit_premium: float,
    fill_mode: str,
) -> tuple[float, str, float] | None:
    """Resolve a one-session BUY without using any later session."""
    values = (signal_close, session_open, session_low, buy_limit_premium)
    if not all(np.isfinite(v) for v in values):
        return None
    if signal_close <= 0 or session_open <= 0 or session_low <= 0:
        return None
    if buy_limit_premium < 0:
        raise ValueError("buy_limit_premium must be non-negative")
    if fill_mode not in {"touch_fill", "open_only"}:
        raise ValueError(f"Unsupported fill_mode: {fill_mode}")

    limit_price = float(signal_close) * (1.0 + float(buy_limit_premium))
    if session_open <= limit_price:
        return float(session_open), "open", float(limit_price)
    if fill_mode == "touch_fill" and session_low <= limit_price:
        return float(limit_price), "intraday_touch_proxy", float(limit_price)
    return None


def build_execution_portfolio(
    *,
    policy_id: str,
    mapped_selections: pd.DataFrame,
    prices: pd.DataFrame,
    config: ExecutionConfig,
) -> PortfolioResult:
    if not np.isfinite(config.starting_capital) or config.starting_capital <= 0:
        raise ValueError("starting_capital must be finite and positive")
    if not np.isfinite(config.buy_limit_premium) or config.buy_limit_premium < 0:
        raise ValueError("buy_limit_premium must be finite and non-negative")
    if config.fill_mode not in {"touch_fill", "open_only"}:
        raise ValueError(f"Unsupported fill_mode: {config.fill_mode}")

    required = {"policy_id", "trade_date", "symbol", "next_session_date", "entry_available"}
    missing = sorted(required - set(mapped_selections.columns))
    if missing:
        raise ValueError(f"Mapped selections missing required columns: {missing}")

    selections = mapped_selections.loc[mapped_selections["policy_id"] == policy_id].copy()
    if selections.empty:
        raise ValueError(f"No mapped selections found for policy {policy_id}")
    if not bool(selections["entry_available"].all()):
        raise ValueError(f"Cannot construct {policy_id}: selected next-session entry unavailable")

    selections["trade_date"] = pd.to_datetime(selections["trade_date"]).dt.normalize()
    selections["next_session_date"] = pd.to_datetime(selections["next_session_date"]).dt.normalize()
    prices = prices.copy()
    prices["trade_date"] = pd.to_datetime(prices["trade_date"]).dt.normalize()

    open_lookup = _build_price_lookup(prices, "open_adj")
    low_lookup = _build_price_lookup(prices, "low_adj")
    close_lookup = _build_price_lookup(prices, "close_adj")
    close_history = _build_close_history(prices)
    market_dates = prices["trade_date"].drop_duplicates().sort_values().reset_index(drop=True)

    schedule_rows = selections[["trade_date", "next_session_date"]].drop_duplicates().sort_values(
        ["next_session_date", "trade_date"]
    )
    if schedule_rows["next_session_date"].duplicated().any():
        raise ValueError("Multiple signal dates map to the same rebalance date")

    schedule: dict[pd.Timestamp, dict[str, object]] = {}
    for row in schedule_rows.itertuples(index=False):
        signal_date = pd.Timestamp(row.trade_date)
        rebalance_date = pd.Timestamp(row.next_session_date)
        schedule[rebalance_date] = {
            "signal_date": signal_date,
            "selected_symbols": set(
                selections.loc[selections["trade_date"] == signal_date, "symbol"].astype(str)
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
            selected_today = set(rebalance_event["selected_symbols"])
            target_symbol_count = len(selected_today)
            for symbol in selected_today:
                pending_exits.pop(symbol, None)

        # Previously deferred exits execute at first later valid open.
        for symbol in sorted(list(pending_exits)):
            if symbol in selected_today:
                continue
            open_price = _get_valid_open(open_lookup, trade_date=valuation_date, symbol=symbol)
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
                s for s in new_symbols
                if _get_valid_open(open_lookup, trade_date=valuation_date, symbol=s) is None
            )
            if missing_new:
                raise ValueError(
                    f"Missing or invalid open_adj for newly selected symbols on "
                    f"{valuation_date.date().isoformat()}: {missing_new}"
                )

            # Full exits first. Missing exit opens remain frozen/pending exactly as C10.
            outgoing = set(holdings) - selected_today
            for symbol in sorted(outgoing):
                open_price = _get_valid_open(open_lookup, trade_date=valuation_date, symbol=symbol)
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
                s for s in holdings
                if _get_valid_open(open_lookup, trade_date=valuation_date, symbol=s) is None
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
                p = _get_valid_open(open_lookup, trade_date=valuation_date, symbol=symbol)
                assert p is not None
                tradable_existing_value += holdings[symbol] * p

            nav_open_before_rebalance_costs = cash + frozen_value + tradable_existing_value
            if not np.isfinite(nav_open_before_rebalance_costs) or nav_open_before_rebalance_costs <= 0:
                raise ValueError("Invalid opening NAV")

            allocatable_value = max(nav_open_before_rebalance_costs - frozen_value, 0.0)
            n = len(tradable_selected)
            target_weight = 1.0 / n if n else 0.0
            target_notional = allocatable_value / n if n else 0.0

            desired: dict[str, int] = {}
            open_prices: dict[str, float] = {}
            for symbol in sorted(tradable_selected):
                p = _get_valid_open(open_lookup, trade_date=valuation_date, symbol=symbol)
                assert p is not None
                open_prices[symbol] = p
                desired[symbol] = max(int(math.floor(target_notional / p)), 0)
                if desired[symbol] >= 1:
                    purchasable_target_count += 1
                else:
                    skipped_price_count += 1

            # Target reductions are sells and provide cash before target additions.
            for symbol in sorted(tradable_selected):
                pre = int(holdings.get(symbol, 0))
                target = desired[symbol]
                if target >= pre:
                    continue
                qty = pre - target
                flow, fee = _record_trade(
                    trade_rows,
                    policy_id=policy_id,
                    starting_capital=config.starting_capital,
                    signal_date=current_signal_date,
                    trade_date=valuation_date,
                    symbol=symbol,
                    side="SELL",
                    shares=qty,
                    price=open_prices[symbol],
                    pre_shares=pre,
                    post_shares=target,
                    target_shares=target,
                    target_weight=target_weight,
                    reason="rebalance_target",
                    schedule=config.cost_schedule,
                )
                cash += flow
                day_cost += fee
                if target:
                    holdings[symbol] = target
                else:
                    holdings.pop(symbol, None)

            # Additions are cash constrained after exact fees; no leverage.
            # CP3 keeps CP2's open-based desired share counts so that the
            # execution rule is the only changed deployment mechanic.
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
                    # The price rule was satisfied, but no whole share could be
                    # funded after exact transaction costs. This is not an
                    # execution-price fill and must not inflate buy_fill_fraction.
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
                    target_weight=target_weight,
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
                    f"{config.starting_capital} on {valuation_date.date().isoformat()}"
                )

        if not holdings:
            # Keep a complete daily NAV series even when all one-session BUY
            # limits miss and the portfolio remains fully in cash.
            nav_close = cash
            daily_return = nav_close / previous_nav_close - 1.0
            nav_rows.append({
                "policy_id": policy_id,
                "starting_capital": float(config.starting_capital),
                "trade_date": valuation_date,
                "nav_close": nav_close,
                "cash": cash,
                "invested_value": 0.0,
                "daily_return": daily_return,
                "cumulative_return": nav_close / config.starting_capital - 1.0,
                "holdings_count": 0,
                "target_symbol_count": target_symbol_count if rebalance_event is not None else np.nan,
                "purchasable_target_count": purchasable_target_count if rebalance_event is not None else np.nan,
                "skipped_price_count": skipped_price_count if rebalance_event is not None else np.nan,
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
            })
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
            market_values[symbol] = holdings[symbol] * float(mark["close_adj"])
            stale_count += int(bool(mark["stale_valuation"]))

        invested = float(sum(market_values.values()))
        nav_close = cash + invested
        if not np.isfinite(nav_close) or nav_close <= 0:
            raise ValueError("Invalid closing NAV")

        for symbol in sorted(holdings):
            mark = close_marks[symbol]
            position_rows.append({
                "policy_id": policy_id,
                "starting_capital": float(config.starting_capital),
                "trade_date": valuation_date,
                "symbol": symbol,
                "shares": int(holdings[symbol]),
                "close_adj": float(mark["close_adj"]),
                "valuation_price_date": pd.Timestamp(mark["valuation_price_date"]),
                "stale_valuation": bool(mark["stale_valuation"]),
                "stale_calendar_days": int(mark["stale_calendar_days"]),
                "market_value": market_values[symbol],
                "weight_close": market_values[symbol] / nav_close,
                "source_signal_date": source_signal_by_symbol[symbol],
                "rebalance_date": rebalance_date_by_symbol[symbol],
                "pending_exit": symbol in pending_exits,
            })

        daily_return = nav_close / previous_nav_close - 1.0
        nav_rows.append({
            "policy_id": policy_id,
            "starting_capital": float(config.starting_capital),
            "trade_date": valuation_date,
            "nav_close": nav_close,
            "cash": cash,
            "invested_value": invested,
            "daily_return": daily_return,
            "cumulative_return": nav_close / config.starting_capital - 1.0,
            "holdings_count": len(holdings),
            "target_symbol_count": target_symbol_count if rebalance_event is not None else np.nan,
            "purchasable_target_count": purchasable_target_count if rebalance_event is not None else np.nan,
            "skipped_price_count": skipped_price_count if rebalance_event is not None else np.nan,
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
        })
        previous_nav_close = nav_close

    trades = pd.DataFrame(trade_rows) if trade_rows else _empty_trades()
    positions = pd.DataFrame(position_rows) if position_rows else _empty_positions()
    nav = pd.DataFrame(nav_rows) if nav_rows else _empty_nav()

    if not trades.empty:
        trades = trades.sort_values(["trade_date", "symbol", "side"]).reset_index(drop=True)
    if not positions.empty:
        positions = positions.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    if not nav.empty:
        nav = nav.sort_values("trade_date").reset_index(drop=True)

    return PortfolioResult(trades=trades, positions=positions, nav=nav)


def summarize_execution_nav(
    nav: pd.DataFrame, *, starting_capital: float
) -> dict[str, float | int | str]:
    if nav.empty:
        raise ValueError("Cannot summarize empty NAV")
    ordered = nav.sort_values("trade_date").reset_index(drop=True)
    returns = ordered["daily_return"].astype(float)
    total_return = float(ordered.iloc[-1]["nav_close"] / starting_capital - 1.0)
    elapsed_days = int((pd.Timestamp(ordered.iloc[-1]["trade_date"]) - pd.Timestamp(ordered.iloc[0]["trade_date"])).days)
    annualized_return = np.nan
    if elapsed_days > 0 and total_return > -1:
        annualized_return = float((1.0 + total_return) ** (365.25 / elapsed_days) - 1.0)
    std = float(returns.std(ddof=1))
    volatility = float(std * np.sqrt(252))
    sharpe = float(returns.mean() / std * np.sqrt(252)) if std > 0 else np.nan
    peak = ordered["nav_close"].cummax()
    drawdown = ordered["nav_close"] / peak - 1.0
    rebalances = ordered.loc[ordered["rebalance_flag"]].copy()
    return {
        "policy_id": str(ordered.iloc[0]["policy_id"]),
        "starting_capital": float(starting_capital),
        "start_date": pd.Timestamp(ordered.iloc[0]["trade_date"]).date().isoformat(),
        "end_date": pd.Timestamp(ordered.iloc[-1]["trade_date"]).date().isoformat(),
        "observations": int(len(ordered)),
        "ending_nav": float(ordered.iloc[-1]["nav_close"]),
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": volatility,
        "sharpe_zero_rf": sharpe,
        "max_drawdown": float(drawdown.min()),
        "rebalance_count": int(ordered["rebalance_flag"].sum()),
        "mean_cash_fraction": float(ordered["residual_cash_fraction"].mean()),
        "median_rebalance_cash_fraction": float(rebalances["residual_cash_fraction"].median()),
        "total_skipped_price_targets": int(rebalances["skipped_price_count"].fillna(0).sum()),
        "rebalance_dates_with_price_skips": int((rebalances["skipped_price_count"].fillna(0) > 0).sum()),
        "total_transaction_cost": float(ordered["transaction_cost"].sum()),
        "stale_position_days": int(ordered["stale_holdings_count"].sum()),
        "pending_exit_days": int((ordered["pending_exit_count"] > 0).sum()),
        "buy_addition_attempts": int(ordered["buy_addition_attempt_count"].sum()),
        "missed_buy_additions": int(ordered["missed_buy_count"].sum()),
        "unfunded_buy_additions": int(ordered["unfunded_buy_count"].sum()),
        "open_buy_fills": int(ordered["open_buy_fill_count"].sum()),
        "touch_buy_fills": int(ordered["touch_buy_fill_count"].sum()),
        "buy_fill_fraction": (
            float(
                (ordered["open_buy_fill_count"].sum() + ordered["touch_buy_fill_count"].sum())
                / ordered["buy_addition_attempt_count"].sum()
            )
            if ordered["buy_addition_attempt_count"].sum() > 0
            else np.nan
        ),
    }
