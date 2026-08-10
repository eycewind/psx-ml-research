from __future__ import annotations

import argparse
from pathlib import Path
import json

import pandas as pd

from psx_ml.c11.live_orders import build_signal_plan, build_session_open_orders
from psx_ml.live.account_state import load_manual_account_state
from psx_ml.live.ntfy_notifier import NtfyConfig, send_ntfy
from psx_ml.live.render import render_order_ticket, render_signal_plan


def _read_frame(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported table format: {path}")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def cmd_signal(args: argparse.Namespace) -> int:
    selections = _read_frame(args.selections)
    closes = _read_frame(args.closes)
    plan = build_signal_plan(
        selections=selections,
        signal_date=args.signal_date,
        signal_closes=closes,
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    plan.to_parquet(out, index=False)
    message = render_signal_plan(plan)
    print(message)
    if args.notify:
        send_ntfy(
            config=NtfyConfig.from_env(),
            title="PSX A07 PLAN READY",
            message=message,
            priority=4,
        )
    return 0


def cmd_open(args: argparse.Namespace) -> int:
    plan = _read_frame(args.plan)
    opens = _read_frame(args.opens)
    state = load_manual_account_state(args.account_state)
    orders = build_session_open_orders(
        signal_plan=plan,
        execution_date=args.execution_date,
        session_opens=opens,
        current_positions=state.positions,
        cash=state.cash_pkr,
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    orders.to_parquet(out, index=False)
    message = render_order_ticket(orders, cash_before=state.cash_pkr)
    print(message)
    if args.notify:
        send_ntfy(
            config=NtfyConfig.from_env(),
            title="PSX A07 ORDER TICKET",
            message=message,
            priority=5,
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manual-live adapter around accepted C11 CP7")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("signal", help="build after-close A07 signal plan")
    s.add_argument("--selections", required=True, help="live P4/P5 selections parquet/csv")
    s.add_argument("--closes", required=True, help="signal-date closes parquet/csv")
    s.add_argument("--signal-date", required=True)
    s.add_argument("--output", default="artifacts/live/latest_signal_plan.parquet")
    s.add_argument("--notify", action="store_true")
    s.set_defaults(func=cmd_signal)

    o = sub.add_parser("open", help="build next-session manual order ticket")
    o.add_argument("--plan", required=True, help="signal-plan parquet")
    o.add_argument("--opens", required=True, help="execution-date opens parquet/csv")
    o.add_argument("--execution-date", required=True)
    o.add_argument("--account-state", default="config/live_account.json")
    o.add_argument("--output", default="artifacts/live/latest_order_ticket.parquet")
    o.add_argument("--notify", action="store_true")
    o.set_defaults(func=cmd_open)
    return p


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
