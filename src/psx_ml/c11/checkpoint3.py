from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.inputs import (
    LAST_PRE_HOLDOUT_DATE,
    assert_no_holdout,
    load_c10_selections,
    load_execution_prices,
)
from psx_ml.c10.prices import map_next_session_entries
from psx_ml.c11.checkpoint2 import CAPITAL_GRID, POLICIES
from psx_ml.c11.execution_portfolio import (
    ExecutionConfig,
    build_execution_portfolio,
    summarize_execution_nav,
)


SCENARIOS = (
    ("touch_1pct", "touch_fill", 0.01, False),
    ("touch_2pct_primary", "touch_fill", 0.02, True),
    ("touch_3pct", "touch_fill", 0.03, False),
    ("open_only_1pct", "open_only", 0.01, False),
    ("open_only_2pct", "open_only", 0.02, False),
    ("open_only_3pct", "open_only", 0.03, False),
)
PRIMARY_SCENARIO_ID = "touch_2pct_primary"

PROCESSED = Path("data/processed/c11")
REPORTS = Path("artifacts/reports")

TRADES = PROCESSED / "execution_trades.parquet"
POSITIONS = PROCESSED / "execution_positions.parquet"
NAV = PROCESSED / "execution_nav.parquet"
SUMMARY = PROCESSED / "execution_summary.parquet"

REPORT = REPORTS / "C11_CP3_EXECUTION_MODEL_REPORT.md"
MANIFEST = REPORTS / "C11_CP3_EXECUTION_MODEL_MANIFEST.json"

CP2_SUMMARY = PROCESSED / "whole_share_summary.parquet"
DAILY_OHLCV = Path("data/cache/daily_ohlcv.parquet")
C9_SELECTIONS = Path("data/processed/c9/candidate_selections.parquet")
P4_SELECTIONS = Path("data/processed/c10/p4_kmi30_selections.parquet")
P5_SELECTIONS = Path("data/processed/c10/p5_shariah_screened_selections.parquet")


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


def _load_cp2_reference() -> pd.DataFrame:
    frame = pd.read_parquet(CP2_SUMMARY)
    required = {
        "policy_id",
        "starting_capital",
        "ending_nav",
        "annualized_return",
        "sharpe_zero_rf",
        "max_drawdown",
        "mean_cash_fraction",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"CP2 summary missing columns: {missing}")

    expected = {
        (policy, capital)
        for policy in POLICIES
        for capital in CAPITAL_GRID
    }
    actual = set(
        zip(
            frame["policy_id"].astype(str),
            frame["starting_capital"].astype(float),
        )
    )
    if actual != expected:
        raise ValueError("CP2 summary policy/capital grid mismatch")
    return frame[list(required)].copy()


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    selections = load_c10_selections()
    prices = load_execution_prices(maximum_date=LAST_PRE_HOLDOUT_DATE)

    required_price_columns = {
        "trade_date", "symbol", "open_adj", "low_adj", "close_adj"
    }
    missing_prices = sorted(required_price_columns - set(prices.columns))
    if missing_prices:
        raise ValueError(
            f"Execution prices missing CP3 columns: {missing_prices}"
        )

    mapped = map_next_session_entries(selections, prices)
    cp2 = _load_cp2_reference()

    trade_frames: list[pd.DataFrame] = []
    position_frames: list[pd.DataFrame] = []
    nav_frames: list[pd.DataFrame] = []
    summaries: list[dict[str, object]] = []

    for scenario_id, fill_mode, premium, is_primary in SCENARIOS:
        for capital in CAPITAL_GRID:
            for policy_id in POLICIES:
                result = build_execution_portfolio(
                    policy_id=policy_id,
                    mapped_selections=mapped,
                    prices=prices,
                    config=ExecutionConfig(
                        starting_capital=capital,
                        buy_limit_premium=premium,
                        fill_mode=fill_mode,
                    ),
                )
                assert_no_holdout(result.trades)
                assert_no_holdout(result.positions)
                assert_no_holdout(result.nav)

                for frame in (result.trades, result.positions, result.nav):
                    frame["scenario_id"] = scenario_id
                    frame["fill_mode"] = fill_mode
                    frame["buy_limit_premium"] = float(premium)
                    frame["is_primary_scenario"] = bool(is_primary)

                trade_frames.append(result.trades)
                position_frames.append(result.positions)
                nav_frames.append(result.nav)

                summary = summarize_execution_nav(
                    result.nav,
                    starting_capital=capital,
                )
                summary["scenario_id"] = scenario_id
                summary["fill_mode"] = fill_mode
                summary["buy_limit_premium"] = float(premium)
                summary["is_primary_scenario"] = bool(is_primary)
                summary["trade_rows"] = int(len(result.trades))
                summary["position_rows"] = int(len(result.positions))
                summary["unique_symbols_traded"] = (
                    int(result.trades["symbol"].nunique())
                    if not result.trades.empty
                    else 0
                )
                summaries.append(summary)

    trades = pd.concat(trade_frames, ignore_index=True)
    positions = pd.concat(position_frames, ignore_index=True)
    nav = pd.concat(nav_frames, ignore_index=True)
    summary = pd.DataFrame(summaries)

    cp2_ref = cp2.rename(
        columns={
            "ending_nav": "cp2_ending_nav",
            "annualized_return": "cp2_annualized_return",
            "sharpe_zero_rf": "cp2_sharpe_zero_rf",
            "max_drawdown": "cp2_max_drawdown",
            "mean_cash_fraction": "cp2_mean_cash_fraction",
        }
    )
    summary = summary.merge(
        cp2_ref,
        on=["policy_id", "starting_capital"],
        how="left",
        validate="many_to_one",
    )
    summary["annualized_return_delta_vs_cp2"] = (
        summary["annualized_return"] - summary["cp2_annualized_return"]
    )
    summary["sharpe_delta_vs_cp2"] = (
        summary["sharpe_zero_rf"] - summary["cp2_sharpe_zero_rf"]
    )
    summary["ending_nav_ratio_vs_cp2"] = (
        summary["ending_nav"] / summary["cp2_ending_nav"]
    )

    expected_rows = len(SCENARIOS) * len(CAPITAL_GRID) * len(POLICIES)
    if len(summary) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} CP3 summary rows, got {len(summary)}"
        )

    if not trades.empty:
        dates = pd.to_datetime(trades["trade_date"])
        if (dates >= pd.Timestamp("2026-01-01")).any():
            raise ValueError("2026 holdout access in CP3 trades")
        quantities = pd.to_numeric(trades["shares"], errors="raise")
        if not ((quantities > 0) & (quantities == quantities.round())).all():
            raise ValueError("Non-integer CP3 trade shares")
    for name, frame in (("positions", positions), ("nav", nav)):
        dates = pd.to_datetime(frame["trade_date"])
        if (dates >= pd.Timestamp("2026-01-01")).any():
            raise ValueError(f"2026 holdout access in CP3 {name}")

    if (nav["cash"] < -1e-6).any():
        raise ValueError("Negative cash found in CP3")

    buy_trades = trades.loc[trades["side"].astype(str) == "BUY"].copy()
    if not buy_trades.empty:
        if buy_trades["fill_quality"].isna().any():
            raise ValueError("BUY trade missing fill_quality")
        allowed_fill = {"open", "intraday_touch_proxy"}
        if not set(buy_trades["fill_quality"].astype(str)).issubset(allowed_fill):
            raise ValueError("Unexpected CP3 BUY fill quality")

    _write_parquet(trades, TRADES)
    _write_parquet(positions, POSITIONS)
    _write_parquet(nav, NAV)
    _write_parquet(summary, SUMMARY)

    primary = summary.loc[
        summary["scenario_id"].astype(str) == PRIMARY_SCENARIO_ID
    ].copy()
    primary_cols = [
        "policy_id",
        "starting_capital",
        "ending_nav",
        "annualized_return",
        "sharpe_zero_rf",
        "max_drawdown",
        "buy_fill_fraction",
        "missed_buy_additions",
        "unfunded_buy_additions",
        "mean_cash_fraction",
        "annualized_return_delta_vs_cp2",
    ]

    sensitivity = summary.loc[
        summary["starting_capital"].astype(float) == 1_000_000.0,
        [
            "scenario_id",
            "policy_id",
            "annualized_return",
            "sharpe_zero_rf",
            "max_drawdown",
            "buy_fill_fraction",
            "missed_buy_additions",
            "unfunded_buy_additions",
            "mean_cash_fraction",
        ],
    ].sort_values(["policy_id", "scenario_id"])

    report = f"""# C11 CP3 — One-Session Limit Execution Model

## Frozen execution rule

Primary deployment proxy:

- BUY reference: signal-session `close_adj`;
- BUY maximum price: signal close + 2%;
- validity: next trading session only;
- if next-session open <= limit: fill at open;
- otherwise, if next-session low <= limit: fill at limit and mark `intraday_touch_proxy`;
- otherwise: BUY addition is missed and is not chased on a later day;
- SELL reductions and exits: next available open, retaining the accepted deferred-exit rule;
- whole shares only;
- exact `actual_broker_all_in` costs deducted from cash;
- no leverage.

The `intraday_touch_proxy` is not claimed to be a certain fill. Daily OHLC proves only that the level was touched during the session; it does not establish queue priority or intraday sequencing.

`buy_fill_fraction` counts only BUY additions that actually execute at least one whole share. If the price rule is satisfied but available cash cannot fund one whole share after exact fees, the attempt is recorded separately as `unfunded_buy_additions` and is not counted as a fill.

Conservative sensitivity:

- `open_only`: a BUY fills only when the next-session open is at/below the limit.

Premium sensitivities of +1% and +3% are reported only as robustness scenarios. They are **not** candidates from which C11 selects the historically best-performing threshold.

P1/P2 remain research diagnostics at CP3. They cannot become executable C11 portfolios until the mandatory PIT Shariah gate is applied.

## Primary +2% touch-fill results

{primary[primary_cols].sort_values(["starting_capital", "policy_id"]).to_markdown(index=False)}

## Sensitivity at PKR 1,000,000

{sensitivity.to_markdown(index=False)}

## CP2 comparison

`annualized_return_delta_vs_cp2` is a direct execution-model comparison because CP3 retains CP2's whole-share sizing, fee accounting, valuation rules and capital grid while adding the one-session BUY price cap/fill rule.

A CP3 improvement versus CP2 can arise from obtaining a lower assumed BUY price on `intraday_touch_proxy` rows. Such improvement must be interpreted cautiously because daily OHLC cannot prove that the full order would have filled at the limit.

## Outputs

- `{TRADES}`
- `{POSITIONS}`
- `{NAV}`
- `{SUMMARY}`
"""
    REPORT.write_text(report, encoding="utf-8")

    manifest = {
        "contract": "C11",
        "checkpoint": 3,
        "status": "COMPLETE",
        "holdout_accessed": False,
        "primary_scenario_id": PRIMARY_SCENARIO_ID,
        "scenarios": [
            {
                "scenario_id": scenario_id,
                "fill_mode": fill_mode,
                "buy_limit_premium": premium,
                "is_primary": is_primary,
            }
            for scenario_id, fill_mode, premium, is_primary in SCENARIOS
        ],
        "execution_basis": {
            "shares": "whole_integer",
            "weighting": "equal_weight",
            "target_share_basis": "CP2 next-open target quantities",
            "buy_reference": "signal_session_close_adj",
            "buy_validity": "next_session_only",
            "primary_buy_limit_premium": 0.02,
            "primary_fill_mode": "touch_fill",
            "touch_fill_semantics": (
                "open<=limit => open; else low<=limit => limit proxy; "
                "else missed, no chase"
            ),
            "buy_fill_fraction_semantics": (
                "executed BUY additions / BUY addition attempts; attempts "
                "that satisfy the price rule but cannot fund one whole share "
                "after exact fees are counted separately as unfunded"
            ),
            "sell_execution": "next_available_open_with_deferred_exit_handling",
            "cost_schedule": "actual_broker_all_in_exact_cash_deduction",
            "leverage": False,
            "p1_p2_note": (
                "research-only until mandatory PIT Shariah gating in later C11 checkpoint"
            ),
        },
        "inputs": {
            str(CP2_SUMMARY): _sha256(CP2_SUMMARY),
            str(DAILY_OHLCV): _sha256(DAILY_OHLCV),
            str(C9_SELECTIONS): _sha256(C9_SELECTIONS),
            str(P4_SELECTIONS): _sha256(P4_SELECTIONS),
            str(P5_SELECTIONS): _sha256(P5_SELECTIONS),
        },
        "outputs": {
            str(TRADES): {"rows": int(len(trades)), "sha256": _sha256(TRADES)},
            str(POSITIONS): {
                "rows": int(len(positions)),
                "sha256": _sha256(POSITIONS),
            },
            str(NAV): {"rows": int(len(nav)), "sha256": _sha256(NAV)},
            str(SUMMARY): {"rows": int(len(summary)), "sha256": _sha256(SUMMARY)},
        },
        "primary_summaries": primary.sort_values(
            ["starting_capital", "policy_id"]
        ).to_dict(orient="records"),
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print("=== PRIMARY: touch_fill, signal close +2%, one session ===")
    print(
        primary[primary_cols]
        .sort_values(["starting_capital", "policy_id"])
        .to_string(index=False)
    )
    print()
    print("=== SENSITIVITY: PKR 1,000,000 ===")
    print(sensitivity.to_string(index=False))
    print()
    print(f"Trades:    {len(trades):,} -> {TRADES}")
    print(f"Positions: {len(positions):,} -> {POSITIONS}")
    print(f"NAV rows:  {len(nav):,} -> {NAV}")
    print(f"Summary:   {len(summary):,} -> {SUMMARY}")
    print(f"Report:    {REPORT}")
    print(f"Manifest:  {MANIFEST}")


if __name__ == "__main__":
    main()
