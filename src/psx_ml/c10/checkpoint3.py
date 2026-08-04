from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.costs import (
    COST_SCENARIOS,
    apply_trade_costs,
    build_costed_nav,
    summarize_costed_nav,
)
from psx_ml.c10.inputs import assert_no_holdout


PROCESSED_DIR = Path("data/processed/c10")
REPORT_DIR = Path("artifacts/reports")

GROSS_TRADES_PATH = PROCESSED_DIR / "frictionless_trades.parquet"
GROSS_NAV_PATH = PROCESSED_DIR / "frictionless_nav.parquet"

COSTED_TRADES_PATH = PROCESSED_DIR / "costed_trades.parquet"
COSTED_NAV_PATH = PROCESSED_DIR / "costed_nav.parquet"
COST_SUMMARY_PATH = PROCESSED_DIR / "cost_summary.parquet"

REPORT_PATH = REPORT_DIR / "C10_TRANSACTION_COST_REPORT.md"
MANIFEST_PATH = REPORT_DIR / "C10_CHECKPOINT3_MANIFEST.json"
DELIVERY_PATH = REPORT_DIR / "C10_CHECKPOINT3_DELIVERY.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_parquet_without_filesystem(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    with path.open("wb") as handle:
        pq.write_table(table, handle)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    starting_capital = 1_000_000.0

    gross_trades = pd.read_parquet(GROSS_TRADES_PATH)
    gross_nav = pd.read_parquet(GROSS_NAV_PATH)

    assert_no_holdout(gross_trades)
    assert_no_holdout(gross_nav)

    costed_trade_frames: list[pd.DataFrame] = []
    costed_nav_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    for schedule in COST_SCENARIOS.values():
        scenario_trades = apply_trade_costs(gross_trades, schedule)
        scenario_nav = build_costed_nav(
            gross_nav=gross_nav,
            costed_trades=scenario_trades,
            starting_capital=starting_capital,
        )

        assert_no_holdout(scenario_trades)
        assert_no_holdout(scenario_nav)

        costed_trade_frames.append(scenario_trades)
        costed_nav_frames.append(scenario_nav)

        for policy_id, policy_nav in scenario_nav.groupby(
            "policy_id", sort=False
        ):
            summary = summarize_costed_nav(
                policy_nav,
                starting_capital=starting_capital,
            )
            gross_policy = (
                gross_nav.loc[gross_nav["policy_id"] == policy_id]
                .sort_values("trade_date")
                .reset_index(drop=True)
            )
            summary["ending_gross_nav"] = float(
                gross_policy.iloc[-1]["nav_close"]
            )
            summary["gross_total_return"] = float(
                gross_policy.iloc[-1]["nav_close"]
                / starting_capital
                - 1.0
            )
            summary["ending_nav_cost_drag"] = (
                summary["ending_gross_nav"]
                - summary["ending_net_nav"]
            )
            summary_rows.append(summary)

    costed_trades = pd.concat(costed_trade_frames, ignore_index=True)
    costed_nav = pd.concat(costed_nav_frames, ignore_index=True)
    summary_frame = (
        pd.DataFrame(summary_rows)
        .sort_values(["cost_schedule_id", "policy_id"])
        .reset_index(drop=True)
    )

    write_parquet_without_filesystem(costed_trades, COSTED_TRADES_PATH)
    write_parquet_without_filesystem(costed_nav, COSTED_NAV_PATH)
    write_parquet_without_filesystem(summary_frame, COST_SUMMARY_PATH)

    report = f"""# C10 Transaction Cost Report

## Scope

Checkpoint 3 applies explicit transaction costs to the audited Checkpoint 2 frictionless trade and NAV ledgers.

Baseline actual broker schedule, derived from the user's real transaction ledger:

- commission: 0.15% of transaction value or PKR 0.03/share, whichever is higher;
- SST: 15% of commission;
- CDC: PKR 0.005/share;
- applied independently to buys and sells.

Sensitivity scenarios use 0.20% and 0.25% ad-valorem brokerage while retaining the PKR 0.03 per-share floor.

Configured but currently zero:

- additional notional levies;
- tax on brokerage;
- fixed per-trade fees.

Excluded:

- capital gains tax;
- slippage and bid/ask spread;
- market impact;
- capacity limits;
- board-lot restrictions;
- financing costs.

## Method

For each policy and cost scenario:

1. Calculate exact trade-level brokerage from shares and notional.
2. Aggregate costs by trade date.
3. Convert daily cost to a fraction of the prior gross closing NAV.
4. Deduct the cost fraction before applying that day's gross portfolio return.
5. Compound the resulting net daily return series.

This return-level overlay preserves the audited Checkpoint 2 gross holdings and execution decisions. It does not resize future holdings after costs.

## Results

{summary_frame.to_markdown(index=False)}

## Outputs

- Costed trades: `{COSTED_TRADES_PATH}`
- Costed daily NAV: `{COSTED_NAV_PATH}`
- Cost summary: `{COST_SUMMARY_PATH}`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")

    manifest = {
        "contract": "C10",
        "checkpoint": 3,
        "status": "COMPLETE",
        "holdout_accessed": False,
        "method": "scale_invariant_daily_return_cost_overlay",
        "baseline": "actual_broker_all_in",
        "cost_scenarios": {
            key: value.to_dict() for key, value in COST_SCENARIOS.items()
        },
        "excluded_costs": [
            "capital_gains_tax",
            "slippage",
            "bid_ask_spread",
            "market_impact",
            "capacity_limits",
            "board_lots",
            "financing",
        ],
        "inputs": {
            str(GROSS_TRADES_PATH): sha256_file(GROSS_TRADES_PATH),
            str(GROSS_NAV_PATH): sha256_file(GROSS_NAV_PATH),
        },
        "outputs": {
            str(COSTED_TRADES_PATH): {
                "sha256": sha256_file(COSTED_TRADES_PATH),
                "rows": int(len(costed_trades)),
            },
            str(COSTED_NAV_PATH): {
                "sha256": sha256_file(COSTED_NAV_PATH),
                "rows": int(len(costed_nav)),
            },
            str(COST_SUMMARY_PATH): {
                "sha256": sha256_file(COST_SUMMARY_PATH),
                "rows": int(len(summary_frame)),
            },
        },
        "summaries": summary_frame.to_dict(orient="records"),
    }

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    delivery = """# C10 Checkpoint 3 Delivery

Status: **COMPLETE**

Checkpoint 3 adds:

- exact trade-level PSX minimum brokerage;
- PKR 0.03 per-share brokerage floor;
- 0.15% ad-valorem brokerage minimum;
- buy-side and sell-side cost application;
- 0.20% and 0.25% brokerage sensitivity scenarios;
- daily transaction-cost aggregation;
- net daily return and NAV series;
- gross-versus-net performance summaries;
- explicit holdout protection.

Additional broker levies, taxes on commission, slippage, impact, board lots and capacity remain outside this checkpoint.
"""
    DELIVERY_PATH.write_text(delivery, encoding="utf-8")

    print(summary_frame.to_string(index=False))
    print()
    print(f"Costed trades: {len(costed_trades):,} -> {COSTED_TRADES_PATH}")
    print(f"Costed NAV:    {len(costed_nav):,} -> {COSTED_NAV_PATH}")
    print(f"Summary rows:  {len(summary_frame):,} -> {COST_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
