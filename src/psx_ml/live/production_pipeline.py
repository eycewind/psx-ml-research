from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, time, timezone
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
from psx_ml.live.eod_exclusions import (
    REQUIRED_CONSUMER,
    SOURCE as EOD_EXCLUSION_SOURCE,
    exclusion_symbols,
    load_eod_symbol_exclusions,
)
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
            account_state=getattr(args, "account_state", Path("config/live_account.json")).resolve(),
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


def _read_frame(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"JSON table must be a top-level list of rows: {path}")
        return pd.DataFrame(payload)
    raise ValueError(f"Unsupported table format: {path}")


def _file_artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
    }


def _stable_json_hash(payload: object) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _business_rows(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for row in frame.to_dict("records"):
        out = {}
        for key, value in row.items():
            if key in {"trade_date", "signal_date", "execution_date"}:
                out[key] = _day(value)
            elif pd.isna(value):
                out[key] = None
            elif hasattr(value, "item"):
                out[key] = value.item()
            else:
                out[key] = value
        rows.append(out)
    return rows


def _write_order_ticket_json(path: Path, orders: pd.DataFrame) -> list[dict[str, object]]:
    rows = _business_rows(orders)
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
    if not payload:
        raise ValueError(f"JSON handoff artifact must be non-empty: {path}")
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "rows": len(payload),
        "top_level_type": "list",
    }


def _phase_a_manifest_path(output_root: Path, signal_date: str) -> Path:
    return output_root / signal_date / "phase_a_decision_manifest.json"


def _phase_b_manifest_path(output_root: Path, signal_date: str) -> Path:
    return output_root / signal_date / "production_manifest.json"


def _copy_artifact(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


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


def _remove_exact_date_exclusions(
    frame: pd.DataFrame,
    *,
    date: str,
    name: str,
    excluded_symbols: set[str],
) -> pd.DataFrame:
    if not excluded_symbols:
        return frame
    if "trade_date" not in frame.columns or "symbol" not in frame.columns:
        raise ValueError(f"{name} missing required trade_date/symbol columns")
    day = pd.Timestamp(date).normalize()
    symbols = frame["symbol"].astype(str).str.strip().str.upper()
    mask = frame["trade_date"].eq(day) & symbols.isin(excluded_symbols)
    return frame.loc[~mask].copy()


def _phase_a_decision_hash(
    *,
    signal_date: str,
    execution_date: str,
    scoring_manifest: dict,
    selections: pd.DataFrame,
    signal_plan: pd.DataFrame,
    source_db: Path,
    eod_symbol_exclusions: list[dict[str, str]],
) -> str:
    model = scoring_manifest.get("model", {})
    payload = {
        "artifact_kind": "c17_phase_a_decision",
        "allocation_id": PRIMARY_ALLOCATION_ID,
        "signal_date": signal_date,
        "execution_date": execution_date,
        "source_db_sha256": sha256_file(source_db),
        "model": {
            "path": model.get("path"),
            "sha256": model.get("sha256"),
            "model_name": model.get("model_name"),
            "target_name": model.get("target_name"),
            "feature_variant": model.get("feature_variant"),
            "retrained": model.get("retrained"),
        },
        "eod_symbol_exclusions": eod_symbol_exclusions,
        "selections": _business_rows(selections),
        "signal_plan": _business_rows(signal_plan),
    }
    return _stable_json_hash(payload)


def _phase_b_decision_hash(
    *,
    phase_a_hash: str,
    live_open_path: Path,
    account_state_path: Path,
    deployable_capital_pkr: float,
    orders: pd.DataFrame,
) -> str:
    return _stable_json_hash(
        {
            "artifact_kind": "c17_phase_b_ticket",
            "allocation_id": PRIMARY_ALLOCATION_ID,
            "phase_a_decision_sha256": phase_a_hash,
            "live_open_sha256": sha256_file(live_open_path),
            "account_state_sha256": sha256_file(account_state_path),
            "deployable_capital_pkr": float(deployable_capital_pkr),
            "orders": _business_rows(orders),
        }
    )


def _load_existing_manifest(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_same_identity(existing: dict, expected: dict, *, label: str) -> None:
    keys = ["allocation_id", "signal_date", "execution_date"]
    mismatches = {
        key: {"existing": existing.get(key), "expected": expected.get(key)}
        for key in keys
        if existing.get(key) != expected.get(key)
    }
    if mismatches:
        raise ValueError(f"Existing {label} manifest identity mismatch: {mismatches}")


def run_phase_a(
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
    manifest_path = _phase_a_manifest_path(output_root, signal_day)
    existing = _load_existing_manifest(manifest_path)

    eod_symbol_exclusions = load_eod_symbol_exclusions(paths.source_db, signal_day)
    excluded_symbols = exclusion_symbols(eod_symbol_exclusions)
    closes = _load_exact_daily_prices(paths.source_db, signal_day, "close_adj")
    with tempfile.TemporaryDirectory(prefix="psx-c17-phase-a-") as tmp:
        candidate_root = Path(tmp)
        scoring_paths = LiveScoringPaths.from_args(
            repo=repo,
            source_db=paths.source_db,
            model=paths.model,
            c8_manifest=paths.c8_manifest,
            c6_universe=paths.c6_universe,
            security_master=paths.security_master,
            feature_config=paths.feature_config,
            output_root=candidate_root,
        )
        scoring_manifest = scorer(scoring_paths, signal_day)
        predictions_path = Path(scoring_manifest["outputs"]["predictions_path"])
        features_path = Path(scoring_manifest["outputs"]["features_path"])
        predictions = _require_exact_frame_date(pd.read_parquet(predictions_path), signal_day, "predictions")
        features = _require_exact_frame_date(pd.read_parquet(features_path), signal_day, "features")
        predictions = _remove_exact_date_exclusions(
            predictions,
            date=signal_day,
            name="predictions",
            excluded_symbols=excluded_symbols,
        )
        features = _remove_exact_date_exclusions(
            features,
            date=signal_day,
            name="features",
            excluded_symbols=excluded_symbols,
        )

        kmi30 = _load_kmi30_history(repo / DEFAULT_KMI30_HISTORY)
        screened = load_screened_history(repo / DEFAULT_SHARIAH_HISTORY)
        selections = build_live_selections(
            predictions=predictions,
            features=features,
            kmi30_history=kmi30,
            screened_history=screened,
            date=signal_day,
        )
        signal_plan = build_signal_plan(
            selections=selections,
            signal_date=signal_day,
            signal_closes=closes,
        )
        if set(signal_plan["allocation_id"].astype(str)) != {PRIMARY_ALLOCATION_ID}:
            raise ValueError("Phase A signal plan did not preserve accepted allocation")

        decision_hash = _phase_a_decision_hash(
            signal_date=signal_day,
            execution_date=execution_day,
            scoring_manifest=scoring_manifest,
            selections=selections,
            signal_plan=signal_plan,
            source_db=paths.source_db,
            eod_symbol_exclusions=eod_symbol_exclusions,
        )

        expected_identity = {
            "allocation_id": PRIMARY_ALLOCATION_ID,
            "signal_date": signal_day,
            "execution_date": execution_day,
        }
        if existing is not None:
            _assert_same_identity(existing, expected_identity, label="Phase-A")
            if existing.get("phase_a_decision_sha256") != decision_hash:
                raise ValueError(
                    "Conflicting Phase-A decision for "
                    f"{PRIMARY_ALLOCATION_ID}/{signal_day}/{execution_day}"
                )
            return existing

        live_dir.mkdir(parents=True, exist_ok=True)
        final_predictions_path = live_dir / "predictions.parquet"
        final_features_path = live_dir / "features.parquet"
        final_selections_path = live_dir / "selections.parquet"
        final_signal_plan_path = live_dir / "signal_plan.parquet"
        if excluded_symbols:
            predictions.to_parquet(final_predictions_path, index=False)
            features.to_parquet(final_features_path, index=False)
        else:
            _copy_artifact(predictions_path, final_predictions_path)
            _copy_artifact(features_path, final_features_path)
        selections.to_parquet(final_selections_path, index=False)
        signal_plan.to_parquet(final_signal_plan_path, index=False)
        durable_scoring_manifest = dict(scoring_manifest)
        durable_scoring_manifest["outputs"] = {
            **scoring_manifest.get("outputs", {}),
            "features_path": str(final_features_path.resolve()),
            "features_sha256": sha256_file(final_features_path),
            "predictions_path": str(final_predictions_path.resolve()),
            "predictions_sha256": sha256_file(final_predictions_path),
        }

        selection_manifest = {
            "date": signal_day,
            "rows": int(len(selections)),
            "p4_rows": int((selections["policy_id"].astype(str) == "D_P4_kmi30_strict").sum()),
            "p5_rows": int((selections["policy_id"].astype(str) == "D_P5_shariah_screened").sum()),
            "overlap_symbols": int(selections.groupby("symbol")["policy_id"].nunique().eq(2).sum()),
            "output": str(final_selections_path.resolve()),
            "output_sha256": sha256_file(final_selections_path),
            "eod_symbol_exclusions": {
                "source": EOD_EXCLUSION_SOURCE,
                "required_consumer": REQUIRED_CONSUMER,
                "signal_date": signal_day,
                "excluded_symbol_count": len(eod_symbol_exclusions),
                "symbols": eod_symbol_exclusions,
            },
        }
        _write_json(live_dir / "selection_manifest.json", selection_manifest)

        manifest = {
            "manifest_version": 1,
            "artifact_kind": "c17_phase_a_decision",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "code_revision": _git_revision(repo),
            "allocation_id": PRIMARY_ALLOCATION_ID,
            "signal_date": signal_day,
            "execution_date": execution_day,
            "phase_a_decision_sha256": decision_hash,
            "source_data": {
                "source_db": str(paths.source_db.resolve()),
                "source_db_sha256": sha256_file(paths.source_db),
                "signal_close_date": signal_day,
                "eod_symbol_exclusion_source": EOD_EXCLUSION_SOURCE,
            },
            "eod_symbol_exclusions": {
                "source": EOD_EXCLUSION_SOURCE,
                "required_consumer": REQUIRED_CONSUMER,
                "signal_date": signal_day,
                "excluded_symbol_count": len(eod_symbol_exclusions),
                "symbols": eod_symbol_exclusions,
            },
            "model": scoring_manifest.get("model", {}),
            "inputs": {
                "features": _artifact(final_features_path),
                "predictions": _artifact(final_predictions_path),
            },
            "outputs": {
                "selections": _artifact(final_selections_path),
                "signal_plan": _artifact(final_signal_plan_path),
                "selection_manifest": _file_artifact(live_dir / "selection_manifest.json"),
            },
            "scoring_manifest": durable_scoring_manifest,
            "selection_manifest": selection_manifest,
        }
        _write_json(manifest_path, manifest)
        return manifest


def _is_at_or_after_settle_boundary(value: object) -> bool:
    try:
        ts = pd.Timestamp(value)
    except Exception:
        return False
    if pd.isna(ts):
        return False
    if ts.tzinfo is not None:
        ts = ts.tz_convert("Asia/Karachi")
    return ts.time() >= time(9, 40)


def _validate_live_open_frame(
    frame: pd.DataFrame,
    *,
    execution_date: str,
    required_symbols: set[str],
) -> pd.DataFrame:
    required = {
        "trade_date",
        "symbol",
        "open",
        "first_qualifying_poll_ts",
        "confirmed_poll_ts",
        "confirmation_count",
        "source",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Live-open artifact missing columns: {missing}")

    x = frame.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"], errors="raise").dt.normalize()
    x["symbol"] = x["symbol"].astype(str).str.strip().str.upper()
    x["open"] = pd.to_numeric(x["open"], errors="coerce")
    x["confirmation_count"] = pd.to_numeric(x["confirmation_count"], errors="coerce")
    x["source"] = x["source"].astype(str)
    first_ok = x["first_qualifying_poll_ts"].map(_is_at_or_after_settle_boundary)
    confirmed_ok = x["confirmed_poll_ts"].map(_is_at_or_after_settle_boundary)

    day = pd.Timestamp(execution_date).normalize()
    wrong_date = x.loc[~x["trade_date"].eq(day), ["trade_date", "symbol"]]
    if not wrong_date.empty:
        raise ValueError(
            "Live-open artifact contains wrong execution date rows:\n"
            + wrong_date.head(20).to_string(index=False)
        )
    if x.duplicated(["trade_date", "symbol"]).any():
        dupes = x.loc[x.duplicated(["trade_date", "symbol"], keep=False), ["trade_date", "symbol"]]
        raise ValueError("Duplicate live-open rows:\n" + dupes.head(20).to_string(index=False))
    bad = x.loc[
        (
            x["open"].isna()
            | (x["open"] <= 0)
            | (x["source"] != "psx_portal")
            | x["first_qualifying_poll_ts"].isna()
            | x["confirmed_poll_ts"].isna()
            | x["confirmation_count"].lt(2)
            | ~first_ok
            | ~confirmed_ok
        ),
        "symbol",
    ].tolist()
    if bad:
        raise ValueError(f"Invalid settled live open for: {bad}")

    available = set(x["symbol"])
    missing_symbols = sorted(required_symbols - available)
    if missing_symbols:
        raise ValueError(f"Missing required execution open for: {missing_symbols}")

    return x.loc[x["symbol"].isin(required_symbols), ["trade_date", "symbol", "open"]].rename(
        columns={"open": "open_adj"}
    )


def _load_phase_a_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("artifact_kind") != "c17_phase_a_decision":
        raise ValueError(f"Not a C17 Phase-A decision manifest: {path}")
    if manifest.get("allocation_id") != PRIMARY_ALLOCATION_ID:
        raise ValueError("Phase-A decision does not preserve accepted allocation")
    return manifest


def run_phase_b(
    *,
    phase_a_manifest_path: Path,
    live_open_path: Path,
    account_state_path: Path,
) -> dict:
    phase_a_manifest_path = phase_a_manifest_path.resolve()
    live_open_path = live_open_path.resolve()
    account_state_path = account_state_path.resolve()
    phase_a = _load_phase_a_manifest(phase_a_manifest_path)
    signal_day = _day(phase_a["signal_date"])
    execution_day = _day(phase_a["execution_date"])
    output_root = phase_a_manifest_path.parent.parent
    live_dir = output_root / signal_day
    manifest_path = _phase_b_manifest_path(output_root, signal_day)
    existing = _load_existing_manifest(manifest_path)

    signal_plan_path = Path(phase_a["outputs"]["signal_plan"]["path"])
    signal_plan = pd.read_parquet(signal_plan_path)
    if set(signal_plan["allocation_id"].astype(str)) != {PRIMARY_ALLOCATION_ID}:
        raise ValueError("Phase-A signal plan does not preserve accepted allocation")
    if set(pd.to_datetime(signal_plan["trade_date"]).dt.normalize().dt.strftime("%Y-%m-%d")) != {signal_day}:
        raise ValueError("Phase-A signal plan date does not match manifest")

    state = load_manual_account_state(
        account_state_path,
        require_deployable_capital=True,
    )
    required_symbols = set(signal_plan["symbol"].astype(str).str.strip().str.upper()) | set(
        state.positions["symbol"].astype(str).str.strip().str.upper()
    )
    opens = _validate_live_open_frame(
        _read_frame(live_open_path),
        execution_date=execution_day,
        required_symbols=required_symbols,
    )

    orders = build_session_open_orders(
        signal_plan=signal_plan,
        execution_date=execution_day,
        session_opens=opens,
        current_positions=state.positions,
        cash=state.cash_pkr,
        deployable_capital_pkr=state.deployable_capital_pkr,
    )
    phase_b_hash = _phase_b_decision_hash(
        phase_a_hash=phase_a["phase_a_decision_sha256"],
        live_open_path=live_open_path,
        account_state_path=account_state_path,
        deployable_capital_pkr=state.deployable_capital_pkr,
        orders=orders,
    )

    expected_identity = {
        "allocation_id": PRIMARY_ALLOCATION_ID,
        "signal_date": signal_day,
        "execution_date": execution_day,
    }
    if existing is not None:
        _assert_same_identity(existing, expected_identity, label="Phase-B")
        if existing.get("phase_b_ticket_sha256") != phase_b_hash:
            raise ValueError(
                "Conflicting Phase-B ticket for "
                f"{PRIMARY_ALLOCATION_ID}/{signal_day}/{execution_day}"
            )
        return existing

    live_dir.mkdir(parents=True, exist_ok=True)
    order_ticket_path = live_dir / f"order_ticket_{execution_day}.parquet"
    order_ticket_json_path = live_dir / f"order_ticket_{execution_day}.json"
    orders.to_parquet(order_ticket_path, index=False)
    _write_order_ticket_json(order_ticket_json_path, orders)

    manifest = {
        "manifest_version": 2,
        "artifact_kind": "c17_phase_b_ticket",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_revision": _git_revision(output_root.parent.parent),
        "allocation_id": PRIMARY_ALLOCATION_ID,
        "signal_date": signal_day,
        "execution_date": execution_day,
        "phase_b_ticket_sha256": phase_b_hash,
        "phase_a": {
            "manifest_path": str(phase_a_manifest_path),
            "manifest_sha256": sha256_file(phase_a_manifest_path),
            "phase_a_decision_sha256": phase_a["phase_a_decision_sha256"],
        },
        "inputs": {
            "live_open": _file_artifact(live_open_path),
            "account_state": _file_artifact(account_state_path),
        },
        "account_state_schema": {
            "cash_pkr": "actual broker cash available for orders",
            "deployable_capital_pkr": "explicit strategy capital mandate used for target sizing",
            "positions": "object mapping broker-held symbol to current whole shares",
        },
        "strategy_capital": {
            "deployable_capital_pkr": float(state.deployable_capital_pkr),
            "source": "manual_account_state.deployable_capital_pkr",
            "target_sizing_formula": (
                "target_shares = floor(deployable_capital_pkr * target_weight / execution_open_price)"
            ),
        },
        "outputs": {
            "order_ticket": _artifact(order_ticket_path),
            "order_ticket_json": _json_artifact(order_ticket_json_path),
        },
        "order_ticket_schema": list(orders.columns),
    }
    _write_json(manifest_path, manifest)
    return manifest


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
        deployable_capital_pkr=state.deployable_capital_pkr,
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


def _add_scoring_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--source-db", type=Path, required=True)
    p.add_argument("--signal-date", required=True)
    p.add_argument("--execution-date", required=True)
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--output-root", type=Path, default=Path("artifacts/live"))
    p.add_argument("--model", type=Path)
    p.add_argument("--c8-manifest", type=Path)
    p.add_argument("--c6-universe", type=Path)
    p.add_argument("--security-master", type=Path)
    p.add_argument("--feature-config", type=Path)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Production-safe A07 ticket pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("phase-a", help="freeze after-close C17 Phase-A signal decision")
    _add_scoring_args(a)

    b = sub.add_parser("phase-b", help="build C17 Phase-B ticket from frozen decision and settled live opens")
    b.add_argument("--phase-a-manifest", type=Path, required=True)
    b.add_argument("--live-open", type=Path, required=True)
    b.add_argument("--account-state", type=Path, required=True)

    r = sub.add_parser("run", help="C16-compatible one-shot score/select/plan/ticket path")
    _add_scoring_args(r)
    r.add_argument("--account-state", type=Path, required=True)
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "phase-a":
        result = run_phase_a(
            paths=ProductionPipelinePaths.from_args(args),
            signal_date=args.signal_date,
            execution_date=args.execution_date,
        )
        print(json.dumps({
            "phase_a_manifest": str(_phase_a_manifest_path(_resolve_under_repo(args.repo.resolve(), args.output_root), _day(args.signal_date)).resolve()),
            "phase_a_decision_sha256": result["phase_a_decision_sha256"],
        }, indent=2, sort_keys=True))
    elif args.command == "phase-b":
        result = run_phase_b(
            phase_a_manifest_path=args.phase_a_manifest,
            live_open_path=args.live_open,
            account_state_path=args.account_state,
        )
        print(json.dumps({
            "production_manifest": str(_phase_b_manifest_path(Path(args.phase_a_manifest).resolve().parent.parent, _day(result["signal_date"])).resolve()),
            "order_ticket_json": result["outputs"]["order_ticket_json"]["path"],
            "phase_b_ticket_sha256": result["phase_b_ticket_sha256"],
        }, indent=2, sort_keys=True))
    elif args.command == "run":
        run_production_pipeline(
            paths=ProductionPipelinePaths.from_args(args),
            signal_date=args.signal_date,
            execution_date=args.execution_date,
        )
    else:
        raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
