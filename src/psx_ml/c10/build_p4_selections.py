from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.p4_selection import (
    P4_POLICY_ID,
    P4SelectionConfig,
    build_p4_selections,
    locate_primary_prediction_file,
)


C9_SELECTIONS = Path(
    "data/processed/c9/candidate_selections.parquet"
)
MEMBERSHIP = Path(
    "data/reference/kmi30_membership_history.parquet"
)
OUTPUT = Path(
    "data/processed/c10/p4_kmi30_selections.parquet"
)
REPORT = Path(
    "artifacts/reports/C10_CP4A_P4_SELECTION_REPORT.md"
)
MANIFEST = Path(
    "artifacts/reports/C10_CP4A_P4_SELECTION_MANIFEST.json"
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


def write_parquet(
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
    prediction_path = (
        locate_primary_prediction_file()
    )

    predictions = pd.read_parquet(
        prediction_path
    )
    membership = pd.read_parquet(
        MEMBERSHIP
    )
    c9 = pd.read_parquet(
        C9_SELECTIONS
    )

    c9["trade_date"] = pd.to_datetime(
        c9["trade_date"],
        errors="raise",
    ).dt.normalize()

    weekly_dates = (
        c9.loc[
            c9["policy_id"]
            == "P1_broad_canonical",
            "trade_date",
        ]
        .drop_duplicates()
        .sort_values()
    )

    config = P4SelectionConfig(
        percentile=0.10,
        sector_cap=2,
        minimum_count=1,
    )

    selections = build_p4_selections(
        predictions=predictions,
        membership=membership,
        weekly_signal_dates=weekly_dates,
        config=config,
    )

    if (
        selections["trade_date"]
        >= pd.Timestamp("2026-01-01")
    ).any():
        raise ValueError(
            "P4 selection accessed 2026 holdout rows"
        )

    if not selections[
        "kmi30_member"
    ].all():
        raise ValueError(
            "Non-KMI-30 row entered P4"
        )

    date_counts = (
        selections.groupby(
            "trade_date"
        )["symbol"]
        .size()
    )

    sector_counts = (
        selections.groupby(
            ["trade_date", "sector"]
        )["symbol"]
        .size()
    )

    if (
        sector_counts
        > config.sector_cap
    ).any():
        raise ValueError(
            "P4 sector cap exceeded"
        )

    write_parquet(
        selections,
        OUTPUT,
    )

    summary = pd.DataFrame(
        {
            "metric": [
                "rows",
                "signal_dates",
                "unique_symbols",
                "minimum_holdings",
                "median_holdings",
                "maximum_holdings",
                "first_signal_date",
                "last_signal_date",
            ],
            "value": [
                len(selections),
                selections[
                    "trade_date"
                ].nunique(),
                selections[
                    "symbol"
                ].nunique(),
                int(date_counts.min()),
                float(date_counts.median()),
                int(date_counts.max()),
                selections[
                    "trade_date"
                ].min().date().isoformat(),
                selections[
                    "trade_date"
                ].max().date().isoformat(),
            ],
        }
    )

    interval_counts = (
        selections.groupby(
            [
                "effective_from",
                "effective_to",
            ]
        )
        .agg(
            selection_rows=(
                "symbol",
                "size",
            ),
            signal_dates=(
                "trade_date",
                "nunique",
            ),
            selected_symbols=(
                "symbol",
                "nunique",
            ),
        )
        .reset_index()
    )

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT.write_text(
        "# C10 CP4A P4 KMI-30 Selection Report\n\n"
        "## Policy\n\n"
        "- Policy ID: `P4_kmi30_strict`\n"
        "- Prediction basis: accepted C8 out-of-fold LightGBM\n"
        "- Target: 5-session market-relative rank\n"
        "- Feature variant: `B_market_context`\n"
        "- Schedule: P1 weekly signal dates\n"
        "- Universe: point-in-time KMI-30 only\n"
        "- Selection: top 10% within effective KMI-30 candidates\n"
        "- Sector cap: maximum 2 selected names per sector\n"
        "- Ties: prediction descending, symbol ascending\n"
        "- Retraining: none\n"
        "- 2026 holdout accessed: false\n\n"
        "## Summary\n\n"
        + summary.to_markdown(index=False)
        + "\n\n## Membership interval coverage\n\n"
        + interval_counts.to_markdown(index=False)
        + "\n",
        encoding="utf-8",
    )

    manifest = {
        "contract": "C10",
        "checkpoint": "CP4A-P4-selection",
        "status": "COMPLETE",
        "policy_id": P4_POLICY_ID,
        "holdout_accessed": False,
        "retraining": False,
        "definition": {
            "model_name": "lightgbm_cpu",
            "horizon": 5,
            "target_family": (
                "market_relative"
            ),
            "feature_variant": (
                "B_market_context"
            ),
            "universe": (
                "point_in_time_kmi30"
            ),
            "selection": (
                "top_10pct_within_kmi30"
            ),
            "sector_cap": 2,
            "schedule": (
                "P1_weekly_signal_dates"
            ),
        },
        "inputs": {
            str(prediction_path): (
                sha256_file(
                    prediction_path
                )
            ),
            str(MEMBERSHIP): (
                sha256_file(
                    MEMBERSHIP
                )
            ),
            str(C9_SELECTIONS): (
                sha256_file(
                    C9_SELECTIONS
                )
            ),
        },
        "output": {
            "path": str(OUTPUT),
            "sha256": sha256_file(
                OUTPUT
            ),
            "rows": int(
                len(selections)
            ),
            "signal_dates": int(
                selections[
                    "trade_date"
                ].nunique()
            ),
            "unique_symbols": int(
                selections[
                    "symbol"
                ].nunique()
            ),
        },
    }

    MANIFEST.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print(
        f"Prediction input: {prediction_path}"
    )
    print(summary.to_string(index=False))
    print()
    print(interval_counts.to_string(index=False))
    print()
    print(
        f"P4 selections: {len(selections):,} "
        f"-> {OUTPUT}"
    )
    print(f"Report: {REPORT}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
