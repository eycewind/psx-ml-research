from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


FINAL_HOLDOUT_START = pd.Timestamp("2026-01-01")
LAST_PRE_HOLDOUT_DATE = FINAL_HOLDOUT_START - pd.Timedelta(days=1)

C9_SELECTIONS_PATH = Path("data/processed/c9/candidate_selections.parquet")
P4_SELECTIONS_PATH = Path("data/processed/c10/p4_kmi30_selections.parquet")
PRICE_PATH = Path("data/cache/daily_ohlcv.parquet")
FEATURE_PATH = Path("data/processed/features/daily_features.parquet")


@dataclass(frozen=True)
class FrameAudit:
    path: str
    rows: int
    symbols: int
    min_date: str
    max_date: str
    holdout_rows: int
    duplicate_keys: int


def normalize_dates(frame: pd.DataFrame, *, column: str = "trade_date") -> pd.DataFrame:
    result = frame.copy()
    result[column] = pd.to_datetime(result[column], errors="raise").dt.normalize()
    return result


def assert_no_holdout(frame: pd.DataFrame, *, column: str = "trade_date") -> None:
    dates = pd.to_datetime(frame[column], errors="raise")
    count = int((dates >= FINAL_HOLDOUT_START).sum())
    if count:
        raise ValueError(
            f"Final holdout access denied: {count} rows dated 2026 or later"
        )


def _validate_selection_schema(
    frame: pd.DataFrame,
    *,
    source_name: str,
) -> pd.DataFrame:
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
            f"{source_name} selections missing required columns: {missing}"
        )

    result = normalize_dates(frame)
    result["selection_date"] = pd.to_datetime(
        result["selection_date"],
        errors="raise",
    ).dt.normalize()
    result["symbol"] = (
        result["symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    assert_no_holdout(result)
    return result


def load_c9_selections(
    path: Path = C9_SELECTIONS_PATH,
) -> pd.DataFrame:
    frame = _validate_selection_schema(
        pd.read_parquet(path),
        source_name="C9",
    )

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
            "Required frozen C9 policies are missing: "
            f"{missing_policies}"
        )

    frame = frame.loc[
        frame["policy_id"].isin(valid_policies)
    ].copy()

    return frame.sort_values(
        ["trade_date", "policy_id", "symbol"]
    ).reset_index(drop=True)


def load_p4_selections(
    path: Path = P4_SELECTIONS_PATH,
) -> pd.DataFrame:
    frame = _validate_selection_schema(
        pd.read_parquet(path),
        source_name="P4",
    )

    expected_policy = "P4_kmi30_strict"
    policies = set(
        frame["policy_id"].dropna().unique()
    )
    if policies != {expected_policy}:
        raise ValueError(
            "P4 selection file must contain only "
            f"{expected_policy}; found {sorted(policies)}"
        )

    if "kmi30_member" not in frame.columns:
        raise ValueError(
            "P4 selections missing kmi30_member"
        )
    if not frame["kmi30_member"].fillna(False).all():
        raise ValueError(
            "P4 selections contain non-KMI-30 rows"
        )

    if frame.duplicated(
        ["policy_id", "trade_date", "symbol"]
    ).any():
        raise ValueError(
            "P4 selections contain duplicate policy/date/symbol rows"
        )

    return frame.sort_values(
        ["trade_date", "policy_id", "symbol"]
    ).reset_index(drop=True)


def load_c10_selections(
    *,
    c9_path: Path = C9_SELECTIONS_PATH,
    p4_path: Path = P4_SELECTIONS_PATH,
) -> pd.DataFrame:
    c9 = load_c9_selections(c9_path)
    p4 = load_p4_selections(p4_path)

    common_columns = sorted(
        set(c9.columns) & set(p4.columns)
    )

    required_common = {
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
    missing_common = sorted(
        required_common - set(common_columns)
    )
    if missing_common:
        raise ValueError(
            "Combined C10 selection inputs lack shared required "
            f"columns: {missing_common}"
        )

    combined = pd.concat(
        [
            c9[common_columns],
            p4[common_columns],
        ],
        ignore_index=True,
        sort=False,
    )

    if combined.duplicated(
        ["policy_id", "trade_date", "symbol"]
    ).any():
        raise ValueError(
            "Combined C10 selections contain duplicate "
            "policy/date/symbol rows"
        )

    expected_policies = {
        "P1_broad_canonical",
        "P2_conservative_consensus",
        "P4_kmi30_strict",
    }
    policies = set(
        combined["policy_id"].dropna().unique()
    )
    if policies != expected_policies:
        raise ValueError(
            "Combined C10 policy set mismatch: "
            f"{sorted(policies)}"
        )

    assert_no_holdout(combined)

    return combined.sort_values(
        ["trade_date", "policy_id", "symbol"]
    ).reset_index(drop=True)

def load_execution_prices(
    *,
    path: Path = PRICE_PATH,
    maximum_date: pd.Timestamp = LAST_PRE_HOLDOUT_DATE,
) -> pd.DataFrame:
    maximum_date = min(
        pd.Timestamp(maximum_date).normalize(),
        LAST_PRE_HOLDOUT_DATE,
    )
    columns = [
        "trade_date", "symbol", "open_adj", "high_adj", "low_adj",
        "close_adj", "volume_adj", "adj_factor",
    ]
    frame = normalize_dates(pd.read_parquet(path, columns=columns))
    frame = frame.loc[frame["trade_date"] <= maximum_date].copy()
    assert_no_holdout(frame)

    duplicate_count = int(frame.duplicated(["trade_date", "symbol"]).sum())
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

    return frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)


def load_liquidity_features(
    *,
    path: Path = FEATURE_PATH,
    maximum_date: pd.Timestamp,
) -> pd.DataFrame:
    columns = [
        "trade_date", "symbol", "turnover_1obs_adj",
        "turnover_median_20obs_adj", "stale_close_run_length",
        "zero_volume_flag", "missing_volume_flag",
    ]
    frame = normalize_dates(pd.read_parquet(path, columns=columns))
    frame = frame.loc[frame["trade_date"] <= maximum_date].copy()
    assert_no_holdout(frame)

    if frame.duplicated(["trade_date", "symbol"]).any():
        raise ValueError(
            "Liquidity feature data contains duplicate date-symbol rows"
        )

    return frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)


def audit_frame(
    frame: pd.DataFrame,
    *,
    path: Path,
    key_columns: tuple[str, ...] = ("trade_date", "symbol"),
) -> FrameAudit:
    dates = pd.to_datetime(frame["trade_date"], errors="raise")
    return FrameAudit(
        path=str(path),
        rows=int(len(frame)),
        symbols=int(frame["symbol"].nunique()),
        min_date=dates.min().date().isoformat(),
        max_date=dates.max().date().isoformat(),
        holdout_rows=int((dates >= FINAL_HOLDOUT_START).sum()),
        duplicate_keys=int(frame.duplicated(list(key_columns)).sum()),
    )
