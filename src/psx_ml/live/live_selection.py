from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from psx_ml.c10.p4_selection import (
    P4SelectionConfig,
    attach_kmi30_membership,
    filter_primary_prediction_rows,
    select_top_percentile_with_sector_cap,
)
from psx_ml.c10.p5_selection import (
    P5Config,
    _select_one_date,
    attach_point_in_time_liquidity,
    attach_screened_membership,
    load_screened_history,
)
from psx_ml.c11.live_orders import P4, P5

DEFAULT_KMI30_HISTORY = Path("data/reference/kmi30_membership_history.csv")
DEFAULT_SHARIAH_HISTORY = Path("data/reference/kmi_all_share_screened_universe_history.csv")


def _day(value: object) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def _load_kmi30_history(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
    else:
        frame = pd.read_csv(path)
    required = {"symbol", "effective_from", "effective_to"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"KMI30 history missing columns: {missing}")
    return frame


def _normalize_live_predictions(frame: pd.DataFrame, date: object) -> pd.DataFrame:
    day = _day(date)
    x = frame.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.normalize()
    x["symbol"] = x["symbol"].astype(str).str.strip().str.upper()
    x = x.loc[x["trade_date"] == day].copy()
    if x.empty:
        raise ValueError(f"No live predictions for {day.date()}")
    if x.duplicated(["trade_date", "symbol"]).any():
        raise ValueError("Duplicate live prediction date/symbol rows")
    return x


def _live_liquidity(features: pd.DataFrame, date: object) -> pd.DataFrame:
    day = _day(date)
    required = {"trade_date", "symbol", "turnover_median_20obs_adj"}
    missing = sorted(required - set(features.columns))
    if missing:
        raise ValueError(f"Live features missing liquidity columns: {missing}")
    x = features[["trade_date", "symbol", "turnover_median_20obs_adj"]].copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.normalize()
    x["symbol"] = x["symbol"].astype(str).str.strip().str.upper()
    x = x.loc[x["trade_date"] <= day].copy()
    x = x.rename(columns={"trade_date": "liquidity_observation_date"})
    if x.duplicated(["symbol", "liquidity_observation_date"]).any():
        raise ValueError("Duplicate live liquidity symbol/date rows")
    return x


def build_live_p4(*, predictions, membership, date, config=P4SelectionConfig()) -> pd.DataFrame:
    day = _day(date)
    primary = filter_primary_prediction_rows(predictions)
    primary = primary.loc[primary["trade_date"] == day].copy()
    eligible = attach_kmi30_membership(primary, membership)
    date_rows = eligible.loc[eligible["trade_date"] == day].copy()
    if date_rows.empty:
        raise ValueError(f"No KMI30 candidates for {day.date()}")
    selected = select_top_percentile_with_sector_cap(date_rows, config).copy()
    selected["policy_id"] = P4
    selected["shariah_eligible"] = True
    selected["shariah_source"] = "kmi30_membership_history"
    selected["shariah_confidence"] = "high"
    return selected


def build_live_p5(*, predictions, screened_history, liquidity, date, config=P5Config()) -> pd.DataFrame:
    day = _day(date)
    x = predictions.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.normalize()
    x["symbol"] = x["symbol"].astype(str).str.strip().str.upper()
    x = x.loc[
        (x["trade_date"] == day)
        & (x["horizon"].astype(int) == config.horizon)
        & (x["feature_variant"].astype(str) == config.feature_variant)
        & (x["model_name"].astype(str) == config.model_name)
        & (x["target_family"].astype(str).isin({"market_relative", "market_relative_rank"}))
    ].copy()
    if x.empty:
        raise ValueError(f"No P5 primary prediction rows for {day.date()}")
    screened = attach_screened_membership(x, screened_history)
    screened = attach_point_in_time_liquidity(screened, liquidity)
    selected = _select_one_date(screened, config).copy()
    if selected.empty:
        raise ValueError("P5 selection produced no rows")
    if selected.groupby(["trade_date", "sector"], dropna=False).size().gt(config.sector_cap).any():
        raise ValueError("P5 sector cap breach")
    selected["policy_id"] = P5
    selected["shariah_eligible"] = True
    selected["shariah_source"] = selected["membership_source"].astype(str)
    selected["shariah_confidence"] = selected["membership_confidence"].astype(str)
    return selected


def build_live_selections(*, predictions, features, kmi30_history, screened_history, date) -> pd.DataFrame:
    predictions = _normalize_live_predictions(predictions, date)
    liquidity = _live_liquidity(features, date)
    p4 = build_live_p4(predictions=predictions, membership=kmi30_history, date=date)
    p5 = build_live_p5(predictions=predictions, screened_history=screened_history, liquidity=liquidity, date=date)
    keep = ["policy_id", "trade_date", "symbol", "prediction", "sector", "selection_rank", "shariah_eligible", "shariah_source", "shariah_confidence"]
    out = pd.concat([p4[keep], p5[keep]], ignore_index=True)
    if set(out["policy_id"].astype(str)) != {P4, P5}:
        raise ValueError("Live selection must contain both deployment P4 and P5")
    if out.duplicated(["policy_id", "trade_date", "symbol"]).any():
        raise ValueError("Duplicate live deployment selection")
    return out.sort_values(["policy_id", "selection_rank", "symbol"], kind="mergesort").reset_index(drop=True)


def run(*, repo: Path, date: str) -> Path:
    day = _day(date)
    live_dir = repo / "artifacts/live" / day.strftime("%Y-%m-%d")
    predictions = pd.read_parquet(live_dir / "predictions.parquet")
    features = pd.read_parquet(live_dir / "features.parquet")
    kmi30 = _load_kmi30_history(repo / DEFAULT_KMI30_HISTORY)
    screened = load_screened_history(repo / DEFAULT_SHARIAH_HISTORY)
    selections = build_live_selections(predictions=predictions, features=features, kmi30_history=kmi30, screened_history=screened, date=day)
    out_path = live_dir / "selections.parquet"
    selections.to_parquet(out_path, index=False)
    summary = {
        "date": day.strftime("%Y-%m-%d"),
        "rows": int(len(selections)),
        "p4_rows": int((selections["policy_id"] == P4).sum()),
        "p5_rows": int((selections["policy_id"] == P5).sum()),
        "overlap_symbols": int(selections.groupby("symbol")["policy_id"].nunique().eq(2).sum()),
        "output": str(out_path.resolve()),
    }
    (live_dir / "selection_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(out_path.resolve())
    return out_path


def main() -> None:
    p = argparse.ArgumentParser(description="Build live P4/P5 deployment selections")
    p.add_argument("--date", required=True)
    p.add_argument("--repo", type=Path, default=Path.cwd())
    a = p.parse_args()
    run(repo=a.repo.resolve(), date=a.date)


if __name__ == "__main__":
    main()
