from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import numpy as np
import pandas as pd

from psx_ml.c11.capital_allocation import AllocationDefinition, build_allocation_targets


PRIMARY_ALLOCATION_ID = "A07_P4_25_P5_75"
P4 = "D_P4_kmi30_strict"
P5 = "D_P5_shariah_screened"

PRIMARY_DEFINITION = AllocationDefinition(
    PRIMARY_ALLOCATION_ID,
    ((P4, 0.25), (P5, 0.75)),
    "production_primary",
)


@dataclass(frozen=True)
class BrokerCostSchedule:
    commission_rate: float = 0.0015
    commission_min_per_share: float = 0.03
    sst_rate: float = 0.15
    cdc_per_share: float = 0.005


@dataclass(frozen=True)
class LiveOrderConfig:
    buy_limit_premium: float = 0.02
    cost_schedule: BrokerCostSchedule = BrokerCostSchedule()
    cash_tolerance: float = 1e-7


def _norm_date(value: object) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def _validate_signal_rows(rows: pd.DataFrame, signal_date: pd.Timestamp) -> pd.DataFrame:
    required = {
        "policy_id",
        "trade_date",
        "symbol",
        "shariah_eligible",
        "shariah_source",
        "shariah_confidence",
    }
    missing = sorted(required - set(rows.columns))
    if missing:
        raise ValueError(f"Live selections missing columns: {missing}")

    x = rows.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.normalize()
    x["symbol"] = x["symbol"].astype(str)
    x = x.loc[
        (x["trade_date"] == signal_date)
        & x["policy_id"].isin([P4, P5])
    ].copy()

    present = set(x["policy_id"].astype(str))
    if present != {P4, P5}:
        raise ValueError(
            f"Signal date {signal_date.date()} requires both P4 and P5; got {sorted(present)}"
        )
    if x.duplicated(["policy_id", "trade_date", "symbol"]).any():
        raise ValueError("Duplicate live policy/date/symbol selection")
    if not x["shariah_eligible"].astype(bool).all():
        bad = x.loc[
            ~x["shariah_eligible"].astype(bool),
            ["policy_id", "symbol"],
        ]
        raise ValueError(
            "Non-Shariah row entered production selections: "
            + bad.to_string(index=False)
        )
    if x["shariah_source"].isna().any():
        raise ValueError("Production selection missing Shariah provenance")
    if x["shariah_confidence"].isna().any():
        raise ValueError("Production selection missing Shariah confidence")

    return x


def build_signal_plan(
    *,
    selections: pd.DataFrame,
    signal_date: object,
    signal_closes: pd.DataFrame,
    config: LiveOrderConfig = LiveOrderConfig(),
) -> pd.DataFrame:
    """Build the after-close/pre-open A07 production plan.

    This phase freezes:
      - source P4/P5 membership;
      - merged A07 target weights;
      - Shariah provenance;
      - BUY limit = signal close * 1.02.

    It deliberately does NOT invent target share counts before the next
    session's open is known. CP3/CP4B sizing is based on next-session opens.
    """
    signal_date = _norm_date(signal_date)
    source = _validate_signal_rows(selections, signal_date)

    targets = build_allocation_targets(source, PRIMARY_DEFINITION)
    targets = targets.loc[targets["trade_date"] == signal_date].copy()

    close_required = {"trade_date", "symbol", "close_adj"}
    missing = sorted(close_required - set(signal_closes.columns))
    if missing:
        raise ValueError(f"Signal closes missing columns: {missing}")

    closes = signal_closes.copy()
    closes["trade_date"] = pd.to_datetime(closes["trade_date"]).dt.normalize()
    closes["symbol"] = closes["symbol"].astype(str)
    closes = closes.loc[
        closes["trade_date"] == signal_date,
        ["trade_date", "symbol", "close_adj"],
    ].drop_duplicates(["trade_date", "symbol"])

    plan = targets.merge(
        closes,
        on=["trade_date", "symbol"],
        how="left",
        validate="one_to_one",
    )
    plan["signal_close"] = pd.to_numeric(plan["close_adj"], errors="coerce")
    plan = plan.drop(columns=["close_adj"])
    if plan["signal_close"].isna().any() or (plan["signal_close"] <= 0).any():
        bad = plan.loc[
            plan["signal_close"].isna() | (plan["signal_close"] <= 0),
            "symbol",
        ].tolist()
        raise ValueError(f"Missing/invalid signal close for: {bad}")

    provenance = (
        source.sort_values(["symbol", "policy_id"])
        .groupby("symbol")
        .agg(
            shariah_sources=("shariah_source", lambda s: "|".join(sorted(set(map(str, s))))),
            shariah_confidences=("shariah_confidence", lambda s: "|".join(sorted(set(map(str, s))))),
        )
        .reset_index()
    )
    flags = (
        source.assign(
            p4_selected=source["policy_id"].eq(P4),
            p5_selected=source["policy_id"].eq(P5),
        )
        .groupby("symbol", as_index=False)
        .agg(
            p4_selected=("p4_selected", "max"),
            p5_selected=("p5_selected", "max"),
        )
    )
    plan = plan.merge(flags, on="symbol", how="left", validate="one_to_one")
    plan = plan.merge(provenance, on="symbol", how="left", validate="one_to_one")

    plan["allocation_id"] = PRIMARY_ALLOCATION_ID
    plan["shariah_eligible"] = True
    plan["buy_limit_price"] = plan["signal_close"] * (1.0 + config.buy_limit_premium)
    plan["execution_rule"] = "NEXT_SESSION_ONLY_TOUCH_2PCT_NO_CHASE"
    plan["sizing_status"] = "DEFER_TO_SESSION_OPEN"
    plan["status"] = "PLANNED"
    plan["reason"] = "A07_PRIMARY_TARGET"

    columns = [
        "allocation_id",
        "trade_date",
        "symbol",
        "p4_selected",
        "p5_selected",
        "target_weight",
        "sleeve_count",
        "contributing_policies",
        "shariah_eligible",
        "shariah_sources",
        "shariah_confidences",
        "signal_close",
        "buy_limit_price",
        "execution_rule",
        "sizing_status",
        "status",
        "reason",
    ]
    return plan[columns].sort_values(
        ["target_weight", "symbol"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)


def _fee_components(
    *,
    shares: int,
    price: float,
    schedule: BrokerCostSchedule,
) -> dict[str, float]:
    notional = float(shares) * float(price)
    commission = max(
        notional * float(schedule.commission_rate),
        float(shares) * float(schedule.commission_min_per_share),
    )
    sst = commission * float(schedule.sst_rate)
    cdc = float(shares) * float(schedule.cdc_per_share)
    total = commission + sst + cdc
    return {
        "estimated_notional": notional,
        "estimated_commission": commission,
        "estimated_sst": sst,
        "estimated_cdc": cdc,
        "estimated_total_cost": total,
    }


def _affordable_shares(
    *,
    desired: int,
    price: float,
    cash: float,
    schedule: BrokerCostSchedule,
) -> int:
    lo, hi = 0, max(int(desired), 0)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        fees = _fee_components(shares=mid, price=price, schedule=schedule)
        needed = fees["estimated_notional"] + fees["estimated_total_cost"]
        if needed <= cash + 1e-12:
            lo = mid
        else:
            hi = mid - 1
    return lo


def build_session_open_orders(
    *,
    signal_plan: pd.DataFrame,
    execution_date: object,
    session_opens: pd.DataFrame,
    current_positions: pd.DataFrame,
    cash: float,
    deployable_capital_pkr: float | None = None,
    config: LiveOrderConfig = LiveOrderConfig(),
) -> pd.DataFrame:
    """Resolve exact whole-share orders at the next session open.

    By default this preserves the historical CP3/CP4B sizing convention. When
    ``deployable_capital_pkr`` is provided, target share counts use that
    explicit strategy capital mandate instead of broker-account NAV:
      target_shares = floor(deployable_capital_pkr * target_weight / open)
      - target share counts use actual session opens;
      - SELL reductions/exits are resolved first;
      - BUY additions are constrained by remaining cash and exact fees;
      - BUYs are only eligible when open <= the frozen +2% limit.

    Intraday-touch fills cannot be known at the open. Orders whose open is above
    the limit are emitted as LIMIT_WAIT rather than falsely marked missed.
    After the session, the normal execution ledger can classify them as
    intraday-touch fills or misses using the low.
    """
    execution_date = _norm_date(execution_date)

    required_plan = {
        "allocation_id", "trade_date", "symbol", "target_weight",
        "signal_close", "buy_limit_price", "shariah_eligible",
    }
    missing = sorted(required_plan - set(signal_plan.columns))
    if missing:
        raise ValueError(f"Signal plan missing columns: {missing}")
    if set(signal_plan["allocation_id"].astype(str)) != {PRIMARY_ALLOCATION_ID}:
        raise ValueError("Session-open order builder only accepts frozen A07 plan")
    if not signal_plan["shariah_eligible"].astype(bool).all():
        raise ValueError("Non-Shariah target in session-open plan")

    opens_required = {"trade_date", "symbol", "open_adj"}
    missing = sorted(opens_required - set(session_opens.columns))
    if missing:
        raise ValueError(f"Session opens missing columns: {missing}")
    opens = session_opens.copy()
    opens["trade_date"] = pd.to_datetime(opens["trade_date"]).dt.normalize()
    opens["symbol"] = opens["symbol"].astype(str)
    opens = opens.loc[
        opens["trade_date"] == execution_date,
        ["symbol", "open_adj"],
    ].drop_duplicates("symbol")
    open_map = {
        str(r.symbol): float(r.open_adj)
        for r in opens.itertuples(index=False)
        if pd.notna(r.open_adj) and float(r.open_adj) > 0
    }

    pos_required = {"symbol", "shares"}
    missing = sorted(pos_required - set(current_positions.columns))
    if missing:
        raise ValueError(f"Current positions missing columns: {missing}")
    pos = current_positions.copy()
    pos["symbol"] = pos["symbol"].astype(str)
    pos["shares"] = pd.to_numeric(pos["shares"], errors="raise").astype(int)
    if (pos["shares"] < 0).any():
        raise ValueError("Negative current position")
    if pos["symbol"].duplicated().any():
        raise ValueError("Duplicate current position symbol")
    holdings = dict(zip(pos["symbol"], pos["shares"]))

    if not np.isfinite(cash) or cash < 0:
        raise ValueError("cash must be finite and non-negative")
    running_cash = float(cash)

    target = signal_plan.copy()
    target["symbol"] = target["symbol"].astype(str)
    weights = dict(zip(target["symbol"], target["target_weight"].astype(float)))
    limits = dict(zip(target["symbol"], target["buy_limit_price"].astype(float)))
    selected = set(weights)

    # For a production order ticket, every currently held or targeted symbol
    # must have an opening price before exact CP3-style sizing is possible.
    needed_open = set(holdings) | selected
    missing_open = sorted(s for s in needed_open if s not in open_map)
    if missing_open:
        raise ValueError(
            "Exact session-open sizing requires open price for current/target "
            f"symbols; missing: {missing_open}"
        )

    nav_open = running_cash + sum(
        int(shares) * open_map[symbol]
        for symbol, shares in holdings.items()
    )
    if nav_open <= 0:
        raise ValueError("Invalid opening NAV")
    if deployable_capital_pkr is None:
        sizing_capital = nav_open
    else:
        sizing_capital = float(deployable_capital_pkr)
        if not np.isfinite(sizing_capital) or sizing_capital <= 0:
            raise ValueError("deployable_capital_pkr must be finite and positive")

    desired = {
        symbol: max(int(math.floor(sizing_capital * weight / open_map[symbol])), 0)
        for symbol, weight in weights.items()
    }

    rows: list[dict[str, object]] = []

    # Exit/reduction orders first.
    all_symbols = sorted(set(holdings) | selected)
    for symbol in all_symbols:
        current = int(holdings.get(symbol, 0))
        wanted = int(desired.get(symbol, 0))
        if current <= wanted:
            continue
        qty = current - wanted
        price = open_map[symbol]
        fees = _fee_components(
            shares=qty,
            price=price,
            schedule=config.cost_schedule,
        )
        running_cash += fees["estimated_notional"] - fees["estimated_total_cost"]
        rows.append({
            "allocation_id": PRIMARY_ALLOCATION_ID,
            "signal_date": _norm_date(signal_plan["trade_date"].iloc[0]),
            "execution_date": execution_date,
            "symbol": symbol,
            "target_weight": float(weights.get(symbol, 0.0)),
            "current_shares": current,
            "target_shares": wanted,
            "order_side": "SELL",
            "order_shares": qty,
            "order_type": "MARKET_AT_OPEN",
            "reference_open": price,
            "buy_limit_price": np.nan,
            "status": "READY",
            "reason": "REBAlANCE_EXIT" if symbol not in selected else "REBALANCE_REDUCTION",
            **fees,
        })
        holdings[symbol] = wanted

    # BUY additions second, with exact cash/fee constraint.
    for symbol in sorted(selected):
        current = int(holdings.get(symbol, 0))
        wanted = int(desired[symbol])
        delta = wanted - current
        if delta <= 0:
            continue

        open_price = open_map[symbol]
        limit_price = limits[symbol]

        if open_price <= limit_price:
            fill_reference = open_price
            status = "READY"
            order_type = "BUY_AT_OPEN"
            reason = "OPEN_WITHIN_LIMIT"
        else:
            fill_reference = limit_price
            status = "LIMIT_WAIT"
            order_type = "LIMIT_DAY"
            reason = "OPEN_ABOVE_LIMIT_WAIT_FOR_TOUCH"

        affordable = _affordable_shares(
            desired=delta,
            price=fill_reference,
            cash=running_cash,
            schedule=config.cost_schedule,
        )
        if affordable <= 0:
            rows.append({
                "allocation_id": PRIMARY_ALLOCATION_ID,
                "signal_date": _norm_date(signal_plan["trade_date"].iloc[0]),
                "execution_date": execution_date,
                "symbol": symbol,
                "target_weight": float(weights[symbol]),
                "current_shares": current,
                "target_shares": wanted,
                "order_side": "BUY",
                "order_shares": 0,
                "order_type": "NONE",
                "reference_open": open_price,
                "buy_limit_price": limit_price,
                "status": "SKIP",
                "reason": "INSUFFICIENT_CASH",
                "estimated_notional": 0.0,
                "estimated_commission": 0.0,
                "estimated_sst": 0.0,
                "estimated_cdc": 0.0,
                "estimated_total_cost": 0.0,
            })
            continue

        fees = _fee_components(
            shares=affordable,
            price=fill_reference,
            schedule=config.cost_schedule,
        )
        running_cash -= fees["estimated_notional"] + fees["estimated_total_cost"]
        if running_cash < -config.cash_tolerance:
            raise RuntimeError("Order construction produced negative cash")

        rows.append({
            "allocation_id": PRIMARY_ALLOCATION_ID,
            "signal_date": _norm_date(signal_plan["trade_date"].iloc[0]),
            "execution_date": execution_date,
            "symbol": symbol,
            "target_weight": float(weights[symbol]),
            "current_shares": current,
            "target_shares": wanted,
            "order_side": "BUY",
            "order_shares": affordable,
            "order_type": order_type,
            "reference_open": open_price,
            "buy_limit_price": limit_price,
            "status": status,
            "reason": reason if affordable == delta else reason + "_CASH_CLIPPED",
            **fees,
        })
        holdings[symbol] = current + affordable

    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(columns=[
            "allocation_id","signal_date","execution_date","symbol",
            "target_weight","current_shares","target_shares","order_side",
            "order_shares","order_type","reference_open","buy_limit_price",
            "status","reason","estimated_notional","estimated_commission",
            "estimated_sst","estimated_cdc","estimated_total_cost",
        ])

    result["cash_after_planned_orders"] = running_cash
    return result.sort_values(
        ["order_side", "symbol"],
        kind="mergesort",
    ).reset_index(drop=True)
