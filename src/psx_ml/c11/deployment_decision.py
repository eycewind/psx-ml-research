from __future__ import annotations

import pandas as pd


PRIMARY_CANDIDATE = "A07_P4_25_P5_75"
SECONDARY_CANDIDATE = "A17_P2R_P4_P5_equal"
REFERENCE = "A06_P5"


def build_finalist_scorecard(
    allocation_summary: pd.DataFrame,
    concentration_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Join accepted CP4B economics/execution with CP5 concentration.

    This is a reporting/decision table only. It does not optimize weights or
    re-run any model.
    """
    finalists = [PRIMARY_CANDIDATE, SECONDARY_CANDIDATE, REFERENCE]

    a = allocation_summary.loc[
        allocation_summary["allocation_id"].isin(finalists)
    ].copy()
    c = concentration_summary.loc[
        concentration_summary["allocation_id"].isin(finalists)
    ].copy()

    key = ["allocation_id", "starting_capital"]
    out = a.merge(c, on=key, how="left", validate="one_to_one")

    if out[key].duplicated().any():
        raise ValueError("Duplicate finalist/capital scorecard row")

    return out.sort_values(key).reset_index(drop=True)


def select_primary_deployment(scorecard_1m: pd.DataFrame) -> str:
    """Freeze the C11 deployment choice without return-grid optimization.

    CP6 compares only the two finalists already nominated after CP4B/CP5:
      - A07: P4 25% / P5 75%
      - A17: P2-refill / P4 / P5 equal thirds

    The choice is deliberately not an argmax over return or Sharpe. A07 is
    selected because, relative to A17, it:
      * uses only the two native Shariah policies P4/P5;
      * avoids the transformed P2-refill sleeve;
      * has materially lower worst realized single-name concentration;
      * has materially lower worst realized sector concentration;
      * retains strong execution and higher historical annualized return.

    A17 remains the secondary/risk-balanced diagnostic candidate because its
    historical drawdown and Sharpe are somewhat better.
    """
    required = {
        "allocation_id",
        "annualized_return",
        "sharpe_zero_rf",
        "max_drawdown",
        "realized_max_name_worst",
        "realized_max_sector_worst",
    }
    missing = sorted(required - set(scorecard_1m.columns))
    if missing:
        raise ValueError(f"CP6 scorecard missing columns: {missing}")

    ids = set(scorecard_1m["allocation_id"].astype(str))
    if PRIMARY_CANDIDATE not in ids or SECONDARY_CANDIDATE not in ids:
        raise ValueError("CP6 finalist rows missing")

    # The selection itself is policy-frozen, not metric-optimized. Assertions
    # below protect the evidence used to justify that freeze.
    a07 = scorecard_1m.loc[
        scorecard_1m["allocation_id"] == PRIMARY_CANDIDATE
    ].iloc[0]
    a17 = scorecard_1m.loc[
        scorecard_1m["allocation_id"] == SECONDARY_CANDIDATE
    ].iloc[0]

    if not (
        float(a07["realized_max_name_worst"])
        < float(a17["realized_max_name_worst"])
    ):
        raise RuntimeError("Expected A07 single-name concentration advantage lost")
    if not (
        float(a07["realized_max_sector_worst"])
        < float(a17["realized_max_sector_worst"])
    ):
        raise RuntimeError("Expected A07 sector concentration advantage lost")

    return PRIMARY_CANDIDATE
