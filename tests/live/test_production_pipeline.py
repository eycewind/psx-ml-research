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


def _write_account(repo: Path, *, deployable_capital: float | None = 100_000.0) -> Path:
    path = repo / "account.json"
    payload = {"cash_pkr": 100_000, "positions": {}}
    if deployable_capital is not None:
        payload["deployable_capital_pkr"] = deployable_capital
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_account_state(
    repo: Path,
    *,
    cash: float,
    positions: dict[str, int],
    deployable_capital: float | None = 50_000.0,
) -> Path:
    path = repo / "account.json"
    payload = {"cash_pkr": cash, "positions": positions}
    if deployable_capital is not None:
        payload["deployable_capital_pkr"] = deployable_capital
    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
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
    con.execute(
        "CREATE TABLE c17_eod_symbol_exclusions ("
        "signal_date TEXT, symbol TEXT, reason TEXT, recorded_at TEXT)"
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


def _insert_eod_exclusion(
    source_db: Path,
    *,
    signal_date: str,
    symbol: str | None,
    reason: str | None = "malformed official EOD bar: open NULL/high-low zero/volume 2",
) -> None:
    con = sqlite3.connect(source_db)
    con.execute(
        "INSERT INTO c17_eod_symbol_exclusions "
        "(signal_date, symbol, reason, recorded_at) VALUES (?, ?, ?, ?)",
        (signal_date, symbol, reason, f"{signal_date}T18:00:00+05:00"),
    )
    con.commit()
    con.close()


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


def _write_actual_holdings_acceptance_phase_a(repo: Path) -> Path:
    signal_date = "2026-08-18"
    execution_date = "2026-08-19"
    live_dir = repo / f"artifacts/live/{signal_date}"
    live_dir.mkdir(parents=True, exist_ok=True)

    opening_cash = 3_200.0
    deployable_capital = 50_000.0
    positions = {
        "APL": 4,
        "ICL": 17,
        "IMAGE": 92,
        "KSBP": 10,
        "LCI": 11,
        "MARI": 9,
        "MTL": 22,
        "OCTOPUS": 79,
        "SGF": 21,
        "SSOM": 5,
        "WAFI": 13,
    }
    _write_account_state(
        repo,
        cash=opening_cash,
        positions=positions,
        deployable_capital=deployable_capital,
    )
    open_price = 100.0

    def weight_for(target_shares: int) -> float:
        return ((target_shares + 0.001) * open_price) / deployable_capital

    signal_plan = pd.DataFrame(
        {
            "allocation_id": [PRIMARY_ALLOCATION_ID] * 5,
            "trade_date": pd.to_datetime([signal_date] * 5),
            "symbol": ["APL", "ICL", "IMAGE", "LCI", "NEWC"],
            "target_weight": [
                weight_for(4),
                weight_for(20),
                weight_for(50),
                weight_for(11),
                weight_for(5),
            ],
            "signal_close": [100.0] * 5,
            "buy_limit_price": [102.0] * 5,
            "shariah_eligible": [True] * 5,
        }
    )
    signal_plan_path = live_dir / "signal_plan.parquet"
    signal_plan.to_parquet(signal_plan_path, index=False)

    selected = set(signal_plan["symbol"])
    live_open = [
        {
            "trade_date": execution_date,
            "symbol": symbol,
            "open": open_price,
            "first_qualifying_poll_ts": f"{execution_date}T09:40:30+05:00",
            "confirmed_poll_ts": f"{execution_date}T09:42:00+05:00",
            "confirmation_count": 2,
            "source": "psx_portal",
        }
        for symbol in sorted(set(positions) | selected)
    ]
    (repo / "settled_live_open.json").write_text(
        json.dumps(live_open, indent=2),
        encoding="utf-8",
    )

    phase_a_manifest = {
        "manifest_version": 1,
        "artifact_kind": "c17_phase_a_decision",
        "allocation_id": PRIMARY_ALLOCATION_ID,
        "signal_date": signal_date,
        "execution_date": execution_date,
        "phase_a_decision_sha256": "actual-holdings-acceptance-fixture",
        "outputs": {
            "signal_plan": {
                "path": str(signal_plan_path.resolve()),
                "rows": int(len(signal_plan)),
                "sha256": "fixture",
            },
        },
    }
    phase_a_manifest_path = live_dir / "phase_a_decision_manifest.json"
    phase_a_manifest_path.write_text(
        json.dumps(phase_a_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return phase_a_manifest_path


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


def test_phase_a_eod_exclusion_removes_symbol_before_selection_and_signal_plan(tmp_path: Path) -> None:
    paths = _phase_a_paths(tmp_path)
    _insert_eod_exclusion(paths.source_db, signal_date="2026-08-13", symbol="AAA")

    manifest = run_phase_a(
        paths=paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )

    live_dir = tmp_path / "artifacts/live/2026-08-13"
    predictions = pd.read_parquet(live_dir / "predictions.parquet")
    features = pd.read_parquet(live_dir / "features.parquet")
    selections = pd.read_parquet(live_dir / "selections.parquet")
    signal_plan = pd.read_parquet(live_dir / "signal_plan.parquet")

    assert "AAA" not in set(predictions["symbol"])
    assert "AAA" not in set(features["symbol"])
    assert "AAA" not in set(selections["symbol"])
    assert "AAA" not in set(signal_plan["symbol"])
    assert "AAA" not in set(selections.loc[selections["policy_id"].eq("D_P4_kmi30_strict"), "symbol"])
    assert "AAA" not in set(selections.loc[selections["policy_id"].eq("D_P5_shariah_screened"), "symbol"])
    assert manifest["eod_symbol_exclusions"]["excluded_symbol_count"] == 1
    assert manifest["eod_symbol_exclusions"]["symbols"] == [
        {
            "symbol": "AAA",
            "reason": "malformed official EOD bar: open NULL/high-low zero/volume 2",
        }
    ]


def test_phase_a_eod_exclusions_are_exact_signal_date_scoped(tmp_path: Path) -> None:
    paths = _phase_a_paths(tmp_path)
    _insert_eod_exclusion(paths.source_db, signal_date="2026-08-12", symbol="AAA")
    _insert_eod_exclusion(paths.source_db, signal_date="2026-08-14", symbol="BBB")

    manifest = run_phase_a(
        paths=paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )

    selections = pd.read_parquet(tmp_path / "artifacts/live/2026-08-13/selections.parquet")
    signal_plan = pd.read_parquet(tmp_path / "artifacts/live/2026-08-13/signal_plan.parquet")
    assert manifest["eod_symbol_exclusions"]["excluded_symbol_count"] == 0
    assert "AAA" in set(selections["symbol"])
    assert "AAA" in set(signal_plan["symbol"])


def test_phase_a_no_exclusion_case_preserves_existing_selection_output(tmp_path: Path) -> None:
    baseline_paths = _phase_a_paths(tmp_path / "baseline")
    excluded_paths = _phase_a_paths(tmp_path / "excluded")
    _insert_eod_exclusion(excluded_paths.source_db, signal_date="2026-08-12", symbol="AAA")

    baseline = run_phase_a(
        paths=baseline_paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )
    scoped = run_phase_a(
        paths=excluded_paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )

    pd.testing.assert_frame_equal(
        pd.read_parquet(tmp_path / "baseline/artifacts/live/2026-08-13/selections.parquet"),
        pd.read_parquet(tmp_path / "excluded/artifacts/live/2026-08-13/selections.parquet"),
    )
    pd.testing.assert_frame_equal(
        pd.read_parquet(tmp_path / "baseline/artifacts/live/2026-08-13/signal_plan.parquet"),
        pd.read_parquet(tmp_path / "excluded/artifacts/live/2026-08-13/signal_plan.parquet"),
    )
    assert baseline["eod_symbol_exclusions"]["symbols"] == []
    assert scoped["eod_symbol_exclusions"]["symbols"] == []


def test_phase_a_decision_hash_changes_when_eod_exclusion_set_changes(tmp_path: Path) -> None:
    baseline_paths = _phase_a_paths(tmp_path / "baseline")
    excluded_paths = _phase_a_paths(tmp_path / "excluded")
    _insert_eod_exclusion(excluded_paths.source_db, signal_date="2026-08-13", symbol="AAA")

    baseline = run_phase_a(
        paths=baseline_paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )
    excluded = run_phase_a(
        paths=excluded_paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )

    assert excluded["phase_a_decision_sha256"] != baseline["phase_a_decision_sha256"]


def test_phase_a_rejects_malformed_and_conflicting_eod_exclusion_metadata(tmp_path: Path) -> None:
    paths = _phase_a_paths(tmp_path / "blank")
    _insert_eod_exclusion(paths.source_db, signal_date="2026-08-13", symbol="AAA", reason="")
    with pytest.raises(ValueError, match="Malformed EOD symbol exclusion row"):
        run_phase_a(
            paths=paths,
            signal_date="2026-08-13",
            execution_date="2026-08-17",
            scorer=_fake_scorer,
        )

    conflict_paths = _phase_a_paths(tmp_path / "conflict")
    _insert_eod_exclusion(conflict_paths.source_db, signal_date="2026-08-13", symbol="AAA", reason="first")
    _insert_eod_exclusion(conflict_paths.source_db, signal_date="2026-08-13", symbol="AAA", reason="second")
    with pytest.raises(ValueError, match="Conflicting EOD exclusion reasons"):
        run_phase_a(
            paths=conflict_paths,
            signal_date="2026-08-13",
            execution_date="2026-08-17",
            scorer=_fake_scorer,
        )


def test_phase_a_allows_duplicate_identical_eod_exclusions(tmp_path: Path) -> None:
    paths = _phase_a_paths(tmp_path)
    _insert_eod_exclusion(paths.source_db, signal_date="2026-08-13", symbol="AAA", reason="same")
    _insert_eod_exclusion(paths.source_db, signal_date="2026-08-13", symbol="AAA", reason="same")

    manifest = run_phase_a(
        paths=paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )

    assert manifest["eod_symbol_exclusions"]["symbols"] == [{"symbol": "AAA", "reason": "same"}]


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
    assert manifest["strategy_capital"]["deployable_capital_pkr"] == 100_000.0
    assert manifest["strategy_capital"]["source"] == "manual_account_state.deployable_capital_pkr"
    assert "deployable_capital_pkr" in manifest["account_state_schema"]
    assert manifest["outputs"]["order_ticket_json"]["top_level_type"] == "list"
    assert set(parquet["allocation_id"]) == {PRIMARY_ALLOCATION_ID}


def test_phase_b_requires_explicit_deployable_capital(tmp_path: Path) -> None:
    run_phase_a(
        paths=_phase_a_paths(tmp_path),
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )
    _write_account(tmp_path, deployable_capital=None)
    with pytest.raises(ValueError, match="deployable_capital_pkr is required"):
        run_phase_b(
            phase_a_manifest_path=tmp_path / "artifacts/live/2026-08-13/phase_a_decision_manifest.json",
            live_open_path=_write_live_open(tmp_path, "2026-08-13", "2026-08-17"),
            account_state_path=tmp_path / "account.json",
        )


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


def test_phase_a_keeps_owned_symbol_eligible_for_scoring_and_selection(tmp_path: Path) -> None:
    paths = _phase_a_paths(tmp_path)
    _write_account_state(tmp_path, cash=100_000.0, positions={"AAA": 10})

    run_phase_a(
        paths=paths,
        signal_date="2026-08-13",
        execution_date="2026-08-17",
        scorer=_fake_scorer,
    )

    predictions = pd.read_parquet(tmp_path / "artifacts/live/2026-08-13/predictions.parquet")
    selections = pd.read_parquet(tmp_path / "artifacts/live/2026-08-13/selections.parquet")
    assert "AAA" in set(predictions["symbol"])
    assert "AAA" in set(selections["symbol"])


def test_phase_b_rebalances_against_actual_2026_08_19_holdings(tmp_path: Path) -> None:
    phase_a_manifest = _write_actual_holdings_acceptance_phase_a(tmp_path)
    manifest = run_phase_b(
        phase_a_manifest_path=phase_a_manifest,
        live_open_path=tmp_path / "settled_live_open.json",
        account_state_path=tmp_path / "account.json",
    )
    ticket = pd.read_parquet(tmp_path / "artifacts/live/2026-08-18/order_ticket_2026-08-19.parquet")
    rows = {row.symbol: row for row in ticket.itertuples(index=False)}

    assert manifest["outputs"]["order_ticket_json"]["top_level_type"] == "list"
    assert "APL" not in rows
    assert "LCI" not in rows
    assert "HOLD" not in set(ticket["order_side"])

    icl = rows["ICL"]
    assert icl.current_shares == 17
    assert icl.target_shares == 20
    assert icl.order_side == "BUY"
    assert icl.order_shares == 3

    image = rows["IMAGE"]
    assert image.current_shares == 92
    assert image.target_shares == 50
    assert image.order_side == "SELL"
    assert image.order_shares == 42

    ksbp = rows["KSBP"]
    assert ksbp.current_shares == 10
    assert ksbp.target_shares == 0
    assert ksbp.order_side == "SELL"
    assert ksbp.order_shares == 10

    newc = rows["NEWC"]
    assert newc.current_shares == 0
    assert newc.target_shares == 5
    assert newc.order_side == "BUY"
    assert newc.order_shares == 5

    assert rows["ICL"].target_shares == 20
    assert rows["NEWC"].target_shares == 5
