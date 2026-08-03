from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


FINAL_HOLDOUT_START = pd.Timestamp("2026-01-01")

C9_SELECTIONS_PATH = Path(
    "data/processed/c9/candidate_selections.parquet"
)

PRICE_PATH = Path(
    "data/cache/daily_ohlcv.parquet"
)

FEATURE_PATH = Path(
    "data/processed/features/daily_features.parquet"
)


@dataclass(frozen=True)
class FrameAudit:
    path: str
    rows: int
    symbols: int
    min_date: str
    max_date: str
    holdout_rows: int
    duplicate_keys: int


def normalize_dates(
    frame: pd.DataFrame,
    *,
    column: str = "trade_date",
) -> pd.DataFrame:
    result = frame.copy()
    result[column] = pd.to_datetime(
        result[column],
        errors="raise",
    ).dt.normalize()
    return result


def assert_no_holdout(
    frame: pd.DataFrame,
    *,
    column: str = "trade_date",
) -> None:
    dates = pd.to_datetime(frame[column], errors="raise")
    count = int((dates >= FINAL_HOLDOUT_START).sum())

    if count:
        raise ValueError(
            f"Final holdout access denied: {count} rows dated 2026 or later"
        )


def load_c9_selections(
    path: Path = C9_SELECTIONS_PATH,
) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    frame = normalize_dates(frame)

    required = {
        "policy_id",
        "trade_date",
        "symbol",
        "fold_id",
        "horizon",
        "target_family",
        "feature_variant",
        "model_name",
        "prediction",
        "sector",
        "selection_date",
        "selection_tail",
    }

    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            f"C9 selections missing required columns: {missing}"
        )

    assert_no_holdout(frame)

    valid_policies = {
        "P1_broad_canonical",
        "P2_conservative_consensus",
    }

    available_policies = set(
        frame["policy_id"].dropna().unique()
    )

    missing_policies = sorted(
        valid_policies - available_policies
    )

    if missing_policies:
        raise ValueError(
            f"Required frozen C9 policies are missing: {missing_policies}"
        )

    frame = frame.loc[
        frame["policy_id"].isin(valid_policies)
    ].copy()

    return frame.sort_values(
        ["trade_date", "policy_id", "symbol"]
    ).reset_index(drop=True)


def load_execution_prices(
    *,
    path: Path = PRICE_PATH,
    maximum_date: pd.Timestamp,
) -> pd.DataFrame:
    columns = [
        "trade_date",
        "symbol",
        "open_adj",
        "high_adj",
        "low_adj",
        "close_adj",
        "volume_adj",
        "adj_factor",
    ]

    frame = pd.read_parquet(path, columns=columns)
    frame = normalize_dates(frame)

    frame = frame.loc[
        frame["trade_date"] <= maximum_date
    ].copy()

    assert_no_holdout(frame)

    duplicate_count = int(
        frame.duplicated(["trade_date", "symbol"]).sum()
    )

    if duplicate_count:
        raise ValueError(
            f"Price data contains {duplicate_count} duplicate date-symbol rows"
        )

    for column in ["open_adj", "close_adj"]:
        invalid = frame[column].notna() & (frame[column] <= 0)
        if invalid.any():
            raise ValueError(
                f"Price data contains invalid non-positive {column}"
            )

    return frame.sort_values(
        ["trade_date", "symbol"]
    ).reset_index(drop=True)


def load_liquidity_features(
    *,
    path: Path = FEATURE_PATH,
    maximum_date: pd.Timestamp,
) -> pd.DataFrame:
    columns = [
        "trade_date",
        "symbol",
        "turnover_1obs_adj",
        "turnover_median_20obs_adj",
        "stale_close_run_length",
        "zero_volume_flag",
        "missing_volume_flag",
    ]

    frame = pd.read_parquet(path, columns=columns)
    frame = normalize_dates(frame)

    frame = frame.loc[
        frame["trade_date"] <= maximum_date
    ].copy()

    assert_no_holdout(frame)

    if frame.duplicated(["trade_date", "symbol"]).any():
        raise ValueError(
            "Liquidity feature data contains duplicate date-symbol rows"
        )

    return frame.sort_values(
        ["trade_date", "symbol"]
    ).reset_index(drop=True)


def audit_frame(
    frame: pd.DataFrame,
    *,
    path: Path,
    key_columns: tuple[str, ...] = (
        "trade_date",
        "symbol",
    ),
) -> FrameAudit:
    dates = pd.to_datetime(frame["trade_date"], errors="raise")

    return FrameAudit(
        path=str(path),
        rows=int(len(frame)),
        symbols=int(frame["symbol"].nunique()),
        min_date=dates.min().date().isoformat(),
        max_date=dates.max().date().isoformat(),
        holdout_rows=int(
            (dates >= FINAL_HOLDOUT_START).sum()
        ),
        duplicate_keys=int(
            frame.duplicated(list(key_columns)).sum()
        ),
    )
