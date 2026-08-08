from __future__ import annotations
from pathlib import Path
import hashlib, json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from psx_ml.c11.concentration_overlap import (
    pairwise_selection_overlap,
    realized_concentration_by_date,
    summarize_concentration,
    target_concentration_by_date,
)

DEPLOYMENT = Path("data/processed/c11/deployment_selections.parquet")
TARGETS = Path("data/processed/c11/cp4b_allocation_targets.parquet")
POSITIONS = Path("data/processed/c11/cp4b_execution_positions.parquet")
CP4A_MANIFEST = Path("artifacts/reports/C11_CP4A_SHARIAH_SELECTION_MANIFEST.json")
CP4B_MANIFEST = Path("artifacts/reports/C11_CP4B_CAPITAL_ALLOCATION_MANIFEST.json")
OUT_TARGET_DAILY = Path("data/processed/c11/cp5_target_concentration_daily.parquet")
OUT_REALIZED_DAILY = Path("data/processed/c11/cp5_realized_concentration_daily.parquet")
OUT_OVERLAP_DAILY = Path("data/processed/c11/cp5_policy_overlap_daily.parquet")
OUT_SUMMARY = Path("data/processed/c11/cp5_concentration_summary.parquet")
OUT_OVERLAP_SUMMARY = Path("data/processed/c11/cp5_policy_overlap_summary.parquet")
REPORT = Path("artifacts/reports/C11_CP5_CONCENTRATION_OVERLAP_REPORT.md")
MANIFEST = Path("artifacts/reports/C11_CP5_CONCENTRATION_OVERLAP_MANIFEST.json")

SOURCE_POLICIES = [
    "D_P1_shariah_filter", "D_P1_shariah_refill",
    "D_P2_shariah_filter", "D_P2_shariah_refill",
    "D_P4_kmi30_strict", "D_P5_shariah_screened",
]
FOCUS_ALLOCATIONS = [
    "A05_P4", "A06_P5", "A07_P4_25_P5_75",
    "A16_P2F_P4_P5_equal", "A17_P2R_P4_P5_equal",
]
CAPITAL_FOR_FOCUS = 1_000_000.0

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _write(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    with path.open("wb") as f:
        pq.write_table(table, f)

def main() -> None:
    deployment = pd.read_parquet(DEPLOYMENT)
    targets = pd.read_parquet(TARGETS)
    positions = pd.read_parquet(POSITIONS)
    for df in (deployment, targets, positions):
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.normalize()
        if (df["trade_date"] >= pd.Timestamp("2026-01-01")).any():
            raise ValueError("2026 row in CP5 input")

    sectors = deployment[["trade_date", "symbol", "sector"]].copy()
    non_null = sectors.dropna(subset=["sector"])
    conflicts = non_null.groupby(["trade_date", "symbol"])["sector"].nunique()
    if (conflicts > 1).any():
        raise ValueError(f"Conflicting sector labels: {conflicts.loc[conflicts > 1].head().to_dict()}")
    sector_map = (
        sectors.sort_values(["trade_date", "symbol"])
        .drop_duplicates(["trade_date", "symbol"], keep="first")
    )

    target_daily = target_concentration_by_date(targets, sector_map)
    realized_daily = realized_concentration_by_date(positions, sector_map)
    overlap_daily = pairwise_selection_overlap(deployment, SOURCE_POLICIES)
    summary = summarize_concentration(target_daily, realized_daily)

    overlap_summary = (
        overlap_daily.groupby(["left_policy", "right_policy"])
        .agg(
            dates=("trade_date", "nunique"),
            intersection_mean=("intersection_count", "mean"),
            intersection_median=("intersection_count", "median"),
            jaccard_mean=("jaccard", "mean"),
            jaccard_median=("jaccard", "median"),
            jaccard_max=("jaccard", "max"),
            left_overlap_mean=("overlap_left_fraction", "mean"),
            right_overlap_mean=("overlap_right_fraction", "mean"),
        ).reset_index().sort_values("jaccard_mean", ascending=False).reset_index(drop=True)
    )

    for frame, path in (
        (target_daily, OUT_TARGET_DAILY),
        (realized_daily, OUT_REALIZED_DAILY),
        (overlap_daily, OUT_OVERLAP_DAILY),
        (summary, OUT_SUMMARY),
        (overlap_summary, OUT_OVERLAP_SUMMARY),
    ):
        _write(frame, path)

    focus = summary.loc[
        summary["allocation_id"].isin(FOCUS_ALLOCATIONS)
        & (summary["starting_capital"].astype(float) == CAPITAL_FOR_FOCUS)
    ].copy()
    focus_cols = [
        "allocation_id",
        "target_names_median",
        "target_max_name_mean",
        "target_max_name_worst",
        "target_top3_mean",
        "target_effective_names_mean",
        "target_max_sector_mean",
        "target_max_sector_worst",
        "realized_max_name_mean",
        "realized_max_name_worst",
        "realized_top3_mean",
        "realized_effective_names_mean",
        "realized_effective_names_min",
        "realized_max_sector_mean",
        "realized_max_sector_worst",
        "realized_effective_sectors_mean",
    ]
    focus = focus[focus_cols].sort_values("allocation_id")

    report = f"""# C11 CP5 — Concentration and Overlap

## Scope

CP5 is diagnostic only. It does not train models, alter selections or optimize
allocation weights.

It measures target concentration on weekly signal dates, realized daily close
concentration after execution, name/sector HHI and effective counts, and
pairwise source-policy selection overlap.

Realized name/sector concentration is normalized over invested capital, so
residual cash cannot make a concentrated invested portfolio look safer.

## Focus allocations at PKR 1,000,000

{focus.to_markdown(index=False)}

## Source-policy overlap

{overlap_summary.to_markdown(index=False)}

## Interpretation

High historical return does not excuse poor diversification. Compare worst
single-name weight, top-3 concentration, effective names, sector concentration
and source-policy overlap before choosing the final deployment allocation.

P1 remains diagnostic because CP4A materially transformed it under refill.
The primary comparison remains P4, P5, P4/P5 and the two P2/P4/P5 equal-third
candidates.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")

    manifest = {
        "contract": "C11",
        "checkpoint": "CP5",
        "status": "COMPLETE",
        "holdout_accessed": False,
        "method": "diagnostic_concentration_and_overlap_no_weight_optimization",
        "inputs": {
            str(DEPLOYMENT): _sha256(DEPLOYMENT),
            str(TARGETS): _sha256(TARGETS),
            str(POSITIONS): _sha256(POSITIONS),
            str(CP4A_MANIFEST): _sha256(CP4A_MANIFEST),
            str(CP4B_MANIFEST): _sha256(CP4B_MANIFEST),
        },
        "outputs": {
            str(OUT_TARGET_DAILY): {"rows": len(target_daily), "sha256": _sha256(OUT_TARGET_DAILY)},
            str(OUT_REALIZED_DAILY): {"rows": len(realized_daily), "sha256": _sha256(OUT_REALIZED_DAILY)},
            str(OUT_OVERLAP_DAILY): {"rows": len(overlap_daily), "sha256": _sha256(OUT_OVERLAP_DAILY)},
            str(OUT_SUMMARY): {"rows": len(summary), "sha256": _sha256(OUT_SUMMARY)},
            str(OUT_OVERLAP_SUMMARY): {"rows": len(overlap_summary), "sha256": _sha256(OUT_OVERLAP_SUMMARY)},
        },
        "focus_allocations": FOCUS_ALLOCATIONS,
        "focus_capital": CAPITAL_FOR_FOCUS,
        "focus_results": focus.to_dict(orient="records"),
        "overlap_summary": overlap_summary.to_dict(orient="records"),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")

    print("=== C11 CP5: CONCENTRATION / OVERLAP ===")
    print("\n=== FOCUS ALLOCATIONS @ PKR 1,000,000 ===")
    print(focus.to_string(index=False))
    print("\n=== HIGHEST SOURCE-POLICY OVERLAPS ===")
    print(overlap_summary.head(15).to_string(index=False))
    print()
    print(f"Target daily:    {len(target_daily):,} -> {OUT_TARGET_DAILY}")
    print(f"Realized daily:  {len(realized_daily):,} -> {OUT_REALIZED_DAILY}")
    print(f"Overlap daily:   {len(overlap_daily):,} -> {OUT_OVERLAP_DAILY}")
    print(f"Summary:         {len(summary):,} -> {OUT_SUMMARY}")
    print(f"Overlap summary: {len(overlap_summary):,} -> {OUT_OVERLAP_SUMMARY}")
    print(f"Report:          {REPORT}")
    print(f"Manifest:        {MANIFEST}")

if __name__ == "__main__":
    main()
