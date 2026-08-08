from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import hashlib
import json
import tomllib
from typing import Iterable

import pandas as pd

from psx_ml.c9.agreement import intersection_union
from psx_ml.c9.pipeline import _filter_schedule, _policy, _turnover_ranks
from psx_ml.c9.policies import apply_liquidity, percentile_ranks, sector_constraint, select
from psx_ml.c11.shariah_gate import normalize_screening_history


P1 = "P1_broad_canonical"
P2 = "P2_conservative_consensus"

D_P1_FILTER = "D_P1_shariah_filter"
D_P1_REFILL = "D_P1_shariah_refill"
D_P2_FILTER = "D_P2_shariah_filter"
D_P2_REFILL = "D_P2_shariah_refill"
D_P4 = "D_P4_kmi30_strict"
D_P5 = "D_P5_shariah_screened"

DEPLOYMENT_POLICIES = (
    D_P1_FILTER,
    D_P1_REFILL,
    D_P2_FILTER,
    D_P2_REFILL,
    D_P4,
    D_P5,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_c9_config(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _read_parquet_rows_direct(
    path: Path,
    *,
    columns: list[str] | None = None,
    filters: list[tuple[str, str, object]] | None = None,
) -> list[dict]:
    """Read Parquet without PyArrow Dataset/LocalFileSystem registration.

    Use Arrow tables all the way through filtering and finish with
    ``Table.to_pylist()``. This deliberately mirrors C9's original
    ``pq.read_table(...).to_pylist()`` scalar/null semantics.

    In particular, converting through pandas is unsafe here because Arrow nulls
    in fields such as ``sector`` can become ``NaN``. C9's sector constraint
    treats ``None`` as missing, while ``bool(float('nan'))`` is True; that can
    alter the selected names even when predictions are identical.
    """
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    requested = list(columns) if columns is not None else None
    filter_columns = [f[0] for f in (filters or [])]
    read_columns = None
    if requested is not None:
        read_columns = list(dict.fromkeys(requested + filter_columns))

    rows: list[dict] = []
    with path.open("rb") as handle:
        parquet = pq.ParquetFile(handle)
        for row_group in range(parquet.num_row_groups):
            table = parquet.read_row_group(
                row_group,
                columns=read_columns,
            )

            mask = None
            for column, operator, value in filters or []:
                if operator != "=":
                    raise ValueError(
                        "CP4A direct reader supports '=' filters only, "
                        f"got {operator!r}"
                    )
                current = pc.equal(table[column], pa.scalar(value))
                current = pc.fill_null(current, False)
                mask = current if mask is None else pc.and_(mask, current)

            if mask is not None:
                table = table.filter(mask)

            if table.num_rows == 0:
                continue

            if requested is not None:
                table = table.select(requested)

            rows.extend(table.to_pylist())

    return rows


def _prepare_c9_rows_direct(paths: dict[str, Path], manifest: dict) -> list[dict]:
    """Reproduce C9 ``_prepare`` while avoiding ``pq.read_table`` Dataset IO."""
    rank = _read_parquet_rows_direct(
        paths["c8_rank_predictions_path"],
        filters=[("task_type", "=", "rank")],
    )

    reference_path = (
        Path(paths["c8_rank_predictions_path"]).parents[2]
        / "c9/reference_rank_predictions.parquet"
    )
    if reference_path.exists():
        rank += _read_parquet_rows_direct(reference_path)

    features = {
        (r["trade_date"], r["symbol"]): r
        for r in _read_parquet_rows_direct(
            paths["feature_targets_path"],
            columns=[
                "trade_date",
                "symbol",
                "turnover_median_20obs_adj",
                "turnover_rank_adj",
                "ret_20obs_rank_adj",
            ],
        )
    }

    relative = {
        (r["trade_date"], r["symbol"]): r
        for r in _read_parquet_rows_direct(
            paths["relative_targets_path"],
            columns=["trade_date", "symbol", "sector"],
        )
    }

    reg = _read_parquet_rows_direct(
        paths["c8_regression_predictions_path"],
        filters=[
            ("horizon", "=", 5),
            ("target_family", "=", "market_relative"),
            ("feature_variant", "=", "B_market_context"),
            ("model_name", "=", "lightgbm_cpu"),
            ("comparison_subset_natural", "=", True),
        ],
    )

    regmap = {
        (r["fold_id"], r["trade_date"], r["symbol"]): r
        for r in reg
    }
    turnover = _turnover_ranks(features.values())
    provenance = manifest["supplemental_evaluation"]["generation_code"]["commit"]

    out: list[dict] = []
    for r in rank:
        key = (r["trade_date"], r["symbol"])
        f = features.get(key, {})
        q = relative.get(key, {})
        g = regmap.get((r["fold_id"], *key), {})
        out.append(
            {
                "trade_date": r["trade_date"],
                "symbol": r["symbol"],
                "fold_id": r["fold_id"],
                "horizon": r["horizon"],
                "target_family": "market_relative_rank",
                "feature_variant": r["feature_variant"],
                "model_name": r["model_name"],
                "prediction": r["prediction"],
                "actual_rank_target": r["target"],
                "actual_market_relative_return": r["outcome"],
                "sector": q.get("sector"),
                "turnover_median_20obs_adj": f.get(
                    "turnover_median_20obs_adj"
                ),
                "turnover_percentile_rank": turnover.get(key),
                "momentum_rank": f.get("ret_20obs_rank_adj"),
                "liquidity_rank": f.get("turnover_rank_adj"),
                "market_trend_regime": g.get("market_trend_regime"),
                "market_volatility_regime": g.get(
                    "market_volatility_regime"
                ),
                "market_breadth_regime": g.get("market_breadth_regime"),
                "market_dispersion_regime": g.get(
                    "market_dispersion_regime"
                ),
                "prediction_provenance": provenance,
            }
        )

    return out


def c9_input_paths(repo: Path, config_path: Path) -> tuple[dict[str, Path], dict]:
    cfg = load_c9_config(config_path)
    paths = {
        key: (repo / value).resolve()
        for key, value in cfg["input"].items()
    }
    manifest_path = repo / "artifacts/reports/C9_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    frozen = manifest["input_provenance"]["hashes"]
    for key, path in paths.items():
        expected = frozen.get(key)
        if expected is None:
            continue
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(
                f"C9 input hash mismatch for {key}: expected {expected}, got {actual}"
            )

    return paths, manifest


def build_c9_ranked_universes(
    *,
    repo: Path,
    config_path: Path,
) -> tuple[list[dict], list[dict], dict]:
    paths, c9_manifest = c9_input_paths(repo, config_path)
    c8_manifest = json.loads(paths["c8_manifest_path"].read_text(encoding="utf-8"))

    rows = _prepare_c9_rows_direct(paths, c8_manifest)
    canonical = [
        r
        for r in rows
        if int(r["horizon"]) == 5
        and r["feature_variant"] == "B_market_context"
        and r["model_name"] in {"lightgbm_cpu", "xgboost_gpu"}
        and str(r["trade_date"]) < "2026-01-01"
    ]

    ranked: list[dict] = []
    for key in sorted(
        {(r["model_name"], r["fold_id"]) for r in canonical}
    ):
        model, fold = key
        ranked += percentile_ranks(
            [
                r
                for r in canonical
                if r["model_name"] == model and r["fold_id"] == fold
            ]
        )

    lgb = [r for r in ranked if r["model_name"] == "lightgbm_cpu"]
    xgb = [r for r in ranked if r["model_name"] == "xgboost_gpu"]

    if not lgb or not xgb:
        raise RuntimeError("Accepted C9 canonical ranked universes are empty")

    return lgb, xgb, c9_manifest


def reconstruct_p1_p2(
    lgb: list[dict],
    xgb: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    p1, _, _ = _policy(
        lgb,
        "percentile",
        0.10,
        "weekly_first_session",
        "L0",
        "S1",
    )

    lt = select(
        _filter_schedule(
            apply_liquidity(lgb, "L1"),
            "weekly_first_session",
        ),
        "percentile",
        0.10,
    )
    xt = select(
        _filter_schedule(
            apply_liquidity(xgb, "L1"),
            "weekly_first_session",
        ),
        "percentile",
        0.10,
    )
    consensus, _ = intersection_union(lt, xt)
    p2, _ = sector_constraint(consensus, "S1")
    return p1, p2, consensus


def assert_exact_reconstruction(
    reconstructed: Iterable[dict],
    accepted: pd.DataFrame,
    *,
    policy_id: str,
) -> None:
    accepted_part = accepted.loc[
        accepted["policy_id"].astype(str) == policy_id
    ].copy()
    if accepted_part.empty:
        raise RuntimeError(f"Accepted C9 artifact contains no {policy_id}")

    left = pd.DataFrame(list(reconstructed)).copy()
    if left.empty:
        raise RuntimeError(f"Reconstruction produced no {policy_id}")

    left["trade_date"] = pd.to_datetime(left["trade_date"]).dt.normalize()
    accepted_part["trade_date"] = pd.to_datetime(
        accepted_part["trade_date"]
    ).dt.normalize()
    left["symbol"] = left["symbol"].astype(str)
    accepted_part["symbol"] = accepted_part["symbol"].astype(str)

    key = ["trade_date", "symbol"]
    left_keys = set(map(tuple, left[key].itertuples(index=False, name=None)))
    accepted_keys = set(
        map(tuple, accepted_part[key].itertuples(index=False, name=None))
    )
    if left_keys != accepted_keys:
        missing = sorted(accepted_keys - left_keys)[:20]
        extra = sorted(left_keys - accepted_keys)[:20]
        raise RuntimeError(
            f"{policy_id} reconstruction key mismatch; "
            f"missing={missing}, extra={extra}"
        )

    if len(left) != len(accepted_part):
        raise RuntimeError(
            f"{policy_id} reconstruction row mismatch: "
            f"{len(left)} != {len(accepted_part)}"
        )


def _gate_lookup(
    history: pd.DataFrame,
    symbol: str,
    signal_date: object,
) -> dict:
    sym = str(symbol).strip().upper()
    date = pd.Timestamp(signal_date).normalize()

    rows = history.loc[
        (history["symbol"] == sym)
        & (history["effective_from"] <= date)
        & (
            history["effective_to"].isna()
            | (date < history["effective_to"])
        )
    ]
    if len(rows) > 1:
        raise RuntimeError(
            f"Multiple PIT Shariah records for {sym} on {date.date()}"
        )

    if rows.empty:
        return {
            "shariah_eligible": False,
            "gate_status": "rejected_unknown",
            "shariah_source": None,
            "shariah_confidence": None,
            "screening_snapshot_date": None,
            "screening_effective_from": None,
            "screening_effective_to": None,
            "low_confidence_flag": False,
            "gate_reason": "no_point_in_time_shariah_record",
        }

    row = rows.iloc[0]
    eligible = bool(row["is_shariah_screened_eligible"])
    confidence = str(row["membership_confidence"])
    low = eligible and confidence == "low"

    def iso(value: object) -> str | None:
        if pd.isna(value):
            return None
        return pd.Timestamp(value).date().isoformat()

    return {
        "shariah_eligible": eligible,
        "gate_status": (
            "eligible_flagged_low_confidence"
            if low
            else "eligible"
            if eligible
            else "rejected_non_compliant"
        ),
        "shariah_source": str(row["membership_source"]),
        "shariah_confidence": confidence,
        "screening_snapshot_date": iso(row["screening_snapshot_date"]),
        "screening_effective_from": iso(row["effective_from"]),
        "screening_effective_to": iso(row["effective_to"]),
        "low_confidence_flag": low,
        "gate_reason": (
            "point_in_time_shariah_eligible_low_confidence"
            if low
            else "point_in_time_shariah_eligible"
            if eligible
            else "point_in_time_shariah_ineligible"
        ),
    }


def attach_gate(
    rows: pd.DataFrame,
    history: pd.DataFrame,
) -> pd.DataFrame:
    if rows.empty:
        return rows.copy()

    work = rows.copy()
    work["trade_date"] = pd.to_datetime(work["trade_date"]).dt.normalize()
    work["symbol"] = work["symbol"].astype(str).str.strip().str.upper()

    decisions = [
        _gate_lookup(history, symbol, date)
        for symbol, date in zip(work["symbol"], work["trade_date"])
    ]

    # Upstream artifacts such as P5 already carry Shariah provenance.
    # CP4A re-resolves PIT eligibility, so overwrite those fields instead of
    # creating duplicate column names.
    work = work.reset_index(drop=True)
    decision_frame = pd.DataFrame(decisions)
    for column in decision_frame.columns:
        work[column] = decision_frame[column].to_numpy()

    return work


def _sector_capped_scan(
    candidates: pd.DataFrame,
    *,
    target_count: int,
    sector_cap: int = 2,
) -> pd.DataFrame:
    if target_count <= 0 or candidates.empty:
        return candidates.iloc[0:0].copy()

    ordered = candidates.sort_values(
        ["prediction_percentile_rank", "symbol"],
        ascending=[False, True],
        kind="mergesort",
    )

    selected = []
    sector_counts: dict[str, int] = defaultdict(int)
    for index, row in ordered.iterrows():
        sector = str(row.get("sector", "")).strip()
        if not sector:
            continue
        if sector_counts[sector] >= sector_cap:
            continue
        selected.append(index)
        sector_counts[sector] += 1
        if len(selected) >= target_count:
            break

    result = ordered.loc[selected].copy()
    result["deployment_selection_rank"] = range(1, len(result) + 1)
    return result


def build_filter_only(
    accepted_rows: pd.DataFrame,
    history: pd.DataFrame,
    *,
    upstream_policy_id: str,
    deployment_policy_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = accepted_rows.loc[
        accepted_rows["policy_id"].astype(str) == upstream_policy_id
    ].copy()
    gated = attach_gate(source, history)

    audit = gated.copy()
    audit["deployment_policy_id"] = deployment_policy_id
    audit["deployment_variant"] = "filter_only"
    audit["originally_selected"] = True
    audit["refill_candidate"] = False
    audit["deployment_action"] = gated["shariah_eligible"].map(
        {True: "retain", False: "reject"}
    )

    selected = gated.loc[gated["shariah_eligible"]].copy()
    selected["upstream_policy_id"] = upstream_policy_id
    selected["deployment_policy_id"] = deployment_policy_id
    selected["policy_id"] = deployment_policy_id
    selected["deployment_variant"] = "filter_only"
    selected["originally_selected"] = True
    selected["refill_candidate"] = False

    selected = selected.sort_values(
        ["trade_date", "prediction_percentile_rank", "symbol"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    selected["deployment_selection_rank"] = (
        selected.groupby("trade_date").cumcount() + 1
    )
    return selected.reset_index(drop=True), audit.reset_index(drop=True)


def build_p1_refill(
    *,
    lgb: list[dict],
    accepted_p1: pd.DataFrame,
    history: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    accepted = accepted_p1.copy()
    accepted["trade_date"] = pd.to_datetime(accepted["trade_date"]).dt.normalize()
    accepted_keys = set(
        zip(accepted["trade_date"], accepted["symbol"].astype(str))
    )
    target_counts = accepted.groupby("trade_date").size().to_dict()
    dates = set(target_counts)

    universe = pd.DataFrame(
        [
            r
            for r in lgb
            if pd.Timestamp(r["trade_date"]).normalize() in dates
        ]
    )
    universe["trade_date"] = pd.to_datetime(
        universe["trade_date"]
    ).dt.normalize()
    universe = attach_gate(universe, history)
    universe["originally_selected"] = [
        (d, str(s)) in accepted_keys
        for d, s in zip(universe["trade_date"], universe["symbol"])
    ]

    selected_chunks = []
    audit_chunks = []
    for date, group in universe.groupby("trade_date", sort=True):
        target = int(target_counts[date])
        eligible = group.loc[group["shariah_eligible"]].copy()
        chosen = _sector_capped_scan(
            eligible,
            target_count=target,
            sector_cap=2,
        )
        chosen["deployment_target_count"] = target
        chosen["deployment_shortfall"] = target - len(chosen)
        chosen["refill_candidate"] = ~chosen["originally_selected"].astype(bool)
        selected_chunks.append(chosen)

        audit = group.copy()
        chosen_keys = set(chosen["symbol"].astype(str))
        audit["deployment_action"] = [
            "retain_or_refill" if s in chosen_keys else
            "reject_shariah" if not eligible_flag else
            "not_needed_or_sector_capped"
            for s, eligible_flag in zip(
                audit["symbol"].astype(str),
                audit["shariah_eligible"].astype(bool),
            )
        ]
        audit["deployment_target_count"] = target
        audit_chunks.append(audit)

    selected = pd.concat(selected_chunks, ignore_index=True)
    selected["upstream_policy_id"] = P1
    selected["deployment_policy_id"] = D_P1_REFILL
    selected["policy_id"] = D_P1_REFILL
    selected["deployment_variant"] = "filter_and_refill"

    audit = pd.concat(audit_chunks, ignore_index=True)
    audit["deployment_policy_id"] = D_P1_REFILL
    audit["deployment_variant"] = "filter_and_refill"
    audit["refill_candidate"] = ~audit["originally_selected"].astype(bool)

    return selected, audit


def build_p2_refill(
    *,
    consensus: list[dict],
    accepted_p2: pd.DataFrame,
    history: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    accepted = accepted_p2.copy()
    accepted["trade_date"] = pd.to_datetime(accepted["trade_date"]).dt.normalize()
    accepted_keys = set(
        zip(accepted["trade_date"], accepted["symbol"].astype(str))
    )
    target_counts = accepted.groupby("trade_date").size().to_dict()

    pool = pd.DataFrame(consensus)
    pool["trade_date"] = pd.to_datetime(pool["trade_date"]).dt.normalize()
    pool = pool.loc[pool["trade_date"].isin(target_counts)].copy()
    pool = attach_gate(pool, history)
    pool["originally_selected"] = [
        (d, str(s)) in accepted_keys
        for d, s in zip(pool["trade_date"], pool["symbol"])
    ]

    selected_chunks = []
    audit_chunks = []
    for date, group in pool.groupby("trade_date", sort=True):
        target = int(target_counts[date])
        eligible = group.loc[group["shariah_eligible"]].copy()
        chosen = _sector_capped_scan(
            eligible,
            target_count=target,
            sector_cap=2,
        )
        chosen["deployment_target_count"] = target
        chosen["deployment_shortfall"] = target - len(chosen)
        chosen["refill_candidate"] = ~chosen["originally_selected"].astype(bool)
        chosen["refill_scope"] = "accepted_p2_top10_consensus_intersection"
        selected_chunks.append(chosen)

        chosen_keys = set(chosen["symbol"].astype(str))
        audit = group.copy()
        audit["deployment_action"] = [
            "retain_or_refill" if s in chosen_keys else
            "reject_shariah" if not eligible_flag else
            "not_needed_or_sector_capped"
            for s, eligible_flag in zip(
                audit["symbol"].astype(str),
                audit["shariah_eligible"].astype(bool),
            )
        ]
        audit["deployment_target_count"] = target
        audit["refill_scope"] = "accepted_p2_top10_consensus_intersection"
        audit_chunks.append(audit)

    selected = pd.concat(selected_chunks, ignore_index=True)
    selected["upstream_policy_id"] = P2
    selected["deployment_policy_id"] = D_P2_REFILL
    selected["policy_id"] = D_P2_REFILL
    selected["deployment_variant"] = "filter_and_refill"

    audit = pd.concat(audit_chunks, ignore_index=True)
    audit["deployment_policy_id"] = D_P2_REFILL
    audit["deployment_variant"] = "filter_and_refill"
    audit["refill_candidate"] = ~audit["originally_selected"].astype(bool)

    return selected, audit


def build_p4_authoritative_passthrough(
    source: pd.DataFrame,
    history: pd.DataFrame,
    *,
    upstream_policy_id: str = "P4_kmi30_strict",
    deployment_policy_id: str = D_P4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate P4 from its authoritative PIT KMI30 membership.

    KMI30 membership is itself the upstream Shariah eligibility basis for P4.
    The generic screened-universe history is retained as a secondary coverage
    diagnostic and must not veto a valid PIT KMI30 membership row merely
    because that separate history lacks the symbol/date.
    """
    work = source.copy()
    work["trade_date"] = pd.to_datetime(work["trade_date"]).dt.normalize()

    required = {
        "kmi30_member",
        "effective_from",
        "effective_to",
        "notice_date",
        "notice_no",
    }
    missing = sorted(required - set(work.columns))
    if missing:
        raise ValueError(f"P4 source missing authoritative provenance: {missing}")

    if not work["kmi30_member"].astype(bool).all():
        raise RuntimeError("P4 contains a row not marked as KMI30 member")

    effective_from = pd.to_datetime(
        work["effective_from"], errors="raise"
    ).dt.normalize()
    notice_date = pd.to_datetime(
        work["notice_date"], errors="raise"
    ).dt.normalize()

    # effective_to can deliberately contain 9999-12-31, which pandas cannot
    # represent at nanosecond resolution. Compare it as ISO YYYY-MM-DD text.
    effective_to_text = work["effective_to"].astype(str).str[:10]
    trade_text = work["trade_date"].dt.strftime("%Y-%m-%d")

    if (effective_from > work["trade_date"]).any():
        raise RuntimeError("P4 row precedes KMI30 effective_from")
    if (notice_date > work["trade_date"]).any():
        raise RuntimeError("P4 row precedes its official KMI30 notice")
    if (trade_text >= effective_to_text).any():
        raise RuntimeError("P4 row falls outside KMI30 effective_to")

    # Secondary diagnostic against the generic screened history.
    secondary = attach_gate(
        work[["trade_date", "symbol"]].copy(),
        history,
    )
    secondary = secondary.rename(
        columns={
            "shariah_eligible": "screen_history_eligible",
            "gate_status": "screen_history_gate_status",
            "shariah_source": "screen_history_source",
            "shariah_confidence": "screen_history_confidence",
            "screening_snapshot_date": "screen_history_snapshot_date",
            "screening_effective_from": "screen_history_effective_from",
            "screening_effective_to": "screen_history_effective_to",
            "low_confidence_flag": "screen_history_low_confidence_flag",
            "gate_reason": "screen_history_gate_reason",
        }
    )
    secondary = secondary.drop(columns=["trade_date", "symbol"])

    work = pd.concat(
        [work.reset_index(drop=True), secondary.reset_index(drop=True)],
        axis=1,
    )

    # Authoritative P4 deployment eligibility comes from PIT KMI30 membership.
    work["shariah_eligible"] = True
    work["gate_status"] = "eligible_authoritative_kmi30"
    work["shariah_source"] = "official_psx_kmi30_membership"
    work["shariah_confidence"] = "high"
    work["screening_snapshot_date"] = work["review_as_of"].astype(str).str[:10]
    work["screening_effective_from"] = work["effective_from"].astype(str).str[:10]
    work["screening_effective_to"] = work["effective_to"].astype(str).str[:10]
    work["low_confidence_flag"] = False
    work["gate_reason"] = "point_in_time_kmi30_membership"

    selected = work.copy()
    selected["upstream_policy_id"] = upstream_policy_id
    selected["deployment_policy_id"] = deployment_policy_id
    selected["policy_id"] = deployment_policy_id
    selected["deployment_variant"] = "authoritative_kmi30_passthrough"
    selected["originally_selected"] = True
    selected["refill_candidate"] = False
    selected = selected.sort_values(
        ["trade_date", "symbol"],
        kind="mergesort",
    ).reset_index(drop=True)
    selected["deployment_selection_rank"] = (
        selected.groupby("trade_date").cumcount() + 1
    )

    audit = work.copy()
    audit["deployment_policy_id"] = deployment_policy_id
    audit["deployment_variant"] = "authoritative_kmi30_passthrough"
    audit["originally_selected"] = True
    audit["refill_candidate"] = False
    audit["deployment_action"] = "retain"

    return selected, audit


def build_defensive_passthrough(
    source: pd.DataFrame,
    history: pd.DataFrame,
    *,
    upstream_policy_id: str,
    deployment_policy_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    gated = attach_gate(source, history)
    audit = gated.copy()
    audit["deployment_policy_id"] = deployment_policy_id
    audit["deployment_variant"] = "defensive_shariah_gate"
    audit["originally_selected"] = True
    audit["refill_candidate"] = False
    audit["deployment_action"] = gated["shariah_eligible"].map(
        {True: "retain", False: "reject"}
    )

    selected = gated.loc[gated["shariah_eligible"]].copy()
    selected["upstream_policy_id"] = upstream_policy_id
    selected["deployment_policy_id"] = deployment_policy_id
    selected["policy_id"] = deployment_policy_id
    selected["deployment_variant"] = "defensive_shariah_gate"
    selected["originally_selected"] = True
    selected["refill_candidate"] = False
    selected = selected.sort_values(
        ["trade_date", "symbol"],
        kind="mergesort",
    ).reset_index(drop=True)
    selected["deployment_selection_rank"] = (
        selected.groupby("trade_date").cumcount() + 1
    )
    return selected, audit
