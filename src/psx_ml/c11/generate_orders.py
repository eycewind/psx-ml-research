from __future__ import annotations

import argparse
from pathlib import Path
import json

import pandas as pd

from psx_ml.c11.live_orders import build_signal_plan, build_session_open_orders


def _read(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(p)
    if p.suffix.lower() == ".csv":
        return pd.read_csv(p)
    raise ValueError(f"Unsupported input: {p}")


def _write(df: pd.DataFrame, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() == ".parquet":
        df.to_parquet(p, index=False)
    elif p.suffix.lower() == ".csv":
        df.to_csv(p, index=False)
    elif p.suffix.lower() == ".json":
        p.write_text(
            json.dumps(df.to_dict(orient="records"), indent=2, default=str) + "\n",
            encoding="utf-8",
        )
    else:
        raise ValueError(f"Unsupported output: {p}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="C11 CP7 frozen A07 production order generator"
    )
    sub = ap.add_subparsers(dest="phase", required=True)

    plan = sub.add_parser("plan", help="after-close signal plan")
    plan.add_argument("--signal-date", required=True)
    plan.add_argument("--selections", required=True)
    plan.add_argument("--closes", required=True)
    plan.add_argument("--out", required=True)

    orders = sub.add_parser("orders", help="next-session open order ticket")
    orders.add_argument("--execution-date", required=True)
    orders.add_argument("--signal-plan", required=True)
    orders.add_argument("--opens", required=True)
    orders.add_argument("--positions", required=True)
    orders.add_argument("--cash", required=True, type=float)
    orders.add_argument("--out", required=True)

    args = ap.parse_args()

    if args.phase == "plan":
        result = build_signal_plan(
            selections=_read(args.selections),
            signal_date=args.signal_date,
            signal_closes=_read(args.closes),
        )
    else:
        result = build_session_open_orders(
            signal_plan=_read(args.signal_plan),
            execution_date=args.execution_date,
            session_opens=_read(args.opens),
            current_positions=_read(args.positions),
            cash=args.cash,
        )

    _write(result, args.out)
    print(result.to_string(index=False))
    print(f"\nWrote {len(result)} rows -> {args.out}")


if __name__ == "__main__":
    main()
