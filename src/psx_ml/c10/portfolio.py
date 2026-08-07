from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PortfolioConfig:
    starting_capital: float = 1_000_000.0
    cash_tolerance: float = 1e-6


@dataclass(frozen=True)
class PortfolioResult:
    trades: pd.DataFrame
    positions: pd.DataFrame
    nav: pd.DataFrame


def _valid_price(value: object) -> bool:
    if pd.isna(value):
        return False
    numeric = float(value)
    return bool(np.isfinite(numeric) and numeric > 0)


def _build_price_lookup(
    prices: pd.DataFrame,
    column: str,
) -> pd.Series:
    required = {"trade_date", "symbol", column}
    missing = sorted(required - set(prices.columns))
    if missing:
        raise ValueError(
            f"Price frame missing required columns for {column}: {missing}"
        )

    if prices.duplicated(["trade_date", "symbol"]).any():
        raise ValueError("Price frame contains duplicate date-symbol rows")

    return prices.set_index(["trade_date", "symbol"])[column]


def _get_valid_open(
    open_lookup: pd.Series,
    *,
    trade_date: pd.Timestamp,
    symbol: str,
) -> float | None:
    key = (trade_date, symbol)
    if key not in open_lookup.index:
        return None

    value = open_lookup.loc[key]
    if not _valid_price(value):
        return None

    return float(value)


def _build_close_history(
    prices: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    required = {"trade_date", "symbol", "close_adj"}
    missing = sorted(required - set(prices.columns))
    if missing:
        raise ValueError(
            f"Price frame missing close history columns: {missing}"
        )

    close_numeric = pd.to_numeric(
        prices["close_adj"],
        errors="coerce",
    )
    valid = prices.loc[
        close_numeric.notna()
        & np.isfinite(close_numeric)
        & (close_numeric > 0),
        ["trade_date", "symbol", "close_adj"],
    ].copy()

    histories: dict[str, pd.DataFrame] = {}

    for symbol, group in valid.groupby("symbol", sort=False):
        histories[str(symbol)] = (
            group.sort_values("trade_date")
            .drop_duplicates("trade_date", keep="last")
            .reset_index(drop=True)
        )

    return histories


def _resolve_close(
    close_history: dict[str, pd.DataFrame],
    *,
    symbol: str,
    valuation_date: pd.Timestamp,
    strictly_before: bool = False,
) -> dict[str, object]:
    history = close_history.get(symbol)
    if history is None or history.empty:
        raise ValueError(
            f"No valid close_adj history for symbol {symbol}"
        )

    dates = history["trade_date"].to_numpy(dtype="datetime64[ns]")
    side = "left" if strictly_before else "right"
    position = int(
        np.searchsorted(
            dates,
            np.datetime64(valuation_date),
            side=side,
        )
        - 1
    )

    if position < 0:
        relation = "prior" if strictly_before else "current or prior"
        raise ValueError(
            f"No {relation} valid close_adj for {symbol} on "
            f"{valuation_date.date().isoformat()}"
        )

    source_date = pd.Timestamp(
        history.iloc[position]["trade_date"]
    )
    close_adj = float(history.iloc[position]["close_adj"])

    return {
        "close_adj": close_adj,
        "valuation_price_date": source_date,
        "stale_valuation": source_date < valuation_date,
        "stale_calendar_days": int(
            (valuation_date - source_date).days
        ),
    }


def _empty_trades() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "policy_id",
            "signal_date",
            "trade_date",
            "symbol",
            "side",
            "shares",
            "price",
            "notional",
            "gross_cash_flow",
            "pre_shares",
            "post_shares",
            "pre_weight_open",
            "target_weight",
            "reason",
            "deferred_from_date",
        ]
    )


def _empty_positions() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "policy_id",
            "trade_date",
            "symbol",
            "shares",
            "close_adj",
            "valuation_price_date",
            "stale_valuation",
            "stale_calendar_days",
            "market_value",
            "weight_close",
            "source_signal_date",
            "rebalance_date",
            "pending_exit",
        ]
    )


def _empty_nav() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "policy_id",
            "trade_date",
            "nav_close",
            "cash",
            "invested_value",
            "daily_return",
            "cumulative_return",
            "holdings_count",
            "stale_holdings_count",
            "pending_exit_count",
            "rebalance_flag",
            "source_signal_date",
        ]
    )


def _record_trade(
    rows: list[dict[str, object]],
    *,
    policy_id: str,
    signal_date: pd.Timestamp,
    trade_date: pd.Timestamp,
    symbol: str,
    side: str,
    shares: float,
    price: float,
    pre_shares: float,
    post_shares: float,
    pre_weight_open: float,
    target_weight: float,
    reason: str,
    deferred_from_date: pd.Timestamp | None = None,
) -> float:
    notional = abs(shares) * price
    gross_cash_flow = -notional if side == "BUY" else notional

    rows.append(
        {
            "policy_id": policy_id,
            "signal_date": signal_date,
            "trade_date": trade_date,
            "symbol": symbol,
            "side": side,
            "shares": abs(shares),
            "price": price,
            "notional": notional,
            "gross_cash_flow": gross_cash_flow,
            "pre_shares": pre_shares,
            "post_shares": post_shares,
            "pre_weight_open": pre_weight_open,
            "target_weight": target_weight,
            "reason": reason,
            "deferred_from_date": deferred_from_date,
        }
    )

    return gross_cash_flow


def build_frictionless_portfolio(
    *,
    policy_id: str,
    mapped_selections: pd.DataFrame,
    prices: pd.DataFrame,
    config: PortfolioConfig = PortfolioConfig(),
) -> PortfolioResult:
    required_selection_columns = {
        "policy_id",
        "trade_date",
        "symbol",
        "next_session_date",
        "entry_available",
    }
    missing = sorted(
        required_selection_columns - set(mapped_selections.columns)
    )
    if missing:
        raise ValueError(
            f"Mapped selections missing required columns: {missing}"
        )

    selections = mapped_selections.loc[
        mapped_selections["policy_id"] == policy_id
    ].copy()

    if selections.empty:
        raise ValueError(f"No mapped selections found for policy {policy_id}")

    if not bool(selections["entry_available"].all()):
        unavailable = selections.loc[
            ~selections["entry_available"],
            ["trade_date", "symbol"],
        ]
        raise ValueError(
            "Cannot construct portfolio with unavailable selected entries: "
            f"{unavailable.to_dict(orient='records')}"
        )

    selections["trade_date"] = pd.to_datetime(
        selections["trade_date"],
        errors="raise",
    ).dt.normalize()
    selections["next_session_date"] = pd.to_datetime(
        selections["next_session_date"],
        errors="raise",
    ).dt.normalize()

    prices = prices.copy()
    prices["trade_date"] = pd.to_datetime(
        prices["trade_date"],
        errors="raise",
    ).dt.normalize()

    open_lookup = _build_price_lookup(prices, "open_adj")
    close_history = _build_close_history(prices)

    market_dates = (
        prices["trade_date"]
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    schedule_rows = (
        selections[
            ["trade_date", "next_session_date"]
        ]
        .drop_duplicates()
        .sort_values(["next_session_date", "trade_date"])
        .reset_index(drop=True)
    )

    if schedule_rows["next_session_date"].duplicated().any():
        raise ValueError(
            f"Policy {policy_id} has multiple signal dates mapping to "
            "the same rebalance date"
        )

    schedule: dict[pd.Timestamp, dict[str, object]] = {}
    for row in schedule_rows.itertuples(index=False):
        signal_date = pd.Timestamp(row.trade_date)
        rebalance_date = pd.Timestamp(row.next_session_date)
        selected = set(
            selections.loc[
                selections["trade_date"] == signal_date,
                "symbol",
            ].astype(str)
        )
        schedule[rebalance_date] = {
            "signal_date": signal_date,
            "selected_symbols": selected,
        }

    first_rebalance_date = min(schedule)
    valuation_dates = market_dates.loc[
        market_dates >= first_rebalance_date
    ]

    holdings: dict[str, float] = {}
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

        if rebalance_event is not None:
            current_signal_date = pd.Timestamp(
                rebalance_event["signal_date"]
            )
            selected_today = set(
                rebalance_event["selected_symbols"]
            )

            for symbol in selected_today:
                pending_exits.pop(symbol, None)

        for symbol in sorted(list(pending_exits)):
            if symbol in selected_today:
                continue

            open_price = _get_valid_open(
                open_lookup,
                trade_date=valuation_date,
                symbol=symbol,
            )
            if open_price is None:
                continue

            pre_shares = float(holdings[symbol])
            cash += _record_trade(
                trade_rows,
                policy_id=policy_id,
                signal_date=pending_exits[symbol]["signal_date"],
                trade_date=valuation_date,
                symbol=symbol,
                side="SELL",
                shares=pre_shares,
                price=open_price,
                pre_shares=pre_shares,
                post_shares=0.0,
                pre_weight_open=np.nan,
                target_weight=0.0,
                reason="deferred_exit",
                deferred_from_date=pending_exits[symbol][
                    "deferred_from_date"
                ],
            )
            holdings.pop(symbol)
            source_signal_by_symbol.pop(symbol, None)
            rebalance_date_by_symbol.pop(symbol, None)
            pending_exits.pop(symbol)

        if rebalance_event is not None:
            assert current_signal_date is not None

            new_symbols = selected_today - set(holdings)
            missing_new_opens = sorted(
                symbol
                for symbol in new_symbols
                if _get_valid_open(
                    open_lookup,
                    trade_date=valuation_date,
                    symbol=symbol,
                )
                is None
            )
            if missing_new_opens:
                raise ValueError(
                    "Missing or invalid open_adj for newly selected symbols "
                    f"on {valuation_date.date().isoformat()}: "
                    f"{missing_new_opens}"
                )

            outgoing = set(holdings) - selected_today
            for symbol in sorted(outgoing):
                open_price = _get_valid_open(
                    open_lookup,
                    trade_date=valuation_date,
                    symbol=symbol,
                )

                if open_price is None:
                    pending_exits[symbol] = {
                        "signal_date": current_signal_date,
                        "deferred_from_date": valuation_date,
                    }
                    continue

                pre_shares = float(holdings[symbol])
                cash += _record_trade(
                    trade_rows,
                    policy_id=policy_id,
                    signal_date=current_signal_date,
                    trade_date=valuation_date,
                    symbol=symbol,
                    side="SELL",
                    shares=pre_shares,
                    price=open_price,
                    pre_shares=pre_shares,
                    post_shares=0.0,
                    pre_weight_open=np.nan,
                    target_weight=0.0,
                    reason="rebalance_exit",
                )
                holdings.pop(symbol)
                source_signal_by_symbol.pop(symbol, None)
                rebalance_date_by_symbol.pop(symbol, None)

            frozen_symbols = {
                symbol
                for symbol in holdings
                if _get_valid_open(
                    open_lookup,
                    trade_date=valuation_date,
                    symbol=symbol,
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
                frozen_value += (
                    holdings[symbol] * float(mark["close_adj"])
                )

            tradable_selected = selected_today - frozen_symbols
            tradable_existing_value = 0.0

            for symbol in sorted(tradable_selected & set(holdings)):
                open_price = _get_valid_open(
                    open_lookup,
                    trade_date=valuation_date,
                    symbol=symbol,
                )
                assert open_price is not None
                tradable_existing_value += (
                    holdings[symbol] * open_price
                )

            nav_open = cash + frozen_value + tradable_existing_value
            if not np.isfinite(nav_open) or nav_open <= 0:
                raise ValueError(
                    f"Invalid opening NAV for {policy_id} on "
                    f"{valuation_date.date().isoformat()}"
                )

            allocatable_value = max(nav_open - frozen_value, 0.0)
            target_weight = (
                1.0 / len(tradable_selected)
                if tradable_selected
                else 0.0
            )
            target_notional = (
                allocatable_value / len(tradable_selected)
                if tradable_selected
                else 0.0
            )

            for symbol in sorted(tradable_selected):
                open_price = _get_valid_open(
                    open_lookup,
                    trade_date=valuation_date,
                    symbol=symbol,
                )
                assert open_price is not None

                pre_shares = float(holdings.get(symbol, 0.0))
                post_shares = target_notional / open_price
                delta_shares = post_shares - pre_shares

                if abs(delta_shares) > 1e-12:
                    side = "BUY" if delta_shares > 0 else "SELL"
                    pre_value = pre_shares * open_price
                    pre_weight_open = pre_value / nav_open

                    cash += _record_trade(
                        trade_rows,
                        policy_id=policy_id,
                        signal_date=current_signal_date,
                        trade_date=valuation_date,
                        symbol=symbol,
                        side=side,
                        shares=delta_shares,
                        price=open_price,
                        pre_shares=pre_shares,
                        post_shares=post_shares,
                        pre_weight_open=pre_weight_open,
                        target_weight=target_weight,
                        reason="rebalance_target",
                    )

                holdings[symbol] = post_shares
                source_signal_by_symbol[symbol] = current_signal_date
                rebalance_date_by_symbol[symbol] = valuation_date

            if abs(cash) <= config.cash_tolerance:
                cash = 0.0

            if cash < -config.cash_tolerance:
                raise ValueError(
                    f"Negative frictionless cash balance {cash} for "
                    f"{policy_id} on {valuation_date.date().isoformat()}"
                )

        if not holdings:
            continue

        market_values: dict[str, float] = {}
        close_marks: dict[str, dict[str, object]] = {}
        stale_holdings_count = 0

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
            stale_holdings_count += int(
                bool(mark["stale_valuation"])
            )

        invested_value = sum(market_values.values())
        nav_close = cash + invested_value

        if not np.isfinite(nav_close) or nav_close <= 0:
            raise ValueError(
                f"Invalid closing NAV for {policy_id} on "
                f"{valuation_date.date().isoformat()}"
            )

        for symbol in sorted(holdings):
            mark = close_marks[symbol]
            position_rows.append(
                {
                    "policy_id": policy_id,
                    "trade_date": valuation_date,
                    "symbol": symbol,
                    "shares": holdings[symbol],
                    "close_adj": float(mark["close_adj"]),
                    "valuation_price_date": pd.Timestamp(
                        mark["valuation_price_date"]
                    ),
                    "stale_valuation": bool(
                        mark["stale_valuation"]
                    ),
                    "stale_calendar_days": int(
                        mark["stale_calendar_days"]
                    ),
                    "market_value": market_values[symbol],
                    "weight_close": market_values[symbol] / nav_close,
                    "source_signal_date": source_signal_by_symbol[symbol],
                    "rebalance_date": rebalance_date_by_symbol[symbol],
                    "pending_exit": symbol in pending_exits,
                }
            )

        daily_return = nav_close / previous_nav_close - 1.0
        cumulative_return = (
            nav_close / config.starting_capital - 1.0
        )

        nav_rows.append(
            {
                "policy_id": policy_id,
                "trade_date": valuation_date,
                "nav_close": nav_close,
                "cash": cash,
                "invested_value": invested_value,
                "daily_return": daily_return,
                "cumulative_return": cumulative_return,
                "holdings_count": len(holdings),
                "stale_holdings_count": stale_holdings_count,
                "pending_exit_count": len(pending_exits),
                "rebalance_flag": rebalance_event is not None,
                "source_signal_date": current_signal_date,
            }
        )

        previous_nav_close = nav_close

    trades = pd.DataFrame(trade_rows) if trade_rows else _empty_trades()
    positions = (
        pd.DataFrame(position_rows)
        if position_rows
        else _empty_positions()
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

    return PortfolioResult(
        trades=trades,
        positions=positions,
        nav=nav,
    )


def summarize_frictionless_nav(
    nav: pd.DataFrame,
    *,
    starting_capital: float,
) -> dict[str, float | int | str]:
    if nav.empty:
        raise ValueError("Cannot summarize an empty NAV series")

    ordered = nav.sort_values("trade_date").reset_index(drop=True)
    daily_returns = ordered["daily_return"].astype(float)

    total_return = float(
        ordered.iloc[-1]["nav_close"] / starting_capital - 1.0
    )
    elapsed_days = int(
        (
            pd.Timestamp(ordered.iloc[-1]["trade_date"])
            - pd.Timestamp(ordered.iloc[0]["trade_date"])
        ).days
    )

    annualized_return = np.nan
    if elapsed_days > 0 and total_return > -1:
        annualized_return = float(
            (1.0 + total_return) ** (365.25 / elapsed_days) - 1.0
        )

    daily_std = float(daily_returns.std(ddof=1))
    annualized_volatility = float(daily_std * np.sqrt(252))

    sharpe_zero_rf = np.nan
    if daily_std > 0:
        sharpe_zero_rf = float(
            daily_returns.mean() / daily_std * np.sqrt(252)
        )

    running_peak = ordered["nav_close"].cummax()
    drawdown = ordered["nav_close"] / running_peak - 1.0

    return {
        "policy_id": str(ordered.iloc[0]["policy_id"]),
        "start_date": pd.Timestamp(
            ordered.iloc[0]["trade_date"]
        ).date().isoformat(),
        "end_date": pd.Timestamp(
            ordered.iloc[-1]["trade_date"]
        ).date().isoformat(),
        "observations": int(len(ordered)),
        "starting_capital": float(starting_capital),
        "ending_nav": float(ordered.iloc[-1]["nav_close"]),
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe_zero_rf": sharpe_zero_rf,
        "max_drawdown": float(drawdown.min()),
        "positive_day_fraction": float(
            (daily_returns > 0).mean()
        ),
        "rebalance_count": int(
            ordered["rebalance_flag"].sum()
        ),
        "stale_position_days": int(
            ordered["stale_holdings_count"].sum()
        ),
        "pending_exit_days": int(
            (ordered["pending_exit_count"] > 0).sum()
        ),
        "max_pending_exits": int(
            ordered["pending_exit_count"].max()
        ),
    }
