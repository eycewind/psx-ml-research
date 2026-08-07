from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.inputs import LAST_PRE_HOLDOUT_DATE, assert_no_holdout, load_c10_selections, load_execution_prices
from psx_ml.c10.prices import map_next_session_entries
from psx_ml.c11.whole_share_portfolio import WholeShareConfig, build_whole_share_portfolio, summarize_whole_share_nav


CAPITAL_GRID = (50_000.0, 100_000.0, 250_000.0, 500_000.0, 1_000_000.0)
POLICIES = (
    "P1_broad_canonical",
    "P2_conservative_consensus",
    "P4_kmi30_strict",
    "P5_shariah_screened",
)

PROCESSED = Path("data/processed/c11")
REPORTS = Path("artifacts/reports")
TRADES = PROCESSED / "whole_share_trades.parquet"
POSITIONS = PROCESSED / "whole_share_positions.parquet"
NAV = PROCESSED / "whole_share_nav.parquet"
SUMMARY = PROCESSED / "whole_share_summary.parquet"
REPORT = REPORTS / "C11_CP2_WHOLE_SHARE_CAPITAL_REPORT.md"
MANIFEST = REPORTS / "C11_CP2_WHOLE_SHARE_CAPITAL_MANIFEST.json"
C10_COST_SUMMARY = Path("data/processed/c10/cost_summary.parquet")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    with path.open("wb") as f:
        pq.write_table(table, f)


def _load_c10_baseline() -> pd.DataFrame:
    frame = pd.read_parquet(C10_COST_SUMMARY)
    frame = frame.loc[
        frame["cost_schedule_id"].astype(str) == "actual_broker_all_in",
        [
            "policy_id", "ending_net_nav", "net_annualized_return",
            "net_sharpe_zero_rf", "net_max_drawdown",
        ],
    ].copy()
    if set(frame["policy_id"]) != set(POLICIES):
        raise ValueError("C10 actual-cost baseline policy set mismatch")
    return frame


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    selections = load_c10_selections()
    prices = load_execution_prices(maximum_date=LAST_PRE_HOLDOUT_DATE)
    mapped = map_next_session_entries(selections, prices)
    baseline = _load_c10_baseline()

    trade_frames = []
    position_frames = []
    nav_frames = []
    summaries = []

    for capital in CAPITAL_GRID:
        for policy_id in POLICIES:
            result = build_whole_share_portfolio(
                policy_id=policy_id,
                mapped_selections=mapped,
                prices=prices,
                config=WholeShareConfig(starting_capital=capital),
            )
            assert_no_holdout(result.trades)
            assert_no_holdout(result.positions)
            assert_no_holdout(result.nav)

            trade_frames.append(result.trades)
            position_frames.append(result.positions)
            nav_frames.append(result.nav)
            summary = summarize_whole_share_nav(result.nav, starting_capital=capital)
            summary["trade_rows"] = int(len(result.trades))
            summary["position_rows"] = int(len(result.positions))
            summary["unique_symbols_traded"] = int(result.trades["symbol"].nunique()) if not result.trades.empty else 0
            summaries.append(summary)

    trades = pd.concat(trade_frames, ignore_index=True)
    positions = pd.concat(position_frames, ignore_index=True)
    nav = pd.concat(nav_frames, ignore_index=True)
    summary = pd.DataFrame(summaries)

    baseline_scaled = baseline.rename(columns={
        "ending_net_nav": "c10_1m_ending_net_nav",
        "net_annualized_return": "c10_fractional_net_annualized_return",
        "net_sharpe_zero_rf": "c10_fractional_net_sharpe",
        "net_max_drawdown": "c10_fractional_net_max_drawdown",
    })
    summary = summary.merge(baseline_scaled, on="policy_id", how="left", validate="many_to_one")
    summary["annualized_return_delta_vs_c10_reference"] = (
        summary["annualized_return"] - summary["c10_fractional_net_annualized_return"]
    )
    summary["sharpe_delta_vs_c10_reference"] = (
        summary["sharpe_zero_rf"] - summary["c10_fractional_net_sharpe"]
    )

    for name, frame in (("trades", trades), ("positions", positions), ("nav", nav)):
        if not frame.empty:
            dates = pd.to_datetime(frame["trade_date"])
            if (dates >= pd.Timestamp("2026-01-01")).any():
                raise ValueError(f"2026 holdout access in {name}")

    if not trades.empty:
        quantities = pd.to_numeric(trades["shares"], errors="raise")
        if not ((quantities > 0) & (quantities == quantities.round())).all():
            raise ValueError("Non-integer shares found in C11 CP2 trades")
    if (nav["cash"] < -1e-6).any():
        raise ValueError("Negative cash found in C11 CP2")

    _write_parquet(trades, TRADES)
    _write_parquet(positions, POSITIONS)
    _write_parquet(nav, NAV)
    _write_parquet(summary, SUMMARY)

    view_cols = [
        "policy_id", "starting_capital", "ending_nav", "annualized_return",
        "sharpe_zero_rf", "max_drawdown", "mean_cash_fraction",
        "total_skipped_price_targets", "rebalance_dates_with_price_skips",
        "total_transaction_cost", "annualized_return_delta_vs_c10_reference",
    ]
    report = f"""# C11 CP2 — Whole-Share Capital-Aware Deployment Report

## Scope

This checkpoint measures the deployment cost of whole-share execution across the CP1-frozen capital grid.

Included:

- accepted C10 P1, P2, P4 and P5 selections;
- next-session `open_adj` execution;
- whole shares only;
- equal target weights;
- net-to-target rebalancing;
- exact `actual_broker_all_in` costs deducted from cash at each trade;
- explicit residual cash;
- no leverage;
- C10 missing-close and deferred-exit valuation rules.

Not yet included:

- P1/P2 Shariah filter/refill transformation;
- policy combinations;
- gap/limit-order rules;
- partial fills or intraday market impact;
- stop-loss logic.

**Important:** P1/P2 rows in CP2 are research diagnostics only. They are not final executable C11 portfolios until the mandatory Shariah gate is applied in the later deployment-policy checkpoint.

## Results

{summary[view_cols].sort_values(["starting_capital", "policy_id"]).to_markdown(index=False)}

## C10 reference comparison

`annualized_return_delta_vs_c10_reference` compares the C11 whole-share, exact-cash result against the accepted C10 fractional-share `actual_broker_all_in` annualized return.

**This is a reference/reconciliation metric, not a pure whole-share drag measurement.** C10 applies transaction costs as a return-level overlay on the gross portfolio ledger, while C11 CP2 deducts exact transaction costs directly from portfolio cash at each trade. The two systems therefore differ in both share granularity and fee-accounting mechanics. A positive or negative delta must not be interpreted as the isolated effect of whole-share sizing.

C10 remains immutable.

## Outputs

- `{TRADES}`
- `{POSITIONS}`
- `{NAV}`
- `{SUMMARY}`
"""
    REPORT.write_text(report, encoding="utf-8")

    manifest = {
        "contract": "C11",
        "checkpoint": 2,
        "status": "COMPLETE",
        "holdout_accessed": False,
        "capital_grid_pkr": list(CAPITAL_GRID),
        "policies": list(POLICIES),
        "portfolio_basis": {
            "shares": "whole_integer",
            "weighting": "equal_weight",
            "execution": "next_session_open_adj",
            "trading": "net_to_target",
            "cost_schedule": "actual_broker_all_in_exact_cash_deduction",
            "leverage": False,
            "residual_cash": "retained",
            "shariah_note": "P1/P2 are research-only until later mandatory PIT Shariah gating",
        },
        "inputs": {
            str(C10_COST_SUMMARY): _sha256(C10_COST_SUMMARY),
        },
        "outputs": {
            str(TRADES): {"rows": int(len(trades)), "sha256": _sha256(TRADES)},
            str(POSITIONS): {"rows": int(len(positions)), "sha256": _sha256(POSITIONS)},
            str(NAV): {"rows": int(len(nav)), "sha256": _sha256(NAV)},
            str(SUMMARY): {"rows": int(len(summary)), "sha256": _sha256(SUMMARY)},
        },
        "summaries": summary.sort_values(["starting_capital", "policy_id"]).to_dict(orient="records"),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")

    print(summary[view_cols].sort_values(["starting_capital", "policy_id"]).to_string(index=False))
    print()
    print(f"Trades:    {len(trades):,} -> {TRADES}")
    print(f"Positions: {len(positions):,} -> {POSITIONS}")
    print(f"NAV rows:  {len(nav):,} -> {NAV}")
    print(f"Summary:   {len(summary):,} -> {SUMMARY}")
    print(f"Report:    {REPORT}")
    print(f"Manifest:  {MANIFEST}")


if __name__ == "__main__":
    main()
