from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


P4_POLICY_ID = "P4_kmi30_strict"


@dataclass(frozen=True)
class P4SelectionConfig:
    percentile: float = 0.10
    sector_cap: int = 2
    minimum_count: int = 1


def normalize_prediction_columns(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    aliases = {
        "fold": "fold_id",
        "model": "model_name",
        "date": "trade_date",
    }

    for old, new in aliases.items():
        if old in result.columns and new not in result.columns:
            result = result.rename(columns={old: new})

    required = {
        "trade_date",
        "symbol",
        "horizon",
        "target_family",
        "feature_variant",
        "model_name",
        "prediction",
        "sector",
    }
    missing = sorted(required - set(result.columns))
    if missing:
        raise ValueError(
            f"Prediction frame missing required columns: {missing}"
        )

    result["trade_date"] = pd.to_datetime(
        result["trade_date"],
        errors="raise",
    ).dt.normalize()

    result["symbol"] = (
        result["symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result["prediction"] = pd.to_numeric(
        result["prediction"],
        errors="raise",
    )

    return result


def filter_primary_prediction_rows(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    frame = normalize_prediction_columns(predictions)

    filtered = frame.loc[
        (frame["horizon"].astype(int) == 5)
        & (
            frame["target_family"].astype(str).isin(
                {
                    "market_relative",
                    "market_relative_rank",
                }   
            )
        )
        & (
            frame["feature_variant"].astype(str)
            == "B_market_context"
        )
        & (
            frame["model_name"].astype(str)
            == "lightgbm_cpu"
        )
    ].copy()

    if filtered.empty:
        raise ValueError(
            "No primary LightGBM 5-session market-relative "
            "prediction rows found"
        )

    duplicate_keys = [
        "trade_date",
        "symbol",
    ]
    if filtered.duplicated(duplicate_keys).any():
        sample = filtered.loc[
            filtered.duplicated(
                duplicate_keys,
                keep=False,
            ),
            duplicate_keys
            + [
                "fold_id",
                "model_name",
            ],
        ].head(20)

        raise ValueError(
            "Duplicate primary prediction date-symbol rows:\n"
            + sample.to_string(index=False)
        )

    return filtered


def normalize_membership(
    membership: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "symbol",
        "effective_from",
        "effective_to",
    }
    missing = sorted(required - set(membership.columns))
    if missing:
        raise ValueError(
            f"Membership frame missing required columns: {missing}"
        )

    result = membership.copy()
    result["symbol"] = (
        result["symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    result["effective_from"] = pd.to_datetime(
        result["effective_from"],
        errors="raise",
    ).dt.normalize()

    finite = (
        result["effective_to"].astype(str)
        != "9999-12-31"
    )
    result["effective_to_parsed"] = pd.Timestamp.max.normalize()
    result.loc[
        finite,
        "effective_to_parsed",
    ] = pd.to_datetime(
        result.loc[
            finite,
            "effective_to",
        ],
        errors="raise",
    ).dt.normalize()

    return result


def attach_kmi30_membership(
    predictions: pd.DataFrame,
    membership: pd.DataFrame,
) -> pd.DataFrame:
    prediction_frame = predictions.copy()
    prediction_frame["trade_date"] = pd.to_datetime(
        prediction_frame["trade_date"],
        errors="raise",
    ).dt.normalize()
    prediction_frame["symbol"] = (
        prediction_frame["symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    member_frame = normalize_membership(membership)

    intervals = (
        member_frame[
            [
                "effective_from",
                "effective_to_parsed",
            ]
        ]
        .drop_duplicates()
        .sort_values("effective_from")
        .reset_index(drop=True)
    )

    pieces: list[pd.DataFrame] = []

    for row in intervals.itertuples(index=False):
        interval_members = member_frame.loc[
            (
                member_frame["effective_from"]
                == row.effective_from
            )
            & (
                member_frame[
                    "effective_to_parsed"
                ]
                == row.effective_to_parsed
            )
        ].copy()

        interval_predictions = prediction_frame.loc[
            (
                prediction_frame["trade_date"]
                >= row.effective_from
            )
            & (
                prediction_frame["trade_date"]
                <= row.effective_to_parsed
            )
        ].copy()

        if interval_predictions.empty:
            continue

        merged = interval_predictions.merge(
            interval_members.drop(
                columns=["effective_to_parsed"],
            ),
            on="symbol",
            how="inner",
            validate="many_to_one",
            suffixes=("", "_membership"),
        )

        pieces.append(merged)

    if not pieces:
        raise ValueError(
            "No predictions matched point-in-time KMI-30 membership"
        )

    result = pd.concat(
        pieces,
        ignore_index=True,
    )

    if (
        result["trade_date"]
        < result["effective_from"]
    ).any():
        raise ValueError(
            "Prediction matched before KMI-30 effective_from"
        )

    finite_result = (
        result["effective_to"].astype(str)
        != "9999-12-31"
    )
    if (
        result.loc[
            finite_result,
            "trade_date",
        ]
        > pd.to_datetime(
            result.loc[
                finite_result,
                "effective_to",
            ]
        ).dt.normalize()
    ).any():
        raise ValueError(
            "Prediction matched after KMI-30 effective_to"
        )

    return result


def select_top_percentile_with_sector_cap(
    date_rows: pd.DataFrame,
    config: P4SelectionConfig,
) -> pd.DataFrame:
    if date_rows.empty:
        return date_rows.copy()

    if not (0 < config.percentile <= 1):
        raise ValueError(
            "percentile must be in (0, 1]"
        )
    if config.sector_cap <= 0:
        raise ValueError(
            "sector_cap must be positive"
        )

    ranked = (
        date_rows.sort_values(
            ["prediction", "symbol"],
            ascending=[False, True],
            kind="mergesort",
        )
        .reset_index(drop=True)
        .copy()
    )

    candidate_count = len(ranked)
    target_count = max(
        config.minimum_count,
        int(np.ceil(
            candidate_count
            * config.percentile
        )),
    )

    selected_indexes: list[int] = []
    sector_counts: dict[str, int] = {}

    for index, row in ranked.iterrows():
        sector = str(row["sector"])
        used = sector_counts.get(sector, 0)

        if used >= config.sector_cap:
            continue

        selected_indexes.append(index)
        sector_counts[sector] = used + 1

        if len(selected_indexes) >= target_count:
            break

    selected = ranked.loc[
        selected_indexes
    ].copy()

    selected["kmi30_candidate_count"] = (
        candidate_count
    )
    selected["selection_target_count"] = (
        target_count
    )
    selected["selection_rank"] = np.arange(
        1,
        len(selected) + 1,
    )
    selected["prediction_percentile_rank_kmi30"] = (
        1.0
        - (
            selected["selection_rank"] - 1
        )
        / max(candidate_count, 1)
    )

    return selected


def build_p4_selections(
    *,
    predictions: pd.DataFrame,
    membership: pd.DataFrame,
    weekly_signal_dates: pd.Series,
    config: P4SelectionConfig = P4SelectionConfig(),
) -> pd.DataFrame:
    primary = filter_primary_prediction_rows(
        predictions
    )

    signal_dates = pd.to_datetime(
        weekly_signal_dates,
        errors="raise",
    )

    if isinstance(signal_dates, pd.Series):
        signal_dates = signal_dates.dt.normalize()
    elif isinstance(signal_dates, pd.DatetimeIndex):
        signal_dates = signal_dates.normalize()
    else:
        signal_dates = pd.DatetimeIndex(
            signal_dates
        ).normalize()

    signal_dates = pd.Index(
        sorted(signal_dates.unique())
    )

    primary = primary.loc[
        primary["trade_date"].isin(
            signal_dates
        )
    ].copy()

    if primary.empty:
        raise ValueError(
            "No primary predictions matched weekly signal dates"
        )

    eligible = attach_kmi30_membership(
        primary,
        membership,
    )

    selected_frames: list[pd.DataFrame] = []

    for trade_date in signal_dates:
        date_rows = eligible.loc[
            eligible["trade_date"]
            == trade_date
        ].copy()

        if date_rows.empty:
            raise ValueError(
                "No eligible KMI-30 prediction rows for "
                f"weekly signal date {trade_date.date()}"
            )

        selected_frames.append(
            select_top_percentile_with_sector_cap(
                date_rows,
                config,
            )
        )

    result = pd.concat(
        selected_frames,
        ignore_index=True,
    )

    result["policy_id"] = P4_POLICY_ID
    result["selection_date"] = (
        result["trade_date"]
    )
    result["selection_tail"] = "top"
    result["kmi30_member"] = True

    ordered_columns = [
        "policy_id",
        "trade_date",
        "symbol",
        "fold_id",
        "horizon",
        "target_family",
        "feature_variant",
        "model_name",
        "prediction",
        "actual_rank_target",
        "actual_market_relative_return",
        "sector",
        "turnover_median_20obs_adj",
        "turnover_percentile_rank",
        "momentum_rank",
        "liquidity_rank",
        "market_trend_regime",
        "market_volatility_regime",
        "market_breadth_regime",
        "market_dispersion_regime",
        "prediction_provenance",
        "prediction_percentile_rank_kmi30",
        "selection_date",
        "selection_tail",
        "kmi30_member",
        "kmi30_candidate_count",
        "selection_target_count",
        "selection_rank",
        "effective_from",
        "effective_to",
        "review_as_of",
        "notice_date",
        "notice_no",
        "source_url",
        "source_type",
    ]

    available_order = [
        column
        for column in ordered_columns
        if column in result.columns
    ]
    remaining = [
        column
        for column in result.columns
        if column not in available_order
    ]

    result = result[
        available_order + remaining
    ].sort_values(
        ["trade_date", "selection_rank", "symbol"]
    ).reset_index(drop=True)

    return result


def locate_primary_prediction_file(
    root: Path = Path("artifacts/predictions/c8"),
) -> Path:
    candidates: list[tuple[int, Path]] = []

    if not root.exists():
        raise FileNotFoundError(
            f"Prediction root does not exist: {root}"
        )

    for path in root.rglob("*.parquet"):
        try:
            frame = pd.read_parquet(path)
        except Exception:
            continue

        columns = set(frame.columns)
        normalized = set(columns)
        if "model" in normalized:
            normalized.add("model_name")
        if "fold" in normalized:
            normalized.add("fold_id")

        required = {
            "trade_date",
            "symbol",
            "horizon",
            "target_family",
            "feature_variant",
            "model_name",
            "prediction",
            "sector",
        }

        if required.issubset(normalized):
            candidates.append(
                (len(frame), path)
            )

    if not candidates:
        raise FileNotFoundError(
            "Could not locate a C8 prediction parquet "
            "with the required schema under "
            f"{root}"
        )

    candidates.sort(
        key=lambda item: (
            -item[0],
            str(item[1]),
        )
    )

    return candidates[0][1]
