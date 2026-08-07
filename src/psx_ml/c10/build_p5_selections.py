from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.p5_selection import (
    C8_PREDICTIONS,
    C9_SELECTIONS,
    DAILY_FEATURES,
    SCREENED_HISTORY,
    P5_POLICY_ID,
    P5Config,
    build_p5_selections,
    load_liquidity,
    load_primary_predictions,
    load_screened_history,
    load_weekly_signal_dates,
)

OUTPUT = Path(
    "data/processed/c10/p5_shariah_screened_selections.parquet"
)
REPORT = Path(
    "artifacts/reports/C10_CP4B_P5_SELECTION_REPORT.md"
)
MANIFEST = Path(
    "artifacts/reports/C10_CP4B_P5_SELECTION_MANIFEST.json"
)

EXPECTED_HASHES = {
    C8_PREDICTIONS:
        "f5420468eb8cce20b8f9bdc1bc19585904993af69bcc95cadb60f28661466ee3",
    C9_SELECTIONS:
        "3ff902152a75d168218850535d4c40da4dd949b54e22ccdfc6560d39646dc520",
    DAILY_FEATURES:
        "0da1b030197519eb01c8623cc4bd3e542c275167e6a7bb89b84c15d01181e9aa",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_parquet(frame: pd.DataFrame, path: Path) -> None:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    with path.open("wb") as handle:
        pq.write_table(table, handle)


def main() -> None:
    for path, expected in EXPECTED_HASHES.items():
        actual = sha256(path)
        if actual != expected:
            raise ValueError(
                f"Input hash mismatch for {path}: {actual} != {expected}"
            )

    config = P5Config()
    weekly_dates = load_weekly_signal_dates()
    predictions = load_primary_predictions(config=config)
    history = load_screened_history()
    liquidity = load_liquidity()

    selections = build_p5_selections(
        predictions,
        history,
        liquidity,
        weekly_dates,
        config,
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_parquet(selections, OUTPUT)

    dates = pd.to_datetime(selections["trade_date"])
    holdings = selections.groupby("trade_date").size()

    confidence = (
        selections.groupby("membership_confidence")
        .agg(
            rows=("symbol", "size"),
            signal_dates=("trade_date", "nunique"),
            unique_symbols=("symbol", "nunique"),
        )
        .reset_index()
    )

    shortfalls = (
        selections[
            ["trade_date", "selection_target_count", "selection_shortfall"]
        ]
        .drop_duplicates()
        .loc[lambda x: x["selection_shortfall"].gt(0)]
    )

    lines = [
        "# C10 CP4B — P5 Selection Report",
        "",
        f"- Policy: `{P5_POLICY_ID}`",
        "- Universe: point-in-time official Shariah-screened universe",
        "- Exact KMI All Share membership claimed: no",
        "- Model: `lightgbm_cpu`",
        "- Horizon: `5`",
        "- Target family: `market_relative`",
        "- Feature variant: `B_market_context`",
        "- Liquidity: exclude bottom 25% by `turnover_median_20obs_adj`",
        "- Selection: top 10% after liquidity filter",
        "- Sector cap: 2",
        "",
        "## Counts",
        "",
        f"- Rows: {len(selections)}",
        f"- Signal dates: {dates.nunique()}",
        f"- Unique symbols: {selections['symbol'].nunique()}",
        f"- Date range: {dates.min().date()} to {dates.max().date()}",
        f"- Holdings/date min: {int(holdings.min())}",
        f"- Holdings/date median: {float(holdings.median()):.1f}",
        f"- Holdings/date max: {int(holdings.max())}",
        f"- Selection shortfall dates: {len(shortfalls)}",
        "",
        "## Membership confidence exposure",
        "",
        "| Confidence | Rows | Signal dates | Unique symbols |",
        "|---|---:|---:|---:|",
    ]

    for row in confidence.itertuples(index=False):
        lines.append(
            f"| {row.membership_confidence} | {row.rows} | "
            f"{row.signal_dates} | {row.unique_symbols} |"
        )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "checkpoint": "C10-CP4B-3-p5-selection",
        "holdout_accessed": False,
        "policy_id": P5_POLICY_ID,
        "definition": (
            "point-in-time Shariah-screened policy; "
            "not exact KMI All Share membership"
        ),
        "inputs": {
            str(path): sha256(path)
            for path in (
                C8_PREDICTIONS,
                C9_SELECTIONS,
                DAILY_FEATURES,
                SCREENED_HISTORY,
            )
        },
        "output": {
            "path": str(OUTPUT),
            "rows": int(len(selections)),
            "sha256": sha256(OUTPUT),
        },
        "signal_dates": int(dates.nunique()),
        "unique_symbols": int(selections["symbol"].nunique()),
        "minimum_holdings": int(holdings.min()),
        "median_holdings": float(holdings.median()),
        "maximum_holdings": int(holdings.max()),
        "selection_shortfall_dates": int(len(shortfalls)),
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("\n".join(lines))
    print(f"\nP5 selections: {len(selections)} -> {OUTPUT}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
