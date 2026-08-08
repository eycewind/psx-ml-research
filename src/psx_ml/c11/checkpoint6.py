from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c11.deployment_decision import (
    PRIMARY_CANDIDATE,
    SECONDARY_CANDIDATE,
    REFERENCE,
    build_finalist_scorecard,
    select_primary_deployment,
)


CP4B_SUMMARY = Path("data/processed/c11/cp4b_allocation_summary.parquet")
CP4B_NAV = Path("data/processed/c11/cp4b_execution_nav.parquet")
CP4B_TRADES = Path("data/processed/c11/cp4b_execution_trades.parquet")
CP5_SUMMARY = Path("data/processed/c11/cp5_concentration_summary.parquet")

CP4B_MANIFEST = Path("artifacts/reports/C11_CP4B_CAPITAL_ALLOCATION_MANIFEST.json")
CP5_MANIFEST = Path("artifacts/reports/C11_CP5_CONCENTRATION_OVERLAP_MANIFEST.json")

OUT_SCORECARD = Path("data/processed/c11/cp6_finalist_scorecard.parquet")
OUT_NAV = Path("data/processed/c11/cp6_finalist_nav.parquet")
OUT_TRADES = Path("data/processed/c11/cp6_finalist_trades.parquet")
REPORT = Path("artifacts/reports/C11_CP6_FINAL_DEPLOYMENT_BACKTEST_REPORT.md")
MANIFEST = Path("artifacts/reports/C11_CP6_FINAL_DEPLOYMENT_BACKTEST_MANIFEST.json")

FINALISTS = [PRIMARY_CANDIDATE, SECONDARY_CANDIDATE, REFERENCE]
CAPITALS = [50_000.0, 100_000.0, 250_000.0, 500_000.0, 1_000_000.0]


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


def _capital_stability(scorecard: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for allocation_id, g in scorecard.groupby("allocation_id"):
        g = g.sort_values("starting_capital")
        rows.append(
            {
                "allocation_id": allocation_id,
                "capital_levels": int(g["starting_capital"].nunique()),
                "annualized_return_min": float(g["annualized_return"].min()),
                "annualized_return_max": float(g["annualized_return"].max()),
                "sharpe_min": float(g["sharpe_zero_rf"].min()),
                "sharpe_max": float(g["sharpe_zero_rf"].max()),
                "max_drawdown_worst": float(g["max_drawdown"].min()),
                "buy_fill_fraction_min": float(g["buy_fill_fraction"].min()),
                "mean_cash_fraction_max": float(g["mean_cash_fraction"].max()),
                "ending_nav_1m": float(
                    g.loc[
                        g["starting_capital"].astype(float) == 1_000_000.0,
                        "ending_nav",
                    ].iloc[0]
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("allocation_id").reset_index(drop=True)


def main() -> None:
    allocation = pd.read_parquet(CP4B_SUMMARY)
    nav = pd.read_parquet(CP4B_NAV)
    trades = pd.read_parquet(CP4B_TRADES)
    concentration = pd.read_parquet(CP5_SUMMARY)

    # CP6 must be a pure frozen-artifact extraction/decision checkpoint.
    expected_allocs = set(FINALISTS)
    scorecard = build_finalist_scorecard(allocation, concentration)
    if set(scorecard["allocation_id"].astype(str)) != expected_allocs:
        raise ValueError("Unexpected CP6 finalist set")
    if set(scorecard["starting_capital"].astype(float)) != set(CAPITALS):
        raise ValueError("Unexpected CP6 capital grid")
    if len(scorecard) != len(FINALISTS) * len(CAPITALS):
        raise ValueError("Unexpected CP6 scorecard row count")

    nav = nav.loc[nav["allocation_id"].isin(FINALISTS)].copy()
    trades = trades.loc[trades["allocation_id"].isin(FINALISTS)].copy()
    nav["trade_date"] = pd.to_datetime(nav["trade_date"]).dt.normalize()
    trades["trade_date"] = pd.to_datetime(trades["trade_date"]).dt.normalize()

    if (nav["trade_date"] >= pd.Timestamp("2026-01-01")).any():
        raise ValueError("2026 NAV row in CP6")
    if (trades["trade_date"] >= pd.Timestamp("2026-01-01")).any():
        raise ValueError("2026 trade row in CP6")
    if (nav["cash"] < -1e-7).any():
        raise ValueError("Negative cash in frozen CP6 NAV")

    one_m = scorecard.loc[
        scorecard["starting_capital"].astype(float) == 1_000_000.0
    ].copy()
    primary = select_primary_deployment(one_m)
    if primary != PRIMARY_CANDIDATE:
        raise RuntimeError("Unexpected CP6 primary deployment selection")

    stability = _capital_stability(scorecard)

    # Final backtest artifact is not recomputed. It is an exact extraction of
    # the already-validated CP4B execution ledger for the frozen finalists.
    _write(scorecard, OUT_SCORECARD)
    _write(nav, OUT_NAV)
    _write(trades, OUT_TRADES)

    cols = [
        "allocation_id",
        "ending_nav",
        "annualized_return",
        "sharpe_zero_rf",
        "max_drawdown",
        "buy_fill_fraction",
        "mean_cash_fraction",
        "total_transaction_cost",
        "realized_max_name_worst",
        "realized_max_sector_worst",
        "realized_effective_names_mean",
    ]
    one_m_table = one_m[cols].sort_values("allocation_id")

    report = f"""# C11 CP6 — Final Deployment Backtest

## Decision

**Primary deployment allocation: `{PRIMARY_CANDIDATE}`**

Composition:

- 25% sleeve allocation to `D_P4_kmi30_strict`
- 75% sleeve allocation to `D_P5_shariah_screened`
- each sleeve equal-weight internally on each signal date;
- overlapping symbols merged into one target position/order.

**Secondary diagnostic candidate: `{SECONDARY_CANDIDATE}`**

`{REFERENCE}` remains the standalone Shariah-screened benchmark.

## Why A07 is frozen as primary

This is not a return-maximizing grid search. CP4B defined the candidate weights
before evaluation and CP5 assessed concentration separately.

Compared with A17, A07:

- uses only the two native Shariah deployment policies P4 and P5;
- avoids dependency on the materially transformed P2-refill sleeve;
- has substantially lower worst realized single-name concentration;
- has substantially lower worst realized sector concentration;
- retains strong execution characteristics;
- produced higher historical annualized return in the accepted pre-holdout test.

A17 remains useful as a risk-balanced diagnostic because its historical Sharpe
and maximum drawdown were somewhat better.

## PKR 1,000,000 finalist comparison

{one_m_table.to_markdown(index=False)}

## Stability across capital levels

{stability.to_markdown(index=False)}

## Frozen execution semantics

No execution rule is changed in CP6. The final backtest is an exact extraction
from the accepted CP4B merged-portfolio execution ledger:

- BUY limit = signal-session close +2%;
- next session only;
- fill at open if open <= limit;
- otherwise intraday-touch proxy at limit if low <= limit;
- otherwise miss/no chase;
- whole shares;
- exact broker costs;
- no leverage;
- next-open reductions/exits with deferred exits when required.

## Shariah semantics

A07 inherits the accepted CP4A policy rules:

- P4: official PIT KMI30 membership is authoritative Shariah provenance;
- P5: PIT screened-universe eligibility is mandatory;
- no unknown/non-eligible row is executable.

## Holdout

No 2026 data is accessed. CP6 does not retrain, re-rank, change selections,
search weights, or introduce new indicators.

## Next checkpoint

CP7 converts the frozen A07 policy into a production signal/order artifact for
the next live session, including capital-aware whole-share orders, limits,
Shariah provenance and explicit skip/miss reasons.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")

    manifest = {
        "contract": "C11",
        "checkpoint": "CP6",
        "status": "COMPLETE",
        "holdout_accessed": False,
        "primary_deployment_allocation": PRIMARY_CANDIDATE,
        "secondary_diagnostic_allocation": SECONDARY_CANDIDATE,
        "reference_allocation": REFERENCE,
        "selection_method": (
            "predefined_finalists_multicriteria_policy_freeze_"
            "not_return_or_sharpe_argmax"
        ),
        "execution_rule": "C11_CP3_primary_touch_2pct",
        "inputs": {
            str(CP4B_SUMMARY): _sha256(CP4B_SUMMARY),
            str(CP4B_NAV): _sha256(CP4B_NAV),
            str(CP4B_TRADES): _sha256(CP4B_TRADES),
            str(CP5_SUMMARY): _sha256(CP5_SUMMARY),
            str(CP4B_MANIFEST): _sha256(CP4B_MANIFEST),
            str(CP5_MANIFEST): _sha256(CP5_MANIFEST),
        },
        "outputs": {
            str(OUT_SCORECARD): {
                "rows": len(scorecard),
                "sha256": _sha256(OUT_SCORECARD),
            },
            str(OUT_NAV): {
                "rows": len(nav),
                "sha256": _sha256(OUT_NAV),
            },
            str(OUT_TRADES): {
                "rows": len(trades),
                "sha256": _sha256(OUT_TRADES),
            },
        },
        "capital_grid": CAPITALS,
        "pk1m_scorecard": one_m_table.to_dict(orient="records"),
        "capital_stability": stability.to_dict(orient="records"),
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print("=== C11 CP6: FINAL DEPLOYMENT BACKTEST ===")
    print(f"PRIMARY:   {PRIMARY_CANDIDATE}")
    print(f"SECONDARY: {SECONDARY_CANDIDATE}")
    print(f"REFERENCE: {REFERENCE}")
    print()
    print("=== PKR 1,000,000 ===")
    print(one_m_table.to_string(index=False))
    print()
    print("=== CAPITAL STABILITY ===")
    print(stability.to_string(index=False))
    print()
    print(f"Scorecard: {len(scorecard):,} -> {OUT_SCORECARD}")
    print(f"NAV:       {len(nav):,} -> {OUT_NAV}")
    print(f"Trades:    {len(trades):,} -> {OUT_TRADES}")
    print(f"Report:    {REPORT}")
    print(f"Manifest:  {MANIFEST}")


if __name__ == "__main__":
    main()
