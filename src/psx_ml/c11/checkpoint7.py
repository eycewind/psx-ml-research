from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c11.live_orders import (
    PRIMARY_ALLOCATION_ID,
    build_signal_plan,
)


DEPLOYMENT = Path("data/processed/c11/deployment_selections.parquet")
CP6_MANIFEST = Path("artifacts/reports/C11_CP6_FINAL_DEPLOYMENT_BACKTEST_MANIFEST.json")
DAILY_OHLCV = Path("data/cache/daily_ohlcv.parquet")

OUT_PLAN = Path("data/processed/c11/cp7_historical_signal_plan.parquet")
OUT_JSON = Path("artifacts/reports/C11_CP7_HISTORICAL_SIGNAL_PLAN.json")
REPORT = Path("artifacts/reports/C11_CP7_PRODUCTION_ORDER_ARTIFACT_REPORT.md")
MANIFEST = Path("artifacts/reports/C11_CP7_PRODUCTION_ORDER_ARTIFACT_MANIFEST.json")

# Last accepted pre-holdout signal date. CP7 acceptance remains historical;
# it must not silently consume a live/2026 date.
FIXTURE_SIGNAL_DATE = pd.Timestamp("2025-12-22")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), f)


def _read_daily_ohlcv() -> pd.DataFrame:
    # Avoid PyArrow dataset filesystem registration paths in this environment.
    with DAILY_OHLCV.open("rb") as f:
        table = pq.ParquetFile(f).read(
            columns=["trade_date", "symbol", "close_adj"]
        )
    return table.to_pandas()


def main() -> None:
    deployment = pd.read_parquet(DEPLOYMENT)
    deployment["trade_date"] = pd.to_datetime(
        deployment["trade_date"]
    ).dt.normalize()

    if (deployment["trade_date"] >= pd.Timestamp("2026-01-01")).any():
        raise ValueError("2026 row in CP7 acceptance input")

    available_dates = sorted(
        deployment.loc[
            deployment["policy_id"].isin(
                ["D_P4_kmi30_strict", "D_P5_shariah_screened"]
            ),
            "trade_date",
        ].unique()
    )
    fixture_date = FIXTURE_SIGNAL_DATE
    if fixture_date not in set(map(pd.Timestamp, available_dates)):
        # Deterministic historical fallback to latest common pre-holdout date.
        p4_dates = set(
            deployment.loc[
                deployment["policy_id"] == "D_P4_kmi30_strict",
                "trade_date",
            ]
        )
        p5_dates = set(
            deployment.loc[
                deployment["policy_id"] == "D_P5_shariah_screened",
                "trade_date",
            ]
        )
        common = sorted(p4_dates & p5_dates)
        if not common:
            raise ValueError("No common P4/P5 historical signal date")
        fixture_date = pd.Timestamp(common[-1])

    if fixture_date >= pd.Timestamp("2026-01-01"):
        raise ValueError("CP7 acceptance fixture crossed into holdout")

    closes = _read_daily_ohlcv()
    plan = build_signal_plan(
        selections=deployment,
        signal_date=fixture_date,
        signal_closes=closes,
    )

    if plan.empty:
        raise ValueError("CP7 historical signal plan is empty")
    if set(plan["allocation_id"].astype(str)) != {PRIMARY_ALLOCATION_ID}:
        raise ValueError("CP7 generated unexpected allocation")
    if not plan["shariah_eligible"].astype(bool).all():
        raise ValueError("CP7 generated non-Shariah plan")
    if plan["symbol"].duplicated().any():
        raise ValueError("CP7 generated duplicate symbol")
    if abs(float(plan["target_weight"].sum()) - 1.0) > 1e-10:
        raise ValueError("CP7 target weights do not sum to one")

    _write(plan, OUT_PLAN)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "artifact_type": "historical_signal_plan_fixture",
                "allocation_id": PRIMARY_ALLOCATION_ID,
                "signal_date": fixture_date.date().isoformat(),
                "execution_rule": "NEXT_SESSION_ONLY_TOUCH_2PCT_NO_CHASE",
                "rows": plan.to_dict(orient="records"),
            },
            indent=2,
            default=str,
        ) + "\n",
        encoding="utf-8",
    )

    report = f"""# C11 CP7 — Production Signal / Order Artifact

## Frozen production policy

`{PRIMARY_ALLOCATION_ID}`

- 25% `D_P4_kmi30_strict`
- 75% `D_P5_shariah_screened`
- equal weight inside each sleeve
- overlapping names merged
- hard Shariah provenance
- BUY limit = signal close +2%
- next session only
- no chase
- whole shares and exact broker fees at execution

## Two-phase live workflow

CP7 deliberately separates **signal planning** from **session-open sizing**.

### Phase A — after signal-session close

`build_signal_plan(...)` produces:

- merged A07 target weights;
- P4/P5 contribution flags;
- Shariah provenance/confidence;
- signal close;
- +2% BUY limit;
- explicit `DEFER_TO_SESSION_OPEN` sizing status.

Exact target shares are **not** fabricated after the close because the accepted
CP3/CP4B sizing rule uses the next session's actual opening prices.

### Phase B — next session open

`build_session_open_orders(...)` receives:

- the frozen signal plan;
- actual session opens;
- current positions;
- available cash.

It then produces exact whole-share BUY/SELL/HOLD actions. SELL reductions are
resolved first. BUYs whose open is within the +2% limit are ready at the open;
BUYs opening above the limit become DAY limit orders waiting for the accepted
intraday-touch condition.

The live engine never needs to retrain or alter the accepted policy.

## Acceptance fixture

CP7 acceptance uses only historical pre-holdout data.

Fixture signal date: `{fixture_date.date().isoformat()}`

Rows: {len(plan)}

Target weight sum: {plan["target_weight"].sum():.12f}

No 2026/live data is consumed by this checkpoint.

## Production output schema

Signal-plan fields include:

- `allocation_id`
- `trade_date`
- `symbol`
- `p4_selected`
- `p5_selected`
- `target_weight`
- `contributing_policies`
- `shariah_eligible`
- `shariah_sources`
- `shariah_confidences`
- `signal_close`
- `buy_limit_price`
- `execution_rule`
- `sizing_status`
- `status`
- `reason`

Session-open order fields include:

- `signal_date`
- `execution_date`
- `symbol`
- `target_weight`
- `current_shares`
- `target_shares`
- `order_side`
- `order_shares`
- `order_type`
- `reference_open`
- `buy_limit_price`
- estimated broker fee components
- `status`
- `reason`

## Boundary

This checkpoint constructs orders from supplied current selections/prices.
It does **not** define how the production system obtains a new 2026 P4/P5
selection. That live ranking/screening integration must feed the same frozen
input schema and is operational wiring rather than a new trading methodology.
"""
    REPORT.write_text(report, encoding="utf-8")

    manifest = {
        "contract": "C11",
        "checkpoint": "CP7",
        "status": "COMPLETE",
        "holdout_accessed": False,
        "primary_allocation": PRIMARY_ALLOCATION_ID,
        "historical_fixture_signal_date": fixture_date.date().isoformat(),
        "production_architecture": "two_phase_signal_plan_then_session_open_orders",
        "execution_rule": "C11_CP3_primary_touch_2pct",
        "inputs": {
            str(DEPLOYMENT): _sha256(DEPLOYMENT),
            str(CP6_MANIFEST): _sha256(CP6_MANIFEST),
            str(DAILY_OHLCV): _sha256(DAILY_OHLCV),
        },
        "outputs": {
            str(OUT_PLAN): {
                "rows": len(plan),
                "sha256": _sha256(OUT_PLAN),
            },
            str(OUT_JSON): {
                "sha256": _sha256(OUT_JSON),
            },
        },
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== C11 CP7: PRODUCTION SIGNAL / ORDER ARTIFACT ===")
    print(f"Primary allocation: {PRIMARY_ALLOCATION_ID}")
    print(f"Historical fixture: {fixture_date.date().isoformat()}")
    print(f"Rows: {len(plan)}")
    print(f"Weight sum: {plan['target_weight'].sum():.12f}")
    print()
    print(plan[
        [
            "symbol", "p4_selected", "p5_selected", "target_weight",
            "signal_close", "buy_limit_price", "shariah_confidences",
        ]
    ].to_string(index=False))
    print()
    print(f"Plan:     {OUT_PLAN}")
    print(f"JSON:     {OUT_JSON}")
    print(f"Report:   {REPORT}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
