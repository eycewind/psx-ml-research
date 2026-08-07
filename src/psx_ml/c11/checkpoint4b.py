from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.inputs import LAST_PRE_HOLDOUT_DATE, assert_no_holdout, load_execution_prices
from psx_ml.c11.capital_allocation import AllocationDefinition, build_allocation_targets
from psx_ml.c11.checkpoint2 import CAPITAL_GRID
from psx_ml.c11.execution_portfolio import ExecutionConfig, summarize_execution_nav
from psx_ml.c11.weighted_execution import build_weighted_execution_portfolio


DEPLOYMENT_SELECTIONS = Path("data/processed/c11/deployment_selections.parquet")
CP4A_MANIFEST = Path("artifacts/reports/C11_CP4A_SHARIAH_SELECTION_MANIFEST.json")
CP3_MANIFEST = Path("artifacts/reports/C11_CP3_EXECUTION_MODEL_MANIFEST.json")
DAILY_OHLCV = Path("data/cache/daily_ohlcv.parquet")

OUT_TARGETS = Path("data/processed/c11/cp4b_allocation_targets.parquet")
OUT_TRADES = Path("data/processed/c11/cp4b_execution_trades.parquet")
OUT_POSITIONS = Path("data/processed/c11/cp4b_execution_positions.parquet")
OUT_NAV = Path("data/processed/c11/cp4b_execution_nav.parquet")
OUT_SUMMARY = Path("data/processed/c11/cp4b_allocation_summary.parquet")
REPORT = Path("artifacts/reports/C11_CP4B_CAPITAL_ALLOCATION_REPORT.md")
MANIFEST = Path("artifacts/reports/C11_CP4B_CAPITAL_ALLOCATION_MANIFEST.json")

P1F = "D_P1_shariah_filter"
P1R = "D_P1_shariah_refill"
P2F = "D_P2_shariah_filter"
P2R = "D_P2_shariah_refill"
P4 = "D_P4_kmi30_strict"
P5 = "D_P5_shariah_screened"


ALLOCATIONS = (
    AllocationDefinition("A01_P1_filter", ((P1F, 1.0),), "standalone_diagnostic"),
    AllocationDefinition("A02_P1_refill", ((P1R, 1.0),), "standalone_diagnostic"),
    AllocationDefinition("A03_P2_filter", ((P2F, 1.0),), "standalone"),
    AllocationDefinition("A04_P2_refill", ((P2R, 1.0),), "standalone"),
    AllocationDefinition("A05_P4", ((P4, 1.0),), "standalone"),
    AllocationDefinition("A06_P5", ((P5, 1.0),), "standalone"),

    AllocationDefinition("A07_P4_25_P5_75", ((P4, 0.25), (P5, 0.75)), "two_policy"),
    AllocationDefinition("A08_P4_50_P5_50", ((P4, 0.50), (P5, 0.50)), "two_policy"),
    AllocationDefinition("A09_P4_75_P5_25", ((P4, 0.75), (P5, 0.25)), "two_policy"),

    AllocationDefinition("A10_P2F_25_P5_75", ((P2F, 0.25), (P5, 0.75)), "two_policy"),
    AllocationDefinition("A11_P2F_50_P5_50", ((P2F, 0.50), (P5, 0.50)), "two_policy"),
    AllocationDefinition("A12_P2F_75_P5_25", ((P2F, 0.75), (P5, 0.25)), "two_policy"),

    AllocationDefinition("A13_P2R_25_P5_75", ((P2R, 0.25), (P5, 0.75)), "two_policy"),
    AllocationDefinition("A14_P2R_50_P5_50", ((P2R, 0.50), (P5, 0.50)), "two_policy"),
    AllocationDefinition("A15_P2R_75_P5_25", ((P2R, 0.75), (P5, 0.25)), "two_policy"),

    AllocationDefinition(
        "A16_P2F_P4_P5_equal",
        ((P2F, 1.0 / 3.0), (P4, 1.0 / 3.0), (P5, 1.0 / 3.0)),
        "three_policy",
    ),
    AllocationDefinition(
        "A17_P2R_P4_P5_equal",
        ((P2R, 1.0 / 3.0), (P4, 1.0 / 3.0), (P5, 1.0 / 3.0)),
        "three_policy",
    ),
)


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


def _map_next_sessions(targets: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Map each signal date to the next market session without future leakage."""
    market_dates = (
        pd.to_datetime(prices["trade_date"])
        .dt.normalize()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    next_map = {
        market_dates[i]: market_dates[i + 1]
        for i in range(len(market_dates) - 1)
    }

    out = targets.copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.normalize()
    out["next_session_date"] = out["trade_date"].map(next_map)
    if out["next_session_date"].isna().any():
        bad = sorted(out.loc[out["next_session_date"].isna(), "trade_date"].unique())
        raise ValueError(f"Missing next session for signal dates: {bad[:10]}")

    open_keys = set(
        zip(
            pd.to_datetime(prices["trade_date"]).dt.normalize(),
            prices["symbol"].astype(str),
        )
    )
    out["entry_available"] = [
        (pd.Timestamp(d), str(s)) in open_keys
        for d, s in zip(out["next_session_date"], out["symbol"])
    ]
    if not out["entry_available"].all():
        bad = out.loc[
            ~out["entry_available"],
            ["policy_id", "trade_date", "next_session_date", "symbol"],
        ]
        raise ValueError(
            "Selected CP4B target missing next-session price row: "
            + bad.head(20).to_string(index=False)
        )
    return out


def _target_diagnostics(targets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for allocation_id, group in targets.groupby("policy_id", sort=True):
        by_date = group.groupby("trade_date")
        counts = by_date.size()
        max_w = by_date["target_weight"].max()
        overlaps = by_date["sleeve_count"].apply(lambda s: int((s > 1).sum()))
        rows.append(
            {
                "policy_id": allocation_id,
                "dates": int(group["trade_date"].nunique()),
                "target_rows": int(len(group)),
                "symbols": int(group["symbol"].nunique()),
                "target_count_min": int(counts.min()),
                "target_count_median": float(counts.median()),
                "target_count_max": int(counts.max()),
                "mean_max_target_weight": float(max_w.mean()),
                "max_target_weight": float(max_w.max()),
                "mean_overlap_symbol_count": float(overlaps.mean()),
                "max_overlap_symbol_count": int(overlaps.max()),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    for definition in ALLOCATIONS:
        definition.validate()

    selections = pd.read_parquet(DEPLOYMENT_SELECTIONS)
    selections["trade_date"] = pd.to_datetime(
        selections["trade_date"]
    ).dt.normalize()
    if not selections["shariah_eligible"].astype(bool).all():
        raise ValueError("CP4B input contains non-Shariah deployment row")
    if (selections["trade_date"] >= pd.Timestamp("2026-01-01")).any():
        raise ValueError("2026 row in CP4B deployment selections")

    prices = load_execution_prices(maximum_date=LAST_PRE_HOLDOUT_DATE)
    required_prices = {"trade_date", "symbol", "open_adj", "low_adj", "close_adj"}
    missing = sorted(required_prices - set(prices.columns))
    if missing:
        raise ValueError(f"CP4B execution prices missing: {missing}")

    target_frames = [
        build_allocation_targets(selections, definition)
        for definition in ALLOCATIONS
    ]
    targets = pd.concat(target_frames, ignore_index=True)
    targets = _map_next_sessions(targets, prices)

    if targets.duplicated(["policy_id", "trade_date", "symbol"]).any():
        raise ValueError("Duplicate merged CP4B target")
    weight_sums = targets.groupby(["policy_id", "trade_date"])["target_weight"].sum()
    if not np.allclose(weight_sums.to_numpy(), 1.0, atol=1e-10, rtol=0):
        raise ValueError("CP4B target weights do not sum to one")

    target_diag = _target_diagnostics(targets)

    trade_frames = []
    position_frames = []
    nav_frames = []
    summaries = []

    for capital in CAPITAL_GRID:
        for definition in ALLOCATIONS:
            result = build_weighted_execution_portfolio(
                policy_id=definition.allocation_id,
                mapped_targets=targets,
                prices=prices,
                config=ExecutionConfig(
                    starting_capital=capital,
                    buy_limit_premium=0.02,
                    fill_mode="touch_fill",
                ),
            )
            assert_no_holdout(result.trades)
            assert_no_holdout(result.positions)
            assert_no_holdout(result.nav)

            for frame in (result.trades, result.positions, result.nav):
                frame["allocation_id"] = definition.allocation_id
                frame["allocation_category"] = definition.category

            trade_frames.append(result.trades)
            position_frames.append(result.positions)
            nav_frames.append(result.nav)

            summary = summarize_execution_nav(
                result.nav,
                starting_capital=capital,
            )
            summary["allocation_id"] = definition.allocation_id
            summary["allocation_category"] = definition.category
            summary["sleeves"] = "|".join(
                f"{p}:{w:.12g}" for p, w in definition.sleeves
            )
            summary["trade_rows"] = int(len(result.trades))
            summary["unique_symbols_traded"] = (
                int(result.trades["symbol"].nunique())
                if len(result.trades)
                else 0
            )
            summaries.append(summary)

    trades = pd.concat(trade_frames, ignore_index=True)
    positions = pd.concat(position_frames, ignore_index=True)
    nav = pd.concat(nav_frames, ignore_index=True)
    summary = pd.DataFrame(summaries)

    expected = len(ALLOCATIONS) * len(CAPITAL_GRID)
    if len(summary) != expected:
        raise ValueError(f"Expected {expected} summaries, got {len(summary)}")

    if (nav["cash"] < -1e-6).any():
        raise ValueError("Negative cash in CP4B")
    if not trades.empty:
        q = pd.to_numeric(trades["shares"], errors="raise")
        if not ((q > 0) & (q == q.round())).all():
            raise ValueError("Non-integer CP4B shares")

    _write(targets, OUT_TARGETS)
    _write(trades, OUT_TRADES)
    _write(positions, OUT_POSITIONS)
    _write(nav, OUT_NAV)
    _write(summary, OUT_SUMMARY)

    cap1m = summary.loc[
        summary["starting_capital"].astype(float) == 1_000_000.0
    ].copy().sort_values("allocation_id")

    report = f"""# C11 CP4B — Capital Allocation and Merged-Portfolio Execution

## Frozen evaluation design

CP4B does not search continuous allocation weights and does not select weights
by maximizing historical return.

The allocation grid was specified before this execution comparison:

- six standalones;
- P4/P5 at 25/75, 50/50 and 75/25;
- P2-filter/P5 at 25/75, 50/50 and 75/25;
- P2-refill/P5 at 25/75, 50/50 and 75/25;
- equal-third P2-filter/P4/P5;
- equal-third P2-refill/P4/P5.

P1 filter/refill remain standalone diagnostics because CP4A showed that P1
requires a large selection transformation under the Shariah gate.

## Portfolio construction

Each sleeve is equal-weight internally on each signal date. Sleeve weights are
then applied. If multiple sleeves select the same symbol, their weights are
aggregated into **one target position and one order stream**. NAVs from
independent sleeves are not added together.

Execution is the frozen CP3 primary rule:

- signal-session close +2% BUY limit;
- next session only;
- open fill when open <= limit;
- otherwise intraday-touch proxy at the limit when low <= limit;
- otherwise miss with no chase;
- whole shares;
- exact broker costs;
- no leverage;
- next-open reductions/exits with deferred exits where required.

## Target diagnostics

{target_diag.to_markdown(index=False)}

## PKR 1,000,000 results

{cap1m[
    [
        "allocation_id",
        "allocation_category",
        "ending_nav",
        "annualized_return",
        "annualized_volatility",
        "sharpe_zero_rf",
        "max_drawdown",
        "buy_fill_fraction",
        "missed_buy_additions",
        "unfunded_buy_additions",
        "mean_cash_fraction",
        "total_transaction_cost",
    ]
].to_markdown(index=False)}

## Decision boundary

These results are diagnostic. CP4B must not choose the historically highest
returning allocation mechanically. The final deployment choice should consider
risk-adjusted return, drawdown, cash drag, execution quality, concentration,
overlap and the provenance/degree of transformation of each input policy.
Concentration and overlap are investigated explicitly in CP5.

## Outputs

- `{OUT_TARGETS}`
- `{OUT_TRADES}`
- `{OUT_POSITIONS}`
- `{OUT_NAV}`
- `{OUT_SUMMARY}`
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")

    manifest = {
        "contract": "C11",
        "checkpoint": "CP4B",
        "status": "COMPLETE",
        "holdout_accessed": False,
        "selection_rule": "predefined_allocation_grid_not_return_optimized",
        "execution_rule": "C11_CP3_primary_touch_2pct",
        "allocations": [
            {
                "allocation_id": d.allocation_id,
                "category": d.category,
                "sleeves": [
                    {"policy_id": p, "weight": w} for p, w in d.sleeves
                ],
            }
            for d in ALLOCATIONS
        ],
        "capital_grid": list(map(float, CAPITAL_GRID)),
        "inputs": {
            str(DEPLOYMENT_SELECTIONS): _sha256(DEPLOYMENT_SELECTIONS),
            str(CP4A_MANIFEST): _sha256(CP4A_MANIFEST),
            str(CP3_MANIFEST): _sha256(CP3_MANIFEST),
            str(DAILY_OHLCV): _sha256(DAILY_OHLCV),
        },
        "outputs": {
            str(OUT_TARGETS): {"rows": len(targets), "sha256": _sha256(OUT_TARGETS)},
            str(OUT_TRADES): {"rows": len(trades), "sha256": _sha256(OUT_TRADES)},
            str(OUT_POSITIONS): {"rows": len(positions), "sha256": _sha256(OUT_POSITIONS)},
            str(OUT_NAV): {"rows": len(nav), "sha256": _sha256(OUT_NAV)},
            str(OUT_SUMMARY): {"rows": len(summary), "sha256": _sha256(OUT_SUMMARY)},
        },
        "target_diagnostics": target_diag.to_dict(orient="records"),
        "capital_1m_results": cap1m.to_dict(orient="records"),
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print("=== C11 CP4B: PREDEFINED CAPITAL-ALLOCATION GRID ===")
    print(f"allocations={len(ALLOCATIONS)} capital_levels={len(CAPITAL_GRID)} runs={expected}")
    print()
    print("=== TARGET DIAGNOSTICS ===")
    print(target_diag.to_string(index=False))
    print()
    print("=== PKR 1,000,000 ===")
    print(
        cap1m[
            [
                "allocation_id",
                "ending_nav",
                "annualized_return",
                "sharpe_zero_rf",
                "max_drawdown",
                "buy_fill_fraction",
                "missed_buy_additions",
                "unfunded_buy_additions",
                "mean_cash_fraction",
                "total_transaction_cost",
            ]
        ].to_string(index=False)
    )
    print()
    print(f"Targets:   {len(targets):,} -> {OUT_TARGETS}")
    print(f"Trades:    {len(trades):,} -> {OUT_TRADES}")
    print(f"Positions: {len(positions):,} -> {OUT_POSITIONS}")
    print(f"NAV:       {len(nav):,} -> {OUT_NAV}")
    print(f"Summary:   {len(summary):,} -> {OUT_SUMMARY}")
    print(f"Report:    {REPORT}")
    print(f"Manifest:  {MANIFEST}")


if __name__ == "__main__":
    main()
