from __future__ import annotations
from itertools import combinations
import numpy as np
import pandas as pd

def _effective_n(weights: pd.Series) -> float:
    w = pd.to_numeric(weights, errors="raise").astype(float).to_numpy()
    s = float(w.sum())
    if s <= 0:
        return np.nan
    w = w / s
    hhi = float(np.square(w).sum())
    return 1.0 / hhi if hhi > 0 else np.nan

def _hhi(weights: pd.Series) -> float:
    w = pd.to_numeric(weights, errors="raise").astype(float).to_numpy()
    s = float(w.sum())
    if s <= 0:
        return np.nan
    w = w / s
    return float(np.square(w).sum())

def target_concentration_by_date(targets: pd.DataFrame, sector_map: pd.DataFrame) -> pd.DataFrame:
    required = {"policy_id", "trade_date", "symbol", "target_weight"}
    missing = sorted(required - set(targets.columns))
    if missing:
        raise ValueError(f"targets missing columns: {missing}")
    x = targets.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.normalize()
    x["symbol"] = x["symbol"].astype(str)
    sm = sector_map[["trade_date", "symbol", "sector"]].copy()
    sm["trade_date"] = pd.to_datetime(sm["trade_date"]).dt.normalize()
    sm["symbol"] = sm["symbol"].astype(str)
    sm = sm.drop_duplicates(["trade_date", "symbol"])
    x = x.merge(sm, on=["trade_date", "symbol"], how="left", validate="many_to_one")
    rows = []
    for (policy_id, trade_date), g in x.groupby(["policy_id", "trade_date"], sort=True):
        g = g.sort_values(["target_weight", "symbol"], ascending=[False, True])
        w = g["target_weight"].astype(float)
        if not np.isclose(w.sum(), 1.0, atol=1e-9, rtol=0):
            raise ValueError(f"{policy_id} {trade_date}: target weights != 1")
        sector = (
            g.assign(sector_key=g["sector"].fillna("__UNKNOWN__"))
            .groupby("sector_key")["target_weight"]
            .sum().sort_values(ascending=False)
        )
        rows.append({
            "policy_id": str(policy_id),
            "trade_date": pd.Timestamp(trade_date),
            "name_count": int(len(g)),
            "max_name_weight": float(w.max()),
            "top3_name_weight": float(w.head(3).sum()),
            "top5_name_weight": float(w.head(5).sum()),
            "name_hhi": _hhi(w),
            "effective_name_count": _effective_n(w),
            "sector_count": int(len(sector)),
            "max_sector_weight": float(sector.iloc[0]) if len(sector) else np.nan,
            "top2_sector_weight": float(sector.head(2).sum()) if len(sector) else np.nan,
            "sector_hhi": _hhi(sector) if len(sector) else np.nan,
            "effective_sector_count": _effective_n(sector) if len(sector) else np.nan,
            "unknown_sector_weight": float(sector.get("__UNKNOWN__", 0.0)),
        })
    return pd.DataFrame(rows)

def realized_concentration_by_date(positions: pd.DataFrame, sector_map: pd.DataFrame) -> pd.DataFrame:
    required = {"allocation_id", "starting_capital", "trade_date", "symbol", "weight_close"}
    missing = sorted(required - set(positions.columns))
    if missing:
        raise ValueError(f"positions missing columns: {missing}")
    x = positions.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.normalize()
    x["symbol"] = x["symbol"].astype(str)
    sm = sector_map[["symbol", "sector"]].dropna(subset=["sector"]).copy()
    sm["symbol"] = sm["symbol"].astype(str)
    sm = sm.drop_duplicates(["symbol"], keep="last")
    x = x.merge(sm, on="symbol", how="left", validate="many_to_one")
    rows = []
    for (allocation_id, capital, trade_date), g in x.groupby(
        ["allocation_id", "starting_capital", "trade_date"], sort=True
    ):
        w = g["weight_close"].astype(float)
        invested_weight = float(w.sum())
        if invested_weight <= 0:
            continue
        wn = w / invested_weight
        sector = (
            g.assign(
                sector_key=g["sector"].fillna("__UNKNOWN__"),
                invested_norm_weight=wn.to_numpy(),
            )
            .groupby("sector_key")["invested_norm_weight"]
            .sum().sort_values(ascending=False)
        )
        rows.append({
            "allocation_id": str(allocation_id),
            "starting_capital": float(capital),
            "trade_date": pd.Timestamp(trade_date),
            "holding_count": int(len(g)),
            "invested_weight_of_nav": invested_weight,
            "max_name_weight_of_invested": float(wn.max()),
            "top3_name_weight_of_invested": float(wn.sort_values(ascending=False).head(3).sum()),
            "top5_name_weight_of_invested": float(wn.sort_values(ascending=False).head(5).sum()),
            "name_hhi_of_invested": _hhi(wn),
            "effective_name_count": _effective_n(wn),
            "sector_count": int(len(sector)),
            "max_sector_weight_of_invested": float(sector.iloc[0]) if len(sector) else np.nan,
            "top2_sector_weight_of_invested": float(sector.head(2).sum()) if len(sector) else np.nan,
            "sector_hhi_of_invested": _hhi(sector) if len(sector) else np.nan,
            "effective_sector_count": _effective_n(sector) if len(sector) else np.nan,
            "unknown_sector_weight_of_invested": float(sector.get("__UNKNOWN__", 0.0)),
        })
    return pd.DataFrame(rows)

def pairwise_selection_overlap(deployment_selections: pd.DataFrame, policies: list[str]) -> pd.DataFrame:
    x = deployment_selections.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.normalize()
    x["symbol"] = x["symbol"].astype(str)
    rows = []
    all_dates = sorted(x.loc[x["policy_id"].isin(policies), "trade_date"].unique())
    by = {}
    for (pid, date), g in x.loc[x["policy_id"].isin(policies)].groupby(["policy_id", "trade_date"]):
        by[(str(pid), pd.Timestamp(date))] = set(g["symbol"])
    for left, right in combinations(policies, 2):
        for date in all_dates:
            a = by.get((left, pd.Timestamp(date)), set())
            b = by.get((right, pd.Timestamp(date)), set())
            inter, union = a & b, a | b
            rows.append({
                "left_policy": left,
                "right_policy": right,
                "trade_date": pd.Timestamp(date),
                "left_count": len(a),
                "right_count": len(b),
                "intersection_count": len(inter),
                "union_count": len(union),
                "jaccard": len(inter) / len(union) if union else np.nan,
                "overlap_left_fraction": len(inter) / len(a) if a else np.nan,
                "overlap_right_fraction": len(inter) / len(b) if b else np.nan,
            })
    return pd.DataFrame(rows)

def summarize_concentration(target_daily: pd.DataFrame, realized_daily: pd.DataFrame) -> pd.DataFrame:
    ts = (
        target_daily.groupby("policy_id")
        .agg(
            signal_dates=("trade_date", "nunique"),
            target_names_median=("name_count", "median"),
            target_names_min=("name_count", "min"),
            target_max_name_mean=("max_name_weight", "mean"),
            target_max_name_worst=("max_name_weight", "max"),
            target_top3_mean=("top3_name_weight", "mean"),
            target_effective_names_mean=("effective_name_count", "mean"),
            target_effective_names_min=("effective_name_count", "min"),
            target_max_sector_mean=("max_sector_weight", "mean"),
            target_max_sector_worst=("max_sector_weight", "max"),
            target_effective_sectors_mean=("effective_sector_count", "mean"),
            target_unknown_sector_weight_mean=("unknown_sector_weight", "mean"),
        ).reset_index().rename(columns={"policy_id": "allocation_id"})
    )
    rs = (
        realized_daily.groupby(["allocation_id", "starting_capital"])
        .agg(
            realized_days=("trade_date", "nunique"),
            holdings_median=("holding_count", "median"),
            holdings_min=("holding_count", "min"),
            invested_fraction_mean=("invested_weight_of_nav", "mean"),
            realized_max_name_mean=("max_name_weight_of_invested", "mean"),
            realized_max_name_worst=("max_name_weight_of_invested", "max"),
            realized_top3_mean=("top3_name_weight_of_invested", "mean"),
            realized_effective_names_mean=("effective_name_count", "mean"),
            realized_effective_names_min=("effective_name_count", "min"),
            realized_max_sector_mean=("max_sector_weight_of_invested", "mean"),
            realized_max_sector_worst=("max_sector_weight_of_invested", "max"),
            realized_effective_sectors_mean=("effective_sector_count", "mean"),
            realized_unknown_sector_weight_mean=("unknown_sector_weight_of_invested", "mean"),
        ).reset_index()
    )
    return rs.merge(ts, on="allocation_id", how="left", validate="many_to_one")
