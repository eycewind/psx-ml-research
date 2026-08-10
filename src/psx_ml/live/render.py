from __future__ import annotations

import math
import pandas as pd


def _money(value: object) -> str:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return "-"
    if not math.isfinite(x):
        return "-"
    return f"{x:,.2f}"


def render_signal_plan(plan: pd.DataFrame) -> str:
    if plan.empty:
        return "NO TRADES / empty A07 signal plan"
    date = pd.Timestamp(plan["trade_date"].iloc[0]).date().isoformat()
    lines = [
        f"A07 signal plan — {date}",
        f"Targets: {len(plan)}",
        "BUY limits are +2% vs signal close; exact shares deferred to next-session open.",
        "",
    ]
    for r in plan.sort_values(["target_weight", "symbol"], ascending=[False, True]).itertuples():
        lines.append(
            f"{r.symbol}: weight {float(r.target_weight)*100:.2f}% | "
            f"close {_money(r.signal_close)} | max buy {_money(r.buy_limit_price)}"
        )
    return "\n".join(lines)


def render_order_ticket(orders: pd.DataFrame, *, cash_before: float) -> str:
    if orders.empty:
        return "NO ACTION — session-open order ticket is empty"
    execution_date = pd.Timestamp(orders["execution_date"].iloc[0]).date().isoformat()
    final_cash = float(orders["cash_after_planned_orders"].iloc[-1])
    actionable = orders.loc[orders["order_side"].isin(["BUY", "SELL"])].copy()
    lines = [
        f"A07 manual order ticket — {execution_date}",
        f"Cash before: PKR {_money(cash_before)}",
        f"Planned/reserved cash after: PKR {_money(final_cash)}",
        f"Actions: {len(actionable)}",
        "",
    ]
    for r in orders.itertuples():
        if r.order_side == "HOLD":
            continue
        if r.order_side == "SELL":
            lines.append(
                f"SELL {r.symbol} {int(r.order_shares)} @ OPEN | {r.status} | {r.reason}"
            )
        elif r.order_side == "BUY":
            if int(r.order_shares) <= 0:
                lines.append(f"SKIP {r.symbol} | {r.reason}")
            elif r.status == "READY":
                lines.append(
                    f"BUY {r.symbol} {int(r.order_shares)} @ OPEN "
                    f"(open {_money(r.reference_open)}, max {_money(r.buy_limit_price)})"
                )
            else:
                lines.append(
                    f"BUY {r.symbol} {int(r.order_shares)} LIMIT {_money(r.buy_limit_price)} DAY "
                    f"(open {_money(r.reference_open)} above limit; NO CHASE)"
                )
    lines.extend(["", "Manual execution only. Verify broker state before placing orders."])
    return "\n".join(lines)
