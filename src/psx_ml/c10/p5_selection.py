from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import numpy as np
import pandas as pd


P5_POLICY_ID = "P5_shariah_screened"

C8_PREDICTIONS = Path(
    "artifacts/predictions/c8/validation_predictions.parquet"
)
C9_SELECTIONS = Path(
    "data/processed/c9/candidate_selections.parquet"
)
DAILY_FEATURES = Path(
    "data/processed/features/daily_features.parquet"
)
SCREENED_HISTORY = Path(
    "data/reference/kmi_all_share_screened_universe_history.csv"
)


@dataclass(frozen=True)
class P5Config:
    model_name: str = "lightgbm_cpu"
    horizon: int = 5
    target_family: str = "market_relative"
    feature_variant: str = "B_market_context"
    liquidity_keep_fraction: float = 0.75
    selection_fraction: float = 0.10
    sector_cap: int = 2


def load_weekly_signal_dates(path: Path = C9_SELECTIONS) -> pd.DatetimeIndex:
    frame = pd.read_parquet(path)
    p1 = frame.loc[
        frame["policy_id"].astype(str) == "P1_broad_canonical"
    ].copy()
    if p1.empty:
        raise ValueError("No P1_broad_canonical rows found")
    dates = pd.DatetimeIndex(
        pd.to_datetime(p1["trade_date"]).unique()
    ).sort_values()
    if (dates.year >= 2026).any():
        raise ValueError("2026 holdout dates found")
    return dates


def load_primary_predictions(
    path: Path = C8_PREDICTIONS,
    config: P5Config = P5Config(),
) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    required = {
        "trade_date", "symbol", "horizon", "target_family",
        "feature_variant", "model_name", "prediction", "sector",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"C8 predictions missing: {sorted(missing)}")

    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    frame["symbol"] = frame["symbol"].astype(str).str.strip().str.upper()

    result = frame.loc[
        (frame["horizon"].astype(int) == config.horizon)
        & (frame["target_family"].astype(str) == config.target_family)
        & (frame["feature_variant"].astype(str) == config.feature_variant)
        & (frame["model_name"].astype(str) == config.model_name)
    ].copy()

    if result.empty:
        raise ValueError("No accepted primary C8 prediction rows found")
    if (result["trade_date"].dt.year >= 2026).any():
        raise ValueError("2026 holdout predictions found")
    if result.duplicated(["trade_date", "symbol"]).any():
        raise ValueError(
            "Primary C8 rows are not unique by trade_date/symbol"
        )
    return result


def load_screened_history(path: Path = SCREENED_HISTORY) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
    elif path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    else:
        raise ValueError(
            f"Unsupported screened-history format: {path.suffix}"
        )

    required = {
        "symbol",
        "effective_from",
        "effective_to",
        "screening_snapshot_date",
        "membership_source",
        "membership_confidence",
        "is_shariah_screened_eligible",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            f"Screened history missing columns: {sorted(missing)}"
        )

    for col in (
        "effective_from",
        "effective_to",
        "screening_snapshot_date",
    ):
        frame[col] = pd.to_datetime(
            frame[col],
            errors="coerce",
        )

    frame["symbol"] = (
        frame["symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    eligible = (
        frame["is_shariah_screened_eligible"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(
            {
                "true": True,
                "false": False,
                "1": True,
                "0": False,
            }
        )
    )
    if eligible.isna().any():
        bad = sorted(
            frame.loc[
                eligible.isna(),
                "is_shariah_screened_eligible",
            ]
            .astype(str)
            .unique()
            .tolist()
        )
        raise ValueError(
            "Unrecognized screened-history eligibility values: "
            f"{bad}"
        )
    frame["is_shariah_screened_eligible"] = eligible.astype(bool)

    if (frame["effective_from"].dt.year >= 2026).any():
        raise ValueError("2026 rows found in screened history")

    return frame


def load_liquidity(path: Path = DAILY_FEATURES) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    required = {
        "trade_date",
        "symbol",
        "turnover_median_20obs_adj",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Daily features missing: {sorted(missing)}")

    result = frame[
        ["trade_date", "symbol", "turnover_median_20obs_adj"]
    ].copy()
    result["trade_date"] = pd.to_datetime(result["trade_date"])
    result["symbol"] = result["symbol"].astype(str).str.strip().str.upper()
    result = result.rename(
        columns={"trade_date": "liquidity_observation_date"}
    )
    if result.duplicated(
        ["symbol", "liquidity_observation_date"]
    ).any():
        raise ValueError("Liquidity source has duplicate symbol/date rows")
    return result


def attach_screened_membership(
    predictions: pd.DataFrame,
    history: pd.DataFrame,
) -> pd.DataFrame:
    chunks = []
    intervals = (
        history[
            [
                "effective_from",
                "effective_to",
                "screening_snapshot_date",
                "membership_source",
                "membership_confidence",
            ]
        ]
        .drop_duplicates()
        .sort_values("effective_from")
    )

    for interval in intervals.itertuples(index=False):
        mask = predictions["trade_date"] >= interval.effective_from
        if pd.notna(interval.effective_to):
            mask &= predictions["trade_date"] < interval.effective_to

        date_slice = predictions.loc[mask].copy()
        if date_slice.empty:
            continue

        members = history.loc[
            (history["effective_from"] == interval.effective_from)
            & history["is_shariah_screened_eligible"].astype(bool),
            ["symbol"],
        ]

        joined = date_slice.merge(
            members,
            on="symbol",
            how="inner",
            validate="many_to_one",
        )
        joined["screening_effective_from"] = interval.effective_from
        joined["screening_effective_to"] = interval.effective_to
        joined["screening_snapshot_date"] = interval.screening_snapshot_date
        joined["membership_source"] = interval.membership_source
        joined["membership_confidence"] = interval.membership_confidence
        chunks.append(joined)

    if not chunks:
        raise ValueError("No predictions matched screened universe")

    result = pd.concat(chunks, ignore_index=True)
    if result.duplicated(["trade_date", "symbol"]).any():
        raise ValueError("Membership join produced duplicate rows")
    return result


def attach_point_in_time_liquidity(
    candidates: pd.DataFrame,
    liquidity: pd.DataFrame,
) -> pd.DataFrame:
    left = candidates.copy()
    left["_row_id"] = np.arange(len(left))

    # pandas.merge_asof requires the ASOF key itself to be
    # globally monotonic. Sorting by symbol first can make
    # trade_date move backwards when the symbol changes,
    # which raises "left keys must be sorted".
    left = left.sort_values(
        ["trade_date", "symbol", "_row_id"],
        kind="mergesort",
    )
    right = liquidity.sort_values(
        ["liquidity_observation_date", "symbol"],
        kind="mergesort",
    )

    result = pd.merge_asof(
        left,
        right,
        left_on="trade_date",
        right_on="liquidity_observation_date",
        by="symbol",
        direction="backward",
        allow_exact_matches=True,
    )

    future = (
        result["liquidity_observation_date"].notna()
        & (
            result["liquidity_observation_date"]
            > result["trade_date"]
        )
    )
    if future.any():
        raise ValueError("Future liquidity observation used")

    result["liquidity_age_calendar_days"] = (
        result["trade_date"]
        - result["liquidity_observation_date"]
    ).dt.days

    return (
        result.sort_values("_row_id")
        .drop(columns="_row_id")
        .reset_index(drop=True)
    )


def _select_one_date(
    frame: pd.DataFrame,
    config: P5Config,
) -> pd.DataFrame:
    work = frame.copy()
    work = work.loc[
        pd.to_numeric(work["prediction"], errors="coerce").notna()
        & pd.to_numeric(
            work["turnover_median_20obs_adj"], errors="coerce"
        ).gt(0)
    ].copy()

    before_count = len(work)
    if before_count == 0:
        return work

    ordered = work.sort_values(
        ["turnover_median_20obs_adj", "symbol"],
        ascending=[True, True],
        kind="mergesort",
    ).copy()
    ordered["liquidity_rank_ascending"] = np.arange(
        1, len(ordered) + 1
    )
    ordered["liquidity_percentile_rank"] = (
        ordered["liquidity_rank_ascending"] / len(ordered)
    )

    drop_count = math.floor(
        len(ordered) * (1.0 - config.liquidity_keep_fraction)
    )
    liquid = ordered.loc[
        ordered["liquidity_rank_ascending"] > drop_count
    ].copy()

    after_count = len(liquid)
    target_count = max(
        1,
        math.ceil(after_count * config.selection_fraction),
    )

    ranked = liquid.sort_values(
        ["prediction", "turnover_median_20obs_adj", "symbol"],
        ascending=[False, False, True],
        kind="mergesort",
    ).copy()
    ranked["candidate_rank"] = np.arange(1, len(ranked) + 1)

    selected_indexes = []
    sector_counts: dict[str, int] = {}

    for index, row in ranked.iterrows():
        sector = str(row.get("sector", "")).strip() or "__MISSING_SECTOR__"
        if sector_counts.get(sector, 0) >= config.sector_cap:
            continue
        selected_indexes.append(index)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        if len(selected_indexes) >= target_count:
            break

    selected = ranked.loc[selected_indexes].copy()
    selected["selection_rank"] = np.arange(1, len(selected) + 1)
    selected["shariah_candidate_count_before_liquidity"] = before_count
    selected["shariah_candidate_count_after_liquidity"] = after_count
    selected["selection_target_count"] = target_count
    selected["selection_shortfall"] = target_count - len(selected)
    selected["liquidity_filter_pass"] = True
    selected["policy_id"] = P5_POLICY_ID
    selected["selection_date"] = selected["trade_date"]
    return selected


def build_p5_selections(
    predictions: pd.DataFrame,
    screened_history: pd.DataFrame,
    liquidity: pd.DataFrame,
    weekly_signal_dates: pd.DatetimeIndex,
    config: P5Config = P5Config(),
) -> pd.DataFrame:
    primary = predictions.loc[
        predictions["trade_date"].isin(
            pd.DatetimeIndex(pd.to_datetime(weekly_signal_dates))
        )
    ].copy()

    screened = attach_screened_membership(primary, screened_history)
    screened = attach_point_in_time_liquidity(screened, liquidity)

    chunks = []
    for _, group in screened.groupby("trade_date", sort=True):
        selected = _select_one_date(group, config)
        if not selected.empty:
            chunks.append(selected)

    if not chunks:
        raise ValueError("P5 selection produced no rows")

    result = pd.concat(chunks, ignore_index=True).sort_values(
        ["trade_date", "selection_rank"]
    ).reset_index(drop=True)

    if (result["trade_date"].dt.year >= 2026).any():
        raise ValueError("2026 holdout rows in P5 selections")
    if result.duplicated(["trade_date", "symbol"]).any():
        raise ValueError("Duplicate P5 date/symbol rows")
    if result.duplicated(["trade_date", "selection_rank"]).any():
        raise ValueError("Duplicate P5 date/rank rows")
    if (
        result.groupby(["trade_date", "sector"], dropna=False)
        .size()
        .gt(config.sector_cap)
        .any()
    ):
        raise ValueError("P5 sector cap breach")

    return result
