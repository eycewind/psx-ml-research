from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c8.context_features import build_context_features
from psx_ml.data.sqlite import connect_readonly
from psx_ml.features.config import load_feature_config
from psx_ml.features.pipeline import compute_features
from psx_ml.universe.point_in_time import build_point_in_time

DEFAULT_MODEL = Path("artifacts/models/c8_supplemental/rank_5_B_market_context_fold_2025_lightgbm_cpu.txt")
DEFAULT_C8_MANIFEST = Path("artifacts/reports/C8_MANIFEST.json")
DEFAULT_C6_UNIVERSE = Path("data/processed/universe/c6_universe_membership.parquet")
DEFAULT_SECURITY_MASTER = Path("data/reference/psx_security_master_2026-08-01.parquet")
DEFAULT_FEATURE_CONFIG = Path("config/features.example.toml")
DEFAULT_OUTPUT_ROOT = Path("artifacts/live")
CANONICAL_UNIVERSE = "pit_liquid_ordinary_equity_v1"
EXPECTED_MODEL_SHA256 = "ecc95b9d78aa4dd26b30dbe4560eec716d4f21a8e190e59ea02b84a75d3643d5"
EXPECTED_TARGET = "fwd_market_relative_rank_5s"
EXPECTED_FEATURE_VARIANT = "B_market_context"
EXPECTED_MODEL_NAME = "lightgbm_cpu"
EXPECTED_HORIZON = 5

@dataclass(frozen=True)
class LiveScoringPaths:
    repo: Path
    source_db: Path
    model: Path
    c8_manifest: Path
    c6_universe: Path
    security_master: Path
    feature_config: Path
    output_root: Path

    @classmethod
    def from_args(cls, repo: Path, source_db: Path, model: Path | None = None,
                  c8_manifest: Path | None = None, c6_universe: Path | None = None,
                  security_master: Path | None = None, feature_config: Path | None = None,
                  output_root: Path | None = None):
        repo = repo.resolve()
        def rp(value, default):
            p = default if value is None else value
            return p.resolve() if p.is_absolute() else (repo / p).resolve()
        return cls(repo, source_db.resolve(), rp(model, DEFAULT_MODEL),
                   rp(c8_manifest, DEFAULT_C8_MANIFEST), rp(c6_universe, DEFAULT_C6_UNIVERSE),
                   rp(security_master, DEFAULT_SECURITY_MASTER), rp(feature_config, DEFAULT_FEATURE_CONFIG),
                   rp(output_root, DEFAULT_OUTPUT_ROOT))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _normalize_date(value) -> str:
    return pd.Timestamp(value).normalize().date().isoformat()

def latest_trade_date(con: sqlite3.Connection) -> str:
    row = con.execute("SELECT MAX(trade_date) FROM daily_ohlc").fetchone()
    if not row or row[0] is None:
        raise ValueError("daily_ohlc is empty")
    return str(row[0])

def _load_c8_feature_order(path: Path) -> list[str]:
    raw = json.loads(path.read_text())
    features = raw.get("feature_definitions", {}).get("variants", {}).get(EXPECTED_FEATURE_VARIANT)
    if not features:
        raise ValueError(f"{EXPECTED_FEATURE_VARIANT} not present in {path}")
    if len(features) != 56:
        raise ValueError(f"Expected 56 {EXPECTED_FEATURE_VARIANT} features, got {len(features)}")
    if len(set(features)) != len(features):
        raise ValueError("Duplicate feature names in frozen C8 manifest")
    return list(features)

def _verify_frozen_model(path: Path) -> str:
    actual = sha256_file(path)
    if actual != EXPECTED_MODEL_SHA256:
        raise ValueError(f"Frozen live-model SHA-256 mismatch: expected {EXPECTED_MODEL_SHA256}, actual {actual}, path {path}")
    return actual

def _query_daily(con: sqlite3.Connection, through_date: str) -> pa.Table:
    cols = ["trade_date","symbol","open_adj","high_adj","low_adj","close_adj","volume_adj"]
    sql = "SELECT " + ",".join(cols) + " FROM daily_ohlc WHERE trade_date <= ? ORDER BY trade_date,symbol"
    rows = [dict(r) for r in con.execute(sql, (through_date,))]
    if not rows:
        raise ValueError(f"No daily_ohlc rows through {through_date}")
    return pa.Table.from_pylist(rows)

def _build_c1_universe(con: sqlite3.Connection, through_date: str) -> pa.Table:
    rows = []
    for r in build_point_in_time(con, lookback_sessions=60, minimum_history_sessions=40,
                                 minimum_median_turnover_pkr=1_000_000, maximum_stale_fraction=0.20):
        if str(r["trade_date"]) <= through_date:
            rows.append({"trade_date": str(r["trade_date"]), "symbol": str(r["symbol"]), "eligible": bool(r["eligible"])})
    if not rows:
        raise ValueError("C1 PIT universe construction returned no rows")
    return pa.Table.from_pylist(rows)

def _load_security_master(path: Path) -> pd.DataFrame:
    sm = pd.read_parquet(path)
    required = {"symbol","sector","instrument_family"}
    missing = required - set(sm.columns)
    if missing:
        raise ValueError(f"Security master missing columns: {sorted(missing)}")
    sm = sm.copy()
    sm["symbol"] = sm["symbol"].astype(str).str.strip().str.upper()
    if sm["symbol"].duplicated().any():
        raise ValueError("Duplicate security-master symbols")
    return sm

def _load_frozen_c6(path: Path) -> pd.DataFrame:
    cols = ["trade_date","symbol","universe_name","eligible","instrument_type"]
    df = pd.read_parquet(path, columns=cols)
    df = df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.normalize()
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    return df

def _c3_frame(daily: pa.Table, c1_universe: pa.Table, feature_config: Path, repo: Path) -> pd.DataFrame:
    cfg = load_feature_config(feature_config, repo)
    table, _registry, _quality = compute_features(daily, c1_universe, cfg)
    out = table.to_pandas()
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.normalize()
    out["symbol"] = out["symbol"].astype(str).str.strip().str.upper()
    return out

def _eligible_c8_rows(c3: pd.DataFrame, c1_universe: pa.Table, c6_path: Path,
                      security_master_path: Path, through_date: str):
    through = pd.Timestamp(through_date).normalize()
    c6 = _load_frozen_c6(c6_path)
    sm = _load_security_master(security_master_path)
    sector_map = sm.set_index("symbol")["sector"].to_dict()
    ordinary = set(sm.loc[sm["instrument_family"].astype(str) == "ordinary_equity", "symbol"])
    c6_primary = c6.loc[(c6["universe_name"].astype(str) == CANONICAL_UNIVERSE)
                        & c6["eligible"].astype(bool)
                        & (c6["instrument_type"].astype(str) == "ordinary_equity")].copy()
    frozen_max = c6["trade_date"].max()
    frozen_keys = set(zip(c6_primary["trade_date"].dt.strftime("%Y-%m-%d"), c6_primary["symbol"]))
    u = c1_universe.to_pandas()
    u["trade_date"] = pd.to_datetime(u["trade_date"]).dt.normalize()
    u["symbol"] = u["symbol"].astype(str).str.strip().str.upper()
    eu = u.loc[u["eligible"].astype(bool)]
    live_keys = set(zip(eu["trade_date"].dt.strftime("%Y-%m-%d"), eu["symbol"]))
    work = c3.loc[c3["trade_date"] <= through].copy()
    keep, provenance = [], []
    for row in work[["trade_date","symbol"]].itertuples(index=False):
        ds = row.trade_date.date().isoformat(); s = row.symbol
        if row.trade_date <= frozen_max:
            ok = (ds, s) in frozen_keys; src = "frozen_c6"
        else:
            ok = (ds, s) in live_keys and s in ordinary; src = "c1_plus_security_master"
        keep.append(ok); provenance.append(src)
    keep = np.asarray(keep, dtype=bool)
    work = work.loc[keep].copy()
    work["universe_provenance"] = np.asarray(provenance, dtype=object)[keep]
    work["sector"] = work["symbol"].map(sector_map)
    if work.empty:
        raise ValueError(f"No eligible ordinary-equity rows through {through_date}")
    source_label = "frozen_c6_only" if through <= frozen_max else f"frozen_c6_through_{frozen_max.date().isoformat()}_then_live_extension"
    return work, source_label

def _build_b_market_context(eligible_rows: pd.DataFrame, feature_order: list[str]) -> pd.DataFrame:
    rows_df = eligible_rows.sort_values(["trade_date","symbol"], kind="mergesort").reset_index(drop=True)
    rows = rows_df.to_dict("records")
    context = build_context_features(rows, minimum_sector_peers=5, rolling_window=60, minimum_rolling=30)
    # Match C8 feature-variant precedence exactly:
    # B_market_context = dict.fromkeys(c7 + market + market_relative).
    # If a C8 context feature duplicates an existing C3/C7 feature,
    # the C3/C7 value must win.
    for name, values in context.items():
        if name not in rows_df.columns:
            rows_df[name] = values
    missing = [f for f in feature_order if f not in rows_df.columns]
    if missing:
        raise ValueError(f"Live feature builder missing frozen features: {missing}")
    out = rows_df[["trade_date","symbol","sector","universe_provenance"] + feature_order].copy()
    for f in feature_order:
        out[f] = pd.to_numeric(out[f], errors="coerce")
    return out

def _score_latest(feature_frame: pd.DataFrame, feature_order: list[str], model_path: Path, score_date: str) -> pd.DataFrame:
    day = pd.Timestamp(score_date).normalize()
    latest = feature_frame.loc[feature_frame["trade_date"] == day].copy()
    if latest.empty:
        raise ValueError(f"No eligible live feature rows for requested date {score_date}")
    x = latest[feature_order].to_numpy(dtype=float)
    booster = lgb.Booster(model_file=str(model_path))
    if booster.num_feature() != len(feature_order):
        raise ValueError(f"Model expects {booster.num_feature()} features; frozen manifest defines {len(feature_order)}")
    latest["prediction"] = np.asarray(booster.predict(x), dtype=float)
    latest["horizon"] = EXPECTED_HORIZON
    latest["target_name"] = EXPECTED_TARGET
    latest["target_family"] = "market_relative_rank"
    latest["feature_variant"] = EXPECTED_FEATURE_VARIANT
    latest["model_name"] = EXPECTED_MODEL_NAME
    latest["model_fold"] = "fold_2025"
    cols = ["trade_date","symbol","sector","prediction","horizon","target_name","target_family","feature_variant","model_name","model_fold","universe_provenance"]
    return latest[cols].sort_values(["prediction","symbol"], ascending=[False,True], kind="mergesort").reset_index(drop=True)

def _write_outputs(paths, score_date, feature_frame, predictions, feature_order, model_sha, universe_provenance):
    out_dir = paths.output_root / score_date
    out_dir.mkdir(parents=True, exist_ok=True)
    features_path = out_dir / "features.parquet"
    predictions_path = out_dir / "predictions.parquet"
    manifest_path = out_dir / "scoring_manifest.json"
    day = pd.Timestamp(score_date).normalize()
    latest_features = feature_frame.loc[feature_frame["trade_date"] == day,
        ["trade_date","symbol","sector","universe_provenance"] + feature_order].copy()
    latest_features.to_parquet(features_path, index=False)
    predictions.to_parquet(predictions_path, index=False)
    finite_counts = {f: int(pd.to_numeric(latest_features[f], errors="coerce").notna().sum()) for f in feature_order}
    manifest = {
        "manifest_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "score_date": score_date,
        "source_db": str(paths.source_db),
        "model": {"path": str(paths.model), "sha256": model_sha, "fold": "fold_2025", "model_name": EXPECTED_MODEL_NAME,
                  "task": "rank", "target_name": EXPECTED_TARGET, "horizon": EXPECTED_HORIZON,
                  "feature_variant": EXPECTED_FEATURE_VARIANT, "retrained": False},
        "universe": {"name": CANONICAL_UNIVERSE, "provenance": universe_provenance,
                     "security_master": str(paths.security_master), "c6_universe": str(paths.c6_universe)},
        "features": {"count": len(feature_order), "ordered_names": feature_order,
                     "latest_rows": int(len(latest_features)), "finite_count_by_feature": finite_counts},
        "outputs": {"features_path": str(features_path), "features_sha256": sha256_file(features_path),
                    "predictions_path": str(predictions_path), "predictions_sha256": sha256_file(predictions_path),
                    "prediction_rows": int(len(predictions))}}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest

def score(paths: LiveScoringPaths, score_date: str | None = None) -> dict:
    model_sha = _verify_frozen_model(paths.model)
    feature_order = _load_c8_feature_order(paths.c8_manifest)
    with connect_readonly(paths.source_db) as con:
        date = _normalize_date(score_date or latest_trade_date(con))
        daily = _query_daily(con, date)
        c1_universe = _build_c1_universe(con, date)
    c3 = _c3_frame(daily, c1_universe, paths.feature_config, paths.repo)
    eligible, universe_provenance = _eligible_c8_rows(c3, c1_universe, paths.c6_universe, paths.security_master, date)
    features = _build_b_market_context(eligible, feature_order)
    predictions = _score_latest(features, feature_order, paths.model, date)
    return _write_outputs(paths, date, features, predictions, feature_order, model_sha, universe_provenance)

def parity(paths: LiveScoringPaths, date: str, rtol: float = 1e-10, atol: float = 1e-12) -> dict:
    feature_order = _load_c8_feature_order(paths.c8_manifest)
    date = _normalize_date(date)
    # Historical parity must use the exact frozen C1 inputs that produced
    # the accepted research artifacts. The current watcher DB may contain
    # later corrections/backfills that change historical PIT eligibility.
    frozen_daily_path = paths.repo / "data/cache/daily_ohlcv.parquet"
    frozen_universe_path = paths.repo / "data/cache/point_in_time_universe.parquet"

    daily = pq.read_table(frozen_daily_path)
    universe = pq.read_table(frozen_universe_path)

    daily = daily.filter(
        pa.compute.less_equal(daily["trade_date"], pa.scalar(date))
    )
    c1_universe = universe.filter(
        pa.compute.less_equal(universe["trade_date"], pa.scalar(date))
    )

    c3 = _c3_frame(daily, c1_universe, paths.feature_config, paths.repo)
    eligible, _ = _eligible_c8_rows(c3, c1_universe, paths.c6_universe, paths.security_master, date)
    live = _build_b_market_context(eligible, feature_order)
    day = pd.Timestamp(date).normalize()
    live = live.loc[live["trade_date"] == day].copy()
    c3_hist = pd.read_parquet(paths.repo / "data/processed/features/daily_features.parquet")
    market = pd.read_parquet(paths.repo / "data/processed/features/c8_market_context_features.parquet")
    relative = pd.read_parquet(paths.repo / "data/processed/features/c8_relative_features.parquet")
    for df in (c3_hist, market, relative):
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.normalize(); df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    keys = ["trade_date","symbol"]
    accepted = c3_hist.copy()

    market_add = [
        c for c in market.columns
        if c not in keys and c not in accepted.columns
    ]
    accepted = accepted.merge(
        market[keys + market_add],
        on=keys,
        how="inner",
    )

    relative_add = [
        c for c in relative.columns
        if c not in keys and c not in accepted.columns
    ]
    accepted = accepted.merge(
        relative[keys + relative_add],
        on=keys,
        how="inner",
    )

    accepted = accepted.loc[accepted["trade_date"] == day].copy()
    common = live.merge(accepted[keys + feature_order], on=keys, how="inner", suffixes=("_live","_accepted"))
    if common.empty:
        raise ValueError(f"No common historical rows for parity date {date}")
    failures=[]; max_abs=0.0; compared=0
    for f in feature_order:
        a=pd.to_numeric(common[f+"_live"],errors="coerce").to_numpy(float); b=pd.to_numeric(common[f+"_accepted"],errors="coerce").to_numpy(float)
        both_nan=np.isnan(a)&np.isnan(b); one_nan=np.isnan(a)^np.isnan(b); finite=np.isfinite(a)&np.isfinite(b)
        ok=both_nan.copy(); ok[finite]=np.isclose(a[finite],b[finite],rtol=rtol,atol=atol)
        diff=np.abs(a[finite]-b[finite]); max_abs=max(max_abs,float(diff.max())) if diff.size else max_abs
        if one_nan.any() or not ok.all():
            failures.append({"feature":f,"one_sided_nulls":int(one_nan.sum()),"mismatches":int((~ok).sum()),"max_abs_diff":float(diff.max()) if diff.size else None})
        compared += len(a)
    report={"date":date,"live_rows":int(len(live)),"accepted_rows":int(len(accepted)),"common_rows":int(len(common)),
            "feature_count":len(feature_order),"value_comparisons":int(compared),"rtol":rtol,"atol":atol,
            "max_abs_diff":max_abs,"failed_features":failures,
            "passed":not failures and len(live)==len(accepted) and len(common)==len(live)}
    out_dir=paths.output_root/"parity"; out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/f"{date}.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    return report

def _add_common(p):
    p.add_argument("--source-db", type=Path, required=True); p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--model", type=Path); p.add_argument("--c8-manifest", type=Path); p.add_argument("--c6-universe", type=Path)
    p.add_argument("--security-master", type=Path); p.add_argument("--feature-config", type=Path); p.add_argument("--output-root", type=Path)

def _paths(a):
    return LiveScoringPaths.from_args(a.repo,a.source_db,a.model,a.c8_manifest,a.c6_universe,a.security_master,a.feature_config,a.output_root)

def main():
    p=argparse.ArgumentParser(description="Frozen 2025 LightGBM live scorer for PSX C11 deployment"); sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("score"); _add_common(s); s.add_argument("--date")
    q=sub.add_parser("parity"); _add_common(q); q.add_argument("--date",required=True); q.add_argument("--rtol",type=float,default=1e-10); q.add_argument("--atol",type=float,default=1e-12)
    a=p.parse_args(); paths=_paths(a)
    if a.command=="score":
        r=score(paths,a.date); print(f"Live score complete: {r['score_date']} {r['outputs']['prediction_rows']} rows"); print(r['outputs']['predictions_path'])
    else:
        r=parity(paths,a.date,a.rtol,a.atol); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r['passed'] else 2)

if __name__ == "__main__": main()
