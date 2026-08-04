from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.inputs import (
    C9_SELECTIONS_PATH,
    P4_SELECTIONS_PATH,
    LAST_PRE_HOLDOUT_DATE,
    PRICE_PATH,
    assert_no_holdout,
    load_c10_selections,
    load_execution_prices,
)
from psx_ml.c10.portfolio import (
    PortfolioConfig,
    build_frictionless_portfolio,
    summarize_frictionless_nav,
)
from psx_ml.c10.prices import map_next_session_entries


PROCESSED_DIR = Path("data/processed/c10")
REPORT_DIR = Path("artifacts/reports")

TRADES_PATH = PROCESSED_DIR / "frictionless_trades.parquet"
POSITIONS_PATH = PROCESSED_DIR / "frictionless_positions.parquet"
NAV_PATH = PROCESSED_DIR / "frictionless_nav.parquet"

REPORT_PATH = REPORT_DIR / "C10_FRICTIONLESS_REPORT.md"
MANIFEST_PATH = REPORT_DIR / "C10_CHECKPOINT2_MANIFEST.json"
DELIVERY_PATH = REPORT_DIR / "C10_CHECKPOINT2_DELIVERY.md"


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
    """
    Write Parquet through an already-open local file handle.

    This bypasses PyArrow filesystem discovery, which can fail in some
    mixed Conda/PyArrow environments with duplicate 'file' scheme
    registration.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    table = pa.Table.from_pandas(
        frame,
        preserve_index=False,
    )

    with path.open("wb") as handle:
        pq.write_table(table, handle)


def _canonical_policy_frame(
    frame: pd.DataFrame,
    policy_ids: set[str],
) -> pd.DataFrame:
    subset = frame.loc[
        frame["policy_id"].isin(policy_ids)
    ].copy()

    sort_columns = [
        column
        for column in (
            "policy_id",
            "trade_date",
            "symbol",
            "side",
            "reason",
        )
        if column in subset.columns
    ]

    return subset.sort_values(
        sort_columns,
        kind="mergesort",
    ).reset_index(drop=True)


def _assert_existing_p1_p2_unchanged(
    *,
    path: Path,
    regenerated: pd.DataFrame,
) -> None:
    if not path.exists():
        return

    existing = pd.read_parquet(path)
    policies = {
        "P1_broad_canonical",
        "P2_conservative_consensus",
    }

    expected = _canonical_policy_frame(
        existing,
        policies,
    )
    actual = _canonical_policy_frame(
        regenerated,
        policies,
    )

    pd.testing.assert_frame_equal(
        actual,
        expected,
        check_dtype=False,
        check_exact=False,
        rtol=1e-12,
        atol=1e-9,
    )



def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    config = PortfolioConfig(
        starting_capital=1_000_000.0
    )

    selections = load_c10_selections()

    prices = load_execution_prices(
        maximum_date=LAST_PRE_HOLDOUT_DATE,
    )

    mapped = map_next_session_entries(
        selections,
        prices,
    )

    policy_ids = [
        "P1_broad_canonical",
        "P2_conservative_consensus",
        "P4_kmi30_strict",
    ]

    trade_frames: list[pd.DataFrame] = []
    position_frames: list[pd.DataFrame] = []
    nav_frames: list[pd.DataFrame] = []
    summaries: list[dict[str, object]] = []

    for policy_id in policy_ids:
        result = build_frictionless_portfolio(
            policy_id=policy_id,
            mapped_selections=mapped,
            prices=prices,
            config=config,
        )

        assert_no_holdout(result.trades)
        assert_no_holdout(result.positions)
        assert_no_holdout(result.nav)

        trade_frames.append(result.trades)
        position_frames.append(result.positions)
        nav_frames.append(result.nav)

        summary = summarize_frictionless_nav(
            result.nav,
            starting_capital=config.starting_capital,
        )

        summary["trade_rows"] = int(
            len(result.trades)
        )

        summary["position_rows"] = int(
            len(result.positions)
        )

        summary["unique_symbols_traded"] = int(
            result.trades["symbol"].nunique()
        )

        summary["deferred_exit_trades"] = int(
            (
                result.trades["reason"]
                == "deferred_exit"
            ).sum()
        )

        summaries.append(summary)

    trades = pd.concat(
        trade_frames,
        ignore_index=True,
    )

    positions = pd.concat(
        position_frames,
        ignore_index=True,
    )

    nav = pd.concat(
        nav_frames,
        ignore_index=True,
    )

    _assert_existing_p1_p2_unchanged(
        path=TRADES_PATH,
        regenerated=trades,
    )
    _assert_existing_p1_p2_unchanged(
        path=POSITIONS_PATH,
        regenerated=positions,
    )
    _assert_existing_p1_p2_unchanged(
        path=NAV_PATH,
        regenerated=nav,
    )

    write_parquet_without_filesystem(
        trades,
        TRADES_PATH,
    )

    write_parquet_without_filesystem(
        positions,
        POSITIONS_PATH,
    )

    write_parquet_without_filesystem(
        nav,
        NAV_PATH,
    )

    summary_frame = pd.DataFrame(summaries)

    report = f"""# C10 Frictionless Portfolio Report

## Scope

This checkpoint evaluates portfolio construction and gross accounting only.

Included:

- frozen policies P1, P2 and P4;
- next-session adjusted-open execution;
- equal target weights at every weekly rebalance;
- net trading from existing holdings to new target holdings;
- fractional shares;
- daily adjusted-close valuation;
- prior-close carry-forward for missing daily closes;
- deferred exits when an outgoing holding has no valid rebalance-date open;
- explicit cash and invested-value accounting.

Excluded:

- brokerage;
- taxes and levies;
- slippage;
- bid/ask spread;
- market impact;
- board-lot restrictions;
- capacity limits;
- financing and interest.

Starting capital for each independent policy portfolio: PKR {config.starting_capital:,.2f}

## Gross performance

{summary_frame.to_markdown(index=False)}

## Output ledgers

- Trades: `{TRADES_PATH}`
- Positions: `{POSITIONS_PATH}`
- Daily NAV: `{NAV_PATH}`

These are frictionless results and are not estimates of realizable net performance.
"""

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    manifest = {
        "contract": "C10",
        "checkpoint": 2,
        "status": "COMPLETE",
        "holdout_accessed": False,
        "portfolio_basis": {
            "starting_capital_pkr": (
                config.starting_capital
            ),
            "weighting": "equal_weight",
            "rebalance_execution": (
                "next_session_open_adj"
            ),
            "valuation": "daily_close_adj",
            "missing_close_policy": (
                "latest_prior_valid_close"
            ),
            "missing_exit_open_policy": (
                "defer_until_first_later_valid_open"
            ),
            "shares": "fractional",
            "trading": "net_to_target",
            "fees": 0.0,
            "taxes": 0.0,
            "slippage": 0.0,
            "capacity_limits": False,
        },
        "inputs": {
            str(C9_SELECTIONS_PATH): sha256_file(C9_SELECTIONS_PATH),
            str(P4_SELECTIONS_PATH): sha256_file(P4_SELECTIONS_PATH),
            str(PRICE_PATH): sha256_file(
                PRICE_PATH
            ),
        },
        "outputs": {
            str(TRADES_PATH): {
                "sha256": sha256_file(TRADES_PATH),
                "rows": int(len(trades)),
            },
            str(POSITIONS_PATH): {
                "sha256": sha256_file(POSITIONS_PATH),
                "rows": int(len(positions)),
            },
            str(NAV_PATH): {
                "sha256": sha256_file(NAV_PATH),
                "rows": int(len(nav)),
            },
        },
        "policy_summaries": summaries,
    }

    MANIFEST_PATH.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    delivery = """# C10 Checkpoint 2 Delivery

Status: **COMPLETE**

Checkpoint 2 adds:

- equal-weight portfolio construction for P1, P2 and P4;
- net rebalancing at next-session adjusted opens;
- trade-level gross cash-flow accounting;
- deferred exits where a valid opening execution price is unavailable;
- prior-close carry-forward for missing daily valuation closes;
- daily position valuation at adjusted closes;
- daily NAV and return series;
- gross performance and drawdown summaries;
- explicit confirmation that 2026 remained inaccessible.

No transaction costs, slippage, taxes, capacity restrictions, or board-lot rules are included yet.
"""

    DELIVERY_PATH.write_text(
        delivery,
        encoding="utf-8",
    )

    print(summary_frame.to_string(index=False))
    print()
    print(
        f"Trades:    {len(trades):,} -> {TRADES_PATH}"
    )
    print(
        f"Positions: {len(positions):,} -> {POSITIONS_PATH}"
    )
    print(
        f"NAV rows:  {len(nav):,} -> {NAV_PATH}"
    )


if __name__ == "__main__":
    main()