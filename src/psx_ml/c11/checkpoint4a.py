from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c11.deployment_selection import (
    D_P1_FILTER,
    D_P1_REFILL,
    D_P2_FILTER,
    D_P2_REFILL,
    D_P4,
    D_P5,
    P1,
    P2,
    assert_exact_reconstruction,
    build_c9_ranked_universes,
    build_defensive_passthrough,
    build_filter_only,
    build_p1_refill,
    build_p2_refill,
    build_p4_authoritative_passthrough,
    reconstruct_p1_p2,
    sha256_file,
)
from psx_ml.c11.shariah_gate import normalize_screening_history


C9_CONFIG = Path("config/c9.example.toml")
C9_SELECTIONS = Path("data/processed/c9/candidate_selections.parquet")
P4_SELECTIONS = Path("data/processed/c10/p4_kmi30_selections.parquet")
P5_SELECTIONS = Path("data/processed/c10/p5_shariah_screened_selections.parquet")
SHARIAH_HISTORY = Path(
    "data/reference/kmi_all_share_screened_universe_history.csv"
)

OUT_SELECTIONS = Path("data/processed/c11/deployment_selections.parquet")
OUT_AUDIT = Path("data/processed/c11/deployment_shariah_gate_audit.parquet")
REPORT = Path("artifacts/reports/C11_CP4A_SHARIAH_SELECTION_REPORT.md")
MANIFEST = Path("artifacts/reports/C11_CP4A_SHARIAH_SELECTION_MANIFEST.json")

EXPECTED_HASHES = {
    C9_SELECTIONS: "3ff902152a75d168218850535d4c40da4dd949b54e22ccdfc6560d39646dc520",
    P4_SELECTIONS: "75ef50328110d573649906d47ee08733b60977953bb7c67c37d869eae05fd03c",
    P5_SELECTIONS: "0166c4a67c6d12241ddef1b7f7fc4002d6fa8071d01cbd6499b32dd22811c57c",
    SHARIAH_HISTORY: "525bb1e26e4b9ec71b838122b27e63ce1c95755f4b244991973f6d2da949f70a",
}


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    with path.open("wb") as f:
        pq.write_table(table, f)


def _check_frozen_hashes() -> dict[str, str]:
    hashes = {}
    for path, expected in EXPECTED_HASHES.items():
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(
                f"Frozen input changed: {path}: expected {expected}, got {actual}"
            )
        hashes[str(path)] = actual
    return hashes


def _policy_summary(
    selections: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for policy_id, group in selections.groupby("policy_id", sort=True):
        dates = group.groupby("trade_date").size()
        a = audit.loc[
            audit["deployment_policy_id"].astype(str) == str(policy_id)
        ]
        rejected = int((~a["shariah_eligible"].astype(bool)).sum()) if len(a) else 0
        unknown = int(
            (a["gate_status"].astype(str) == "rejected_unknown").sum()
        ) if len(a) else 0
        low = int(group["low_confidence_flag"].astype(bool).sum())
        refills = (
            int(group["refill_candidate"].astype(bool).sum())
            if "refill_candidate" in group.columns
            else 0
        )
        shortfall_dates = 0
        if "deployment_shortfall" in group.columns:
            shortfall_dates = int(
                group.groupby("trade_date")["deployment_shortfall"]
                .max()
                .gt(0)
                .sum()
            )

        rows.append(
            {
                "policy_id": policy_id,
                "rows": len(group),
                "dates": group["trade_date"].nunique(),
                "symbols": group["symbol"].nunique(),
                "holdings_min": int(dates.min()),
                "holdings_median": float(dates.median()),
                "holdings_max": int(dates.max()),
                "gate_rejections_in_audit": rejected,
                "unknown_rejections_in_audit": unknown,
                "low_confidence_selected_rows": low,
                "refill_selected_rows": refills,
                "shortfall_dates": shortfall_dates,
            }
        )
    return pd.DataFrame(rows)


def _assert_deployment_integrity(selections: pd.DataFrame) -> None:
    if selections.empty:
        raise RuntimeError("CP4A produced no deployment selections")

    selections["trade_date"] = pd.to_datetime(
        selections["trade_date"]
    ).dt.normalize()

    if (selections["trade_date"] >= pd.Timestamp("2026-01-01")).any():
        raise RuntimeError("2026 holdout rows found in CP4A selections")
    if not selections["shariah_eligible"].astype(bool).all():
        raise RuntimeError("Ineligible row escaped into deployment selections")
    if selections.duplicated(
        ["policy_id", "trade_date", "symbol"]
    ).any():
        raise RuntimeError("Duplicate deployment policy/date/symbol rows")

    for policy_id, group in selections.groupby("policy_id"):
        breaches = (
            group.groupby(["trade_date", "sector"], dropna=False)
            .size()
            .gt(2)
        )
        if policy_id in {
            D_P1_FILTER,
            D_P1_REFILL,
            D_P2_FILTER,
            D_P2_REFILL,
        } and breaches.any():
            raise RuntimeError(f"Sector-cap breach in {policy_id}")


def main() -> None:
    hashes_before = _check_frozen_hashes()

    accepted = pd.read_parquet(C9_SELECTIONS)
    p4 = pd.read_parquet(P4_SELECTIONS)
    p5 = pd.read_parquet(P5_SELECTIONS)
    history = normalize_screening_history(pd.read_csv(SHARIAH_HISTORY))

    lgb, xgb, c9_manifest = build_c9_ranked_universes(
        repo=Path.cwd(),
        config_path=C9_CONFIG,
    )
    reconstructed_p1, reconstructed_p2, consensus = reconstruct_p1_p2(lgb, xgb)
    assert_exact_reconstruction(
        reconstructed_p1,
        accepted,
        policy_id=P1,
    )
    assert_exact_reconstruction(
        reconstructed_p2,
        accepted,
        policy_id=P2,
    )

    accepted_p1 = accepted.loc[
        accepted["policy_id"].astype(str) == P1
    ].copy()
    accepted_p2 = accepted.loc[
        accepted["policy_id"].astype(str) == P2
    ].copy()

    p1_filter, p1_filter_audit = build_filter_only(
        accepted,
        history,
        upstream_policy_id=P1,
        deployment_policy_id=D_P1_FILTER,
    )
    p2_filter, p2_filter_audit = build_filter_only(
        accepted,
        history,
        upstream_policy_id=P2,
        deployment_policy_id=D_P2_FILTER,
    )
    p1_refill, p1_refill_audit = build_p1_refill(
        lgb=lgb,
        accepted_p1=accepted_p1,
        history=history,
    )
    p2_refill, p2_refill_audit = build_p2_refill(
        consensus=consensus,
        accepted_p2=accepted_p2,
        history=history,
    )
    p4_deploy, p4_audit = build_p4_authoritative_passthrough(
        p4,
        history,
        upstream_policy_id="P4_kmi30_strict",
        deployment_policy_id=D_P4,
    )
    p5_deploy, p5_audit = build_defensive_passthrough(
        p5,
        history,
        upstream_policy_id="P5_shariah_screened",
        deployment_policy_id=D_P5,
    )

    selections = pd.concat(
        [
            p1_filter,
            p1_refill,
            p2_filter,
            p2_refill,
            p4_deploy,
            p5_deploy,
        ],
        ignore_index=True,
        sort=False,
    )
    audits = pd.concat(
        [
            p1_filter_audit,
            p1_refill_audit,
            p2_filter_audit,
            p2_refill_audit,
            p4_audit,
            p5_audit,
        ],
        ignore_index=True,
        sort=False,
    )

    # C9 stores selection_date as strings while P4/P5 use timestamps.
    # Normalize the mixed upstream representation before Parquet serialization.
    for frame in (selections, audits):
        if "selection_date" in frame.columns:
            frame["selection_date"] = pd.to_datetime(
                frame["selection_date"],
                errors="coerce",
            ).dt.normalize()

    _assert_deployment_integrity(selections)
    hashes_after = _check_frozen_hashes()
    if hashes_before != hashes_after:
        raise RuntimeError("Frozen upstream artifact changed during CP4A")

    summary = _policy_summary(selections, audits)

    _write_parquet(selections, OUT_SELECTIONS)
    _write_parquet(audits, OUT_AUDIT)

    p1_original_counts = (
        accepted_p1.assign(
            trade_date=pd.to_datetime(accepted_p1["trade_date"]).dt.normalize()
        )
        .groupby("trade_date")
        .size()
    )
    p2_original_counts = (
        accepted_p2.assign(
            trade_date=pd.to_datetime(accepted_p2["trade_date"]).dt.normalize()
        )
        .groupby("trade_date")
        .size()
    )

    def shortfall(policy: str, original_counts: pd.Series) -> dict:
        counts = (
            selections.loc[selections["policy_id"] == policy]
            .groupby("trade_date")
            .size()
            .reindex(original_counts.index, fill_value=0)
        )
        delta = original_counts - counts
        return {
            "dates": int((delta > 0).sum()),
            "total_missing_holdings": int(delta.clip(lower=0).sum()),
            "maximum_shortfall": int(delta.max()),
        }

    shortfalls = {
        D_P1_FILTER: shortfall(D_P1_FILTER, p1_original_counts),
        D_P1_REFILL: shortfall(D_P1_REFILL, p1_original_counts),
        D_P2_FILTER: shortfall(D_P2_FILTER, p2_original_counts),
        D_P2_REFILL: shortfall(D_P2_REFILL, p2_original_counts),
    }

    report = f"""# C11 CP4A — PIT Shariah-Gated Deployment Selections

## Status

Selection transformation complete. This stage does **not** choose policy weights or a final deployment combination.

## Frozen rule

- Every executable candidate must pass the accepted point-in-time Shariah gate.
- Unknown/unavailable eligibility is rejected.
- Low-confidence eligible rows remain allowed and are flagged.
- P1/P2 accepted C9 outputs remain immutable.
- `filter_only` removes rejected names without replacement.
- `filter_and_refill` scans the original accepted ranking and preserves the upstream selected holding count where possible.
- P1 refill may continue below the original top-10% cut because CP1 explicitly defines refill as a deployment transformation that continues down the accepted ranking.
- P2 refill does **not** broaden the accepted consensus definition. It scans only the original P2 top-10% LightGBM/XGBoost consensus intersection, in the same LightGBM percentile-rank order used by the accepted S1 sector constraint. Therefore P2 refill may retain a shortfall when the accepted consensus pool contains too few PIT-Shariah-eligible names.
- P4 uses its official PIT KMI30 membership as authoritative Shariah provenance; the generic screened history is secondary diagnostic coverage and cannot veto a valid KMI30 row.
- P5 is defensively re-gated against the accepted screened-universe history.

## Exact C9 reconstruction

- P1 reconstructed before gating: **PASS**
- P2 reconstructed before gating: **PASS**
- C9 accepted selection artifact unchanged: **PASS**
- 2026 holdout accessed: **false**

## Deployment selection summary

{summary.to_markdown(index=False)}

## Holding shortfalls versus accepted upstream P1/P2

```json
{json.dumps(shortfalls, indent=2)}
```

## Interpretation boundary

CP4A establishes auditable Shariah-compliant deployment candidate sets only.
It does not select between filter-only and refill based on historical returns.
That decision belongs to the CP4 capital-allocation/execution comparison.

## Outputs

- `{OUT_SELECTIONS}`
- `{OUT_AUDIT}`
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")

    manifest = {
        "contract": "C11",
        "checkpoint": "CP4A",
        "status": "COMPLETE",
        "holdout_accessed": False,
        "git_parent_checkpoint": "C11 CP3",
        "c9_reconstruction": {
            "p1_exact": True,
            "p2_exact": True,
            "c9_generation_commit": c9_manifest.get("code", {}).get("commit"),
        },
        "rules": {
            D_P1_FILTER: "accepted P1 selected rows -> PIT Shariah filter only",
            D_P1_REFILL: (
                "scan full accepted LightGBM ranking on accepted P1 dates; "
                "PIT Shariah gate; S1 cap2; refill to accepted P1 holding count where possible"
            ),
            D_P2_FILTER: "accepted P2 selected rows -> PIT Shariah filter only",
            D_P2_REFILL: (
                "accepted P2 top10 LightGBM/XGBoost consensus intersection only; "
                "PIT Shariah gate; LightGBM percentile order; S1 cap2; "
                "refill to accepted P2 holding count where possible"
            ),
            D_P4: "accepted P4 rows -> authoritative PIT KMI30 Shariah provenance; generic screening history secondary diagnostic only",
            D_P5: "accepted P5 rows -> defensive PIT Shariah gate",
        },
        "input_hashes": hashes_before,
        "outputs": {
            str(OUT_SELECTIONS): {
                "rows": int(len(selections)),
                "sha256": sha256_file(OUT_SELECTIONS),
            },
            str(OUT_AUDIT): {
                "rows": int(len(audits)),
                "sha256": sha256_file(OUT_AUDIT),
            },
        },
        "summary": summary.to_dict(orient="records"),
        "shortfalls": shortfalls,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print("=== C11 CP4A: SHARIAH-GATED DEPLOYMENT SELECTIONS ===")
    print("C9 P1 exact reconstruction: PASS")
    print("C9 P2 exact reconstruction: PASS")
    print()
    print(summary.to_string(index=False))
    print()
    print("=== SHORTFALLS VS UPSTREAM HOLDING COUNTS ===")
    for policy, value in shortfalls.items():
        print(
            f"{policy}: dates={value['dates']}, "
            f"total_missing={value['total_missing_holdings']}, "
            f"max_shortfall={value['maximum_shortfall']}"
        )
    print()
    print(f"Selections: {len(selections):,} -> {OUT_SELECTIONS}")
    print(f"Gate audit: {len(audits):,} -> {OUT_AUDIT}")
    print(f"Report: {REPORT}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
