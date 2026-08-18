from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from psx_ml.c10.p5_selection import load_screened_history
from psx_ml.c11.live_orders import (
    PRIMARY_ALLOCATION_ID,
    build_session_open_orders,
    build_signal_plan,
)
from psx_ml.data.sqlite import connect_readonly, require_daily_schema
from psx_ml.live.account_state import load_manual_account_state
from psx_ml.live.live_scoring import LiveScoringPaths, score, sha256_file
from psx_ml.live.live_selection import (
    DEFAULT_KMI30_HISTORY,
    DEFAULT_SHARIAH_HISTORY,
    _load_kmi30_history,
    build_live_selections,
)


@dataclass(frozen=True)
class ProductionPipelinePaths:
    repo: Path
    source_db: Path
    account_state: Path
    output_root: Path = Path("artifacts/live")
    model: Path | None = None
    c8_manifest: Path | None = None
    c6_universe: Path | None = None
    security_master: Path | None = None
    feature_config: Path | None = None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ProductionPipelinePaths":
        return cls(
            repo=args.repo.resolve(),
            source_db=args.source_db.resolve(),
            account_state=args.account_state.resolve(),
            output_root=args.output_root,
            model=args.model,
            c8_manifest=args.c8_manifest,
            c6_universe=args.c6_universe,
            security_master=args.security_master,
            feature_config=args.feature_config,
        )


def _day(value: object) -> str:
    return pd.Timestamp(value).normalize().date().isoformat()


def _resolve_under_repo(repo: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def _git_revision(repo: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def _load_exact_daily_prices(source_db: Path, date: str, price_column: str) -> pd.DataFrame:
    require = ["trade_date", "symbol", price_column]
    with connect_readonly(source_db) as con:
        require_daily_schema(con, require)
        latest = con.execute("SELECT MAX(trade_date) FROM daily_ohlc").fetchone()[0]
        rows = [
            dict(row)
            for row in con.execute(
                "SELECT trade_date,symbol,"
                + price_column
                + " FROM daily_ohlc WHERE trade_date = ? ORDER BY symbol",
                (date,),
            )
        ]

    if not rows:
        raise ValueError(
            f"Required production date {date} not present in daily_ohlc "
            f"for {price_column}; latest available date is {latest}"
        )

    frame = pd.DataFrame(rows)
    frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="raise").dt.normalize()
    frame["symbol"] = frame["symbol"].astype(str).str.strip().str.upper()
    frame[price_column] = pd.to_numeric(frame[price_column], errors="coerce")

    if frame.duplicated(["trade_date", "symbol"]).any():
        dupes = frame.loc[
            frame.duplicated(["trade_date", "symbol"], keep=False),
            ["trade_date", "symbol"],
        ]
        raise ValueError("Duplicate production price rows:\n" + dupes.to_string(index=False))
    if frame[price_column].isna().any() or (frame[price_column] <= 0).any():
        bad = frame.loc[
            frame[price_column].isna() | (frame[price_column] <= 0),
            "symbol",
        ].tolist()
        raise ValueError(f"Missing/invalid {price_column} for {date}: {bad}")
    return frame


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_order_ticket_json(path: Path, orders: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for row in orders.to_dict("records"):
        out = {}
        for key, value in row.items():
            if key in {"signal_date", "execution_date"}:
                out[key] = _day(value)
            elif pd.isna(value):
                out[key] = None
            elif hasattr(value, "item"):
                out[key] = value.item()
            else:
                out[key] = value
        rows.append(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return rows


def _artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "rows": int(pd.read_parquet(path).shape[0]),
    }


def _json_artifact(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"JSON handoff artifact must be a top-level list: {path}")
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "rows": len(payload),
        "top_level_type": "list",
    }


def _require_exact_frame_date(frame: pd.DataFrame, date: str, name: str) -> pd.DataFrame:
    if "trade_date" not in frame.columns or "symbol" not in frame.columns:
        raise ValueError(f"{name} missing required trade_date/symbol columns")
    result = frame.copy()
    result["trade_date"] = pd.to_datetime(result["trade_date"], errors="raise").dt.normalize()
    result["symbol"] = result["symbol"].astype(str).str.strip().str.upper()
    day = pd.Timestamp(date).normalize()
    if not result["trade_date"].eq(day).any():
        available = sorted(result["trade_date"].dt.strftime("%Y-%m-%d").unique().tolist())
        raise ValueError(f"{name} has no rows for required signal date {date}; available dates: {available}")
    return result


def run_production_pipeline(
    *,
    paths: ProductionPipelinePaths,
    signal_date: object,
    execution_date: object,
    scorer: Callable[[LiveScoringPaths, str], dict] = score,
) -> dict:
    signal_day = _day(signal_date)
    execution_day = _day(execution_date)
    if pd.Timestamp(execution_day) <= pd.Timestamp(signal_day):
        raise ValueError("execution_date must be after signal_date")

    repo = paths.repo.resolve()
    output_root = _resolve_under_repo(repo, paths.output_root)
    live_dir = output_root / signal_day
    live_dir.mkdir(parents=True, exist_ok=True)

    closes = _load_exact_daily_prices(paths.source_db, signal_day, "close_adj")
    opens = _load_exact_daily_prices(paths.source_db, execution_day, "open_adj")

    scoring_paths = LiveScoringPaths.from_args(
        repo=repo,
        source_db=paths.source_db,
        model=paths.model,
        c8_manifest=paths.c8_manifest,
        c6_universe=paths.c6_universe,
        security_master=paths.security_master,
        feature_config=paths.feature_config,
        output_root=output_root,
    )
    scoring_manifest = scorer(scoring_paths, signal_day)

    predictions_path = Path(scoring_manifest["outputs"]["predictions_path"])
    features_path = Path(scoring_manifest["outputs"]["features_path"])
    predictions = _require_exact_frame_date(pd.read_parquet(predictions_path), signal_day, "predictions")
    features = _require_exact_frame_date(pd.read_parquet(features_path), signal_day, "features")
    kmi30 = _load_kmi30_history(repo / DEFAULT_KMI30_HISTORY)
    screened = load_screened_history(repo / DEFAULT_SHARIAH_HISTORY)

    selections = build_live_selections(
        predictions=predictions,
        features=features,
        kmi30_history=kmi30,
        screened_history=screened,
        date=signal_day,
    )
    selections_path = live_dir / "selections.parquet"
    selections.to_parquet(selections_path, index=False)

    signal_plan = build_signal_plan(
        selections=selections,
        signal_date=signal_day,
        signal_closes=closes,
    )
    if set(signal_plan["allocation_id"].astype(str)) != {PRIMARY_ALLOCATION_ID}:
        raise ValueError("Production signal plan did not preserve accepted allocation")
    signal_plan_path = live_dir / "signal_plan.parquet"
    signal_plan.to_parquet(signal_plan_path, index=False)

    state = load_manual_account_state(paths.account_state)
    orders = build_session_open_orders(
        signal_plan=signal_plan,
        execution_date=execution_day,
        session_opens=opens,
        current_positions=state.positions,
        cash=state.cash_pkr,
    )
    order_ticket_path = live_dir / f"order_ticket_{execution_day}.parquet"
    orders.to_parquet(order_ticket_path, index=False)
    order_ticket_json_path = live_dir / f"order_ticket_{execution_day}.json"
    _write_order_ticket_json(order_ticket_json_path, orders)

    selection_manifest = {
        "date": signal_day,
        "rows": int(len(selections)),
        "p4_rows": int((selections["policy_id"].astype(str) == "D_P4_kmi30_strict").sum()),
        "p5_rows": int((selections["policy_id"].astype(str) == "D_P5_shariah_screened").sum()),
        "overlap_symbols": int(selections.groupby("symbol")["policy_id"].nunique().eq(2).sum()),
        "output": str(selections_path.resolve()),
        "output_sha256": sha256_file(selections_path),
    }
    _write_json(live_dir / "selection_manifest.json", selection_manifest)

    manifest = {
        "manifest_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_revision": _git_revision(repo),
        "signal_date": signal_day,
        "execution_date": execution_day,
        "allocation_id": PRIMARY_ALLOCATION_ID,
        "source_data": {
            "source_db": str(paths.source_db.resolve()),
            "source_db_sha256": sha256_file(paths.source_db),
            "signal_close_date": signal_day,
            "execution_open_date": execution_day,
        },
        "inputs": {
            "predictions": _artifact(predictions_path),
            "features": _artifact(features_path),
            "account_state": {
                "path": str(paths.account_state.resolve()),
                "sha256": sha256_file(paths.account_state),
            },
        },
        "outputs": {
            "selections": _artifact(selections_path),
            "signal_plan": _artifact(signal_plan_path),
            "order_ticket": _artifact(order_ticket_path),
            "order_ticket_json": _json_artifact(order_ticket_json_path),
        },
        "scoring_manifest": scoring_manifest,
        "selection_manifest": selection_manifest,
        "order_ticket_schema": list(orders.columns),
    }
    manifest_path = live_dir / "production_manifest.json"
    _write_json(manifest_path, manifest)
    print(json.dumps({
        "signal_date": signal_day,
        "execution_date": execution_day,
        "allocation_id": PRIMARY_ALLOCATION_ID,
        "order_ticket": str(order_ticket_path.resolve()),
        "order_ticket_json": str(order_ticket_json_path.resolve()),
        "production_manifest": str(manifest_path.resolve()),
    }, indent=2, sort_keys=True))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Production-safe A07 ticket pipeline")
    p.add_argument("--source-db", type=Path, required=True)
    p.add_argument("--signal-date", required=True)
    p.add_argument("--execution-date", required=True)
    p.add_argument("--account-state", type=Path, required=True)
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--output-root", type=Path, default=Path("artifacts/live"))
    p.add_argument("--model", type=Path)
    p.add_argument("--c8-manifest", type=Path)
    p.add_argument("--c6-universe", type=Path)
    p.add_argument("--security-master", type=Path)
    p.add_argument("--feature-config", type=Path)
    return p


def main() -> None:
    args = build_parser().parse_args()
    run_production_pipeline(
        paths=ProductionPipelinePaths.from_args(args),
        signal_date=args.signal_date,
        execution_date=args.execution_date,
    )


if __name__ == "__main__":
    main()
