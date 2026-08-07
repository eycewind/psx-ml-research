from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.capacity import (
    CAPACITY_SCENARIOS,
    attach_point_in_time_liquidity,
    build_policy_capacity_limits,
    evaluate_capacity_scenario,
    summarize_capacity,
)
from psx_ml.c10.inputs import (
    FEATURE_PATH,
    assert_no_holdout,
)


PROCESSED_DIR = Path("data/processed/c10")
REPORT_DIR = Path("artifacts/reports")

GROSS_TRADES_PATH = (
    PROCESSED_DIR
    / "frictionless_trades.parquet"
)

DIAGNOSTICS_PATH = (
    PROCESSED_DIR
    / "capacity_trade_diagnostics.parquet"
)
SUMMARY_PATH = (
    PROCESSED_DIR
    / "capacity_summary.parquet"
)
LIMITS_PATH = (
    PROCESSED_DIR
    / "capacity_limits.parquet"
)

REPORT_PATH = (
    REPORT_DIR
    / "C10_CAPACITY_REPORT.md"
)
MANIFEST_PATH = (
    REPORT_DIR
    / "C10_CHECKPOINT4_MANIFEST.json"
)
DELIVERY_PATH = (
    REPORT_DIR
    / "C10_CHECKPOINT4_DELIVERY.md"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def write_parquet_without_filesystem(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    table = pa.Table.from_pandas(
        frame,
        preserve_index=False,
    )

    with path.open("wb") as handle:
        pq.write_table(
            table,
            handle,
        )


def main() -> None:
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    trades = pd.read_parquet(
        GROSS_TRADES_PATH
    )

    liquidity = pd.read_parquet(
        FEATURE_PATH,
        columns=[
            "trade_date",
            "symbol",
            "turnover_median_20obs_adj",
        ],
    )

    assert_no_holdout(trades)

    attached = attach_point_in_time_liquidity(
        trades,
        liquidity,
    )

    diagnostic_frames: list[
        pd.DataFrame
    ] = []

    for scenario in CAPACITY_SCENARIOS:
        diagnostics = evaluate_capacity_scenario(
            attached,
            scenario,
        )

        assert_no_holdout(
            diagnostics
        )

        diagnostic_frames.append(
            diagnostics
        )

    all_diagnostics = pd.concat(
        diagnostic_frames,
        ignore_index=True,
    )

    summary = summarize_capacity(
        all_diagnostics
    )

    limits = build_policy_capacity_limits(
        attached
    )

    write_parquet_without_filesystem(
        all_diagnostics,
        DIAGNOSTICS_PATH,
    )
    write_parquet_without_filesystem(
        summary,
        SUMMARY_PATH,
    )
    write_parquet_without_filesystem(
        limits,
        LIMITS_PATH,
    )

    compact = summary[
        [
            "scenario_id",
            "policy_id",
            "portfolio_capital",
            "participation_rate",
            "fully_feasible_fraction",
            "notional_fill_fraction",
            "capacity_breach_trades",
            "breach_date_count",
        ]
    ]

    report = f"""# C10 Liquidity and Capacity Report

## Scope

Checkpoint 4 measures whether the frozen P1, P2, P4 and P5 trade ledgers can be executed at larger portfolio sizes.

Capacity reference:

- `turnover_median_20obs_adj`
- joined using each trade's `signal_date`
- no execution-day or future turnover is used

Participation scenarios:

- 5% of reference turnover
- 10% of reference turnover
- 20% of reference turnover

Portfolio capital scenarios:

- PKR 1 million
- PKR 5 million
- PKR 10 million
- PKR 25 million
- PKR 50 million

Missing or non-positive liquidity is treated as zero executable capacity.

## Method

For each trade:

1. Scale the Checkpoint 2 trade notional by portfolio capital.
2. Compute capacity as point-in-time median turnover multiplied by the participation cap.
3. Compute the maximum executable notional and fill ratio.
4. Record full feasibility, capacity breach and unfilled notional.

This checkpoint is diagnostic only. It does not yet feed partial fills back into holdings, cash or NAV.

## Scenario summary

{compact.to_markdown(index=False)}

## Implied policy capacity limits

{limits.to_markdown(index=False)}

## Outputs

- Trade diagnostics: `{DIAGNOSTICS_PATH}`
- Scenario summary: `{SUMMARY_PATH}`
- Capacity limits: `{LIMITS_PATH}`
"""

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    manifest = {
        "contract": "C10",
        "checkpoint": 4,
        "status": "COMPLETE",
        "holdout_accessed": False,
        "liquidity_basis": (
            "signal_date_turnover_median_20obs_adj"
        ),
        "missing_liquidity_policy": (
            "zero_capacity"
        ),
        "capacity_is_diagnostic_only": True,
        "scenarios": [
            scenario.to_dict()
            for scenario
            in CAPACITY_SCENARIOS
        ],
        "inputs": {
            str(GROSS_TRADES_PATH): (
                sha256_file(
                    GROSS_TRADES_PATH
                )
            ),
            str(FEATURE_PATH): (
                sha256_file(
                    FEATURE_PATH
                )
            ),
        },
        "outputs": {
            str(DIAGNOSTICS_PATH): {
                "sha256": sha256_file(
                    DIAGNOSTICS_PATH
                ),
                "rows": int(
                    len(all_diagnostics)
                ),
            },
            str(SUMMARY_PATH): {
                "sha256": sha256_file(
                    SUMMARY_PATH
                ),
                "rows": int(
                    len(summary)
                ),
            },
            str(LIMITS_PATH): {
                "sha256": sha256_file(
                    LIMITS_PATH
                ),
                "rows": int(
                    len(limits)
                ),
            },
        },
        "summary": summary.to_dict(
            orient="records"
        ),
        "capacity_limits": limits.to_dict(
            orient="records"
        ),
    }

    MANIFEST_PATH.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    delivery = """# C10 Checkpoint 4 Delivery

Status: **COMPLETE**

Checkpoint 4 adds:

- point-in-time liquidity joins;
- signal-date 20-session median turnover capacity reference;
- 5%, 10% and 20% participation scenarios;
- PKR 1m, 5m, 10m, 25m and 50m capital scenarios;
- trade-level fill ratios and unfilled notional;
- policy-level feasibility summaries;
- implied capital limits at multiple trade-feasibility percentiles;
- conservative zero capacity for missing liquidity;
- explicit confirmation that 2026 remained inaccessible.

This checkpoint does not yet alter portfolio holdings or NAV for partial fills.
"""

    DELIVERY_PATH.write_text(
        delivery,
        encoding="utf-8",
    )

    print(
        compact.to_string(
            index=False
        )
    )
    print()
    print("Capacity limits:")
    print(
        limits.to_string(
            index=False
        )
    )
    print()
    print(
        f"Diagnostics: {len(all_diagnostics):,} "
        f"-> {DIAGNOSTICS_PATH}"
    )
    print(
        f"Summary:     {len(summary):,} "
        f"-> {SUMMARY_PATH}"
    )
    print(
        f"Limits:      {len(limits):,} "
        f"-> {LIMITS_PATH}"
    )


if __name__ == "__main__":
    main()
