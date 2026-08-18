import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from psx_ml.c11.live_orders import PRIMARY_ALLOCATION_ID
from psx_ml.live.production_pipeline import (
    ProductionPipelinePaths,
    build_parser,
    run_phase_a,
    run_phase_b,
    run_production_pipeline,
)


ORDER_COLUMNS = [
    "allocation_id",
    "signal_date",
    "execution_date",
    "symbol",
    "target_weight",
    "current_shares",
    "target_shares",
    "order_side",
    "order_shares",
    "order_type",
    "reference_open",
    "buy_limit_price",
    "status",
    "reason",
    "estimated_notional",
    "estimated_commission",
    "estimated_sst",
    "estimated_cdc",
    "estimated_total_cost",
    "cash_after_planned_orders",
]


def _write_reference_inputs(repo: Path) -> None:
    ref = repo / "data/reference"
    ref.mkdir(parents=True)
    pd.DataFrame(
        {
            "symbol": ["AAA", "BBB", "CCC"],
            "effective_from": ["2025-12-01"] * 3,
            "effective_to": ["9999-12-31"] * 3,
        }
    ).to_csv(ref / "kmi30_membership_history.csv", index=False)
    pd.DataFrame(
        {
            "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
            "effective_from": [pd.Timestamp("2025-12-01")] * 6,
            "effective_to": [pd.NaT] * 6,
            "screening_snapshot_date": [pd.Timestamp("2025-12-01")] * 6,
            "membership_source": ["official_full_screening_table"] * 6,
            "membership_confidence": ["medium"] * 6,
            "is_shariah_screened_eligible": [True] * 6,
        }
    ).to_csv(ref / "kmi_all_share_screened_universe_history.csv", index=False)


def _write_account(repo: Path) -> Path:
    path = repo / "account.json"
    path.write_text(json.dumps({"cash_pkr": 100_000, "positions": {}}), encoding="utf-8")
    return path


def _write_source_db(
    repo: Path,
    include_execution_date: bool = True,
    include_close: bool = True,
    signal_date: str = "2026-08-10",
    execution_date: str = "2026-08-11",
) -> Path:
    path = repo / "source.db"
    con = sqlite3.connect(path)
    close_col = "close_adj REAL," if include_close else ""
    con.execute(
        "CREATE TABLE daily_ohlc ("
        "trade_date TEXT, symbol TEXT, open_adj REAL, "
        + close_col
        + "volume_adj REAL)"
    )
    rows = []
    for symbol, close, open_ in [
        ("AAA", 100.0, 101.0),
        ("BBB", 90.0, 91.0),
        ("CCC", 80.0, 81.0),
        ("DDD", 70.0, 71.0),
        ("EEE", 60.0, 61.0),
        ("FFF", 50.0, 51.0),
    ]:
        if include_close:
            rows.append((signal_date, symbol, open_ - 1.0, close, 1000.0))
            if include_execution_date:
                rows.append((execution_date, symbol, open_, close + 1.0, 1000.0))
        else:
            rows.append((signal_date, symbol, open_ - 1.0, 1000.0))
    placeholders = ",".join(["?"] * (5 if include_close else 4))
    con.executemany(f"INSERT INTO daily_ohlc VALUES ({placeholders})", rows)
    con.commit()
    con.close()
    return path


def _fake_scorer(scoring_paths, signal_date: str) -> dict:
    live_dir = scoring_paths.output_root / signal_date
    live_dir.mkdir(parents=True, exist_ok=True)
    day = pd.Timestamp(signal_date)
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
    predictions = pd.DataFrame(
        {
            "trade_date": [day] * 6,
            "symbol": symbols,
            "fold_id": ["fold_2025"] * 6,
            "horizon": [5] * 6,
            "target_family": ["market_relative_rank"] * 6,
            "feature_variant": ["B_market_context"] * 6,
            "model_name": ["lightgbm_cpu"] * 6,
            "prediction": [0.60, 0.59, 0.58, 0.57, 0.56, 0.55],
            "sector": ["A", "B", "C", "D", "E", "F"],
        }
    )
    features = pd.DataFrame(
        {
            "trade_date": [day] * 6,
            "symbol": symbols,
            "turnover_median_20obs_adj": [100, 90, 80, 70, 60, 50],
        }
    )
    predictions_path = live_dir / "predictions.parquet"
    features_path = live_dir / "features.parquet"
    predictions.to_parquet(predictions_path, index=False)
    features.to_parquet(features_path, index=False)
    return {
        "score_date": signal_date,
        "model": {
            "path": "artifacts/models/c8_supplemental/rank_5_B_market_context_fold_2025_lightgbm_cpu.txt",
            "sha256": "ecc95b9d78aa4dd26b30dbe4560eec716d4f21a8e190e59ea02b84a75d3643d5",
            "model_name": "lightgbm_cpu",
            "target_name": "fwd_market_relative_rank_5s",
            "feature_variant": "B_market_context",
            "retrained": False,
        },
        "outputs": {
            "predictions_path": str(predictions_path),
            "features_path": str(features_path),
            "prediction_rows": 6,
        },
    }


def _stale_feature_scorer(scoring_paths, signal_date: str) -> dict:
    manifest = _fake_scorer(scoring_paths, signal_date)
    features_path = Path(manifest["outputs"]["features_path"])
    features = pd.read_parquet(features_path)
    features["trade_date"] = pd.Timestamp(signal_date) - pd.Timedelta(days=1)
    features.to_parquet(features_path, index=False)
    return manifest


def _business_rows(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for row in frame.to_dict("records"):
        out = {}
        for key, value in row.items():
            if key in {"signal_date", "execution_date"}:
                out[key] = pd.Timestamp(value).date().isoformat()
            elif pd.isna(value):
                out[key] = None
            elif hasattr(value, "item"):
                out[key] = value.item()
            else:
                out[key] = value
        rows.append(out)
    return rows


def _paths(repo: Path) -> ProductionPipelinePaths:
    _write_reference_inputs(repo)
    return ProductionPipelinePaths(
        repo=repo,
        source_db=_write_source_db(repo),
        account_state=_write_account(repo),
        output_root=Path("artifacts/live"),
    )


def _phase_a_paths(repo: Path, signal_date: str = "2026-08-13", execution_date: str = "2026-08-17") -> ProductionPipelinePaths:
    _write_reference_inputs(repo)
    return ProductionPipelinePaths(
        repo=repo,
        source_db=_write_source_db(
            repo,
            include_execution_date=False,
            signal_date=signal_date,
            execution_date=execution_date,
        ),
        account_state=_write_account(repo),
        output_root=Path("artifacts/live"),
    )


def _write_live_open(repo: Path, signal_date: str, execution_date: str, *, missing_symbol: str | None = None, wrong_date: bool = False) -> Path:
    plan = pd.read_parquet(repo / f"artifacts/live/{signal_date}/signal_plan.parquet")
    rows = []
    for idx, symbol in enumerate(plan["symbol"].astype(str).str.upper()):
        if symbol == missing_symbol:
            continue
        rows.append(
            {
                "trade_date": "2026-08-18" if wrong_date else execution_date,
                "symbol": symbol,
                "open": 50.0 + idx,
                "first_qualifying_poll_ts": f"{execution_date}T09:40:30+05:00",
                "confirmed_poll_ts": f"{execution_date}T09:42:00+05:00",
                "confirmation_count": 2,
                "source": "psx_portal",
            }
        )
    if not rows:
        rows.append(
            {
                "trade_date": "2026-08-18" if wrong_date else execution_date,
                "symbol": "ZZZ",
                "open": 99.0,
                "first_qualifying_poll_ts": f"{execution_date}T09:40:30+05:00",
                "confirmed_poll_ts": f"{execution_date}T09:42:00+05:00",
                "confirmation_count": 2,
                "source": "psx_portal",
            }
        )
    path = repo / "settled_live_open.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path


def test_production_pipeline_generates_selection_plan_and_ticket_without_manual_selection_file(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    manifest = run_production_pipeline(
        paths=paths,
        signal_date="2026-08-10",
        execution_date="2026-08-11",
        scorer=_fake_scorer,
    )

    live_dir = tmp_path / "artifacts/live/2026-08-10"
    assert (live_dir / "selections.parquet").is_file()
    assert (live_dir / "signal_plan.parquet").is_file()
    assert (live_dir / "order_ticket_2026-08-11.json").is_file()
    ticket = pd.read_parquet(live_dir / "order_ticket_2026-08-11.parquet")
    assert list(ticket.columns) == ORDER_COLUMNS
    assert set(ticket["allocation_id"]) == {PRIMARY_ALLOCATION_ID}
    assert manifest["allocation_id"] == PRIMARY_ALLOCATION_ID
    assert manifest["outputs"]["order_ticket_json"]["top_level_type"] == "list"
    assert "--selections" not in build_parser().format_help()


def test_json_ticket_is_top_level_list_and_matches_parquet_business_rows(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    run_production_pipeline(
        paths=paths,
        signal_date="2026-08-10",
        execution_date="2026-08-11",
        scorer=_fake_scorer,
    )

    live_dir = tmp_path / "artifacts/live/2026-08-10"
    parquet = pd.read_parquet(live_dir / "order_ticket_2026-08-11.parquet")
    payload = json.loads((live_dir / "order_ticket_2026-08-11.json").read_text(encoding="utf-8"))

    assert isinstance(payload, list)
    assert payload
    assert payload == _business_rows(parquet)
    assert {row["signal_date"] for row in payload} == {"2026-08-10"}
    assert {row["execution_date"] for row in payload} == {"2026-08-11"}


def test_production_selection_is_deterministic(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    first = run_production_pipeline(
        paths=paths,
        signal_date="2026-08-10",
        execution_date="2026-08-11",
        scorer=_fake_scorer,
    )
    first_selection_hash = first["outputs"]["selections"]["sha256"]
    first_json_hash = first["outputs"]["order_ticket_json"]["sha256"]
    first_ticket = pd.read_parquet(tmp_path / "artifacts/live/2026-08-10/order_ticket_2026-08-11.parquet")
    first_json = json.loads((tmp_path / "artifacts/live/2026-08-10/order_ticket_2026-08-11.json").read_text(encoding="utf-8"))

    second = run_production_pipeline(
        paths=paths,
        signal_date="2026-08-10",
        execution_date="2026-08-11",
        scorer=_fake_scorer,
    )
    second_ticket = pd.read_parquet(tmp_path / "artifacts/live/2026-08-10/order_ticket_2026-08-11.parquet")

    assert second["outputs"]["selections"]["sha256"] == first_selection_hash
    assert second["outputs"]["order_ticket_json"]["sha256"] == first_json_hash
    pd.testing.assert_frame_equal(second_ticket, first_ticket)
    assert json.loads((tmp_path / "artifacts/live/2026-08-10/order_ticket_2026-08-11.json").read_text(encoding="utf-8")) == first_json


def test_missing_required_input_fails_closed(tmp_path: Path) -> None:
    _write_reference_inputs(tmp_path)
    paths = ProductionPipelinePaths(
        repo=tmp_path,
        source_db=_write_source_db(tmp_path, include_close=False),
        account_state=_write_account(tmp_path),
    )
    with pytest.raises(Exception, match="close_adj"):
        run_production_pipeline(
            paths=paths,
            signal_date="2026-08-10",
            execution_date="2026-08-11",
            scorer=_fake_scorer,
        )


def test_wrong_date_required_input_fails_closed(tmp_path: Path) -> None:
    _write_reference_inputs(tmp_path)
    paths = ProductionPipelinePaths(
        repo=tmp_path,
        source_db=_write_source_db(tmp_path, include_execution_date=False),
        account_state=_write_account(tmp_path),
    )
    with pytest.raises(ValueError, match="2026-08-11 not present"):
        run_production_pipeline(
            paths=paths,
            signal_date="2026-08-10",
            execution_date="2026-08-11",
            scorer=_fake_scorer,
        )


def test_stale_scored_feature_input_fails_closed(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    with pytest.raises(ValueError, match="features has no rows for required signal date"):
        run_production_pipeline(
            paths=paths,
            signal_date="2026-08-10",
            execution_date="2026-08-11",
            scorer=_stale_feature_scorer,
        )


def test_execution_date_must_follow_signal_date(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    with pytest.raises(ValueError, match="execution_date must be after signal_date"):
        run_production_pipeline(
            paths=paths,
            signal_date="2026-08-10",
            execution_date="2026-08-10",
            scorer=_fake_scorer,
        )


def test_phase_a_requires_no_execution_session_open_and_supports_holiday_pair(tmp_path: Path) -> None:
    manifest = run_phase_a(
        paths=_phase_a_paths(tmp_path),
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )

    assert manifest["allocation_id"] == PRIMARY_ALLOCATION_ID
    assert manifest["signal_date"] == "2026-08-13"
    assert manifest["execution_date"] == "2026-08-17"
    assert manifest["model"]["retrained"] is False
    assert (tmp_path / "artifacts/live/2026-08-13/phase_a_decision_manifest.json").is_file()
    assert (tmp_path / "artifacts/live/2026-08-13/signal_plan.parquet").is_file()


def test_phase_a_decision_is_deterministic_and_conflict_checked(tmp_path: Path) -> None:
    paths = _phase_a_paths(tmp_path)
    first = run_phase_a(
        paths=paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )
    second = run_phase_a(
        paths=paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )
    assert second["phase_a_decision_sha256"] == first["phase_a_decision_sha256"]

    def changed_scorer(scoring_paths, signal_date: str) -> dict:
        manifest = _fake_scorer(scoring_paths, signal_date)
        predictions_path = Path(manifest["outputs"]["predictions_path"])
        predictions = pd.read_parquet(predictions_path)
        predictions.loc[predictions["symbol"] == "AAA", "prediction"] = -9.0
        predictions.to_parquet(predictions_path, index=False)
        return manifest

    with pytest.raises(ValueError, match="Conflicting Phase-A decision"):
        run_phase_a(
            paths=paths,
            signal_date="2026-08-13",
            execution_date="2026-08-17",
            scorer=changed_scorer,
        )


def test_phase_b_consumes_phase_a_and_emits_canonical_json_with_provenance(tmp_path: Path) -> None:
    phase_a = run_phase_a(
        paths=_phase_a_paths(tmp_path),
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )
    live_open = _write_live_open(tmp_path, "2026-08-13", "2026-08-17")
    manifest = run_phase_b(
        phase_a_manifest_path=tmp_path / "artifacts/live/2026-08-13/phase_a_decision_manifest.json",
        live_open_path=live_open,
        account_state_path=tmp_path / "account.json",
    )

    live_dir = tmp_path / "artifacts/live/2026-08-13"
    parquet = pd.read_parquet(live_dir / "order_ticket_2026-08-17.parquet")
    payload = json.loads((live_dir / "order_ticket_2026-08-17.json").read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload == _business_rows(parquet)
    assert manifest["phase_a"]["phase_a_decision_sha256"] == phase_a["phase_a_decision_sha256"]
    assert manifest["outputs"]["order_ticket_json"]["top_level_type"] == "list"
    assert set(parquet["allocation_id"]) == {PRIMARY_ALLOCATION_ID}


def test_phase_b_rejects_wrong_date_and_missing_required_open(tmp_path: Path) -> None:
    run_phase_a(
        paths=_phase_a_paths(tmp_path),
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )
    phase_a_manifest = tmp_path / "artifacts/live/2026-08-13/phase_a_decision_manifest.json"
    with pytest.raises(ValueError, match="wrong execution date"):
        run_phase_b(
            phase_a_manifest_path=phase_a_manifest,
            live_open_path=_write_live_open(tmp_path, "2026-08-13", "2026-08-17", wrong_date=True),
            account_state_path=tmp_path / "account.json",
        )

    required_symbol = pd.read_parquet(tmp_path / "artifacts/live/2026-08-13/signal_plan.parquet")["symbol"].iloc[0]
    with pytest.raises(ValueError, match="Missing required execution open"):
        run_phase_b(
            phase_a_manifest_path=phase_a_manifest,
            live_open_path=_write_live_open(tmp_path, "2026-08-13", "2026-08-17", missing_symbol=required_symbol),
            account_state_path=tmp_path / "account.json",
        )


def test_phase_b_is_idempotent_and_conflict_checked(tmp_path: Path) -> None:
    run_phase_a(
        paths=_phase_a_paths(tmp_path),
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )
    phase_a_manifest = tmp_path / "artifacts/live/2026-08-13/phase_a_decision_manifest.json"
    live_open = _write_live_open(tmp_path, "2026-08-13", "2026-08-17")
    first = run_phase_b(
        phase_a_manifest_path=phase_a_manifest,
        live_open_path=live_open,
        account_state_path=tmp_path / "account.json",
    )
    second = run_phase_b(
        phase_a_manifest_path=phase_a_manifest,
        live_open_path=live_open,
        account_state_path=tmp_path / "account.json",
    )
    assert second["phase_b_ticket_sha256"] == first["phase_b_ticket_sha256"]

    rows = json.loads(live_open.read_text(encoding="utf-8"))
    rows[0]["open"] = rows[0]["open"] + 1.0
    live_open.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="Conflicting Phase-B ticket"):
        run_phase_b(
            phase_a_manifest_path=phase_a_manifest,
            live_open_path=live_open,
            account_state_path=tmp_path / "account.json",
        )
