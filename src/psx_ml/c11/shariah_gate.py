from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


REQUIRED_HISTORY_COLUMNS = {
    "symbol",
    "effective_from",
    "effective_to",
    "screening_snapshot_date",
    "membership_source",
    "membership_confidence",
    "is_shariah_screened_eligible",
}

ALLOWED_CONFIDENCE = {"high", "medium", "low"}


@dataclass(frozen=True)
class ShariahGateDecision:
    symbol: str
    signal_date: str
    shariah_eligible: bool
    gate_status: str
    shariah_source: str | None
    shariah_confidence: str | None
    screening_snapshot_date: str | None
    screening_effective_from: str | None
    screening_effective_to: str | None
    low_confidence_flag: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(bool)

    mapped = (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map({"true": True, "false": False, "1": True, "0": False})
    )
    if mapped.isna().any():
        bad = sorted(series.loc[mapped.isna()].astype(str).unique().tolist())
        raise ValueError(f"Unrecognized Shariah eligibility values: {bad}")
    return mapped.astype(bool)


def normalize_screening_history(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(REQUIRED_HISTORY_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Shariah screening history missing columns: {missing}")

    result = frame.copy()
    result["symbol"] = result["symbol"].astype(str).str.strip().str.upper()
    for column in ("effective_from", "effective_to", "screening_snapshot_date"):
        result[column] = pd.to_datetime(result[column], errors="coerce").dt.normalize()

    if result["effective_from"].isna().any():
        raise ValueError("Shariah screening history contains invalid effective_from")
    if result["screening_snapshot_date"].isna().any():
        raise ValueError("Shariah screening history contains invalid screening_snapshot_date")

    result["membership_source"] = result["membership_source"].astype(str).str.strip()
    result["membership_confidence"] = (
        result["membership_confidence"].astype(str).str.strip().str.lower()
    )
    bad_confidence = sorted(
        set(result["membership_confidence"].unique()) - ALLOWED_CONFIDENCE
    )
    if bad_confidence:
        raise ValueError(f"Unexpected membership confidence values: {bad_confidence}")

    result["is_shariah_screened_eligible"] = _normalize_bool(
        result["is_shariah_screened_eligible"]
    )

    invalid_interval = (
        result["effective_to"].notna()
        & (result["effective_to"] <= result["effective_from"])
    )
    if invalid_interval.any():
        raise ValueError("Shariah screening history contains invalid intervals")

    # A symbol may have many non-overlapping intervals, but never two active
    # records on the same date. This is the key fail-closed PIT property.
    for symbol, group in result.groupby("symbol", sort=False):
        ordered = group.sort_values("effective_from")
        previous_end: pd.Timestamp | None = None
        for row in ordered.itertuples(index=False):
            start = row.effective_from
            end = row.effective_to
            if previous_end is None:
                pass
            elif pd.isna(previous_end):
                raise ValueError(
                    f"Overlapping/open-ended Shariah intervals for {symbol}"
                )
            elif start < previous_end:
                raise ValueError(f"Overlapping Shariah intervals for {symbol}")
            previous_end = end

    return result.sort_values(["symbol", "effective_from"]).reset_index(drop=True)


def decide_shariah_eligibility(
    history: pd.DataFrame,
    *,
    symbol: str,
    signal_date: str | pd.Timestamp,
) -> ShariahGateDecision:
    normalized = normalize_screening_history(history)
    sym = str(symbol).strip().upper()
    date = pd.Timestamp(signal_date).normalize()

    rows = normalized.loc[
        (normalized["symbol"] == sym)
        & (normalized["effective_from"] <= date)
        & (
            normalized["effective_to"].isna()
            | (date < normalized["effective_to"])
        )
    ]

    if len(rows) > 1:
        raise ValueError(
            f"Multiple PIT Shariah records resolve for {sym} on {date.date()}"
        )

    if rows.empty:
        return ShariahGateDecision(
            symbol=sym,
            signal_date=date.date().isoformat(),
            shariah_eligible=False,
            gate_status="rejected_unknown",
            shariah_source=None,
            shariah_confidence=None,
            screening_snapshot_date=None,
            screening_effective_from=None,
            screening_effective_to=None,
            low_confidence_flag=False,
            reason="no_point_in_time_shariah_record",
        )

    row = rows.iloc[0]
    confidence = str(row["membership_confidence"])
    eligible = bool(row["is_shariah_screened_eligible"])
    low_flag = eligible and confidence == "low"

    def iso(value: object) -> str | None:
        if pd.isna(value):
            return None
        return pd.Timestamp(value).date().isoformat()

    return ShariahGateDecision(
        symbol=sym,
        signal_date=date.date().isoformat(),
        shariah_eligible=eligible,
        gate_status=("eligible_flagged_low_confidence" if low_flag else "eligible")
        if eligible
        else "rejected_non_compliant",
        shariah_source=str(row["membership_source"]),
        shariah_confidence=confidence,
        screening_snapshot_date=iso(row["screening_snapshot_date"]),
        screening_effective_from=iso(row["effective_from"]),
        screening_effective_to=iso(row["effective_to"]),
        low_confidence_flag=low_flag,
        reason=(
            "point_in_time_shariah_eligible_low_confidence"
            if low_flag
            else "point_in_time_shariah_eligible"
            if eligible
            else "point_in_time_shariah_ineligible"
        ),
    )
